"""Description: Shared text identity used by AgentScope's human-facing interfaces."""

ASCII_LOGO = r"""
    ___                    __  _____
   /   | ____ ____  ____  / /_/ ___/_________  ____  ___
  / /| |/ __ `/ _ \/ __ \/ __/\__ \/ ___/ __ \/ __ \/ _ \
 / ___ / /_/ /  __/ / / / /_ ___/ / /__/ /_/ / /_/ /  __/
/_/  |_\__, /\___/_/ /_/\__//____/\___/\____/ .___/\___/
      /____/                                 /_/
""".strip("\n")

PRODUCT_TAGLINE = "See every capability. Approve only what belongs."


def terminal_banner() -> str:
    """Return a compact title treatment for interactive terminal output."""
    rule = "=" * 64
    return f"{ASCII_LOGO}\n{rule}\n  {PRODUCT_TAGLINE}\n{rule}"
