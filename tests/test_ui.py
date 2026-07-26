"""Description: Browser UI tests for product identity and safe HTML rendering."""

import html

from wakindex.branding import ASCII_LOGO, MASCOT_NAME, PRODUCT_TAGLINE
from wakindex.policy import Policy
from wakindex.ui import _page


def test_policy_editor_displays_ascii_identity_and_heading() -> None:
    document = _page(["filesystem.read"], Policy()).decode("utf-8")

    assert ASCII_LOGO in html.unescape(document)
    assert MASCOT_NAME in document
    assert PRODUCT_TAGLINE in document
    assert "<h1>Permission control center</h1>" in document
    assert "<title>wakIndex · Permission control center</title>" in document
