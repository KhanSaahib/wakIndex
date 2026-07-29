"""Description: Deterministic account, agent, model, authentication, and access attribution."""

from __future__ import annotations

import getpass
import hashlib
import json
import platform
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from wakindex.environment import discover_user_configs, scan_environment
from wakindex.models import Finding, Manifest
from wakindex.policy import Policy, evaluate
from wakindex.scanners import discover_workspace_configs, scan_repository

ACCOUNT_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
ACCOUNT_FIELDS = {
    "id",
    "display_name",
    "kind",
    "home",
    "department",
    "endpoint",
    "environment",
    "tags",
    "provider_accounts",
}
ORGANIZATION_FIELDS = {"name", "environment"}
PRODUCT_NAMES = {
    "claude": "Claude Code",
    "claude-desktop": "Claude Desktop",
    "codex": "OpenAI Codex",
    "cursor": "Cursor",
    "gemini": "Gemini CLI",
    "github": "GitHub Actions",
    "mcp": "MCP client",
    "skill": "Agent skill",
    "vscode": "Visual Studio Code",
}


def _required_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _optional_string(value: Any, field_name: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    return value.strip()


def _string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ValueError(f"{field_name} must be an array of non-empty strings")
    return tuple(sorted(set(item.strip() for item in value)))


@dataclass(frozen=True, order=True)
class Account:
    """One explicitly scoped human, service, or shared account."""

    id: str
    display_name: str
    kind: str
    department: str = ""
    endpoint: str = ""
    environment: str = ""
    tags: tuple[str, ...] = ()
    provider_accounts: tuple[tuple[str, str], ...] = ()
    home: Path | None = field(default=None, compare=False, repr=False)

    def provider_account(self, provider: str) -> str:
        """Return an operator-provided provider account alias or an explicit gap."""
        accounts = dict(self.provider_accounts)
        if provider in accounts:
            return accounts[provider]
        if provider == "claude-desktop" and "claude" in accounts:
            return accounts["claude"]
        return "unmapped"

    def as_dict(self) -> dict[str, Any]:
        """Serialize business context without the profile scan boundary."""
        return {
            "id": self.id,
            "display_name": self.display_name,
            "kind": self.kind,
            "department": self.department,
            "endpoint": self.endpoint,
            "environment": self.environment,
            "tags": list(self.tags),
            "provider_accounts": dict(self.provider_accounts),
        }


@dataclass(frozen=True)
class AccountCatalog:
    """Trusted operator catalog controlling account discovery and business labels."""

    organization: str
    environment: str
    accounts: tuple[Account, ...]
    version: int = 1


@dataclass(frozen=True)
class ConfigIdentity:
    """Safe identity hints statically extracted from one agent configuration."""

    models: tuple[str, ...] = ()
    model_provider: str = ""
    auth_contexts: tuple[str, ...] = ()


@dataclass(frozen=True, order=True)
class AgentInstance:
    """One account-bound agent configuration surface."""

    id: str
    account_id: str
    provider: str
    product: str
    source: str
    scope: str
    models: tuple[str, ...]
    model_provider: str
    provider_account: str
    auth_contexts: tuple[str, ...]
    model_status: str
    access_count: int
    high_risk_count: int
    policy_denials: int

    def as_dict(self) -> dict[str, Any]:
        """Return the stable agent representation."""
        return {
            "id": self.id,
            "account_id": self.account_id,
            "provider": self.provider,
            "product": self.product,
            "source": self.source,
            "scope": self.scope,
            "models": list(self.models),
            "model_provider": self.model_provider,
            "provider_account": self.provider_account,
            "auth_contexts": list(self.auth_contexts),
            "model_status": self.model_status,
            "access_count": self.access_count,
            "high_risk_count": self.high_risk_count,
            "policy_denials": self.policy_denials,
        }


@dataclass(frozen=True, order=True)
class AccessRecord:
    """One normalized permission attributed to an account and agent instance."""

    account_id: str
    agent_id: str
    permission: str
    resource: str
    source: str
    evidence: str
    risk: str
    decision: str
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict, compare=False)

    def as_dict(self) -> dict[str, Any]:
        """Return the stable access-edge representation."""
        return {
            "account_id": self.account_id,
            "agent_id": self.agent_id,
            "permission": self.permission,
            "resource": self.resource,
            "source": self.source,
            "evidence": self.evidence,
            "risk": self.risk,
            "decision": self.decision,
            "reason": self.reason,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class IdentityInventory:
    """A deterministic account-to-agent-to-access inventory."""

    organization: str
    environment: str
    workspace: str
    accounts: tuple[Account, ...]
    agents: tuple[AgentInstance, ...]
    access: tuple[AccessRecord, ...]
    schema_version: str = "identity-1.0"

    def as_dict(self) -> dict[str, Any]:
        """Return the stable public identity inventory shape."""
        configured_models = {
            model for agent in self.agents for model in agent.models if agent.models
        }
        return {
            "schema_version": self.schema_version,
            "organization": self.organization,
            "environment": self.environment,
            "workspace": self.workspace,
            "summary": {
                "accounts": len(self.accounts),
                "agents": len(self.agents),
                "configured_models": len(configured_models),
                "access_records": len(self.access),
                "high_risk_access": sum(record.risk == "high" for record in self.access),
                "policy_denials": sum(record.decision == "denied" for record in self.access),
                "runtime_selected_models": sum(
                    agent.model_status == "runtime-selected" for agent in self.agents
                ),
                "unmapped_provider_accounts": sum(
                    agent.provider_account == "unmapped" for agent in self.agents
                ),
            },
            "accounts": [account.as_dict() for account in self.accounts],
            "agents": [agent.as_dict() for agent in self.agents],
            "access": [record.as_dict() for record in self.access],
        }

    def to_json(self) -> str:
        """Serialize with stable key and record ordering."""
        return json.dumps(self.as_dict(), indent=2, sort_keys=True) + "\n"


def load_account_catalog(path: Path) -> AccountCatalog:
    """Load and strictly validate an explicit version 1 account catalog."""
    with path.open("rb") as stream:
        data = tomllib.load(stream)
    unknown_top_level = set(data) - {"version", "organization", "accounts"}
    if unknown_top_level:
        raise ValueError(f"account catalog has unknown field: {sorted(unknown_top_level)[0]}")
    version = data.get("version", 1)
    if not isinstance(version, int) or isinstance(version, bool) or version != 1:
        raise ValueError(f"unsupported account catalog version: {version}")
    organization_data = data.get("organization", {})
    if not isinstance(organization_data, dict):
        raise ValueError("organization must be a table")
    unknown_organization = set(organization_data) - ORGANIZATION_FIELDS
    if unknown_organization:
        raise ValueError(f"organization has unknown field: {sorted(unknown_organization)[0]}")
    organization = _optional_string(
        organization_data.get("name", "Local environment"),
        "organization name",
    )
    environment = _optional_string(
        organization_data.get("environment", ""),
        "organization environment",
    )
    raw_accounts = data.get("accounts", [])
    if not isinstance(raw_accounts, list) or not raw_accounts:
        raise ValueError("account catalog must contain at least one [[accounts]] table")
    accounts: list[Account] = []
    for index, raw_account in enumerate(raw_accounts):
        label = f"account {index + 1}"
        if not isinstance(raw_account, dict):
            raise ValueError(f"{label} must be a table")
        unknown = set(raw_account) - ACCOUNT_FIELDS
        if unknown:
            raise ValueError(f"{label} has unknown field: {sorted(unknown)[0]}")
        account_id = _required_string(raw_account.get("id"), f"{label} id")
        if not ACCOUNT_ID_PATTERN.fullmatch(account_id):
            raise ValueError(
                f"{label} id must start with an alphanumeric character and contain only "
                "letters, numbers, '.', '_', or '-'"
            )
        kind = _required_string(raw_account.get("kind", "human"), f"{label} kind")
        if kind not in {"human", "service", "shared"}:
            raise ValueError(f"{label} kind must be 'human', 'service', or 'shared'")
        provider_accounts = raw_account.get("provider_accounts", {})
        if not isinstance(provider_accounts, dict) or not all(
            isinstance(key, str) and key and isinstance(value, str) and value
            for key, value in provider_accounts.items()
        ):
            raise ValueError(f"{label} provider_accounts must map strings to strings")
        home_value = raw_account.get("home")
        home: Path | None = None
        if home_value is not None:
            home_text = _required_string(home_value, f"{label} home")
            candidate = Path(home_text).expanduser()
            if not candidate.is_absolute():
                candidate = path.parent / candidate
            if candidate.is_symlink() or not candidate.is_dir():
                raise ValueError(f"{label} home is not a readable directory")
            home = candidate.resolve()
        account_environment = _optional_string(
            raw_account.get("environment", environment),
            f"{label} environment",
        )
        accounts.append(
            Account(
                id=account_id,
                display_name=_required_string(
                    raw_account.get("display_name", account_id),
                    f"{label} display_name",
                ),
                kind=kind,
                department=_optional_string(
                    raw_account.get("department"),
                    f"{label} department",
                ),
                endpoint=_optional_string(raw_account.get("endpoint"), f"{label} endpoint"),
                environment=account_environment,
                tags=_string_tuple(raw_account.get("tags"), f"{label} tags"),
                provider_accounts=tuple(sorted(provider_accounts.items())),
                home=home,
            )
        )
    ids = [account.id for account in accounts]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate account id")
    return AccountCatalog(
        organization=organization or "Local environment",
        environment=environment,
        accounts=tuple(sorted(accounts)),
        version=version,
    )


def current_account_catalog() -> AccountCatalog:
    """Build a current-user catalog without enumerating other local profiles."""
    username = getpass.getuser() or "current-user"
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", username).strip("-") or "current-user"
    endpoint = platform.node() or "local-endpoint"
    return AccountCatalog(
        organization="Local environment",
        environment="personal",
        accounts=(
            Account(
                id=normalized,
                display_name=username,
                kind="human",
                endpoint=endpoint,
                environment="personal",
                home=Path.home().resolve(),
            ),
        ),
    )


def _load_config(path: Path) -> dict[str, Any]:
    try:
        if path.suffix.lower() == ".toml":
            with path.open("rb") as stream:
                payload = tomllib.load(stream)
        else:
            payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, tomllib.TOMLDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _model_values(primary: Any, fallback: Any = None) -> tuple[str, ...]:
    values: list[str] = []
    if isinstance(primary, str) and primary:
        values.append(primary)
    if isinstance(fallback, str) and fallback:
        values.append(fallback)
    elif isinstance(fallback, list):
        values.extend(item for item in fallback if isinstance(item, str) and item)
    return tuple(dict.fromkeys(values))


def _inspect_config(path: Path, provider: str, scope: str) -> ConfigIdentity:
    payload = _load_config(path)
    if provider == "codex":
        agents = payload.get("agents", {})
        subagent_model = agents.get("default_subagent_model") if isinstance(agents, dict) else None
        models = _model_values(payload.get("model"), subagent_model)
        model_provider = payload.get("model_provider", "openai") if scope == "user" else ""
        if not isinstance(model_provider, str):
            model_provider = ""
        contexts: set[str] = set()
        providers = payload.get("model_providers", {})
        selected = providers.get(model_provider, {}) if isinstance(providers, dict) else {}
        if isinstance(selected, dict):
            env_key = selected.get("env_key")
            if isinstance(env_key, str) and env_key:
                contexts.add(f"environment:{env_key}")
            if selected.get("requires_openai_auth") is True:
                contexts.add("auth:openai-login")
            auth = selected.get("auth", {})
            if isinstance(auth, dict) and isinstance(auth.get("command"), str):
                contexts.add("auth-command:configured")
            aws = selected.get("aws", {})
            if isinstance(aws, dict) and isinstance(aws.get("profile"), str):
                contexts.add(f"aws-profile:{aws['profile']}")
        return ConfigIdentity(models, model_provider, tuple(sorted(contexts)))
    if provider == "claude":
        return ConfigIdentity(
            models=_model_values(payload.get("model"), payload.get("fallbackModel")),
            model_provider="anthropic",
        )
    if provider == "gemini":
        model = payload.get("model", {})
        model_name = model.get("name") if isinstance(model, dict) else model
        security = payload.get("security", {})
        auth = security.get("auth", {}) if isinstance(security, dict) else {}
        contexts: set[str] = set()
        if isinstance(auth, dict):
            selected = auth.get("selectedType")
            enforced = auth.get("enforcedType")
            if isinstance(selected, str) and selected:
                contexts.add(f"auth-selected:{selected}")
            if isinstance(enforced, str) and enforced:
                contexts.add(f"auth-enforced:{enforced}")
        selected_type = auth.get("selectedType") if isinstance(auth, dict) else None
        provider_name = "google-vertex" if selected_type == "vertex-ai" else "google-gemini"
        return ConfigIdentity(
            models=_model_values(model_name),
            model_provider=provider_name,
            auth_contexts=tuple(sorted(contexts)),
        )
    return ConfigIdentity()


def _agent_id(account: Account, workspace: str, provider: str, source: str) -> str:
    value = "\0".join(
        (
            account.endpoint or "unknown-endpoint",
            workspace,
            account.id,
            provider,
            source,
        )
    ).encode()
    return f"agent-{hashlib.sha256(value).hexdigest()[:16]}"


def _decision(finding: Finding, policy: Policy | None) -> tuple[str, str]:
    if policy is None:
        return "unreviewed", ""
    result = evaluate(Manifest(root=".", findings=(finding,)), policy)
    if result.passed:
        return "allowed", ""
    return "denied", result.violations[0].reason


def build_identity_inventory(
    workspace: Path,
    catalog: AccountCatalog,
    *,
    policy: Policy | None = None,
    platform_name: str | None = None,
    workspace_id: str | None = None,
) -> IdentityInventory:
    """Build deterministic identity and access relationships for explicit accounts."""
    workspace = workspace.resolve()
    if not workspace.is_dir():
        raise ValueError(f"workspace is not a directory: {workspace}")
    normalized_workspace_id = (workspace_id or workspace.name).strip()
    if not normalized_workspace_id:
        raise ValueError("workspace id must be a non-empty string")
    workspace_targets = discover_workspace_configs(workspace)
    workspace_manifest = scan_repository(workspace)
    agents: list[AgentInstance] = []
    access: list[AccessRecord] = []
    for account in catalog.accounts:
        user_targets = (
            discover_user_configs(account.home, platform_name=platform_name)
            if account.home is not None
            else ()
        )
        manifest = (
            scan_environment(
                workspace,
                account.home,
                platform_name=platform_name,
            )
            if account.home is not None
            else workspace_manifest
        )
        targets = [
            (target.source, target.provider, target.path, "workspace")
            for target in workspace_targets
        ]
        targets.extend(
            (target.source, target.provider, target.path, "user") for target in user_targets
        )
        findings_by_target: dict[tuple[str, str], list[Finding]] = {}
        for finding in manifest.findings:
            provider = str(finding.metadata.get("provider", "mcp"))
            findings_by_target.setdefault((finding.source, provider), []).append(finding)
        for source, provider, config_path, scope in sorted(targets):
            findings = tuple(sorted(findings_by_target.get((source, provider), [])))
            agent_id = _agent_id(account, normalized_workspace_id, provider, source)
            inspection = _inspect_config(config_path, provider, scope)
            agent_records: list[AccessRecord] = []
            for finding in findings:
                decision, reason = _decision(finding, policy)
                record = AccessRecord(
                    account_id=account.id,
                    agent_id=agent_id,
                    permission=finding.permission,
                    resource=finding.resource,
                    source=finding.source,
                    evidence=finding.evidence,
                    risk=finding.risk,
                    decision=decision,
                    reason=reason,
                    metadata=dict(sorted(finding.metadata.items())),
                )
                agent_records.append(record)
                access.append(record)
            agents.append(
                AgentInstance(
                    id=agent_id,
                    account_id=account.id,
                    provider=provider,
                    product=PRODUCT_NAMES.get(provider, provider.replace("-", " ").title()),
                    source=source,
                    scope=scope,
                    models=inspection.models,
                    model_provider=inspection.model_provider,
                    provider_account=account.provider_account(provider),
                    auth_contexts=inspection.auth_contexts,
                    model_status="configured" if inspection.models else "runtime-selected",
                    access_count=len(agent_records),
                    high_risk_count=sum(record.risk == "high" for record in agent_records),
                    policy_denials=sum(record.decision == "denied" for record in agent_records),
                )
            )
    return IdentityInventory(
        organization=catalog.organization,
        environment=catalog.environment,
        workspace=normalized_workspace_id,
        accounts=tuple(sorted(catalog.accounts)),
        agents=tuple(sorted(agents)),
        access=tuple(sorted(access)),
    )
