#!/usr/bin/env python3

from bluez_peripheral.util import Adapter, get_message_bus
from bluez_peripheral.advert import Advertisement, AdvertisingIncludes
from bluez_peripheral.agent import NoIoAgent
from bluez_peripheral.gatt.service import Service
from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CharFlags
from bluez_peripheral.uuid import BTUUID

import asyncio
from uuid import UUID


class LBSService(Service):
    def __init__(self):
        super().__init__('00001523-1212-efde-1523-785feabcd123', True)

    @characteristic('00001524-1212-efde-1523-785feabcd123', CharFlags.ENCRYPT_READ)
    def button_characteristic(self, options):
        return bytes([0])


async def main():
    # Alternativly you can request this bus directly from dbus_next.
    bus = await get_message_bus()

    service = LBSService()
    await service.register(bus)

    # An agent is required to handle pairing 
    agent = NoIoAgent()
    # This script needs superuser for this to work.
    await agent.register(bus)

    adapter = await Adapter.get_first(bus)

    # Start an advert.
    advert = Advertisement("LBS", ['00001523-1212-efde-1523-785feabcd123'], 0x0080, 0)
    await advert.register(bus, adapter)

    print('Should be initialized, entering loop...')
    while True:
        # Handle dbus requests.
        await asyncio.sleep(5)

    await bus.wait_for_disconnect()


if __name__ == "__main__":
    asyncio.run(main())
