#include <stdint.h>
#include <string.h>
#include <assert.h>
#include <unistd.h>
#include "syscfg/syscfg.h"
#include "os/os.h"
#include "nimble/ble.h"
#include "nimble/nimble_opt.h"
#include "controller/ble_phy.h"
#include "controller/ble_ll.h"
#include "controller/ble_ll_conn.h"
#include "controller/ble_ll_ctrl.h"
#include "controller/ble_ll_tmr.h"
#include "uart/uart.h"
#include "fifo.h"
#include "tinycrypt/ccm_mode.h"
#include "tinycrypt/constants.h"


#ifndef min
#define min(a, b) ((a) < (b) ? (a) : (b))
#endif


void print_pkt(const uint8_t *pkt, uint16_t len, bool is_incoming, bool is_accepted);
void phy_task_recv_func(void *arg);
static void recv_packet(struct os_event *ev);
static int ble_phy_uart_tx_char(void *arg);
static int ble_phy_uart_rx_char(void *arg, uint8_t byte);


// Misc driver state
int8_t  phy_txpwr_dbm;
uint8_t phy_chan;
uint8_t phy_state;
uint32_t phy_access_address;
uint8_t rx_sn;
uint8_t rx_nesn;
ble_phy_tx_end_func txend_cb;
void *txend_arg;
struct ble_mbuf_hdr rx_hdr;
uint8_t ll_state;
volatile bool sent_non_empty_pkt = false;

// Encryption settings
bool enc_enabled = false;
uint8_t enc_key[16];
uint8_t enc_iv[8];
uint64_t enc_counter;

// UART buffers
struct uart_dev *uart_dev = NULL;
FIFO_CREATE(serial_tx_buf, 1024);
FIFO_CREATE(serial_rx_buf, 1024);
volatile bool uart_is_connected = false;

// Task for packet reception
struct os_task phy_task_recv;
#define PHY_TASK_RECV_STACK_SIZE 4096
os_stack_t phy_task_recv_stack[PHY_TASK_RECV_STACK_SIZE];
static struct os_eventq phy_task_recv_evq;
static struct os_event ev_recv_packet = {.ev_cb = recv_packet};


// We need to check if g_ble_ll_data.ll_state is set before
// forwarding packets to the link layer. Otherwise, we risk
// getting stuck. This is a workaround. Should probably be
// solved in a different way...
extern struct ble_ll_obj g_ble_ll_data;

// The BLE controller uses a 40s timer to kill the connection if
// certain procedures time out. This is very useful for PSF because
// we can end up in a situation where we're no longer able to communicate
// with the SUT (crypto key mismatch) and this will do the reset for us.
// However, we don't want to wait 40s, so we use this little function to
// change the timeout to 5s after every incoming message from the learner.
extern struct ble_ll_conn_sm *g_ble_ll_conn_cur_sm;
void refresh_rsp_timer() {
    if(g_ble_ll_conn_cur_sm && os_callout_remaining_ticks(&g_ble_ll_conn_cur_sm->ctrl_proc_rsp_timer.co, os_time_get()) > 0) {
        os_callout_reset(&g_ble_ll_conn_cur_sm->ctrl_proc_rsp_timer.co, os_time_ms_to_ticks32(5000));
    }
}

// The BLE controller schedules some radio timing related events internally.
// With the PSF-bridge driver we're not paying attention to any timing at all,
// which breaks something in the controller. This is a monkey patch that just
// makes sure that things get scheduled in the future (not in the past).
// I can't say that I really understand any of this, but it seems to work well
// enough to run our tests.
static int preempt_any(struct ble_ll_sched_item *sch, struct ble_ll_sched_item *item) {
    return 1;
}
int __wrap_ble_ll_sched_conn_reschedule(struct ble_ll_conn_sm *connsm) {
    connsm->conn_sch.start_time = ble_ll_tmr_get() + 100;
    connsm->conn_sch.end_time = connsm->conn_sch.start_time + 164;
    os_sr_t sr;
    OS_ENTER_CRITICAL(sr);
    int rc = ble_ll_sched_insert(&connsm->conn_sch, 0, preempt_any);
    OS_EXIT_CRITICAL(sr);
    ble_ll_sched_restart();
    return rc;
}


