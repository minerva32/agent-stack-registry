# Agent Stack Registry

> **MCP Servers, AI Agents, and Developer Tools — scored, structured, auto-discovered.**

[![Validate Registry](https://github.com/minerva32/agent-stack-registry/actions/workflows/validate.yml/badge.svg)](https://github.com/minerva32/agent-stack-registry/actions)

---

## 🔌 MCP Servers

The MCP ecosystem is exploding. We track quality MCP server implementations with verified scores.

| Name | Stars | License | Score |
|------|-------|---------|-------|
| [playwright-mcp](https://github.com/microsoft/playwright-mcp) | ⭐33.9k | Apache-2.0 | 9.0 |
| [fastmcp](https://github.com/PrefectHQ/fastmcp) | ⭐25.7k | Apache-2.0 | 8.8 |
| [Figma-Context-MCP](https://github.com/GLips/Figma-Context-MCP) | ⭐15.1k | MIT | 8.5 |
| [mcp-chrome](https://github.com/hangwin/mcp-chrome) | ⭐11.9k | MIT | 8.3 |
| [mcp-use](https://github.com/mcp-use/mcp-use) | ⭐10.1k | MIT | 8.2 |
| [aws-labs-mcp](https://github.com/awslabs/mcp) | ⭐9.3k | Apache-2.0 | 8.0 |
| [mcp-toolbox](https://github.com/googleapis/mcp-toolbox) | ⭐15.6k | Apache-2.0 | 8.4 |
| [github MCP](https://github.com/github/github-mcp-server) | official | MIT | 8.4 |
| [filesystem MCP](https://github.com/modelcontextprotocol/servers) | official | MIT | 8.5 |
| [brave-search MCP](https://github.com/modelcontextprotocol/servers) | official | MIT | 8.0 |

[View all MCP servers →](registry/mcp-servers/)

---

## 🧠 AI Coding Agents

| Name | MCP | Score |
|------|-----|-------|
| Claude Code | ✅ | 9.2 |
| Gemini CLI | ✅ | 8.7 |
| OpenClaw | ✅ | 8.9 |
| Codex CLI | ✅ | 8.5 |
| Cline | ✅ | 8.3 |

[View all agents →](registry/agents/)

---

## 🛡 Safety & Sandbox

Production agent safety patterns — allowlists, dry-run, sandbox isolation.

[View safety patterns →](registry/safety/)

---

## 🧪 Benchmarks

SWE-bench, HumanEval, agent-bench — scored by relevance to coding agents.

[View benchmarks →](registry/evals/)

---

## 🤖 Auto-Discovery

This registry is **self-updating**. A weekly GitHub Actions workflow (or Hermes cron job) scans GitHub for new MCP servers and AI agent tools, generates scored YAML entries, and opens a PR for review.

New entries land in `registry/_discovered/` → human review → promoted to `registry/<category>/`.

**Want to add something?** [Open an issue](https://github.com/minerva32/agent-stack-registry/issues/new) or submit a PR.

---

## 📁 Structure

```
registry/
├── mcp-servers/    # MCP server implementations (primary focus)
├── agents/         # CLI-based coding agents
├── tools/          # Supporting tools
├── protocols/      # MCP and interfaces
├── templates/      # Reusable project templates
├── safety/         # Sandbox and safety patterns
├── evals/          # Benchmarks
└── _discovered/    # Auto-discovered, pending review
```

---

## 📜 License

MIT
