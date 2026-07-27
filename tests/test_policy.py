"""Description: Policy tests proving deny precedence, wildcards, and default behavior."""

from pathlib import Path

from wakindex.models import Finding, Manifest
from wakindex.policy import Policy, evaluate


def finding(permission: str) -> Finding:
    return Finding(
        permission=permission,
        resource="fixture",
        source="fixture.json",
        evidence="test evidence",
        risk="medium",
    )


def test_explicit_deny_wins_over_wildcard_allow() -> None:
    policy = Policy(default="deny", allow=("filesystem.*",), deny=("filesystem.write",))
    result = evaluate(Manifest(root=".", findings=(finding("filesystem.write"),)), policy)
    assert not result.passed
    assert result.violations[0].reason == "explicitly denied"


def test_default_deny_rejects_unknown_permissions() -> None:
    result = evaluate(
        Manifest(root=".", findings=(finding("future.capability"),)),
        Policy(default="deny"),
    )
    assert not result.passed
    assert result.violations[0].reason == "not allowed"


def test_policy_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "policy.toml"
    original = Policy(
        default="deny",
        allow=("filesystem.read", "process.execute"),
        deny=("process.shell",),
    )
    original.write(path)
    assert Policy.load(path) == original
