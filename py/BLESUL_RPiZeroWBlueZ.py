from scapy.fields import RawVal
from scapy.layers.bluetooth4LE import *
from scapy.layers.bluetooth import *

from BLESUL import BLESUL


class BLESUL_RPiZeroWBlueZ(BLESUL):
    def __init__(self, serial_port, device_address):
        BLESUL.__init__(self, serial_port, device_address, reset_cmd='scripts/reset_manually.sh', recv_s_min=0.5, recv_s_max=2.0)

    # The handle can be different on different devices.
    # Usually, it's looked up with another request, but we're skipping that here.
    def att_read_req_pre(self, pkt):
        pkt.gatt_handle = 0x18
        return pkt