// For some reason, this function is called twice
int ble_phy_init() {
    printf("ble_phy_init\n");
    phy_state = BLE_PHY_STATE_IDLE;
    phy_chan = BLE_PHY_NUM_CHANS;

    // Open the serial interface
    if(!uart_dev) {
        struct uart_conf uc = {
            .uc_speed = 115200,
            .uc_databits = 8,
            .uc_stopbits = 1,
            .uc_parity = UART_PARITY_NONE,
            .uc_flow_ctl = UART_FLOW_CTL_NONE,
            .uc_tx_char = ble_phy_uart_tx_char,
            .uc_rx_char = ble_phy_uart_rx_char,
        };
        uart_dev = uart_open("uart1", &uc);
    }

    // Set up the task responsible for receiving packets
    if(!phy_task_recv.t_func) {
        os_eventq_init(&phy_task_recv_evq);
        os_task_init(&phy_task_recv, "phy_task_recv", phy_task_recv_func, NULL, 20,
            OS_WAIT_FOREVER, phy_task_recv_stack, PHY_TASK_RECV_STACK_SIZE);
    }

    return 0;
}


// Task responsible for receiving packets
void phy_task_recv_func(void *arg) {
    while (1) {
        os_eventq_run(&phy_task_recv_evq);
    }
}

// Peeks at the content in the fifo and if it finds a complete
// packet, it returns its length (without cmd, length and checksum).
uint16_t fifo_get_pkt_len(struct fifo *f) {
    if(fifo_get_size(f) > 3) {
        assert(fifo_peek(f, 0) == 0xA7);
        uint16_t btle_pkt_len = fifo_peek(f, 1) + (fifo_peek(f, 2) << 8);
        if(fifo_get_size(f) >= (1 + 2 + btle_pkt_len + 1)) { // cmd + length + btle pkt + checksum
            return btle_pkt_len;
        }
    }
    return 0;
}

