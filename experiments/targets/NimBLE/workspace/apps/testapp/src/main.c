#include "bsp/bsp.h"
#include "config/config.h"
#include "console/console.h"
#include "hal/hal_gpio.h"
#include "hal/hal_system.h"
#include "host/ble_hs.h"
#include "host/ble_uuid.h"
#include "host/util/util.h"
#include "nimble/ble.h"
#include "os/mynewt.h"
#include "services/gap/ble_svc_gap.h"
#include "split/split.h"


#ifdef ARCH_sim
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include <errno.h>

// Global variable from the driver that indicates
// when is has got a uart connection.
// We should wait for that before starting advertising.
extern volatile bool uart_is_connected;
#else
#define printf(msg, ...) modlog_printf(LOG_MODULE_DEFAULT, LOG_LEVEL_INFO, msg, ##__VA_ARGS__)
#endif


static int bleprph_gap_event(struct ble_gap_event *event, void *arg);
static int gatt_svr_chr_access_button(uint16_t conn_handle, uint16_t attr_handle, struct ble_gatt_access_ctxt *ctxt, void *arg);
static void gatt_svr_register_cb(struct ble_gatt_register_ctxt *ctxt, void *arg);
static int gatt_svr_init(void);


static void print_addr(const uint8_t *addr) {
    const uint8_t *u8p = addr;
    printf("%02x:%02x:%02x:%02x:%02x:%02x",
                u8p[5], u8p[4], u8p[3], u8p[2], u8p[1], u8p[0]);
}

static void bleprph_print_conn_desc(struct ble_gap_conn_desc *desc) {
    printf("handle=%d our_ota_addr_type=%d our_ota_addr=", desc->conn_handle, desc->our_ota_addr.type);
    print_addr(desc->our_ota_addr.val);
    printf(" our_id_addr_type=%d our_id_addr=", desc->our_id_addr.type);
    print_addr(desc->our_id_addr.val);
    printf(" peer_ota_addr_type=%d peer_ota_addr=", desc->peer_ota_addr.type);
    print_addr(desc->peer_ota_addr.val);
    printf(" peer_id_addr_type=%d peer_id_addr=", desc->peer_id_addr.type);
    print_addr(desc->peer_id_addr.val);
    printf(" conn_itvl=%d conn_latency=%d supervision_timeout=%d encrypted=%d authenticated=%d bonded=%d\n",
                desc->conn_itvl, desc->conn_latency,
                desc->supervision_timeout,
                desc->sec_state.encrypted,
                desc->sec_state.authenticated,
                desc->sec_state.bonded);
}


static void bleprph_advertise(void) {
    uint8_t own_addr_type;
    struct ble_gap_adv_params adv_params;
    struct ble_hs_adv_fields fields;
    const char *name;

    // The BLE MAC address is provided by the driver
    int rc = ble_hs_id_infer_auto(0, &own_addr_type);
    if (rc != 0) {
        printf("error determining address type; rc=%d\n", rc);
        return;
    }

    memset(&fields, 0, sizeof(fields));
    fields.flags = BLE_HS_ADV_F_DISC_GEN | BLE_HS_ADV_F_BREDR_UNSUP;
    
    name = ble_svc_gap_device_name();
    fields.name = (uint8_t *)name;
    fields.name_len = strlen(name);
    fields.name_is_complete = 1;

    rc = ble_gap_adv_set_fields(&fields);
    if (rc != 0) {
        printf("error setting advertisement data; rc=%d\n", rc);
        return;
    }

    // Begin advertising
    memset(&adv_params, 0, sizeof adv_params);
    adv_params.conn_mode = BLE_GAP_CONN_MODE_UND;
    adv_params.disc_mode = BLE_GAP_DISC_MODE_GEN;
    rc = ble_gap_adv_start(own_addr_type, NULL, BLE_HS_FOREVER,
                           &adv_params, bleprph_gap_event, NULL);
    if (rc != 0) {
        printf("error enabling advertisement; rc=%d\n", rc);
        return;
    }
}



