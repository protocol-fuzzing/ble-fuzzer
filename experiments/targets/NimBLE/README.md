# NimBLE

NimBLE is an open source BLE stack that can either be tested entirely in software or on an nRF52840 DK board. To build it, the `newt` command line tool is used, which can be installed as a go package. The go installation instructions can be found [here](https://go.dev/doc/install) and then the `newt` tool can be installed with:

```sh
go install mynewt.apache.org/newt/newt@latest
```

After that, the tool can be used to download the necessary dependencies:

```sh
cd workspace
newt install
```

## Testing in software

First, build the testapp with:

```sh
newt build sim_testapp
```

This produces a binary under `workspace/bin/targets/sim_testapp/app/apps/testapp/testapp.elf`. This file can simply be executed to start the testapp with the NimBLE stack. It will print something like:

```
uart0 at /dev/pts/3
uart1 at /dev/pts/4
Waiting for UART connection...
```

The uart1 interface is the one that will be used with this test setup to exchange messages. NimBLE is configured in the software setup to use the MAC address `11:22:33:44:55:66`. A test would therefore be started like this:

```sh
java -jar target/ble-fuzzer-1.0-SNAPSHOT.jar @experiments/args/NimBLE_pairing -adapter /dev/pts/4 -connect "11:22:33:44:55:66"
```

## Testing on hardware

For testing on hardware, the default connection timeout of 40 seconds should be decreased to e.g. 13 seconds in NimBLE. The mapper relies on broken connections terminating themselves and we don't want to wait too long. The change can be done by setting `#define BLE_LL_CTRL_PROC_TIMEOUT_MS     (13000) /* ms */` in the file `repos/apache-mynewt-nimble/nimble/controller/include/controller/ble_ll_ctrl.h`. (This requires running `newt install` first to download the dependencies.)

Building NimBLE for hardware, which includes the testapp and a bootloader, and flashing the built code to a connected nRF52840 DK board is done as follows:

```sh
newt build nrf52_PCA10056_boot
newt build nrf52_PCA10056_testapp
newt create-image nrf52_PCA10056_testapp 1.0.0
newt load nrf52_PCA10056_boot
newt load nrf52_PCA10056_testapp
```
