<<<<<<< HEAD
# hermes-cloud
Hermes Agent cloud gateway — 24/7 via GitHub Codespaces
=======
# 🤖 Hermes Cloud — GitHub Codespaces 24/7 Gateway

Your Hermes agent that stays alive even when your laptop is off.

## How It Works

1. **Codespace runs in the cloud** (free, 60h/month)
2. **Telegram bridge stays alive** — bot responds even if your laptop sleeps
3. **Keepalive loop** pings every 5 minutes to prevent auto-sleep
4. **Health watchdog** monitors everything silently

## Quick Start

### 1. Create the Repo

Go to [github.com/new](https://github.com/new) and create a repo called `hermes-cloud`.

### 2. Push This Code

```bash
cd ~/hermes-cloud
git init
git add .
git commit -m "Initial commit: Hermes Cloud gateway"
git remote add origin https://github.com/YOUR_USERNAME/hermes-cloud.git
git push -u origin main
```

### 3. Launch the Codespace

- Go to `https://github.com/YOUR_USERNAME/hermes-cloud`
- Click the green **"<> Code"** button
- Select **"Codespaces"** tab
- Click **"Create codespace on main"**

### 4. Configure Your Telegram Token

Once the Codespace is running, open the terminal and:

```bash
echo 'TELEGRAM_BOT_TOKEN=your_token_here' > ~/.hermes/.env
bash .devcontainer/start-gateway.sh
```

## What Runs Here

| Service | Port | Purpose |
|---------|------|---------|
| Hermes Gateway | 3000 | Main Telegram bridge |
| Health Server | 8080 | Keepalive + health check |
| Keepalive Loop | — | Pings every 5min to prevent idle timeout |

## Prevent Idle Timeout

Codespaces auto-stop after 30 min idle on free accounts. This setup:
- Runs a keepalive loop internally
- Touches files periodically
- Pings local services

**For true 24/7**, upgrade to GitHub Pro ($4/month) for 180h or use a GitHub Enterprise/Education account.

## Architecture

```
Telegram ←→ Codespace (cloud) ←→ Your Local Hermes
                  ↓
          If local offline:
          Buffers messages
          Responds with "Sofiane is offline"
```

## Files

```
.devcontainer/
├── devcontainer.json    — Codespace config
├── setup-hermes.sh      — One-time setup
├── start-gateway.sh     — Start the gateway
└── post-attach.sh       — Status on connect
```
>>>>>>> c1a9894 (Initial commit: Hermes Cloud gateway with devcontainer)
