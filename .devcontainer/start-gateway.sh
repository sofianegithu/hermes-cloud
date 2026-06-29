#!/bin/bash
# 🔌 Hermes Cloud Gateway Starter — runs every time Codespace starts/resumes
set -e

echo "🔌 Hermes Cloud Gateway starting at $(date)..."

cd ~

# Pull latest memory from local
if [ -f /workspaces/hermes-cloud/scripts/cloud_memory_pull.py ]; then
    echo "📥 Pulling latest memory from local..."
    python3 /workspaces/hermes-cloud/scripts/cloud_memory_pull.py
    echo "✅ Memory sync complete"
fi

# Source the .env if it exists
if [ -f ~/.hermes/.env ]; then
    set -a
    source ~/.hermes/.env
    set +a
    echo "✅ Environment loaded"
fi

# Check if token is configured
if grep -q "__SET_ME__\|^TELEGRAM_BOT_TOKEN=*** ~/.hermes/.env 2>/dev/null; then
    echo "
╔══════════════════════════════════════════════╗
║  ❌ TELEGRAM BOT TOKEN NOT CONFIGURED       ║
╠══════════════════════════════════════════════╣
║  Edit ~/.hermes/.env and set:               ║
║    TELEGRAM_BOT_TOKEN=***        ║
║                                              ║
║  Then re-run: bash .devcontainer/start-     ║
║                        gateway.sh            ║
╚══════════════════════════════════════════════╝
"
    exit 1
fi

echo "✅ Telegram token found"

# Try to start the gateway
echo "🚀 Starting Hermes gateway..."
hermes gateway run --port 3000 &
GATEWAY_PID=$!
echo "   PID: $GATEWAY_PID"

# Wait and verify
sleep 5
if curl -s http://localhost:3000/health > /dev/null 2>&1; then
    echo "✅ Gateway is LIVE on port 3000"
else
    echo "⚠️ Gateway not responding yet — may still be starting..."
fi

# Start keepalive loop (prevents 30-min idle timeout)
(
    while true; do
        sleep 240  # every 4 min
        # Ping gateway to keep it alive
        curl -s http://localhost:3000/health > /dev/null 2>&1 || {
            # If gateway died, restart it
            echo "[$(date)] Gateway not responding — restarting..."
            kill $GATEWAY_PID 2>/dev/null || true
            hermes gateway run --port 3000 &
            GATEWAY_PID=$!
            sleep 5
        }
        # Touch home dir to prevent idle timeout
        touch ~/.hermes/.env 2>/dev/null || true
        echo "[$(date)] Keepalive ping" >> ~/.hermes/logs/keepalive.log 2>/dev/null || true
    done
) &
echo "✅ Keepalive loop started (pings every 4min)"

# === ☁️ DAILY INNOVATION RESEARCH CRON ===
echo "📡 Setting up daily agent innovation research cron (8AM UTC)..."
mkdir -p ~/.hermes/logs
mkdir -p ~/.hermes/scripts

# Copy research script from repo if available
if [ -f /workspaces/hermes-cloud/scripts/cloud_research_cron.py ]; then
    cp /workspaces/hermes-cloud/scripts/cloud_research_cron.py ~/.hermes/scripts/cloud_research_cron.py
    chmod +x ~/.hermes/scripts/cloud_research_cron.py
    echo "✅ Research script installed from repo"
fi

# Install daily cron (8 AM UTC every day)
# The script outputs to a file; we send it via the gateway API
(crontab -l 2>/dev/null | grep -v "cloud_research_cron"; echo "0 8 * * * cd ~/.hermes/scripts && python3 cloud_research_cron.py 2>&1 | tee -a ~/.hermes/logs/research_cron.log; if [ -f ~/.hermes/cron/research_output.json ]; then curl -s -X POST http://localhost:3000/api/send -H 'Content-Type: application/json' -d \"{\\\"chat_id\\\":\\\"5615834073\\\",\\\"text\\\":\\\"☁️ **Cloud Research Daily**\n\n\\\$(python3 -c \\\"import json; d=json.load(open('/home/codespace/.hermes/cron/research_output.json')); print(d.get('summary','')[:3000])\\\" 2>/dev/null || echo 'No findings')\\\"}\" 2>&1 || true; fi") | crontab -

echo "✅ Daily research cron installed (runs at 8:00 AM UTC, delivers via Telegram)"

# Save PID for later
echo $GATEWAY_PID > ~/.hermes/gateway.pid
echo ""
echo "🌐 Gateway URL: http://localhost:3000"
echo "📝 Logs: ~/.hermes/logs/"
echo "📡 Research cron: 8 AM daily → Telegram"
echo "🛑 To stop: kill \$(cat ~/.hermes/gateway.pid)"
