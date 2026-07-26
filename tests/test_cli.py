"""Description: End-to-end CLI tests for manifests, policy exits, and SARIF output."""

import json
from pathlib import Path

from agentscope.cli import main

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
    policy = tmp_path / "agentscope-policy.toml"
    policy.write_text("# keep me\n", encoding="utf-8")
    assert main(["init", "--policy", str(policy)]) == 1
    assert policy.read_text(encoding="utf-8") == "# keep me\n"
