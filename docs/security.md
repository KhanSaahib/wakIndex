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
Secret detection stores names only. Embedded-credential detection reports the environment or
header field name and discards its value. User audits check only documented configuration paths,
skip symlinks, and replace the audited home prefix with `~` in evidence and metadata. They do not
crawl arbitrary profile files.

The browser editor listens on `127.0.0.1` and writes only the explicitly selected policy path.
Scoped rules are preserved when the editor changes legacy permission-wide choices.

The enterprise dashboard also listens only on `127.0.0.1`. It is read-only, serves one immutable
inventory snapshot, fetches hostile data from a same-origin JSON endpoint, and inserts values with
DOM text operations rather than executable HTML. Responses disable caching and framing, prevent
MIME sniffing, suppress referrers, and apply a restrictive Content Security Policy. It is not an
authenticated multi-user web service and must not be exposed directly to a network.

Account catalogs are trusted operator input. They may contain business identity labels and
provider-account aliases, but profile home paths are used only for discovery and are never
serialized. wakindex does not read vendor credential stores, keychains, login sessions, browser
profiles, or chat transcripts to resolve an identity.

wakindex does not validate remote server behavior, live cloud IAM, runtime sandbox enforcement,
the active model for a session, or the live provider login behind an operator alias.
See `docs/architecture.md` for the complete threat model and trust boundaries.
