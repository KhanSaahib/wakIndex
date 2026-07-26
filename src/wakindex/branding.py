"""Description: Responsive snake mascot and product identity for wakIndex interfaces."""

from __future__ import annotations

import shutil

PRODUCT_NAME = "wakIndex"
MASCOT_NAME = "WAK, THE PERMISSION SNAKE"
PRODUCT_TAGLINE = "Inventory first. Grant less. Run safer."

ASCII_LOGO = r"""
                            .-""-.
                          .'  _  _  '.
                         /   (o)(o)   \
                        |      /\      |       WAK SAYS:
                        |    \____/    |       CHECK IT BEFORE
                         \            /        YOU CONNECT IT.
                          '._      _.'
                             |    |
              __             |    |
          ___/ /_            |    |
         / _  __/            |    |             thumbs up
        / /_/ /              |    |                 /
        \____/==.             |    |                /
           \\   '._          |    |           _.-'
            \\     '-._______/      \_______.-'
             \\______________  /\  __________/
                         .---' /  \ '---.
                    _.-'      / /\ \      '-._
                 .-'_________/ /  \ \_________'-.
                /_____________/    \_____________\
""".strip("\n")

WORDMARK = r"""
 __        __    _    _  _____ _   _ ____  _____ __  __
 \ \      / /   / \  | |/ /_ _| \ | |  _ \| ____|\ \/ /
  \ \ /\ / /   / _ \ | ' / | ||  \| | | | |  _|   \  /
   \ V  V /   / ___ \| . \ | || |\  | |_| | |___  /  \
    \_/\_/   /_/   \_\_|\_\___|_| \_|____/|_____|/_/\_\
""".strip("\n")

COMPACT_LOGO = r"""
       /^\/^\
     _|__|  O|
\/  /~     \_/ \
 \____|________/
       \_______)   wakIndex
""".strip("\n")


def terminal_banner(width: int | None = None) -> str:
    """Return a terminal-safe full or compact mascot based on available width."""
    available = width if width is not None else shutil.get_terminal_size((80, 24)).columns
    if available < 72:
        identity = f"{COMPACT_LOGO}\n  {MASCOT_NAME}"
        rule_width = min(max(available, 36), 64)
    else:
        identity = f"{ASCII_LOGO}\n{WORDMARK}\n  {MASCOT_NAME}"
        rule_width = 64
    rule = "=" * rule_width
    return f"{identity}\n{rule}\n  {PRODUCT_TAGLINE}\n{rule}"
