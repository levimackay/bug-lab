#ifndef CONFIG_H
#define CONFIG_H

#define CONFIG_MAX_ENTRIES 64
#define CONFIG_KEY_LEN 64
#define CONFIG_VALUE_LEN 128

typedef struct {
    char key[CONFIG_KEY_LEN];
    char value[CONFIG_VALUE_LEN];
} config_entry_t;

typedef struct {
    config_entry_t entries[CONFIG_MAX_ENTRIES];
    int count;
} config_t;

/* Parses a "key = value" file (# and ; start comments, blank lines ignored).
 * Returns a heap-allocated config on success, or NULL on error. */
config_t *config_load(const char *path);

const char *config_get(const config_t *cfg, const char *key);

void config_free(config_t *cfg);

#endif