static void recv_packet(struct os_event *ev) {
    printf("========= recv_packet =========\n");
    bool is_adv_chan_pkt = false;
    uint8_t rx_buf[260];
    uint32_t rx_buf_len;

    // If we got a complete packet in the fifo, read it
    while((rx_buf_len = fifo_get_pkt_len(&serial_rx_buf))) {
        // Ignore the first 3 bytes and the last checksum byte
        fifo_get_buf(&serial_rx_buf, rx_buf, 3);
        fifo_get_buf(&serial_rx_buf, rx_buf, rx_buf_len);
        fifo_get_byte(&serial_rx_buf);

        // Decrypt the packet if necessary
        bool crypto_ok = true;
        if(enc_enabled && rx_buf_len > 10 && rx_buf[5] > 0) {
            // Create the nonce
            uint8_t nonce[13];
            memcpy(nonce, &enc_counter, 5);
            nonce[4] |= 0x80;
            memcpy(&nonce[5], enc_iv, 8);
            // Decrypt the packet
            uint8_t aad = rx_buf[4] & 0xE3; // ll header flags (with mask)
            uint16_t cipher_len = rx_buf_len - 6; // access address and ll header are not encrypted
            uint8_t plain[cipher_len - 4];
            struct tc_aes_key_sched_struct sched;
            struct tc_ccm_mode_struct ccm;
            tc_aes128_set_encrypt_key(&sched, enc_key);
            tc_ccm_config(&ccm, &sched, nonce, sizeof(nonce), 4);
            int ret = tc_ccm_decryption_verification(plain, sizeof(plain), &aad, 1, &rx_buf[6], cipher_len, &ccm);
            crypto_ok = (ret == TC_CRYPTO_SUCCESS);
            memcpy(&rx_buf[6], plain, cipher_len - 4);
            rx_buf[5] -= 4; // remove tag from the ll payload length
            rx_buf_len -= 4;
        }

        // Decide whether to accept the packet
        is_adv_chan_pkt = *((uint32_t *) &rx_buf[0]) == 0x8e89bed6;
        bool accept = ((phy_chan >= 37 && is_adv_chan_pkt) || (phy_chan < 37 && !is_adv_chan_pkt));
        if(accept) {
            refresh_rsp_timer();
        } else {
            print_pkt(rx_buf, rx_buf_len, true, accept);
            rx_buf_len = 0;
            crypto_ok = true;
        }

        // Debugging some problem that occurs after around 20h of testing.
        // If we previously sent a valid CONNECT_IND, we should be on a data channel.
        // Otherwise, something is fishy and we can't continue.
        static bool last_msg_was_conn = false;
        if(last_msg_was_conn && phy_chan >= 37) {
            printf("BUG: NOT ON DATA CHANNEL AFTER CONNECT_IND\n");
            printf("(debug this or restart the SUT and continue testing)\n");
            sleep(1000000);
        }
        if(is_adv_chan_pkt && (rx_buf[4] & BLE_ADV_PDU_HDR_TYPE_MASK) == BLE_ADV_PDU_TYPE_CONNECT_IND && accept) {
            last_msg_was_conn = true;
        } else {
            last_msg_was_conn = false;
        }

        for(int i_pkt = 0; i_pkt < 6; i_pkt++) {
            // After any incoming packet, accepted or not, we send empty packets
            // if we're on a data channel. This is to simulate the mechanism that
            // keeps the connection alive and allows the NimBLE stack to return
            // multiple Bluetooth packets. PSF is not aware of this as this is
            // usually handled by the dongle firmware.
            if(!rx_buf_len && phy_chan < 37) {
                // Simulate an empty data packet
                memcpy(rx_buf, &phy_access_address, 4);
                rx_buf[4] = 0x01; // ll header flags
                rx_buf[5] = 0x00; // ll header length
                rx_buf_len = 6;
                is_adv_chan_pkt = false;
            }

            // If we have something, send it to the ble stack
            int rc;
            if(rx_buf_len) {
                if(!is_adv_chan_pkt) {
                    // Fix sn/nesn
                    rx_buf[4] = (rx_buf[4] & 0xf3) | (rx_sn << 3) | (rx_nesn << 2);
                }
                print_pkt(rx_buf, rx_buf_len, true, true);
                memset(&rx_hdr, 0, sizeof(rx_hdr));
                rc = ble_ll_rx_start(&rx_buf[4], phy_chan, &rx_hdr); // skip the access address
                if(rc >= 0) {
                    rx_hdr.rxinfo.rssi = 0;
                    rx_hdr.rxinfo.channel = phy_chan;
                    rx_hdr.rxinfo.phy = BLE_PHY_1M;
                    rx_hdr.rxinfo.flags |= BLE_MBUF_HDR_F_CRC_OK | ll_state | (!crypto_ok ? BLE_MBUF_HDR_F_MIC_FAILURE : 0);
                    ble_ll_rx_end(&rx_buf[4], &rx_hdr);
                } else {
                    printf("PDU rejected for some reason\n");
                }
                rx_buf_len = 0;
            }

            // Sleep a little before sending the next packet. This allows the
            // scheduler to schedule the tasks that send a response. Typically,
            // we should be able to read the whole response to a request by
            // sending 5 subsequent empty packets (and reading their responses).
            // But there are exceptions where the system can respond with more
            // packets (e.g. when packets are queued after multiple LL_CTRL_PAUSE_ENC_REQ
            // are sent in sequence). To handle this more dynamically, we check
            // if a non-empty packet was returned after the current request and
            // if so, reset the loop counter. This should ensure that we keep
            // receiving as long as there is data, plus 5 empty packets.

            // Another task is also responsible for resetting g_ble_ll_data.ll_state.
            // We want to make sure to sleep long enough until this happens.
            // If that variable is not reset, no new packets will be accepted,
            // which becomes very problematic when a CONNECT_IND is rejected.
            
            os_time_delay(OS_TICKS_PER_SEC / 50); // 20ms
            int sleep_ms = 20;
            for(; rc >= 0 && sleep_ms < 200 && (g_ble_ll_data.ll_state == 0); sleep_ms += 10) {
                os_time_delay(OS_TICKS_PER_SEC / 100); // 10ms
            }
            if(g_ble_ll_data.ll_state == 0) {
                printf("WARNING: ll_state == 0, despite %d ms sleep\n", sleep_ms);
            }

            if(sent_non_empty_pkt) {
                sent_non_empty_pkt = false;
                i_pkt = 0;
            }
        }
    }
}


