#!/usr/bin/env bash

# This script sets up the python environment if it doesn't exist yet.
# It should be sourced (i.e. called with "source scripts/setup_venv.sh")
# so that the python environment will be available in the calling shell.

if [ -d "venv" ]; then
    # shellcheck source=/dev/null
    source venv/bin/activate
else
    # Create a venv and activate it
    python3 -m venv venv
    # shellcheck source=/dev/null
    source venv/bin/activate
    # Install dependencies from PyPi
    pip3 install -r requirements.txt
    # Install the BLESMPServer
    git clone https://github.com/apferscher/ble-learning.git
    cd ble-learning || exit
    git checkout febd774109c41a6635659b8847cc766e667841dd
    cd libs/smp_server || exit
    python3 setup.py install
    cd ../../..
    rm -rf ble-learning
fi
