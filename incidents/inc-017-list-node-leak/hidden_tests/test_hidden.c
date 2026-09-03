#include <sanitizer/allocator_interface.h>

#include "queue.h"
#include "harness.h"

/* AddressSanitizer's own live-allocation counter, not LeakSanitizer (which
 * this platform does not support): it reflects every byte currently handed
 * out by the allocator, so a node that is unlinked but never freed keeps
 * counting here even though it is unreachable. */
TEST(ten_thousand_cycles_leave_heap_flat) {
    queue_t *q = queue_create();
    size_t before = __sanitizer_get_current_allocated_bytes();

    for (int i = 0; i < 10000; i++) {
        queue_push(q, i, "reindex-job");
        queue_remove(q, i);
    }

    size_t after = __sanitizer_get_current_allocated_bytes();
    long delta = (long)after - (long)before;
    CHECK(delta <= 200000);
    CHECK(queue_size(q) == 0);

    queue_destroy(q);
}

int main(void) {
    return RUN_ALL();
}