void print_pkt(const uint8_t *pkt, uint16_t len, bool is_incoming, bool is_accepted) {
    const char *dir = is_incoming ? "<-" : "->";

    bool is_adv_chan_pkt = *((uint32_t *) &pkt[0]) == 0x8e89bed6;
    char *msg_desc = "UNKN  ";
    if(is_adv_chan_pkt && (pkt[4] & BLE_ADV_PDU_HDR_TYPE_MASK) == BLE_ADV_PDU_TYPE_ADV_IND) {
        msg_desc = "ADVI  ";
    } else if(is_adv_chan_pkt && (pkt[4] & BLE_ADV_PDU_HDR_TYPE_MASK) == BLE_ADV_PDU_TYPE_SCAN_REQ) {
        msg_desc = "SCAN  ";
    } else if(is_adv_chan_pkt && (pkt[4] & BLE_ADV_PDU_HDR_TYPE_MASK) == BLE_ADV_PDU_TYPE_CONNECT_IND) {
        msg_desc = "CONN  ";
    } else if(is_adv_chan_pkt && (pkt[4] & BLE_ADV_PDU_HDR_TYPE_MASK) == BLE_ADV_PDU_TYPE_SCAN_RSP) {
        msg_desc = "SCAN_R";
    } else if(!is_adv_chan_pkt && len == 6 && pkt[5] == 0) {
        msg_desc = "EMTY  ";
    } else if(!is_adv_chan_pkt && pkt[6] == 0x02) {
        msg_desc = "TERM  ";
    } else if(!is_adv_chan_pkt && pkt[6] == 0x03) {
        msg_desc = "ENC   ";
    } else if(!is_adv_chan_pkt && pkt[6] == 0x04) {
        msg_desc = "ENC_R ";
    } else if(!is_adv_chan_pkt && pkt[6] == 0x05) {
        msg_desc = "SENC  ";
    } else if(!is_adv_chan_pkt && pkt[6] == 0x06) {
        msg_desc = "SENC_R";
    } else if(!is_adv_chan_pkt && pkt[6] == 0x07) {
        msg_desc = "UNKN_R";
    } else if(!is_adv_chan_pkt && pkt[6] == 0x08) {
        msg_desc = "FEAT  ";
    } else if(!is_adv_chan_pkt && pkt[6] == 0x09) {
        msg_desc = "FEAT_R";
    } else if(!is_adv_chan_pkt && pkt[6] == 0x0a) {
        msg_desc = "PAUS  ";
    } else if(!is_adv_chan_pkt && pkt[6] == 0x0b) {
        msg_desc = "PAUS_R";
    } else if(!is_adv_chan_pkt && pkt[6] == 0x0d) {
        msg_desc = "REJT  ";
    } else if(!is_adv_chan_pkt && pkt[6] == 0x0e) {
        msg_desc = "SLFT  ";
    } else if(!is_adv_chan_pkt && len > 10 && (pkt[4] & 0b11) == 0b10 && pkt[8] == 0x06 && pkt[10] == 0x01) {
        msg_desc = "PAIR  ";
    } else if(!is_adv_chan_pkt && len > 10 && (pkt[4] & 0b11) == 0b10 && pkt[8] == 0x06 && pkt[10] == 0x02) {
        msg_desc = "PAIR_R";
    } else if(!is_adv_chan_pkt && len > 10 && (pkt[4] & 0b11) == 0b10 && pkt[8] == 0x06 && pkt[10] == 0x03) {
        msg_desc = "CONF  ";
    } else if(!is_adv_chan_pkt && len > 10 && (pkt[4] & 0b11) == 0b10 && pkt[8] == 0x06 && pkt[10] == 0x04) {
        msg_desc = "RAND  ";
    } else if(!is_adv_chan_pkt && len > 10 && (pkt[4] & 0b11) == 0b10 && pkt[8] == 0x06 && pkt[10] == 0x05) {
        msg_desc = "FAIL  ";
    } else if(!is_adv_chan_pkt) {
        msg_desc = "DATA  ";
    }
    
    char *accept_str = "   ";
    if(is_incoming && is_accepted) {
        accept_str = " OK";
    } else if(is_incoming && !is_accepted) {
        accept_str = "NOK";
    }

    printf("%s [ch %02hhu %s %s]", dir, phy_chan, msg_desc, accept_str);
    for (int i = 0; i < len; i++) {
        printf(" %02x", pkt[i]);
    }
    printf("\n");
}


