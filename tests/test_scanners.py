"""Description: Integration tests for realistic repository permission discovery."""

from pathlib import Path

from agentscope.scanners import scan_repository

FIXTURES = Path(__file__).parent / "fixtures"


def test_risky_repository_inventory_is_complete_and_secret_safe() -> None:
    manifest = scan_repository(FIXTURES / "risky_repo")
    permission_ids = {finding.permission for finding in manifest.findings}

    assert {
        "agent.unrestricted",
        "process.execute",
        "process.shell",
        "network.access",
        "secrets.inherit",
        "filesystem.outside_workspace",
        "github.token",
    } <= permission_ids
    serialized = manifest.to_json()
    assert "PROD_DATABASE_URL" in serialized
    assert "MCP_API_TOKEN" in serialized
    assert "secret-value" not in serialized


def test_scan_is_deterministic() -> None:
    first = scan_repository(FIXTURES / "risky_repo").to_json()
    second = scan_repository(FIXTURES / "risky_repo").to_json()
    assert first == second


def test_sources_are_relative_and_cannot_escape_scan_root() -> None:
    manifest = scan_repository(FIXTURES / "risky_repo")
    assert manifest.findings
    assert all(not finding.source.startswith(("/", "\\")) for finding in manifest.findings)
    assert all(".." not in Path(finding.source).parts for finding in manifest.findings)


def test_repository_ignore_file_excludes_matching_fixtures(tmp_path: Path) -> None:
    ignored = tmp_path / "tests" / "fixtures" / ".mcp.json"
    ignored.parent.mkdir(parents=True)
    ignored.write_text('{"servers":{"risky":{"command":"bash"}}}', encoding="utf-8")
    (tmp_path / ".agentscopeignore").write_text("tests/fixtures/**\n", encoding="utf-8")
    assert not scan_repository(tmp_path).findings
