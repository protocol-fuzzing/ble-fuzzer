#!/usr/bin/env bash

notify-send -t 3600000 -a ProtocolStateFuzzer -h string:x-canonical-private-synchronous:my-notification ProtocolStateFuzzer 'Device reset needed'
read -r -p 'PLEASE RESET THE DEVICE AND THEN PRESS ENTER TO CONTINUE...'
notify-send -t 1 -a ProtocolStateFuzzer -h string:x-canonical-private-synchronous:my-notification ProtocolStateFuzzer 'Continuing'

