"""Description: Enterprise identity inventory tests for account, model, and access attribution."""

from pathlib import Path

import pytest

from wakindex.identity import build_identity_inventory, load_account_catalog
from wakindex.policy import Policy

FIXTURES = Path(__file__).parent / "fixtures"


def test_account_catalog_loads_business_context_without_serializing_homes() -> None:
    catalog = load_account_catalog(FIXTURES / "enterprise-accounts.toml")

    assert catalog.organization == "Example Corporation"
    assert catalog.environment == "production"
    assert [account.id for account in catalog.accounts] == ["alice", "bob"]
    assert catalog.accounts[0].provider_account("codex") == "openai-enterprise/alice"
    assert "home" not in catalog.accounts[0].as_dict()


def test_identity_inventory_maps_accounts_agents_models_and_access_privately() -> None:
    catalog = load_account_catalog(FIXTURES / "enterprise-accounts.toml")

    first = build_identity_inventory(
        FIXTURES / "safe_repo",
        catalog,
        platform_name="win32",
    )
    second = build_identity_inventory(
        FIXTURES / "safe_repo",
        catalog,
        platform_name="win32",
    )
    serialized = first.to_json()

    assert serialized == second.to_json()
    assert first.schema_version == "identity-1.0"
    assert first.workspace == "safe_repo"
    assert {account.id for account in first.accounts} == {"alice", "bob"}
    assert len({agent.id for agent in first.agents}) == len(first.agents)
    assert {record.account_id for record in first.access} == {"alice", "bob"}
    assert any(
        agent.account_id == "alice"
        and agent.provider == "codex"
        and agent.models == ("gpt-5.5",)
        and agent.model_provider == "openai"
        and agent.provider_account == "openai-enterprise/alice"
        for agent in first.agents
    )
    assert any(
        agent.account_id == "bob"
        and agent.provider == "codex"
        and agent.models == ("anthropic.claude-sonnet-4-6",)
        and agent.model_provider == "amazon-bedrock"
        and "aws-profile:corp-readonly" in agent.auth_contexts
        for agent in first.agents
    )
    assert any(
        agent.account_id == "bob"
        and agent.provider == "claude"
        and agent.models == ("claude-opus-4-6", "claude-sonnet-4-6")
        and agent.access_count == 0
        for agent in first.agents
    )
    assert any(
        agent.account_id == "bob"
        and agent.provider == "gemini"
        and "auth-selected:vertex-ai" in agent.auth_contexts
        for agent in first.agents
    )
    assert "FIXTURE_LITERAL_DO_NOT_EMIT" not in serialized
    assert "FIXTURE_HOOK_TOKEN_DO_NOT_EMIT" not in serialized
    assert str((FIXTURES / "user_home").resolve()) not in serialized
    assert str((FIXTURES / "user_home_bob").resolve()) not in serialized


def test_agent_ids_include_endpoint_and_workspace_context() -> None:
    catalog = load_account_catalog(FIXTURES / "enterprise-accounts.toml")

    first = build_identity_inventory(
        FIXTURES / "safe_repo",
        catalog,
        platform_name="win32",
        workspace_id="payments-api",
    )
    second = build_identity_inventory(
        FIXTURES / "safe_repo",
        catalog,
        platform_name="win32",
        workspace_id="analytics-api",
    )

    assert first.workspace == "payments-api"
    assert {agent.id for agent in first.agents}.isdisjoint({agent.id for agent in second.agents})


def test_identity_inventory_attaches_deterministic_policy_decisions() -> None:
    catalog = load_account_catalog(FIXTURES / "enterprise-accounts.toml")
    policy = Policy(
        default="allow",
        deny=("agent.unrestricted", "secrets.embedded"),
    )

    inventory = build_identity_inventory(
        FIXTURES / "safe_repo",
        catalog,
        policy=policy,
        platform_name="win32",
    )

    denied = [record for record in inventory.access if record.decision == "denied"]
    assert denied
    assert any(record.permission == "agent.unrestricted" for record in denied)
    assert all(record.reason == "explicitly denied" for record in denied)
    assert any(record.decision == "allowed" for record in inventory.access)


def test_duplicate_account_ids_fail_closed(tmp_path: Path) -> None:
    catalog = tmp_path / "accounts.toml"
    catalog.write_text(
        """
        # Description: Invalid duplicate account test catalog.
        version = 1
        [[accounts]]
        id = "same"
        display_name = "First"
        kind = "human"
        [[accounts]]
        id = "same"
        display_name = "Second"
        kind = "human"
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate account id"):
        load_account_catalog(catalog)
