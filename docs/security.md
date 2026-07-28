# Security Policy

## Description

This document defines wakindex's supported-version policy, security boundaries, and private
vulnerability-reporting expectations.

## Supported versions

Until `1.0.0`, only the latest published minor release receives security fixes. After `1.0.0`, the
latest major release and any additional versions listed in a GitHub Security Advisory are
supported.

## Report a vulnerability

Use the repository's private GitHub Security Advisory flow. Include the affected version, input
format, reproduction steps, expected impact, and any proposed mitigation. Do not open a public
issue for an undisclosed vulnerability and never include live credentials or customer data.

## Security boundaries

wakindex scans untrusted text without executing configured agents, tools, or MCP commands.
Secret detection stores names only. The browser editor listens on `127.0.0.1` and writes only the
explicitly selected policy path.

wakindex does not validate remote server behavior, live cloud IAM, or runtime sandbox enforcement.
See `docs/architecture.md` for the complete threat model and trust boundaries.
