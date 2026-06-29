#!/usr/bin/env python3
"""
🤝 AGENT MESH PROTOCOL — communication layer between local and cloud Hermes agents.

This script enables bidirectional agent-to-agent communication:
  - Cloud agents can delegate tasks to local (via webhook)
  - Local can send results back to cloud (via Telegram/WhatsApp)
  - Knowledge is shared between all agents
  - Each agent reports its capabilities and status

Usage:
  python agent_mesh.py send-task <target> <task_json>   # Send a task to another agent
  python agent_mesh.py broadcast <message>              # Broadcast to all agents
  python agent_mesh.py status                           # Report this agent's status
"""

import json, sys, os, urllib.request, time, hmac, hashlib
from pathlib import Path
from datetime import datetime

HOME = Path.home()
DATA = HOME / "AppData/Local/hermes"
LOG_FILE = DATA / "agent_mesh.log"

# === CONFIG ===
LOCAL_WEBHOOK_URL = os.environ.get("LOCAL_WEBHOOK_URL", "http://localhost:8644")
LOCAL_WEBHOOK_SECRET = os.environ.get("LOCAL_WEBHOOK_SECRET", "mesh-webhook-secret")
CLOUD_WEBHOOK_URL = os.environ.get("CLOUD_WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "5615834073")


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    DATA.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def hmac_sign(payload: str, secret: str) -> str:
    """HMAC-SHA256 sign a payload."""
    return hmac.new(
        secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()


def send_webhook(url: str, secret: str, event: str, payload: dict) -> dict:
    """Send a task/event to an agent's webhook endpoint."""
    body = json.dumps(payload).encode()
    signature = hmac_sign(body.decode(), secret)

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Secret": secret,
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": event,
            "User-Agent": "Hermes-Mesh-Agent/1.0"
        }
    )
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read())
        log(f"✅ Sent {event} to {url} — status: {result.get('status', 'ok')}")
        return result
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        log(f"❌ HTTP {e.code} from {url}: {body[:200]}")
        return {"status": "error", "code": e.code, "detail": body[:200]}
    except Exception as e:
        log(f"❌ Failed to reach {url}: {e}")
        return {"status": "error", "detail": str(e)}


def send_telegram(message: str) -> dict:
    """Send a message via Telegram (used by local to reach cloud)."""
    if not TELEGRAM_BOT_TOKEN:
        log("⚠️ No TELEGRAM_BOT_TOKEN set")
        return {"status": "error", "detail": "no token"}
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}
        )
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        log(f"✅ Sent Telegram message")
        return result
    except Exception as e:
        log(f"❌ Telegram send failed: {e}")
        return {"status": "error", "detail": str(e)}


# === TASK TYPES ===

TASK_TEMPLATES = {
    "execute": {
        "description": "Run a terminal command and return output",
        "fields": ["command", "workdir", "timeout"],
        "example": {"command": "ls -la", "workdir": "/home/user", "timeout": 30}
    },
    "file_read": {
        "description": "Read a file and return contents",
        "fields": ["path", "offset", "limit"],
        "example": {"path": "/home/user/config.yaml", "offset": 1, "limit": 100}
    },
    "file_write": {
        "description": "Write content to a file",
        "fields": ["path", "content"],
        "example": {"path": "/tmp/output.txt", "content": "Hello from cloud!"}
    },
    "search": {
        "description": "Search files on the local system",
        "fields": ["pattern", "path", "target"],
        "example": {"pattern": "api_key", "path": "/home/user", "target": "content"}
    },
    "system_status": {
        "description": "Get local system health report",
        "fields": [],
        "example": {}
    },
    "knowledge_query": {
        "description": "Query local agent's memory/knowledge",
        "fields": ["query"],
        "example": {"query": "What do we know about the project setup?"}
    },
    "knowledge_share": {
        "description": "Share knowledge with the local agent",
        "fields": ["topic", "content", "source"],
        "example": {"topic": "API endpoints", "content": "New endpoint discovered...", "source": "cloud-agent"}
    }
}


