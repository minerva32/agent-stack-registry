# Contributing to Agent Stack Registry

Thanks for contributing! This registry is community-driven and strictly curated.

---

## ✅ What can be submitted

- CLI-based coding agents
- MCP servers and protocols
- Agent-friendly repositories
- Eval/benchmark harnesses
- Safety and sandbox patterns
- Automation templates

## ❌ What will be rejected

- Blog posts or tutorials (no primary source)
- Abandoned repositories (no commits in 12+ months)
- Generic AI tools without clear agent use case
- Marketing pages or product landing pages
- Entries without evidence or score justification

---

## 📋 How to submit

1. Fork this repository
2. Copy `examples/entry-template.yaml` to the appropriate `registry/<category>/` directory
3. Fill in all required fields (name, category, homepage, license, status, last_verified, agent_fit_score, tags)
4. **Provide `score_breakdown`** — each of the 7 criteria scored 0–10 with brief justification in `notes`
5. **Provide `evidence`** — at least 2 sources (official repo, docs, benchmark result, community usage)
6. Run `python scripts/validate_registry.py` locally to confirm your entry passes
7. Open a PR with title: `[add] <category>/<name>`

---

## 🔢 Agent Fit Score Criteria

All 7 criteria must be scored to prevent gaming:

| Criterion | Description |
|-----------|-------------|
| Installability | How easy is it to install and run? |
| Automation Readiness | Does it have consistent CLI/API for scripting? |
| Extensibility | Does it support plugins, MCP, or hooks? |
| Repo Clarity | Is the README and docs clear for agents to navigate? |
| Sandbox Safety | Does it support safe/isolated execution? |
| Reproducibility | Can the dev environment be reproduced consistently? |
| Maintenance | Is it actively maintained (commits, releases, issues)? |

**Score = average of 7 criteria (0–10)**

PRs without score breakdown or evidence will be returned for revision.

---

## 🔄 Updating entries

To update `last_verified`, status, or score:
- Open a PR with title: `[update] <category>/<name>`
- Explain what changed and provide updated evidence

---

## 💬 Questions

Open an issue or start a discussion. We're friendly!