// UART packet format recv:
// 0xA7 <2 bytes BTLE len LE> <BTLE packet with access address without crc>

// UART packet format send:
// <0xA7/0xBB> <2 bytes BTLE len LE> <2 bytes event counter LE, unused> <BTLE packet with access address> <checksum, sum of BTLE>
// 0xA7: actually sent packet, 0xBB: simulated received packet to be logged

// Link layer packet format:
// <BTLE packet without access address>

static int ble_phy_uart_tx_char(void *arg) {
    if(fifo_is_empty(&serial_tx_buf)) {
        return -1;
    }
    return fifo_get_byte(&serial_tx_buf);
}


static int ble_phy_uart_rx_char(void *arg, uint8_t byte) {
    static uint32_t pkt_count = 0;
    pkt_count++;
    if(pkt_count == 1) {
        // The first byte is the config-log-tx command
        assert(byte == 0xCC);
    } else if(pkt_count == 2) {
        // The second byte is the config value.
        // It's irrelevant for us, but we know we have a valid connection
        // and there'll only come ble packets afterwards.
        uart_is_connected = true;
    } else {
        // Everything after that just goes straight into the rx buffer
        assert(!fifo_is_full(&serial_rx_buf));
        fifo_add_byte(&serial_rx_buf, byte);
        if(fifo_get_pkt_len(&serial_rx_buf)) {
            os_eventq_put(&phy_task_recv_evq, &ev_recv_packet);
        }
    }
    return 0;
}


// Copies the data from the phy receive buffer into an mbuf chain.
// This function was copied from mynewt-nimble/nimble/drivers/native/src/ble_phy.c
// It seems unnecessarily complex and I don't understand why it's
// in the driver, but it seems to work, so I'm not messing with it.
void ble_phy_rxpdu_copy(uint8_t *dptr, struct os_mbuf *rxpdu) {
    //printf("ble_phy_rxpdu_copy\n");
    uint16_t rem_bytes;
    uint16_t mb_bytes;
    uint16_t copylen;
    uint32_t *dst;
    uint32_t *src;
    struct os_mbuf *m;
    struct ble_mbuf_hdr *ble_hdr;
    struct os_mbuf_pkthdr *pkthdr;

    pkthdr = OS_MBUF_PKTHDR(rxpdu);
    rem_bytes = pkthdr->omp_len;

    /* Fill in the mbuf pkthdr first. */
    dst = (uint32_t *)(rxpdu->om_data);
    src = (uint32_t *)dptr;

    mb_bytes = (rxpdu->om_omp->omp_databuf_len - rxpdu->om_pkthdr_len - 4);
    copylen = min(mb_bytes, rem_bytes);
    copylen &= 0xFFFC;
    rem_bytes -= copylen;
    mb_bytes -= copylen;
    rxpdu->om_len = copylen;
    while (copylen > 0) {
        *dst = *src;
        ++dst;
        ++src;
        copylen -= 4;
    }

    /* Copy remaining bytes */
    m = rxpdu;
    while (rem_bytes > 0) {
        /* If there are enough bytes in the mbuf, copy them and leave */
        if (rem_bytes <= mb_bytes) {
            memcpy(m->om_data + m->om_len, src, rem_bytes);
            m->om_len += rem_bytes;
            break;
        }

        m = SLIST_NEXT(m, om_next);
        assert(m != NULL);

        mb_bytes = m->om_omp->omp_databuf_len;
        copylen = min(mb_bytes, rem_bytes);
        copylen &= 0xFFFC;
        rem_bytes -= copylen;
        mb_bytes -= copylen;
        m->om_len = copylen;
        dst = (uint32_t *)m->om_data;
        while (copylen > 0) {
            *dst = *src;
            ++dst;
            ++src;
            copylen -= 4;
        }
    }

    /* Copy ble header */
    ble_hdr = BLE_MBUF_HDR_PTR(rxpdu);
    memcpy(ble_hdr, &rx_hdr, sizeof(struct ble_mbuf_hdr));
}



