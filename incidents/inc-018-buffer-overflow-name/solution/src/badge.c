#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "badge.h"

badge_t *badge_create(int id, const char *title, const char *name) {
    badge_t *b = malloc(sizeof(badge_t));
    if (!b) {
        return NULL;
    }
    b->id = id;
    snprintf(b->title, BADGE_TITLE_LEN, "%s", title);
    snprintf(b->name, BADGE_NAME_LEN, "%s", name);
    return b;
}

void badge_format(const badge_t *b, char *out, size_t out_len) {
    snprintf(out, out_len, "%s (%s) #%04d", b->name, b->title, b->id);
}

void badge_free(badge_t *b) {
    free(b);
}
