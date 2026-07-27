# wakindex Agent Instructions

## Description

This file is the durable handoff reference for any coding agent working on wakindex. Read it before changing the repository.

## Product contract

wakindex is a local-first, deterministic permission inventory and policy checker for AI agents, MCP servers, skills, and GitHub Actions. It must work without an LLM, network access, or API keys. Static analysis must never execute discovered commands and must never record secret values.

## Architecture

- `src/wakindex/scanners.py` discovers supported files and emits normalized permission findings.
- `src/wakindex/models.py` owns the stable manifest schema.
- `src/wakindex/policy.py` evaluates findings against TOML policy.
- `src/wakindex/cli.py` exposes `scan`, `check`, `init`, and `ui`.
- `src/wakindex/ui.py` serves a loopback-only policy editor using the Python standard library.
- `tests/fixtures/risky_repo` is the realistic adversarial fixture and must remain free of real credentials.

## Working rules

1. Write or update a failing test before changing behavior.
2. Keep scanning deterministic: sort paths and findings; never include timestamps in comparable output.
3. Treat inputs as hostile. Do not follow symlinks outside the scan root, execute commands, interpolate environment variables, or expose secret values.
4. Maintain backward compatibility for the manifest schema within a major version.
5. Every source or configuration file starts with a short description comment or docstring where its format permits comments.
6. Run `python -m pytest`, `python -m ruff check .`, and the Docker test command before release.
7. Update `docs/architecture.md`, `README.md`, and `CHANGELOG.md` when behavior changes.

## Current status

The MVP supports Claude-style settings, VS Code and generic MCP JSON, `SKILL.md` files, GitHub workflow permissions, environment-variable references, manifest generation, TOML policy enforcement, SARIF output, a Docker action, and a local permission editor.
