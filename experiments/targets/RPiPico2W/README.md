# RPiPico2W

Target board: Raspberry Pi Pico 2 W

## Building

(see instruction here: https://github.com/raspberrypi/pico-sdk?tab=readme-ov-file#unix-command-line)

```sh
# Install dependencies
sudo apt install cmake python3 build-essential gcc-arm-none-eabi libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib

# Download the pico-sdk
git clone --depth=1 --recurse-submodules https://github.com/raspberrypi/pico-sdk.git

# Build
cd peripheral
cmake -S . -B build -DPICO_SDK_PATH=../pico-sdk -DPICO_BOARD=pico2_w
cmake --build build -j $(nproc)
```

## Flashing

- Hold the `bootsel` button while plugging the board into the PC
- The board's bootloader should show a virtual file system, mount it somewhere
- Copy `build/picow_ble_peripheral.uf2` into the root directory and then eject it
- The board should automatically boot into the firmware
