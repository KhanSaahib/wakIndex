"""Description: Policy tests proving deny precedence, wildcards, and default behavior."""

from pathlib import Path

import pytest

from wakindex.models import Finding, Manifest
from wakindex.policy import Policy, Rule, evaluate


def finding(
    permission: str,
    *,
    resource: str = "fixture",
    source: str = "fixture.json",
    risk: str = "medium",
    metadata: dict[str, str] | None = None,
) -> Finding:
    return Finding(
        permission=permission,
        resource=resource,
        source=source,
        evidence="test evidence",
        risk=risk,
        metadata=metadata or {},
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


def test_scoped_rule_allows_only_the_approved_host_and_server() -> None:
    policy = Policy(
        default="deny",
        rules=(
            Rule(
                id="approved-corporate-mcp",
                effect="allow",
                permission="network.access",
                resource="corporate-*",
                source="user/codex/config.toml",
                metadata=(("host", "mcp.example.internal"), ("provider", "codex")),
                reason="Company-managed gateway",
            ),
        ),
    )
    approved = finding(
        "network.access",
        resource="corporate-tools",
        source="user/codex/config.toml",
        metadata={"host": "mcp.example.internal", "provider": "codex"},
    )
    unapproved = finding(
        "network.access",
        resource="corporate-tools",
        source="user/codex/config.toml",
        metadata={"host": "attacker.example", "provider": "codex"},
    )

    result = evaluate(Manifest(root=".", findings=(approved, unapproved)), policy)

    assert not result.passed
    assert result.violations == (result.violations[0],)
    assert result.violations[0].finding == unapproved
    assert result.violations[0].reason == "not allowed"


def test_scoped_deny_wins_over_legacy_and_scoped_allow() -> None:
    target = finding(
        "network.access",
        resource="production",
        metadata={"host": "prod.example.com"},
    )
    policy = Policy(
        default="allow",
        allow=("network.*",),
        rules=(
            Rule(
                id="allow-production",
                effect="allow",
                permission="network.access",
                metadata=(("host", "*.example.com"),),
            ),
            Rule(
                id="block-production",
                effect="deny",
                permission="network.access",
                metadata=(("host", "prod.example.com"),),
                reason="Production access requires a broker",
            ),
        ),
    )

    result = evaluate(Manifest(root=".", findings=(target,)), policy)

    assert result.violations[0].reason == (
        "denied by rule 'block-production': Production access requires a broker"
    )


def test_scoped_rules_round_trip_through_toml(tmp_path: Path) -> None:
    path = tmp_path / "policy.toml"
    original = Policy(
        default="deny",
        rules=(
            Rule(
                id="approved-host",
                effect="allow",
                permission="network.*",
                resource="corp-*",
                source="user/*",
                risk="medium",
                metadata=(("host", "*.example.internal"), ("provider", "codex")),
                reason="Managed service",
            ),
        ),
    )

    original.write(path)

    assert Policy.load(path) == original
    assert "[[rules]]" in path.read_text(encoding="utf-8")


def test_duplicate_rule_ids_are_rejected() -> None:
    duplicate = Rule(id="same", effect="allow", permission="network.access")

    with pytest.raises(ValueError, match="duplicate policy rule id"):
        Policy(rules=(duplicate, duplicate))
