# wakindex

> Static permission inventory and scoped policy gates for AI agents, MCP servers, skills, user
> environments, and GitHub Actions.

## Overview

wakindex treats agent configuration like a production workload definition. Before an agent runs,
it inventories process execution, filesystem reach, remote endpoints, inherited secret names,
approval bypasses, embedded credential fields, and GitHub token permissions, then checks that
inventory against an explicit policy.

Analysis is deterministic and local. It requires no LLM, API key, cloud account, or network
connection. Discovered commands are never executed and credential values are never emitted.

## Status

wakindex is pre-1.0 software. Manifest compatibility is maintained within a package major version;
minor releases before `1.0.0` may include documented compatibility changes. See
[RELEASE.md](RELEASE.md) for the full versioning policy.

## Installation

Python 3.11 or newer is required.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install .
```

For isolated command installation, `pipx install .` is also supported.

## Quick start

```bash
wakindex init
wakindex scan . --output wakindex-manifest.json
wakindex audit . --output endpoint-manifest.json
wakindex check . --policy wakindex-policy.toml
wakindex check . --include-user --policy wakindex-policy.toml
wakindex ui . --policy wakindex-policy.toml
```

`scan` stays repository-only. `audit` combines the repository with a fixed allowlist of known
current-user agent configuration files. `wakindex init` creates a conservative starter policy.
The UI listens on
`http://127.0.0.1:8765`, provides explicit Allow/Deny controls, and does not contact an external
service.

## Commands

| Command | Purpose |
| --- | --- |
| `wakindex scan [PATH]` | Produce a deterministic permission inventory |
| `wakindex audit [PATH]` | Inventory the workspace and known user agent configuration |
| `wakindex check [PATH]` | Enforce a TOML policy; returns `2` for violations |
| `wakindex init` | Create a starter policy without overwriting an existing file |
| `wakindex ui [PATH]` | Edit discovered permissions using the loopback-only browser UI |

Use `--format text` for humans, JSON for manifests, and SARIF for code scanning. JSON and SARIF
remain clean on stdout.

## What is detected

- MCP commands, arguments, remote URLs, and inherited environment-variable names;
- Codex `config.toml`, Claude, Cursor, Gemini, VS Code, and generic MCP configuration;
- Claude-style allowed tools, unrestricted sandboxes, and auto-approval modes;
- Claude command hooks and Codex network or additional writable-root grants;
- sensitive environment or HTTP-header fields containing literal credential material, without
  recording the value;
- skill instructions declaring shell or network behavior;
- GitHub Actions token permissions, including broad write scopes;
- relative paths that appear to escape the repository.

wakindex records secret and credential field names only and never emits their values. Use
`.wakindexignore` with repository-relative globs for intentional fixtures or generated content.

## Personal environment audit

`audit` does not crawl a home directory. It checks only documented paths for Codex, Claude Code,
Claude Desktop, Cursor, Gemini CLI, and VS Code. Missing files and symlinks are skipped, and output
uses labels such as `user/codex/config.toml` instead of absolute profile paths.

```bash
wakindex audit ~/work/project
wakindex audit ~/work/project --home /profiles/alice --format text
```

`--home` makes endpoint-management and container runs deterministic. Repository-only behavior
remains the default for `scan`, `check`, and the GitHub Action.

## Scoped policy

```toml
# Description: wakindex permission policy; scoped deny rules take precedence.
version = 1
default = "deny"
allow = ["filesystem.read"]
deny = [
  "agent.unrestricted",
  "agent.auto_approve",
  "process.shell",
  "filesystem.outside_workspace",
  "secrets.embedded",
]

[[rules]]
id = "approved-corporate-mcp"
effect = "allow"
permission = "network.access"
resource = "corporate-tools"
source = "user/codex/config.toml"
reason = "Company-managed gateway"
metadata = { host = "mcp.example.internal", provider = "codex" }
```

Legacy arrays accept permission wildcards such as `filesystem.*`. Named rules additionally match
resource/server names, source, risk, and metadata such as host, command, provider, or inherited
variable name. Every deny takes precedence over every allow.

- [docs/policy.md](docs/policy.md) is the complete schema and matching reference.
- [examples/personal-policy.toml](examples/personal-policy.toml) is a conservative individual
  starting point.
- [examples/corporate-policy.toml](examples/corporate-policy.toml) demonstrates a narrow managed
  gateway approval.

## Corporate rollout

For a managed developer endpoint:

```bash
wakindex audit /workspace --home /home/employee --output endpoint-manifest.json
wakindex check /workspace --include-user --home /home/employee \
  --policy corporate-wakindex-policy.toml --format sarif --output wakindex.sarif
```

For repository CI, keep the GitHub Action repository-scoped and store the reviewed policy beside
the code. The manifest is stable for pull-request diffs and rule IDs provide auditable policy
justifications.

## GitHub Action

Pin the action to an immutable published version tag:

```yaml
- uses: KhanSaahib/wakindex@v0.1.0
  with:
    path: .
    policy: wakindex-policy.toml
    output: wakindex.sarif
```

The included Docker action runs on Linux GitHub runners. `.github/workflows/wakindex.yml` shows a
SARIF upload integration.

## Docker

```bash
docker build -t wakindex .
docker run --rm -v "$PWD:/workspace" \
  wakindex check /workspace --policy /workspace/wakindex-policy.toml
```

Audit a mounted profile read-only:

```bash
docker run --rm \
  -v "$PWD:/workspace:ro" \
  -v "$HOME:/audit-home:ro" \
  wakindex audit /workspace --home /audit-home
```

Run the containerized quality gate:

```bash
docker build --target test -t wakindex-test .
docker run --rm wakindex-test
```

## Security boundaries

wakindex is a static reviewer, not a runtime sandbox. It does not inspect remote MCP
implementations, resolve live IAM policies, or prove what a tool does after execution. See
[docs/architecture.md](docs/architecture.md) for trust boundaries and
[docs/security.md](docs/security.md) for vulnerability reporting.

## Development and releases

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
```

- [CONTRIBUTING.md](CONTRIBUTING.md) defines the contribution quality bar.
- [CHANGELOG.md](CHANGELOG.md) records user-visible changes.
- [docs/real-world-audit.md](docs/real-world-audit.md) records the endpoint-audit design.
- [RELEASE.md](RELEASE.md) defines SemVer and tag-driven GitHub releases.

## References

The permission model is informed by the
[OWASP AI Security Verification Standard](https://owasp.org/www-project-artificial-intelligence-security-verification-standard-aisvs-docs/),
the [OWASP agentic-security landscape](https://genai.owasp.org/resource/ai-security-solutions-landscape-for-agentic-ai-q2-2026/),
the [Model Context Protocol authorization specification](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization),
[Codex MCP configuration](https://developers.openai.com/codex/mcp/),
[Claude Code settings](https://code.claude.com/docs/en/settings),
[Cursor MCP configuration](https://docs.cursor.com/context/model-context-protocol),
[Gemini CLI MCP configuration](https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/mcp-server.md),
[VS Code MCP configuration](https://code.visualstudio.com/docs/agents/reference/mcp-configuration),
and [GitHub container-action guidance](https://docs.github.com/en/actions/concepts/workflows-and-actions/custom-actions).

## License

Apache-2.0. See [LICENSE](LICENSE).
