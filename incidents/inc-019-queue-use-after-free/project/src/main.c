#include <stdio.h>
#include <stdlib.h>

#include "queue.h"

/* The order dispatcher: push events as they happen, pop and hand them to
 * the shipping notifier in order. */
int main(void) {
    message_queue_t *q = mq_create();
    mq_push(q, "order.created:8841");
    mq_push(q, "order.shipped:8841");
    mq_push(q, "order.created:9002");

    for (int i = 0; i < 3; i++) {
        char *msg = mq_pop(q);
        if (!msg) {
            fprintf(stderr, "queue empty early\n");
            break;
        }
        printf("dispatched: %s\n", msg);
        free(msg);
    }

    mq_destroy(q);
    return 0;
}
