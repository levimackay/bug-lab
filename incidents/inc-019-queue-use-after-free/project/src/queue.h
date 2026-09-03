#ifndef QUEUE_H
#define QUEUE_H

#define MQ_PAYLOAD_LEN 128

typedef struct message_queue message_queue_t;

message_queue_t *mq_create(void);

/* Copies payload (truncated to fit) onto the tail of the queue. Returns 0
 * on success, -1 on allocation failure. */
int mq_push(message_queue_t *q, const char *payload);

/* Dequeues the oldest message and returns a heap copy of its payload. The
 * caller owns it and must free() it. Returns NULL if the queue is empty. */
char *mq_pop(message_queue_t *q);

int mq_size(const message_queue_t *q);

void mq_destroy(message_queue_t *q);

#endif
