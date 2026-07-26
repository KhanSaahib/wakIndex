"""Description: Loopback-only, no-dependency permission policy editor with radio controls."""

from __future__ import annotations

import html
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from agentscope.policy import Policy
from agentscope.scanners import scan_repository


def _page(permissions: list[str], policy: Policy, message: str = "") -> bytes:
    rows = []
    for permission in permissions:
        allowed = permission in policy.allow
        rows.append(
            "<tr><td><code>{0}</code></td>"
            '<td><label><input type="radio" name="permission:{0}" value="allow" {1}> Allow</label></td>'
            '<td><label><input type="radio" name="permission:{0}" value="deny" {2}> Deny</label></td></tr>'.format(
                html.escape(permission),
                "checked" if allowed else "",
                "" if allowed else "checked",
            )
        )
    document = f"""<!doctype html>
<!-- Description: Local AgentScope policy editor rendered without external assets. -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>AgentScope permissions</title>
<style>
:root{{font:16px system-ui;color:#17212b;background:#f4f7f9}}body{{max-width:900px;margin:3rem auto;padding:0 1rem}}
main{{background:white;border:1px solid #dbe3e8;border-radius:14px;padding:2rem;box-shadow:0 8px 30px #18304212}}
h1{{margin-top:0}}table{{width:100%;border-collapse:collapse}}td,th{{text-align:left;padding:.8rem;border-bottom:1px solid #e6ecef}}
button{{margin-top:1.3rem;background:#0969da;color:white;border:0;border-radius:8px;padding:.75rem 1.1rem;font-weight:700}}
.note{{color:#52606d}}.message{{background:#dafbe1;padding:.7rem;border-radius:8px}}
</style></head><body><main><h1>AgentScope permissions</h1>
<p class="note">Choose an explicit policy for every permission discovered locally. Deny is selected by default.</p>
{f'<p class="message">{html.escape(message)}</p>' if message else ""}
<form method="post"><table><thead><tr><th>Permission</th><th colspan="2">Decision</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table><button type="submit">Save policy</button></form>
</main></body></html>"""
    return document.encode("utf-8")


def serve(root: Path, policy_path: Path, port: int, open_browser: bool) -> int:
    """Serve the editor on loopback until interrupted."""
    permissions = sorted({item.permission for item in scan_repository(root).findings})
    policy = Policy.load(policy_path) if policy_path.exists() else Policy()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            body = _page(permissions, policy)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:  # noqa: N802
            nonlocal policy
            length = min(int(self.headers.get("Content-Length", "0")), 64_000)
            form = urllib.parse.parse_qs(self.rfile.read(length).decode("utf-8"))
            allowed = tuple(
                item for item in permissions if form.get(f"permission:{item}") == ["allow"]
            )
            denied = tuple(item for item in permissions if item not in allowed)
            policy = Policy(default="deny", allow=allowed, deny=denied)
            policy.write(policy_path)
            body = _page(permissions, policy, f"Saved {policy_path}")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"AgentScope policy editor: {url}")
    if open_browser:
        threading.Timer(0.2, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped AgentScope policy editor")
    finally:
        server.server_close()
    return 0
