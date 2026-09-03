/* Minimal test harness printing TAP. Include from a test .c file:
 *
 *   #include "harness.h"
 *   TEST(push_then_pop) { CHECK(pop(push(q, 1)) == 1); }
 *   int main(void) { RUN_ALL(); }
 *
 * Each TEST registers itself; RUN_ALL prints "ok N - name" / "not ok N - name"
 * with "# file:line: expr" diagnostics for failed checks and returns non-zero
 * when any test failed. A sanitizer abort mid-run leaves the TAP output short,
 * which Bug Lab reports as a failure together with the sanitizer report.
 */
#ifndef BUGLAB_HARNESS_H
#define BUGLAB_HARNESS_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef void (*bl_test_fn)(void);
struct bl_test { const char *name; bl_test_fn fn; };

static struct bl_test bl_tests[256];
static int bl_test_count = 0;
static int bl_current_failed = 0;

static void bl_register(const char *name, bl_test_fn fn) {
    if (bl_test_count < 256) { bl_tests[bl_test_count].name = name; bl_tests[bl_test_count].fn = fn; bl_test_count++; }
}

#define TEST(name) \
    static void bl_test_##name(void); \
    __attribute__((constructor)) static void bl_reg_##name(void) { bl_register(#name, bl_test_##name); } \
    static void bl_test_##name(void)

#define CHECK(cond) do { if (!(cond)) { bl_current_failed = 1; printf("# %s:%d: CHECK(%s) failed\n", __FILE__, __LINE__, #cond); } } while (0)
#define CHECK_EQ_INT(a, b) do { long bl_a = (long)(a), bl_b = (long)(b); if (bl_a != bl_b) { bl_current_failed = 1; printf("# %s:%d: %s == %s: %ld != %ld\n", __FILE__, __LINE__, #a, #b, bl_a, bl_b); } } while (0)
#define CHECK_EQ_STR(a, b) do { const char *bl_a = (a), *bl_b = (b); if (!bl_a || !bl_b || strcmp(bl_a, bl_b) != 0) { bl_current_failed = 1; printf("# %s:%d: %s == %s: \"%s\" != \"%s\"\n", __FILE__, __LINE__, #a, #b, bl_a ? bl_a : "(null)", bl_b ? bl_b : "(null)"); } } while (0)

static int RUN_ALL(void) {
    int failed = 0;
    setvbuf(stdout, NULL, _IONBF, 0);
    printf("1..%d\n", bl_test_count);
    for (int i = 0; i < bl_test_count; i++) {
        bl_current_failed = 0;
        bl_tests[i].fn();
        printf("%s %d - %s\n", bl_current_failed ? "not ok" : "ok", i + 1, bl_tests[i].name);
        failed += bl_current_failed;
    }
    return failed ? 1 : 0;
}

#endif
