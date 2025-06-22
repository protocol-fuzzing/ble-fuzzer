from colorama import Fore
from scapy.fields import RawVal
from scapy.layers.bluetooth4LE import *
from scapy.layers.bluetooth import *

from BLESUL import BLESUL


# Non-determinism fix:
# Ignoring LL_ADV_SCAN_RSP as sometimes there are multiple returned
# for a single LL_ADV_SCAN_REQ. We might see those artefacts from resetting
# the system during later messages.
# Ignoring LL_CTRL_VERSION_IND as it is sent only sometimes after connecting.
OUTPUT_FILTER = [
    'LL_ADV_SCAN_RSP',
    'LL_CTRL_VERSION_IND'
]


class BLESUL_ArduinoNanoESP32(BLESUL):
    def __init__(self, serial_port, device_address):
        BLESUL.__init__(self, serial_port, device_address, reset_cmd='scripts/reset_manually.sh', recv_s_min=0.2, recv_s_max=0.5, output_symbol_filters=OUTPUT_FILTER)
        self.peripheral_address_is_rand = 0

    # The handle can be different on different devices.
    # Usually, it's looked up with another request, but we're skipping that here.
    def att_read_req_pre(self, pkt):
        pkt.gatt_handle = 0x2a
        return pkt

    def is_last_sym_suspicious(self):
        # Non-determinism fix:
        # When an LL_CTRL_PAUSE_ENC_REQ follows after a second LL_ADV_CONNECT_IND,
        # the peripheral returns sometimes LL_CTRL_REJECT_IND, sometimes LL_CTRL_PAUSE_ENC_RSP
        # and sometimes nothing at all. LL_CTRL_REJECT_IND seems to be the most likely and
        # consistent response, so we mark the others as suspicious.
        if len(self.input_sequence) >= 2 and self.input_sequence[-2] == 'LL_ADV_CONNECT_IND' and self.input_sequence[-1] == 'LL_CTRL_PAUSE_ENC_REQ' and not 'LL_CTRL_REJECT_IND' in self.output_sequence[-1]:
            return True
        return BLESUL.is_last_sym_suspicious(self)