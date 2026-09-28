/* Per-job CUPS backend. Apple owns USB; CUPS owns scheduling and cancellation.
 * Validate the completed encoder stream before USB, load stock firmware only
 * if absent, and report documented PJL feedback through standard CUPS stderr.
 */
#include "hp1020-common.h"
#include <arpa/inet.h>
#include <ctype.h>
#include <poll.h>
#include <stdint.h>
#include <sys/socket.h>
#ifndef HP1020_USB
#define HP1020_USB "/usr/libexec/cups/backend/usb"
#endif
#ifndef HP1020_CONNECT_TIMEOUT
#define HP1020_CONNECT_TIMEOUT 30
#define HP1020_TRANSFER_TIMEOUT 180
#define HP1020_CLOSE_TIMEOUT 30
#define HP1020_STATUS_GRACE 8
#define HP1020_PROGRESS_TIMEOUT 300
#endif
#define LIMIT (1024LL * 1024 * 1024)
#define FRAME 16384
static const char prefix[] = "\033%-12345X@PJL JOB\n";
static const char suffix[] = "\033%-12345X@PJL EOJ\n\033%-12345X";
static const char *reasons[] = {"media-empty-error", "media-jam-error", "cover-open-error", "toner-empty-error", "toner-low-warning", "offline-report"};

typedef struct {
    pid_t pid;
    int input, back, side, log, exited, exit_code;
    double connected, progress;
    char token[64], ident[8193], frame[FRAME + 1], logs[FRAME + 1];
    size_t used, log_used, side_used, parent_used;
    unsigned char side_data[8196], parent_data[8196];
    int discard, attention, started, completed, cancelled, reason, got_id, reset, pending;
    unsigned pages, last_page;
} Transport;
static int parent_side = -1, parent_back = -1;

