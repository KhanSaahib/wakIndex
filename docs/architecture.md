# wakindex Architecture

## Description

This document defines wakindex's system boundaries, data flow, security invariants, component
responsibilities, and extension contract.

## Goals and non-goals

wakindex answers four pre-execution questions:

1. Which processes, tools, and network endpoints can an agent configuration invoke?
2. Which files, environment-variable names, and GitHub token permissions can it reach?
3. Which normalized permissions does that imply?
4. Does the inventory comply with a repository-owned policy?

wakindex is a static reviewer. It does not execute agents or MCP servers, fetch remote tool
descriptions, resolve live cloud IAM, prove runtime behavior, or replace sandboxing and identity
controls.

## Trust boundaries

The repository being scanned is untrusted. Configuration text, Markdown, paths, workflow YAML,
and environment references may be intentionally malicious. The local policy and wakindex process
are trusted inputs controlled by the reviewer.

Security invariants:

- discovered commands are represented as evidence and never executed;
- environment-variable names may be recorded, but values are never read;
- symlinks and resolved paths outside the scan root are not traversed;
- manifest ordering is deterministic and excludes runtime timestamps;
- policy deny rules take precedence over allow rules;
- the policy editor binds only to `127.0.0.1`;
- malformed or unsupported inputs fail closed where policy is concerned and do not crash a scan.

## Processing pipeline

```text
untrusted repository
        |
        v
candidate discovery --> format scanners --> normalized Finding values
                                                |
                                                v
                                      deterministic Manifest
                                         /             \
                                        v               v
                                 JSON / text / SARIF   TOML policy
                                                          |
                                                          v
                                                  pass or violations
```

## Component responsibilities

| Component | Responsibility | Must not do |
| --- | --- | --- |
| `scanners.py` | Discover supported files and extract permission evidence | Execute commands, read secrets, or escape the root |
| `models.py` | Define stable `Finding` and `Manifest` serialization | Add volatile runtime state |
| `policy.py` | Load TOML and apply deny, allow, then default | Infer intent probabilistically |
| `sarif.py` | Translate violations to SARIF 2.1 | Change policy decisions |
| `cli.py` | Validate arguments, select output, and return stable exit codes | Pollute JSON or SARIF stdout |
| `ui.py` | Edit explicit allow/deny choices on loopback | Contact remote services |
| `release.py` | Match immutable SemVer tags to the package version | Publish or mutate tags |

## Data model and compatibility

A finding contains:

- a normalized permission ID such as `process.execute`;
- the affected resource;
- a repository-relative source path;
- bounded human-readable evidence;
- a risk level;
- optional structured metadata.

The manifest schema version is independent from the package version. Within a package major
version, existing fields and permission meanings remain compatible. An incompatible schema change
requires a new schema version, migration guidance, fixtures for both behaviors where practical,
and a changelog entry.

## Permission taxonomy

Current permission IDs:

- `process.execute` and `process.shell`;
- `filesystem.read`, `filesystem.write`, and `filesystem.outside_workspace`;
- `network.access`;
- `secrets.inherit`;
- `github.token`;
- `agent.unrestricted`.

Policies accept exact IDs and category wildcards such as `filesystem.*`. Explicit deny always wins,
then explicit allow, then the configured default.

## Supported inputs

- Claude-style `.claude/settings.json` and `.claude/settings.local.json`;
- VS Code and generic `.vscode/mcp.json`, `.mcp.json`, and `mcp.json`;
- `.agents/skills/**/SKILL.md`, `.claude/skills/**/SKILL.md`, and `skills/**/SKILL.md`;
- `.github/workflows/*.yml` and `*.yaml`;
- `${NAME}`, `$NAME`, and `%NAME%` environment references in MCP configuration.

Repository-relative globs in `.wakindexignore` exclude intentional fixtures or generated content.
Ignore rules are a reviewer decision and therefore part of the trusted configuration boundary.

## Failure behavior

- unreadable or malformed candidate files are skipped without executing fallback logic;
- a missing policy causes `check` to fail with exit code `1`;
- policy violations return exit code `2`;
- compliant scans return `0`;
- machine formats remain valid on stdout, with diagnostics sent to stderr.

## Extension contract

To support a new ecosystem:

1. add a scanner that returns normalized `Finding` values;
2. register it in `scan_repository`;
3. add sanitized safe and adversarial fixtures;
4. test determinism, path containment, and secret-value safety;
5. extend the taxonomy only when existing permission IDs cannot express the capability;
6. update this document, README, and changelog.

Vendor-specific details belong in finding metadata rather than the core manifest schema.
