#ifndef BADGE_H
#define BADGE_H

#include <stddef.h>

#define BADGE_TITLE_LEN 16
#define BADGE_NAME_LEN 32

typedef struct {
    int id;
    char title[BADGE_TITLE_LEN];
    char name[BADGE_NAME_LEN];
} badge_t;

/* Builds a badge from the roster's raw name field. name is copied in,
 * truncated to fit if it doesn't. Returns NULL on allocation failure. */
badge_t *badge_create(int id, const char *title, const char *name);

/* Writes "Name (title) #id" into out (a caller-supplied buffer of out_len
 * bytes), truncating if necessary. */
void badge_format(const badge_t *b, char *out, size_t out_len);

void badge_free(badge_t *b);

#endif
