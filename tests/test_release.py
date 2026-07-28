"""Description: Regression tests for release tags, package versioning, and automation."""

import tomllib
from pathlib import Path

import pytest

from wakindex import __version__
from wakindex.release import ReleaseValidationError, validate_release_tag

ROOT = Path(__file__).parents[1]


def test_release_tag_must_match_package_version() -> None:
    assert validate_release_tag(f"v{__version__}", __version__) == __version__


@pytest.mark.parametrize(
    ("tag", "reason"),
    [
        ("0.1.0", "must start with v"),
        ("v0.1", "must use vMAJOR.MINOR.PATCH"),
        ("v0.1.0-rc.1", "must use vMAJOR.MINOR.PATCH"),
        ("v0.2.0", "does not match package version"),
    ],
)
def test_invalid_release_tags_are_rejected(tag: str, reason: str) -> None:
    with pytest.raises(ReleaseValidationError, match=reason):
        validate_release_tag(tag, __version__)


def test_package_version_is_single_sourced() -> None:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        config = tomllib.load(stream)

    assert config["project"]["dynamic"] == ["version"]
    assert "version" not in config["project"]
    assert config["tool"]["hatch"]["version"]["path"] == "src/wakindex/__init__.py"


def test_release_workflow_is_tag_driven_and_minimally_privileged() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

    assert 'tags: ["v*.*.*"]' in workflow
    assert "contents: write" in workflow
    assert "python scripts/check_release.py" in workflow
    assert "gh release create" in workflow
    assert "pull_request:" not in workflow


def test_local_agent_instructions_are_ignored() -> None:
    ignore_rules = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "/AGENTS.md" in ignore_rules
