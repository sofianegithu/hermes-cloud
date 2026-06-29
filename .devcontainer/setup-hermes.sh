#!/bin/bash
# 🚀 Hermes Cloud Setup — runs once when the Codespace is created
set -e

echo "🔧 Installing Hermes Agent in cloud environment..."
cd ~

# Install hermes via pip
pip install --upgrade pip --quiet
pip install hermes-agent --quiet 2>/dev/null || {
    echo "⚠️ pip install failed, trying from source..."
    git clone --depth 1 https://github.com/nousresearch/hermes-agent.git /tmp/hermes-build 2>/dev/null || true
    if [ -f /tmp/hermes-build/pyproject.toml ]; then
        cd /tmp/hermes-build && pip install -e . --quiet && cd ~
    else
        echo "❌ Could not install hermes-agent. Manual install needed."
        exit 1
    fi
}

echo "✅ Hermes Agent installed ($(hermes --version 2>/dev/null || echo 'ok'))"

# Set up config directory
mkdir -p ~/.hermes/cron ~/.hermes/logs ~/.hermes/scripts

# Copy scripts from repo if available
if [ -d /workspaces/hermes-cloud/scripts ]; then
    cp /workspaces/hermes-cloud/scripts/*.py ~/.hermes/scripts/ 2>/dev/null || true
    chmod +x ~/.hermes/scripts/*.py 2>/dev/null || true
    echo "✅ Scripts installed"
fi

# Write .env template (user must set TELEGRAM_BOT_TOKEN)
if ! grep -q "TELEGRAM_BOT_TOKEN=" ~/.hermes/.env 2>/dev/null || grep -q "__SET_ME__" ~/.hermes/.env 2>/dev/null; then
    cat > ~/.hermes/.env << 'ENVEOF'
TELEGRAM_BOT_TOKEN=__SET_ME__
TELEGRAM_HOME_CHANNEL=5615834073
TELEGRAM_ALLOWED_USERS=5615834073
GATEWAY_ALLOW_ALL_USERS=true
ENVEOF
    echo "⚠️  Set your TELEGRAM_BOT_TOKEN in ~/.hermes/.env before starting the gateway"
fi

# Write config.yaml
cat > ~/.hermes/config.yaml << 'CEOF'
gateway:
  enabled: true
  providers:
    - telegram
  port: 3000
  allow_all_users: true
CEOF
echo "✅ Config written"

# Set up cron for health check
(crontab -l 2>/dev/null; echo "*/30 * * * * cd ~ && python3 ~/.hermes/scripts/cloud_health.py 2>/dev/null || true") | crontab -
echo "✅ Cron health check installed"

# Write setup marker
echo "✅ Hermes Cloud setup complete at $(date)" > ~/.hermes/cloud-setup-done
echo ""
echo "╔════════════════════════════════════╗"
echo "║  🚀  HERMES CLOUD READY          ║"
echo "╠════════════════════════════════════╣"
echo "║  Run: bash .devcontainer/start-   ║"
echo "║       gateway.sh                  ║"
echo "║  To start the gateway             ║"
echo "╚════════════════════════════════════╝"
