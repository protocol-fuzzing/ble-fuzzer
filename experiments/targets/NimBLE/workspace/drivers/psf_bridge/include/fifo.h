#pragma once

#include <stdint.h>


struct fifo {
    uint16_t capacity;
    uint16_t size;
    uint16_t tail;
    uint8_t *buf;
};

#define FIFO_CREATE(name, cap) \
    uint8_t name ## _buf[cap]; \
    struct fifo name = {.capacity = cap, .size = 0, .tail = 0, .buf = name ## _buf};


#define __fifo_tail_offset(f, o) (((f)->tail + o) % (f)->capacity)

#define __fifo_head_pos(f) __fifo_tail_offset(f, (f)->size)

#define fifo_get_capacity(f) ((f)->capacity)

#define fifo_get_size(f) ((f)->size)

#define fifo_is_full(f) (fifo_get_capacity(f) == fifo_get_size(f))

#define fifo_is_empty(f) (fifo_get_size(f) == 0)

#define fifo_has_space(f, n) ((fifo_get_capacity(f) - fifo_get_size(f)) >= n)

#define fifo_peek(f, offset) ((f)->buf[__fifo_tail_offset(f, offset)])

static inline void fifo_add_byte(struct fifo *f, uint8_t c) {
    f->buf[__fifo_head_pos(f)] = c;
    f->size++;
}

static inline void fifo_add_buf(struct fifo *f, const uint8_t *data, uint16_t size) {
    for(int i = 0; i < size; i++) {
        fifo_add_byte(f, data[i]);
    }
}

static inline uint8_t fifo_get_byte(struct fifo *f) {
    uint8_t c = f->buf[f->tail];
    f->tail = __fifo_tail_offset(f, 1);
    f->size--;
    return c;
}

static inline void fifo_get_buf(struct fifo *f, uint8_t *data, uint16_t size) {
    for(int i = 0; i < size; i++) {
        data[i] = fifo_get_byte(f);
    }
}
