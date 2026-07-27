"""Description: TOML policy loading, writing, matching, and deterministic evaluation."""

from __future__ import annotations

import fnmatch
import tomllib
from dataclasses import dataclass
from pathlib import Path

from wakindex.models import Finding, Manifest


@dataclass(frozen=True)
class Policy:
    """An allow/deny policy with explicit deny precedence."""

    default: str = "deny"
    allow: tuple[str, ...] = ()
    deny: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.default not in {"allow", "deny"}:
            raise ValueError("policy default must be 'allow' or 'deny'")

    @classmethod
    def load(cls, path: Path) -> Policy:
        """Load a policy from TOML."""
        with path.open("rb") as stream:
            data = tomllib.load(stream)
        return cls(
            default=str(data.get("default", "deny")),
            allow=tuple(str(item) for item in data.get("allow", [])),
            deny=tuple(str(item) for item in data.get("deny", [])),
        )

    def write(self, path: Path) -> None:
        """Write TOML without an optional serialization dependency."""

        def array(values: tuple[str, ...]) -> str:
            escaped = [value.replace("\\", "\\\\").replace('"', '\\"') for value in values]
            return "[" + ", ".join(f'"{value}"' for value in escaped) + "]"

        content = (
            "# Description: wakindex permission policy; deny rules take precedence.\n"
            f'default = "{self.default}"\n'
            f"allow = {array(self.allow)}\n"
            f"deny = {array(self.deny)}\n"
        )
        path.write_text(content, encoding="utf-8")


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


def _matches(permission: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatchcase(permission, pattern) for pattern in patterns)


def evaluate(manifest: Manifest, policy: Policy) -> Evaluation:
    """Apply deny, allow, then default in that order."""
    violations: list[Violation] = []
    for finding in manifest.findings:
        if _matches(finding.permission, policy.deny):
            violations.append(Violation(finding, "explicitly denied"))
        elif _matches(finding.permission, policy.allow):
            continue
        elif policy.default == "deny":
            violations.append(Violation(finding, "not allowed"))
    return Evaluation(tuple(violations))
