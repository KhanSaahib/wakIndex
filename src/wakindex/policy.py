"""Description: TOML policy loading, scoped matching, writing, and deterministic evaluation."""

from __future__ import annotations

import fnmatch
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from wakindex.models import Finding, Manifest

RULE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
RULE_FIELDS = {"id", "effect", "permission", "resource", "source", "risk", "metadata", "reason"}


def _matches(value: str, pattern: str) -> bool:
    return fnmatch.fnmatchcase(value, pattern)


def _matches_any(value: str, patterns: tuple[str, ...]) -> bool:
    return any(_matches(value, pattern) for pattern in patterns)


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _string_array(data: dict[str, Any], field: str) -> tuple[str, ...]:
    value = data.get(field, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"policy {field} must be an array of strings")
    return tuple(value)


def _quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


@dataclass(frozen=True)
class Rule:
    """A named allow or deny selector for one class of findings."""

    id: str
    effect: str
    permission: str
    resource: str = "*"
    source: str = "*"
    risk: str = "*"
    metadata: tuple[tuple[str, str], ...] = ()
    reason: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not RULE_ID_PATTERN.fullmatch(self.id):
            raise ValueError(
                "policy rule id must start with an alphanumeric character and contain only "
                "letters, numbers, '.', '_', or '-'"
            )
        if not isinstance(self.effect, str) or self.effect not in {"allow", "deny"}:
            raise ValueError(f"policy rule '{self.id}' effect must be 'allow' or 'deny'")
        for field, value in (
            ("permission", self.permission),
            ("resource", self.resource),
            ("source", self.source),
            ("risk", self.risk),
        ):
            if not isinstance(value, str) or not value:
                raise ValueError(f"policy rule '{self.id}' {field} must not be empty")
        keys = [key for key, _ in self.metadata]
        if len(keys) != len(set(keys)):
            raise ValueError(f"policy rule '{self.id}' has duplicate metadata selectors")
        if any(
            not isinstance(key, str) or not key or not isinstance(value, str)
            for key, value in self.metadata
        ):
            raise ValueError(f"policy rule '{self.id}' metadata selectors must be strings")
        if not isinstance(self.reason, str):
            raise ValueError(f"policy rule '{self.id}' reason must be a string")

    def matches(self, finding: Finding) -> bool:
        """Return whether every rule selector matches a finding."""
        if not all(
            (
                _matches(finding.permission, self.permission),
                _matches(finding.resource, self.resource),
                _matches(finding.source, self.source),
                _matches(finding.risk, self.risk),
            )
        ):
            return False
        return all(
            key in finding.metadata and _matches(str(finding.metadata[key]), pattern)
            for key, pattern in self.metadata
        )


