"""Description: Known-path user configuration discovery and combined environment auditing."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from wakindex.models import Manifest
from wakindex.scanners import scan_config_file, scan_repository


@dataclass(frozen=True, order=True)
class ConfigTarget:
    """One explicitly known user configuration path with a stable public label."""

    source: str
    provider: str
    path: Path


def _candidate_targets(home: Path, platform_name: str) -> tuple[ConfigTarget, ...]:
    targets = [
        ConfigTarget("user/claude/mcp.json", "claude", home / ".claude.json"),
        ConfigTarget(
            "user/claude/settings.json",
            "claude",
            home / ".claude" / "settings.json",
        ),
        ConfigTarget(
            "user/codex/config.toml",
            "codex",
            home / ".codex" / "config.toml",
        ),
        ConfigTarget(
            "user/cursor/mcp.json",
            "cursor",
            home / ".cursor" / "mcp.json",
        ),
        ConfigTarget(
            "user/gemini/settings.json",
            "gemini",
            home / ".gemini" / "settings.json",
        ),
    ]
    if platform_name.startswith("win"):
        targets.extend(
            [
                ConfigTarget(
                    "user/claude-desktop/mcp.json",
                    "claude-desktop",
                    home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json",
                ),
                ConfigTarget(
                    "user/vscode/mcp.json",
                    "vscode",
                    home / "AppData" / "Roaming" / "Code" / "User" / "mcp.json",
                ),
            ]
        )
    elif platform_name == "darwin":
        targets.extend(
            [
                ConfigTarget(
                    "user/claude-desktop/mcp.json",
                    "claude-desktop",
                    home
                    / "Library"
                    / "Application Support"
                    / "Claude"
                    / "claude_desktop_config.json",
                ),
                ConfigTarget(
                    "user/vscode/mcp.json",
                    "vscode",
                    home / "Library" / "Application Support" / "Code" / "User" / "mcp.json",
                ),
            ]
        )
    else:
        targets.extend(
            [
                ConfigTarget(
                    "user/claude-desktop/mcp.json",
                    "claude-desktop",
                    home / ".config" / "Claude" / "claude_desktop_config.json",
                ),
                ConfigTarget(
                    "user/vscode/mcp.json",
                    "vscode",
                    home / ".config" / "Code" / "User" / "mcp.json",
                ),
            ]
        )
    return tuple(targets)


def discover_user_configs(
    home: Path,
    *,
    platform_name: str | None = None,
) -> tuple[ConfigTarget, ...]:
    """Return existing known user config files without traversing the profile."""
    resolved_home = home.resolve()
    found: list[ConfigTarget] = []
    seen: set[Path] = set()
    for target in _candidate_targets(resolved_home, platform_name or sys.platform):
        if target.path.is_symlink() or not target.path.is_file():
            continue
        try:
            resolved = target.path.resolve()
            resolved.relative_to(resolved_home)
        except (OSError, ValueError):
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        found.append(ConfigTarget(target.source, target.provider, resolved))
    return tuple(sorted(found))


def scan_environment(
    workspace: Path,
    home: Path,
    *,
    platform_name: str | None = None,
) -> Manifest:
    """Combine one workspace scan with an explicit known-path user audit."""
    workspace = workspace.resolve()
    home = home.resolve()
    findings = set(scan_repository(workspace).findings)
    for target in discover_user_configs(home, platform_name=platform_name):
        findings.update(
            scan_config_file(
                target.path,
                workspace_root=workspace,
                source=target.source,
                provider=target.provider,
                scope="user",
                redact_prefix=home,
            )
        )
    return Manifest(root=".", findings=tuple(sorted(findings)))