// This is called whenever anything with the connection changes
static int bleprph_gap_event(struct ble_gap_event *event, void *arg) {
    struct ble_gap_conn_desc desc;
    int rc;

    switch (event->type) {
    case BLE_GAP_EVENT_CONNECT:
        /* A new connection was established or a connection attempt failed. */
        printf("connection %s; status=%d ", event->connect.status == 0 ? "established" : "failed", event->connect.status);
        if (event->connect.status == 0) {
            rc = ble_gap_conn_find(event->connect.conn_handle, &desc);
            assert(rc == 0);
            bleprph_print_conn_desc(&desc);
        }
        printf("\n");

        if (event->connect.status != 0) {
            /* Connection failed; resume advertising. */
            bleprph_advertise();
        }
        return 0;

    case BLE_GAP_EVENT_DISCONNECT:
        printf("disconnect; reason=%d ", event->disconnect.reason);
        bleprph_print_conn_desc(&event->disconnect.conn);
        printf("\n");

        /* Connection terminated; resume advertising. */
        bleprph_advertise();
        return 0;

    case BLE_GAP_EVENT_CONN_UPDATE:
        /* The central has updated the connection parameters. */
        printf("connection updated; status=%d ", event->conn_update.status);
        rc = ble_gap_conn_find(event->conn_update.conn_handle, &desc);
        assert(rc == 0);
        bleprph_print_conn_desc(&desc);
        printf("\n");
        return 0;

    case BLE_GAP_EVENT_ADV_COMPLETE:
        printf("advertise complete; reason=%d\n", event->adv_complete.reason);
        //bleprph_advertise();
        return 0;

    case BLE_GAP_EVENT_ENC_CHANGE:
        /* Encryption has been enabled or disabled for this connection. */
        printf("encryption change event; status=%d ", event->enc_change.status);
        rc = ble_gap_conn_find(event->connect.conn_handle, &desc);
        assert(rc == 0);
        bleprph_print_conn_desc(&desc);
        printf("\n");
        return 0;

    case BLE_GAP_EVENT_SUBSCRIBE:
        printf("subscribe event; conn_handle=%d attr_handle=%d reason=%d prevn=%d curn=%d previ=%d curi=%d\n",
                    event->subscribe.conn_handle,
                    event->subscribe.attr_handle,
                    event->subscribe.reason,
                    event->subscribe.prev_notify,
                    event->subscribe.cur_notify,
                    event->subscribe.prev_indicate,
                    event->subscribe.cur_indicate);
        return 0;

    case BLE_GAP_EVENT_MTU:
        printf("mtu update event; conn_handle=%d cid=%d mtu=%d\n",
                    event->mtu.conn_handle,
                    event->mtu.channel_id,
                    event->mtu.value);
        return 0;

    case BLE_GAP_EVENT_REPEAT_PAIRING:
        /* We already have a bond with the peer, but it is attempting to
         * establish a new secure link.  This app sacrifices security for
         * convenience: just throw away the old bond and accept the new link.
         */

        /* Delete the old bond. */
        rc = ble_gap_conn_find(event->repeat_pairing.conn_handle, &desc);
        assert(rc == 0);
        ble_store_util_delete_peer(&desc.peer_id_addr);

        /* Return BLE_GAP_REPEAT_PAIRING_RETRY to indicate that the host should
         * continue with the pairing operation.
         */
        return BLE_GAP_REPEAT_PAIRING_RETRY;

    case BLE_GAP_EVENT_PASSKEY_ACTION:
        printf("passkey action event; action=%d\n", event->passkey.params.action);
        if (event->passkey.params.action == BLE_SM_IOACT_NUMCMP) {
            printf(" numcmp=%lu", (unsigned long)event->passkey.params.numcmp);
            struct ble_sm_io pk;
            pk.action = BLE_SM_IOACT_NUMCMP;
            pk.numcmp_accept = 1;
            int rc = ble_sm_inject_io(event->passkey.conn_handle, &pk);
            if (rc) {
                printf("ble_sm_inject_io failed to confirm passkey\n");
            }
        }
        return 0;
    }

    return 0;
}

static void bleprph_on_reset(int reason) {
    printf("Resetting state; reason=%d\n", reason);
}

static void bleprph_on_sync(void) {
    /* Make sure we have proper identity address set (public preferred) */
    int rc = ble_hs_util_ensure_addr(0);
    assert(rc == 0);
    /* Begin advertising. */
    bleprph_advertise();
}


