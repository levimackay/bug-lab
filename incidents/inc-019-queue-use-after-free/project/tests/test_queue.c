#include <stdlib.h>

#include "queue.h"
#include "harness.h"

TEST(push_increases_size) {
    message_queue_t *q = mq_create();
    mq_push(q, "job-1");
    CHECK(mq_size(q) == 1);
    mq_destroy(q);
}

TEST(pop_decreases_size_and_returns_non_null) {
    /* Deliberately does not free() or read the popped pointer here - this
     * suite only checks bookkeeping, never the payload itself. */
    message_queue_t *q = mq_create();
    mq_push(q, "job-1");
    char *popped = mq_pop(q);
    CHECK(popped != NULL);
    CHECK(mq_size(q) == 0);
    mq_destroy(q);
}

TEST(pop_on_empty_queue_returns_null) {
    message_queue_t *q = mq_create();
    CHECK(mq_pop(q) == NULL);
    mq_destroy(q);
}

TEST(multiple_pushes_track_count) {
    message_queue_t *q = mq_create();
    mq_push(q, "a");
    mq_push(q, "b");
    mq_push(q, "c");
    CHECK(mq_size(q) == 3);
    mq_destroy(q);
}

int main(void) {
    return RUN_ALL();
}
