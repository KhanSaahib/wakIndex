# wakindex

> Review permissions for AI agents, MCP servers, skills, and GitHub Actions before they run.

## Description

wakindex treats agent configuration like a production workload definition. It statically inventories process execution, filesystem reach, remote access, inherited credential names, agent bypass modes, and GitHub token scopes. The resulting manifest can be reviewed by a person or enforced by policy in a pull request.

Core analysis is deterministic and local. It does not need an LLM, API key, cloud account, or network connection, and it never launches discovered tools.

## Install

wakindex requires Python 3.11 or newer:

```bash
git clone https://github.com/KhanSaahib/AgentScope.git
cd AgentScope
python -m pip install .
wakindex --version
```

For isolated installation from a checkout, `pipx install .` is also supported.

## Quick start

```bash
wakindex init
wakindex scan . --format text
wakindex scan . --output wakindex-manifest.json
wakindex check . --policy wakindex-policy.toml
wakindex ui . --policy wakindex-policy.toml
```

`scan` inventories declared capabilities. `check` applies policy and exits `0` when compliant, `2` for policy violations, and `1` for operational errors.

The optional policy editor listens only on `http://127.0.0.1:8765`. It presents explicit Allow/Deny radio controls and uses no external scripts, fonts, services, or credentials.

## What it detects

- MCP process commands, arguments, remote endpoints, and environment references;
- Claude-style allowed tools and permission-bypass modes;
- skill declarations with shell, network, or credential exposure;
- GitHub Actions token permissions, including write and broad scopes;
- paths that appear to escape the repository workspace.

Secret findings contain environment-variable names only, never their values. URLs and commands are recorded as evidence but are not opened or executed.

Supported configuration currently includes Claude settings, VS Code and generic MCP JSON, `SKILL.md`, and GitHub workflow YAML. Use `.wakindexignore` with repository-relative glob patterns to exclude known fixtures or generated content.

## Permission manifest

JSON output is stable and designed for code review:

```json
{
  "schema_version": "1.0",
  "root": ".",
  "summary": {
    "high": 1,
    "low": 0,
    "medium": 1,
    "total": 2
  },
  "findings": [
    {
      "permission": "process.execute",
      "resource": "docs",
      "source": ".vscode/mcp.json",
      "evidence": "command: python",
      "risk": "medium",
      "metadata": {
        "command": "python"
      }
    }
  ]
}
```

Each finding explains the permission, affected resource, evidence source, risk, and structured metadata.

## Policy

`wakindex init` creates a conservative TOML policy. Exact IDs and category wildcards are supported:

```toml
# Deny rules take precedence over allow rules.
default = "deny"
allow = ["filesystem.read", "process.execute"]
deny = [
  "agent.unrestricted",
  "filesystem.outside_workspace",
  "process.shell",
]
```

Evaluation order is explicit deny, explicit allow, then default. A deny-default policy makes newly detected capabilities visible instead of silently accepting them.

For code-scanning integrations:

```bash
wakindex check . \
  --policy wakindex-policy.toml \
  --format sarif \
  --output wakindex.sarif
```

## GitHub Action

Add the policy file to your repository, then pin a full release tag:

```yaml
name: Agent permission review
on:
  pull_request:
permissions:
  contents: read
  security-events: write
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # Replace vX.Y.Z with a published release.
      - uses: KhanSaahib/AgentScope@vX.Y.Z
        with:
          path: .
          policy: wakindex-policy.toml
          output: wakindex.sarif
```

The Docker Action runs on Linux GitHub runners. Pin a full version or commit SHA in security-sensitive repositories.

## Docker

```bash
docker build -t wakindex .
docker run --rm -v "$PWD:/workspace" \
  wakindex check /workspace --policy /workspace/wakindex-policy.toml
```

Run the complete containerized test target with:

```bash
docker build --target test -t wakindex-test .
docker run --rm wakindex-test
```

## Security model and limitations

wakindex statically reviews declarations. It cannot prove what a remote MCP server does, expand live cloud IAM roles, or replace runtime isolation. Treat its manifest as a preflight permission review and combine it with sandboxing, short-lived credentials, least privilege, and runtime monitoring.

See [architecture](docs/architecture.md) for trust boundaries and extension rules, and [security policy](docs/security.md) for vulnerability reporting.

## Development and releases

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
docker build --target test -t wakindex-test .
```

Contributions should include sanitized fixtures and behavior-focused tests. See [CONTRIBUTING.md](CONTRIBUTING.md).

wakindex follows Semantic Versioning and publishes immutable tag-driven GitHub releases with Python artifacts and checksums. See [RELEASE.md](RELEASE.md) and [CHANGELOG.md](CHANGELOG.md).

## Security references

The permission model is informed by the OWASP AI Security Verification Standard, OWASP agentic-security work, the Model Context Protocol authorization specification, and GitHub's container-action guidance.

## License

Apache-2.0. See [LICENSE](LICENSE).
