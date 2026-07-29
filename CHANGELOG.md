# Changelog

## Description

All notable user-visible changes to wakindex are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and releases follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Local-first scanner, policy engine, CLI, SARIF output, browser policy editor, Docker image, and
  GitHub Action.
- Tag-driven GitHub Release workflow with wheel artifacts and SHA-256 checksums.
- Explicit SemVer, changelog, and release process in `RELEASE.md`.
- Two-part WAK / INDEX panel with init guidance.
- Environment audits for known Codex, Claude, Cursor, Gemini, VS Code, and Claude Desktop user
  configuration.
- Native Codex TOML scanning, Claude hook discovery, sandbox write/network grants, auto-approval
  and embedded-credential signals, and privacy-preserving user source labels.
- Versioned, resource-scoped policy rules with stable IDs, metadata selectors, reasons, and deny
  precedence.
- Copyable personal and corporate policy examples.

### Changed

- Standardized the product name as lowercase `wakindex`.
- Limited the startup panel to `wakindex init` so scan, check, UI, and help remain compact.
- Expanded architecture, contribution, security, and user documentation.
- Added provider and workspace/user scope metadata to normalized findings.
