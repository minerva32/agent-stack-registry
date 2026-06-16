#!/usr/bin/env python3
"""Score and promote discovered registry entries using repo metadata only.

Fast path — no README fetching. Uses stars, description, topics, license,
recent pushes from the GitHub API repo endpoint. Scales to 1000+ entries.
"""
import json, os, sys, yaml, time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError

REGISTRY_ROOT = Path(__file__).resolve().parent.parent / "registry"
DISCOVERED_DIR = REGISTRY_ROOT / "_discovered"
REJECTED_DIR = REGISTRY_ROOT / "_rejected"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", os.environ.get("GH_TOKEN", ""))

CATEGORY_DIR_MAP = {
    "mcp-server": "mcp-servers", "agent": "agents", "tool": "tools",
    "eval": "evals", "safety": "safety", "protocol": "protocols",
    "template": "templates", "repo": "repos",
}


def github_api(path):
    url = f"https://api.github.com{path}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "agent-stack-registry/2.0"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except HTTPError as e:
        if e.code == 403:
            time.sleep(60)
            return github_api(path)
        return None
    except Exception:
        return None


def fetch_meta(full_name):
    return github_api(f"/repos/{full_name}")


def is_false_positive(entry, meta):
    """Check if repo is clearly NOT what category claims, based on metadata."""
    category = entry.get("category", "")
    desc = (meta.get("description") or "").lower()
    topics = [t.lower() for t in meta.get("topics", [])]
    name = (meta.get("name") or "").lower()

    if category == "mcp-server":
        signals = "mcp" in desc or "mcp" in name or any("mcp" in t for t in topics)
        if not signals:
            return True, "no MCP signal in name/description/topics"
    elif category == "agent":
        signals = any(w in desc for w in ["agent", "cli", "coding", "ai "])
        if not signals:
            return True, "no agent signal"
    return False, ""


def compute_score(meta, category):
    """Score 0-10 from metadata signals only."""
    desc = (meta.get("description") or "").lower()
    topics = [t.lower() for t in meta.get("topics", [])]
    stars = meta.get("stargazers_count", 0)
    pushed = meta.get("pushed_at", "")
    open_issues = meta.get("open_issues_count", 0)
    has_wiki = meta.get("has_wiki", False)
    has_pages = meta.get("has_pages", False)
    forks = meta.get("forks_count", 0)
    license_spdx = (meta.get("license") or {}).get("spdx_id", "")

    s = {}

    # installability: inferred from language + package signals in topics
    lang = (meta.get("language") or "").lower()
    has_pkg = any(t in topics for t in ["npm", "pip", "pypi", "docker", "npm-package", "docker-image", "homebrew"])
    has_cli_topic = "cli" in topics
    s["installability"] = min(10, 4 + (lang in ("python","typescript","javascript","go","rust"))*2 + has_pkg*2 + has_cli_topic*2)

    # automation_readiness
    has_mcp = "mcp" in topics or category == "mcp-server"
    has_api = "api" in topics or "rest" in topics
    s["automation_readiness"] = min(10, 3 + has_mcp*4 + has_cli_topic*3 + has_api*2)

    # extensibility: plugin/config topics
    has_plugins = any(t in topics for t in ["plugin","plugins","extension","extensible","modular"])
    has_config = any(t in topics for t in ["configuration","config","dotenv","yaml","json-config"])
    s["extensibility"] = min(10, 3 + has_plugins*4 + has_config*3)

    # repo_clarity: inferred from has_wiki, has_pages, license, description length
    has_license = bool(license_spdx and license_spdx != "NOASSERTION")
    desc_len = len(desc)
    s["repo_clarity"] = min(10, 2 + has_wiki*2 + has_pages*1 + has_license*3 + min(desc_len/100, 2))

    # sandbox_safety
    has_docker = "docker" in topics
    has_sandbox = "sandbox" in topics or "sandbox" in desc
    s["sandbox_safety"] = min(10, 2 + has_docker*4 + has_sandbox*4)

    # reproducibility: CI, lockfiles
    has_ci = meta.get("has_ci", False) or "ci" in topics or "github-actions" in topics or "cicd" in topics
    s["reproducibility"] = min(10, 2 + has_ci*5 + has_license*3)

    # maintenance: stars, recent push, open issues ratio
    updated = False
    if pushed:
        try:
            dt = datetime.strptime(pushed[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            updated = (datetime.now(timezone.utc) - dt) < timedelta(days=90)
        except: pass
    star_bonus = 0
    if stars > 50000: star_bonus = 5
    elif stars > 10000: star_bonus = 4
    elif stars > 1000: star_bonus = 3
    elif stars > 100: star_bonus = 2
    elif stars > 10: star_bonus = 1
    issue_penalty = max(0, open_issues / 500)
    s["maintenance"] = min(10, 2 + updated*3 + star_bonus - issue_penalty)

    overall = round(sum(s.values()) / len(s), 1)
    return overall, s


def main():
    dry_run = "--dry-run" in sys.argv
    entries = sorted(DISCOVERED_DIR.glob("*.yaml"))
    if not entries:
        print("✅ No entries to score.")
        return 0

    total = len(entries)
    print(f"🔍 Scoring {total} entries (metadata-only, no README)...\n")
    promoted, rejected, kept = [], [], []

    for i, ep in enumerate(entries):
        entry = yaml.safe_load(open(ep))
        name = entry.get("name", ep.stem)
        full_name = entry.get("repo", name)
        category = entry.get("category", "unknown")

        meta = fetch_meta(full_name)
        if not meta:
            kept.append((name, "API fetch failed"))
            continue

        is_fp, reason = is_false_positive(entry, meta)
        if is_fp:
            REJECTED_DIR.mkdir(parents=True, exist_ok=True)
            entry["reject_reason"] = reason
            if not dry_run:
                yaml.dump(entry, open(REJECTED_DIR / ep.name, "w"),
                         default_flow_style=False, allow_unicode=True, sort_keys=False)
                ep.unlink()
            rejected.append((name, reason))
            continue

        score, breakdown = compute_score(meta, category)
        entry["agent_fit_score"] = score
        entry["score_breakdown"] = breakdown
        entry["last_verified"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        entry["stars"] = meta.get("stargazers_count", 0)
        entry["tags"] = meta.get("topics", [])[:8]
        entry["evidence"] = [meta.get("html_url", "")]

        if score >= 6.0:
            cat_dir = CATEGORY_DIR_MAP.get(category, "tools")
            target = REGISTRY_ROOT / cat_dir / ep.name
            target.parent.mkdir(parents=True, exist_ok=True)
            if not dry_run:
                yaml.dump(entry, open(target, "w"),
                         default_flow_style=False, allow_unicode=True, sort_keys=False)
                ep.unlink()
            promoted.append((name, score, cat_dir))
        else:
            if not dry_run:
                yaml.dump(entry, open(ep, "w"),
                         default_flow_style=False, allow_unicode=True, sort_keys=False)
            kept.append((name, f"score={score}"))

        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{total}] {promoted=} {rejected=} {kept=}")

        time.sleep(0.15)

    print(f"\n{'='*50}")
    print(f"✅ Promoted: {len(promoted)}  ❌ Rejected: {len(rejected)}  ⏳ Kept: {len(kept)}")
    for name, score, cat in promoted:
        print(f"   {name} → {cat}/ ({score})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
