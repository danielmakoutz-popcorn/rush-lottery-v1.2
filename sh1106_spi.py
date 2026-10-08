import time
import spidev
from RPi import GPIO
from PIL import Image

class SH1106_SPI:
    """
    Minimal SH1106 128x64 SPI driver for Raspberry Pi.
    - SPI0 CE0 by default
    - DC and RST are BCM numbers
    """
    def __init__(self, dc=22, rst=18, spi_bus=0, spi_dev=0, speed_hz=500000, col_offset=2):
        self.DC = dc
        self.RST = rst
        self.col_offset = col_offset

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.DC, GPIO.OUT)
        GPIO.setup(self.RST, GPIO.OUT)

        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_dev)
        self.spi.max_speed_hz = speed_hz
        self.spi.mode = 0

        self.reset()
        self.init_display()

    def reset(self):
        GPIO.output(self.RST, 0)
        time.sleep(0.05)
        GPIO.output(self.RST, 1)
        time.sleep(0.05)

    def cmd(self, *bytes_):
        GPIO.output(self.DC, 0)
        self.spi.xfer2(list(bytes_))

    def data(self, bytes_):
        GPIO.output(self.DC, 1)
        self.spi.xfer2(list(bytes_))

    def init_display(self):
        # SH1106 init sequence (works on many 1.3" 128x64 modules)
        self.cmd(0xAE)        # display off
        self.cmd(0xD5, 0x80)  # clock
        self.cmd(0xA8, 0x3F)  # multiplex 1/64
        self.cmd(0xD3, 0x00)  # display offset
        self.cmd(0x40)        # start line 0
        self.cmd(0xAD, 0x8B)  # DC-DC on
        self.cmd(0xA1)        # segment remap
        self.cmd(0xC8)        # COM scan direction
        self.cmd(0xDA, 0x12)  # COM pins
        self.cmd(0x81, 0xCF)  # contrast
        self.cmd(0xA4)        # RAM display
        self.cmd(0xA6)        # normal display
        self.cmd(0xAF)        # display on
        time.sleep(0.02)

    def set_page_col(self, page, col):
        self.cmd(0xB0 | (page & 0x0F))
        self.cmd(0x10 | ((col >> 4) & 0x0F))
        self.cmd(0x00 | (col & 0x0F))

    def clear(self):
        for page in range(8):
            self.set_page_col(page, self.col_offset)
            self.data([0x00] * 128)

    def display_image(self, img: Image.Image):
        """
        img must be 128x64, mode '1' (1-bit). We'll pack it into SH1106 pages.
        """
        if img.mode != "1":
            img = img.convert("1")
        if img.size != (128, 64):
            img = img.resize((128, 64))

        pixels = img.load()

        for page in range(8):
            self.set_page_col(page, self.col_offset)
            buf = []
            y0 = page * 8
            for x in range(128):
                b = 0
                for bit in range(8):
                    y = y0 + bit
                    # In PIL mode '1', pixel is 0 or 255
                    if pixels[x, y] != 0:
                        b |= (1 << bit)
                buf.append(b)
            self.data(buf)

    def close(self):
        try:
            self.spi.close()
        finally:
            GPIO.cleanup()
