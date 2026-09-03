#ifndef QUEUE_H
#define QUEUE_H

typedef struct queue queue_t;

queue_t *queue_create(void);

/* Copies name; returns 0 on success, -1 on allocation failure. */
int queue_push(queue_t *q, int id, const char *name);

/* Unlinks and releases the job with this id. Returns 1 if it was found,
 * 0 if no job with that id is queued. */
int queue_remove(queue_t *q, int id);

int queue_size(const queue_t *q);

/* NULL if not found. Owned by the queue; do not free. */
const char *queue_peek_name(const queue_t *q, int id);

void queue_destroy(queue_t *q);

#endif
