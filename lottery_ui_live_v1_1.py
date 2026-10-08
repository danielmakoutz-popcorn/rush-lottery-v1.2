import time
import random
import hashlib
import signal
import sys
import logging
import os
import subprocess
import json
from PIL import Image, ImageDraw, ImageFont
from sh1106_spi import SH1106_SPI
from lottery_hash import LotteryHasher
from animations.rush_rest import RUSH_REST_FRAMES
from animations.rush_found import RUSH_FOUND_FRAMES
from animations.rush_morning import RUSH_MORNING_FRAMES
from animations.rush_clean import RUSH_CLEAN_FRAMES
from animations.rush_alien import RUSH_ALIEN_FRAMES
from animations.rush_overheat import RUSH_OVERHEAT_FRAMES
from logging.handlers import RotatingFileHandler

RUSH_FRAMES = [
    # Frame 1
    [
        "............................",
        "............................",
        "............xxx.............",
        "...........xxxxxxxxx........",
        "..........x....x............",
        ".........x....x.x...........",
        ".........x......x...........",
        "..........xx..xx............",
        "............xx..............",
        "............xx..............",
        "...........xxx..............",
        "..........x.xxx.....xxx.....",
        "..........x.xx.x....x.x.....",
        "...........xxx..xxx.xxx.....",
        "............xx.....xx.......",
        "............xxxxxxxxx.......",
        "............xx..............",
        "............xx..............",
        "............xx..............",
        "............xx..............",
        "............xx..............",
        "............xx..............",
        "...........x..x.............",
        "..........x....x............",
        ".........x......x...........",
        "........x........x..........",
        ".......x..........x.........",
        "......x............x........",
        ".....x..............x.......",
        ".....x..............x.......",
        "....x................x......",
        "....x................x......",
        "...x..................x.....",
        "...x..................x.....",
        "...x..................x.....",
    ],

    # Frame 2
    [
        "............................",
        "............................",
        ".................xxx........",
        "................xxxxxxxxx...",
        "...............x....x.......",
        "..............x....x.x......",
        "..............x......x......",
        "...............xx..xx.......",
        ".................xx.........",
        ".................xx.........",
        "................xx..........",
        "...............xxxx....xxx..",
        "...............xxx.x...x.x..",
        "...............xxx..x..xxx..",
        "..............xx..x..xxx....",
        "..............xx..x....xx...",
        ".............xx....xx...xx..",
        ".............xx......xxxxx..",
        ".............xx.............",
        "............xx..............",
        "............xx..............",
        "............xx..............",
        "...........x..x.............",
        "..........x....x............",
        ".........x......x...........",
        "........x........x..........",
        ".......x..........x.........",
        "......x............x........",
        ".....x..............x.......",
        ".....x..............x.......",
        "....x................x......",
        "....x................x......",
        "...x..................x.....",
        "...x..................x.....",
        "...x..................x.....",
    ],

    # Frame 3
    [
        "............................",
        "............................",
        "............................",
        "...................xxxx.....",
        "..................x....x....",
        ".................x......x...",
        "................x.......xx..",
        ".................x....x.xx..",
        "..................xxx...xx..",
        ".................xx.xxx.x...",
        "................xx......x...",
        "...............xxxx....xxx..",
        "...............xxx.x...x.x..",
        "...............xxx..x..xxx..",
        "..............xx..x..xxx....",
        "..............xx..x....x....",
        ".............xx....x....x...",
        "..............xx....x....x..",
        "..............xx.....xx..xx.",
        ".............xx........xx.xx",
        ".............xx..........xxx",
        "............xx..............",
        "...........x..x.............",
        "..........x....x............",
        ".........x......x...........",
        "........x........x..........",
        ".......x..........x.........",
        "......x............x........",
        ".....x..............x.......",
        ".....x..............x.......",
        "....x................x......",
        "....x................x......",
        "...x..................x.....",
        "...x..................x.....",
        "...x..................x.....",
    ],

    # Frame 4 (arc flash / active)
    [
        "............................",
        "............................",
        "............................",
        "...................xxxx.....",
        "..................x....x....",
        ".................x......x...",
        "................x..xx...xx..",
        ".................x.xx.x.xx..",
        "..................xxx...xx..",
        ".................xx.xxx.x...",
        "................xx......x...",
        "...............xxxx...xxxx..",
        "...............xxx.x..xx.x..",
        "...............xxx..x.xxxx..",
        "..............xx..x..xxx....",
        "..............xx..x....x....",
        ".............xx....x....x...",
        "..............xx....x....x..",
        "..............xx.....xx..xx.",
        ".............xx........xx.xx",
        ".............xx..........xxx",
        "............xx..............",
        "...........x..x.............",
        "..........x....x............",
        ".........x......x...........",
        "........x........x..........",
        ".......x..........x.........",
        "......x............x........",
        ".....x..............x.......",
        ".....x..............x.......",
        "....x................x......",
        "....x................x......",
        "...x..................x.....",
        "...x..................x.....",
        "...x..................x.....",
    ],

    # Frame 5
    [
        "............................",
        "............................",
        ".................xxx........",
        "................xxxxxxxxx...",
        "...............x....x.......",
        "..............x....x.x......",
        "..............x......x......",
        "...............xx..xx.......",
        ".................xx.........",
        ".................xx.........",
        "................xx..........",
        "...............xxxx....xxx..",
        "...............xxx.x...x.x..",
        "...............xxx..x..xxx..",
        "..............xx..x..xxx....",
        "..............xx..x....xx...",
        ".............xx....xx...xx..",
        ".............xx......xxxxx..",
        ".............xx.............",
        "............xx..............",
        "............xx..............",
        "............xx..............",
        "...........x..x.............",
        "..........x....x............",
        ".........x......x...........",
        "........x........x..........",
        ".......x..........x.........",
        "......x............x........",
        ".....x..............x.......",
        ".....x..............x.......",
        "....x................x......",
        "....x................x......",
        "...x..................x.....",
        "...x..................x.....",
        "...x..................x.....",
    ],

    # Frame 6
    [
        "............................",
        "............................",
        "............xxxx............",
        "...........xxxxxxx..........",
        "..........x....xxx..........",
        ".........x....x..x..........",
        "..........x......xx.........",
        "...........x....x..x........",
        "............xxxx............",
        "............xx..............",
        "...........xxx..............",
        "..........x.xxx......xxxx...",
        "..........x.xx.x....xx.x....",
        "...........xxx..xx..xxx.....",
        "............xx....xx........",
        "............xxxxxxxx........",
        "............xx..............",
        "............xx..............",
        "............xx..............",
        "............xx..............",
        "............xx..............",
        "............xx..............",
        "...........x..x.............",
        "..........x....x............",
        ".........x......x...........",
        "........x........x..........",
        ".......x..........x.........",
        "......x............x........",
        ".....x..............x.......",
        ".....x..............x.......",
        "....x................x......",
        "....x................x......",
        "...x..................x.....",
        "...x..................x.....",
        "...x..................x.....",
    ],
]