int mynewt_main(int argc, char **argv) {
    /* Initialize OS */
    sysinit();

    /* Initialize the NimBLE host configuration. */
    ble_hs_cfg.reset_cb = bleprph_on_reset;
    ble_hs_cfg.sync_cb = bleprph_on_sync;
    ble_hs_cfg.gatts_register_cb = gatt_svr_register_cb;
    ble_hs_cfg.store_status_cb = ble_store_util_status_rr;

    ble_hs_cfg.sm_bonding = 0;
    ble_hs_cfg.sm_our_key_dist = 0; //BLE_SM_PAIR_KEY_DIST_ENC
    ble_hs_cfg.sm_their_key_dist = 0;
    // ble_hs_cfg.sm_bonding = 1;
    // ble_hs_cfg.sm_our_key_dist = 7; //BLE_SM_PAIR_KEY_DIST_ENC
    // ble_hs_cfg.sm_their_key_dist = 7;

    ble_hs_cfg.sm_sc = 1;
    ble_hs_cfg.sm_mitm = 1;
    ble_hs_cfg.sm_io_cap = BLE_SM_IO_CAP_DISP_YES_NO;

    int rc = gatt_svr_init();
    assert(rc == 0);

    conf_load();

#ifdef ARCH_sim
    printf("Waiting for UART connection...\n");
    while(!uart_is_connected) {
        os_time_delay(100);
    }
    printf("UART connected!\n");
#endif

    while (1) {
        os_eventq_run(os_eventq_dflt_get());
    }
    return 0;
}





// ========================================================
// GATT related functionality
// ========================================================


// 00001523-1212-efde-1523-785feabcd123
static const ble_uuid128_t gatt_svr_svc_lbs_uuid =
    BLE_UUID128_INIT(0x23, 0xd1, 0xbc, 0xea, 0x5f, 0x78, 0x23, 0x15,
                     0xde, 0xef, 0x12, 0x12, 0x23, 0x15, 0x00, 0x00);

// 00001524-1212-efde-1523-785feabcd123
static const ble_uuid128_t gatt_svr_chr_button_uuid =
    BLE_UUID128_INIT(0x23, 0xd1, 0xbc, 0xea, 0x5f, 0x78, 0x23, 0x15,
                     0xde, 0xef, 0x12, 0x12, 0x24, 0x15, 0x00, 0x00);

static const struct ble_gatt_svc_def gatt_svr_svcs[] = {
    {
        /*** Service: LBS. */
        .type = BLE_GATT_SVC_TYPE_PRIMARY,
        .uuid = &gatt_svr_svc_lbs_uuid.u,
        .characteristics = (struct ble_gatt_chr_def[]) { {
            /*** Characteristic: Button state. */
            .uuid = &gatt_svr_chr_button_uuid.u,
            .access_cb = gatt_svr_chr_access_button,
            .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_READ_ENC /*| BLE_GATT_CHR_F_READ_AUTHEN*/,
        }, {
            0, /* No more characteristics in this service. */
        } },
    }, {
        0, /* No more services. */
    },
};

static int gatt_svr_chr_access_button(uint16_t conn_handle, uint16_t attr_handle, struct ble_gatt_access_ctxt *ctxt, void *arg) {
    if (ble_uuid_cmp(ctxt->chr->uuid, &gatt_svr_chr_button_uuid.u) == 0) {
        assert(ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR);
        printf("Reading the button value!\n");
        const uint8_t button_val = 0;
        int rc = os_mbuf_append(ctxt->om, &button_val, sizeof(button_val));
        return rc == 0 ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
    }

    // Unknown characteristic
    assert(0);
    return BLE_ATT_ERR_UNLIKELY;
}

static void gatt_svr_register_cb(struct ble_gatt_register_ctxt *ctxt, void *arg) {
    char buf[BLE_UUID_STR_LEN];

    switch (ctxt->op) {
    case BLE_GATT_REGISTER_OP_SVC:
        printf("registered service %s with handle=%d\n", ble_uuid_to_str(ctxt->svc.svc_def->uuid, buf), ctxt->svc.handle);
        break;

    case BLE_GATT_REGISTER_OP_CHR:
        printf("registering characteristic %s with def_handle=%d val_handle=%d\n",
                    ble_uuid_to_str(ctxt->chr.chr_def->uuid, buf),
                    ctxt->chr.def_handle,
                    ctxt->chr.val_handle);
        break;

    case BLE_GATT_REGISTER_OP_DSC:
        printf("registering descriptor %s with handle=%d\n",
                    ble_uuid_to_str(ctxt->dsc.dsc_def->uuid, buf),
                    ctxt->dsc.handle);
        break;

    default:
        assert(0);
        break;
    }
}

static int gatt_svr_init() {
    int rc;

    rc = ble_gatts_count_cfg(gatt_svr_svcs);
    if (rc != 0) {
        return rc;
    }

    rc = ble_gatts_add_svcs(gatt_svr_svcs);
    if (rc != 0) {
        return rc;
    }

    return 0;
}
