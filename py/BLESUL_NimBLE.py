import time

from scapy.fields import RawVal
from scapy.layers.bluetooth4LE import *
from scapy.layers.bluetooth import *

from BLESUL import BLESUL


# Note:
# There is a bug somewhere in NimBLE or more likely in the bridge driver
# that is probably timing related. After about 20 h of testing, NimBLE sometimes
# shows problems that is doesn't switch to the data channels after a connection
# is established. The only way to fix this (right now) is to restart the NimBLE
# process. The NimBLE driver prompts us to do that when it detects that case.


class BLESUL_NimBLE(BLESUL):
    def __init__(self, serial_port, device_address):
        BLESUL.__init__(self, serial_port, device_address, reset_cmd='scripts/reset_manually.sh', recv_s_min=0.15, recv_s_max=0.3)
        self.peripheral_address_is_rand = 0
    
    def is_rsp_complete(self, pkts, recv_s_time, recv_s_min=None, recv_s_max=None, req=None):
        # Non-determinism fix:
        # The LL_ADV_CONNECT_IND sometimes takes some time to return a response
        if req is not None and BTLE_CONNECT_REQ in req:
            return BLESUL.is_rsp_complete(self, pkts, recv_s_time, recv_s_min, 0.5)
        # We should receive response packets (if just empty data) fairly
        # reliably. If we didn't receive anything after the minimum timeout means
        # that the connection was most likely terminated.
        if recv_s_min is None:
            recv_s_min = self.recv_s_min
        if recv_s_time >= recv_s_min and len(pkts) == 0:
            return True
        # There's some problem that always only one BTLE_ADV_IND is sent
        # so we can speed up the reset a little by knowing that we're
        # good once we got one BTLE_ADV_IND and one BTLE_SCAN_RSP.
        if any(BTLE_ADV_IND in p for p in pkts) and any(BTLE_SCAN_RSP in p for p in pkts):
            return True
        # BLESUL decides
        return BLESUL.is_rsp_complete(self, pkts, recv_s_time, recv_s_min, recv_s_max)

    # Not disabling encryption because rn we can't switch from
    # a data channel to an advertising channel with nimble.
    # Also, we're sending a LL_LENGTH_REQ after each connect
    # to avoid non-determinism when packets are split up into
    # multiple ones.
    def ll_adv_connect_ind(self, pkt):
        self.send(pkt)
        res_pkts = self.receive(req=pkt)
        pkt = self.packets['LL_CTRL_LENGTH_REQ'](self)
        self.send(pkt)
        self.receive(req=pkt)
        return self.output_symbol(res_pkts)

    # Not disabling encryption because rn we can't switch from
    # a data channel to an advertising channel with nimble
    def ll_adv_scan_req_pre(self, pkt):
        return pkt

    # The handle can be different on different devices.
    # Usually, it's looked up with another request, but we're skipping that here.
    def att_read_req_pre(self, pkt):
        pkt.gatt_handle = 0x24
        return pkt
