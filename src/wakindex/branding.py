"""Description: Canonical two-part wakIndex banner shared by human-facing interfaces."""

PRODUCT_NAME = "wakIndex"
PRODUCT_TAGLINE = "Inventory first. Grant less. Run safer."

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
    """Return the canonical banner; width is retained for API compatibility."""
    del width
    return CLI_BANNER
