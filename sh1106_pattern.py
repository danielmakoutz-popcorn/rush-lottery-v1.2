import time
import spidev
from RPi import GPIO

DC  = 22   # BCM (physical 15)
RST = 18   # BCM (physical 12)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(DC, GPIO.OUT)
GPIO.setup(RST, GPIO.OUT)

spi = spidev.SpiDev()
spi.open(0, 0)                 # bus 0, CE0
spi.max_speed_hz = 500000
spi.mode = 0

def cmd(*bytes_):
    GPIO.output(DC, 0)
    spi.xfer2(list(bytes_))

def data(bytes_):
    GPIO.output(DC, 1)
    spi.xfer2(bytes_)

def reset():
    GPIO.output(RST, 0)
    time.sleep(0.05)
    GPIO.output(RST, 1)
    time.sleep(0.05)

def set_page_col(page, col):
    # SH1106 page addressing + column set
    cmd(0xB0 | (page & 0x0F))             # page 0..7
    cmd(0x10 | ((col >> 4) & 0x0F))       # higher col nibble
    cmd(0x00 | (col & 0x0F))              # lower col nibble

reset()

# SH1106 init sequence (common for 128x64)
cmd(0xAE)        # display off
cmd(0xD5, 0x80)  # clock
cmd(0xA8, 0x3F)  # multiplex 1/64
cmd(0xD3, 0x00)  # display offset
cmd(0x40)        # start line 0
cmd(0xAD, 0x8B)  # DC-DC on (often needed on SH1106 modules)
cmd(0xA1)        # segment remap
cmd(0xC8)        # COM scan direction
cmd(0xDA, 0x12)  # COM pins
cmd(0x81, 0xCF)  # contrast
cmd(0xA4)        # resume to RAM content (not all pixels on)
cmd(0xA6)        # normal display
cmd(0xAF)        # display on
time.sleep(0.05)

# Clear + draw a checker pattern
COL_OFFSET = 2   # try 0, 2, 4 later if needed

for page in range(8):
    set_page_col(page, COL_OFFSET)
    row = []
    for i in range(128):
        row.append(0xAA if (page % 2 == 0) else 0x55)  # checker-ish stripes
    data(row)

print("Pattern written. You should see stripes/checker.")
spi.close()
GPIO.cleanup()