// Called from the NimBLE stack when it wants to transmit a packet
int ble_phy_tx(ble_phy_tx_pducb_t pducb, void *pducb_arg, uint8_t end_trans) {
    phy_state = BLE_PHY_STATE_TX;

    // Get the tx pdu
    uint8_t hdr_byte;
    uint8_t tx_buf[512];
    uint16_t ll_payload_len = pducb(&tx_buf[6], pducb_arg, &hdr_byte);

    // Extract sn/nesn (doesn't matter in case this is an advertisement)
    if(phy_chan < 37) { 
        rx_sn = !!(hdr_byte & BLE_LL_DATA_HDR_NESN_MASK);
        rx_nesn = !!(hdr_byte & BLE_LL_DATA_HDR_SN_MASK) ^ 1;
    }

    // If a non-empty packet is sent, notify the receiver side
    // to keep simulating recevining empty packets
    if(ll_payload_len > 0) {
        sent_non_empty_pkt = true;
    }

    // Encrypt the payload
    if(enc_enabled && ll_payload_len > 0) {
        // Create the nonce
        uint8_t nonce[13];
        memcpy(nonce, &enc_counter, 5);
        nonce[4] &= 0x7F;
        memcpy(&nonce[5], enc_iv, 8);
        // Encrypt the packet
        uint8_t aad = hdr_byte & 0xE3; // ll header flags (with mask)
        uint16_t cipher_len = ll_payload_len + 4; // the 4 tag bytes get appended
        uint8_t cipher[cipher_len];
        struct tc_aes_key_sched_struct sched;
        struct tc_ccm_mode_struct ccm;
        tc_aes128_set_encrypt_key(&sched, enc_key);
        tc_ccm_config(&ccm, &sched, nonce, sizeof(nonce), 4);
        tc_ccm_generation_encryption(cipher, cipher_len, &aad, 1, &tx_buf[6], ll_payload_len, &ccm);
        memcpy(&tx_buf[6], cipher, cipher_len);
        ll_payload_len += 4;
    }

    // Add the header and crc
    uint16_t btle_pkt_len = 4 + 2 + ll_payload_len + 3; // access address + ll header + payload (with tag if encrypted) + crc
    tx_buf[0] = (uint8_t) (phy_access_address & 0xFF); // access address
    tx_buf[1] = (uint8_t) ((phy_access_address >> 8) & 0xFF); // access address
    tx_buf[2] = (uint8_t) ((phy_access_address >> 16) & 0xFF); // access address
    tx_buf[3] = (uint8_t) ((phy_access_address >> 24) & 0xFF); // access address
    tx_buf[4] = hdr_byte; // ll header (flags)
    tx_buf[5] = ll_payload_len; // ll header (length)
    tx_buf[btle_pkt_len - 3] = 0; // crc (fake, not checked)
    tx_buf[btle_pkt_len - 2] = 0; // crc (fake, not checked)
    tx_buf[btle_pkt_len - 1] = 0; // crc (fake, not checked)

    // Calculate the checksum
    uint8_t checksum = 0;
    for(int i = 0; i < btle_pkt_len; i++) {
        checksum += tx_buf[i];
    }

    // Write cmd header, ll header, payload, crc, checksum to the serial transmit buffer
    assert(fifo_has_space(&serial_tx_buf, 5 + btle_pkt_len + 1));
    fifo_add_byte(&serial_tx_buf, 0xA7); // cmd
    fifo_add_byte(&serial_tx_buf, (uint8_t) (btle_pkt_len & 0xFF)); // btle pkt length low
    fifo_add_byte(&serial_tx_buf, (uint8_t) ((btle_pkt_len >> 8) & 0xFF)); // btle pkt length high
    fifo_add_byte(&serial_tx_buf, 0); // event counter low, unused
    fifo_add_byte(&serial_tx_buf, 0); // event counter high, unused
    fifo_add_buf(&serial_tx_buf, tx_buf, btle_pkt_len); // btle packet
    fifo_add_byte(&serial_tx_buf, checksum); // checksum
    uart_start_tx(uart_dev);

    print_pkt(tx_buf, btle_pkt_len, false, true);

    // Notify NimBLE that we sent the packet
    if(txend_cb) {
        txend_cb(txend_arg);
    }
    
    return 0;
}


