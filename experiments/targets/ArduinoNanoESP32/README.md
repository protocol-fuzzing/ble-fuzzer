# Arduino Nano ESP32

The easiest way to build and flash the program is to install the Arduino IDE. In there, install the board support package "Arduino ESP32 Boards" and simply click on the compile/flash buttons. Alternatively, the `arduino-cli` can be used for building an flashing:

```sh
arduino-cli compile -b arduino:esp32:nano_nora peripheral.ino
arduino-cli upload peripheral.ino -p /dev/ttyACM0 -b arduino:esp32:nano_nora
```

