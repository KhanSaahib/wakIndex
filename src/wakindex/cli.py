"""Description: Dependency-free command-line interface for scanning and policy enforcement."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from wakindex.branding import terminal_banner
from wakindex.models import Manifest
from wakindex.policy import Policy, evaluate
from wakindex.sarif import render_sarif
from wakindex.scanners import scan_repository

DEFAULT_POLICY = Policy(
    default="deny",
    allow=("filesystem.read",),
    deny=("agent.unrestricted", "process.shell", "filesystem.outside_workspace"),
)


def _configure_utf8(stream: object) -> None:
    """Use UTF-8 on real text streams while remaining compatible with test captures."""
    reconfigure = getattr(stream, "reconfigure", None)
    if callable(reconfigure):
        try:
            reconfigure(encoding="utf-8", errors="strict")
        except (AttributeError, OSError, ValueError):
            pass


def _write_or_print(content: str, output: str | None) -> None:
    if output:
        Path(output).write_text(content, encoding="utf-8")
    else:
        print(content, end="")


def _text_report(manifest: Manifest) -> str:
    lines = [f"INVENTORY - {len(manifest.findings)} permission finding(s)"]
    for item in manifest.findings:
        lines.append(
            f"[{item.risk.upper():6}] {item.permission:30} {item.source} - {item.evidence}"
        )
    return "\n".join(lines) + "\n"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wakindex",
        description=terminal_banner(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version="wakIndex 0.1.0")
    commands = parser.add_subparsers(dest="command", required=True)

    scan = commands.add_parser("scan", help="create a permission inventory")
    scan.add_argument("path", nargs="?", default=".")
    scan.add_argument("--format", choices=("json", "text"), default="json")
    scan.add_argument("--output")

    check = commands.add_parser("check", help="enforce a TOML permission policy")
    check.add_argument("path", nargs="?", default=".")
    check.add_argument("--policy", default="wakindex-policy.toml")
    check.add_argument("--format", choices=("text", "json", "sarif"), default="text")
    check.add_argument("--output")

    init = commands.add_parser("init", help="create a conservative starter policy")
    init.add_argument("--policy", default="wakindex-policy.toml")
    init.add_argument("--force", action="store_true")

    ui = commands.add_parser("ui", help="open the local permission policy editor")
    ui.add_argument("path", nargs="?", default=".")
    ui.add_argument("--policy", default="wakindex-policy.toml")
    ui.add_argument("--port", type=int, default=8765)
    ui.add_argument("--no-browser", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    _configure_utf8(sys.stdout)
    _configure_utf8(sys.stderr)
    arguments = list(argv) if argv is not None else sys.argv[1:]
    if arguments not in (["--help"], ["-h"]):
        print(terminal_banner(), file=sys.stderr)
    args = _parser().parse_args(arguments)
    if args.command == "init":
        target = Path(args.policy)
        if target.exists() and not args.force:
            print(f"Refusing to overwrite existing policy: {target}", file=sys.stderr)
            return 1
        DEFAULT_POLICY.write(target)
        print(f"Created policy: {target}")
        return 0

    if args.command == "ui":
        from wakindex.ui import serve

        return serve(Path(args.path), Path(args.policy), args.port, not args.no_browser)

    root = Path(args.path)
    if not root.is_dir():
        print(f"Scan path is not a directory: {root}", file=sys.stderr)
        return 1
    manifest = scan_repository(root)
    if args.command == "scan":
        content = manifest.to_json() if args.format == "json" else _text_report(manifest)
        _write_or_print(content, args.output)
        return 0

    policy_path = Path(args.policy)
    if not policy_path.is_file():
        print(f"Policy not found: {policy_path}; run 'wakindex init'", file=sys.stderr)
        return 1
    evaluation = evaluate(manifest, Policy.load(policy_path))
    if args.format == "sarif":
        content = render_sarif(evaluation)
    elif args.format == "json":
        content = manifest.to_json()
    else:
        status = "PASS" if evaluation.passed else "FAIL"
        lines = [f"POLICY REVIEW - {status}"]
        lines.extend(
            f"- {item.finding.permission} in {item.finding.source}: {item.reason}"
            for item in evaluation.violations
        )
        content = "\n".join(lines) + "\n"
    _write_or_print(content, args.output)
    return 0 if evaluation.passed else 2
