#include <stdint.h>
#include <assert.h>
#include <string.h>
#include <stdlib.h>
#include <stdbool.h>
#include "syscfg/syscfg.h"
#include "os/os.h"
#include "nimble/ble.h"
#include "nimble/nimble_opt.h"
#include "controller/ble_hw.h"
#include "tinycrypt/aes.h"


static ble_rng_isr_cb_t rng_cb;
static bool rng_started;
static struct tc_aes_key_sched_struct g_ctx;


// Returns the public device address
int ble_hw_get_public_addr(ble_addr_t *addr) {
    static const ble_addr_t public_addr = {
        .type = BLE_ADDR_PUBLIC,
        .val = {0x66, 0x55, 0x44, 0x33, 0x22, 0x11}
    };
    memcpy(addr, &public_addr, sizeof(public_addr));
    return 0;
}

// No random static address available
int ble_hw_get_static_addr(ble_addr_t *addr) {
    return -1;
}

void ble_hw_whitelist_clear() {}

// We're not using whitelists, pretend it's full
int ble_hw_whitelist_add(const uint8_t *addr, uint8_t addr_type) {
    printf("ble_hw_whitelist_add\n");
    return BLE_ERR_MEM_CAPACITY;
}

void ble_hw_whitelist_rmv(const uint8_t *addr, uint8_t addr_type) {}

uint8_t ble_hw_whitelist_size() {
    return 0;
}

void ble_hw_whitelist_enable() {}

void ble_hw_whitelist_disable() {}

int ble_hw_whitelist_match() {
    return 0;
}

// Encrypt some data
int ble_hw_encrypt_block(struct ble_encryption_block *ecb) {
    printf("ble_hw_encrypt_block\n");
    tc_aes128_set_encrypt_key(&g_ctx, ecb->key);
    tc_aes_encrypt(ecb->cipher_text, ecb->plain_text, &g_ctx);
    return 0;
}

// Initialize RNG
int ble_hw_rng_init(ble_rng_isr_cb_t cb, int bias) {
    printf("ble_hw_rng_init\n");
    rng_cb = cb;
    return 0;
}

// Start generating random values
int ble_hw_rng_start() {
    printf("ble_hw_rng_start\n");
    rng_started = true;
    if (rng_cb) {
        while(rng_started) {
            rng_cb(rand());
        }
    }
    return 0;
}

// Stop generating random values
int ble_hw_rng_stop() {
    printf("ble_hw_rng_stop\n");
    rng_started = false;
    return 0;
}

// Return a single random number
uint8_t ble_hw_rng_read() {
    printf("ble_hw_rng_read\n");
    return rand();
}


#if MYNEWT_VAL(BLE_LL_CFG_FEAT_LL_PRIVACY)

void ble_hw_resolv_list_clear() {}

int ble_hw_resolv_list_add(uint8_t *irk) {
    printf("ble_hw_resolv_list_add\n");
    return BLE_ERR_MEM_CAPACITY;
}

void ble_hw_resolv_list_rmv(int index) {}

uint8_t ble_hw_resolv_list_size() {
    return 0;
}

int ble_hw_resolv_list_match() {
    return -1;
}

#endif
