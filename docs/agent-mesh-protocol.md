# 🤝 Hermes Agent Mesh Protocol

**Version 1.0** — Inter-agent communication protocol for local ↔ cloud Hermes agents.

## Architecture

```
☁️ CLOUD HERMES (Codespace)          🖥️ LOCAL HERMES (Laptop)
                                     ┌─────────────────────────┐
  ┌────────────────────┐             │ Telegram Gateway (3000)  │
  │ Telegram Bot       │◄───────────►│ WhatsApp Bridge (3000)  │
  │ Replies 24/7       │             │ Webhook API (8644)      │
  │ Cron Jobs          │             │ Full Tool Access        │
  │ Skills & Memory    │             │ Cron Jobs               │
  └──────┬─────────────┘             │ Computer Use            │
         │                           └──────────┬──────────────┘
         │ Webhook: localtask.execute            │ Webhook: knowledge.share
         │ Webhook: system.status                │ Webhook: task.execute
         │                              Messages
         └──────────────────────────────────────────────────────┘
                    Telegram / Cloudflare Tunnel
```

## How It Works

### Local → Cloud (me → cloud)
When local needs cloud to do something:
1. Sends structured task via **Telegram** to the cloud agent
2. Cloud receives it, processes, responds back to Telegram

### Cloud → Local (cloud → me)
When cloud needs local to do something:
1. Calls local **webhook API** at `http://localhost:8644/webhooks/<endpoint>`
2. Local processes the task, returns structured result

### Bidirectional Knowledge
Memory sync happens via **Git** (every 15 min) and **webhook broadcast** (realtime).

## Task Protocol

Every task follows this JSON structure:

```json
{
  "protocol_version": "1.0",
  "from_agent": "cloud-hermes",
  "to_agent": "local-hermes",
  "task_type": "execute",
  "task_id": "task-1748567890-a1b2c3d4",
  "payload": {
    "command": "ls -la",
    "workdir": "/home/user",
    "timeout": 30
  },
  "reply_channel": "telegram",
  "timestamp": "2026-06-30T10:30:00Z"
}
```

**Response format:**

```json
{
  "protocol_version": "1.0",
  "in_response_to": "task-1748567890-a1b2c3d4",
  "from_agent": "local-hermes",
  "to_agent": "cloud-hermes",
  "success": true,
  "data": "total 24\n-rw-r--r-- 1 user user 1234 ...",
  "error": null,
  "timestamp": "2026-06-30T10:30:05Z"
}
```

## Task Types

| Type | Description | From |
|------|-------------|------|
| `execute` | Run a terminal command | Cloud → Local |
| `file_read` | Read a file's contents | Cloud → Local |
| `file_write` | Write content to a file | Cloud → Local |
| `search` | Search local filesystem | Cloud → Local |
| `system_status` | Get local health report | Cloud → Local |
| `knowledge_query` | Query our knowledge base | Both |
| `knowledge_share` | Share a learning | Both |
| `delegate` | Delegate to sub-agents | Both |
| `computer_use` | Use local desktop | Cloud → Local |

## Webhook Endpoints (Local)

| Endpoint | Event | Purpose |
|----------|-------|---------|
| `/webhooks/execute-task` | `task.execute` | Execute terminal/file tasks |
| `/webhooks/system-status` | `system.status` | Report local system health |
| `/webhooks/knowledge-share` | `knowledge.share` | Share learnings with local |

All endpoints require `X-Webhook-Secret` and optional `X-Webhook-Signature` headers.

## Usage

### Cloud → Local (send a task)

```bash
# Using agent_mesh.py
python agent_mesh.py to-local '{
  "task_type": "execute",
  "payload": {"command": "whoami", "timeout": 10}
}'

# Direct curl
curl -X POST http://localhost:8644/webhooks/execute-task \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: mesh-webhook-secret" \
  -d '{"task_type":"execute","payload":{"command":"whoami"}}'
```

### Local → Cloud (send a task)

```bash
# Using agent_mesh.py
python agent_mesh.py to-cloud '{
  "task_type": "knowledge_share",
  "payload": {"topic": "New API discovered", "content": "...", "source": "free-api-hunter"}
}'
```

### Check Agent Status

```bash
python agent_mesh.py status
```

## Failover Lifecycle

1. **Normal** — Both agents active, local handles heavy work, cloud handles messaging
2. **Laptop Sleeps** — Cron stops locally, cloud continues Telegram + cron
3. **Laptop Returns** — Cloud pull latest memory, resume sync
4. **Codespace Stops** (30h limit) — Cloud shuts down gracefully
5. **Laptop On, Cloud Off** — Local runs everything, waits for cloud restart

## Setup Checklist

- [x] Local webhook subscriptions created
- [x] Agent mesh Python utility written
- [x] Cloud cron bootstrapper written
- [x] Cloud full agent config written
- [ ] Restart Hermes app to activate webhook server
- [ ] Set up Cloudflare Tunnel for public webhook URL
- [ ] Set up GitHub Codespaces secrets (TELEGRAM_BOT_TOKEN)
- [ ] Push to cloud repo
- [ ] Test cloud → local task delegation
- [ ] Test local → cloud knowledge sharing
