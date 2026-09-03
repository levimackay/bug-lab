#include <stdlib.h>

#include "queue.h"
#include "harness.h"

TEST(pop_removes_the_oldest_message) {
    message_queue_t *q = mq_create();
    mq_push(q, "job-1");
    mq_push(q, "job-2");
    char *first = mq_pop(q);
    CHECK(first != NULL);
    CHECK(mq_size(q) == 1);
    mq_destroy(q);
}

TEST(pop_returns_a_readable_copy_of_the_payload) {
    message_queue_t *q = mq_create();
    mq_push(q, "order.created:8841");
    char *popped = mq_pop(q);
    CHECK(popped != NULL);
    CHECK_EQ_STR(popped, "order.created:8841");
    free(popped);
    mq_destroy(q);
}

int main(void) {
    return RUN_ALL();
}
