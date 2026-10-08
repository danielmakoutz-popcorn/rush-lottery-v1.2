#!/usr/bin/env python3
import os
import time
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

AP_SSID = "RUSH-MINER-SETUP"
AP_PASS = ""  # leave empty for open AP (simplest). If you want a password, set it and adjust hostapd.conf.
AP_IP = "192.168.4.1"
AP_NET = "192.168.4.0/24"
DHCP_START = "192.168.4.50"
DHCP_END = "192.168.4.150"
AP_WINDOW_SECONDS = 120
CONNECT_WAIT_SECONDS = 20
PROVISION_FLAG = "/var/lib/rush-wifi/provisioned"

HOSTAPD_CONF = "/home/daniel/oled/wifi_provision/hostapd.conf"
DNSMASQ_CONF = "/home/daniel/oled/wifi_provision/dnsmasq.conf"
WPA_SUPPLICANT = "/etc/wpa_supplicant/wpa_supplicant.conf"

def sh(cmd: str, check=True):
    return subprocess.run(cmd, shell=True, check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def is_wifi_connected() -> bool:
    # "connected" means wlan0 has an IP and a default route exists
    try:
        ip = sh("ip -4 addr show wlan0 | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){3}'", check=False).stdout.strip()
        if not ip:
            return False
        route = sh("ip route | grep -q '^default '", check=False)
        return route.returncode == 0
    except Exception:
        return False

def wait_for_normal_wifi(seconds: int) -> bool:
    for _ in range(seconds):
        if is_wifi_connected():
            return True
        time.sleep(1)
    return False

def write_hostapd_conf():
    # Open AP by default (simplest). If you later want WPA2 AP, we can add it.
    conf = f"""interface=wlan0
driver=nl80211
ssid={AP_SSID}
hw_mode=g
channel=6
wmm_enabled=0
auth_algs=1
ignore_broadcast_ssid=0
"""
    with open(HOSTAPD_CONF, "w") as f:
        f.write(conf)

def write_dnsmasq_conf():
    conf = f"""interface=wlan0
bind-interfaces
dhcp-range={DHCP_START},{DHCP_END},255.255.255.0,12h
domain-needed
bogus-priv
"""
    with open(DNSMASQ_CONF, "w") as f:
        f.write(conf)

def start_ap_services():
    # Make sure wlan0 is free
    sh("sudo rfkill unblock wifi", check=False)
    sh("sudo ip link set wlan0 down", check=False)

    # Assign static IP for AP mode
    sh(f"sudo ip addr flush dev wlan0", check=False)
    sh("sudo ip link set wlan0 up", check=False)
    sh(f"sudo ip addr add {AP_IP}/24 dev wlan0", check=False)

    write_hostapd_conf()
    write_dnsmasq_conf()

    # Start dnsmasq with our custom config
    sh(f"sudo dnsmasq -C {DNSMASQ_CONF} -x /run/dnsmasq_wifiprov.pid", check=True)

    # Start hostapd with our custom config
    sh(f"sudo hostapd {HOSTAPD_CONF} -B -P /run/hostapd_wifiprov.pid", check=True)

def stop_ap_services():
    sh("sudo kill $(cat /run/hostapd_wifiprov.pid) 2>/dev/null", check=False)
    sh("sudo kill $(cat /run/dnsmasq_wifiprov.pid) 2>/dev/null", check=False)
    sh("sudo ip addr flush dev wlan0", check=False)
    sh("sudo ip link set wlan0 down", check=False)
    sh("sudo ip link set wlan0 up", check=False)

def set_timezone(tz: str):
    # tz like "America/Los_Angeles"
    if tz and "/" in tz and len(tz) < 64:
        sh(f"sudo timedatectl set-timezone '{tz}'", check=False)

def save_wifi(ssid: str, psk: str):
    if not ssid:
        raise ValueError("SSID missing")

    # Use NetworkManager (correct for Bookworm)
    nm_active = (
        subprocess.run(
            "systemctl is-active NetworkManager",
            shell=True,
            stdout=subprocess.PIPE,
            text=True
        ).stdout.strip() == "active"
    )

    if not nm_active:
        raise RuntimeError("NetworkManager is not active")

    # Remove any existing connection with same SSID (avoid duplicates)
    subprocess.run(
        f"nmcli -t -f NAME,TYPE con show | "
        f"awk -F: '$2==\"wifi\" && $1==\"{ssid}\" {{print $1}}' | "
        f"xargs -r -I{{}} nmcli con delete \"{{}}\"",
        shell=True
    )

    # Create + save connection
    if psk:
        subprocess.check_call(
            f"nmcli dev wifi connect '{ssid}' password '{psk}'",
            shell=True
        )
    else:
        subprocess.check_call(
            f"nmcli dev wifi connect '{ssid}'",
            shell=True
        )

    # Ensure it reconnects forever
    subprocess.run(
        f"nmcli con modify '{ssid}' connection.autoconnect yes",
        shell=True
    )

def wait_for_nm_connection(timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            out = subprocess.check_output(
                "nmcli -t -f DEVICE,STATE dev",
                shell=True,
                text=True
            )
            for line in out.splitlines():
                if line.startswith("wlan0:connected"):
                    return True
        except Exception:
            pass
        time.sleep(2)
    return False

class SetupHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        page = f"""<!doctype html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>RUSH Wi-Fi Setup</title>
<style>
body{{font-family:system-ui, sans-serif; margin:24px; max-width:520px}}
label{{display:block; margin-top:12px}}
input,select,button{{width:100%; padding:10px; font-size:16px; margin-top:6px}}
small{{color:#555}}
</style></head>
<body>
<h2>RUSH Wi-Fi Setup</h2>
<p><small>Enter your Wi-Fi name (SSID), password, and timezone. Then Save. Device will reboot.</small></p>
<form method="POST">
<label>Wi-Fi Name (SSID)
<input name="ssid" placeholder="YourWiFiName" required></label>
<label>Wi-Fi Password
<input name="psk" type="password" placeholder="Password"></label>
<label>Timezone
<select name="tz">
  <option value="America/Los_Angeles">Pacific (America/Los_Angeles)</option>
  <option value="America/Denver">Mountain (America/Denver)</option>
  <option value="America/Chicago">Central (America/Chicago)</option>
  <option value="America/New_York">Eastern (America/New_York)</option>
</select></label>
<button type="submit">Save & Reboot</button>
</form>
</body></html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        data = self.rfile.read(length).decode("utf-8", errors="ignore")
        form = parse_qs(data)

        ssid = (form.get("ssid", [""])[0] or "").strip()
        psk  = (form.get("psk", [""])[0] or "").strip()
        tz   = (form.get("tz", ["America/Los_Angeles"])[0] or "America/Los_Angeles").strip()

        try:
            save_wifi(ssid, psk)
            set_timezone(tz)

            if not wait_for_nm_connection(60):
                raise RuntimeError("Wi-Fi failed to connect. Check password or signal.")

            os.makedirs("/var/lib/rush-wifi", exist_ok=True)
            with open("/var/lib/rush-wifi/provisioned", "w") as f:
                f.write("ok")

            msg = "<h3>Saved.</h3><p>Rebooting now…</p>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(msg.encode("utf-8"))

            # reboot after response returns
            subprocess.Popen("sudo reboot", shell=True)
        except Exception as e:
            msg = f"<h3>Error</h3><pre>{e}</pre><p><a href='/'>Back</a></p>"
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(msg.encode("utf-8"))

def run_setup_server(window_seconds: int):
    httpd = HTTPServer((AP_IP, 80), SetupHandler)
    httpd.timeout = 1
    end = time.time() + window_seconds
    while time.time() < end:
        httpd.handle_request()
    httpd.server_close()

def main():

    if os.path.exists(PROVISION_FLAG):
        return

    # If Wi-Fi comes up normally quickly, do nothing.
    if wait_for_normal_wifi(CONNECT_WAIT_SECONDS):
        return

    # Otherwise start AP + setup page for a short window.
    start_ap_services()
    try:
        run_setup_server(AP_WINDOW_SECONDS)
    finally:
        stop_ap_services()
        # After window ends, device continues running offline if not configured.

if __name__ == "__main__":
    main()
