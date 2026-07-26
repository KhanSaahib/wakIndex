# Contributing to AgentScope

## Description

This guide defines the minimum quality and security bar for contributions.

Start with an issue describing the permission format or policy behavior. Add a sanitized fixture and a failing test before implementation. Never add live secrets, execute scanned commands, or introduce network requirements into core scanning.

Run:

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
docker build --target test -t agentscope-test .
```

Changes should keep manifests deterministic and update the architecture document when adding a new permission category.

