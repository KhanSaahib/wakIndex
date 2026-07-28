# wakindex Architecture

## Description

This document defines wakindex's system boundaries, trust model, data contracts, and rules for safely extending the scanner.

## Purpose and scope

Agent permissions are rarely declared in one place. MCP launch commands, agent allowlists, skill instructions, workflow token scopes, environment references, and filesystem paths collectively describe the effective pre-runtime attack surface.

wakindex converts those declarations into a normalized permission manifest and evaluates it against an explicit team policy. It answers four review questions:

1. What processes and tools may run?
2. What local or remote resources may be reached?
3. Which credential names or platform identities may be inherited?
4. Which findings exceed policy?

wakindex is a static preflight control. It does not attest runtime behavior, inspect remote server implementations, query cloud IAM, resolve OAuth grants, or replace operating-system sandboxing.

## Design principles

- **Safe by construction:** parse configuration as data and never execute it.
- **Local first:** core behavior has no network, LLM, or API-key dependency.
- **Deterministic:** stable traversal and sorting make manifests reviewable in Git.
- **Explainable:** every finding has a source, evidence summary, risk, and resource.
- **Deny first:** explicit deny rules override allows; unknown permissions fail under a deny-default policy.
- **Format tolerant, model strict:** vendor inputs may vary, but normalized permission identifiers stay stable.
- **Secret minimizing:** retain environment-variable names only; discard values.

## System context

```text
Untrusted repository
  JSON / YAML / Markdown / environment references
                    |
                    v
          discovery and safe parsers
                    |
                    v
        normalized Finding objects
              /             \
             v               v
      Manifest JSON      TOML policy
             |               |
             +-------> evaluation
                         /    |    \
                        v     v     v
                     text   JSON  SARIF
```

The repository is the only untrusted input boundary in core scanning. Policy files are operator-controlled inputs, but invalid policy must still fail clearly rather than weaken enforcement.

## Component responsibilities

| Component | Responsibility | Must not |
|---|---|---|
| `scanners.py` | Discover supported files and normalize declarations | Execute commands, follow escaping symlinks, read secret values |
| `models.py` | Define stable findings and manifest serialization | Contain vendor-specific parsing |
| `policy.py` | Load TOML and apply deny/allow/default precedence | Infer intent or silently permit unknown permissions |
| `sarif.py` | Map violations to SARIF 2.1 | Change policy decisions |
| `cli.py` | Validate arguments, select output, set exit codes | Mix diagnostics into JSON or SARIF |
| `ui.py` | Edit policy on loopback with explicit decisions | Bind publicly or require external assets |
| `scripts/check_release.py` | Validate release metadata against a tag | Publish, tag, or mutate repository state |

## Discovery and parsing

Discovery walks the scan root in stable path order. Symlinks are skipped, resolved candidates must remain beneath the root, and `.wakindexignore` applies repository-relative glob patterns before parsing.

Supported inputs currently include:

- `.claude/settings.json`, `.claude/settings.local.json`, and compatible permission blocks;
- `.vscode/mcp.json`, `.mcp.json`, and `mcp.json`;
- `.agents/skills/**/SKILL.md`, `.claude/skills/**/SKILL.md`, and `skills/**/SKILL.md`;
- `.github/workflows/*.yml` and `*.yaml`;
- `${NAME}`, `$NAME`, and `%NAME%` environment references.

Malformed or unsupported files are skipped without stopping the repository scan. A parser should emit a finding only when evidence is explicit enough to explain.

## Normalized manifest contract

Each `Finding` includes:

- `permission`: stable `category.action` identifier;
- `resource`: affected tool, server, identity, or path;
- `source`: repository-relative evidence file;
- `evidence`: concise, bounded explanation;
- `risk`: `low`, `medium`, or `high`;
- `metadata`: structured vendor or resource details.

Current permission identifiers are:

- `process.execute` and `process.shell`;
- `filesystem.read`, `filesystem.write`, and `filesystem.outside_workspace`;
- `network.access`;
- `secrets.inherit`;
- `github.token`;
- `agent.unrestricted`.

Manifest schema changes follow these rules:

- additive optional metadata is backward compatible;
- removing or renaming fields or permission identifiers is breaking;
- breaking changes require a schema-version increment and major package release;
- output order and JSON formatting remain deterministic within a schema version.

## Policy evaluation

Policies support exact identifiers and shell-style category wildcards such as `filesystem.*`. Evaluation order is:

1. matching deny rule → violation;
2. matching allow rule → accepted;
3. no match → policy default.

This precedence prevents a broad allow from overriding a narrow deny. Recommended team policy uses `default = "deny"` so new scanner capabilities require conscious review.

## Trust and failure boundaries

- Secret matching observes variable names embedded in configuration, never process-environment values.
- URLs may be recorded as evidence, but scanning never connects to them.
- Command strings are evidence only and are never passed to a shell.
- Absolute machine paths are not emitted as finding sources.
- The policy editor binds to `127.0.0.1` and writes only the selected policy file.
- JSON and SARIF outputs contain no banners or human-only diagnostics.
- CI receives exit code `2` for policy violations and `1` for operational errors.

## Extending wakindex

For a new ecosystem or permission:

1. add a sanitized realistic fixture using `.invalid` hosts and fake secret names;
2. add a failing integration test for discovery, evidence, risk, and determinism;
3. implement a parser that returns normalized `Finding` objects;
4. register it in repository discovery without broadening traversal unsafely;
5. document the input format and permission identifier;
6. verify text, JSON, SARIF, policy, and Docker behavior;
7. add a changelog entry.

Vendor-specific semantics belong in parser code and `metadata`, not in the core model.

## Release architecture

Package releases are created from immutable `vX.Y.Z` tags. The release workflow validates version synchronization and changelog state before running the same local and Docker quality gates. Only then does it build Python artifacts, produce checksums, and create a GitHub Release. See `RELEASE.md` for the complete operator procedure and compatibility policy.

## Known limitations and roadmap boundaries

Static configuration shows declared capability, not whether a remote implementation honors it. Cloud-role expansion, runtime tracing, OAuth-scope introspection, configuration dataflow across generated files, and signed provenance are potential future layers. They should be added as explicit analyzers rather than hidden network behavior in core scanning.
