#include <sanitizer/allocator_interface.h>
#include <stdio.h>

#include "queue.h"

/* The reindex worker pushes one job, processes it, and removes it, all day
 * long. Steady-state memory should be flat: nothing here should accumulate. */
#define CYCLES 10000
#define LEAK_THRESHOLD_BYTES 200000

int main(void) {
    queue_t *q = queue_create();

    size_t before = __sanitizer_get_current_allocated_bytes();
    for (int i = 0; i < CYCLES; i++) {
        queue_push(q, i, "reindex-job");
        queue_remove(q, i);
    }
    size_t after = __sanitizer_get_current_allocated_bytes();

    long delta = (long)after - (long)before;
    printf("live heap before: %zu bytes\n", before);
    printf("live heap after:  %zu bytes\n", after);
    printf("delta over %d push/remove cycles: %ld bytes\n", CYCLES, delta);

    queue_destroy(q);

    if (delta > LEAK_THRESHOLD_BYTES) {
        fprintf(stderr, "job queue leaked memory across the burst (delta %ld > %d)\n", delta, LEAK_THRESHOLD_BYTES);
        return 1;
    }
    return 0;
}
