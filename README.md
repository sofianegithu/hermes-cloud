# ☁️ Hermes Cloud — Full Agent Gateway

**Your 24/7 Hermes agent in the cloud.**  
Stays alive when your laptop sleeps. Runs cron. Replies on Telegram. Delegates work to local.

## The New Architecture — Agent Mesh

```
TELEGRAM ──┐
           ├── ☁️ CLOUD HERMES (Codespace)
           │     • Full Hermes agent (not just a relay)
           │     • Telegram bot responds 24/7
           │     • All cron jobs run here too
           │     • Webhook API for agent ↔ agent comms
           │
WHATSAPP ──┤
           └── 🖥️ LOCAL HERMES (Laptop)
                 • Full tool access (terminal, files, browser, computer-use)
                 • Webhook API receives cloud delegations
                 • Agent mesh protocol for structured tasks
```

## What Changed

| Before (old) | After (new) |
|-------------|-------------|
| Cloud = dumb relay | Cloud = full Hermes agent with config |
| No cron on cloud | All 11 cron jobs run on cloud too |
| No webhook on local | Local has webhook API for cloud delegations |
| One-way memory sync | Bidirectional knowledge sharing |
| No agent protocol | Structured JSON task format for agent↔agent |

## Quick Start

### 1. Set GitHub Codespaces Secrets

Go to your repo → Settings → Secrets and variables → Codespaces, add:

| Secret | Value |
|--------|-------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token |
| `GH_TOKEN_FOR_API` | GitHub token for API access |
| `MESH_WEBHOOK_SECRET` | Secret for agent↔agent webhooks |

### 2. Create the Codespace

```
https://github.com/YOUR_USERNAME/hermes-cloud → Code → Codespaces → Create
```

### 3. Verify

```bash
# Check gateway
curl http://localhost:3000/health

# Check cron
hermes cron list

# Check agent mesh
python3 scripts/agent_mesh.py status
```

## Services

| Service | Port | Purpose |
|---------|------|---------|
| Telegram Gateway | 3000 | Bot responds 24/7 |
| Agent Mesh Webhook | 8644 | Cloud ↔ Local communication |
| Keepalive Loop | — | Prevents 30-min idle timeout |
| Cron Scheduler | — | All jobs run on cloud |

## Cron Jobs (Cloud)

| Time | Name | Description |
|------|------|-------------|
| 6AM daily | 🚀 Morning Power-Up | Daily briefing & motivation |
| Every 15min | 🔄 Memory Sync | Sync knowledge with local |
| 10AM daily | 💡 Content Generator | Social media content ideas |
| 12PM daily | 🔍 Free API Hunter | Find new free AI APIs |
| 9PM daily | 🌙 Evening Wind-Down | Evening reflection & coaching |
| Every 4h | 🏥 System Health | Health monitoring |
| 2AM daily | 🔬 Deep Audit | Full system audit |
| 2AM Sat | ⚡ Auto-Improvement | Self-improvement tasks |
| 10AM Sun | 📊 Weekly Review | Weekly strategic review |

## Agent Mesh Protocol

See [docs/agent-mesh-protocol.md](docs/agent-mesh-protocol.md) for the full protocol spec.

Quick usage:

```bash
# Check agent status
python3 scripts/agent_mesh.py status

# Cloud → Local (send a task)
curl -X POST http://localhost:8644/webhooks/execute-task \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: mesh-webhook-secret" \
  -d '{"task_type":"execute","payload":{"command":"ls -la"}}'

# Local → Cloud (via Telegram)
python3 scripts/agent_mesh.py to-cloud '{"task_type":"knowledge_share","payload":{...}}'
```

## Files

```
hermes-cloud/
├── .devcontainer/
│   ├── devcontainer.json     — Codespace config (auto-setup + auto-start)
│   ├── setup-hermes.sh       — One-time install of Hermes + config
│   ├── start-gateway.sh      — Start gateway + cron + keepalive
│   ├── cron_bootstrap.sh     — Create all cron jobs (idempotent)
│   └── post-attach.sh        — Show status on VS Code connect
├── scripts/
│   ├── agent_mesh.py         — Agent-to-agent communication tool
│   ├── cloud_memory_pull.py  — Pull memory from local git
│   ├── cloud_health.py       — Health monitoring watchdog
│   └── gateway_keeper.py     — Gateway uptime monitor
├── docs/
│   └── agent-mesh-protocol.md — Full protocol specification
└── README.md
```

## Troubleshooting

**"Why isn't the webhook running?"**  
Restart the Hermes app on your local machine. The webhook config needs a gateway reload.

**"Cloud cron jobs aren't running"**  
Run `bash .devcontainer/cron_bootstrap.sh` manually. The postStartCommand should do this automatically.

**"Codespace keeps stopping"**  
Free accounts get 30h/month and auto-stop after 30min idle. The keepalive loop helps but GitHub's limits still apply.
