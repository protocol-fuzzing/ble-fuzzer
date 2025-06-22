# nRF52840

Building and flashing this project can be done with the following steps:

- Install the "nRF Connect for VS Code" extension in VS Code
- Use the extension to install the latest stable sdk and toolchain
- Open this folder, containing the nRF application
- Use the nRF extension to create a build configuration
    - Select as board target "nrf52840dongle/nrf52840"
- Use the nRF extension to build the project
- The built binary should be located in `build/nrf52840/zephyr/zephyr.hex`
- Connect the nRF52840 Dongle and put it into bootloader mode
    - To get into bootloader mode, the small reset button needs to be pressed
    - Attention: The reset button is not the white button that's clearly visible. There's another button right next to it that goes sideways.
- Use the tool [nRF Connect for Desktop](https://www.nordicsemi.com/Products/Development-tools/nRF-Connect-for-Desktop) to flash the built binary
