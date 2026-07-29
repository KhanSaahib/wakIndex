"""Description: Enterprise dashboard tests for safe rendering, export, and HTTP protections."""

import json
import threading
import urllib.request
from pathlib import Path

from wakindex.dashboard import create_dashboard_server, render_dashboard_shell
from wakindex.identity import build_identity_inventory, load_account_catalog

FIXTURES = Path(__file__).parent / "fixtures"


def _inventory():
    return build_identity_inventory(
        FIXTURES / "safe_repo",
        load_account_catalog(FIXTURES / "enterprise-accounts.toml"),
        platform_name="win32",
    )


def test_dashboard_shell_is_enterprise_ready_and_does_not_embed_untrusted_values() -> None:
    document = render_dashboard_shell().decode("utf-8")

    assert "<title>wakindex · Identity & access posture</title>" in document
    assert "Identity &amp; access posture" in document
    assert 'id="account-filter"' in document
    assert 'id="provider-filter"' in document
    assert 'id="risk-filter"' in document
    assert 'id="access-table"' in document
    assert "/inventory.json" in document
    assert "<script>alert('x')</script>" not in document
    assert "https://" not in document


def test_dashboard_serves_same_origin_inventory_with_security_headers() -> None:
    inventory = _inventory()
    server = create_dashboard_server(inventory, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        with urllib.request.urlopen(base_url, timeout=2) as response:  # noqa: S310
            document = response.read().decode("utf-8")
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            assert response.headers["X-Frame-Options"] == "DENY"
            assert "default-src 'self'" in response.headers["Content-Security-Policy"]
            assert "'unsafe-inline'" not in response.headers["Content-Security-Policy"]
            assert "script-src 'sha256-" in response.headers["Content-Security-Policy"]
            assert response.headers["Cache-Control"] == "no-store"
            assert "Identity &amp; access posture" in document

        with urllib.request.urlopen(f"{base_url}/inventory.json", timeout=2) as response:  # noqa: S310
            payload = json.loads(response.read())
            assert response.headers["Content-Type"] == "application/json; charset=utf-8"
            assert payload["schema_version"] == "identity-1.0"
            assert payload["summary"]["accounts"] == 2
            assert any(
                account["display_name"] == "Bob <script>alert('x')</script>"
                for account in payload["accounts"]
            )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
