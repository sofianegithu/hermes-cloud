#!/bin/bash
# 🔌 Start Hermes Gateway — runs every time the Codespace starts/resumes
set -e

echo "🔌 Hermes Cloud Gateway starting at $(date)..."

# Source the config if it exists
if [ -f ~/.hermes/config.yaml ]; then
    echo "✅ Config found"
fi

# Try to start the gateway
hermes gateway start 2>/dev/null || {
    echo "⚠️ 'hermes gateway start' not available, trying npx gateway..."
    npx --yes @hermes-agent/gateway start --port 3000 2>/dev/null || {
        echo "⚠️ Starting simple health server as fallback..."
        # Fallback: simple health endpoint to keep Codespace alive
        python3 -m http.server 8080 --bind 0.0.0.0 &
        echo "✅ Health server running on port 8080"
    }
}

# Verify gateway is running
sleep 3
if curl -s http://localhost:3000/health > /dev/null 2>&1; then
    echo "✅ Gateway is LIVE on port 3000"
else
    echo "⚠️ Gateway may not be running — check logs at ~/.hermes/logs/"
fi

# Start a keepalive loop in background that pings every 5 min
(
    while true; do
        sleep 300
        curl -s http://localhost:3000/health > /dev/null 2>&1 || {
            echo "[$(date)] Gateway ping failed — attempting restart..."
            hermes gateway restart 2>/dev/null || true
        }
        # Ping Codespace to prevent idle timeout
        curl -s -o /dev/null http://localhost:8080/ 2>/dev/null || true
    done
) &

echo "✅ Keepalive loop started (ping every 5min)"
echo "🌐 Gateway URL: http://localhost:3000"
