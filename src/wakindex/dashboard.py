"""Description: Secure loopback enterprise dashboard for identity and access inventories."""

from __future__ import annotations

import base64
import hashlib
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from wakindex.identity import IdentityInventory

SECURITY_HEADERS = {
    "Cache-Control": "no-store",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}


def _content_hash(content: str) -> str:
    digest = hashlib.sha256(content.encode()).digest()
    return base64.b64encode(digest).decode()


def _security_headers(dashboard_body: bytes) -> dict[str, str]:
    document = dashboard_body.decode("utf-8")
    style = document.partition("<style>")[2].partition("</style>")[0]
    script = document.partition("<script>")[2].partition("</script>")[0]
    headers = dict(SECURITY_HEADERS)
    headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        f"style-src 'sha256-{_content_hash(style)}'; "
        f"script-src 'sha256-{_content_hash(script)}'; "
        "connect-src 'self'; img-src 'none'; object-src 'none'; base-uri 'none'; "
        "frame-ancestors 'none'; form-action 'none'"
    )
    return headers


def render_dashboard_shell() -> bytes:
    """Return a fixed shell that fetches untrusted inventory through same-origin JSON."""
    document = """<!doctype html>
<!-- Description: Local wakindex identity dashboard rendered without external assets. -->
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>wakindex · Identity & access posture</title>
<style>
:root{font:15px Inter,ui-sans-serif,system-ui,-apple-system,sans-serif;color:#17212b;background:#f4f6f8;--ink:#0c1d2a;--muted:#5c6975;--line:#dfe5e9;--mint:#16b886;--navy:#071b2b;--red:#c92a2a;--amber:#b26800;--green:#087f5b}
*{box-sizing:border-box}body{margin:0;min-width:320px}.topbar{background:var(--navy);color:white;border-bottom:4px solid var(--mint)}.topbar-inner{max-width:1480px;margin:auto;padding:22px 28px;display:flex;align-items:center;justify-content:space-between;gap:24px}.brand{margin:0;color:#72f1c5;font-weight:850;font-size:1.65rem;letter-spacing:-.04em}.eyebrow{margin:0 0 5px;color:#93aaa4;font-size:.72rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase}.topbar h1{margin:0;font-size:1.5rem;letter-spacing:-.02em}.export{color:#d8fff1;text-decoration:none;border:1px solid #3a685b;border-radius:9px;padding:9px 13px;font-weight:750}.layout{max-width:1480px;margin:auto;padding:28px}.context{display:flex;justify-content:space-between;align-items:end;gap:24px;margin-bottom:20px}.context h2{margin:0;font-size:1.45rem}.context p{margin:6px 0 0;color:var(--muted)}.status{font-size:.8rem;background:#e6fcf5;color:#087f5b;border:1px solid #b2f2df;border-radius:999px;padding:6px 10px;font-weight:800}.metrics{display:grid;grid-template-columns:repeat(6,minmax(130px,1fr));gap:12px;margin-bottom:20px}.metric,.panel{background:white;border:1px solid var(--line);border-radius:14px;box-shadow:0 5px 18px #1830420a}.metric{padding:17px}.metric-label{color:var(--muted);font-size:.74rem;font-weight:800;text-transform:uppercase;letter-spacing:.08em}.metric-value{display:block;margin-top:8px;font-size:1.75rem;font-weight:850;color:var(--ink)}.metric.danger .metric-value{color:var(--red)}.coverage{padding:15px 18px;margin-bottom:20px;display:flex;gap:12px;align-items:flex-start;border-left:4px solid var(--amber)}.coverage strong{display:block}.coverage p{margin:4px 0 0;color:var(--muted)}.panel{padding:20px;margin-bottom:20px}.panel-header{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:14px}.panel h3{margin:0;font-size:1.05rem}.panel-note{color:var(--muted);font-size:.83rem}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:10px}table{width:100%;border-collapse:collapse;min-width:900px}th,td{text-align:left;padding:11px 12px;border-bottom:1px solid #edf0f2;vertical-align:top}th{position:sticky;top:0;background:#f8fafb;color:#4d5b66;font-size:.72rem;letter-spacing:.06em;text-transform:uppercase}tbody tr:last-child td{border-bottom:0}tbody tr:hover{background:#f8fbfa}.primary{font-weight:750;color:var(--ink)}.secondary{display:block;margin-top:3px;color:var(--muted);font-size:.78rem}.pill{display:inline-flex;align-items:center;border-radius:999px;padding:4px 8px;font-size:.72rem;font-weight:800;background:#e9ecef;color:#43515c}.pill.high,.pill.denied{background:#fff0f0;color:var(--red)}.pill.medium,.pill.unreviewed{background:#fff4e6;color:var(--amber)}.pill.low,.pill.allowed,.pill.configured{background:#e6fcf5;color:var(--green)}.pill.runtime-selected{background:#edf2ff;color:#364fc7}.filters{display:grid;grid-template-columns:minmax(220px,2fr) repeat(3,minmax(140px,1fr));gap:10px;margin-bottom:14px}input,select{width:100%;border:1px solid #cad3d9;border-radius:8px;background:white;padding:10px;color:var(--ink)}input:focus,select:focus{outline:3px solid #16b88633;border-color:var(--mint)}.matrix{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:12px}.matrix-card{border:1px solid var(--line);border-radius:10px;padding:14px}.matrix-card h4{margin:0}.matrix-card p{margin:4px 0 10px;color:var(--muted);font-size:.8rem}.permission-list{display:flex;gap:6px;flex-wrap:wrap}.empty{padding:26px;text-align:center;color:var(--muted)}.loading{padding:50px;text-align:center;color:var(--muted)}@media(max-width:1050px){.metrics{grid-template-columns:repeat(3,1fr)}.filters{grid-template-columns:1fr 1fr}}@media(max-width:650px){.layout,.topbar-inner{padding:18px}.topbar-inner,.context{align-items:flex-start;flex-direction:column}.metrics{grid-template-columns:1fr 1fr}.filters{grid-template-columns:1fr}.export{width:100%;text-align:center}}
</style>
</head>
<body>
<header class="topbar"><div class="topbar-inner">
<div><p class="brand">wakindex</p></div>
<div><p class="eyebrow">Enterprise security inventory</p><h1>Identity &amp; access posture</h1></div>
<a class="export" href="/inventory.json" download="wakindex-identity-access.json">Export JSON</a>
</div></header>
<main class="layout">
<section class="context"><div><h2 id="organization">Loading inventory…</h2><p id="environment"></p></div><span class="status">Static · local · read-only</span></section>
<section class="metrics" aria-label="Inventory summary">
<article class="metric"><span class="metric-label">Accounts</span><strong class="metric-value" id="metric-accounts">—</strong></article>
<article class="metric"><span class="metric-label">Agent surfaces</span><strong class="metric-value" id="metric-agents">—</strong></article>
<article class="metric"><span class="metric-label">Configured models</span><strong class="metric-value" id="metric-models">—</strong></article>
<article class="metric"><span class="metric-label">Access records</span><strong class="metric-value" id="metric-access">—</strong></article>
<article class="metric danger"><span class="metric-label">High risk</span><strong class="metric-value" id="metric-high">—</strong></article>
<article class="metric danger"><span class="metric-label">Policy denials</span><strong class="metric-value" id="metric-denials">—</strong></article>
</section>
<section class="panel coverage" aria-live="polite"><div aria-hidden="true">△</div><div><strong>Attribution coverage</strong><p id="coverage-text">Loading coverage status…</p></div></section>
<section class="panel">
<div class="panel-header"><div><h3>Identity map</h3><span class="panel-note">Account → agent surface → configured model → provider identity</span></div></div>
<div class="table-wrap"><table><thead><tr><th>Account</th><th>Endpoint</th><th>Agent</th><th>Configured model</th><th>Provider account</th><th>Auth context</th><th>Access</th><th>Posture</th></tr></thead><tbody id="identity-body"><tr><td colspan="8" class="loading">Loading…</td></tr></tbody></table></div>
</section>
<section class="panel">
<div class="panel-header"><div><h3>Permission matrix</h3><span class="panel-note">Effective static capabilities grouped by account and agent</span></div></div>
<div class="matrix" id="permission-matrix"><p class="loading">Loading…</p></div>
</section>
<section class="panel">
<div class="panel-header"><div><h3>Access explorer</h3><span class="panel-note" id="result-count">Loading records…</span></div></div>
<div class="filters">
<input id="access-search" type="search" placeholder="Search permission, resource, source, model…" aria-label="Search access records">
<select id="account-filter" aria-label="Filter by account"><option value="">All accounts</option></select>
<select id="provider-filter" aria-label="Filter by provider"><option value="">All providers</option></select>
<select id="risk-filter" aria-label="Filter by risk"><option value="">All risks</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select>
</div>
<div class="table-wrap"><table id="access-table"><thead><tr><th>Risk</th><th>Decision</th><th>Account</th><th>Agent / model</th><th>Permission</th><th>Resource</th><th>Source / evidence</th></tr></thead><tbody id="access-body"><tr><td colspan="7" class="loading">Loading…</td></tr></tbody></table></div>
</section>
</main>
<script>
"use strict";
const state={inventory:null,accounts:new Map(),agents:new Map()};
const byId=id=>document.getElementById(id);
const text=(tag,value,className="")=>{const node=document.createElement(tag);node.textContent=value||"—";if(className)node.className=className;return node};
const addCell=(row,primary,secondary="")=>{const cell=document.createElement("td");cell.append(text("span",primary,"primary"));if(secondary)cell.append(text("span",secondary,"secondary"));row.append(cell)};
const pill=(value,kind=value)=>text("span",value,`pill ${kind}`);
const modelLabel=agent=>agent.models.length?agent.models.join(", "):"Runtime / default";
function fillSelect(id,values){const select=byId(id);values.forEach(value=>{const option=document.createElement("option");option.value=value;option.textContent=value;select.append(option)})}
function renderSummary(data){const s=data.summary;byId("organization").textContent=data.organization;const environment=data.environment||"not specified";byId("environment").textContent=`Environment: ${environment} · Workspace: ${data.workspace}`;byId("metric-accounts").textContent=s.accounts;byId("metric-agents").textContent=s.agents;byId("metric-models").textContent=s.configured_models;byId("metric-access").textContent=s.access_records;byId("metric-high").textContent=s.high_risk_access;byId("metric-denials").textContent=s.policy_denials;byId("coverage-text").textContent=`${s.runtime_selected_models} agent surface(s) use a runtime/default model; ${s.unmapped_provider_accounts} provider account mapping(s) are unresolved.`}
function renderIdentities(){const body=byId("identity-body");body.replaceChildren();state.inventory.agents.forEach(agent=>{const account=state.accounts.get(agent.account_id);const row=document.createElement("tr");addCell(row,account.display_name,`${account.id} · ${account.department||account.kind}`);addCell(row,account.endpoint||"Not supplied",account.environment);addCell(row,agent.product,`${agent.provider} · ${agent.scope}`);const modelCell=document.createElement("td");modelCell.append(text("span",modelLabel(agent),"primary"));modelCell.append(document.createElement("br"));modelCell.append(pill(agent.model_status,agent.model_status));if(agent.model_provider)modelCell.append(text("span",agent.model_provider,"secondary"));row.append(modelCell);addCell(row,agent.provider_account,agent.provider_account==="unmapped"?"Operator mapping needed":"Operator supplied");addCell(row,agent.auth_contexts.join(", ")||"Not observed");addCell(row,String(agent.access_count),`${agent.high_risk_count} high risk`);const posture=document.createElement("td");posture.append(agent.policy_denials?pill(`${agent.policy_denials} denied`,"denied"):pill("No denials","allowed"));row.append(posture);body.append(row)});if(!body.children.length){const row=document.createElement("tr");const cell=text("td","No agent configurations found.","empty");cell.colSpan=8;row.append(cell);body.append(row)}}
function renderMatrix(){const matrix=byId("permission-matrix");matrix.replaceChildren();state.inventory.agents.forEach(agent=>{const records=state.inventory.access.filter(record=>record.agent_id===agent.id);if(!records.length)return;const account=state.accounts.get(agent.account_id);const card=document.createElement("article");card.className="matrix-card";card.append(text("h4",`${account.id} · ${agent.product}`));card.append(text("p",`${modelLabel(agent)} · ${agent.source}`));const permissions=document.createElement("div");permissions.className="permission-list";[...new Set(records.map(record=>record.permission))].sort().forEach(permission=>permissions.append(pill(permission)));card.append(permissions);matrix.append(card)});if(!matrix.children.length)matrix.append(text("p","No permissions discovered.","empty"))}
function renderAccess(){const query=byId("access-search").value.toLowerCase();const accountFilter=byId("account-filter").value;const providerFilter=byId("provider-filter").value;const riskFilter=byId("risk-filter").value;const records=state.inventory.access.filter(record=>{const agent=state.agents.get(record.agent_id);const haystack=[record.permission,record.resource,record.source,record.evidence,record.account_id,agent.product,modelLabel(agent)].join(" ").toLowerCase();return(!query||haystack.includes(query))&&(!accountFilter||record.account_id===accountFilter)&&(!providerFilter||agent.provider===providerFilter)&&(!riskFilter||record.risk===riskFilter)});const body=byId("access-body");body.replaceChildren();records.forEach(record=>{const agent=state.agents.get(record.agent_id);const account=state.accounts.get(record.account_id);const row=document.createElement("tr");const risk=document.createElement("td");risk.append(pill(record.risk,record.risk));row.append(risk);const decision=document.createElement("td");decision.append(pill(record.decision,record.decision));if(record.reason)decision.append(text("span",record.reason,"secondary"));row.append(decision);addCell(row,account.display_name,account.id);addCell(row,agent.product,modelLabel(agent));addCell(row,record.permission);addCell(row,record.resource);addCell(row,record.source,record.evidence);body.append(row)});if(!records.length){const row=document.createElement("tr");const cell=text("td","No access records match these filters.","empty");cell.colSpan=7;row.append(cell);body.append(row)}byId("result-count").textContent=`${records.length} of ${state.inventory.access.length} records`}
async function start(){try{const response=await fetch("/inventory.json",{cache:"no-store"});if(!response.ok)throw new Error(`HTTP ${response.status}`);state.inventory=await response.json();state.inventory.accounts.forEach(account=>state.accounts.set(account.id,account));state.inventory.agents.forEach(agent=>state.agents.set(agent.id,agent));fillSelect("account-filter",state.inventory.accounts.map(account=>account.id));fillSelect("provider-filter",[...new Set(state.inventory.agents.map(agent=>agent.provider))].sort());renderSummary(state.inventory);renderIdentities();renderMatrix();renderAccess();["access-search","account-filter","provider-filter","risk-filter"].forEach(id=>byId(id).addEventListener("input",renderAccess))}catch(error){byId("organization").textContent="Inventory unavailable";byId("environment").textContent=error.message}}
start();
</script>
</body>
</html>"""
    return document.encode("utf-8")