LOG_PATH = "/home/daniel/oled/logs/rush.log"
USE_BITCOIN_NODE = True
BITCOIN_CLI = "bitcoin-cli"   # or "/usr/local/bin/bitcoin-cli" if needed
BTC_POLL_SECS = 5.0

def setup_logging():
    os.makedirs("/home/daniel/oled/logs", exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(
        LOG_PATH,
        maxBytes=1_000_000,   # 1 MB each
        backupCount=5         # keep 5 old logs
    )
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(fmt)

    # avoid duplicate handlers if script restarts
    if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        logger.addHandler(handler)

    # also log to console (journalctl)
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        console = logging.StreamHandler()
        console.setFormatter(fmt)
        logger.addHandler(console)

def draw_cloud(d, x, y):
    # ~14x6 cloud, 1-bit
    d.ellipse((x+0, y+2, x+6, y+6), outline=1, fill=0)
    d.ellipse((x+4, y+0, x+10, y+5), outline=1, fill=0)
    d.ellipse((x+8, y+2, x+13, y+6), outline=1, fill=0)
    d.line((x+2, y+6, x+11, y+6), fill=1)

def draw_lightning(d, x, y):
    # tiny bolt under cloud
    d.line((x+6, y+5, x+4, y+8), fill=1)
    d.line((x+4, y+8, x+7, y+8), fill=1)
    d.line((x+7, y+8, x+5, y+11), fill=1)

def draw_weather_overlay(d, box, weather, now, night):
    """
    Minimal, non-busy weather context drawn inside the clock box.
    Clouds at top edge, occasional lightning.
    Snow piles in bottom-right corner of the clock box.
    """
    x0, y0, x1, y1 = box

    # Keep it subtle at night
    if night and weather in ("RAIN", "SNOW", "STORM"):
        cloud_count = 1
    else:
        cloud_count = 2 if weather in ("RAIN", "SNOW", "STORM") else 0

    # Clouds along the top of the clock box
    if cloud_count:
        base_y = y0 + 2
        drift = int(now * 2) % 14  # slow drift
        for i in range(cloud_count):
            cx = x0 + 6 + i * 18 + drift
            # wrap
            if cx > x1 - 16:
                cx = x0 + 2 + (cx - (x1 - 16))
            draw_cloud(d, cx, base_y)

    # Lightning (rare)
    if weather == "STORM":
        # about once every ~8–15 seconds-ish depending on timing
        if int(now * 10) % 97 == 0:
            lx = x0 + 20 + (int(now) % 10)
            ly = y0 + 3
            draw_lightning(d, lx, ly)

    # Snow piles in bottom-right corner (clock box)
    if weather == "SNOW":
        px = x1 - 20
        py = y1 - 8
        # three little mounds
        d.arc((px, py, px+8, py+6), 180, 360, fill=1)
        d.arc((px+6, py+1, px+14, py+7), 180, 360, fill=1)
        d.arc((px+12, py, px+20, py+6), 180, 360, fill=1)

def get_cpu_temp_c():
    """
    Reads Pi CPU temp in Celsius. Returns None if unavailable.
    """
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return int(f.read().strip()) / 1000.0
    except Exception:
        return None

def draw_temp_icon(d, x, y, level="ok"):
    """
    Tiny 8x8 thermometer-ish icon.
    level: "ok" | "warm" | "hot"
    """
    # bulb
    d.ellipse((x+1, y+4, x+3, y+6), outline=1)
    # stem
    d.line((x+2, y+1, x+2, y+4), 1)
    # tick (only if warm/hot)
    if level in ("warm", "hot"):
        d.point((x+4, y+2), 1)
    # alert pixel (only if hot)
    if level == "hot":
        d.point((x+6, y+1), 1)

def has_wifi_ip():
    """
    Cheap 'am I connected' check: wlan0 has an IPv4 address.
    """
    try:
        import subprocess
        r = subprocess.run(["/bin/sh", "-lc", "ip -4 addr show wlan0 | grep -q 'inet '"], check=False)
        return r.returncode == 0
    except Exception:
        return False

def draw_wifi_icon(d, x, y, ok=True):
    """
    Tiny 8x8 wifi-ish glyph. ok=False shows an 'X' mark.
    """
    if not ok:
        d.line((x+1, y+1, x+6, y+6), 1)
        d.line((x+6, y+1, x+1, y+6), 1)
        return
    # simple arcs + dot
    d.point((x+3, y+6), 1)
    d.point((x+2, y+5), 1); d.point((x+4, y+5), 1)
    d.point((x+1, y+4), 1); d.point((x+5, y+4), 1)

def watchdog_ping():
    #only matters when running undersystemd with type=notify
    try:
        os.system("systemd-notify WATCHDOG=1 >/dev/null 2>&1")
    except Exception:
        pass
def draw_sprite(draw, x, y, frame_lines):
    for row, line in enumerate(frame_lines):
        for col, ch in enumerate(line):
            if ch != '.':
                draw.point((x + col, y + row), fill=1)

def is_night():
    hour = time.localtime().tm_hour
    return hour >= 22 or hour < 5

running = True
def _stop(*args):
    global running
    running = False

def daily_weather_state():
    """
    Deterministic weather that changes once per local day.
    """
    day = time.strftime("%Y-%m-%d")
    h = hashlib.sha256(day.encode()).digest()
    r = h[0]  # 0-255
    if r < 120:
        return "CLEAR"
    elif r < 190:
        return "RAIN"
    elif r < 240:
        return "SNOW"
    else:
        return "STORM"

def draw_weather_icon(d, x, y, weather):
    """
    Tiny 10x10-ish icon in 1-bit pixels.
    """
    if weather == "CLEAR":
        # Sun
        d.ellipse((x+2, y+2, x+7, y+7), outline=1)
        d.point((x+4, y), 1); d.point((x+4, y+9), 1)
        d.point((x, y+4), 1); d.point((x+9, y+4), 1)
    elif weather == "RAIN":
        # Cloud + drops
        d.ellipse((x+1, y+2, x+6, y+6), outline=1)
        d.ellipse((x+4, y+1, x+9, y+6), outline=1)
        d.line((x+2, y+6, x+8, y+6), 1)
        d.point((x+3, y+8), 1); d.point((x+6, y+9), 1); d.point((x+8, y+8), 1)
    elif weather == "SNOW":
        # Snowflake-ish
        d.point((x+5, y+5), 1)
        d.line((x+5, y+2, x+5, y+8), 1)
        d.line((x+2, y+5, x+8, y+5), 1)
        d.point((x+3, y+3), 1); d.point((x+7, y+3), 1)
        d.point((x+3, y+7), 1); d.point((x+7, y+7), 1)
    else:  # "STORM"
        # Bolt
        d.line((x+6, y+1, x+3, y+6), 1)
        d.line((x+3, y+6, x+6, y+6), 1)
        d.line((x+6, y+6, x+4, y+9), 1)

def draw_status_icon(d, x, y, status_msg):
    """
    Tiny 8x8 status icon.
    """
    if status_msg.startswith("FOUND"):
        # Star
        d.point((x+3, y), 1); d.point((x+3, y+6), 1)
        d.point((x, y+3), 1); d.point((x+6, y+3), 1)
        d.point((x+1, y+1), 1); d.point((x+5, y+1), 1)
        d.point((x+1, y+5), 1); d.point((x+5, y+5), 1)
    else:
        # Magnifier-ish
        d.ellipse((x+1, y+1, x+5, y+5), outline=1)
        d.line((x+5, y+5, x+7, y+7), 1)

def maybe_refresh_daily_weather(weather_state, weather_day_str):
    """
    Returns (weather_state, weather_day_str) and refreshes at midnight.
    """
    today = time.strftime("%Y-%m-%d")
    if today != weather_day_str:
        return daily_weather_state(), today
    return weather_state, weather_day_str

def draw_nostromo_env(d, box, now, night, weather):
    """
    Draws an industrial sci-fi environment inside `box` (x0,y0,x1,y1).
    Subtle at night, a bit livelier in day. Weather can influence grit/condensation.

    Returns:
      dict with anchor points for effects/alignment:
        - "plug": (x, y) where cable plugs / arc origin
        - "console_box": (cx0, cy0, cx1, cy1)
    """
    x0, y0, x1, y1 = box

    # Interior border inset (gives "panel frame" depth)
    d.rectangle((x0+1, y0+1, x1-1, y1-1), outline=1, fill=0)

    # Floor grating strip along the bottom (hallway vibe)
    floor_y0 = y1 - 5
    floor_y1 = y1 - 2
    d.rectangle((x0+2, floor_y0, x1-2, floor_y1), outline=1, fill=0)

    # Grate slats
    slat_step = 4 if night else 3
    for x in range(x0+3, x1-2, slat_step):
        for y in range(floor_y0+1, floor_y1):
            d.point((x, y), fill=1)

    # Bulkhead ribs (vertical beams)
    rib_step = 10
    for rx in range(x0+6, x1-2, rib_step):
        for y in range(y0+3, y1-7, 2):
            if night and (y % 4 == 0):
                continue
            d.point((rx, y), fill=1)

    # --- LEFT SIDE: remove the "hard wall line" feeling ---
    # Keep some flavor, but avoid a continuous vertical edge.
    pipe_x = x0 + 4  # moved 1px inward
    for y in range(y0+5, y1-6, 3):
        # break up the pipe so it doesn't read like a wall line
        if (y % 9) == 0:
            continue
        d.point((pipe_x, y), fill=1)
        # optional second pixel only in daytime to hint thickness
        if not night and (y % 6 != 0):
            d.point((pipe_x+1, y), fill=1)

    # Elbow pipe across top-left (keep subtle)
    for x in range(x0+4, x0+10, 2):
        d.point((x, y0+4), fill=1)

    # Overhead conduit (top run)
    conduit_y = y0 + 3
    for x in range(x0+4, x1-6, 2):
        d.point((x, conduit_y), fill=1)
    # small junction nodes
    for x in range(x0+8, x1-8, 8):
        d.point((x, conduit_y+1), fill=1)

    # --- RIGHT SIDE: WALL CONSOLE (replaces the old vent-grating) ---
    # Console frame on the right wall
    cx1 = x1 - 3
    cx0 = cx1 - 11
    cy0 = y0 + 7
    cy1 = y1 - 7

    d.rectangle((cx0, cy0, cx1, cy1), outline=1, fill=0)

    # small "screen" at top of console
    d.rectangle((cx0+2, cy0+2, cx1-2, cy0+9), outline=1, fill=0)

    # tiny activity pixels on screen (subtle)
    if not night and (int(now * 2) % 2 == 0):
        d.point((cx0+3, cy0+4), fill=1)
        d.point((cx0+5, cy0+6), fill=1)
        d.point((cx0+7, cy0+5), fill=1)

    # buttons / vents
    d.rectangle((cx0+2, cy0+12, cx0+5, cy0+15), outline=1, fill=0)
    d.rectangle((cx0+7, cy0+12, cx0+9, cy0+15), outline=1, fill=0)

    # plug port near bottom-left of console
    port_x0 = cx0 + 2
    port_y0 = cy1 - 5
    d.rectangle((port_x0, port_y0, port_x0+4, port_y0+3), outline=1, fill=0)
    plug = (port_x0 + 2, port_y0 + 1)

    # OPTIONAL: a thin "right hall wall line" just inside the border
    # (keeps depth while leaving left side more open)
    d.line((x1-2, y0+2, x1-2, y1-2), fill=1)

    # Drifting dust / grit (subtle particles inside box)
    dust_density = 3 if night else 6
    if weather in ("RAIN", "SNOW"):
        dust_density = max(2, dust_density - 2)

    slice_id = int(now * (2 if night else 4))
    for i in range(dust_density):
        px = x0 + 2 + ((slice_id * (17 + i*13)) % (x1 - x0 - 3))
        py = y0 + 3 + ((slice_id * (11 + i*7)) % (y1 - y0 - 6))
        d.point((px, py), fill=1)

    # Occasional electrical arc (rare), triggered by time pattern
    # We'll keep it but move it closer to the console area so it feels "system-y"
    if night:
        arc_tick = int(now * 80)  # slower overall
        arc_now = (arc_tick % 97 == 0)
    else:
        arc_tick = int(now * 120)
        arc_now = (arc_tick % 61 == 0)

    if arc_now:
        ax, ay = plug
        # a tiny jagged spark near the plug
        d.point((ax, ay), fill=1)
        d.point((ax+1, ay-1), fill=1)
        d.point((ax+2, ay), fill=1)
        if not night:
            d.point((ax+3, ay-1), fill=1)

    # Rare steam puff (tiny dots rising) near bottom-left of console
    if (int(now) % 13 == 0) and (not night):
        sx = cx0 - 4
        sy = y1 - 10
        for i in range(3):
            d.point((sx + i, sy - i), fill=1)

    return {"plug": plug, "console_box": (cx0, cy0, cx1, cy1)}

def main():
    setup_logging()
    logging.info("Rush UI starting...")
    global running
    oled = SH1106_SPI(dc=22, rst=18, spi_bus=0, spi_dev=0, speed_hz=500000, col_offset=2)
    oled.clear()

    font = ImageFont.load_default()
    # Bigger font for the big clock (fallback to default if missing)
    try:
        big_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 26)
    except Exception:
        big_font = font

    # Start the background hasher
    hasher = LotteryHasher(target_leading_zero_bits=20, batch_size=2000)
    hasher.start()

    # register shutdown handlers
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    anim_idx = 0
    anim_timer = 0.0
    last_mode = None

    tick_prev = time.monotonic()

    miner_x = 89
    miner_y = 31

    last_found = 0
    found_flash_until = 0.0

    stars = [
        {"x": random.randint(0,127), "y": random.randint(0,63), "spd": random.choice([0.1, 0.2, 0.3])}
        for _ in range(20)
    ]

    # ---- Weather init (seeded daily) ----
    weather_day_str = time.strftime("%Y-%m-%d")
    weather = daily_weather_state()

    # Particles
    raindrops = [{"x": random.randint(0,127), "y": random.randint(0,63), "spd": random.randint(2,5)} for _ in range(14)]
    snowflakes = [{"x": random.randint(0,127), "y": random.randint(0,63), "sx": random.choice([-1,0,1]), "spd": random.choice([0.3,0.5,0.7])} for _ in range(18)]

    storm_flash_until = 0.0

    rot_i = 0
    rot_next = 0.0
    rot_period = 2.2

    last_watchdog = 0.0

    # -----------------------------
    # Rush animation state machine
    # -----------------------------
    FORCE_OVERHEAT = False  # later: set True automatically via temp monitoring
    TEMP_WARM_C = 75.0
    TEMP_HOT_C = 80.0

    # "Once every 2 minutes" alien roll:
    panic_until = 0.0
    next_panic_roll = time.time() + 120.0
    PANIC_CHANCE = 0.50          # tweak: chance each roll (0.35 = 35%)
    PANIC_DURATION = 4.0         # seconds the panic animation plays

    # Daily schedule toggles (reset at midnight)
    sched_day = time.strftime("%Y-%m-%d")
    did_morning = False
    did_clean = False

    # Define time windows (local time on the Pi)
    MORNING_START = (6, 0)       # 06:00
    MORNING_END   = (9, 15)      # 09:15 (tweak)
    CLEAN_TIME    = (9, 30)      # 09:30 (or set to (10,0))

    # Frames + FPS per mode
    RUSH_WORK_FRAMES = RUSH_FRAMES   # your existing "work" loop frames

    FRAMES_BY_MODE = {
        "work":     RUSH_WORK_FRAMES,
        "rest":     RUSH_REST_FRAMES,
        "found":    RUSH_FOUND_FRAMES,
        "morning":  RUSH_MORNING_FRAMES,
        "clean":    RUSH_CLEAN_FRAMES,
        "alien":    RUSH_ALIEN_FRAMES,
        "overheat": RUSH_OVERHEAT_FRAMES,
    }

    FPS_BY_MODE = {
        "work":     1.0,
        "rest":     1.0,
        "found":    6.0,
        "morning":  1.0,
        "clean":    3.0,
        "alien":    1.0,
        "overheat": 1.0,
    }

    def _in_window(hm, start, end):
        # hm/start/end are (hour, minute)
        return start <= hm < end

    # --- Sticky mode control ---
    mode = "work"
    mode_hold_until = 0.0          # don’t allow dropping the mode until this time
    last_mode = None

    clean_until = 0.0  # 0 = inactive

    # optional: if you want certain modes to play once per trigger
    played_found = False
    played_clean = False

    try:
        while running:
            now = time.time()
            # refresh daily weather at midnight
            weather, weather_day_str = maybe_refresh_daily_weather(weather, weather_day_str)
            night = is_night()

            cpu_temp_c = get_cpu_temp_c()
            wifi_ok = has_wifi_ip()

            temp_level = "ok"
            if cpu_temp_c is not None:
                if cpu_temp_c >= TEMP_HOT_C:
                    temp_level = "hot"
                elif cpu_temp_c >= TEMP_WARM_C:
                    temp_level = "warm"

            # If you want overheat animation to actually trigger now:
            if temp_level == "hot":
                FORCE_OVERHEAT = True

            if now - last_watchdog >= 1.0:
                watchdog_ping()
                last_watchdog = now

            # -----------------------------
            # Mode selection (what Rush is doing)
            # -----------------------------
            lt = time.localtime()
            hm = (lt.tm_hour, lt.tm_min)

            # Reset daily flags at midnight
            day_str = time.strftime("%Y-%m-%d")
            if day_str != sched_day:
                sched_day = day_str
                did_morning = False
                did_clean = False

            # --- real delta time (fixes short/1-frame animations) ---
            now_m = time.monotonic()
            dt = now_m - tick_prev
            tick_prev = now_m
            if dt < 0:
                dt = 0.0
            if dt > 0.25:
                dt = 0.25  # clamp so a stall doesn't skip a billion frames

            # ---------------- mode selection ----------------
            mode = "work"

            # Night -> rest
            if night:
                mode = "rest"

            # Morning window (only once per day)
            if (not did_morning) and _in_window(hm, MORNING_START, MORNING_END):
                mode = "morning"
            elif (not did_morning) and (hm >= MORNING_END):
                did_morning = True

            # Clean at a specific time (only once per day)
            if (not did_clean) and (hm >= CLEAN_TIME):
                mode = "clean"
                if clean_until <= 0.0:
                    clean_until = now_m + 8.0  # run clean for 8 seconds

            # Found flash overrides almost everything
            if now < found_flash_until:
                mode = "found"

            # Alien panic roll: check once every 2 minutes
            if now >= next_panic_roll:
                next_panic_roll = now + 120.0
                if random.random() < PANIC_CHANCE:
                    panic_until = now + PANIC_DURATION

            if now < panic_until:
                mode = "alien"

            # Overheat override (manual until we add temp monitoring)
            if FORCE_OVERHEAT:
                mode = "overheat"

            # End clean after its duration
            if mode == "clean" and clean_until > 0.0 and now_m >= clean_until:
                did_clean = True
                clean_until = 0.0
                mode = "work" if not night else "rest"

            # --- Animation selection ---
            active_frames = FRAMES_BY_MODE.get(mode) or FRAMES_BY_MODE["work"]
            anim_fps = FPS_BY_MODE.get(mode, 6.0)

            # Reset frame only when the mode actually changes
            if mode != last_mode:
                anim_idx = 0
                anim_accum = 0.0
                last_mode = mode

            anim_accum += dt
            frame_period = 1.0 / max(anim_fps, 0.1)

            while anim_accum >= frame_period:
                anim_accum -= frame_period
                anim_idx = (anim_idx + 1) % len(active_frames)

            # read stats safely
            with hasher.stats.lock:
                attempts = hasher.stats.attempts
                hps = hasher.stats.hps
                best_hex = hasher.stats.best_hex
                found = hasher.stats.found

            # flash FOUND when it increments
            if found != last_found:
                last_found = found
                found_flash_until = now + 2.0

            # Status: only flash FOUND, otherwise show nothing
            status_msg = "FOUND!!!" if now < found_flash_until else ""

            # Draw UI
            img = Image.new("1", (128, 64), 0)
            d = ImageDraw.Draw(img)
            d.rectangle((0, 0, 127, 63), outline=1, fill=0)

            # --- Night stars (background) ---
            if night:
                for s in stars:
                    d.point((int(s["x"]), int(s["y"])), fill=1)
                    s["y"] += s["spd"]
                    if s["y"] > 63:
                        s["y"] = 0
                        s["x"] = random.randint(0, 127)

            # ---- Weather overlay ----
            weather_strength = 0.45 if night else 1.0

            if weather == "RAIN":
                for i, drop in enumerate(raindrops):
                    if night and (i % 2 == 1):
                        continue
                    d.point((drop["x"], drop["y"]), fill=1)
                    drop["y"] += max(1, int(drop["spd"] * weather_strength))
                    if drop["y"] > 63:
                        drop["y"] = 0
                        drop["x"] = random.randint(0, 127)

            elif weather == "SNOW":
                for i, flake in enumerate(snowflakes):
                    if night and (i % 2 == 1):
                        continue
                    d.point((flake["x"], int(flake["y"])), fill=1)
                    flake["y"] += flake["spd"] * weather_strength
                    flake["x"] = (flake["x"] + flake["sx"]) % 128
                    if flake["y"] > 63:
                        flake["y"] = 0
                        flake["x"] = random.randint(0, 127)

            elif weather == "STORM":
                flash_chance = 0.004 if night else 0.01
                if time.time() > storm_flash_until and random.random() < flash_chance:
                    storm_flash_until = time.time() + (0.10 if night else 0.15)

                if time.time() < storm_flash_until:
                    d.rectangle((0, 0, 127, 63), outline=1, fill=0)
                    x = 6
                    for y in range(0, 64, 6):
                        d.point((x, y), fill=1)
                        x += random.choice([-1, 0, 1])
                        x = max(0, min(127, x))

            # -----------------------------
            # NEW LEFT PANEL GEOMETRY
            # -----------------------------
            # Left area is 0..88 (because miner_box starts at x=90)
            left_x0, left_y0, left_x1, left_y1 = 1, 1, 88, 62

            # Big clock region (about 2/3 height)
            clock_box = (left_x0 + 1, left_y0 + 1, left_x1 - 1, 41)
            d.rectangle(clock_box, outline=1, fill=0)

            # Stats strip at bottom
            stats_box = (left_x0 + 1, 42, left_x1 - 1, left_y1 - 1)
            d.rectangle(stats_box, outline=1, fill=0)

            # Big time (HH:MM) centered
            hhmm = time.strftime("%H:%M")
            ss = time.strftime("%S")

            # center big HH:MM inside clock_box
            bb = d.textbbox((0, 0), hhmm, font=big_font)
            tw = bb[2] - bb[0]
            th = bb[3] - bb[1]
            cx = (clock_box[0] + clock_box[2] - tw) // 2
            cy = (clock_box[1] + clock_box[3] - th) // 2 - 2
            d.text((cx, cy), hhmm, fill=1, font=big_font)

            # small seconds in bottom-right corner of clock_box
            d.text((clock_box[2] - 18, clock_box[3] - 10), ss, fill=1, font=font)

            # Status text inside clock box (small, under time)
            d.text((clock_box[0] + 4, clock_box[1] + 30), status_msg, fill=1, font=font)

            draw_weather_overlay(d, clock_box, weather, now, night)

            # Compact number formatting (inline, no helper fn)
            if attempts >= 1_000_000_000:
                attempts_str = f"{attempts/1_000_000_000:.2f}B"
            elif attempts >= 1_000_000:
                attempts_str = f"{attempts/1_000_000:.2f}M"
            elif attempts >= 1_000:
                attempts_str = f"{attempts/1_000:.2f}K"
            else:
                attempts_str = str(attempts)

            if hps >= 1_000_000:
                hps_str = f"{hps/1_000_000:.2f}M"
            elif hps >= 1_000:
                hps_str = f"{hps/1_000:.2f}K"
            else:
                hps_str = f"{hps:,.0f}"

            # Rotating single-line strip (replaces multi-line stats)
            # rotates between Attempts / H/s / Best / Wins (and FOUND flash if present)
            rot_lines = [
                f"A:{attempts_str}",
                f"H:{hps_str}/s",
                f"Best:{best_hex[:8]}",
                f"W:{found}",
            ]

            # Optional: include FOUND only when it’s active (keeps fluff off screen)
            if status_msg:
                rot_lines = [status_msg] + rot_lines

            # rotate every 2.5 seconds
            rot_i = int(now // 2.5) % len(rot_lines)

            sx, sy = stats_box[0] + 3, stats_box[1] + 8
            d.text((sx, sy), rot_lines[rot_i], fill=1, font=font)

            # -----------------------------
            # RIGHT: STATUS BAR + RUSH BOX
            # -----------------------------
            status_bar = (90, 1, 126, 13)     # small box above Rush
            miner_box  = (90, 14, 126, 62)    # Rush hallway box

            d.rectangle(status_bar, outline=1, fill=0)
            d.rectangle(miner_box, outline=1, fill=0)

            # Icons / mini info in status bar
            sbx0, sby0, sbx1, sby1 = status_bar
            icon_y = sby0 + 2

            # Weather
            draw_weather_icon(d, sbx0 + 2, icon_y, weather)

            # WiFi
            draw_wifi_icon(d, sbx0 + 14, icon_y + 1, ok=wifi_ok)

            # Temperature
            draw_temp_icon(d, sbx0 + 24, icon_y + 1, level=temp_level)

            # Status (FOUND vs SEARCH)
            draw_status_icon(d, sbx0 + 33, icon_y + 1, status_msg if status_msg else "SEARCH")

            # Tiny wins count on the right side of the status bar
            d.text((sbx1 - 18, icon_y), f"W{found}", fill=1, font=font)

            # Environment + Rush
            anchors = draw_nostromo_env(d, miner_box, now, night, weather)
            plug_x, plug_y = anchors["plug"]

            # Draw wins INSIDE the console screen returned by the environment helper
            cx0, cy0, cx1, cy1 = anchors["console_box"]
            d.text((cx0 + 3, cy0 + 0), str(found), fill=1, font=font)

            #scanline
            if night:
                mx0, my0, mx1, my1 = miner_box
                for y in range(my0 + 2, my1 - 2, 4):
                    for x in range(mx0 + 2, mx1 - 2, 6):
                        d.point((x, y), fill=1)

            # Sprite
            frame = active_frames[anim_idx] if 0 <= anim_idx < len(active_frames) else active_frames[0]
            draw_sprite(d, miner_x, miner_y, frame)

            # sparks for impact
            if anim_idx in (1, 3):
                d.point((miner_x + 22, miner_y + 10), fill=1)
                d.point((miner_x + 23, miner_y + 11), fill=1)

            oled.display_image(img)
            time.sleep(0.03)
    except Exception:
        # log crash reason for systemd 
        logging.exception("Fatal error in main loop")
        raise

    finally:
        logging.info("RushUI shutting down")
        # stop background thread first
        try:
            hasher.stop()
        except Exception:
            pass

        # clear display so it doesn't freeze on last frame
        try:
            oled.clear()
        except Exception:
            pass

        # release SPI/GPIO resources
        try:
            oled.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
