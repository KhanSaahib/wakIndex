# AgentScope

> Static permission inventory and policy gates for AI agents, MCP servers, skills, and GitHub Actions.

## Description

AgentScope treats agent configuration like a production workload definition. It creates a readable permission manifest, checks it against team policy, and can block a pull request before an over-privileged agent runs. Analysis is deterministic, local, and requires no LLM, API key, or network access.

## Quick start

```bash
python -m pip install .
agentscope init
agentscope scan . --output agentscope-manifest.json
agentscope check . --policy agentscope-policy.toml
agentscope ui --policy agentscope-policy.toml
```

The UI opens at `http://127.0.0.1:8765` and provides Allow/Deny radio controls for each permission. It does not contact an external service.

## What it finds

- MCP process commands, arguments, remote URLs, and inherited environment variable names
- Claude-style allowed/denied tools and unsafe unrestricted modes
- skill instructions that declare tools or risky shell/network behavior
- GitHub Actions token permissions, including write and broad scopes
- filesystem paths that appear to escape the repository

AgentScope never executes discovered commands and never emits environment variable values.
Use `.agentscopeignore` with repository-relative glob patterns for known fixtures or generated files.

## Policy

`agentscope init` creates a conservative TOML policy:

```toml
# AgentScope policy: exact IDs and "category.*" wildcards are supported.
default = "deny"
allow = ["filesystem.read"]
deny = ["agent.unrestricted", "process.shell", "filesystem.outside_workspace"]
```

`agentscope check` exits `0` when compliant and `2` on policy violations. Use `--format sarif --output agentscope.sarif` for code-scanning integrations.

## GitHub Action

```yaml
- uses: your-org/agentscope@v1
  with:
    path: .
    policy: agentscope-policy.toml
```

The included Docker action runs consistently on Linux GitHub runners. A ready-to-copy workflow lives in `.github/workflows/agentscope.yml`.

## Docker

```bash
docker build -t agentscope .
docker run --rm -v "$PWD:/workspace" agentscope check /workspace --policy /workspace/agentscope-policy.toml
docker build --target test -t agentscope-test .
docker run --rm agentscope-test
```

## Development

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
```

See `AGENTS.md` for the durable maintainer handoff and `docs/architecture.md` for scope and design.

## Security references

The permission model is informed by the OWASP AI Security Verification Standard, OWASP agentic-security work, the Model Context Protocol authorization specification, and GitHub's container-action guidance.

## License

Apache-2.0. See `LICENSE`.
