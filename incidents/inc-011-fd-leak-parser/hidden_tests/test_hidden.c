#include <sys/resource.h>

#include "config.h"
#include "harness.h"

/* Mirrors the reload watchdog in main.c, but under a tight descriptor
 * budget so a leak shows up in well under 300 iterations. */
TEST(reload_survives_two_hundred_cycles_under_fd_pressure) {
    struct rlimit lim = { .rlim_cur = 64, .rlim_max = 64 };
    CHECK(setrlimit(RLIMIT_NOFILE, &lim) == 0);

    int failures = 0;
    for (int i = 0; i < 200; i++) {
        config_t *cfg = config_load("config/service.conf");
        if (!cfg) {
            failures++;
            break;
        }
        config_free(cfg);
    }
    CHECK(failures == 0);
}

int main(void) {
    return RUN_ALL();
}
