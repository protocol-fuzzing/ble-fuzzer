from BLESUL import BLESUL
from BLESUL_NimBLE import BLESUL_NimBLE

# This just uses the BLESUL_NimBLE mapper, but with higher timeouts for the CI.

class BLESUL_CI(BLESUL_NimBLE):
    def __init__(self, serial_port, device_address):
        BLESUL.__init__(self, serial_port, device_address, reset_cmd='scripts/reset_ci.sh', recv_s_min=0.2, recv_s_max=0.5)
        self.peripheral_address_is_rand = 0