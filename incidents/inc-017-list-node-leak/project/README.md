# Reindex worker job queue

An in-memory linked-list queue the reindex worker uses to track jobs between
being scheduled and being processed. Jobs are pushed by id and name, and
removed once processed.

    cc -fsanitize=address,undefined -g -Isrc -o build/app src/*.c
    ASAN_OPTIONS=detect_leaks=0 ./build/app     # 10,000 push/remove cycles, checks the heap stays flat
    cc -fsanitize=address,undefined -g -Isrc -Itests -o build/tests src/queue.c tests/test_queue.c
    ./build/tests

`queue_push(q, id, name)` copies `name` onto a new node. `queue_remove(q, id)`
unlinks and releases the job with that id, returning `1` if it was found or
`0` otherwise. `queue_destroy(q)` releases everything still queued plus the
queue itself.

LeakSanitizer isn't available on this platform, so the self-check in
`main.c` and the regression test both watch
`__sanitizer_get_current_allocated_bytes()` (AddressSanitizer's own live-heap
counter) across a burst of cycles instead of relying on `detect_leaks=1`.
