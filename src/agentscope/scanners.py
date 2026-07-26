"""Description: Safe static scanners for agent, MCP, skill, and workflow configuration."""

from __future__ import annotations

import fnmatch
import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from agentscope.models import Finding, Manifest

ENV_PATTERN = re.compile(
    r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)|%([A-Za-z_][A-Za-z0-9_]*)%"
)
SHELL_PATTERN = re.compile(r"(?:\b(?:bash|sh|zsh|cmd|powershell|pwsh)\b|[|;&]{1,2})", re.IGNORECASE)
NETWORK_PATTERN = re.compile(r"https?://", re.IGNORECASE)
SECRET_NAME_PATTERN = re.compile(
    r"(?:TOKEN|SECRET|PASSWORD|PASS|KEY|CREDENTIAL|DATABASE_URL)", re.IGNORECASE
)


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _finding(
    permission: str,
    resource: str,
    source: str,
    evidence: str,
    risk: str,
    **metadata: Any,
) -> Finding:
    return Finding(permission, resource, source, evidence[:240], risk, metadata)


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _environment_names(value: Any) -> set[str]:
    text = json.dumps(value, sort_keys=True)
    return {next(part for part in match.groups() if part) for match in ENV_PATTERN.finditer(text)}


def _scan_mcp(path: Path, root: Path, payload: dict[str, Any]) -> Iterable[Finding]:
    source = _relative(path, root)
    servers = payload.get("mcpServers", payload.get("servers", {}))
    if not isinstance(servers, dict):
        return
    for name, config in sorted(servers.items()):
        if not isinstance(config, dict):
            continue
        command = config.get("command")
        args = config.get("args", [])
        if isinstance(command, str):
            yield _finding(
                "process.execute",
                str(name),
                source,
                f"command: {command}",
                "medium",
                command=command,
            )
            command_line = " ".join([command, *[str(arg) for arg in args if isinstance(arg, str)]])
            if SHELL_PATTERN.search(command_line):
                yield _finding("process.shell", str(name), source, "shell-capable command", "high")
        url = config.get("url")
        if isinstance(url, str) and urlparse(url).scheme in {"http", "https"}:
            yield _finding(
                "network.access",
                str(name),
                source,
                f"remote MCP endpoint: {url}",
                "medium",
                host=urlparse(url).hostname,
            )
        for env_name in sorted(_environment_names(config)):
            yield _finding(
                "secrets.inherit",
                str(name),
                source,
                f"inherits environment variable: {env_name}",
                "high" if SECRET_NAME_PATTERN.search(env_name) else "medium",
                environment_variable=env_name,
            )
        for arg in args if isinstance(args, list) else []:
            if not isinstance(arg, str) or not (arg.startswith("../") or arg.startswith("..\\")):
                continue
            yield _finding(
                "filesystem.outside_workspace",
                str(name),
                source,
                f"relative path escapes workspace: {arg}",
                "high",
                path=arg,
            )


def _scan_agent_settings(path: Path, root: Path, payload: dict[str, Any]) -> Iterable[Finding]:
    source = _relative(path, root)
    if (
        payload.get("dangerouslySkipPermissions") is True
        or payload.get("permissionMode") == "bypassPermissions"
    ):
        yield _finding(
            "agent.unrestricted",
            "agent",
            source,
            "permission checks are bypassed",
            "high",
        )
    permissions = payload.get("permissions", {})
    if not isinstance(permissions, dict):
        return
    for tool in permissions.get("allow", []):
        if not isinstance(tool, str):
            continue
        lowered = tool.lower()
        if lowered.startswith("read"):
            permission, risk = "filesystem.read", "low"
        elif lowered.startswith(("write", "edit")):
            permission, risk = "filesystem.write", "medium"
        elif lowered.startswith("bash"):
            permission, risk = "process.shell", "high"
        else:
            permission, risk = "process.execute", "medium"
        yield _finding(permission, tool, source, f"allowed tool: {tool}", risk)


def _scan_skill(path: Path, root: Path) -> Iterable[Finding]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return
    source = _relative(path, root)
    lowered = text.lower()
    if re.search(r"allowed-tools\s*:[\s\S]{0,300}\b(?:bash|shell)\b", text, re.IGNORECASE):
        yield _finding(
            "process.shell", path.parent.name, source, "skill declares shell tool", "high"
        )
    if NETWORK_PATTERN.search(text):
        yield _finding(
            "network.access", path.parent.name, source, "skill references a network URL", "medium"
        )
    for env_name in sorted(_environment_names(text)):
        if SECRET_NAME_PATTERN.search(env_name):
            yield _finding(
                "secrets.inherit",
                path.parent.name,
                source,
                f"skill references environment variable: {env_name}",
                "high",
                environment_variable=env_name,
            )
    if "curl " in lowered and ("| bash" in lowered or "| sh" in lowered):
        yield _finding(
            "process.shell",
            path.parent.name,
            source,
            "skill pipes network content to a shell",
            "high",
        )


def _scan_workflow(path: Path, root: Path) -> Iterable[Finding]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return
    source = _relative(path, root)
    if re.search(r"(?m)^\s*permissions\s*:\s*write-all\s*(?:#.*)?$", text):
        yield _finding(
            "github.token",
            "GITHUB_TOKEN",
            source,
            "workflow requests write-all",
            "high",
            scope="write-all",
        )
    for match in re.finditer(r"(?m)^\s{0,8}([a-z-]+)\s*:\s*write\s*(?:#.*)?$", text):
        scope = match.group(1)
        if scope not in {"run", "uses", "name"}:
            yield _finding(
                "github.token",
                "GITHUB_TOKEN",
                source,
                f"workflow requests {scope}: write",
                "high",
                scope=scope,
            )


def _candidate_files(root: Path) -> Iterable[Path]:
    names = {".mcp.json", "mcp.json", "settings.json", "settings.local.json", "SKILL.md"}
    ignore_path = root / ".agentscopeignore"
    try:
        ignore_patterns = tuple(
            line.strip()
            for line in ignore_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    except OSError:
        ignore_patterns = ()
    for path in root.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            path.resolve().relative_to(root.resolve())
        except ValueError:
            continue
        relative = path.resolve().relative_to(root.resolve()).as_posix()
        if any(fnmatch.fnmatchcase(relative, pattern) for pattern in ignore_patterns):
            continue
        if path.name in names or (
            ".github" in path.parts
            and "workflows" in path.parts
            and path.suffix in {".yml", ".yaml"}
        ):
            yield path


def scan_repository(root: Path) -> Manifest:
    """Scan supported configuration beneath root without executing it."""
    root = root.resolve()
    findings: set[Finding] = set()
    for path in sorted(_candidate_files(root), key=lambda item: item.as_posix()):
        if path.name == "SKILL.md":
            findings.update(_scan_skill(path, root))
        elif ".github" in path.parts and "workflows" in path.parts:
            findings.update(_scan_workflow(path, root))
        else:
            payload = _load_json(path)
            if payload is None:
                continue
            if (
                path.name in {".mcp.json", "mcp.json"}
                or "servers" in payload
                or "mcpServers" in payload
            ):
                findings.update(_scan_mcp(path, root, payload))
            if path.name.startswith("settings"):
                findings.update(_scan_agent_settings(path, root, payload))
    ordered = tuple(sorted(findings))
    return Manifest(root=".", findings=ordered)
