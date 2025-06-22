import time

from scapy.fields import RawVal
from scapy.layers.bluetooth4LE import *
from scapy.layers.bluetooth import *

from BLESUL import BLESUL


# Non-determinism fix:
# Ignore late scan responses that leak into other requests.
OUTPUT_FILTER = ['LL_ADV_SCAN_RSP']


class BLESUL_nRF52840DKNimBLE(BLESUL):
    def __init__(self, serial_port, device_address):
        BLESUL.__init__(self, serial_port, device_address, reset_cmd='scripts/reset_manually.sh', recv_s_min=0.15, recv_s_max=0.4, output_symbol_filters=OUTPUT_FILTER)
        self.peripheral_address_is_rand = 1
    
    def is_rsp_complete(self, pkts, recv_s_time, recv_s_min=None, recv_s_max=None, req=None):
        # Non-determinism fix:
        # If there is already a connection and we send an LL_ADV_CONNECT_IND,
        # it takes some time to get processed (around 0.85 seconds!)
        if req is not None and BTLE_CONNECT_REQ in req:
            return BLESUL.is_rsp_complete(self, pkts, recv_s_time, recv_s_min, 2.0)
        # We should receive response packets (if just empty data) fairly
        # reliably. If we didn't receive anything after the minimum timeout,
        # it means that the connection was most likely terminated.
        if recv_s_min is None:
            recv_s_min = self.recv_s_min
        if recv_s_time >= recv_s_min and len(pkts) == 0:
            return True
        # BLESUL decides
        return BLESUL.is_rsp_complete(self, pkts, recv_s_time, recv_s_min, recv_s_max)

    # Non-determinism fix:
    # We're sending a LL_LENGTH_REQ after each connect
    # to avoid packets being split up into multiple ones.
    def ll_adv_connect_ind(self, pkt):
        self.send(pkt)
        res_pkts = self.receive(req=pkt)
        pkt = self.packets['LL_CTRL_LENGTH_REQ'](self)
        self.send(pkt)
        self.receive(req=pkt)
        return self.output_symbol(res_pkts)

    # The handle can be different on different devices.
    # Usually, it's looked up with another request, but we're skipping that here.
    def att_read_req_pre(self, pkt):
        pkt.gatt_handle = 0x24 #0x26 for bleprph
        return pkt

    def is_last_sym_suspicious(self):
        # Non-determinism fix:
        # Might have been sth spurious, but I saw a Raw response after an LL_ADV_CONNECT_IND.
        # We shouldn't really see any Raw responses anywhere since wrongly decrypted
        # packets are being discarded.
        if 'Raw' in self.output_sequence[-1]:
            return True
        return BLESUL.is_last_sym_suspicious(self)