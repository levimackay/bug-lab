#include <stdlib.h>
#include <string.h>

#include "queue.h"

typedef struct job_node {
    int id;
    char *name;
    struct job_node *next;
} job_node_t;

struct queue {
    job_node_t *head;
    int count;
};

queue_t *queue_create(void) {
    queue_t *q = calloc(1, sizeof(queue_t));
    return q;
}

int queue_push(queue_t *q, int id, const char *name) {
    job_node_t *node = malloc(sizeof(job_node_t));
    if (!node) {
        return -1;
    }
    node->name = strdup(name);
    if (!node->name) {
        free(node);
        return -1;
    }
    node->id = id;
    node->next = q->head;
    q->head = node;
    q->count++;
    return 0;
}

int queue_remove(queue_t *q, int id) {
    job_node_t *prev = NULL;
    job_node_t *node = q->head;
    while (node) {
        if (node->id == id) {
            if (prev) {
                prev->next = node->next;
            } else {
                q->head = node->next;
            }
            free(node->name);
            q->count--;
            return 1;
        }
        prev = node;
        node = node->next;
    }
    return 0;
}

int queue_size(const queue_t *q) {
    return q->count;
}

const char *queue_peek_name(const queue_t *q, int id) {
    for (job_node_t *node = q->head; node; node = node->next) {
        if (node->id == id) {
            return node->name;
        }
    }
    return NULL;
}

void queue_destroy(queue_t *q) {
    job_node_t *node = q->head;
    while (node) {
        job_node_t *next = node->next;
        free(node->name);
        free(node);
        node = next;
    }
    free(q);
}
