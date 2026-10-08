import os
import time
import hashlib
import threading
from dataclasses import dataclass, field

def dsha256(b: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(b).digest()).digest()

def random_header_80() -> bytearray:
    # Bitcoin block header is 80 bytes:
    # version(4) + prevhash(32) + merkle(32) + time(4) + bits(4) + nonce(4)
    # For lottery mode, we randomize the whole thing and then vary nonce quickly.
    return bytearray(os.urandom(80))

def le_u32(n: int) -> bytes:
    return int(n & 0xFFFFFFFF).to_bytes(4, "little", signed=False)

@dataclass
class HashStats:
    attempts: int = 0
    hps: float = 0.0
    best_hex: str = "ff" * 32
    last_hex: str = "00" * 32
    found: int = 0
    running: bool = True
    lock: threading.Lock = field(default_factory=threading.Lock)

class LotteryHasher:
    """
    Background Bitcoin-style hashing:
    - Generates random 80-byte headers
    - Iterates nonce values
    - Computes double-SHA256(header)
    - Compares hash to a target
    """
    def __init__(self, target_leading_zero_bits: int = 20, batch_size: int = 2000):
        self.stats = HashStats()
        self.target_bits = target_leading_zero_bits
        self.batch_size = batch_size
        self._thread = None

        # Precompute a target integer like: hash_int < 2^(256 - target_bits)
        # More target_bits => harder.
        self.target_int = 1 << (256 - self.target_bits)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self.stats.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        with self.stats.lock:
            self.stats.running = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def _run(self):
        header = random_header_80()
        nonce = 0

        # timing for hashes/sec
        last_t = time.time()
        last_attempts = 0

        best_int = int(self.stats.best_hex, 16)

        while True:
            with self.stats.lock:
                if not self.stats.running:
                    break

            # Do work in batches to reduce lock overhead
            for _ in range(self.batch_size):
                # Write nonce into last 4 bytes (little endian)
                header[76:80] = le_u32(nonce)
                nonce = (nonce + 1) & 0xFFFFFFFF

                h = dsha256(header)            # bytes, big-endian display
                h_int = int.from_bytes(h, "big")

                # Update best/last without locking every time, then lock periodically
                if h_int < best_int:
                    best_int = h_int
                    best_hex = h.hex()

                    with self.stats.lock:
                        self.stats.best_hex = best_hex

                # “win” check (toy target)
                if h_int < self.target_int:
                    with self.stats.lock:
                        self.stats.found += 1
                    # re-randomize so you don't instantly re-hit similar region
                    header = random_header_80()

                last_hex = h.hex()

                # Increment attempts in memory; lock occasionally
                # (counting locally then adding is faster)
                with self.stats.lock:
                    self.stats.attempts += 1
                    self.stats.last_hex = last_hex

            # Update H/s once per ~0.5s
            now = time.time()
            if now - last_t >= 0.5:
                with self.stats.lock:
                    a = self.stats.attempts
                delta = a - last_attempts
                hps = delta / (now - last_t)
                last_attempts = a
                last_t = now
                with self.stats.lock:
                    self.stats.hps = hps