static void message(const char *text) {
    /* Printer-supplied text cannot inject CUPS control lines. */
    fputs("INFO: ", stderr);
    for (size_t i = 0; text[i] && i < 700; i++) fputc(text[i] >= 32 && text[i] < 127 ? text[i] : ' ', stderr);
    fputc('\n', stderr);
}
static int number(const char *str, unsigned *value) {
    if (!*str) return 0;
    unsigned long n = 0;
    for (; *str; str++) {
        if (*str < '0' || *str > '9' || n > 1000000) return 0;
        n = n * 10 + (*str - '0');
    }
    *value = (unsigned)n; return 1;
}
static void status_frame(Transport *t) {
    char *header = NULL, *name = NULL, *code = NULL, *pages = NULL, *single = NULL;
    int start = 0, end = 0, cancel = 0;
    char *save, *line = strtok_r(t->frame, "\r\n", &save);
    for (; line; line = strtok_r(NULL, "\r\n", &save)) {
        while (*line == ' ') line++;
        size_t n = strlen(line);
        while (n && line[n-1] == ' ') line[--n] = 0;
        if (!strncmp(line, "@PJL ", 5)) { header = line; name = code = pages = single = NULL; start = end = cancel = 0; }
        else if (!strncmp(line, "CODE=", 5)) code = line + 5;
        else if (!strncmp(line, "NAME=", 5)) {
            name = line + 5;
            if (*name == '"') { name++; n = strlen(name); if (n && name[n-1] == '"') name[n-1] = 0; }
        } else if (!strncmp(line, "PAGES=", 6)) pages = line + 6;
        else if (!strcmp(line, "START")) start = 1;
        else if (!strcmp(line, "END")) end = 1;
        else if (!strcmp(line, "CANCELED")) cancel = 1;
        else if (*line) single = line;
    }
    if (!header) return;
    unsigned value;
    if (!strcmp(header, "@PJL INFO STATUS") || !strcmp(header, "@PJL USTATUS DEVICE") || !strcmp(header, "@PJL USTATUS TIMED")) {
        if (!code || strlen(code) != 5 || !number(code, &value)) return;
        int reason = -1;
        const char *text = NULL;
        if (value >= 41000 && value <= 41999) { reason = 0; text = "Out of paper. Add paper to continue."; }
        else switch (value) {
            case 10001: text = "Printer ready."; break;
            case 10002: reason = 5; text = "Printer is offline."; break;
            case 10003: text = "Printer is warming up."; break;
            case 10004: text = "Printer is performing a self-test."; break;
            case 10005: text = "Printer is resetting."; break;
            case 10006: case 40038: reason = 4; text = "Printer reports low toner."; break;
            case 10023: text = "Printer is printing."; break;
            case 30119: case 40022: reason = 1; text = "Paper jam. Clear the jam to continue."; break;
            case 40021: reason = 2; text = "Printer cover is open."; break;
            case 40600: reason = 3; text = "Printer reports no toner cartridge."; break;
        }
        if (!text) { fprintf(stderr, "INFO: Printer reported status %u.\n", value); return; }
        for (int i = 0; i < 6; i++) fprintf(stderr, "STATE: %c%s\n", i == reason ? '+' : '-', reasons[i]);
        if (reason != t->reason || value == 10023) t->progress = hp_now();
        t->reason = reason; t->attention = reason >= 0 && reason != 4;
        message(text);
    } else if (!strcmp(header, "@PJL USTATUS JOB") && name && !strcmp(name, t->token)) {
        if (start) { t->started = 1; t->progress = hp_now(); }
        if (cancel) t->cancelled = 1;
        if (end && pages && number(pages, &value) && value == t->pages) { t->completed = 1; t->progress = hp_now(); }
    } else if (!strcmp(header, "@PJL USTATUS PAGE") && t->started && single && number(single, &value)) {
        if (value > t->last_page && value <= t->pages) {
            t->last_page = value; t->progress = hp_now();
            fprintf(stderr, "INFO: Printer reports page %u of %u printed.\n", value, t->pages);
        }
    }
}
static void back_data(Transport *t, const unsigned char *data, size_t count) {
    for (size_t i = 0; i < count; i++) {
        if (data[i] == '\f') {
            if (!t->discard) { t->frame[t->used] = 0; status_frame(t); }
            t->used = 0; t->discard = 0;
        } else if (t->used == FRAME || !data[i]) t->discard = 1;
        else if (!t->discard) t->frame[t->used++] = data[i];
    }
}
static int nonblock(int fd) { return fcntl(fd, F_SETFL, fcntl(fd, F_GETFL) | O_NONBLOCK); }
static int packet(int fd, unsigned cmd, unsigned result, const void *data, size_t size) {
    unsigned char buffer[8196];
    if (size > 8192) return 0;
    buffer[0] = cmd; buffer[1] = result; buffer[2] = size >> 8; buffer[3] = size;
    if (size) memcpy(buffer + 4, data, size);
    return write(fd, buffer, size + 4) == (ssize_t)size + 4;
}
static int pump(Transport *t, int milliseconds, int cancelling) {
    if (hp_cancelled && !cancelling) return 0;
    struct pollfd fds[] = {{t->back, POLLIN, 0}, {t->side, POLLIN, 0}, {t->log, POLLIN, 0}, {parent_side, POLLIN, 0}};
    int ready = poll(fds, 4, milliseconds);
    if (ready < 0 && errno != EINTR) return 0;
    unsigned char data[8192];
    for (int i = 0; i < 4; i++) {
        if (!(fds[i].revents & (POLLIN | POLLHUP))) continue;
        ssize_t n = read(fds[i].fd, data, sizeof(data));
        if (n < 0 && (errno == EAGAIN || errno == EINTR)) continue;
        if (n <= 0) {
            close(fds[i].fd);
            if (i == 0) t->back = -1;
            if (i == 1) t->side = -1;
            if (i == 2) t->log = -1;
            if (i == 3) parent_side = -1;
            continue;
        }
        if (i == 0) {
            back_data(t, data, (size_t)n);
            /* Preserve the standard back-channel for any upstream filter. */
            if (parent_back >= 0) (void)write(parent_back, data, (size_t)n);
        } else if (i == 2) {
            for (ssize_t j = 0; j < n; j++) {
                if (data[j] == '\n') {
                    t->logs[t->log_used] = 0;
                    if (!strcmp(t->logs, "STATE: -connecting-to-device")) t->connected = hp_now();
                    if (!strncmp(t->logs, "STATE: ", 7)) {
                        int safe = 1;
                        for (size_t k = 7; k < t->log_used; k++) if (!strchr("abcdefghijklmnopqrstuvwxyz0123456789,+- .", t->logs[k])) safe = 0;
                        if (safe) fprintf(stderr, "%s\n", t->logs);
                    } else if (!strncmp(t->logs, "INFO:", 5) || !strncmp(t->logs, "WARNING:", 8) || !strncmp(t->logs, "ERROR:", 6)) message(t->logs);
                    t->log_used = 0;
                } else if (t->log_used < FRAME) t->logs[t->log_used++] = data[j] >= 32 && data[j] < 127 ? data[j] : ' ';
            }
        } else {
            unsigned char *buf = i == 1 ? t->side_data : t->parent_data;
            size_t *used = i == 1 ? &t->side_used : &t->parent_used;
            for (ssize_t j = 0; j < n; j++) {
                if (*used >= 8196) return 0;
                buf[(*used)++] = data[j];
                if (*used < 4) continue;
                size_t len = ((size_t)buf[2] << 8) | buf[3];
                if (len > 8192) return 0;
                if (*used != len + 4) continue;
                if (i == 1) {
                    if (t->pending == buf[0]) {
                        packet(parent_side, buf[0], buf[1], buf + 4, len); t->pending = 0;
                    } else if (buf[0] == 4) {
                        t->got_id = buf[1] == 1 ? 1 : -1;
                        memcpy(t->ident, buf + 4, len); t->ident[len] = 0;
                    } else if (buf[0] == 1) t->reset = buf[1] == 1 ? 1 : -1;
                } else {
                    /* Upstream side-channel traffic is serialized with the
                     * initial identification; unsupported requests get a reply. */
                    if (buf[0] == 4 && t->got_id == 1) packet(parent_side, 4, 1, t->ident, strlen(t->ident));
                    else if (t->got_id == 1 && !t->pending && buf[0] >= 1 && buf[0] <= 8 && buf[1] == 0 && !len) {
                        if (!packet(t->side, buf[0], 0, NULL, 0)) return 0;
                        t->pending = buf[0];
                    } else packet(parent_side, buf[0], 7, NULL, 0); /* NOT_IMPLEMENTED */
                }
                *used = 0;
            }
        }
    }
    if (!t->exited) {
        int status;
        pid_t result = waitpid(t->pid, &status, WNOHANG);
        if (result == t->pid) { t->exited = 1; t->exit_code = WIFEXITED(status) ? WEXITSTATUS(status) : 1; }
        else if (result < 0 && errno == ECHILD) { t->exited = 1; t->exit_code = 1; }
    }
    return !t->cancelled;
}
static int start_usb(Transport *t, const char *uri, char **argv) {
    int input[2] = {-1,-1}, back[2] = {-1,-1}, log[2] = {-1,-1}, side[2] = {-1,-1};
    if (pipe(input) || pipe(back) || pipe(log) || socketpair(AF_UNIX, SOCK_STREAM, 0, side)) goto failed;
    t->pid = fork();
    if (!t->pid) {
        /* Duplicate sources before remapping CUPS's reserved descriptors. */
        int in = fcntl(input[0], F_DUPFD_CLOEXEC, 10), out = fcntl(back[1], F_DUPFD_CLOEXEC, 10);
        int err = fcntl(log[1], F_DUPFD_CLOEXEC, 10), sc = fcntl(side[1], F_DUPFD_CLOEXEC, 10);
        if (in < 0 || out < 0 || err < 0 || sc < 0) _exit(1);
        if (dup2(in, 0) < 0 || dup2(err, 2) < 0 || dup2(out, 3) < 0 || dup2(sc, 4) < 0) _exit(1);
        int nullfd = open("/dev/null", O_WRONLY);
        if (nullfd < 0 || dup2(nullfd, 1) < 0) _exit(1);
        for (int fd = 5, limit = getdtablesize(); fd < limit; fd++) close(fd);
        setenv("DEVICE_URI", uri, 1);
        execl(HP1020_USB, HP1020_USB, argv[1], argv[2], "HP LaserJet 1020 job", "1", "", NULL);
        _exit(1);
    }
    if (t->pid < 0) goto failed;
    close(input[0]); close(back[1]); close(log[1]); close(side[1]);
    t->input = input[1]; t->back = back[0]; t->side = side[0]; t->log = log[0];
    if (nonblock(t->input) || nonblock(t->back) || nonblock(t->side) || nonblock(t->log)) return 0;
    t->reason = -1; t->progress = hp_now();
    if (!packet(t->side, 4, 0, NULL, 0)) return 0;
    while (!t->got_id) {
        if (!pump(t, 50, 0) || t->exited || (t->connected && hp_now() - t->connected > HP1020_CONNECT_TIMEOUT)) return 0;
    }
    if (t->got_id != 1 || !strstr(t->ident, "MDL:HP LaserJet 1020;") || !strstr(t->ident, "MFG:Hewlett-Packard;")) return 0;
    if (!t->connected) t->connected = hp_now();
    return 1;
failed:
    for (int i = 0; i < 2; i++) { if (input[i] >= 0) close(input[i]); if (back[i] >= 0) close(back[i]); if (log[i] >= 0) close(log[i]); if (side[i] >= 0) close(side[i]); }
    return 0;
}
static int stop_usb(Transport *t, int reset) {
    if (t->pid <= 0) return 1;
    if (reset && !t->exited && t->connected && t->side >= 0) {
        t->pending = 0;
        packet(t->side, 1, 0, NULL, 0);
        double until = hp_now() + 2;
        while (!t->reset && !t->exited && hp_now() < until) pump(t, 50, 1);
        message(t->reset == 1 ? "Cancelled; printer buffer reset confirmed." : "Cancelled; printer buffer reset unconfirmed. A power cycle may be needed.");
    }
    /* Apple's SOFT_RESET handler drains pending input before resetting. EOF
     * then lets its stdin backend close normally. CUPS's macOS sandbox can
     * deny even a same-UID child's kill, so never assume kill succeeded and
     * enter a blocking wait. Keep every cleanup wait bounded. */
    if (t->input >= 0) { close(t->input); t->input = -1; }
    double until = hp_now() + HP1020_CLOSE_TIMEOUT;
    while (!t->exited && hp_now() < until) pump(t, 50, 1);
    if (!t->exited) {
        if (kill(t->pid, SIGKILL) < 0 && errno != ESRCH)
            perror("ERROR: Could not terminate the USB transport");
        until = hp_now() + 2;
        while (!t->exited && hp_now() < until) pump(t, 50, 1);
    }
    int fds[] = {t->input, t->back, t->side, t->log};
    for (int i = 0; i < 4; i++) if (fds[i] >= 0) close(fds[i]);
    t->input = t->back = t->side = t->log = -1;
    return t->exited;
}
static int transmit(Transport *t, FILE *file) {
    if (fseeko(file, 0, SEEK_SET)) return 0;
    clearerr(file);
    unsigned char data[32768];
    double last = hp_now();
    for (;;) {
        size_t count = fread(data, 1, sizeof(data), file);
        if (ferror(file)) return 0;
        int ended = feof(file);
        if (!count) break;
        size_t offset = 0;
        while (offset < count) {
            if (!pump(t, 10, 0) || t->exited) return 0;
            ssize_t sent = write(t->input, data + offset, count - offset);
            if (sent > 0) { offset += sent; last = hp_now(); }
            else if (sent < 0 && errno != EAGAIN && errno != EINTR) return 0;
            if (t->attention) last = hp_now();
            if (hp_now() - last > HP1020_TRANSFER_TIMEOUT) return 0;
        }
        if (ended) break;
    }
    return 1;
}
static int finish(Transport *t) {
    close(t->input); t->input = -1;
    double until = hp_now() + HP1020_CLOSE_TIMEOUT;
    while (!t->exited) if (!pump(t, 50, 0) || hp_now() > until) return 0;
    pump(t, 0, 0);
    return !t->exit_code;
}
static int wait_pages(Transport *t) {
    double began = hp_now();
    while (!t->completed) {
        if (!pump(t, 50, 0) || t->exited) return 0;
        if (t->attention) { t->progress = hp_now(); continue; }
        if (!t->started && hp_now() - began > HP1020_STATUS_GRACE) {
            fputs("STATE: +com.hp1020.status-unavailable-warning\n", stderr);
            message("Document sent; the printer has not confirmed physical completion.");
            return 1;
        }
        if (t->started && hp_now() - t->progress > HP1020_PROGRESS_TIMEOUT) return 0;
    }
    fputs("STATE: -com.hp1020.status-unavailable-warning\n", stderr);
    message("Printer confirmed all pages in this job.");
    return 1;
}
static int firmware_loaded(const char *ident) {
    const char *field = strstr(ident, ";FWVER:");
    return field && field[7] && field[7] != ';';
}
static uint32_t u32(const unsigned char *p) { uint32_t n; memcpy(&n, p, 4); return ntohl(n); }
static int validate(FILE *input, off_t length, unsigned *pages, off_t *start, off_t *end) {
    unsigned char head[4096];
    if (fseeko(input, 0, SEEK_SET)) return 0;
    size_t n = fread(head, 1, sizeof(head), input);
    if (n < sizeof(prefix) || memcmp(head, prefix, sizeof(prefix)-1)) return 0;
    size_t offset;
    for (offset = sizeof(prefix)-1; offset + 4 <= n && memcmp(head + offset, "JZJZ", 4); offset++) {}
    if (offset + 4 > n) return 0;
    *start = sizeof(prefix)-1;
    off_t pos = offset + 4;
    int first = 1, in_page = 0, image = 0, ended = 0;
    while (pos + 16 <= length) {
        unsigned char h[16];
        if (fseeko(input, pos, SEEK_SET) || fread(h, 1, 16, input) != 16) return 0;
        uint32_t size = u32(h), kind = u32(h+4), items = u32(h+8);
        if (size < 16 || pos + size > length || h[14] != 0x5a || h[15] != 0x5a || (first && kind != 0) || (!first && kind == 0)) return 0;
        first = 0;
        /* Check every item boundary before accepting generated output. */
        off_t cursor = pos + 16;
        for (uint32_t i = 0; i < items; i++) {
            unsigned char item[8];
            if (cursor + 8 > pos + size || fseeko(input, cursor, SEEK_SET) || fread(item, 1, 8, input) != 8) return 0;
            uint32_t len = u32(item);
            if (len < 8 || cursor + len > pos + size) return 0;
            cursor += len;
        }
        if (kind == 2) { if (in_page) return 0; in_page = 1; image = 0; (*pages)++; }
        if (kind == 5) { if (!in_page || size <= 16) return 0; image = 1; }
        if (kind == 3) { if (!in_page || !image) return 0; in_page = 0; }
        pos += size;
        if (kind == 1) { ended = 1; break; }
    }
    if (!ended || in_page || !*pages || length - pos != sizeof(suffix)-1) return 0;
    char tail[sizeof(suffix)];
    if (fseeko(input, pos, SEEK_SET) || fread(tail, 1, sizeof(suffix)-1, input) != sizeof(suffix)-1 || memcmp(tail, suffix, sizeof(suffix)-1)) return 0;
    *end = pos; return 1;
}
int main(int argc, char **argv) {
    if (argc == 2 && !strcmp(argv[1], "--version")) { puts("HP1020 native CUPS driver 3"); return 0; }
    if (argc == 1) return 0; /* No discovery: installer selects Apple's USB URI. */
    if (argc < 6 || argc > 7) return 3;
    hp_signals();
    if (!hp_options(argv[5])) return 3;
    const char *device = getenv("DEVICE_URI");
    const char *expected = "hp1020://Hewlett-Packard/HP%20LaserJet%201020?";
    if (!device || strncmp(device, expected, strlen(expected)) || strlen(device) > 2040 || strchr(device, '\n') || strchr(device, '\r')) {
        fputs("ERROR: Invalid HP LaserJet 1020 queue address.\n", stderr); return 3;
    }
    char uri[2048]; snprintf(uri, sizeof(uri), "usb:%s", device + 7);
    /* Capture CUPS's inherited channels before temporary files can reuse them. */
    if (fcntl(4, F_GETFD) >= 0) parent_side = fcntl(4, F_DUPFD_CLOEXEC, 10);
    if (fcntl(3, F_GETFD) >= 0) parent_back = fcntl(3, F_DUPFD_CLOEXEC, 10);
    if (parent_side >= 0) nonblock(parent_side);
    if (parent_back >= 0) nonblock(parent_back);
    FILE *raw = hp_temp(), *document = hp_temp();
    int source = argc == 7 ? open(argv[6], O_RDONLY | O_NOFOLLOW | O_NONBLOCK | O_CLOEXEC) : 0;
    Transport t = {.input=-1, .back=-1, .side=-1, .log=-1};
    int ok = 0, stopped = 1;
    if (!raw || !document || source < 0) goto done;
    struct stat st;
    if (argc == 7 && (fstat(source, &st) || !S_ISREG(st.st_mode))) goto done;
    message("Preparing the document.");
    unsigned char buffer[32768];
    off_t length = 0;
    for (;;) {
        if (hp_cancelled) goto done;
        struct pollfd p = {source, POLLIN, 0};
        int ready = poll(&p, 1, 100);
        if (ready < 0 && errno == EINTR) continue;
        if (ready < 0) goto done;
        if (!ready) continue;
        ssize_t n = read(source, buffer, sizeof(buffer));
        if (n < 0 && (errno == EINTR || errno == EAGAIN)) continue;
        if (n < 0) goto done;
        if (!n) break;
        length += n;
        if (length > LIMIT || fwrite(buffer, 1, n, raw) != (size_t)n) goto done;
    }
    if (fflush(raw)) goto done;
    off_t begin, end;
    if (!validate(raw, length, &t.pages, &begin, &end)) { fputs("ERROR: Incomplete or invalid printer data; nothing sent.\n", stderr); goto done; }
    snprintf(t.token, sizeof(t.token), "hp1020-%08x-%08x-%08x", arc4random(), arc4random(), arc4random());
    fprintf(document, "\033%%-12345X@PJL JOB NAME=\"%s\"\n", t.token);
    if (fseeko(raw, begin, SEEK_SET)) goto done;
    while (begin < end) {
        size_t n = (size_t)(end-begin) < sizeof(buffer) ? (size_t)(end-begin) : sizeof(buffer);
        if (fread(buffer, 1, n, raw) != n || fwrite(buffer, 1, n, document) != n) goto done;
        begin += n;
    }
    fprintf(document, "\033%%-12345X@PJL EOJ NAME=\"%s\"\n\033%%-12345X", t.token);
    if (fflush(document) || ferror(document)) goto done;
    message("Connecting to the printer.");
    if (!start_usb(&t, uri, argv)) goto done;
    if (!firmware_loaded(t.ident)) {
        message("Preparing the printer after power-on.");
        FILE *firmware = fopen(HP1020_BASE "/runtime/sihp1020.dl", "rb");
        int sent = firmware && transmit(&t, firmware) && finish(&t);
        if (firmware) fclose(firmware);
        if (!sent) goto done;
        if (!stop_usb(&t, 0)) goto done;
        unsigned pages = t.pages; char token[64]; memcpy(token, t.token, sizeof(token));
        memset(&t, 0, sizeof(t)); t.input=t.back=t.side=t.log=-1; t.pages=pages; memcpy(t.token,token,sizeof(token));
        if (!start_usb(&t, uri, argv) || !firmware_loaded(t.ident)) {
            fputs("ERROR: Printer firmware did not become ready; no document sent.\n", stderr); goto done;
        }
    }
    message("Sending the document.");
    ok = transmit(&t, document) && wait_pages(&t) && finish(&t);
done:
    stopped = stop_usb(&t, hp_cancelled);
    if (raw) fclose(raw);
    if (document) fclose(document);
    if (source > 0) close(source);
    if (parent_side >= 0) close(parent_side);
    if (parent_back >= 0) close(parent_back);
    if (!stopped) {
        fputs("ERROR: USB connection did not close. Reconnect the printer before resuming the queue.\n", stderr);
        return 4; /* CUPS_BACKEND_STOP: do not overlap a stuck transport. */
    }
    if (hp_cancelled) { message("Print job cancelled."); return 0; }
    if (!ok) fputs("ERROR: Job held. Check the printer and any partially printed pages before resuming.\n", stderr);
    return ok ? 0 : 3; /* CUPS_BACKEND_HOLD: no automatic duplicate printing. */
}
