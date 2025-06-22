import os
import serial
import time
from colorama import Fore
from scapy.compat import raw, chb
from scapy.config import conf
from scapy.fields import ByteField, LEShortField, LEIntField
from scapy.layers.bluetooth4LE import BTLE
from scapy.packet import Packet, bind_layers
from scapy.utils import wrpcap

# This file was taken from
# https://github.com/apferscher/ble-learning/blob/main/BLEAdapter/NRF52_Driver.py and
# https://github.com/apferscher/ble-learning/blob/main/BLEAdapter/NordicPkt.py
# and was slightly adapted.


class NORDIC_BLE(Packet):
    """Cooked Nordic BTLE link-layer pseudoheader.
    """
    name = "BTLE Nordic info header"
    fields_desc = [
        ByteField("board", 0),
        LEShortField("payload_len", None),
        ByteField("protocol", 0),
        LEShortField("packet_counter", 0),
        ByteField("packet_id", 0),
        ByteField("packet_len", 10),
        ByteField("flags", 0),
        ByteField("channel", 0),
        ByteField("rssi", 0),
        LEShortField("event_counter", 0),
        LEIntField("delta_time", 0),
    ]

    def post_build(self, p, pay):
        if self.payload_len is None:
            p = p[:1] + chb(len(pay) + 10) + p[2:]
        return p + pay

# bindings
DLT_NORDIC_BLE	= 272
conf.l2types.register(DLT_NORDIC_BLE, NORDIC_BLE)
bind_layers(NORDIC_BLE, BTLE)




NRF52_CMD_DATA = b'\xA7'
NRF52_CMD_DATA_TX = b'\xBB'
NRF52_CMD_CHECKSUM_ERROR = b'\xA8'
NRF52_CMD_CONFIG_AUTO_EMPTY_PDU = b'\xA9'
NRF52_CMD_CONFIG_ACK = b'\xAA'
NRF52_CMD_CONFIG_LOG_TX = b'\xCC'
NRF52_CMD_CONFIG_NESNSN = b'\xAD'
NRF52_CMD_CONFIG_NESN = b'\xAE'
NRF52_CMD_CONFIG_SN = b'\xAF'
NRF52_CMD_BOOTLOADER_SEQ1 = b'\xA6'
NRF52_CMD_BOOTLOADER_SEQ2 = b'\xC7'
NRF52_CMD_LOG = b'\x7F'


class NRF52:
    """ 
        Driver for nRF2850 dongle or development-kit (dk)
    """

    n_debug = False
    event_counter = 0
    packets_buffer = []
    sent_pkt = None
    logs_pcap = False
    reset_cmd = None
    pcap_tx_handover = False


    def __init__(self, port_name=None, baudrate=115200, debug=False, logs_pcap=False, reset_cmd=None):
        if port_name is None:
            print(Fore.RED + 'No port name of nRF52840 provided!')
        self.serial = serial.Serial(port_name, baudrate)
        self.n_debug = debug
        self.logs_pcap = logs_pcap
        self.reset_cmd = reset_cmd
        self.set_log_tx(0)
        if self.n_debug:
            print('NRF52 Dongle: Instance started')

    
    def raw_send(self, pkt):
        raw_pkt = bytearray(pkt[:-3])  # Cut the 3 bytes CRC
        crc = bytearray([sum(raw_pkt) & 0xFF])  # Calculate CRC of raw packet data
        pkt_len = len(raw_pkt)  # Get raw packet data length
        l = bytearray([pkt_len & 0xFF, (pkt_len >> 8) & 0xFF])  # Pack length in 2 bytes (little infian)
        data = NRF52_CMD_DATA + l + raw_pkt + crc
        self.serial.write(data)
        if self.n_debug:
            print(Fore.CYAN + 'Bytes sent: ' + data.hex().upper())
        return data


    def send(self, scapy_pkt):
        self.raw_send(raw(scapy_pkt))
        if self.logs_pcap and self.pcap_tx_handover == 0:
            self.packets_buffer.append(NORDIC_BLE(board=75, protocol=2, flags=0x3) / scapy_pkt)

    
    def save_pcap(self, pcap_filename):
        if self.logs_pcap:
            wrpcap(pcap_filename, self.packets_buffer)  # save packet just sent
            self.packets_buffer = []


    def raw_receive(self):
        # Don't block when reading the cmd byte so that we can return quickly
        self.serial.timeout = 0
        c = self.serial.read(1)
        # If we received something, we block and read the whole message
        if len(c) == 0:
            return
        self.serial.timeout = None
        # Receive BLE adv or channel packets
        if c == NRF52_CMD_DATA or c == NRF52_CMD_DATA_TX:
            lb = ord(self.serial.read(1))
            hb = ord(self.serial.read(1))
            sz = lb | (hb << 8)
            lb = ord(self.serial.read(1))
            hb = ord(self.serial.read(1))
            evt_counter = lb | (hb << 8)
            data = bytearray(self.serial.read(sz))
            checksum = ord(self.serial.read(1))
            if (sum(data) & 0xFF) == checksum:
                # If the data received is correct
                self.event_counter = evt_counter
                
                if c == NRF52_CMD_DATA_TX:
                    self.sent_pkt = data
                    n_flags = 0x03
                    ret_data = None
                else:  # Received packets
                    n_flags = 0x01
                    ret_data = data

                if self.logs_pcap is True and data != None:
                    self.packets_buffer.append(NORDIC_BLE(board=75, protocol=2, flags=n_flags) / BTLE(data))

                if self.n_debug:
                    print("Hex: " + data.hex().upper())

                return ret_data
        # Receive logs from dongle
        elif c == NRF52_CMD_LOG:
            lb = ord(self.serial.read(1))
            hb = ord(self.serial.read(1))
            sz = lb | (hb << 8)
            data = self.serial.read(sz)
            print(data)
        elif c == NRF52_CMD_CHECKSUM_ERROR:
            print(Fore.RED + "NRF52_CMD_CHECKSUM_ERROR")


    def set_log_tx(self, value):
        data = NRF52_CMD_CONFIG_LOG_TX + bytearray([value])
        self.serial.write(data)
        self.pcap_tx_handover = value


    def reset_device(self):
        if self.reset_cmd is None:
            print(Fore.YELLOW + 'NRF52: Cannot reset device, no command provided')
            return
        print(Fore.YELLOW + 'NRF52: Starting device reset' + Fore.RESET)
        print(Fore.YELLOW + 'NRF52: Closing serial port...' + Fore.RESET)
        self.serial.close()
        while True:
            print(Fore.YELLOW + 'NRF52: Running reset command...' + Fore.RESET)
            exit_code = os.system(self.reset_cmd) >> 8
            if exit_code != 0:
                print(Fore.RED + f'Device reset command failed with exit code {exit_code}')
                raise RuntimeError('Device reset failed')
            print(Fore.YELLOW + 'NRF52: Opening serial port...' + Fore.RESET)
            try:
                self.serial.open()
                self.set_log_tx(0)
                break
            except:
                print(Fore.RED + f'Opening serial port failed, trying to reset again...')
                # This can potentially be an endless loop if the device
                # cannot be opened again. In that case, it's not so fun
                # to stop learning, as CTRL-C will only ever be received
                # by the reset_cmd process. We wait here for a moment
                # to allow the user to kill the python process.
                time.sleep(2)
        print(Fore.YELLOW + 'NRF52: Reset done' + Fore.RESET)
    

    def close(self):
        self.serial.close()
