"""Description: Browser UI tests for product identity and safe HTML rendering."""

import html

from agentscope.branding import ASCII_LOGO, MASCOT_NAME, PRODUCT_TAGLINE
from agentscope.policy import Policy
from agentscope.ui import _page


def test_policy_editor_displays_ascii_identity_and_heading() -> None:
    document = _page(["filesystem.read"], Policy()).decode("utf-8")

    assert ASCII_LOGO in html.unescape(document)
    assert MASCOT_NAME in document
    assert PRODUCT_TAGLINE in document
    assert "<h1>Permission control center</h1>" in document
    assert "<title>AgentScope · Permission control center</title>" in document
