# wakindex Architecture

## Description

This document defines wakindex's system boundaries, workspace and endpoint data flow, security
invariants, normalized data model, policy semantics, and extension contract.

## Goals and non-goals

wakindex answers five pre-execution questions:

1. Which agent and MCP configurations are present in a workspace or known user locations?
2. Which processes, tools, and network endpoints can those configurations invoke?
3. Which files, credential names, approval modes, and GitHub token permissions can they reach?
4. Which normalized permissions and concrete resources does that imply?
5. Does the inventory comply with a reviewable local policy?

wakindex is a static reviewer. It does not execute agents or MCP servers, fetch remote tool
descriptions, resolve live cloud IAM, validate downloaded packages, prove runtime behavior, or
replace sandboxing and identity controls.

## Trust and privacy boundaries

The workspace and discovered configuration files are untrusted. JSON, TOML, Markdown, paths,
workflow YAML, and environment references may be intentionally malicious. The policy and wakindex
process are trusted inputs controlled by the reviewer.

Security invariants:

- discovered commands are represented as evidence and never executed;
- credential and environment-variable names may be recorded, but values are never emitted;
- embedded-credential detection reports only the containing field name;
- repository discovery does not traverse symlinks outside the scan root;
- user discovery checks a fixed path allowlist, skips symlinks, and never crawls the profile;
- user sources use stable `user/...` labels and redact the audited home prefix;
- manifest ordering is deterministic and excludes runtime timestamps;
- every matching deny takes precedence over every allow;
- the policy editor binds only to `127.0.0.1` and preserves scoped policy rules;
- malformed policy input fails closed with a diagnostic rather than a traceback.

## Processing pipeline

```text
workspace root -----------------> repository candidate discovery
        |                                      |
        |                                      v
        |                             format-specific scanners
        |                                      |
explicit audit command                         |
        |                                      |
        v                                      |
known user config paths --> privacy context -->+--> normalized Finding values
                                                        |
                                                        v
                                              deterministic Manifest
                                                 /             \
                                                v               v
                                         JSON / text / SARIF   policy v1
                                                                  |
                                                                  v
                                                          pass or violations
```

`scan` uses only the workspace path. `audit` includes known user configuration. `check` remains
workspace-only unless `--include-user` is explicit.

## Component responsibilities

| Component | Responsibility | Must not do |
| --- | --- | --- |
| `environment.py` | Discover known user config paths and combine endpoint findings | Crawl the home directory or emit its absolute prefix |
| `scanners.py` | Extract static evidence from supported files | Execute commands, emit credential values, or escape the boundary |
| `models.py` | Define stable `Finding` and `Manifest` serialization | Add volatile runtime state |
| `policy.py` | Validate TOML and apply legacy/scoped deny precedence | Infer intent or silently accept malformed rules |
| `sarif.py` | Translate violations to SARIF 2.1 | Change policy decisions |
| `cli.py` | Validate arguments, select scan scope/output, and return stable exit codes | Pollute JSON or SARIF stdout |
| `ui.py` | Edit legacy permission choices on loopback while preserving scoped rules | Contact remote services |
| `release.py` | Match immutable SemVer tags to the package version | Publish or mutate tags |

## Discovery scopes

Workspace discovery recursively considers only supported filenames and GitHub workflow locations,
subject to `.wakindexignore`. User discovery does not recurse and considers:

- Codex `~/.codex/config.toml`;
- Claude Code `~/.claude/settings.json` and MCP data in `~/.claude.json`;
- Cursor `~/.cursor/mcp.json`;
- Gemini CLI `~/.gemini/settings.json`;
- platform-specific VS Code user `mcp.json`;
- platform-specific Claude Desktop `claude_desktop_config.json`.

An explicit `--home` makes the user boundary reproducible for containers and endpoint management.
System-level MDM, registry, and fleet APIs are not scanned in this milestone.

## Data model and compatibility

A finding contains:

- a normalized permission ID such as `process.execute`;
- a concrete resource, normally the server, tool, or token identity;
- a repository-relative or stable `user/...` source;
- bounded, value-safe human-readable evidence;
- a `low`, `medium`, or `high` risk;
- structured metadata for policy selectors.

New findings include `provider` and `scope` metadata. Capability-specific metadata includes
`server`, `command`, `host`, `environment_variable`, `path`, `approval_mode`, and
`github_scope`. Vendor-specific details stay in metadata rather than the core manifest shape.

Manifest schema `1.0` remains independent from the package version. Adding metadata keys or new
permission IDs is backward compatible. Removing fields, changing existing permission meaning, or
altering stable source semantics requires a new schema version and migration guidance.

## Permission taxonomy

Current permission IDs:

- `process.execute` and `process.shell`;
- `filesystem.read`, `filesystem.write`, and `filesystem.outside_workspace`;
- `network.access`;
- `secrets.inherit` and `secrets.embedded`;
- `github.token`;
- `agent.auto_approve` and `agent.unrestricted`.

`secrets.embedded` means a sensitive field contains literal material; the value is discarded.
`agent.auto_approve` is narrower than unrestricted host access and identifies confirmation bypass
at either agent or MCP-server scope.

## Policy model

Policy version 1 supports legacy permission-wide `allow` and `deny` patterns plus named rules that
match permission, resource, source, risk, and metadata. Matching is case-sensitive and uses
shell-style wildcards.

Evaluation order is legacy deny, scoped deny, legacy allow, scoped allow, then default. Duplicate
rule IDs, unknown rule fields, unsupported versions, and non-string selectors are invalid.
`docs/policy.md` is the public schema contract.

## Supported inputs

- Claude-style `.claude/settings.json`, `.claude/settings.local.json`, and `.claude.json`;
- Codex `.codex/config.toml` and user `~/.codex/config.toml`;
- VS Code, Cursor, Gemini, Claude Desktop, and generic MCP JSON;
- `.agents/skills/**/SKILL.md`, `.claude/skills/**/SKILL.md`, and `skills/**/SKILL.md`;
- `.github/workflows/*.yml` and `*.yaml`;
- `${NAME}`, `$NAME`, and `%NAME%` environment references;
- Codex `env_vars`, bearer-token variables, and environment-backed HTTP headers.

Repository-relative globs in `.wakindexignore` exclude intentional fixtures or generated content.
Ignore rules are a reviewer decision and part of the trusted configuration boundary.

## Failure behavior

- unreadable or malformed candidate agent files are skipped without executing fallback logic;
- an invalid scan path, user profile path, or policy returns exit code `1`;
- policy violations return exit code `2`;
- compliant scans and audits return `0`;
- machine formats remain valid on stdout, with diagnostics sent to stderr.

## Extension contract

To support a new ecosystem:

1. document the authoritative format and whether its scope is workspace, user, or system;
2. add a scanner returning normalized `Finding` values;
3. use explicit known paths for user/system discovery rather than recursive traversal;
4. add sanitized safe and adversarial fixtures;
5. test determinism, path containment, home redaction, and credential-value safety;
6. extend the taxonomy only when existing permission IDs cannot express the capability;
7. test scoped policy selectors and deny precedence for new metadata;
8. update this document, the policy reference, README, and changelog.
