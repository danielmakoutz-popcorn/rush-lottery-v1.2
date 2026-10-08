# RUSH Lottery v1.2

A **Raspberry Pi hardware/software experiment** combining a small SPI OLED display, a character animation system, device startup automation, Wi-Fi setup support, and a Bitcoin-style hashing demonstration.

This project brings together embedded Linux administration, Python graphics, device I/O, and a continuously updating local interface.

## What's in the repository

- `lottery_hash.py`: threaded double-SHA256 hashing simulation using an 80-byte header and changing nonce; records hash attempts, best hash, and hashes per second.
- `lottery_ui_live.py`: main OLED-oriented interface and animated RUSH character.
- `animations/`: frames for status/idle/event animations.
- `sh1106_spi.py`: SH1106 OLED communication helpers over SPI.
- `wifi_provision/`: experimental network setup helpers for a Raspberry Pi.
- `lottery-miner.service.v1_1`: systemd unit example for automatic startup.
- `requirements.lock.txt`: Python dependency versions used during development.

## Hardware and environment

Designed around a **Raspberry Pi running Linux** with a compatible **SH1106 SPI OLED display**. GPIO/SPI wiring, display configuration, and OS permissions must match your specific hardware.

Install dependencies in a Python virtual environment on the target Pi, then from the project folder run:

```bash
python lottery_ui_live.py
```

Startup scripts and the sample systemd unit contain the original developer's local absolute paths. **Update those paths** before using them on another machine.

## Important distinction

The hashing routine uses Bitcoin-style double-SHA256 and a configurable toy difficulty target for educational visualization. **It is not evidence of Bitcoin network mining, block discovery, or pool integration.**

Wi-Fi provisioning helpers are experimental; review access point security and test them on an isolated device before use.

## Engineering takeaways

This project explores **embedded Python, SPI peripherals, threaded background work, live metric presentation, Linux services, log handling, and hardware-oriented debugging**.
