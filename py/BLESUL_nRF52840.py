import time
from scapy.layers.bluetooth4LE import *
from scapy.layers.bluetooth import *

from BLESUL import BLESUL


# Non-determinism fix:
# This tends to show up around 5s into an established connection,
# so in practice it causes a lot of non-determinism as it can show
# up after different requests. There is not problem with just ignoring it.
OUTPUT_FILTER = ['L2CAP_CONNECTION_PARAMETER_UPDATE_REQ']


class BLESUL_nRF52840(BLESUL):
    def __init__(self, serial_port, device_address):
        BLESUL.__init__(self, serial_port, device_address, reset_cmd='scripts/reset_manually.sh', output_symbol_filters=OUTPUT_FILTER)
    
    # Non-determinism fix:
    # We should do a device reset every now and then to avoid memory leaks
    # or other resource exhaustion problems on the SUL impacting the learning
    def pre(self):
        if (time.time() - self.last_device_reset_time) > 60 * 60 * 8: # 8 h
            self.driver.reset_device()
            self.last_device_reset_time = time.time()
        BLESUL.pre(self)

    # Non-determinism fix:
    # The behavior of the nRF52840 when receiving the LL_TERMINATE_IND
    # packet is a bit weird. It seems to receive two more packets (while
    # more LL_TERMINATE_IND packets don't count to that limit) and then
    # drops the connection. It only still responds to some of those packets
    # (e.g. PAIRING_REQ) while ignoring the others.
    # This behavior is not super interesting, but adds a lot of states.
    # To avoid learning all those states, we just send two more packets
    # here to terminate the connection immediately.
    def ll_ctrl_terminate_ind(self, pkt):
        self.send(pkt)
        pkt = BTLE(access_addr=self.access_address) / BTLE_DATA() / BTLE_CTRL() / LL_FEATURE_REQ(feature_set='le_encryption+le_data_len_ext')
        self.send(pkt)
        pkt = BTLE(access_addr=self.access_address) / BTLE_DATA() / BTLE_CTRL() / LL_FEATURE_REQ(feature_set='le_encryption+le_data_len_ext')
        self.send(pkt)
        return self.receive_output_symbol()

    # The handle can be different on different devices.
    # Usually, it's looked up with another request, but we're skipping that here.
    def att_read_req_pre(self, pkt):
        pkt.gatt_handle = 0x12
        return pkt

    def is_last_sym_suspicious(self):
        # Non-determinism fix:
        # It happens that at some point the device refuses all pairing requests
        if len(self.input_sequence) >= 2 and self.input_sequence[-2] == 'LL_ADV_CONNECT_IND' and self.input_sequence[-1] == 'SM_PAIRING_REQ' and 'SM_FAILED' in self.output_sequence[-1]:
            return True
        return BLESUL.is_last_sym_suspicious(self)
