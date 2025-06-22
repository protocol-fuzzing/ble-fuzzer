from scapy.fields import RawVal
from scapy.layers.bluetooth4LE import *
from scapy.layers.bluetooth import *

from BLESUL import BLESUL


# Non-determinism fix:
# Those messages tend to appear at different points in time
# during communication but are not relevant to the flow we're testing.
# It's mostly bluez asking more information about our "device".
OUTPUT_FILTER = [
    'L2CAP_CONNECTION_PARAMETER_UPDATE_REQ',
    'ATT_EXCHANGE_MTU_REQ',
    'ATT_READ_BY_TYPE_REQ',
    'ATT_READ_BY_GROUP_TYPE_REQ',
    'SM_SIGNING_INFORMATION'
]


class BLESUL_IntelAX200BlueZ(BLESUL):
    def __init__(self, serial_port, device_address):
        BLESUL.__init__(self, serial_port, device_address, reset_cmd='scripts/reset_ble_stack.sh', recv_s_min=0.1, output_symbol_filters=OUTPUT_FILTER)

    # Non-determinism fix:
    # Bluez sends ATT requests at different times to request more data about us
    # and then waits for a response before continuing to answer other packets we send
    def handle_packet(self, pkt):
        if ATT_Exchange_MTU_Request in pkt:
            return BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / ATT_Hdr() / ATT_Exchange_MTU_Response(mtu=247)
        if ATT_Read_By_Type_Request in pkt and pkt[ATT_Read_By_Type_Request].uuid == 0x2b3a:
            return BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / ATT_Hdr() / ATT_Read_By_Type_Response(len=3, handles=RawVal(bytes.fromhex('050001')))
        if ATT_Read_By_Type_Request in pkt and pkt[ATT_Read_By_Type_Request].uuid == 0x2b2a:
            return BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / ATT_Hdr() / ATT_Read_By_Type_Response(len=18, handles=RawVal(bytes.fromhex('09008991c462ebe9d90b9ea0da3e16d0f513')))
        if ATT_Read_By_Group_Type_Request in pkt:
            return BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / ATT_Hdr() / ATT_Error_Response(request=0x10, handle=pkt[ATT_Read_By_Group_Type_Request].start, ecode="unsupported req")
        return None
    