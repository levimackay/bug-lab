#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "queue.h"

typedef struct mq_node {
    char payload[MQ_PAYLOAD_LEN];
    struct mq_node *next;
} mq_node_t;

struct message_queue {
    mq_node_t *head;
    mq_node_t *tail;
    int count;
};

message_queue_t *mq_create(void) {
    return calloc(1, sizeof(message_queue_t));
}

int mq_push(message_queue_t *q, const char *payload) {
    mq_node_t *node = malloc(sizeof(mq_node_t));
    if (!node) {
        return -1;
    }
    snprintf(node->payload, MQ_PAYLOAD_LEN, "%s", payload);
    node->next = NULL;
    if (q->tail) {
        q->tail->next = node;
    } else {
        q->head = node;
    }
    q->tail = node;
    q->count++;
    return 0;
}

char *mq_pop(message_queue_t *q) {
    if (!q->head) {
        return NULL;
    }
    mq_node_t *node = q->head;
    q->head = node->next;
    if (!q->head) {
        q->tail = NULL;
    }
    q->count--;

    char *payload = strdup(node->payload);
    free(node);
    return payload;
}

int mq_size(const message_queue_t *q) {
    return q->count;
}

void mq_destroy(message_queue_t *q) {
    mq_node_t *node = q->head;
    while (node) {
        mq_node_t *next = node->next;
        free(node);
        node = next;
    }
    free(q);
}
