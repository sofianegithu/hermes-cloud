#!/usr/bin/env python3
"""☁️ Cloud Agent Innovation Research — runs daily on cloud Codespace
Rotates through 7 different sources so it never visits the same place twice in a week.
Delivers findings to Telegram so Sofiane gets daily tips even when PC is off.
"""
import json, urllib.request, os, sys, re, time
from pathlib import Path
from datetime import datetime, timezone
from html.parser import HTMLParser

HOME = Path.home()
DATA = HOME / ".hermes"
LOG = DATA / "logs" / "research.log"
OUTPUT = DATA / "cron" / "research_output.json"
RESEARCH_NOTE = DATA / "research_state.json"

# Day-of-week rotation (0=Mon, 6=Sun)
SOURCES = {
    0: {"name": "GitHub Trending", "url": "https://github.com/trending/python?since=weekly"},
    1: {"name": "Hugging Face Daily Papers", "url": "https://huggingface.co/papers"},
    2: {"name": "ArXiv LLM Papers (cs.CL)", "url": "https://arxiv.org/list/cs.CL/recent"},
    3: {"name": "Hacker News - AI/LLM", "url": "https://hn.algolia.com/api/v1/search?query=llm+agent&tags=story&hitsPerPage=10"},
    4: {"name": "Reddit r/LocalLLaMA", "url": "https://www.reddit.com/r/LocalLLaMA/hot.json?limit=10"},
    5: {"name": "Nous Research Hermes GitHub", "url": "https://api.github.com/repos/nousresearch/hermes-agent/releases?per_page=5"},
    6: {"name": "Tech Blogs (Anthropic)", "url": "https://www.anthropic.com/engineering"},
}

HEADERS = {
    "User-Agent": "HermesCloudResearch/1.0",
    "Accept": "text/html,application/json,*/*"
}