def create_dashboard_server(
    inventory: IdentityInventory,
    *,
    port: int,
) -> ThreadingHTTPServer:
    """Create a loopback server for one immutable inventory snapshot."""
    inventory_body = inventory.to_json().encode("utf-8")
    dashboard_body = render_dashboard_shell()
    security_headers = _security_headers(dashboard_body)

    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            for name, value in security_headers.items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/":
                self._send(200, "text/html; charset=utf-8", dashboard_body)
                return
            if self.path == "/inventory.json":
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(inventory_body)))
                self.send_header(
                    "Content-Disposition",
                    'attachment; filename="wakindex-identity-access.json"',
                )
                for name, value in security_headers.items():
                    self.send_header(name, value)
                self.end_headers()
                self.wfile.write(inventory_body)
                return
            self._send(404, "text/plain; charset=utf-8", b"Not found\n")

        def log_message(self, format: str, *args: object) -> None:
            return

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve_dashboard(
    inventory: IdentityInventory,
    *,
    port: int,
    open_browser: bool,
) -> int:
    """Serve a read-only identity dashboard on loopback until interrupted."""
    server = create_dashboard_server(inventory, port=port)
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"Identity dashboard: {url}")
    if open_browser:
        threading.Timer(0.2, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped wakindex identity dashboard")
    finally:
        server.server_close()
    return 0