def format_task(agent_id: str, task_type: str, payload: dict, reply_channel: str = "telegram") -> dict:
    """Format a standardized task for agent-to-agent communication."""
    return {
        "protocol_version": "1.0",
        "from_agent": agent_id,
        "task_type": task_type,
        "payload": payload,
        "reply_channel": reply_channel,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "task_id": f"task-{int(time.time())}-{hashlib.md5(json.dumps(payload).encode()).hexdigest()[:8]}"
    }


def format_response(task: dict, success: bool, data: any, error: str = None) -> dict:
    """Format a standardized response."""
    return {
        "protocol_version": "1.0",
        "in_response_to": task.get("task_id", ""),
        "from_agent": task.get("to_agent", "local-hermes"),
        "to_agent": task.get("from_agent", "cloud-hermes"),
        "success": success,
        "data": data,
        "error": error,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


def show_status():
    """Show this agent's status in mesh format."""
    status = {
        "agent_id": "local-hermes",
        "hostname": os.uname().nodename if hasattr(os, 'uname') else "windows",
        "platform": sys.platform,
        "capabilities": [
            "execute", "file_read", "file_write", "search",
            "system_status", "knowledge_query", "knowledge_share",
            "computer_use", "browser", "delegation"
        ],
        "webhook_url": LOCAL_WEBHOOK_URL,
        "webhook_endpoints": {
            "execute-task": f"{LOCAL_WEBHOOK_URL}/webhooks/execute-task",
            "system-status": f"{LOCAL_WEBHOOK_URL}/webhooks/system-status",
            "knowledge-share": f"{LOCAL_WEBHOOK_URL}/webhooks/knowledge-share"
        },
        "status": "online",
        "last_seen": datetime.utcnow().isoformat() + "Z"
    }
    print(json.dumps(status, indent=2))
    return status


# === MAIN ===

def main():
    if len(sys.argv) < 2:
        print("Agent Mesh Protocol — Communication layer for Hermes agent swarm")
        print("")
        print("Usage:")
        print("  python agent_mesh.py status                    Show this agent's status")
        print("  python agent_mesh.py send-task <url> <json>    Send a task to another agent")
        print("  python agent_mesh.py to-cloud <task_json>      Send task to cloud via Telegram")
        print("  python agent_mesh.py to-local <task_json>      Send task to local via webhook")
        print("  python agent_mesh.py templates                 Show available task templates")
        print("")
        print("Templates:")
        for name, tpl in TASK_TEMPLATES.items():
            print(f"  {name}: {tpl['description']}")
        return

    cmd = sys.argv[1]

    if cmd == "status":
        show_status()

    elif cmd == "send-task" and len(sys.argv) >= 4:
        url = sys.argv[2]
        payload = json.loads(sys.argv[3])
        result = send_webhook(url, LOCAL_WEBHOOK_SECRET, "task.execute", payload)
        print(json.dumps(result, indent=2))

    elif cmd == "to-local" and len(sys.argv) >= 3:
        task = json.loads(sys.argv[2])
        endpoint = task.get("endpoint", "execute-task")
        url = f"{LOCAL_WEBHOOK_URL}/webhooks/{endpoint}"
        event = task.get("event", "task.execute")
        result = send_webhook(url, LOCAL_WEBHOOK_SECRET, event, task)
        print(json.dumps(result, indent=2))

    elif cmd == "to-cloud" and len(sys.argv) >= 3:
        task = json.loads(sys.argv[2])
        message = json.dumps(task, indent=2)
        result = send_telegram(f"📤 **Task from Local → Cloud**\n```json\n{message}\n```")
        print(json.dumps(result, indent=2))

    elif cmd == "templates":
        print(json.dumps(TASK_TEMPLATES, indent=2))

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
