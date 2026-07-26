"""Description: SARIF 2.1 output adapter for GitHub code scanning and CI review."""

from __future__ import annotations

import json

from agentscope.policy import Evaluation


def render_sarif(evaluation: Evaluation) -> str:
    """Render policy violations as a minimal standards-compatible SARIF document."""
    rules = {}
    results = []
    for violation in evaluation.violations:
        finding = violation.finding
        rules[finding.permission] = {
            "id": finding.permission,
            "shortDescription": {"text": f"Agent permission: {finding.permission}"},
            "help": {"text": "Review the finding and explicitly allow or remove this permission."},
        }
        results.append(
            {
                "ruleId": finding.permission,
                "level": "error" if finding.risk == "high" else "warning",
                "message": {"text": f"{finding.evidence} ({violation.reason})"},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": finding.source},
                            "region": {"startLine": 1},
                        }
                    }
                ],
            }
        )
    payload = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "AgentScope",
                        "informationUri": "https://github.com/",
                        "rules": [rules[key] for key in sorted(rules)],
                    }
                },
                "results": results,
            }
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"
