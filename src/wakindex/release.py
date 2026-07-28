"""Description: Validate release tags against wakindex's package version."""

from __future__ import annotations

import re
import sys
from collections.abc import Sequence

from wakindex import __version__

SEMVER_TAG = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class ReleaseValidationError(ValueError):
    """Raised when a release tag is malformed or targets another version."""


def validate_release_tag(tag: str, package_version: str) -> str:
    """Return the validated version or raise a human-readable release error."""
    if not tag.startswith("v"):
        raise ReleaseValidationError("release tag must start with v")
    match = SEMVER_TAG.fullmatch(tag)
    if match is None:
        raise ReleaseValidationError("release tag must use vMAJOR.MINOR.PATCH")
    tag_version = ".".join(match.groups())
    if tag_version != package_version:
        raise ReleaseValidationError(
            f"tag version {tag_version} does not match package version {package_version}"
        )
    return tag_version


def main(argv: Sequence[str] | None = None) -> int:
    """Validate the one tag supplied by the release workflow."""
    arguments = list(argv) if argv is not None else sys.argv[1:]
    if len(arguments) != 1:
        print("usage: python scripts/check_release.py vMAJOR.MINOR.PATCH", file=sys.stderr)
        return 2
    try:
        version = validate_release_tag(arguments[0], __version__)
    except ReleaseValidationError as error:
        print(f"release validation failed: {error}", file=sys.stderr)
        return 1
    print(f"release tag validated for wakindex {version}")
    return 0
