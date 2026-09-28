/* Shared native CUPS driver utilities. No discovery or device access here. */
#ifndef HP1020_COMMON_H
#define HP1020_COMMON_H
#include <cups/cups.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#ifndef HP1020_BASE
#define HP1020_BASE "/Library/Printers/hp1020"
#endif
static volatile sig_atomic_t hp_cancelled;
static void hp_stop(int sig) { (void)sig; hp_cancelled = 1; }
static void hp_signals(void) {
    struct sigaction action = {0};
    action.sa_handler = hp_stop;
    sigaction(SIGTERM, &action, NULL);
    sigaction(SIGINT, &action, NULL);
    signal(SIGPIPE, SIG_IGN);
}
static double hp_now(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts)) { perror("ERROR: Monotonic clock"); exit(3); }
    return ts.tv_sec + ts.tv_nsec / 1e9;
}
static FILE *hp_temp(void) {
    char name[1024];
    int fd = cupsTempFd(name, sizeof(name));
    if (fd < 0) return NULL;
    /* Even a killed process leaves no extra document archive. */
    if (unlink(name)) { close(fd); return NULL; }
    fcntl(fd, F_SETFD, FD_CLOEXEC);
    FILE *file = fdopen(fd, "w+b");
    if (!file) close(fd);
    return file;
}
static int hp_options(const char *raw) {
    cups_option_t *options = NULL;
    int count = cupsParseOptions(raw, 0, &options), valid = 1;
    const char *value = cupsGetOption("sides", count, options);
    if (value && strcasecmp(value, "one-sided")) valid = 0;
    value = cupsGetOption("Duplex", count, options);
    if (value && strcasecmp(value, "None") && strcasecmp(value, "False") && strcasecmp(value, "Off")) valid = 0;
    value = cupsGetOption("InputSlot", count, options);
    if (value && strcasecmp(value, "Auto") && strcasecmp(value, "Automatic")) valid = 0;
    value = cupsGetOption("PageSize", count, options);
    if (!value) value = cupsGetOption("media", count, options);
    if (value && strcasecmp(value, "A4") && strcasecmp(value, "Letter") &&
        strcasecmp(value, "iso_a4_210x297mm") && strcasecmp(value, "na_letter_8.5x11in")) valid = 0;
    cupsFreeOptions(count, options);
    if (!valid) fputs("ERROR: Choose A4 or US Letter, single-sided, using the normal tray.\n", stderr);
    return valid;
}
#endif
