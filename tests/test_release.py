"""Description: Tests for release tag, version synchronization, and changelog validation."""

from pathlib import Path

from scripts.check_release import release_notes, validate_release


def release_tree(tmp_path: Path, version: str = "1.2.3") -> Path:
    """Create the smallest valid release metadata tree."""
    package = tmp_path / "src" / "wakindex"
    package.mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nname = "wakindex-security"\nversion = "{version}"\n',
        encoding="utf-8",
    )
    (package / "__init__.py").write_text(
        f'"""Description: Fixture package metadata."""\n__version__ = "{version}"\n',
        encoding="utf-8",
    )
    (tmp_path / "CHANGELOG.md").write_text(
        f"# Changelog\n\n## [{version}] - 2026-07-27\n\n### Added\n\n- Release.\n",
        encoding="utf-8",
    )
    return tmp_path


def test_valid_release_metadata_passes(tmp_path: Path) -> None:
    assert validate_release(release_tree(tmp_path), "v1.2.3") == []


def test_mismatched_versions_are_all_reported(tmp_path: Path) -> None:
    root = release_tree(tmp_path)
    errors = validate_release(root, "v1.2.4")
    assert any("pyproject.toml" in error for error in errors)
    assert any("runtime version" in error for error in errors)
    assert any("CHANGELOG.md" in error for error in errors)


def test_invalid_tag_is_rejected(tmp_path: Path) -> None:
    errors = validate_release(release_tree(tmp_path), "release-1.2.3")
    assert errors == ["release tag must start with 'v'"]


def test_release_notes_come_from_matching_changelog_section(tmp_path: Path) -> None:
    root = release_tree(tmp_path)
    assert release_notes(root, "1.2.3") == "### Added\n\n- Release.\n"