@dataclass(frozen=True)
class Policy:
    """A versioned policy with legacy patterns and scoped deny precedence."""

    version: int = 1
    default: str = "deny"
    allow: tuple[str, ...] = ()
    deny: tuple[str, ...] = ()
    rules: tuple[Rule, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.version, int) or isinstance(self.version, bool) or self.version != 1:
            raise ValueError(f"unsupported policy version: {self.version}")
        if not isinstance(self.default, str) or self.default not in {"allow", "deny"}:
            raise ValueError("policy default must be 'allow' or 'deny'")
        if any(not isinstance(item, str) or not item for item in (*self.allow, *self.deny)):
            raise ValueError("policy allow and deny entries must be non-empty strings")
        if any(not isinstance(rule, Rule) for rule in self.rules):
            raise ValueError("policy rules must contain Rule values")
        ids = [rule.id for rule in self.rules]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate policy rule id")

    @classmethod
    def load(cls, path: Path) -> Policy:
        """Load and validate a version 1 policy from TOML."""
        with path.open("rb") as stream:
            data = tomllib.load(stream)
        version = data.get("version", 1)
        if not isinstance(version, int) or isinstance(version, bool):
            raise ValueError("policy version must be an integer")
        raw_rules = data.get("rules", [])
        if not isinstance(raw_rules, list):
            raise ValueError("policy rules must be an array of tables")
        rules: list[Rule] = []
        for index, raw_rule in enumerate(raw_rules):
            label = f"policy rule {index + 1}"
            if not isinstance(raw_rule, dict):
                raise ValueError(f"{label} must be a table")
            unknown = set(raw_rule) - RULE_FIELDS
            if unknown:
                raise ValueError(f"{label} has unknown field: {sorted(unknown)[0]}")
            metadata = raw_rule.get("metadata", {})
            if not isinstance(metadata, dict):
                raise ValueError(f"{label} metadata must be a table")
            if not all(
                isinstance(key, str) and isinstance(value, str) for key, value in metadata.items()
            ):
                raise ValueError(f"{label} metadata selectors must be strings")
            reason = raw_rule.get("reason", "")
            if not isinstance(reason, str):
                raise ValueError(f"{label} reason must be a string")
            rules.append(
                Rule(
                    id=_string(raw_rule.get("id"), f"{label} id"),
                    effect=_string(raw_rule.get("effect"), f"{label} effect"),
                    permission=_string(raw_rule.get("permission", "*"), f"{label} permission"),
                    resource=_string(raw_rule.get("resource", "*"), f"{label} resource"),
                    source=_string(raw_rule.get("source", "*"), f"{label} source"),
                    risk=_string(raw_rule.get("risk", "*"), f"{label} risk"),
                    metadata=tuple(sorted(metadata.items())),
                    reason=reason,
                )
            )
        return cls(
            version=version,
            default=str(data.get("default", "deny")),
            allow=_string_array(data, "allow"),
            deny=_string_array(data, "deny"),
            rules=tuple(rules),
        )

    def write(self, path: Path) -> None:
        """Write stable TOML without an optional serialization dependency."""

        def array(values: tuple[str, ...]) -> str:
            return "[" + ", ".join(_quote(value) for value in values) + "]"

        lines = [
            "# Description: wakindex permission policy; scoped deny rules take precedence.",
            f"version = {self.version}",
            f"default = {_quote(self.default)}",
            f"allow = {array(self.allow)}",
            f"deny = {array(self.deny)}",
        ]
        for rule in self.rules:
            lines.extend(
                [
                    "",
                    "[[rules]]",
                    f"id = {_quote(rule.id)}",
                    f"effect = {_quote(rule.effect)}",
                    f"permission = {_quote(rule.permission)}",
                    f"resource = {_quote(rule.resource)}",
                    f"source = {_quote(rule.source)}",
                    f"risk = {_quote(rule.risk)}",
                ]
            )
            if rule.reason:
                lines.append(f"reason = {_quote(rule.reason)}")
            if rule.metadata:
                selectors = ", ".join(
                    f"{_quote(key)} = {_quote(value)}" for key, value in rule.metadata
                )
                lines.append(f"metadata = {{ {selectors} }}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class Violation:
    """A finding rejected by policy."""

    finding: Finding
    reason: str


@dataclass(frozen=True)
class Evaluation:
    """The complete result of evaluating a manifest."""

    violations: tuple[Violation, ...]

    @property
    def passed(self) -> bool:
        return not self.violations


def _matching_rule(finding: Finding, rules: tuple[Rule, ...], effect: str) -> Rule | None:
    return next((rule for rule in rules if rule.effect == effect and rule.matches(finding)), None)


def evaluate(manifest: Manifest, policy: Policy) -> Evaluation:
    """Apply all denies, all allows, then the default in that order."""
    violations: list[Violation] = []
    for finding in manifest.findings:
        if _matches_any(finding.permission, policy.deny):
            violations.append(Violation(finding, "explicitly denied"))
            continue
        deny_rule = _matching_rule(finding, policy.rules, "deny")
        if deny_rule is not None:
            reason = f"denied by rule '{deny_rule.id}'"
            if deny_rule.reason:
                reason += f": {deny_rule.reason}"
            violations.append(Violation(finding, reason))
            continue
        if _matches_any(finding.permission, policy.allow):
            continue
        if _matching_rule(finding, policy.rules, "allow") is not None:
            continue
        if policy.default == "deny":
            violations.append(Violation(finding, "not allowed"))
    return Evaluation(tuple(violations))
