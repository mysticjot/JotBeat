"""tools/ui_server.py — `jotbeat ui`: the human's settings panel
(HANDOFF-PHASE3 Addendum C).

Stdlib only (http.server + one self-contained HTML page, vanilla JS).
Bound to 127.0.0.1 ONLY; non-loopback clients are refused. All reads/writes
go through tools/keys.py and tools/routing.py — the same writer modules the
CLI uses. Key values are accepted via POST but NEVER rendered back; responses
carry char counts, not values.
"""

from __future__ import annotations

import json
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LOOPBACK = ("127.0.0.1", "::1", "localhost")


def is_loopback(addr: str) -> bool:
    return addr in LOOPBACK


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>JotBeat Studio — Settings</title>
<style>
  body { font-family: system-ui, sans-serif; background:#14171c; color:#dde3ea;
         max-width: 960px; margin: 24px auto; padding: 0 16px; }
  h1 { font-size: 20px; } h2 { font-size: 16px; margin-top: 32px;
       border-bottom: 1px solid #2a313a; padding-bottom: 6px; }
  table { border-collapse: collapse; width: 100%; font-size: 13px; }
  th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid #232a33; }
  th { color: #8b96a3; font-weight: 600; }
  input, select, textarea { background:#1c2129; color:#dde3ea;
       border:1px solid #39424e; border-radius:4px; padding:4px 6px; font-size:13px; }
  button { background:#2d6cdf; color:#fff; border:0; border-radius:4px;
           padding:5px 10px; font-size:13px; cursor:pointer; }
  button.sec { background:#39424e; }
  .dot { display:inline-block; width:9px; height:9px; border-radius:50%;
         background:#5a6470; margin-right:6px; }
  .dot.on { background:#3fb950; }
  .muted { color:#8b96a3; font-size:12px; }
  .warn { color:#d29922; font-size:12px; }
  .ok { color:#3fb950; } .fail { color:#f85149; }
  #msg { margin-top:12px; font-size:13px; min-height:18px; }
</style>
</head>
<body>
<h1>JotBeat Studio — Settings</h1>
<p class="muted">Keys are masked on entry and never shown again. All writes go
through the same modules as the CLI. Non-OpenAI API? Run a local LiteLLM proxy
and add it here as family "openai" pointing at http://localhost:4000/v1.</p>

<h2>1 · API Keys</h2>
<table id="keys"><thead><tr><th></th><th>Provider</th><th>Key</th><th>Status</th>
<th></th></tr></thead><tbody></tbody></table>

<h2>2 · Providers</h2>
<table id="providers"><thead><tr><th>Name</th><th>Model</th><th>Family</th>
<th>Tier</th><th>$/M in</th><th>$/M out</th><th></th></tr></thead><tbody></tbody></table>
<p><button class="sec" onclick="document.getElementById('addform').style.display='block'">+ Add provider</button></p>
<div id="addform" style="display:none; border:1px solid #2a313a; padding:12px; border-radius:6px;">
  <p><input id="pname" placeholder="name"> <input id="pmodel" placeholder="model">
     <input id="pbase" placeholder="base URL" size="30"></p>
  <p><input id="penv" placeholder="env var NAME (e.g. MYPROVIDER_API_KEY)" size="34">
     <select id="pfamily"><option>openai</option><option>google</option></select>
     <select id="ptier"><option>free</option><option>bulk</option><option>escalation</option></select>
     <label class="muted"><input type="checkbox" id="pfree"> free</label></p>
  <p><input id="ppin" placeholder="price in /1M" size="10">
     <input id="ppout" placeholder="price out /1M" size="10">
     <input id="ppcached" placeholder="cached in (opt)" size="10"></p>
  <p><textarea id="pheaders" rows="2" cols="60"
     placeholder="custom headers, one KEY=VALUE per line (optional)&#10;e.g. api-key=$MY_HEADER_KEY — $NAME reads from .env"></textarea></p>
  <p class="muted">Family: almost everything is "openai". For anything that
  isn't, run LiteLLM locally and point here at http://localhost:4000/v1.</p>
  <p><button onclick="addProvider()">Add</button></p>
</div>

<h2>3 · Role Routing</h2>
<table id="roles"><thead><tr><th>Role</th><th>Primary</th><th>Fallback</th>
<th></th></tr></thead><tbody></tbody></table>
<p id="msg"></p>

<script>
let STATE = null;

async function api(path, body) {
  const r = await fetch(path, {method: body ? 'POST' : 'GET',
    headers: {'Content-Type': 'application/json'},
    body: body ? JSON.stringify(body) : undefined});
  return r.json();
}

function msg(text, cls) {
  const m = document.getElementById('msg');
  m.textContent = text; m.className = cls || '';
}

async function refresh() {
  STATE = await api('/api/state');
  renderKeys(); renderProviders(); renderRoles();
}

function renderKeys() {
  const tb = document.querySelector('#keys tbody');
  tb.innerHTML = '';
  for (const row of STATE.keys) {
    for (const prov of row.providers) {
      const tr = document.createElement('tr');
      const dot = row.set ? '<span class="dot on"></span>' : '<span class="dot"></span>';
      const status = row.set ? 'set · ' + row.chars + ' chars' : 'missing';
      tr.innerHTML = '<td>' + dot + '</td><td>' + prov + '</td>' +
        '<td><input type="password" id="key-' + prov + '" placeholder="' + row.name + '"></td>' +
        '<td class="muted">' + status + ' <span id="test-' + prov + '"></span></td>' +
        '<td><button onclick="saveKey(\\'' + prov + '\\',\\'' + row.name + '\\')">Save</button> ' +
        '<button class="sec" onclick="testProvider(\\'' + prov + '\\')">Test</button></td>';
      tb.appendChild(tr);
    }
  }
}

async function saveKey(prov, name) {
  const v = document.getElementById('key-' + prov).value;
  if (!v.trim()) { msg('empty value refused', 'fail'); return; }
  const r = await api('/api/keys/set', {name: name, value: v});
  if (r.ok) { msg(name + ' set (' + r.chars + ' chars)', 'ok'); refresh(); }
  else msg(r.error, 'fail');
}

async function testProvider(prov) {
  const el = document.getElementById('test-' + prov);
  el.textContent = 'testing…';
  const r = await api('/api/providers/test', {name: prov});
  el.textContent = r.ok ? ('OK · ' + r.latency_ms + 'ms') : ('FAIL · ' + r.error);
  el.className = r.ok ? 'ok' : 'fail';
}

function renderProviders() {
  const tb = document.querySelector('#providers tbody');
  tb.innerHTML = '';
  for (const p of STATE.providers) {
    const tr = document.createElement('tr');
    tr.innerHTML = '<td>' + p.name + '</td><td>' + p.model + '</td><td>' + p.family +
      '</td><td>' + p.tier + '</td><td>' + p.price_in + '</td><td>' + p.price_out +
      '</td><td><button class="sec" onclick="removeProvider(\\'' + p.name + '\\')">Remove</button></td>';
    tb.appendChild(tr);
  }
}

async function addProvider() {
  const headers = {};
  for (const line of document.getElementById('pheaders').value.split('\\n')) {
    if (line.includes('=')) {
      const i = line.indexOf('=');
      headers[line.slice(0, i).trim()] = line.slice(i + 1).trim();
    }
  }
  const r = await api('/api/providers/add', {
    name: v('pname'), model: v('pmodel'), base_url: v('pbase'), env_key: v('penv'),
    family: v('pfamily'), tier: v('ptier'), free: document.getElementById('pfree').checked,
    price_in: parseFloat(v('ppin') || '0'), price_out: parseFloat(v('ppout') || '0'),
    price_cached_in: v('ppcached') ? parseFloat(v('ppcached')) : null,
    headers: headers,
  });
  if (r.ok) { msg('provider added — now save its key above, Test, then route it', 'ok'); refresh(); }
  else msg(r.error, 'fail');
}

async function removeProvider(name) {
  const r = await api('/api/providers/remove', {name: name});
  if (r.ok) { msg('removed ' + name, 'ok'); refresh(); }
  else msg(r.error, 'fail');
}

function v(id) { return document.getElementById(id).value.trim(); }

function renderRoles() {
  const tb = document.querySelector('#roles tbody');
  tb.innerHTML = '';
  const names = STATE.providers.map(p => p.name);
  for (const role of STATE.roles) {
    const tr = document.createElement('tr');
    let opts = '<option value="">—</option>' +
      names.map(n => '<option>' + n + '</option>').join('');
    tr.innerHTML = '<td>' + role.name + '</td>' +
      '<td><select id="rp-' + role.name + '">' + opts + '</select></td>' +
      '<td><select id="rf-' + role.name + '">' + opts + '</select></td>' +
      '<td><button onclick="saveRole(\\'' + role.name + '\\')">Save</button></td>';
    tb.appendChild(tr);
    if (role.chain[0]) document.getElementById('rp-' + role.name).value = role.chain[0];
    if (role.chain[1]) document.getElementById('rf-' + role.name).value = role.chain[1];
  }
}

async function saveRole(role) {
  const r = await api('/api/route/set', {role: role,
    primary: v('rp-' + role), fallback: v('rf-' + role)});
  if (r.ok) {
    if (r.warnings && r.warnings.length) msg(r.warnings.join(' '), 'warn');
    else msg(role + ' routed', 'ok');
  } else msg(r.error, 'fail');
}

refresh();
</script>
</body>
</html>
"""


def _state(root: Path) -> dict:
    """Full settings state. Presence/char-counts only — never values.
    Header values (which may be secret) are reduced to key NAMES."""
    import models
    from tools.keys import key_status
    from tools.routing import roles_using

    routing = models.load_routing()
    providers = []
    for name, p in routing["providers"].items():
        providers.append({
            "name": name,
            "model": p.get("model"),
            "tier": p.get("tier"),
            "family": p.get("family"),
            "base_url": p.get("base_url"),
            "env_key": p.get("env_key"),
            "free": p.get("free", False),
            "price_in": p.get("price_in"),
            "price_out": p.get("price_out"),
            "verified": bool(p.get("verified")),
            "header_keys": sorted((p.get("headers") or {}).keys()),
            "roles": roles_using(routing, name),
        })
    roles = [
        {"name": r, "chain": cfg["chain"]}
        for r, cfg in routing["roles"].items()
    ]
    return {
        "keys": key_status(root, routing)["expected"],
        "stale_keys": key_status(root, routing)["stale"],
        "providers": providers,
        "roles": roles,
    }


def make_server(root: Path, port: int = 0) -> ThreadingHTTPServer:
    root = Path(root)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # quiet
            pass

        # -- helpers -----------------------------------------------------
        def _guard(self) -> bool:
            if not is_loopback(self.client_address[0]):
                self._json({"ok": False, "error": "loopback only"}, 403)
                return False
            return True

        def _json(self, data: dict, status: int = 200) -> None:
            body = json.dumps(data).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _body(self) -> dict:
            n = int(self.headers.get("Content-Length") or 0)
            try:
                return json.loads(self.rfile.read(n) or b"{}")
            except json.JSONDecodeError:
                return {}

        # -- routes ------------------------------------------------------
        def do_GET(self) -> None:
            if not self._guard():
                return
            if self.path == "/":
                body = PAGE.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif self.path == "/api/state":
                self._json(_state(root))
            else:
                self._json({"ok": False, "error": "not found"}, 404)

        def do_POST(self) -> None:
            if not self._guard():
                return
            from tools.keys import KeysError, remove_key, set_key
            from tools import routing as routing_mod
            import models

            body = self._body()
            try:
                if self.path == "/api/keys/set":
                    n = set_key(root, body.get("name", ""), body.get("value", ""))
                    self._json({"ok": True, "chars": n})

                elif self.path == "/api/keys/remove":
                    removed = remove_key(root, body.get("name", ""))
                    self._json({"ok": True, "removed": removed})

                elif self.path == "/api/providers/add":
                    routing = models.load_routing()
                    entry = routing_mod.build_entry(
                        name=body.get("name", ""), env_key=body.get("env_key", ""),
                        base_url=body.get("base_url") or None,
                        model=body.get("model", ""), family=body.get("family", ""),
                        tier=body.get("tier", ""),
                        price_in=body.get("price_in"), price_out=body.get("price_out"),
                        price_cached_in=body.get("price_cached_in"),
                        free=body.get("free", False), headers=body.get("headers"),
                    )
                    routing_mod.add_provider(routing, entry)
                    routing_mod.save(routing, models.PROVIDERS_FILE)
                    self._json({"ok": True})

                elif self.path == "/api/providers/remove":
                    routing = models.load_routing()
                    routing_mod.remove_provider(routing, body.get("name", ""))
                    routing_mod.save(routing, models.PROVIDERS_FILE)
                    self._json({"ok": True})

                elif self.path == "/api/providers/test":
                    result = models.ping_provider(body.get("name", ""))
                    if result["ok"]:
                        routing = models.load_routing()
                        routing["providers"][body["name"]]["verified"] = True
                        routing_mod.save(routing, models.PROVIDERS_FILE)
                    self._json(result)

                elif self.path == "/api/route/set":
                    chain = [c for c in (body.get("primary"), body.get("fallback")) if c]
                    # de-dup preserving order (primary == fallback is pointless)
                    chain = list(dict.fromkeys(chain))
                    if not chain:
                        raise routing_mod.RoutingError("pick at least a primary")
                    routing = models.load_routing()
                    warnings = routing_mod.set_role_chain(
                        routing, body.get("role", ""), chain)
                    routing_mod.save(routing, models.PROVIDERS_FILE)
                    self._json({"ok": True, "warnings": warnings})

                else:
                    self._json({"ok": False, "error": "not found"}, 404)

            except (KeysError, routing_mod.RoutingError) as e:
                self._json({"ok": False, "error": str(e)}, 400)
            except Exception as e:
                self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)

    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    return httpd


def serve(root: Path) -> None:
    """Boot the settings panel on a free loopback port and open the browser."""
    from cli import load_env  # populates os.environ from .env for provider tests
    load_env()

    httpd = make_server(root)
    url = f"http://127.0.0.1:{httpd.server_address[1]}"
    try:  # pythonw (double-click launcher) may have no stdout at all
        print(f"JotBeat settings -> {url}  (loopback only; Ctrl+C to stop)")
    except Exception:
        pass
    webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        try:
            print("\nsettings UI stopped")
        except Exception:
            pass
    finally:
        httpd.server_close()
