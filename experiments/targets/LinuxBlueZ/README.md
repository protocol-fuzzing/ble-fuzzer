# LinuxBlueZ

This testapp configures BlueZ to advertise a simple characteristic. I recommend changing some settings in BlueZ's configuration (`/etc/bluetooth/main.conf`) to avoid that BlueZ sends requests to the tester asking for device information as this can lead to non-determinism during testing. The settings that should be changed are:

```
ReverseServiceDiscovery = false
NameResolving = false
```

To run this app, a python environment with the dependency `bluez-peripheral` is required:

```sh
pip3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

Due to some change that was made in a newer version of BlueZ, I had to add the following to `venv/lib/python3.13/site-packages/bluez_peripheral/advert.py`:

```python
    @dbus_property()
    def TxPower(self) -> "n":  # type: ignore
        return 0

    @TxPower.setter
    def TxPower(self, val: 'n'):  # type: ignore
        pass
```

The python script can either be executed directly, or a systemd service can be used to manage it. To use systemd, adapt the paths in `ble-peripheral.service` and copy it to `/home/<user>/.config/systemd/user/ble-peripheral.service`. The service can then be managed with the commands:

```sh
systemctl --user start ble-peripheral
systemctl --user status ble-peripheral
systemctl --user stop ble-peripheral
```
