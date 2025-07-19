import colorama
import importlib
import random
import struct
import time
import traceback
from scapy.fields import RawVal
from scapy.layers.bluetooth4LE import *
from scapy.layers.bluetooth import *
from scapy.fields import RawVal
from scapy.packet import Raw
from scapy.compat import raw
from colorama import Fore
from Crypto.Cipher import AES

importlib.import_module('BLESMPServer')
import BLESMPServer
from NRF52_Driver import NRF52


# Parts of this file were taken from https://github.com/apferscher/ble-learning/blob/main/BLESUL.py


class BLESUL:
    packets = {
        'LL_ADV_IND':                       lambda self: BTLE() / BTLE_ADV(RxAdd=self.peripheral_address_is_rand, TxAdd=self.central_address_is_rand) / BTLE_ADV_IND(AdvA=self.central_address),
        'LL_ADV_SCAN_REQ':                  lambda self: BTLE() / BTLE_ADV(RxAdd=self.peripheral_address_is_rand, TxAdd=self.central_address_is_rand) / BTLE_SCAN_REQ(ScanA=self.central_address, AdvA=self.peripheral_address),
        'LL_ADV_SCAN_RSP':                  lambda self: BTLE() / BTLE_ADV(RxAdd=self.peripheral_address_is_rand, TxAdd=self.central_address_is_rand) / BTLE_SCAN_RSP(AdvA=self.central_address),
        'LL_ADV_CONNECT_IND':               lambda self: BTLE() / BTLE_ADV(RxAdd=self.peripheral_address_is_rand, TxAdd=self.central_address_is_rand) / BTLE_CONNECT_REQ(InitA=self.central_address, AdvA=self.peripheral_address, AA=RawVal(struct.pack('<I', self.access_address)), crc_init=0x179a9c, win_size=2, win_offset=1, interval=16, latency=0, timeout=50, chM=0x1FFFFFFFFF, SCA=0, hop=5),

        'LL_DATA':                          lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA(LLID=0x01),

        'LL_CTRL_TERMINATE_IND':            lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / BTLE_CTRL() / LL_TERMINATE_IND(),
        'LL_CTRL_ENC_REQ':                  lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / BTLE_CTRL() / LL_ENC_REQ(rand=0, ediv=0, skdm=int.from_bytes(self.conn_skd[0:8], 'little'), ivm=int.from_bytes(self.conn_iv[0:4], 'little')),
        'LL_CTRL_ENC_RSP':                  lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / BTLE_CTRL() / LL_ENC_RSP(skds=int.from_bytes(self.conn_skd[8:16], 'little'), ivs=int.from_bytes(self.conn_iv[4:8], 'little')),
        'LL_CTRL_START_ENC_REQ':            lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / BTLE_CTRL() / LL_START_ENC_REQ(),
        'LL_CTRL_START_ENC_RSP':            lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / BTLE_CTRL() / LL_START_ENC_RSP(),
        'LL_CTRL_UNKNOWN_RSP':              lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / BTLE_CTRL() / LL_UNKNOWN_RSP(),
        'LL_CTRL_FEATURE_REQ':              lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / BTLE_CTRL() / LL_FEATURE_REQ(feature_set='le_encryption+le_data_len_ext'),
        'LL_CTRL_FEATURE_RSP':              lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / BTLE_CTRL() / LL_FEATURE_RSP(feature_set='le_encryption+le_data_len_ext'),
        'LL_CTRL_PAUSE_ENC_REQ':            lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / BTLE_CTRL() / LL_PAUSE_ENC_REQ(),
        'LL_CTRL_PAUSE_ENC_RSP':            lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / BTLE_CTRL() / LL_PAUSE_ENC_RSP(),
        'LL_CTRL_VERSION_IND':              lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / BTLE_CTRL() / LL_VERSION_IND(version='5.0'),
        'LL_CTRL_REJECT_IND':               lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / BTLE_CTRL() / LL_REJECT_IND(code=0x11),
        'LL_CTRL_PERIPHERAL_FEATURE_REQ':   lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / BTLE_CTRL() / LL_SLAVE_FEATURE_REQ(feature_set='le_encryption+le_data_len_ext'),
        'LL_CTRL_REJECT_EXT_IND':           lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / BTLE_CTRL() / LL_REJECT_EXT_IND(error_code=0x11),
        'LL_CTRL_LENGTH_REQ':               lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / BTLE_CTRL() / LL_LENGTH_REQ(max_tx_bytes=247 + 4, max_rx_bytes=247 + 4),
        'LL_CTRL_LENGTH_RSP':               lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / BTLE_CTRL() / LL_LENGTH_RSP(max_tx_bytes=247 + 4, max_rx_bytes=247 + 4),
        'LL_CTRL_PHY_REQ':                  lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / BTLE_CTRL() / LL_PHY_REQ(tx_phys='phy_coded', rx_phys='phy_coded'),
        'LL_CTRL_PHY_RSP':                  lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / BTLE_CTRL() / LL_PHY_RSP(tx_phys='phy_coded', rx_phys='phy_coded'),
        'LL_CTRL_PHY_UPDATE_IND':           lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / BTLE_CTRL() / LL_PHY_UPDATE_IND(tx_phy='phy_coded', rx_phy='phy_coded'),

        'L2CAP_CONNECTION_PARAMETER_UPDATE_REQ': lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / L2CAP_CmdHdr() / L2CAP_Connection_Parameter_Update_Request(),

        'SM_PAIRING_REQ':                   lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / SM_Hdr() / SM_Pairing_Request(iocap=0x03, oob=0, authentication=0x01, max_key_size=16, initiator_key_distribution=0x01, responder_key_distribution=0x01),
        'SM_PAIRING_REQ_SC':                lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / SM_Hdr() / SM_Pairing_Request(iocap=0x01, oob=0, authentication=0x09, max_key_size=16, initiator_key_distribution=0x01, responder_key_distribution=0x01),
        'SM_PAIRING_RSP':                   lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / SM_Hdr() / SM_Pairing_Response(iocap=0x03, oob=0, authentication=0x01, max_key_size=16, initiator_key_distribution=0x01, responder_key_distribution=0x01),
        'SM_CONFIRM':                       lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / SM_Hdr() / SM_Confirm(confirm=self.confirm),
        'SM_RANDOM':                        lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / SM_Hdr() / SM_Random(random=self.random),
        'SM_FAILED':                        lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / SM_Hdr() / SM_Failed(reason=0x08),
        'SM_ENCRYPTION_INFORMATION':        lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / SM_Hdr() / SM_Encryption_Information(ltk=self.conn_ltk_enc_inf),
        'SM_CENTRAL_IDENTIFICATION':        lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / SM_Hdr() / SM_Master_Identification(ediv=self.ediv, rand=self.rand),
        'SM_IDENTITY_INFORMATION':          lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / SM_Hdr() / SM_Identity_Information(irk=self.irk),
        'SM_IDENTITY_ADDRESS_INFORMATION':  lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / SM_Hdr() / SM_Identity_Address_Information(atype=self.atype),
        'SM_SIGNING_INFORMATION':           lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / SM_Hdr() / SM_Signing_Information(csrk=self.csrk),
        'SM_PUBLIC_KEY':                    lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / SM_Hdr() / SM_Public_Key(key_x=self.key_x, key_y=self.key_y),
        'SM_DHKEY_CHECK':                   lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / SM_Hdr() / SM_DHKey_Check(dhkey_check=self.dhkey_check),

        'ATT_ERROR_RSP':                    lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / ATT_Hdr() / ATT_Error_Response(),
        'ATT_EXCHANGE_MTU_REQ':             lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / ATT_Hdr() / ATT_Exchange_MTU_Request(mtu=247),
        'ATT_EXCHANGE_MTU_RSP':             lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / ATT_Hdr() / ATT_Exchange_MTU_Response(mtu=247),
        'ATT_READ_BY_TYPE_REQ':             lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / ATT_Hdr() / ATT_Read_By_Type_Request(start=0x0001,end=0xffff, uuid=0x2800),
        'ATT_READ_BY_TYPE_RSP':             lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / ATT_Hdr() / ATT_Read_By_Type_Response(),
        'ATT_READ_BY_GROUP_TYPE_REQ':       lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / ATT_Hdr() / ATT_Read_By_Group_Type_Request(start=0x0001,end=0xffff, uuid=0x2800),
        'ATT_READ_BY_GROUP_TYPE_RSP':       lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / ATT_Hdr() / ATT_Read_By_Group_Type_Response(),
        'ATT_READ_REQ':                     lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / ATT_Hdr() / ATT_Read_Request(gatt_handle=0x12),
        'ATT_READ_RSP':                     lambda self: BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / ATT_Hdr() / ATT_Read_Response(value='0')
    }


    def __init__(self, serial_port, device_address, reset_cmd=None, recv_s_min=0.1, recv_s_max=1.0, output_symbol_filters=[]):
        colorama.init(autoreset=True)
        self.driver = NRF52(serial_port, debug=False, logs_pcap=False, reset_cmd=reset_cmd)
        self.peripheral_address = device_address
        self.peripheral_address_is_rand = 1
        self.central_address_is_rand = 0 # BLESMPServer assumes our address is public
        self.recv_s_min = recv_s_min
        self.recv_s_max = recv_s_max
        self.output_symbol_filters = output_symbol_filters + ['LL_ADV_IND', 'LL_DATA']
        self.is_retry_running = False
        self.last_device_reset_time = 0
        self.test_start_time = time.time()
        self.reset_breaks = []
    

    def pre(self):
        try:
            self.reset()
        except Exception as e:
            print(traceback.format_exc())
            raise e
        
    def step(self, input_symbol):
        try:
            output_symbol = self.step_internal(input_symbol)
            # Filter the symbol that is returned to the learner
            return self.filter_symbol(output_symbol, self.output_symbol_filters)
        except Exception as e:
            print(traceback.format_exc())
            raise e
    
    def post(self):
        pass


    def step_internal(self, input_symbol):
        pkt = self.packets[input_symbol](self)
        # If there's a function with the name <input_symbol>
        # defined, we call that to get the output symbol
        if hasattr(self, input_symbol.lower()):
            output_symbol = getattr(self, input_symbol.lower())(pkt)
        else:
            # A function with the name <input_symbol>_pre will be called
            # before the request is made and allows changing the request packet.
            if hasattr(self, input_symbol.lower() + '_pre'):
                pkt = getattr(self, input_symbol.lower() + '_pre')(pkt)
            # Perform the request
            self.send(pkt)
            res_pkts = self.receive(req=pkt)
            # A function with the name <input_symbol>_post will be called with the
            # response and allows changing it before the output symbol is created.
            if hasattr(self, input_symbol.lower() + '_post'):
                res_pkts = getattr(self, input_symbol.lower() + '_post')(res_pkts)
            output_symbol = self.output_symbol(res_pkts)
        # Update sequence
        self.input_sequence.append(input_symbol)
        self.output_sequence.append(output_symbol)
        # If we suspect odd behavior of the SUL, we retry
        if not self.is_retry_running and self.is_last_sym_suspicious():
            output_symbol = self.retry_sequence()
        return output_symbol

    def reset(self):
        # Terminate the current connection (if there is one)
        if hasattr(self, 'access_address'):
            # We don't expect a response.
            # The scan request below will also take care of reading response packets.
            self.send(self.packets['LL_CTRL_TERMINATE_IND'](self))
            time.sleep(self.recv_s_min)
        
        # Reset addresses and internal state
        self.central_address = ':'.join([random.randbytes(1).hex() for i in range(6)])
        self.access_address = random.getrandbits(32)
        self.encrypted = False
        self.enc_tx_pkt_count = 0
        self.enc_rx_pkt_count = 0
        self.conn_iv = b'\x00' * 8 #random.randbytes(8)
        self.conn_skd = b'\x00' * 16 #random.randbytes(8) + (b'\x00' * 8)
        self.conn_ltk = b'\x00' * 16
        self.conn_session_key = b'\x00' * 16
        self.confirm = b'\x00' * 16
        self.random = b'\x00' * 16
        self.conn_ltk_enc_inf = b'\x00' * 16
        self.rand = b'\x00' * 8
        self.ediv = 0
        self.irk = b'\x00' * 16
        self.csrk = b'\x00' * 16
        self.key_x = b'\x00' * 32
        self.key_y = b'\x00' * 32
        self.atype = 0
        self.dhkey_check = b'\x00' * 16

        # Keep track of the input/output symbols in the current sequence
        self.input_sequence = []
        self.output_sequence = []

        # Make sure we can get a response to a scan request (sanity check)
        for i in range(32):
            scan_pkt = self.packets['LL_ADV_SCAN_REQ'](self)
            self.send(scan_pkt)
            scan_res = self.receive(recv_s_min=min(2.0, self.recv_s_min * pow(2, i)), req=scan_pkt)
            if any(BTLE_SCAN_RSP in pkt for pkt in scan_res):
                break
            print(Fore.YELLOW + 'RESET: No scan response, attempting again...' + Fore.RESET)
            if i >= 28:
                print(Fore.YELLOW + 'RESET: Multiple attempts failed, try resetting the device' + Fore.RESET)
                self.reset_device()
        else:
            raise RuntimeError('RESET: PROBLEM: CANNOT GET A SCAN RESPONSE FROM THE DEVICE DURING RESET')
    
    def reset_device(self):
        # Reset the peripheral (and the tester dongle)
        time_before = time.time()
        self.driver.reset_device()
        time.sleep(1) # Give the user a chance to terminate with ctrl-c in case this is called in a loop
        time_after = time.time()
        self.reset_breaks.append((time_before - self.test_start_time, time_after - self.test_start_time))
        self.last_device_reset_time = time_after
    
    
    def ll_adv_scan_req_pre(self, pkt):
        # The scan request is performed unencrypted on the advertising channel.
        # This terminates an ongoing connection.
        self.encrypted = False
        return pkt

    def ll_adv_scan_req_post(self, pkts):
        # Extract the peripheral address type (needed later for pairing)
        for pkt in pkts:
            if pkt is not None and (BTLE_SCAN_RSP in pkt or BTLE_ADV in pkt) and hasattr(pkt, 'AdvA') and hasattr(pkt.AdvA, 'upper') and self.peripheral_address.upper() == pkt.AdvA.upper():
                self.peripheral_address_is_rand = pkt.TxAdd
        return pkts

    def ll_adv_connect_ind_pre(self, pkt):
        # A connect indication always switches to a new unencrypted connection
        self.encrypted = False
        return pkt

    def ll_ctrl_enc_req(self, pkt):
        # Send the request
        self.send(pkt)
        # If the connection was encrypted, it is important that
        # we reset the packet counters for decrypting the response
        self.enc_tx_pkt_count = 0
        self.enc_rx_pkt_count = 0
        # We have to receive the response packets one-by-one because in case a 2nd
        # LL_CTRL_ENC_REQ packet is sent, the LL_CTRL_ENC_RSP will be encrypted with
        # the old key/iv and the LL_CTRL_START_ENC_REQ with the new key/iv.
        # That means we have to switch the key/iv in between.
        res_pkts = []
        time_start = time.time()
        while not self.is_rsp_complete(res_pkts, time.time() - time_start):
            pkts = self.receive(max_pkts=1, req=pkt)
            if len(pkts) > 0:
                pkt = pkts[0]
                res_pkts.append(pkt)
                if LL_ENC_RSP in pkt:
                    # Bluetooth Spec, Vol.6 Part B, 5.1.3.1. Encryption Start procedure
                    # This is a bit confusing. The specification mentions that  SKD and IV
                    # are assembled like this: SKD = SKD_P || SKD_C, IV = IV_P || IV_C
                    # However, we're storing all crypto stuff as little endian byte arrays
                    # because the IV is needed as LE for the nonce and because it's easier
                    # to compare with other stacks like nimble that also store stuff as LE.
                    # This means in the end that the two parts are effectively concatenated
                    # the other way around. Note that the scapy fields are also little endian.
                    self.conn_skd = self.conn_skd[0:8] + struct.pack('<Q', pkt[LL_ENC_RSP].skds)
                    self.conn_iv = self.conn_iv[0:4] + struct.pack('<I', pkt[LL_ENC_RSP].ivs)
                    # Workaround for nimble:
                    # Don't re-calculate the session key after encryption was started.
                    if not self.encrypted:
                        # Things going into the crypto function need to be BE (like in the BLE spec).
                        self.conn_session_key = self.bt_crypto_e(self.conn_ltk[::-1], self.conn_skd[::-1])
                    print('Session key: ' + self.conn_session_key.hex())
                    print('IV: ' + self.conn_iv.hex())
                elif LL_START_ENC_REQ in pkt:
                    self.encrypted = True
        return self.output_symbol(res_pkts)
    
    def ll_ctrl_pause_enc_req_post(self, pkts):
        # The encryption is paused if we get a confirmation from the peripheral
        for pkt in pkts:
            if LL_PAUSE_ENC_RSP in pkt:
                self.encrypted = False
        return pkts

    def sm_pairing_req_pre(self, pkt):
        # The pairing request packet is generated by the BLESMPServer.
        # The reason is that the content goes into the key derivation later.
        # authentication = 0x01 # Bonding only (not setting the secure communication bit)
        # pairing_iocap = 0x03 #NoInputNoOutput
        authentication = pkt[SM_Pairing_Request].authentication
        pairing_iocap = pkt[SM_Pairing_Request].iocap
        central_address_raw = bytes.fromhex(self.central_address.replace(':', ''))
        peripheral_address_raw = bytes.fromhex(self.peripheral_address.replace(':', ''))
        BLESMPServer.set_pin_code('\x00' * 4)
        BLESMPServer.configure_connection(central_address_raw, peripheral_address_raw, self.peripheral_address_is_rand, pairing_iocap, authentication)
        hci_res = BLESMPServer.pairing_request().encode()
        return BTLE(access_addr=self.access_address) / BTLE_DATA() / L2CAP_Hdr() / HCI_Hdr(hci_res)[SM_Hdr]
    
    def sm_pairing_req_sc_pre(self, pkt):
        return self.sm_pairing_req_pre(pkt)


    def bt_crypto_e(self, key, plaintext):
        # Crypto "e" function as defined in the BLE spec
        aes = AES.new(key, AES.MODE_ECB)
        return aes.encrypt(plaintext)

    def smp_process(self, pkt):
        # Handles everything that should go to the security manager layer.
        # Some SMP implementation is used to calculate the encryption related material.
        raw_pkt = raw(HCI_Hdr() / HCI_ACL_Hdr() / L2CAP_Hdr() / pkt[SM_Hdr])
        smp_answer = BLESMPServer.send_hci(raw_pkt)
        if smp_answer is not None and isinstance(smp_answer, list):
            for res in smp_answer:
                res = HCI_Hdr(res)
                print('BLESMPServer: ' + res.summary())
                if SM_Confirm in res:
                    self.confirm = res.confirm
                elif SM_Random in res:
                    self.random = res.random
                elif HCI_Cmd_LE_Enable_Encryption in res:
                    self.conn_ltk = res.ltk
                elif SM_Encryption_Information in res:
                    self.conn_ltk_enc_inf = res.ltk
                elif SM_Master_Identification in res:
                    self.ediv = res.ediv
                    self.rand = res.rand
                elif SM_Identity_Information in res:
                    self.irk = res.irk
                elif SM_Identity_Address_Information in res:
                    self.atype = res.atype
                elif SM_Signing_Information in res:
                    self.csrk = res.csrk
                elif SM_Public_Key in res:
                    self.key_x = res.key_x
                    self.key_y = res.key_y
                elif SM_DHKey_Check in res:
                    self.dhkey_check = res.dhkey_check


    def send(self, pkt):
        # Send a packet to the target
        if self.encrypted and BTLE_DATA in pkt:
            print(f'TX counter: {self.enc_tx_pkt_count}')
            print(Fore.CYAN + 'TX ---> ' + pkt.summary() + ' [ENCRYPTED]' + Fore.RESET)
            raw_pkt = bytearray(raw(pkt))
            aa = raw_pkt[:4] # access address
            header = bytearray([raw_pkt[4]])
            length = bytearray([raw_pkt[5] + 4])  
            crc = b'\x00\x00\x00' 
            pkt_count = bytearray(struct.pack('<Q', self.enc_tx_pkt_count)[:5]) 
            pkt_count[4] |= 0x80 
            nonce = pkt_count + self.conn_iv
            aes = AES.new(self.conn_session_key, AES.MODE_CCM, nonce=nonce, mac_len=4) 
            aes.update(bytes([header[0] & b'\xE3'[0]]))   
            enc_pkt, mic = aes.encrypt_and_digest(bytes(raw_pkt[6:-3])) 
            self.enc_tx_pkt_count += 1 
            aa_raw = bytes(aa)
            pkt_send = bytearray(aa_raw) + bytearray(header) + bytearray(length) + bytearray(enc_pkt) + bytearray(mic) + bytearray(crc)
            self.driver.raw_send(pkt_send)
        else:
            print(Fore.CYAN + 'TX ---> ' + pkt.summary() + Fore.RESET)
            self.driver.send(pkt)


    def is_target(self, pkt):
        # Decides whether an incoming packet is determined for us
        if BTLE_ADV in pkt and hasattr(pkt, 'AdvA') and hasattr(pkt.AdvA, 'upper') and self.peripheral_address.upper() != pkt.AdvA.upper():
            return False
        if BTLE_DATA in pkt and self.access_address != pkt.access_addr:
            print(f'Access address mismatch: {hex(self.access_address)} (ours), {hex(pkt.access_addr)} (received)')
            return False
        return True
    
    def is_rsp_complete(self, pkts, recv_s_time, recv_s_min=None, recv_s_max=None, req=None):
        # How many additional responses we typically
        # expect after seeing one of these packets
        n_add_expect = {
            'LL_CTRL_ENC_RSP': 1, # LL_START_ENC_REQ
            'LL_CTRL_START_ENC_RSP': 3 # SM_Encryption_Information...
        }
        # Keeping track of how many more responses we expect
        n_rsp_expected = 1
        # Keeping track of how many cyclic packets we have seen
        # at the end of the packet sequence
        n_cyclic_seen = 0
        # Look at the packets we have received so far
        for pkt in pkts:
            if pkt.layers()[-1] in [BTLE_ADV, BTLE_ADV_IND, BTLE_ADV_NONCONN_IND, BTLE_ADV_DIRECT_IND, BTLE_DATA]:
                n_cyclic_seen += 1
            else:
                n_cyclic_seen = 0
                n_rsp_expected = n_add_expect.get(self.output_symbol([pkt]), max(0, n_rsp_expected - 1))
        # Heuristic that determines if the sequence seems complete
        sequence_seems_complete = (n_rsp_expected == 0 and n_cyclic_seen >= 5) or n_cyclic_seen >= 10
        # Now consider also the receiving time
        if recv_s_min is None:
            recv_s_min = self.recv_s_min
        if recv_s_max is None:
            recv_s_max = self.recv_s_max
        if recv_s_max < recv_s_min:
            recv_s_max = recv_s_min
        stop_receiving = (recv_s_time >= recv_s_max or (recv_s_time >= recv_s_min and sequence_seems_complete))
        return stop_receiving
    
    def fix_packet(self, pkt):
        # For some reason, scapy doesn't parse all layers for all packets fully.
        # I.e. some packets differ when converting to bytes and back.
        if BTLE_CTRL in pkt and pkt.opcode == 0x05 and LL_START_ENC_REQ not in pkt:
            return pkt / LL_START_ENC_REQ()
        if BTLE_CTRL in pkt and pkt.opcode == 0x06 and LL_START_ENC_RSP not in pkt:
            return pkt / LL_START_ENC_RSP()
        if BTLE_CTRL in pkt and pkt.opcode == 0x0b and LL_PAUSE_ENC_RSP not in pkt:
            return pkt / LL_PAUSE_ENC_RSP()
        return pkt
    
    def filter_symbol(self, symbol, filter):
        # Removes specific symbols from a combined output symbol
        symbol = '+'.join([s for s in symbol.split('+') if s not in filter])
        if symbol == '':
            symbol = 'NORESPONSE'
        return symbol

    def output_symbol(self, pkts):
        # Create a lookup table for the output symbols
        if not hasattr(self, 'symbols'):
            self.symbols = {pkt(self).summary(): sym for sym, pkt in self.packets.items()}
        # Return a special symbol if we don't get any response packets
        if len(pkts) == 0:
            return 'NORESPONSE'
        # Convert the packet list to an output symbol
        symbols = [self.symbols.get(pkt.summary(), pkt.summary().replace(' / ', '>')) for pkt in pkts]
        symbols = list(sorted(set(symbols)))
        return '+'.join(symbols)

    def receive(self, recv_s_min=None, recv_s_max=None, max_pkts=0, req=None):
        # Receive one or more packets from the target
        packets = []
        time_start = time.time()
        time_now = time_start
        while True:
            time.sleep(0.01)
            data = self.driver.raw_receive()
            if data is not None:
                pkt = BTLE(data)
                if pkt is not None and self.is_target(pkt):
                    # If the peripheral changed to the advertising channel, we stop encrypting
                    if BTLE_ADV in pkt:
                        self.encrypted = False
                    is_broken = False
                    if self.encrypted:
                        raw_pkt = bytearray(raw(pkt))
                        aa = raw_pkt[:4]
                        header = bytearray([raw_pkt[4]]) 
                        length = raw_pkt[5]
                        if length >= 5:
                            print(f'RX counter: {self.enc_rx_pkt_count}')
                            length -= 4  
                            pkt_count = bytearray(struct.pack('<Q', self.enc_rx_pkt_count)[:5])  # convert only 5 bytes
                            pkt_count[4] &= 0x7F  # Clear bit 7 for slave -> master
                            nonce = pkt_count + self.conn_iv
                            aes = AES.new(self.conn_session_key, AES.MODE_CCM, nonce=nonce, mac_len=4)  # mac = mic
                            aes.update(bytes([header[0] & 0xE3]))
                            dec_pkt = aes.decrypt(raw_pkt[6:-4 - 3])  # get payload and exclude 3 bytes of crc
                            self.enc_rx_pkt_count += 1
                            try:
                                mic = raw_pkt[6 + length: -3]  # Get mic from payload and exclude crc
                                aes.verify(mic)
                                data = aa + header + bytearray([length]) + dec_pkt + b'\x00\x00\x00'
                            except Exception as e:
                                print('INVALID MIC RECEIVED?!')
                                is_broken = True
                                data = aa + header + bytearray([length]) + dec_pkt + b'\x00\x00\x00'
                            pkt = BTLE(data)
                    # For some packets, the scapy structure needs to be repaired
                    if not is_broken:
                        pkt = self.fix_packet(pkt)
                    # Logging
                    desc_enc = ' [ENCRYPTED]' if self.encrypted else ''
                    desc_broken = ' (broken)' if is_broken else ''
                    print(Fore.MAGENTA + 'RX <--- ' + pkt.summary() + desc_enc + desc_broken + Fore.RESET)
                    # Process non-broken packets.
                    # If the encryption is not working, we just pretend that we don't
                    # receive those packets to avoid non-deterministic behavior.
                    if not is_broken:
                        packets.append(pkt)
                        # Raw packets indicate that we couldn't decrypt a packet correctly.
                        # This should not happen.
                        if 'Raw' in pkt.summary():
                            print('Received a raw packet!')
                            print(data.hex())
                            self.reset_device()
                        # Packets on the SM layer are forwarded to our SMP server
                        if SM_Hdr in pkt:
                            self.smp_process(pkt)
                        # Sometimes it's necessary to sneakily send a response to a non-deterministic
                        # message to continue fuzzing. We don't want ProtocolState-Fuzzer to know about this.
                        if hasattr(self, 'handle_packet'):
                            res_pkt = self.handle_packet(pkt)
                            if res_pkt is not None:
                                self.send(res_pkt)
                                time_start = time.time()
            time_now = time.time()
            if (self.is_rsp_complete(packets, time_now - time_start, recv_s_min, recv_s_max, req)) or (max_pkts > 0 and len(packets) == max_pkts):
                #print(f'Time: {round(time_now - time_start, 2)}')
                break
        return packets

    def receive_output_symbol(self, recv_s_min=None, recv_s_max=None, req=None):
        return self.output_symbol(self.receive(recv_s_min=recv_s_min, recv_s_max=recv_s_max, req=req))


    def is_last_sym_suspicious(self):
        # This can be overridden if needed
        return False


    def retry_sequence(self):
        # This function retries the current sequence to confirm/update the last output symbol.
        # After calling this function, the state of the SUL will be the same as before.
        seq_in = self.input_sequence
        seq_out = self.output_sequence
        attempt = 0
        print(Fore.YELLOW + 'RETRY: Retrying suspicious sequence' + Fore.RESET)
        print(Fore.YELLOW + 'RETRY:  Input: ' + ' '.join(seq_in) + Fore.RESET)
        print(Fore.YELLOW + 'RETRY: Output: ' + ' '.join(seq_out) + Fore.RESET)
        while True:
            attempt += 1
            self.post()
            # Reset the device after multiple failures
            if attempt >= 4:
                print(Fore.YELLOW + 'RETRY: Multiple suspicious responses, try resetting the device' + Fore.RESET)
                self.reset_device()
            print(Fore.YELLOW + f'RETRY: Attempt {attempt}' + Fore.RESET)
            self.is_retry_running = True
            self.pre()
            for sym_in in seq_in:
                print(Fore.YELLOW + f'RETRY: -> ' + sym_in + Fore.RESET)
                sym_out = self.step_internal(sym_in)
                print(Fore.YELLOW + f'RETRY: <- ' + sym_out + Fore.RESET)
            if [self.filter_symbol(s, self.output_symbol_filters) for s in seq_out[:-1]] != [self.filter_symbol(s, self.output_symbol_filters) for s in self.output_sequence[:-1]]:
                # Dammit, this shouldn't happen! We messed up the state of the SUL
                # during the earlier messages. The only thing we can do is to retry...
                if attempt < 7:
                    print(Fore.YELLOW + 'RETRY: Messed up earlier state, retrying!' + Fore.RESET)
                    continue
                else:
                    print(Fore.RED + 'RETRY: Messed up earlier state and cannot recover!' + Fore.RESET)
                    break
            if self.is_last_sym_suspicious():
                if attempt < 6:
                    print(Fore.YELLOW + 'RETRY: Output still suspicious, retrying!' + Fore.RESET)
                    continue
                else:
                    print(Fore.RED + 'RETRY: Could not find unsuspicious alternative!' + Fore.RESET)
                    break
            else:
                print(Fore.YELLOW + 'RETRY: Found better alternative!' + Fore.RESET)
                break
        self.is_retry_running = False
        return self.output_sequence[-1]


    def close(self):
        print(f'Total runtime: {time.time() - self.test_start_time}')
        print('Reset breaks:')
        total_pause_time = 0
        for pause_start, pause_end in self.reset_breaks:
            print(f'  {pause_start} -> {pause_end}')
            total_pause_time += (pause_end - pause_start)
        print(f'  TOTAL: {total_pause_time} s')
        self.driver.save_pcap('BLESUL_io.pcapng')
        self.driver.close()
