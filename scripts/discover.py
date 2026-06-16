#!/usr/bin/env python3
"""Large-scale discovery of AI agent ecosystem tools on GitHub.

Broad queries, low star thresholds, no language filters, full page results.
Target: 30 results per query, 20+ queries = 600+ potential entries per run.

Usage: python3 discover.py [--dry-run]
"""
import json, os, sys, yaml, re, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from urllib.parse import quote

REGISTRY_ROOT = Path(__file__).resolve().parent.parent / "registry"
DISCOVERED_DIR = REGISTRY_ROOT / "_discovered"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", os.environ.get("GH_TOKEN", ""))

# Broad queries — no language filter, low star threshold, sorted by stars
QUERIES = [
    # ── MCP Ecosystem ──
    ("mcp server in:name,description stars:>1", "mcp-server"),
    ("model context protocol in:name,description stars:>1", "mcp-server"),
    ("mcp in:name stars:>5", "mcp-server"),
    ("mcp-client in:name,description stars:>1", "mcp-server"),
    ("mcp in:topics stars:>5", "mcp-server"),

    # ── AI Coding Agents ──
    ("ai coding agent cli in:name,description stars:>5", "agent"),
    ("ai agent terminal in:name,description stars:>5", "agent"),
    ("llm agent cli in:name,description stars:>5", "agent"),
    ("coding agent in:name,description stars:>10", "agent"),

    # ── Agent Frameworks ──
    ("agent framework in:name,description stars:>10", "tool"),
    ("multi-agent in:name,description stars:>5", "tool"),
    ("agent orchestration in:name,description stars:>5", "tool"),
    ("agent swarm in:name,description stars:>5", "tool"),

    # ── Agent Memory / RAG ──
    ("agent memory in:name,description stars:>5", "tool"),
    ("agent rag in:name,description stars:>5", "tool"),
    ("agent knowledge base in:name,description stars:>5", "tool"),

    # ── Evals & Benchmarks ──
    ("agent benchmark in:name,description stars:>5", "eval"),
    ("agent evaluation in:name,description stars:>5", "eval"),
    ("llm benchmark coding in:name,description stars:>10", "eval"),

    # ── Safety & Sandbox ──
    ("agent sandbox in:name,description stars:>3", "safety"),
    ("agent security in:name,description stars:>5", "safety"),
    ("ai agent guardrail in:name,description stars:>3", "safety"),

    # ── Agent Tool Use ──
    ("agent tool use in:name,description stars:>5", "tool"),
    ("function calling agent in:name,description stars:>5", "tool"),
    ("agent browser in:name,description stars:>10", "tool"),

    # ── Dev Tools / CI ──
    ("ai code review agent in:name,description stars:>5", "tool"),
    ("ai pr agent in:name,description stars:>5", "tool"),
    ("llm github action in:name,description stars:>5", "tool"),
]


def load_existing_keys():
    """Return set of (name_lower, homepage_lower) for dedup."""
    keys = set()
    for yaml_path in REGISTRY_ROOT.rglob("*.yaml"):
        if "_discovered" in str(yaml_path) or "_rejected" in str(yaml_path):
            continue
        try:
            data = yaml.safe_load(open(yaml_path))
            keys.add((data.get("name", "").lower(), data.get("homepage", "").lower()))
        except Exception:
            continue
    return keys


def github_api(path):
    url = f"https://api.github.com{path}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "agent-stack-registry/2.0"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except HTTPError as e:
        if e.code == 403:
            print(f"  ⚠️ Rate limited — waiting 60s...")
            time.sleep(60)
            return github_api(path)
        return None
    except Exception as e:
        print(f"  ⚠️ API error: {e}")
        return None


def search_repos(query, sort="stars", per_page=30):
    params = f"?q={quote(query)}&sort={sort}&order=desc&per_page={per_page}"
    result = github_api(f"/search/repositories{params}")
    if result and "items" in result:
        return result["items"], result.get("total_count", 0)
    return [], 0


def generate_entry(repo, category):
    return {
        "name": repo["name"],
        "repo": repo["full_name"],
        "category": category,
        "homepage": repo["html_url"],
        "description": (repo.get("description") or "")[:200],
        "license": (repo.get("license") or {}).get("spdx_id", "unknown") if repo.get("license") else "unknown",
        "open_source": not repo.get("private", False),
        "interface": _guess_interface(repo),
        "status": "archived" if repo.get("archived") else "active",
        "last_verified": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "stars": repo.get("stargazers_count", 0),
        "agent_fit_score": 5.0,
        "tags": repo.get("topics", [])[:8],
        "notes": [f"Auto-discovered {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"],
        "evidence": [repo["html_url"]],
    }


def _guess_interface(repo):
    topics = repo.get("topics", [])
    desc = (repo.get("description") or "").lower()
    ifaces = []
    if "mcp" in topics or "mcp" in desc:
        ifaces.append("mcp")
    if "cli" in topics or "cli" in desc:
        ifaces.append("cli")
    if "api" in topics or "api" in desc:
        ifaces.append("api")
    if "vscode" in topics or "vscode" in desc:
        ifaces.append("vscode")
    return ifaces or ["cli"]


def main():
    dry_run = "--dry-run" in sys.argv
    existing = load_existing_keys()
    print(f"📋 {len(existing)} existing entries indexed\n")

    new_entries = []
    seen = set()
    total_found = 0

    for q, category in QUERIES:
        print(f"🔍 [{category}] {q[:70]}...")
        repos, total = search_repos(q, per_page=30)
        total_found += total
        new_in_query = 0

        for repo in repos:
            full_name = repo["full_name"]
            if full_name in seen:
                continue
            seen.add(full_name)

            key = (repo["name"].lower(), repo["html_url"].lower())
            if any(k[0] == key[0] or k[1] == key[1] for k in existing):
                continue

            entry = generate_entry(repo, category)
            new_entries.append(entry)
            new_in_query += 1

        print(f"   → {new_in_query} new (of {len(repos)} returned, ~{total} total)")
        time.sleep(1.5)

    print(f"\n{'='*50}")
    print(f"📊 Total found across all queries: ~{total_found}")
    print(f"✨ New entries: {len(new_entries)}")

    if dry_run:
        print("(dry-run — not writing files)")
        cats = {}
        for e in new_entries:
            cats[e["category"]] = cats.get(e["category"], 0) + 1
        for cat, count in sorted(cats.items()):
            print(f"  {cat}: {count}")
        return 0

    if not new_entries:
        print("✅ Registry up to date.")
        return 0

    DISCOVERED_DIR.mkdir(parents=True, exist_ok=True)
    for entry in new_entries:
        fname = re.sub(r"[^a-z0-9_-]", "-", entry["name"].lower())[:60] + ".yaml"
        with open(DISCOVERED_DIR / fname, "w") as f:
            f.write(f"# Auto-discovered: {entry['repo']}\n")
            yaml.dump(entry, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"\n💾 {len(new_entries)} entries written to registry/_discovered/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
