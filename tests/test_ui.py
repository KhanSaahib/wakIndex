"""Description: Browser UI tests for product identity and safe HTML rendering."""

from wakindex.branding import PRODUCT_NAME, PRODUCT_TAGLINE
from wakindex.policy import Policy
from wakindex.ui import _page


def test_policy_editor_displays_clean_product_heading_without_mascot() -> None:
    document = _page(["filesystem.read"], Policy()).decode("utf-8")

    assert PRODUCT_NAME in document
    assert PRODUCT_TAGLINE in document
    assert "mascot-name" not in document
    assert "PERMISSION SNAKE" not in document
    assert "<h1>Permission control center</h1>" in document
    assert "<title>wakindex · Permission control center</title>" in document
