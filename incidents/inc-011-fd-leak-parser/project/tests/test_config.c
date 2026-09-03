#include "config.h"
#include "harness.h"

TEST(load_parses_keys) {
    config_t *cfg = config_load("config/service.conf");
    CHECK(cfg != NULL);
    CHECK(cfg->count == 5);
    config_free(cfg);
}

TEST(load_reads_expected_values) {
    config_t *cfg = config_load("config/service.conf");
    CHECK_EQ_STR(config_get(cfg, "service_name"), "orders-api");
    CHECK_EQ_STR(config_get(cfg, "port"), "8080");
    config_free(cfg);
}

TEST(get_missing_key_returns_null) {
    config_t *cfg = config_load("config/service.conf");
    CHECK(config_get(cfg, "does_not_exist") == NULL);
    config_free(cfg);
}

TEST(load_missing_file_returns_null) {
    config_t *cfg = config_load("config/does-not-exist.conf");
    CHECK(cfg == NULL);
}

TEST(repeated_loads_stay_consistent) {
    for (int i = 0; i < 5; i++) {
        config_t *cfg = config_load("config/service.conf");
        CHECK(cfg != NULL);
        CHECK_EQ_STR(config_get(cfg, "log_level"), "info");
        config_free(cfg);
    }
}

int main(void) {
    return RUN_ALL();
}
