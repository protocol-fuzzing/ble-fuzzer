#ifndef SERVER_COMMON_H_
#define SERVER_COMMON_H_

extern uint8_t const profile_data[];

void packet_handler(uint8_t packet_type, uint16_t channel, uint8_t *packet, uint16_t size);

#endif
