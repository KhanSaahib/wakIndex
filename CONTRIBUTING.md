# Contributing to wakindex

## Description

This guide defines the development, testing, documentation, and security expectations for contributions.

## Before changing code

Open an issue for new permission categories, input formats, or compatibility changes. Describe the declaration being detected, its security meaning, expected evidence, and likely risk.

Never add live credentials or production endpoints to fixtures. Use descriptive fake environment names and `.invalid` domains.

## Development setup

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
```

The core package intentionally has no runtime dependencies. Discuss additions before introducing one.

## Change workflow

1. Add or update a realistic fixture.
2. Write a failing behavior-focused test.
3. Implement the narrowest safe parser or policy change.
4. Confirm deterministic output and secret-name-only handling.
5. Update `README.md` for user behavior and `docs/architecture.md` for contracts or boundaries.
6. Add a user-visible entry beneath `[Unreleased]` in `CHANGELOG.md`.
7. Run local and Docker verification.

```bash
pytest
ruff check .
docker build --target test -t wakindex-test .
docker run --rm wakindex-test
```

## Pull requests

Keep pull requests focused and explain:

- the permission or user problem being addressed;
- the input evidence and normalized output;
- security and compatibility implications;
- tests and fixtures used for verification;
- documentation and changelog updates.

Changes must not execute scanned content, follow symlinks outside the scan root, expose secret values, or introduce network requirements into core scanning.

## Releases

Maintainers follow `RELEASE.md`. Contributors should not create release tags or edit published release sections. Add release-worthy changes only under `[Unreleased]`.
