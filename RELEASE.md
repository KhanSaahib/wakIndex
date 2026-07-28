# Releasing wakindex

## Description

This document defines wakindex's versioning contract and the repeatable process for publishing a
GitHub Release from an immutable Git tag.

## Versioning policy

wakindex follows [Semantic Versioning 2.0.0](https://semver.org/):

- `MAJOR` changes when a stable public interface becomes incompatible.
- `MINOR` changes when backward-compatible capabilities are added.
- `PATCH` changes when backward-compatible defects or documentation are fixed.

While wakindex is below `1.0.0`, a minor release may contain compatibility changes. Those changes
must be called out under `Changed` in `CHANGELOG.md`. Patch releases must remain backward
compatible. The manifest schema is versioned independently and cannot change incompatibly without
a documented migration.

The package version has one source of truth: `src/wakindex/__init__.py`. Packaging and
`wakindex --version` both read that value. Release tags are immutable and use
`vMAJOR.MINOR.PATCH`, for example `v0.2.0`.

## Changelog policy

`CHANGELOG.md` follows Keep a Changelog conventions:

1. User-visible work is added to `Unreleased` in the same pull request.
2. Entries use `Added`, `Changed`, `Fixed`, `Deprecated`, `Removed`, or `Security`.
3. A release moves those entries to a dated `MAJOR.MINOR.PATCH` section.
4. Internal refactors without user impact may be omitted.
5. Breaking or security-relevant changes must include upgrade or mitigation guidance.

## Release checklist

1. Start from an up-to-date, clean `main` branch.
2. Choose the next SemVer version and update `__version__`.
3. Move `Unreleased` changelog entries into a dated version section.
4. Run:

   ```bash
   python -m pip install -e ".[dev]"
   python scripts/check_release.py vMAJOR.MINOR.PATCH
   python -m pytest
   python -m ruff check .
   docker build --target test -t wakindex-test .
   ```

5. Merge the release preparation change into `main`.
6. Create and push the exact tag:

   ```bash
   git tag -a vMAJOR.MINOR.PATCH -m "wakindex vMAJOR.MINOR.PATCH"
   git push origin vMAJOR.MINOR.PATCH
   ```

7. Confirm the Release workflow succeeds and publishes the wheel plus `SHA256SUMS`.
8. Review the generated GitHub Release notes and verify the installation artifact.
9. Add a fresh `Unreleased` section if the next change requires one.

Do not reuse, force-move, or recreate a published release tag. Correct a bad release with a new
patch version.
