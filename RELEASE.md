# Release and Versioning Policy

## Description

This document defines how wakindex versions, validates, publishes, and maintains releases.

## Versioning policy

wakindex follows [Semantic Versioning 2.0.0](https://semver.org/):

- `MAJOR` changes for incompatible CLI, policy, manifest-schema, or supported-action behavior.
- `MINOR` changes for backward-compatible capabilities, scanners, permission identifiers, or outputs.
- `PATCH` changes for backward-compatible fixes, documentation corrections, and hardening.

Before `1.0.0`, minor versions may contain compatibility changes as the interface stabilizes. Those changes must be called out prominently in the changelog. Patch releases remain backward compatible.

Pre-releases use SemVer identifiers such as `1.0.0-rc.1` and tags such as `v1.0.0-rc.1`.

## Sources of version truth

The release version appears in two files and must match:

- `pyproject.toml` for package metadata;
- `src/wakindex/__init__.py` for runtime reporting.

`scripts/check_release.py` verifies both sources against the Git tag. Release tags use the exact form `vX.Y.Z` or a valid SemVer pre-release form.

The manifest `schema_version` is versioned separately. Increment it only when the serialized contract changes. A breaking manifest change requires a new major package version.

## Changelog policy

`CHANGELOG.md` follows Keep a Changelog conventions:

- user-visible work is added under `[Unreleased]`;
- entries use `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, or `Security`;
- release preparation moves entries into `## [X.Y.Z] - YYYY-MM-DD`;
- internal refactors without user impact may be omitted.

The release workflow refuses a tag without a matching dated changelog heading.

## Preparing a release

1. Start from an up-to-date, clean `main` branch.
2. Choose the SemVer increment based on compatibility and user impact.
3. Update both version sources.
4. Move relevant changelog entries from `[Unreleased]` into a dated release section.
5. Run the complete verification suite:

   ```bash
   python -m pip install -e ".[dev]"
   python -m pip install build twine
   pytest
   ruff check .
   docker build --target test -t wakindex-test .
   python scripts/check_release.py --tag vX.Y.Z
   python -m build
   python -m twine check dist/*
   ```

6. Open and merge a release-preparation pull request.
7. From the resulting `main` commit, create and push an annotated tag:

   ```bash
   git tag -a vX.Y.Z -m "wakindex X.Y.Z"
   git push origin vX.Y.Z
   ```

## Automated GitHub release

Pushing a `v*` tag starts `.github/workflows/release.yml`. The workflow:

1. validates tag syntax, synchronized versions, and the dated changelog entry;
2. runs tests and lint;
3. builds the Docker test stage;
4. builds the Python wheel and source distribution;
5. validates package metadata;
6. creates SHA-256 checksums;
7. publishes an immutable GitHub Release using the reviewed changelog section, with artifacts.

The workflow intentionally does not publish to PyPI or a container registry. Those channels require a separate, reviewed trusted-publishing design.

## GitHub Action compatibility tags

Consumers should pin the immutable full version, preferably by commit SHA for maximum supply-chain assurance:

```yaml
uses: KhanSaahib/AgentScope@v1.2.3
```

A moving major alias such as `v1` may be updated manually after verifying a release, but it must never cross a major-version boundary. Full `vX.Y.Z` tags are never moved or reused.

## Failed releases and corrections

- If automation fails, fix the cause on `main`, increment the version if the tag was published, and create a new tag.
- Never force-push or retarget a published full version tag.
- If a release is unsafe, mark it clearly in GitHub, document the issue under `Security` or `Fixed`, and publish a corrected patch.
- Security releases follow the same gates but may be prepared privately through GitHub Security Advisories.
