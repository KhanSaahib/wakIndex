"""Description: Shared text identity used by AgentScope's human-facing interfaces."""

ASCII_LOGO = r"""
            .----------------.
         .-'   .----------.   '-.
        /     /  _      _  \     \
       |     |  (o)    (o)  |     |      A G E N T S C O P E
       |     |      /\       |     |      -------------------
       |     |   .-====-.    |     |      PERMISSION SENTINEL
        \     \  '------'   /     /
         '._   '----||----'   _.'
            '-------||-------'
                .---||---.
               /  ALLOW  \
              /____/\_____\
             [ DENY  ||  LOG ]
""".strip("\n")

MASCOT_NAME = "PERMISSION SENTINEL"
PRODUCT_TAGLINE = "See every capability. Approve only what belongs."


def terminal_banner() -> str:
    """Return a compact title treatment for interactive terminal output."""
    rule = "=" * 64
    return f"{ASCII_LOGO}\n{rule}\n  {PRODUCT_TAGLINE}\n{rule}"