def log(msg):
    DATA.mkdir(parents=True, exist_ok=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(LOG, "a") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

def fetch(url, timeout=30):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode("utf-8", errors="replace")
            return content, resp.status, resp.headers.get("Content-Type", "")
    except Exception as e:
        return None, 0, str(e)

def extract_text(html):
    """Strip HTML tags."""
    class Parser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.text = []
        def handle_data(self, data):
            cleaned = data.strip()
            if cleaned:
                self.text.append(cleaned)
    p = Parser()
    p.feed(html)
    return " ".join(p.text)

def research_github_trending(content):
    """Parse GitHub trending page for interesting AI repos."""
    repos = []
    # GitHub trending uses <h2 class="h3 lh-condensed"> with <a href="/owner/repo">
    # Match repo URLs like /owner/repo (but NOT language links like /trending/python?since=)
    for match in re.finditer(r'href="/([^/"]+/[^/"]+)"[^>]*>', content):
        repo = match.group(1)
        # Skip non-repo links (language filters, etc.)
        if '/' not in repo: continue
        if repo.startswith('trending/'): continue
        if repo.startswith('search/'): continue
        if repo.startswith('login'): continue
        if repo.startswith('settings'): continue
        if repo.startswith('topics/'): continue
        if repo.startswith('explore/'): continue
        if repo.startswith('collections/'): continue
        # Only keep AI/agent/LLM related repos
        if any(k in repo.lower() for k in ["ai", "llm", "agent", "transform", "gpt", "langchain", "rag", "embed", "deep", "neural", "cog", "gen", "chat", "bot", "assist", "autom"]):
            full_url = f"https://github.com/{repo}"
            if full_url not in repos:
                repos.append(full_url)
    return repos[:8]

def research_huggingface(content):
    """Extract paper titles from Hugging Face daily papers."""
    papers = []
    for line in content.split("\n"):
        if "Daily Papers" in line or "paper-title" in line or line.strip().startswith("<h"):
            text = extract_text(line)
            if len(text) > 20 and len(text) < 200:
                papers.append(text)
    return papers[:10]

def research_arxiv(content):
    """Extract paper titles from ArXiv."""
    papers = []
    for line in content.split("\n"):
        if line.startswith("Title:"):
            papers.append(line.replace("Title:", "").strip())
    return papers[:10]

def research_hn(content):
    """Parse Hacker News API results."""
    try:
        data = json.loads(content)
        items = []
        for hit in data.get("hits", []):
            title = hit.get("title", "")
            url = hit.get("url", f"https://news.ycombinator.com/item?id={hit.get('objectID','')}")
            points = hit.get("points", 0)
            if points >= 5:
                items.append(f"• {title} ({points} pts) → {url}")
        return items[:8]
    except:
        return ["[Parse error]"]

def research_reddit(content):
    """Parse Reddit JSON."""
    try:
        data = json.loads(content)
        items = []
        for child in data.get("data", {}).get("children", []):
            d = child.get("data", {})
            title = d.get("title", "")
            url = d.get("url", "")
            score = d.get("score", 0)
            if score >= 5:
                items.append(f"• {title} ({score}↑) → {url}")
        return items[:8]
    except:
        return ["[Parse error]"]

def research_github_releases(content):
    """Parse Hermes GitHub releases."""
    try:
        data = json.loads(content)
        items = []
        for rel in data:
            name = rel.get("name") or rel.get("tag_name", "")
            body = rel.get("body", "")[:300]
            url = rel.get("html_url", "")
            items.append(f"📦 {name} → {url}")
            if body:
                items.append(f"   {body}")
        return items[:8]
    except:
        return ["[Parse error or no releases]"]

def research_anthropic(content):
    """Extract article links from Anthropic blog."""
    articles = []
    for line in content.split("\n"):
        if 'href="/engineering/' in line:
            match = re.search(r'href="(/engineering/[^"]+)"', line)
            if match:
                articles.append(f"https://www.anthropic.com{match.group(1)}")
    # Deduplicate
    seen = set()
    unique = []
    for a in articles:
        if a not in seen:
            seen.add(a)
            unique.append(a)
    return unique[:5]

def format_result(name, findings, source_url):
    if not findings:
        return None
    header = f"## 📡 {name}\n"
    items = "\n".join(findings[:8])
    footer = f"\n🔗 {source_url}"
    return header + items + footer

def main():
    day = datetime.now(timezone.utc).weekday()
    source = SOURCES.get(day, SOURCES[0])
    
    log(f"Starting research: {source['name']} (Day {day})")
    print(f"🌐 Source: {source['name']}")
    print(f"📎 URL: {source['url']}")
    print()
    
    content, status, ctype = fetch(source["url"])
    
    if not content:
        msg = f"❌ Failed to fetch {source['name']}: {status}"
        log(msg)
        print(msg)
        # Try fallback source (previous day)
        fallback_day = (day - 1) % 7
        fallback = SOURCES[fallback_day]
        log(f"Trying fallback: {fallback['name']}")
        content, status, ctype = fetch(fallback["url"])
        if not content:
            print(f"❌ Fallback also failed: {status}")
            return
        source = fallback
        print(f"⚠️ Using fallback: {source['name']}")
    
    print(f"✅ Fetched {len(content)} chars (HTTP {status})")
    
    # Route to appropriate parser
    parsers = {
        "GitHub Trending": research_github_trending,
        "Hugging Face Daily Papers": research_huggingface,
        "ArXiv LLM Papers (cs.CL)": research_arxiv,
        "Hacker News - AI/LLM": research_hn,
        "Reddit r/LocalLLaMA": research_reddit,
        "Nous Research Hermes GitHub": research_github_releases,
        "Tech Blogs (Anthropic)": research_anthropic,
    }
    
    parser = parsers.get(source["name"])
    if parser:
        findings = parser(content)
    else:
        findings = [extract_text(content)[:500]]
    
    result = format_result(source["name"], findings, source["url"])
    
    if result:
        print("\n" + "=" * 50)
        print(result)
        print("=" * 50)
        
        # Save output for delivery
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT, "w") as f:
            json.dump({
                "date": datetime.now(timezone.utc).isoformat(),
                "source": source["name"],
                "url": source["url"],
                "findings": findings[:8],
                "summary": result
            }, f, indent=2)
        
        log(f"✅ Research complete: {len(findings)} findings from {source['name']}")
        print(f"\n📁 Output saved to: {OUTPUT}")
        
        # Save state for rotation tracking
        RESEARCH_NOTE.parent.mkdir(parents=True, exist_ok=True)
        with open(RESEARCH_NOTE, "w") as f:
            json.dump({
                "last_run": datetime.now(timezone.utc).isoformat(),
                "last_source": source["name"],
                "days_tracked": list(SOURCES.keys())
            }, f)
    else:
        log(f"⚠️ No findings from {source['name']}")
        print("No findings extracted.")

if __name__ == "__main__":
    main()
