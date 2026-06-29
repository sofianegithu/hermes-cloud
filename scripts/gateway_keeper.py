#!/usr/bin/env python3
"""
🔌 GATEWAY KEEPER — monitors Hermes gateway and reconnects if it drops.
Runs every 3 minutes via cron (no_agent=true, zero token cost).
Only delivers output if the gateway was down and needed fixing.
"""
import subprocess, sys, time
from pathlib import Path
from datetime import datetime

HOME = Path.home()
LOG = HOME / "AppData/Local/hermes/gateway_keeper.log"
CHECK_INTERVAL = 10  # seconds to wait after reconnect before verifying

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG, "a") as f:
        f.write(f"[{ts}] {msg}\n")
    # Also print so cron collects it
    print(f"[{ts}] {msg}")

def run_hermes(args, timeout=30):
    try:
        r = subprocess.run(
            ["hermes"] + args,
            capture_output=True, text=True, timeout=timeout
        )
        return r.returncode == 0, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return False, "", "timeout"
    except FileNotFoundError:
        return False, "", "hermes CLI not found"
    except Exception as e:
        return False, "", str(e)

def check():
    """Returns (is_running: bool, detail: str)"""
    ok, out, err = run_hermes(["gateway", "status"], timeout=15)
    combined = (out + err).lower()
    if ok and "running" in combined:
        return True, "process running"
    # Try port check as backup
    try:
        import urllib.request
        urllib.request.urlopen("http://localhost:3000/health", timeout=5)
        return True, "port 3000 responds"
    except Exception:
        pass
    return False, combined[:200] if combined else "unknown"

def restart():
    """Try to restart the gateway. Returns True if confirmed running."""
    log("Gateway DOWN — attempting restart...")
    
    # Try restart command
    ok, out, err = run_hermes(["gateway", "restart"], timeout=45)
    if ok:
        time.sleep(CHECK_INTERVAL)
        running, detail = check()
        if running:
            log(f"Restart SUCCESS ({detail})")
            return True
        log(f"Restart ran but still down: {detail}")
    else:
        log(f"Restart command failed: {(out+err)[:200]}")
    
    # Fallback: stop then start
    log("Trying stop/start...")
    run_hermes(["gateway", "stop"], timeout=30)
    time.sleep(5)
    ok2, out2, err2 = run_hermes(["gateway", "start"], timeout=45)
    if ok2:
        time.sleep(CHECK_INTERVAL)
        running2, detail2 = check()
        if running2:
            log(f"Stop/start SUCCESS ({detail2})")
            return True
        log(f"Stop/start ran but still down: {detail2}")
    else:
        log(f"Start command failed: {(out2+err2)[:200]}")
    
    # Last resort: try hermes service restart
    log("Trying hermes restart...")
    run_hermes(["restart"], timeout=60)
    time.sleep(CHECK_INTERVAL)
    running3, detail3 = check()
    if running3:
        log(f"Full restart SUCCESS ({detail3})")
        return True
    
    return False

def main():
    running, detail = check()
    
    if running:
        # Silent exit — all good
        return
    
    log(f"Gateway NOT running — detail: {detail}")
    
    reconnected = restart()
    
    if reconnected:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"✅ Gateway was DOWN — reconnected successfully at {ts}")
    else:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"❌ CRITICAL: Gateway DOWN and ALL reconnect attempts failed at {ts}")
        print(f"   Last status: {detail}")
        print(f"   Check: hermes gateway status")
        print(f"   Logs: {LOG}")

if __name__ == "__main__":
    main()
    sys.exit(0)
