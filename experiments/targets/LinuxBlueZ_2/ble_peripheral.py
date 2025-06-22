#!/usr/bin/python3

"""Copyright (c) 2019, Douglas Otwell

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import dbus

from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 5000

class LBSAdvertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("LBS")
        self.include_tx_power = True

class LEDButtonService(Service):
    UUID = "00001523-1212-efde-1523-785feabcd123"

    def __init__(self, index):
        Service.__init__(self, index, self.UUID, True)
        self.add_characteristic(LBSButtonCharacteristic(self))
        self.add_characteristic(LBSLEDCharacteristic(self))

class LBSButtonCharacteristic(Characteristic):
    UUID = "00001524-1212-efde-1523-785feabcd123"

    def __init__(self, service):
        self.notifying = False

        Characteristic.__init__(self, self.UUID, ["read"], service)
        self.add_descriptor(LBSButtonDescriptor(self))

    def ReadValue(self, options):
        return [dbus.Byte(0)]

class LBSButtonDescriptor(Descriptor):
    UUID = "2901"
    DESCRIPTOR_VALUE = "LBS Button"

    def __init__(self, characteristic):
        Descriptor.__init__(self, self.UUID, ["read"], characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value

class LBSLEDCharacteristic(Characteristic):
    UUID = "00001524-1212-efde-1523-785feabcd123"

    def __init__(self, service):
        Characteristic.__init__(self, self.UUID, ["read", "write"], service)
        self.add_descriptor(LBSLEDDescriptor(self))

    def WriteValue(self, value, options):
        self.val = int(value[0])
        print(f'LBS LED value: {self.val}')

    def ReadValue(self, options):
        return dbus.Byte(self.val)

class LBSLEDDescriptor(Descriptor):
    UUID = "2901"
    DESCRIPTOR_VALUE = "LBS LED"

    def __init__(self, characteristic):
        Descriptor.__init__(self, self.UUID, ["read"], characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value

app = Application()
app.add_service(LEDButtonService(0))
app.register()

adv = LBSAdvertisement(0)
adv.register()

try:
    app.run()
except KeyboardInterrupt:
    app.quit()
