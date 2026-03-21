# Agent Stack Registry

> A curated registry of tools, repositories, protocols, and patterns for AI coding agents.

**Not just a list — a structured, scoreable, executable ecosystem registry.**

[![Validate Registry](https://github.com/minerva32/agent-stack-registry/actions/workflows/validate.yml/badge.svg)](https://github.com/minerva32/agent-stack-registry/actions)
[![Link Check](https://github.com/minerva32/agent-stack-registry/actions/workflows/link-check.yml/badge.svg)](https://github.com/minerva32/agent-stack-registry/actions)

---

## 🔥 Featured

| Name | Type | MCP | Score | Status |
|------|------|-----|-------|--------|
| [Claude Code](registry/agents/claude-code.yaml) | Agent | ✅ | 9.2 | active |
| [Gemini CLI](registry/agents/gemini-cli.yaml) | Agent | ✅ | 8.7 | active |
| [OpenClaw](registry/agents/openclaw.yaml) | Agent | ✅ | 8.9 | active |
| [Codex CLI](registry/agents/codex-cli.yaml) | Agent | ✅ | 8.5 | active |
| [Cline](registry/agents/cline.yaml) | Agent | ✅ | 8.3 | active |

---

## 🧠 Agents

| Name | OSS | MCP | Score | Status |
|------|-----|-----|-------|--------|
| Claude Code | ✅ | ✅ | 9.2 | active |
| Gemini CLI | ✅ | ✅ | 8.7 | active |
| OpenClaw | ✅ | ✅ | 8.9 | active |
| Codex CLI | ✅ | ✅ | 8.5 | active |
| Cline | ✅ | ✅ | 8.3 | active |

---

## 🔌 MCP / Protocols

| Name | Type | Score | Status |
|------|------|-------|--------|
| MCP (Model Context Protocol) | protocol | 9.0 | active |
| filesystem MCP | mcp-server | 8.5 | active |
| github MCP | mcp-server | 8.4 | active |
| brave-search MCP | mcp-server | 8.0 | active |
| sqlite MCP | mcp-server | 7.9 | active |

---

## 📦 Templates

| Name | Description | Score |
|------|-------------|-------|
| agent-repo-template | Minimal repo for agent tasks | 8.5 |
| mcp-server-template | Boilerplate MCP server | 8.3 |
| eval-harness-template | Task eval scaffold | 8.0 |
| pr-automation-template | Auto PR + CI template | 8.1 |

---

## 🛡 Safety / Sandbox Patterns

| Name | Description | Score |
|------|-------------|-------|
| command-allowlist | Allowlist-based shell execution | 9.0 |
| dry-run-pattern | Simulate before execute | 8.8 |
| secrets-handling | Env-based secrets isolation | 8.7 |
| containerized-execution | Docker/sandbox isolation | 8.5 |

---

## 🧪 Evals / Benchmarks

| Name | Description | Score |
|------|-------------|-------|
| SWE-bench | Software engineering tasks | 9.2 |
| HumanEval | Code generation benchmark | 8.5 |
| agent-bench | Multi-step agent tasks | 8.3 |
| GitBug-Java | Real GitHub bug fixes | 8.0 |

---

## 📁 Registry Structure

```
registry/
├─ agents/         # CLI-based coding agents
├─ tools/          # Supporting tools
├─ protocols/      # MCP and interfaces
├─ mcp-servers/    # MCP server implementations
├─ templates/      # Reusable project templates
├─ repos/          # Agent-friendly repositories
├─ evals/          # Benchmarks and eval harnesses
└─ safety/         # Sandbox and safety patterns
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Quick rules:**
- Include official source link
- Provide real usage evidence
- YAML schema must pass validation
- Explain agent use value

---

## 📋 Schema

Each entry follows [schemas/entry.schema.json](schemas/entry.schema.json).
See [examples/](examples/) for templates.

---

## 📜 License

MIT
