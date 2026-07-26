"""Description: Stable normalized models for permission findings and manifests."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, order=True)
class Finding:
    """A permission observed in repository configuration."""

    permission: str
    resource: str
    source: str
    evidence: str
    risk: str
    metadata: dict[str, Any] = field(default_factory=dict, compare=False)

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return asdict(self)


@dataclass(frozen=True)
class Manifest:
    """A deterministic inventory for a scan root."""

    root: str
    findings: tuple[Finding, ...]
    schema_version: str = "1.0"

    def as_dict(self) -> dict[str, Any]:
        """Return the stable public manifest shape."""
        return {
            "schema_version": self.schema_version,
            "root": self.root,
            "summary": {
                "total": len(self.findings),
                "high": sum(item.risk == "high" for item in self.findings),
                "medium": sum(item.risk == "medium" for item in self.findings),
                "low": sum(item.risk == "low" for item in self.findings),
            },
            "findings": [item.as_dict() for item in self.findings],
        }

    def to_json(self) -> str:
        """Serialize with stable ordering for reviews and tests."""
        return json.dumps(self.as_dict(), indent=2, sort_keys=True) + "\n"
