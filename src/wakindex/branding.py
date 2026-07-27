"""Description: Canonical two-part wakindex banner shared by human-facing interfaces."""

PRODUCT_NAME = "wakindex"
PRODUCT_TAGLINE = "Inventory first. Grant less. Run safer."
PROJECT_DESCRIPTION = (
    "Inventory and policy-check permissions for AI agents, MCP servers, and skills."
)
COMMAND_GUIDE = """Quick start:
  wakindex init
  wakindex scan .
  wakindex check . --policy wakindex-policy.toml
  wakindex ui . --policy wakindex-policy.toml"""
PANEL_DIVIDER = "─" * 56

CLI_BANNER = """
██╗    ██╗ █████╗ ██╗  ██╗
██║    ██║██╔══██╗██║ ██╔╝
██║ █╗ ██║███████║█████╔╝
██║███╗██║██╔══██║██╔═██╗
╚███╔███╔╝██║  ██║██║  ██╗
 ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝

██╗███╗   ██╗██████╗ ███████╗██╗  ██╗
██║████╗  ██║██╔══██╗██╔════╝╚██╗██╔╝
██║██╔██╗ ██║██║  ██║█████╗   ╚███╔╝
██║██║╚██╗██║██║  ██║██╔══╝   ██╔██╗
██║██║ ╚████║██████╔╝███████╗██╔╝ ██╗
╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝
""".strip("\n")


def terminal_banner(width: int | None = None) -> str:
    """Return the complete startup panel with a final separating newline."""
    del width
    return f"{CLI_BANNER}\n\n{PROJECT_DESCRIPTION}\n\n{COMMAND_GUIDE}\n{PANEL_DIVIDER}\n"
