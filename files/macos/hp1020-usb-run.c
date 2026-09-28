/* Bind CUPS back/side channels without Python preexec_fn or inherited fd leaks.
 * Called only by the worker with its fixed system USB backend and numeric fds. */
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 4) return 2;
    char *end;
    long a = strtol(argv[1], &end, 10);
    if (*end || a < 0 || a > 1024 * 1024) return 2;
    long b = strtol(argv[2], &end, 10);
    if (*end || b < 0 || b > 1024 * 1024) return 2;
    int back = fcntl((int)a, F_DUPFD_CLOEXEC, 10);
    int side = fcntl((int)b, F_DUPFD_CLOEXEC, 10);
    if (back < 0 || side < 0 || dup2(back, 3) < 0 || dup2(side, 4) < 0) {
        perror("HP 1020 channel setup");
        return 1;
    }
    if (a > 4) close((int)a);
    if (b > 4 && b != a) close((int)b);
    close(back);
    close(side);
    execv(argv[3], argv + 3);
    perror("HP 1020 USB backend");
    return 1;
}
