#!/bin/bash
set -e

cd /home/daniel/oled
source /home/daniel/oled/venv/bin/activate

# optional: log stdout/stderr to a file
exec python /home/daniel/oled/lottery_ui_live.py

