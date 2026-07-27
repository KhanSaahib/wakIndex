"""Description: End-to-end CLI tests for manifests, policy exits, and SARIF output."""

import json
from pathlib import Path

import pytest

from wakindex.branding import (
    CLI_BANNER,
    COMMAND_GUIDE,
    PANEL_DIVIDER,
    PROJECT_DESCRIPTION,
    terminal_banner,
)
from wakindex.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def test_scan_writes_machine_readable_manifest(tmp_path: Path) -> None:
    output = tmp_path / "manifest.json"
    exit_code = main(["scan", str(FIXTURES / "safe_repo"), "--output", str(output)])
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["schema_version"] == "1.0"
    assert payload["findings"]


def test_check_fails_risky_repo_and_emits_sarif(tmp_path: Path) -> None:
    policy = tmp_path / "policy.toml"
    policy.write_text(
        'default = "deny"\nallow = ["filesystem.read"]\ndeny = ["agent.unrestricted"]\n',
        encoding="utf-8",
    )
    output = tmp_path / "result.sarif"
    exit_code = main(
        [
            "check",
            str(FIXTURES / "risky_repo"),
            "--policy",
            str(policy),
            "--format",
            "sarif",
            "--output",
            str(output),
        ]
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 2
    assert payload["version"] == "2.1.0"
    assert payload["runs"][0]["results"]


def test_init_refuses_to_overwrite_existing_policy(tmp_path: Path) -> None:
    policy = tmp_path / "wakindex-policy.toml"
    policy.write_text("# keep me\n", encoding="utf-8")
    assert main(["init", "--policy", str(policy)]) == 1
    assert policy.read_text(encoding="utf-8") == "# keep me\n"


def test_text_scan_displays_product_identity(capsys) -> None:
    exit_code = main(["scan", str(FIXTURES / "safe_repo"), "--format", "text"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert CLI_BANNER in captured.err
    assert PROJECT_DESCRIPTION in captured.err
    assert COMMAND_GUIDE in captured.err
    assert f"{PANEL_DIVIDER}\n\n" in captured.err
    assert "PERMISSION SNAKE" not in captured.err
    assert CLI_BANNER not in captured.out
    captured.err.encode("utf-8", errors="strict")


def test_help_displays_the_two_part_wakindex_banner(capsys) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--help"])

    output = capsys.readouterr().out
    assert exit_info.value.code == 0
    assert CLI_BANNER in output
    assert PROJECT_DESCRIPTION in output
    assert COMMAND_GUIDE in output
    assert PANEL_DIVIDER in output
    assert "██╗    ██╗" in output
    assert "██╗███╗   ██╗" in output
    assert "scan" in output


def test_json_scan_remains_machine_readable_without_banner(capsys) -> None:
    exit_code = main(["scan", str(FIXTURES / "safe_repo"), "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert json.loads(captured.out)["schema_version"] == "1.0"
    assert CLI_BANNER not in captured.out
    assert CLI_BANNER in captured.err


def test_startup_panel_ends_with_newline_after_divider() -> None:
    panel = terminal_banner()

    assert panel.endswith(f"{PANEL_DIVIDER}\n")