int ble_phy_rx() {
    phy_state = BLE_PHY_STATE_RX;
    return 0;
}

void ble_phy_restart_rx() {}

void ble_phy_encrypt_enable(const uint8_t *key) {
    printf("ble_phy_encrypt_enable: ");
    for(int i = 0; i < 16; i++) {
        printf("%02x", key[i]);
    }
    printf("\n");
    memcpy(enc_key, key, 16);
    enc_enabled = true;
}

void ble_phy_encrypt_header_mask_set(uint8_t mask) {}

void ble_phy_encrypt_iv_set(const uint8_t *iv) {
    printf("ble_phy_encrypt_iv_set: ");
    for(int i = 0; i < 8; i++) {
        printf("%02x", iv[i]);
    }
    printf("\n");
    memcpy(enc_iv, iv, 8);
}

void ble_phy_encrypt_counter_set(uint64_t counter, uint8_t dir_bit) {
    //printf("ble_phy_encrypt_counter_set: %lu (%hhu)\n", counter, dir_bit);
    enc_counter = counter;
}

void ble_phy_encrypt_disable() {
    printf("ble_phy_encrypt_disable\n");
    enc_enabled = false;
}

void ble_phy_set_txend_cb(ble_phy_tx_end_func cb, void *arg) {
    txend_cb = cb;
    txend_arg = arg;
}

int ble_phy_tx_set_start_time(uint32_t cputime, uint8_t rem_usecs) {
    return 0;
}

int ble_phy_rx_set_start_time(uint32_t cputime, uint8_t rem_usecs) {
    return 0;
}

int ble_phy_tx_power_set(int dbm) {
    phy_txpwr_dbm = dbm;
    return 0;
}

int ble_phy_tx_power_round(int dbm) {
    return dbm;
}

int ble_phy_tx_power_get(void) {
    return phy_txpwr_dbm;
}

void ble_phy_set_rx_pwr_compensation(int8_t compensation) {}

int ble_phy_setchan(uint8_t chan, uint32_t access_addr, uint32_t crcinit) {
    printf("ble_phy_setchan: chan %hhu, access_addr %04x\n", chan, access_addr);
    phy_access_address = access_addr;
    phy_chan = chan;
    if(chan == 37 || chan == 38 || chan == 39) {
        ll_state = BLE_LL_STATE_ADV;
    } else {
        ll_state = BLE_LL_STATE_CONNECTION;
    }
    return 0;
}

uint8_t ble_phy_chan_get() {
    return phy_chan;
}

void ble_phy_disable() {
    phy_state = BLE_PHY_STATE_IDLE;
}

uint32_t ble_phy_access_addr_get() {
    return phy_access_address;
}

int ble_phy_state_get() {
    return phy_state;
}

int ble_phy_rx_started() {
    return 0;
}

uint8_t ble_phy_max_data_pdu_pyld() {
    return BLE_LL_DATA_PDU_MAX_PYLD;
}

void ble_phy_resolv_list_enable() {}

void ble_phy_resolv_list_disable() {}

uint8_t ble_phy_xcvr_state_get() {
    return phy_state;
}

void ble_phy_wfr_enable(int txrx, uint8_t tx_phy_mode, uint32_t wfr_usecs) {}

void ble_phy_rfclk_enable() {}

void ble_phy_rfclk_disable() {}

void ble_phy_tifs_txtx_set(uint16_t usecs, uint8_t anchor) {}
