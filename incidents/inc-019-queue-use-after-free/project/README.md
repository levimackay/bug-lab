# Order dispatcher queue

A small FIFO message queue the order dispatcher uses between "event
happened" and "notifier sent it". Events are pushed as they occur and
popped in order for delivery.

    cc -fsanitize=address,undefined -g -Isrc -o build/app src/*.c
    ./build/app                    # pushes three events, dispatches them in order
    cc -fsanitize=address,undefined -g -Isrc -Itests -o build/tests src/queue.c tests/test_queue.c
    ./build/tests

`mq_push(q, payload)` copies `payload` onto the tail. `mq_pop(q)` dequeues
the oldest message and returns a heap string the caller owns and must
`free()`; it returns `NULL` when the queue is empty. `mq_destroy(q)`
releases whatever is still queued plus the queue itself.
