# Real-world environment auditing

## Description

This design defines the first wakindex expansion aimed at useful personal endpoint audits and
enforceable corporate policy gates while preserving local-only, deterministic analysis.

## Outcome

wakindex will answer two practical questions:

1. Which permissions can the agent configuration in this workspace and the current user's known
   agent configuration files expose?
2. Which exact hosts, server identities, sources, risk levels, and inherited secret names are
   approved by policy?

The milestone adds environment discovery and scoped policy rules. It does not contact vendors,
start MCP servers, resolve cloud IAM, read credential values, or scan arbitrary home-directory
content.

## User workflows

### Personal endpoint

```bash
wakindex audit ~/work/project
wakindex check ~/work/project --include-user --policy wakindex-policy.toml
```

`audit` examines the workspace and a fixed allowlist of user configuration paths for Codex,
Claude, Cursor, Gemini CLI, and VS Code. Sources are reported as stable labels such as
`user/codex/config.toml`; absolute home-directory paths are not emitted.

### Corporate endpoint or CI

```bash
wakindex audit /workspace --home /home/employee --output endpoint-manifest.json
wakindex check /workspace --include-user --home /home/employee \
  --policy corporate-wakindex-policy.toml --format sarif --output wakindex.sarif
```

An endpoint-management system can provide an explicit profile root with `--home`. Repository-only
CI remains the default for `scan` and `check`, so existing workflows do not begin reading runner
profiles unexpectedly.

## Discovery boundary

User auditing is explicit and checks only known files:

| Provider | User configuration |
| --- | --- |
| Codex | `~/.codex/config.toml` |
| Claude Code | `~/.claude/settings.json`, `~/.claude.json` |
| Cursor | `~/.cursor/mcp.json` |
| Gemini CLI | `~/.gemini/settings.json` |
| VS Code | platform-specific `Code/User/mcp.json` |
| Claude Desktop | platform-specific `claude_desktop_config.json` |

Missing files are ignored. Symlinks are not followed. Project discovery continues to use the
repository scanner and `.wakindexignore`.

## Normalized finding metadata

Every newly scanned finding includes:

- `provider`: the configuration ecosystem, such as `codex` or `cursor`;
- `scope`: `workspace` or `user`;
- capability-specific selectors such as `server`, `command`, `host`,
  `environment_variable`, or `github_scope`.

Metadata never contains credential values. User-scope findings replace the audited home prefix
with `~` in evidence and string metadata.

## Scoped policy rules

Legacy `allow` and `deny` permission patterns remain supported. Policies may additionally contain
rules:

```toml
version = 1
default = "deny"
allow = ["filesystem.read"]
deny = ["agent.unrestricted", "agent.auto_approve", "secrets.embedded"]

[[rules]]
id = "approved-corporate-mcp"
effect = "allow"
permission = "network.access"
resource = "corporate-tools"
source = "user/codex/config.toml"
reason = "Company-managed MCP gateway"
metadata = { host = "mcp.example.internal", provider = "codex" }
```

Rule fields use case-sensitive shell-style wildcards. A rule matches only when its permission,
resource, source, risk, and every metadata selector match. Evaluation order is:

1. matching legacy or scoped deny;
2. matching legacy or scoped allow;
3. policy default.

This preserves deny precedence while allowing companies to approve one host or server without
implicitly approving all network or process access.

## New security signals

- `agent.auto_approve`: a server or agent configuration bypasses normal confirmation.
- `secrets.embedded`: a sensitive environment or HTTP-header field contains literal credential
  material. Only the field name is reported.
- Claude command hooks are inventoried as process execution without running the hook.
- Codex workspace write modes, additional writable roots, and sandbox network grants are explicit
  filesystem or network findings.
- Codex `danger-full-access` or equivalent configuration remains `agent.unrestricted`.
- Codex, JSON MCP, Gemini, Cursor, Claude, and VS Code configurations share normalized MCP
  extraction for commands, endpoints, inherited environment-variable names, and escaping paths.

## Compatibility

- Existing repository scans, manifest schema `1.0`, policy arrays, CLI defaults, and exit codes
  remain valid.
- `audit` and `check --include-user` are opt-in additions.
- Policy files without `version` or `rules` load as version 1 legacy policies.
- The browser editor preserves scoped rules and edits only the legacy permission-wide choices.

## Acceptance criteria

1. A synthetic user profile covering all supported providers produces deterministic findings
   without exposing its absolute home path or embedded fixture secret.
2. Codex TOML commands, endpoints, inherited secret names, sandbox mode, and approval behavior are
   detected without executing anything.
3. A scoped allow rule approves only its matching host/server/source; a scoped deny always wins.
4. Legacy policies and existing tests remain compatible.
5. Local, wheel, Docker, and GitHub checks pass without an LLM, API key, or network at runtime.
