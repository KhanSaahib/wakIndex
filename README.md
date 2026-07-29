# wakindex

> Account-aware permission inventory and scoped policy gates for AI agents, configured models,
> MCP servers, skills, user environments, and GitHub Actions.

## Overview

wakindex treats agent configuration like a production workload definition. Before an agent runs,
it inventories process execution, filesystem reach, remote endpoints, inherited secret names,
approval bypasses, embedded credential fields, and GitHub token permissions, then checks that
inventory against an explicit policy. Its identity inventory connects those permissions to the
human, service, or shared account that owns each agent configuration and the model/provider
settings visible before runtime.

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
wakindex inventory . --output identity-access.json
wakindex dashboard .
```

`scan` stays repository-only. `audit` combines the repository with a fixed allowlist of known
current-user agent configuration files. `wakindex init` creates a conservative starter policy.
The UI listens on
`http://127.0.0.1:8765`, provides explicit Allow/Deny controls, and does not contact an external
service. The read-only enterprise dashboard listens separately on `http://127.0.0.1:8766`.

## Commands

| Command | Purpose |
| --- | --- |
| `wakindex scan [PATH]` | Produce a deterministic permission inventory |
| `wakindex audit [PATH]` | Inventory the workspace and known user agent configuration |
| `wakindex check [PATH]` | Enforce a TOML policy; returns `2` for violations |
| `wakindex inventory [PATH]` | Map accounts to agent surfaces, configured models, and access |
| `wakindex dashboard [PATH]` | Open the loopback-only identity and access dashboard |
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

## Identity and access inventory

Run `inventory` without an account catalog for the current operating-system account:

```bash
wakindex inventory ~/work/project --format text
wakindex dashboard ~/work/project
```

For multiple managed accounts, provide a trusted catalog:

```bash
wakindex inventory /workspace \
  --accounts enterprise-accounts.toml \
  --workspace-id payments-api \
  --policy corporate-wakindex-policy.toml \
  --output identity-access.json

wakindex dashboard /workspace \
  --accounts enterprise-accounts.toml \
  --workspace-id payments-api \
  --policy corporate-wakindex-policy.toml
```

The separate `identity-1.0` output contains:

- operator-controlled human, service, or shared account identity;
- department, endpoint, environment, and tags;
- provider-account aliases, such as an approved OpenAI organization or AWS Bedrock profile;
- one deterministic agent instance per account and configuration source;
- endpoint and workspace context suitable for fleet aggregation;
- configured primary/fallback models, model provider, and safe authentication context;
- every static access finding with its account, agent, risk, and policy decision;
- explicit coverage counts for runtime-selected models and unmapped provider accounts.

Account catalogs control exactly which profile roots are inspected. Profile paths are never
serialized. wakindex does not inspect keychains, login sessions, browser profiles, credential
files, or chat history. A model shown in the dashboard is a static configured value and may be
overridden at runtime.

- [docs/identity-access.md](docs/identity-access.md) defines the schema, trust model, dashboard,
  and limitations.
- [examples/enterprise-accounts.toml](examples/enterprise-accounts.toml) is a copyable catalog
  template.

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

For endpoint or fleet collection, export `identity-access.json` and send it through the
organization's existing authenticated EDR, SIEM, or asset-inventory channel. The bundled
dashboard intentionally remains loopback-only and does not attempt to become an unauthenticated
network service.

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

Run the account-aware inventory in a container by making account-catalog home paths match the
read-only profile mounts:

```bash
docker run --rm \
  -v "$PWD:/workspace:ro" \
  -v "/profiles:/profiles:ro" \
  wakindex inventory /workspace \
    --accounts /workspace/enterprise-accounts.toml \
    --policy /workspace/wakindex-policy.toml
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
- [docs/identity-access.md](docs/identity-access.md) records the identity inventory and dashboard
  contract.
- [RELEASE.md](RELEASE.md) defines SemVer and tag-driven GitHub releases.

## References

The permission model is informed by the
[OWASP AI Security Verification Standard](https://owasp.org/www-project-artificial-intelligence-security-verification-standard-aisvs-docs/),
the [OWASP agentic-security landscape](https://genai.owasp.org/resource/ai-security-solutions-landscape-for-agentic-ai-q2-2026/),
the [Model Context Protocol authorization specification](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization),
[NIST NCCoE software and AI agent identity concept paper](https://www.nccoe.nist.gov/sites/default/files/2026-02/accelerating-the-adoption-of-software-and-ai-agent-identity-and-authorization-concept-paper.pdf),
[Codex MCP configuration](https://developers.openai.com/codex/mcp/),
[Codex configuration reference](https://developers.openai.com/codex/config-reference/),
[Claude Code settings](https://code.claude.com/docs/en/settings),
[Claude Code model configuration](https://code.claude.com/docs/en/model-config),
[Cursor MCP configuration](https://docs.cursor.com/context/model-context-protocol),
[Gemini CLI MCP configuration](https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/mcp-server.md),
[Gemini CLI configuration](https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/configuration.md),
[VS Code MCP configuration](https://code.visualstudio.com/docs/agents/reference/mcp-configuration),
and [GitHub container-action guidance](https://docs.github.com/en/actions/concepts/workflows-and-actions/custom-actions).

## License

Apache-2.0. See [LICENSE](LICENSE).
