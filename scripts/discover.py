#!/usr/bin/env python3
"""Discover new MCP servers & AI agent tools on GitHub, generate YAML entries.

Usage: python3 discover.py [--dry-run] [--max 10]
Output: New entries written to registry/_discovered/
"""
import json, os, sys, yaml, re, time, subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError

REGISTRY_ROOT = Path(__file__).resolve().parent.parent / "registry"
DISCOVERED_DIR = REGISTRY_ROOT / "_discovered"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "entry.schema.json"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", os.environ.get("GH_TOKEN", ""))

QUERIES = [
    # MCP servers (primary focus)
    {
        "q": "mcp server in:name,description language:typescript stars:>10",
        "category": "mcp-server",
        "sort": "stars",
    },
    {
        "q": "mcp server in:name,description language:python stars:>10",
        "category": "mcp-server",
        "sort": "stars",
    },
    {
        "q": "mcp tool in:name,description stars:>20",
        "category": "tool",
        "sort": "stars",
    },
    # AI coding agents
    {
        "q": "ai coding agent cli in:name,description stars:>50",
        "category": "agent",
        "sort": "stars",
    },
    # Agent evals / benchmarks
    {
        "q": "agent benchmark eval in:name,description stars:>20",
        "category": "eval",
        "sort": "stars",
    },
    # Safety / sandbox
    {
        "q": "agent sandbox safety in:name,description stars:>10",
        "category": "safety",
        "sort": "stars",
    },
]

# Map GitHub languages to entry categories
LANG_TO_CATEGORY = {
    "TypeScript": "mcp-server",
    "Python": "mcp-server",
    "Go": "tool",
    "Rust": "tool",
}

def load_existing_entries():
    """Load all existing registry entries and return a set of (name, homepage) keys."""
    existing = {}
    for yaml_path in REGISTRY_ROOT.rglob("*.yaml"):
        if "_discovered" in str(yaml_path):
            continue
        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
            key = (data.get("name", "").lower(), data.get("homepage", "").lower())
            existing[key] = data
        except Exception:
            continue
    return existing


def github_api(path):
    """Call GitHub REST API."""
    url = f"https://api.github.com{path}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "agent-stack-registry/1.0"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except HTTPError as e:
        print(f"  ⚠️ GitHub API error: {e.code} {path}")
        return None


def search_repos(query, sort="stars", per_page=10):
    """Search GitHub repos."""
    from urllib.parse import quote
    params = f"?q={quote(query)}&sort={sort}&order=desc&per_page={per_page}"
    result = github_api(f"/search/repositories{params}")
    if result and "items" in result:
        return result["items"]
    return []


def guess_license(repo):
    """Extract license from repo data."""
    lic = repo.get("license")
    if lic and lic.get("spdx_id"):
        return lic["spdx_id"]
    return "unknown"


def guess_interface(repo):
    """Guess interface from description and topics."""
    topics = repo.get("topics", [])
    desc = (repo.get("description") or "").lower()
    interfaces = []
    if "mcp" in topics or "mcp" in desc:
        interfaces.append("mcp")
    if "cli" in topics or "cli" in desc:
        interfaces.append("cli")
    if "api" in topics or "api" in desc:
        interfaces.append("api")
    if "vscode" in topics or "vscode" in desc:
        interfaces.append("vscode")
    return interfaces or ["cli"]


def generate_entry(repo, category):
    """Generate a YAML entry dict from a GitHub repo."""
    name = repo["full_name"]
    desc = repo.get("description") or ""
    topics = repo.get("topics", [])

    return {
        "name": repo["name"],
        "repo": repo["full_name"],
        "category": category,
        "homepage": repo["html_url"],
        "description": desc[:200] if desc else "",
        "license": guess_license(repo),
        "open_source": not repo.get("private", False),
        "interface": guess_interface(repo),
        "status": "active" if repo.get("archived") != True else "archived",
        "last_verified": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "stars": repo.get("stargazers_count", 0),
        "agent_fit_score": 5.0,  # placeholder, needs manual review
        "tags": topics[:8] if topics else [],
        "notes": [f"Auto-discovered {datetime.now(timezone.utc).strftime('%Y-%m-%d')}", desc[:150]],
        "evidence": [repo["html_url"]],
    }


def sanitize_filename(name):
    """Sanitize repo name to a valid filename."""
    return re.sub(r"[^a-z0-9_-]", "-", name.lower())[:60] + ".yaml"


def main():
    dry_run = "--dry-run" in sys.argv
    max_results = 10
    for i, arg in enumerate(sys.argv):
        if arg == "--max" and i + 1 < len(sys.argv):
            max_results = int(sys.argv[i + 1])

    existing = load_existing_entries()
    print(f"📋 {len(existing)} existing entries loaded\n")

    new_entries = []
    seen_repos = set()

    for query_cfg in QUERIES:
        print(f"🔍 Searching: {query_cfg['q'][:80]}...")
        repos = search_repos(query_cfg["q"], query_cfg.get("sort", "stars"), per_page=5)

        for repo in repos:
            full_name = repo["full_name"]
            if full_name in seen_repos:
                continue
            seen_repos.add(full_name)

            # Check if already in registry (by name or homepage)
            key_lower = (repo["name"].lower(), repo["html_url"].lower())
            if any(
                k[0] == repo["name"].lower() or k[1] == repo["html_url"].lower()
                for k in existing
            ):
                print(f"  ⏭️  {full_name} — already in registry")
                continue

            entry = generate_entry(repo, query_cfg["category"])
            new_entries.append(entry)
            print(f"  ✨ {full_name} ⭐{repo.get('stargazers_count',0)} — new {query_cfg['category']}")

        if len(new_entries) >= max_results:
            break
        time.sleep(1.5)  # rate limit courtesy

    if not new_entries:
        print("\n✅ No new entries found. Registry is up to date.")
        return 0

    print(f"\n📝 {len(new_entries)} new entries to add:")

    if dry_run:
        print("(dry-run — not writing files)")
        for entry in new_entries:
            print(f"  → {entry['name']} [{entry['category']}]")
        return 0

    DISCOVERED_DIR.mkdir(parents=True, exist_ok=True)

    for entry in new_entries:
        filename = sanitize_filename(entry["name"])
        filepath = DISCOVERED_DIR / filename
        with open(filepath, "w") as f:
            f.write(f"# Auto-discovered: {entry['repo']}\n")
            f.write(f"# Review and move to registry/<category>/ when ready\n")
            yaml.dump(entry, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print(f"  💾 {filepath.relative_to(REGISTRY_ROOT.parent)}")

    # Generate summary markdown
    summary_path = DISCOVERED_DIR / "SUMMARY.md"
    with open(summary_path, "w") as f:
        f.write(f"# Discovered Entries — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n")
        f.write(f"Auto-discovered {len(new_entries)} new entries.\n\n")
        f.write("| Name | Category | Stars | License |\n")
        f.write("|------|----------|-------|--------|\n")
        for entry in new_entries:
            f.write(f"| [{entry['name']}]({entry['homepage']}) | {entry['category']} | ⭐{entry['stars']} | {entry['license']} |\n")
        f.write(f"\n## Next Steps\n\n")
        f.write(f"1. Review each YAML in `registry/_discovered/`\n")
        f.write(f"2. Adjust `agent_fit_score` and `score_breakdown`\n")
        f.write(f"3. Move approved entries to `registry/<category>/`\n")
        f.write(f"4. Run `python3 scripts/validate_registry.py`\n")

    print(f"\n📊 Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
