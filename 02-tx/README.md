# COMM Board TX Test Script

This directory contains scripts and files to test the COMM board flight 401
bootloader and user program.

Prerequisite:

```bash
cd $HOME/git-repos/tartan-artibeus-ground-support/00-setup/
./setup_p3_venv.sh
source ../p3-env/bin/activate
```

Usage:

```bash
cd $HOME/git-repos/tartan-artibeus-ground-support/02-tx/
python3 tx_test.py /dev/ttyUSB0
```

Deactivate Python virtual environment:

```bash
deactivate
```

## Directory Contents

* [tx_test.py](tx_test.py): Test the transmitter
* [README.md](README.md): This document

## License

Written by Bradley Denby
Other contributors: Emily Ruppel

See the top-level LICENSE file for the license.
