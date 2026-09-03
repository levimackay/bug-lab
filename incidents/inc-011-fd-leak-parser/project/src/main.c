#include <stdio.h>

#include "config.h"

/* The orders API re-reads its config on a timer so ops can roll out a new
 * rate limit or feature flag without a restart. This drives that reload
 * loop the way the service does in production. */
#define RELOAD_COUNT 300

int main(void) {
    const char *path = "config/service.conf";
    int failures = 0;

    for (int i = 0; i < RELOAD_COUNT; i++) {
        config_t *cfg = config_load(path);
        if (!cfg) {
            fprintf(stderr, "reload #%d: config_load(%s) failed\n", i + 1, path);
            failures++;
            break;
        }
        if (i == 0) {
            printf("service.conf loaded: %d keys\n", cfg->count);
            const char *name = config_get(cfg, "service_name");
            printf("service_name = %s\n", name ? name : "(unset)");
        }
        config_free(cfg);
    }

    if (failures > 0) {
        fprintf(stderr, "config reload failed after repeated attempts, giving up\n");
        return 1;
    }

    printf("reloaded config %d times successfully\n", RELOAD_COUNT);
    return 0;
}
