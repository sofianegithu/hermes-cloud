#!/bin/bash
# 🖥️ Hermes Cloud — Post-Attach Status Display
# Shows system status when you connect to the Codespace via VS Code.

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  ☁️  HERMES CLOUD — Full Agent Gateway          ║"
echo "╠══════════════════════════════════════════════════╣"

# Gateway status
if curl -s http://localhost:3000/health > /dev/null 2>&1; then
    UPTIME=$(curl -s http://localhost:3000/health 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"{d.get('uptime',0):.0f}s\")" 2>/dev/null || echo "?")
    echo "║  ✅ Telegram Gateway: RUNNING (uptime: $UPTIME) ║"
else
    echo "║  ❌ Telegram Gateway: OFFLINE                   ║"
fi

# Webhook status
if curl -s http://localhost:8644/health > /dev/null 2>&1; then
    echo "║  ✅ Agent Mesh Webhook: RUNNING                  ║"
else
    echo "║  ℹ️  Agent Mesh Webhook: Not enabled              ║"
fi

# Cron status
CRON_COUNT=$(hermes cron list 2>/dev/null | grep -cE 'scheduled|ok' || echo "0")
echo "║  📋 Cron Jobs: $CRON_COUNT active                        ║"

# Memory sync
if [ -f ~/.hermes/logs/memory-sync.log ]; then
    LAST_SYNC=$(tail -1 ~/.hermes/logs/memory-sync.log 2>/dev/null | cut -d']' -f2- | head -c 60)
    echo "║  🔄 Last memory sync:${LAST_SYNC:- unknown}  ║"
fi

echo "╠══════════════════════════════════════════════════╣"
echo "║  Commands:                                       ║"
echo "║    View logs:  tail -f ~/.hermes/logs/*.log      ║"
echo "║    Cron jobs:  hermes cron list                  ║"
echo "║    Restart:    bash .devcontainer/start-gateway.sh║"
echo "╚══════════════════════════════════════════════════╝"
