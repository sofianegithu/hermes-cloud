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
║    TELEGRAM_BOT_TOKEN=your_token_here        ║
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

# Save PID for later
echo $GATEWAY_PID > ~/.hermes/gateway.pid
echo ""
echo "🌐 Gateway URL: http://localhost:3000"
echo "📝 Logs: ~/.hermes/logs/"
echo "🛑 To stop: kill \$(cat ~/.hermes/gateway.pid)"
