#!/usr/bin/env python3
"""Score and promote discovered registry entries using rule-based heuristics.

No LLM dependency — uses GitHub API metrics + README signals.

Scoring axes (0-10 each, weighted → agent_fit_score 0-10):
  installability:     pip/npm/docker? one-command install?
  automation_readiness: CLI? API? MCP? headless?
  extensibility:      plugin system? config file? env vars?
  repo_clarity:       README quality, docs, examples
  sandbox_safety:     docker? permission model? dry-run?
  reproducibility:    lockfiles? versioned? CI?
  maintenance:        recent commits? active issues? contributors?

Promotion rules:
  - score >= 7.0 AND category verified → promote to registry/<category>/
  - score < 4.0 OR clearly wrong category → reject to _rejected/
  - otherwise → keep in _discovered/ pending human review
"""
import json, os, sys, yaml, time, re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError

REGISTRY_ROOT = Path(__file__).resolve().parent.parent / "registry"
DISCOVERED_DIR = REGISTRY_ROOT / "_discovered"
REJECTED_DIR = REGISTRY_ROOT / "_rejected"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

CATEGORY_DIR_MAP = {
    "mcp-server": "mcp-servers",
    "agent": "agents",
    "tool": "tools",
    "eval": "evals",
    "safety": "safety",
    "protocol": "protocols",
    "template": "templates",
    "repo": "repos",
}


def github_api(path):
    url = f"https://api.github.com{path}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "agent-stack-registry/1.0"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=20) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return None


