#include <ctype.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "config.h"

static void trim(char *s) {
    size_t n = strlen(s);
    while (n > 0 && isspace((unsigned char)s[n - 1])) {
        s[--n] = '\0';
    }
    char *start = s;
    while (*start && isspace((unsigned char)*start)) {
        start++;
    }
    if (start != s) {
        memmove(s, start, strlen(start) + 1);
    }
}

config_t *config_load(const char *path) {
    FILE *fp = fopen(path, "r");
    if (!fp) {
        fprintf(stderr, "config: cannot open %s: %s\n", path, strerror(errno));
        return NULL;
    }

    config_t *cfg = calloc(1, sizeof(config_t));
    if (!cfg) {
        fclose(fp);
        return NULL;
    }

    char line[256];
    int lineno = 0;
    while (fgets(line, sizeof(line), fp)) {
        lineno++;
        trim(line);
        if (line[0] == '\0' || line[0] == '#' || line[0] == ';') {
            continue;
        }
        char *eq = strchr(line, '=');
        if (!eq) {
            fprintf(stderr, "config: %s:%d: malformed line, skipping\n", path, lineno);
            continue;
        }
        *eq = '\0';
        char *key = line;
        char *value = eq + 1;
        trim(key);
        trim(value);
        if (cfg->count >= CONFIG_MAX_ENTRIES) {
            fprintf(stderr, "config: %s: too many entries, truncating at %d\n", path, CONFIG_MAX_ENTRIES);
            break;
        }
        snprintf(cfg->entries[cfg->count].key, CONFIG_KEY_LEN, "%s", key);
        snprintf(cfg->entries[cfg->count].value, CONFIG_VALUE_LEN, "%s", value);
        cfg->count++;
    }

    return cfg;
}

const char *config_get(const config_t *cfg, const char *key) {
    if (!cfg) {
        return NULL;
    }
    for (int i = 0; i < cfg->count; i++) {
        if (strcmp(cfg->entries[i].key, key) == 0) {
            return cfg->entries[i].value;
        }
    }
    return NULL;
}

void config_free(config_t *cfg) {
    free(cfg);
}
