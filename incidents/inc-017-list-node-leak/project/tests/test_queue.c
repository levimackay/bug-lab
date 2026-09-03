#include "queue.h"
#include "harness.h"

TEST(push_increases_size) {
    queue_t *q = queue_create();
    queue_push(q, 1, "reindex-job");
    CHECK(queue_size(q) == 1);
    queue_destroy(q);
}

TEST(remove_decreases_size_and_unlinks) {
    queue_t *q = queue_create();
    queue_push(q, 1, "reindex-job");
    queue_push(q, 2, "thumbnail-job");
    CHECK(queue_remove(q, 1) == 1);
    CHECK(queue_size(q) == 1);
    CHECK(queue_peek_name(q, 1) == NULL);
    CHECK_EQ_STR(queue_peek_name(q, 2), "thumbnail-job");
    queue_destroy(q);
}

TEST(remove_missing_id_returns_zero) {
    queue_t *q = queue_create();
    queue_push(q, 1, "reindex-job");
    CHECK(queue_remove(q, 99) == 0);
    CHECK(queue_size(q) == 1);
    queue_destroy(q);
}

TEST(peek_copies_are_owned_by_queue) {
    queue_t *q = queue_create();
    queue_push(q, 5, "export-job");
    CHECK_EQ_STR(queue_peek_name(q, 5), "export-job");
    queue_destroy(q);
}

TEST(push_remove_small_burst_stays_correct) {
    queue_t *q = queue_create();
    for (int i = 0; i < 20; i++) {
        queue_push(q, i, "job");
        queue_remove(q, i);
    }
    CHECK(queue_size(q) == 0);
    queue_destroy(q);
}

int main(void) {
    return RUN_ALL();
}