def fetch_repo_info(full_name):
    """Fetch repo metadata + README from GitHub API."""
    meta = github_api(f"/repos/{full_name}")
    if not meta:
        return None, None

    # README
    readme_url = f"https://api.github.com/repos/{full_name}/readme"
    headers = {"Accept": "application/vnd.github.raw+json", "User-Agent": "agent-stack-registry/1.0"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    readme = ""
    try:
        req = Request(readme_url, headers=headers)
        with urlopen(req, timeout=15) as resp:
            readme = resp.read().decode("utf-8", errors="replace")[:5000]
    except Exception:
        readme = ""

    return meta, readme


def is_false_positive(entry, meta, readme):
    """Check if repo is clearly NOT what its category claims."""
    category = entry.get("category", "")
    desc = (meta.get("description") or "").lower()
    topics = meta.get("topics", [])
    name = (meta.get("name") or "").lower()
    full_readme = readme.lower()

    if category == "mcp-server":
        mcp_signals = ("mcp" in desc or "mcp" in name or "mcp" in str(topics).lower()
                       or "mcp" in full_readme[:1000]
                       or "model context protocol" in full_readme[:1000])
        if not mcp_signals:
            return True, "No MCP-related signal in description, topics, or README"

    if category == "agent":
        agent_signals = ("agent" in desc or "agent" in name or "cli" in desc
                         or "coding" in desc or "ai " in desc)
        if not agent_signals:
            return True, "No agent-related signal"

    return False, ""


def compute_score(meta, readme, category):
    """Compute agent_fit_score from observable signals."""
    scores = {}

    # installability (0-10)
    has_pip = "pip install" in readme or "pip3 install" in readme
    has_npm = "npm install" in readme or "npx " in readme
    has_docker = "docker" in readme
    has_binary = "brew install" in readme or "curl" in readme or "go install" in readme
    has_one_command = "pip install" in readme[:500] or "npm install" in readme[:500] or "npx" in readme[:500]
    scores["installability"] = min(10, 4 + (has_pip * 2) + (has_npm * 2) + (has_docker * 1) + (has_binary * 1) + (has_one_command * 2))

    # automation_readiness (0-10)
    has_cli = bool(meta.get("topics")) and "cli" in str(meta["topics"]).lower()
    has_api = "api" in str(meta.get("description", "")).lower()
    has_mcp = category == "mcp-server" or "mcp" in str(meta.get("topics", "")).lower()
    scores["automation_readiness"] = min(10, 3 + (has_cli * 3) + (has_api * 2) + (has_mcp * 4))

    # extensibility (0-10)
    has_config = ("config" in readme.lower() or "configuration" in readme.lower() 
                  or ".env" in readme or "yaml" in readme.lower() or "json" in readme.lower())
    has_plugins = "plugin" in readme.lower() or "extension" in readme.lower()
    scores["extensibility"] = min(10, 3 + (has_config * 3) + (has_plugins * 4))

    # repo_clarity (0-10)
    has_readme = len(readme) > 500
    has_examples = "example" in readme.lower()[:2000] or "usage" in readme.lower()[:2000]
    has_badges = "https://img.shields.io" in readme or "badge" in readme.lower()
    scores["repo_clarity"] = min(10, 2 + (has_readme * 3) + (has_examples * 3) + (has_badges * 2))

    # sandbox_safety (0-10)
    has_docker_safety = "docker" in readme.lower()
    has_dry_run = "dry.run" in readme.lower() or "dryrun" in readme.lower()
    has_permission = "permission" in readme.lower() or "allowlist" in readme.lower()
    scores["sandbox_safety"] = min(10, 2 + (has_docker_safety * 4) + (has_dry_run * 2) + (has_permission * 2))

    # reproducibility (0-10)
    has_lockfile = "lock" in str(meta.get("topics", "")) or "package-lock" in readme or "poetry.lock" in readme
    has_ci = meta.get("has_ci", False) or ".github/workflows" in readme
    scores["reproducibility"] = min(10, 2 + (has_lockfile * 3) + (has_ci * 5))

    # maintenance (0-10)
    pushed = meta.get("pushed_at", "")
    updated_recently = False
    if pushed:
        try:
            pushed_dt = datetime.strptime(pushed[:10], "%Y-%m-%d")
            updated_recently = (datetime.now(timezone.utc) - pushed_dt.replace(tzinfo=timezone.utc)) < timedelta(days=60)
        except Exception:
            pass
    stars = meta.get("stargazers_count", 0)
    open_issues = meta.get("open_issues_count", 999)
    scores["maintenance"] = min(10, 2 + (updated_recently * 3) + (min(stars / 500, 1) * 3) + (max(0, 2 - open_issues / 100)))

    # Overall: simple average
    overall = round(sum(scores.values()) / len(scores), 1)
    return overall, scores


def main():
    dry_run = "--dry-run" in sys.argv

    entries = list(DISCOVERED_DIR.glob("*.yaml"))
    if not entries:
        print("✅ No entries in _discovered/ to score.")
        return 0

    print(f"🔍 Scoring {len(entries)} discovered entries (rule-based, no LLM)...\n")

    promoted, rejected, kept = [], [], []

    for i, entry_path in enumerate(entries):
        entry = yaml.safe_load(open(entry_path))
        name = entry.get("name", entry_path.stem)
        full_name = entry.get("repo", name)
        category = entry.get("category", "unknown")

        print(f"  [{i+1}/{len(entries)}] {name} [{category}]")

        meta, readme = fetch_repo_info(full_name)
        if not meta:
            print(f"     ⚠️  Could not fetch repo info — keeping in _discovered/")
            kept.append((name, "API fetch failed"))
            continue

        # False positive check
        is_fp, fp_reason = is_false_positive(entry, meta, readme)
        if is_fp:
            REJECTED_DIR.mkdir(parents=True, exist_ok=True)
            entry["reject_reason"] = fp_reason
            if not dry_run:
                yaml.dump(entry, open(REJECTED_DIR / entry_path.name, "w"),
                         default_flow_style=False, allow_unicode=True, sort_keys=False)
                entry_path.unlink()
            print(f"     ❌ REJECTED (false positive): {fp_reason}")
            rejected.append((name, fp_reason))
            continue

        # Score
        score, breakdown = compute_score(meta, readme, category)
        entry["agent_fit_score"] = score
        entry["score_breakdown"] = breakdown
        entry["last_verified"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        entry["stars"] = meta.get("stargazers_count", 0)
        entry["notes"] = [f"Auto-scored {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"]
        entry["evidence"] = [meta.get("html_url", "")]

        # Decision
        if score >= 7.0:
            cat_dir = CATEGORY_DIR_MAP.get(category, "tools")
            target_dir = REGISTRY_ROOT / cat_dir
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / entry_path.name
            if not dry_run:
                yaml.dump(entry, open(target_path, "w"),
                         default_flow_style=False, allow_unicode=True, sort_keys=False)
                entry_path.unlink()
            print(f"     ✅ PROMOTED → {cat_dir}/ (score: {score})")
            promoted.append((name, score, cat_dir))
        else:
            # Update entry but keep in _discovered
            if not dry_run:
                yaml.dump(entry, open(entry_path, "w"),
                         default_flow_style=False, allow_unicode=True, sort_keys=False)
            print(f"     ⏳ KEPT in _discovered/ (score: {score} — needs review)")
            kept.append((name, f"score={score}"))

        time.sleep(0.3)

    # Summary
    print(f"\n{'='*50}")
    print(f"✅ Promoted: {len(promoted)}")
    for name, score, cat in promoted:
        print(f"   {name} → {cat}/ (score: {score})")
    print(f"⏳ Kept for review: {len(kept)}")
    print(f"❌ Rejected: {len(rejected)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
