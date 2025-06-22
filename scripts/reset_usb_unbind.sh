#!/bin/sh
set -e

# This file tries to write to the files
#   /sys/bus/usb/drivers/usb/unbind
#   /sys/bus/usb/drivers/usb/bind
# so they need to be writable by the user running this script.
# Either make them writable with
#   sudo chmod 222 /sys/bus/usb/drivers/usb/unbind
#   sudo chmod 222 /sys/bus/usb/drivers/usb/bind
# or alternatively run this script as root.
# (It might make sense to configure sudo to not ask for a password in that case.)

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <usb-device>"
    exit 1
fi

USB_DEVICE="$1"
echo "$USB_DEVICE" > /sys/bus/usb/drivers/usb/unbind
sleep 3
echo "$USB_DEVICE" > /sys/bus/usb/drivers/usb/bind
sleep 5

