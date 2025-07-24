#!/bin/sh
set -e

systemctl --user stop ble-peripheral
bluetoothctl power off > /dev/null 2>&1
echo "Restarting bluez"
# Configure sudo to allow running this without asking for a password
sudo "$(realpath scripts/reset_bluez.sh)"
sleep 2
echo "Powering on controller"
bluetoothctl power on > /dev/null 2>&1
sleep 2
echo "Starting BLE service"
systemctl --user start ble-peripheral
sleep 3
