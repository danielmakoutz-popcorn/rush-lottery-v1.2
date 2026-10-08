import time
import spidev
from RPi import GPIO

DC = 22     # BCM
RST = 18    # BCM

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(DC, GPIO.OUT)
GPIO.setup(RST, GPIO.OUT)

# Hard reset the display
GPIO.output(RST, 0)
time.sleep(0.05)
GPIO.output(RST, 1)
time.sleep(0.05)

spi = spidev.SpiDev()
spi.open(0, 0)              # bus 0, device 0 (CE0)
spi.max_speed_hz = 500000
spi.mode = 0

def cmd(b):
    GPIO.output(DC, 0)
    spi.xfer2([b])

def data(bytes_):
    GPIO.output(DC, 1)
    spi.xfer2(bytes_)

# Basic init sequence that often causes *some* visible change even if not perfect
for c in [0xAE, 0xA5, 0xAF]:   # display off, all pixels on, display on
    cmd(c)
    time.sleep(0.2)

# Blast a bunch of data
for _ in range(10):
    data([0xFF] * 128)
    time.sleep(0.1)
    data([0x00] * 128)
    time.sleep(0.1)

spi.close()
GPIO.cleanup()
print("SPI blast done")
