#!/usr/bin/env python3
"""
🏥 Cloud Health Watchdog — monitors the Codespace Hermes gateway.
Runs every 15 min via cron. Silent on success.
"""
import urllib.request, json, sys, os
from datetime import datetime

GATEWAY_URL = "http://localhost:3000/health"
LOG = os.path.expanduser("~/.hermes/logs/cloud-health.log")
ERRORS = []
WARNINGS = []

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(f"[{ts}] {msg}\n")

def check_gateway():
    try:
        r = urllib.request.urlopen(GATEWAY_URL, timeout=10)
        data = json.loads(r.read())
        log(f"Gateway OK: {data}")
        return True
    except Exception as e:
        ERRORS.append(f"Gateway unreachable: {e}")
        return False

def check_disk():
    import shutil
    usage = shutil.disk_usage("/")
    pct = usage.used / usage.total * 100
    if pct > 90:
        ERRORS.append(f"Disk critical: {pct:.0f}% used")
    elif pct > 80:
        WARNINGS.append(f"Disk high: {pct:.0f}% used")

def check_codespace_uptime():
    """Check if Codespace is close to stopping."""
    uptime_file = "/proc/uptime"
    if os.path.exists(uptime_file):
        with open(uptime_file) as f:
            seconds = float(f.read().split()[0])
            hours = seconds / 3600
        if hours > 20:
            WARNINGS.append(f"Codespace running {hours:.0f}h — may auto-stop soon")

def main():
    check_gateway()
    check_disk()
    check_codespace_uptime()

    if ERRORS:
        msg = f"❌ CLOUD HEALTH ALERT — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        for e in ERRORS:
            msg += f"  ❌ {e}\n"
        for w in WARNINGS:
            msg += f"  ⚠️  {w}\n"
        print(msg)
        sys.exit(1)
    elif WARNINGS:
        msg = f"⚠️ Cloud Health Warnings — {datetime.now().strftime('%H:%M')}\n"
        for w in WARNINGS:
            msg += f"  ⚠️  {w}\n"
        print(msg)
        sys.exit(0)
    # Silent exit on success

if __name__ == "__main__":
    main()
