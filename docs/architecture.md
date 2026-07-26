# AgentScope Architecture

## Description

This document records product scope, threat model, design decisions, and extension points for maintainers.

## Problem statement

Agent configurations are workload definitions spread across JSON, Markdown, YAML, and environment references. Reviewers need a stable answer to: what can run, what can it reach, which credentials can it inherit, and does that exceed policy?

## Threat model

AgentScope assumes the scanned repository may be malicious. It protects the reviewer by:

- performing static analysis only;
- recording environment variable names, never values;
- resolving paths without traversing symlinks outside the scan root;
- binding the UI to loopback;
- using exact, testable policy rules rather than probabilistic classification.

It does not prove runtime behavior, inspect remote MCP implementations, validate IAM policies against cloud APIs, or replace sandboxing.

## Data flow

```text
repository files -> format scanners -> normalized findings -> manifest
                                                    |-> TOML policy -> decision
                                                    |-> terminal / JSON / SARIF
                                                    |-> local policy editor
```

## Permission taxonomy

Findings use `category.action` identifiers:

- `process.execute` and `process.shell`
- `filesystem.read`, `filesystem.write`, and `filesystem.outside_workspace`
- `network.access`
- `secrets.inherit`
- `github.token`
- `agent.unrestricted`

Each finding includes source evidence, a risk level, and structured metadata. Policies allow exact IDs or category wildcards such as `filesystem.*`.

## Supported inputs

- `.claude/settings.json`, `.claude/settings.local.json`, and compatible permission blocks
- `.vscode/mcp.json`, `.mcp.json`, and `mcp.json`
- `.agents/skills/**/SKILL.md`, `.claude/skills/**/SKILL.md`, and `skills/**/SKILL.md`
- `.github/workflows/*.yml` and `*.yaml`
- `${NAME}`, `$NAME`, and `%NAME%` environment references in MCP configuration

Repository-relative glob patterns in `.agentscopeignore` exclude known fixtures or generated content.

## Extension model

Add a scanner that returns `Finding` values, register it in `scan_repository`, and introduce a realistic fixture. Avoid vendor-specific fields in the core model; put them in finding metadata.
