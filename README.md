# Tartan Artibeus Ground Support

This repository provides ground support for the Tartan Artibeus satellite.

## Directory Contents

* [00-setup](00-setup/README.md): Setup scripts
* [01-rx](01-rx/README.md): Testbed receiver script
* [02-tx](02-tx/README.md): Testbed transmitter script
* [images](images/README.md): Repository images
* [README.md](README.md): This document

## Software Setup

From a Linux terminal (tested on Ubuntu 20.04):

1. Clone the repository:
```bash
cd $HOME
mkdir git-repos
cd git-repos/
git clone https://github.com/CMUAbstract/tartan-artibeus-ground-support.git
cd tartan-artibeus-ground-support/
```

2. Run the setup script:
```bash
cd 00-setup/
./setup_p3_venv.sh
```

## Testbed Preparation

![Testbed with Breadboard](images/testbed-00.png)

1. Connect an antenna with a u.FL connector to Board A. Connect another antenna
   with a u.FL connector to Board B.

2. Connect one of the FTDI cables to Board A. Connect the ground (black) wire to
   the "FTDI Cable GND" header. Connect the FTDI TX (orange) wire to the
   "FTDI Cable Orange" (Board A RX1) header. Connect the FTDI RX (yellow) wire
   to the "FTDI Cable Yellow" (Board A TX1) header.

3. Connect the other FTDI cable to Board B. Connect the ground (black) wire to
   the "FTDI Cable GND" header. Connect the FTDI TX (orange) wire to the
   "FTDI Cable Orange" (Board B RX1) header. Connect the FTDI RX (yellow) wire
   to the "FTDI Cable Yellow" (Board B TX1) header.

4. Set a variable power supply to output 3.3 V with a maximum current of 200 mA.
   Ensure that the power supply is **NOT** outputting power. Connect the power
   supply ground to the breadboard ground row (marked in black). A black wire is
   provided. Connect the power supply voltage to the breadboard voltage row
   (marked in red). A red wire is provided.

5. Connect the breadboard ground row to Board A GND. A black wire is provided.
   Connect the breadboard ground row to Board B GND. A black wire is provided.

6. **Ensure that the power supply is OFF.** Connect the breadboard voltage row
   to Board A 3.3 V. Connect the breadboard voltage row to Board B 3.3 V.

![Testbed with Antenna](images/testbed-01.png)

## Testbed Usage

Each of the FTDI USB cables must be connected to a computer running a terminal.
Both cables may be connected to the same computer, or each cable may be
connected to a different computer.

**The FTDI cables must be connected to an Earth-grounded computer,** e.g. a
desktop computer. A laptop computer, even while charging, is insufficient. We
recommend plugging the FTDI cables into a well-grounded, desktop computer.

1. Open a new terminal window. This window will be designated the RX Terminal.
   Before inserting Board A FTDI USB into the desktop computer, execute the
   following terminal command. Depending on the device configuration, you may
   receive "No such file or directory" or a list of devices.
```bash
ls -al /dev/ttyUSB*
```

2. Insert Board A FTDI USB into the desktop computer. Repeat the following
   terminal command. **Make note of the new device name**, e.g. `/dev/ttyUSB0`.
```bash
ls -al /dev/ttyUSB*
```

3. Open a new terminal window. This window will be designated the TX Terminal.
   Before inserting Board B FTDI USB into the desktop computer, execute the
   following terminal command. Depending on the device configuration, you may
   receive "No such file or directory" or a list of devices.
```bash
ls -al /dev/ttyUSB*
```

4. Insert Board B FTDI USB into the desktop computer. Repeat the following
   terminal command. Make note of the new device name, e.g. `/dev/ttyUSB1`.
```bash
ls -al /dev/ttyUSB*
```

5. Enable the power output on the variable power supply. Both Board A and Board
   B should exhibit a lit LED.

6. In the RX Terminal, execute the following commands. **Substitute the
   appropriate RX Terminal device name.**
```bash
cd $HOME/git-repos/tartan-artibeus-ground-support/01-rx/
source ../p3-env/bin/activate
python3 rx_test.py /dev/ttyUSB0
```

7. In the TX Terminal, execute the following commands. **Substitute the
   appropriate TX Terminal device name.**
```bash
cd $HOME/git-repos/tartan-artibeus-ground-support/02-tx/
source ../p3-env/bin/activate
python3 tx_test.py /dev/ttyUSB1
```

The TX Terminal should display a sequence of 12 transmitted commands. Each
command is transmitted via RF and received by the other board. The RX Terminal
should display a sequence of 12 matching received commands. The receiving board
replies to each command as it arrives. Both terminals display the command
replies; the RX Terminal displays the reply that is sent via RF, and the TX
Terminal displays the received reply.

After the test completes, deactivate the Python virtual environment in each
terminal with the following command.

```bash
deactivate
```

**Ensure that the power supply is turned OFF.**

## Manifest

* Testbed, including two mounted radio boards
* A tiny breadboard, two u.FL antenna, and jumper wires
* Two FTDI cables with jumper wires attached
* A primary radio board and a secondary, backup radio board
* Two spare FTDI cables
* Spare antenna (u.FL and SMA)
* A CC-Debugger

## License

Written by Bradley Denby  
Other contributors: None

See the top-level LICENSE file for the license.
