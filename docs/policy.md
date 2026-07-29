# wakindex policy reference

## Description

This document defines the version 1 TOML policy schema, matching semantics, compatibility rules,
and practical examples for personal and organization-managed environments.

## Policy structure

```toml
version = 1
default = "deny"
allow = ["filesystem.read"]
deny = ["agent.unrestricted", "agent.auto_approve", "secrets.embedded"]
```

- `version` is optional for legacy files and defaults to `1`.
- `default` is `allow` or `deny`.
- `allow` and `deny` contain case-sensitive shell-style permission patterns.
- `rules` are optional named, scoped allow or deny decisions.

Legacy arrays are useful for organization-wide invariants. Scoped rules are appropriate when one
specific command, MCP server, source, or network host is approved.

## Scoped rules

```toml
[[rules]]
id = "approved-corporate-mcp"
effect = "allow"
permission = "network.access"
resource = "corporate-tools"
source = "user/codex/config.toml"
risk = "medium"
reason = "Company-managed gateway"
metadata = { host = "mcp.example.internal", provider = "codex" }
```

| Field | Required | Default | Meaning |
| --- | --- | --- | --- |
| `id` | yes | — | Stable audit identifier using letters, numbers, `.`, `_`, and `-` |
| `effect` | yes | — | `allow` or `deny` |
| `permission` | no | `*` | Normalized permission pattern |
| `resource` | no | `*` | Finding resource/server pattern |
| `source` | no | `*` | Stable repository or `user/...` source pattern |
| `risk` | no | `*` | `low`, `medium`, `high`, or a pattern |
| `metadata` | no | `{}` | Every named metadata selector must match |
| `reason` | no | empty | Human-readable justification shown for denied findings |

Patterns use Python `fnmatch` semantics and are case-sensitive. Metadata commonly includes:

- `provider`: `codex`, `claude`, `cursor`, `gemini`, `vscode`, or another scanner;
- `scope`: `workspace` or `user`;
- `server`: MCP server name;
- `command`: local MCP launcher;
- `host`: remote MCP host without URL credentials or query parameters;
- `environment_variable`: inherited variable name;
- `github_scope`: requested GitHub token scope.

## Evaluation order

For each finding:

1. a matching legacy `deny` rejects it;
2. a matching scoped deny rejects it;
3. a matching legacy `allow` approves it;
4. a matching scoped allow approves it;
5. `default` decides.

All denies therefore override all allows. If multiple scoped rules match, the first matching deny
or allow in file order supplies the decision explanation.

## Corporate example

This policy denies unsafe global behavior, permits repository reads, and approves one managed MCP
gateway without approving every network destination:

```toml
version = 1
default = "deny"
allow = ["filesystem.read"]
deny = [
  "agent.unrestricted",
  "agent.auto_approve",
  "filesystem.outside_workspace",
  "process.shell",
  "secrets.embedded",
]

[[rules]]
id = "managed-mcp-gateway"
effect = "allow"
permission = "network.access"
resource = "corporate-*"
reason = "MCP traffic is inspected by the company gateway"
metadata = { host = "mcp.example.internal" }

[[rules]]
id = "approved-readonly-github-token"
effect = "allow"
permission = "github.token"
metadata = { github_scope = "contents" }
```

See `examples/corporate-policy.toml` and `examples/personal-policy.toml` for copyable starting
points. Replace example hosts and server names before use.

## Fail-closed behavior

Unsupported versions, duplicate rule IDs, invalid effects, non-string selectors, malformed TOML,
and unknown rule fields make `wakindex check` exit `1` with a concise diagnostic. A syntactically
valid policy violation exits `2`; a compliant audit exits `0`.
