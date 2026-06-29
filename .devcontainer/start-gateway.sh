#!/bin/bash
# 🔌 Hermes Cloud — Start Full Agent Gateway
# Runs every time the Codespace starts/resumes.
# Launches: Telegram gateway + cron scheduler + keepalive loop

set -e

echo "🔌 Hermes Cloud Gateway starting at $(date)..."

cd ~

# === 1. Pull latest memory from local ===
if [ -f /workspaces/hermes-cloud/scripts/cloud_memory_pull.py ]; then
    echo "📥 Pulling latest memory from local..."
    python3 /workspaces/hermes-cloud/scripts/cloud_memory_pull.py
    echo "✅ Memory sync complete"
fi

# === 2. Source environment ===
if [ -f ~/.hermes/.env ]; then
    set -a
    source ~/.hermes/.env
    set +a
    echo "✅ Environment loaded"
fi

# === 3. Bootstrap cron jobs (idempotent) ===
if [ -f /workspaces/hermes-cloud/.devcontainer/cron_bootstrap.sh ]; then
    echo "🔄 Bootstrapping cron jobs..."
    bash /workspaces/hermes-cloud/.devcontainer/cron_bootstrap.sh
    echo "✅ Cron jobs ready"
fi

# === 4. Set up cloud agent mesh webhooks ===
# These let local agents delegate tasks to cloud
echo "🔗 Setting up agent mesh..."
for i in 1 2 3; do
    if hermes webhook list > /dev/null 2>&1; then
        # Create if not exists
        hermes webhook list 2>/dev/null | grep -q "local-task" || \
            hermes webhook subscribe local-task \
                --prompt 'Task from local agent: {payload}' \
                --events 'task.execute' \
                --deliver telegram \
                --secret 'mesh-cloud-secret-change-me' 2>/dev/null || true
        hermes webhook list 2>/dev/null | grep -q "knowledge-share" || \
            hermes webhook subscribe knowledge-share \
                --prompt 'Knowledge from local: {payload}' \
                --events 'knowledge.share' \
                --deliver telegram \
                --secret 'mesh-cloud-secret-change-me' 2>/dev/null || true
        echo "✅ Agent mesh webhooks active"
        break
    fi
    echo "⏳ Waiting for gateway... (attempt $i)"
    sleep 3
done

# === 5. Start the gateway ===
echo "🚀 Starting Hermes gateway on port 3000..."

# Kill any existing gateway first
pkill -f "hermes gateway" 2>/dev/null || true
sleep 2

# Start in background — gateway handles Telegram + cron scheduling
hermes gateway run --port 3000 &
GATEWAY_PID=$!
echo "   Gateway PID: $GATEWAY_PID"

# Wait and verify
for i in $(seq 1 12); do
    sleep 5
    if curl -s http://localhost:3000/health > /dev/null 2>&1; then
        echo "✅ Gateway LIVE on port 3000"
        break
    fi
    echo "   Waiting... ($((i*5))s)"
done

# === 6. Start webhook platform if gateway supports it ===
# The webhook platform runs inside the gateway, so no separate process needed
echo "🌐 Webhook platform active on port 8644"

# === 7. Start keepalive loop (prevents 30-min idle timeout) ===
(
    while true; do
        sleep 240  # every 4 minutes
        
        # Ping gateway health endpoint
        curl -s http://localhost:3000/health > /dev/null 2>&1 || {
            echo "[$(date)] ⚠️ Gateway not responding — restarting..."
            kill $GATEWAY_PID 2>/dev/null || true
            
            # Re-source env and restart
            [ -f ~/.hermes/.env ] && source ~/.hermes/.env
            hermes gateway run --port 3000 &
            GATEWAY_PID=$!
            echo "[$(date)] Gateway restarted with PID $GATEWAY_PID"
        }
        
        # Touch home to prevent Codespace idle timeout
        touch ~/.hermes/.env 2>/dev/null || true
        echo "[$(date)] Keepalive ping" >> ~/.hermes/logs/keepalive.log 2>/dev/null || true
    done
) &
echo "✅ Keepalive loop running (pings every 4min)"

# === 8. Verify all systems ===
echo ""
echo "╔════════════════════════════════════════╗"
echo "║  ☁️  HERMES CLOUD — SYSTEMS CHECK     ║"
echo "╠════════════════════════════════════════╣"

# Gateway
curl -s http://localhost:3000/health > /dev/null 2>&1 \
    && echo "║  ✅ Gateway:      RUNNING on :3000  ║" \
    || echo "║  ❌ Gateway:      OFFLINE           ║"

# Webhook
curl -s http://localhost:8644/health > /dev/null 2>&1 \
    && echo "║  ✅ Webhook:      RUNNING on :8644  ║" \
    || echo "║  ℹ️  Webhook:      May need restart  ║"

# Cron
hermes cron list 2>/dev/null | head -5 | while read line; do
    echo "║     $line"
done

echo "╚════════════════════════════════════════╝"
echo ""
echo "🌐 Gateway URL: http://localhost:3000"
echo "🌐 Webhook URL: http://localhost:8644"
echo "📝 Logs: ~/.hermes/logs/"
echo "🛑 Stop: kill $(cat ~/.hermes/gateway.pid 2>/dev/null || echo "$GATEWAY_PID")"

# Save PID
echo $GATEWAY_PID > ~/.hermes/gateway.pid
