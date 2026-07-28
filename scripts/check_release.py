"""Description: Validate a wakindex release tag, version sources, and changelog entry."""

from __future__ import annotations

import argparse
import ast
import re
import tomllib
from collections.abc import Sequence
from pathlib import Path

SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def package_versions(root: Path) -> tuple[str, str]:
    """Return versions from package metadata and runtime metadata."""
    with (root / "pyproject.toml").open("rb") as stream:
        project_version = str(tomllib.load(stream)["project"]["version"])

    module = ast.parse((root / "src" / "wakindex" / "__init__.py").read_text(encoding="utf-8"))
    runtime_version = ""
    for node in module.body:
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "__version__"
                for target in node.targets
            )
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            runtime_version = node.value.value
            break
    return project_version, runtime_version


def validate_release(root: Path, tag: str) -> list[str]:
    """Return every release-contract violation without mutating the repository."""
    errors: list[str] = []
    if not tag.startswith("v"):
        return ["release tag must start with 'v'"]

    version = tag[1:]
    if not SEMVER.fullmatch(version):
        errors.append(f"release tag is not valid SemVer: {tag}")

    project_version, runtime_version = package_versions(root)
    if project_version != version:
        errors.append(f"pyproject.toml version {project_version!r} does not match {version!r}")
    if runtime_version != version:
        errors.append(f"runtime version {runtime_version!r} does not match {version!r}")

    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    dated_heading = re.compile(
        rf"(?m)^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}\s*$"
    )
    if not dated_heading.search(changelog):
        errors.append(
            f"CHANGELOG.md needs a dated '## [{version}] - YYYY-MM-DD' release heading"
        )
    return errors


def release_notes(root: Path, version: str) -> str:
    """Extract the reviewed body of a dated changelog release section."""
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    section = re.search(
        rf"(?ms)^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}\s*\n"
        rf"(?P<body>.*?)(?=^## \[|\Z)",
        changelog,
    )
    if section is None:
        raise ValueError(f"no dated changelog section for {version}")
    return section.group("body").strip() + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    """Validate command-line input and report actionable release errors."""
    parser = argparse.ArgumentParser(description="Validate wakindex release metadata.")
    parser.add_argument("--tag", required=True, help="Git tag, for example v1.2.3")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--notes-output",
        type=Path,
        help="write the matching changelog section as GitHub release notes",
    )
    args = parser.parse_args(argv)

    errors = validate_release(args.root.resolve(), args.tag)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    if args.notes_output:
        args.notes_output.write_text(
            release_notes(args.root.resolve(), args.tag[1:]),
            encoding="utf-8",
        )
    print(f"Release metadata is valid for {args.tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
