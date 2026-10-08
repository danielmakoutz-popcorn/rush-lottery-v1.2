from luma.core.interface.serial import spi
from luma.oled.device import sh1106
from PIL import Image, ImageDraw

serial = spi(
    port=0,
    device=0,          # CE0
    gpio_DC=22,
    gpio_RST=18,
    bus_speed_hz=500000
)

device = sh1106(
    serial,
    width=128,
    height=64,
    rotate=0
)

# IMPORTANT: column offset fix
device._const.OFFSET = 0

img = Image.new("1", device.size)
draw = ImageDraw.Draw(img)

draw.rectangle(device.bounding_box, outline=255, fill=0)
draw.text((0, 24), "HELLO DANIEL", fill=255)

device.display(img)
print("Displayed HELLO with offset fix")

