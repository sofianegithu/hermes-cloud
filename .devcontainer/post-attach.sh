#!/bin/bash
# 📋 Post-attach script — shows status when you open the Codespace
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║     🤖  Hermes Cloud Gateway  🌐           ║"
echo "╠══════════════════════════════════════════════╣"
echo "║  Status: Checking...                        ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Check gateway
if curl -s http://localhost:3000/health > /dev/null 2>&1; then
    echo "✅ Gateway: RUNNING on port 3000"
else
    echo "❌ Gateway: OFFLINE — run: bash .devcontainer/start-gateway.sh"
fi

# Check health server
if curl -s http://localhost:8080/ > /dev/null 2>&1; then
    echo "✅ Health: RUNNING on port 8080"
else
    echo "❌ Health: OFFLINE"
fi

echo ""
echo "📋 Quick commands:"
echo "   .devcontainer/start-gateway.sh    — Start the gateway"
echo "   cat ~/.hermes/logs/gateway.log    — View gateway logs"
echo "   hermes gateway status             — Check gateway status"
echo ""
