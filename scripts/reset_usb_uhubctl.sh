#!/bin/sh
set -e

# Adjust the device ids
sudo uhubctl -l 3-2 -p 1-3 -a cycle -d 10
