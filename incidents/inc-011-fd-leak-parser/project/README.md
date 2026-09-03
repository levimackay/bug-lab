# Orders API config loader

Small INI-style config reader used by the orders API. The service watches
`config/service.conf` and calls `config_load()` on a timer so ops can change
a rate limit or feature flag without a restart.

    cc -fsanitize=address,undefined -g -Isrc -o build/app src/*.c
    ./build/app             # simulates 300 reload cycles, the way the timer does
    cc -fsanitize=address,undefined -g -Isrc -Itests -o build/tests src/config.c tests/test_config.c
    ./build/tests

`config_load(path)` parses `key = value` lines (`#` and `;` start comments)
into a fixed-size table and returns a heap-allocated `config_t *`, or `NULL`
on error. Callers release it with `config_free()`.
