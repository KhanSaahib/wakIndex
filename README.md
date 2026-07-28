# wakindex

> Static permission inventory and policy gates for AI agents, MCP servers, skills, and GitHub
> Actions.

## Overview

wakindex treats agent configuration like a production workload definition. Before an agent runs,
it inventories process execution, filesystem reach, remote endpoints, inherited secret names, and
GitHub token permissions, then checks that inventory against a repository-owned policy.

Analysis is deterministic and local. It requires no LLM, API key, cloud account, or network
connection, and discovered commands are never executed.

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
wakindex check . --policy wakindex-policy.toml
wakindex ui . --policy wakindex-policy.toml
```

`wakindex init` creates a conservative starter policy. The UI listens on
`http://127.0.0.1:8765`, provides explicit Allow/Deny controls, and does not contact an external
service.

## Commands

| Command | Purpose |
| --- | --- |
| `wakindex scan [PATH]` | Produce a deterministic permission inventory |
| `wakindex check [PATH]` | Enforce a TOML policy; returns `2` for violations |
| `wakindex init` | Create a starter policy without overwriting an existing file |
| `wakindex ui [PATH]` | Edit discovered permissions using the loopback-only browser UI |

Use `--format text` for humans, JSON for manifests, and SARIF for code scanning. JSON and SARIF
remain clean on stdout.

## What is detected

- MCP commands, arguments, remote URLs, and inherited environment-variable names;
- Claude-style allowed tools and unrestricted permission modes;
- skill instructions declaring shell or network behavior;
- GitHub Actions token permissions, including broad write scopes;
- relative paths that appear to escape the repository.

wakindex records secret names only and never emits environment-variable values. Use
`.wakindexignore` with repository-relative globs for intentional fixtures or generated content.

## Policy

```toml
# Description: wakindex permission policy; deny rules take precedence.
default = "deny"
allow = ["filesystem.read"]
deny = ["agent.unrestricted", "process.shell", "filesystem.outside_workspace"]
```

Rules accept exact permission IDs and wildcards such as `filesystem.*`. Evaluation order is
explicit deny, explicit allow, then the default.

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
- [RELEASE.md](RELEASE.md) defines SemVer and tag-driven GitHub releases.

## References

The permission model is informed by the
[OWASP AI Security Verification Standard](https://owasp.org/www-project-artificial-intelligence-security-verification-standard-aisvs-docs/),
the [OWASP agentic-security landscape](https://genai.owasp.org/resource/ai-security-solutions-landscape-for-agentic-ai-q2-2026/),
the [Model Context Protocol authorization specification](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization),
and [GitHub container-action guidance](https://docs.github.com/en/actions/concepts/workflows-and-actions/custom-actions).

## License

Apache-2.0. See [LICENSE](LICENSE).
