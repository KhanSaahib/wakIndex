"""Description: Integration tests for privacy-preserving user environment discovery."""

from pathlib import Path

from wakindex.environment import discover_user_configs, scan_environment

FIXTURES = Path(__file__).parent / "fixtures"


def test_windows_user_discovery_covers_supported_personal_agent_configs() -> None:
    targets = discover_user_configs(FIXTURES / "user_home", platform_name="win32")

    assert {target.provider for target in targets} == {
        "claude",
        "claude-desktop",
        "codex",
        "cursor",
        "gemini",
        "vscode",
    }
    assert all(target.path.is_file() for target in targets)
    assert all(target.source.startswith("user/") for target in targets)


def test_environment_audit_is_deterministic_private_and_security_relevant() -> None:
    workspace = FIXTURES / "safe_repo"
    home = FIXTURES / "user_home"

    first = scan_environment(workspace, home, platform_name="win32")
    second = scan_environment(workspace, home, platform_name="win32")
    serialized = first.to_json()

    assert first.to_json() == second.to_json()
    assert {"agent.auto_approve", "agent.unrestricted", "secrets.embedded"} <= {
        finding.permission for finding in first.findings
    }
    assert {
        "claude",
        "claude-desktop",
        "codex",
        "cursor",
        "gemini",
        "vscode",
    } <= {str(finding.metadata["provider"]) for finding in first.findings}
    assert all(finding.metadata["scope"] in {"user", "workspace"} for finding in first.findings)
    assert "user/codex/config.toml" in {finding.source for finding in first.findings}
    assert "CORP_MCP_TOKEN" in serialized
    assert "FIXTURE_LITERAL_DO_NOT_EMIT" not in serialized
    assert "FIXTURE_HOOK_TOKEN_DO_NOT_EMIT" not in serialized
    assert str(home.resolve()) not in serialized
    assert any(
        finding.permission == "process.execute"
        and finding.metadata.get("provider") == "claude"
        and finding.metadata.get("command") == "python"
        for finding in first.findings
    )
    assert any(
        finding.permission == "secrets.embedded"
        and finding.metadata.get("provider") == "claude"
        and finding.metadata.get("field") == "ANTHROPIC_AUTH_TOKEN"
        for finding in first.findings
    )


def test_environment_audit_does_not_scan_arbitrary_home_files(tmp_path: Path) -> None:
    home = tmp_path / "profile"
    credentials = home / ".aws" / "credentials"
    credentials.parent.mkdir(parents=True)
    credentials.write_text("UNRELATED_HOME_SECRET=DO_NOT_READ_OR_EMIT\n", encoding="utf-8")

    manifest = scan_environment(FIXTURES / "safe_repo", home, platform_name="linux")

    assert "UNRELATED_HOME_SECRET" not in manifest.to_json()


def test_codex_workspace_sandbox_access_is_inventoryable() -> None:
    manifest = scan_environment(
        FIXTURES / "codex_workspace",
        FIXTURES / "empty_home",
        platform_name="linux",
    )

    assert {
        "filesystem.outside_workspace",
        "filesystem.write",
        "network.access",
    } <= {finding.permission for finding in manifest.findings}
    assert all(finding.metadata["provider"] == "codex" for finding in manifest.findings)
