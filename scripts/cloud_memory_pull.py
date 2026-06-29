#!/usr/bin/env python3
"""
☁️ CLOUD MEMORY PULL — pulls memory from the shared git branch.
Runs on cloud Hermes startup and periodically.
No token cost (pull only, pushes only in emergencies).
"""

import sys, subprocess, shutil, json
from pathlib import Path
from datetime import datetime

REPO_DIR = Path.home() / "hermes-cloud"
SYNC_DIR = REPO_DIR / "memory-sync"
BRANCH = "memory-sync"
MEMORIES_DIR = Path.home() / ".hermes" / "memories"
CONFIG_DIR = Path.home() / ".hermes"
LOG_FILE = Path.home() / ".hermes" / "logs" / "memory-sync.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def git(args, timeout=30):
    try:
        r = subprocess.run(["git"] + args, capture_output=True, text=True, timeout=timeout, cwd=REPO_DIR)
        return r.returncode == 0, r.stdout.strip()[:300]
    except Exception as e:
        return False, str(e)

def main():
    log("☁️ Cloud memory pull starting...")
    
    if not REPO_DIR.exists():
        log(f"❌ Repo not found at {REPO_DIR}")
        sys.exit(1)
    
    # Fetch the shared branch
    ok, out = git(["fetch", "origin", BRANCH], timeout=15)
    if not ok:
        log(f"⚠️ Could not fetch {BRANCH} (first time?): {out[:100]}")
        sys.exit(0)
    
    # Check if we're behind
    ok, out = git(["rev-list", "--count", f"HEAD..origin/{BRANCH}"], timeout=10)
    behind = int(out) if ok and out.strip().isdigit() else 0
    
    if behind == 0:
        log("ℹ️ Already up to date with local memory")
    else:
        log(f"📥 {behind} new commit(s) from local — pulling...")
        
        # Save current branch
        ok, current_branch = git(["rev-parse", "--abbrev-ref", "HEAD"])
        
        # Checkout sync branch
        git(["checkout", BRANCH], timeout=5)
        ok, out = git(["pull", "origin", BRANCH], timeout=30)
        
        if ok:
            log("✅ Pulled latest memory from local")
            
            # Apply memory files to cloud Hermes
            MEMORIES_DIR.mkdir(parents=True, exist_ok=True)
            if SYNC_DIR.exists():
                for f in SYNC_DIR.iterdir():
                    if f.suffix in (".md", ".txt", ".yaml", ".json") and f.name != "meta.json":
                        dest = MEMORIES_DIR / f.name
                        shutil.copy2(f, dest)
                        log(f"  📄 Synced: {f.name}")
                
                # Also sync config (non-destructive)
                config_sync = SYNC_DIR / "config.yaml"
                if config_sync.exists():
                    dest = CONFIG_DIR / "config.yaml"
                    if not dest.exists():
                        shutil.copy2(config_sync, dest)
                        log("  📄 Wrote initial config.yaml")
        else:
            log(f"❌ Pull failed: {out[:100]}")
        
        # Go back to original branch
        if current_branch:
            git(["checkout", current_branch], timeout=5)
    
    log("☁️ Cloud memory pull complete")

if __name__ == "__main__":
    main()
