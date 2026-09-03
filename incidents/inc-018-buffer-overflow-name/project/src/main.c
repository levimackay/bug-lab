#include <stdio.h>
#include <string.h>

#include "badge.h"

/* Prints one attendee badge from the roster upload. In production the
 * roster comes from a CSV that vendors fill in by hand, so the name field
 * is whatever they typed. */
static int read_first_line(const char *path, char *buf, size_t buf_len) {
    FILE *fp = fopen(path, "r");
    if (!fp) {
        return -1;
    }
    if (!fgets(buf, (int)buf_len, fp)) {
        fclose(fp);
        return -1;
    }
    fclose(fp);
    buf[strcspn(buf, "\r\n")] = '\0';
    return 0;
}

int main(void) {
    char name[256];
    if (read_first_line("data/roster.txt", name, sizeof(name)) != 0) {
        fprintf(stderr, "could not read data/roster.txt\n");
        return 1;
    }

    badge_t *b = badge_create(4021, "Attendee", name);
    if (!b) {
        fprintf(stderr, "badge_create failed\n");
        return 1;
    }

    char line[128];
    badge_format(b, line, sizeof(line));
    printf("%s\n", line);

    badge_free(b);
    return 0;
}
