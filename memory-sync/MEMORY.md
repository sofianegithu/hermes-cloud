Active Hermes profile: default. Config lives under ~/.hermes/config.yaml. Skills/plugins/cron/memories live under ~/AppData\\Local\\hermes/...
§
WhatsApp bridge (Baileys) on localhost:3000
§
Cron fleet: Gateway Keeper (every 3min, auto-restarts), Health Watchdog (every 4h), Morning Power-Up (6AM, 4 parallel agents), Content Generator (10AM), Free API Hunter (12PM), Evening Wind-Down (9PM), Deep Audit (2AM), Auto-Improve (Sat), Weekly Review (Sun). All deliver to Telegram.
§
PC optimization Jun 28 2026: Freed ~17 GB. Cleared pip cache (9.1GB), npm, browser, AI tool caches, conda pkgs, old node_modules. Disabled startup bloat, visual effects, Windows Search indexing.
§
OpenCode auth.json has 16 provider keys (DeepSeek, Cohere, Groq, Mistral, etc.) at ~/.local/share/opencode/auth.json. Cloudflare Workers AI works (1.6s).
§
Fallback chain: remote first (Cloudflare, Google, Mistral, Cohere, opencode-zen), local LM Studio nemotron last resort only.
§
Sofiane's credential file (D:/General/_Organized/09_Documents/anthropic Api...) stores tokens truncated with '...' — never trust them directly, ask user for full token.
§
Hermes Cloud Codespace launched at https://hermes-cloud-gateway-694xgpvp69j63rr9r.github.dev — repo: sofianegithu/hermes-cloud (2 cores, 8GB RAM). Designed as 24/7 Telegram gateway fallback when local machine is off. Uses devcontainer with auto-start. 60h/month free on free GitHub account.
§
Cloud Failover system: cloud_failover.py runs every 5 min via cron (no_agent=true). Checks local gateway (port 3000). If DOWN → starts GitHub Codespace via API + alerts Telegram. If local recovers → stops Codespace to save hours. GitHub token stored in cloud_failover_config.json. Codespace name: hermes-cloud-gateway-jjqp5grgvxp52wj4.