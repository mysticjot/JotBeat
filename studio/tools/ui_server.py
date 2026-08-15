"""tools/ui_server.py — `jotbeat ui`: the human's settings panel
(HANDOFF-PHASE3 Addendum C).

Stdlib only (http.server + one self-contained HTML page, vanilla JS).
Bound to 127.0.0.1 ONLY; non-loopback clients are refused. All reads/writes
go through tools/keys.py and tools/routing.py — the same writer modules the
CLI uses. Key values are accepted via POST but NEVER rendered back; responses
carry char counts, not values.
"""

from __future__ import annotations

import datetime
import json
import os
import webbrowser
from contextlib import suppress
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LOOPBACK = ("127.0.0.1", "::1", "localhost")

# Bump on every UI change — shown at the top of the page so a stale cached
# page (or an orphan server) is immediately recognizable.
BUILD = "2026-08-15-6"

NO_STORE = ("Cache-Control", "no-store")


def _log(root: Path, line: str) -> None:
    """Append one line to state/ui-debug.log. NEVER log key values —
    only timestamps, routes, and outcome/error text (which carries names
    and char counts at most). Best-effort: logging must never break a request."""
    with suppress(OSError):
        log_path = Path(root) / "state" / "ui-debug.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().isoformat(timespec="seconds")
        with log_path.open("a", encoding="utf-8") as f:
            f.write(f"{stamp} {line}\n")


def is_loopback(addr: str) -> bool:
    return addr in LOOPBACK


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>JotBeat Studio — Settings</title>
<style>
  :root {
    --bg:#0f1216; --panel:#161b22; --panel2:#1d232c; --border:#2a323d;
    --text:#e2e8f0; --muted:#8b96a3; --accent:#4f7cff; --accent-hi:#6b91ff;
    --ok:#3fb950; --warn:#d29922; --fail:#f85149;
  }
  * { box-sizing: border-box; }
  body { font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
         background: var(--bg); color: var(--text);
         max-width: 980px; margin: 28px auto; padding: 0 18px; }
  h1 { font-size: 21px; letter-spacing: .2px; }
  h2 { font-size: 13px; text-transform: uppercase; letter-spacing: .08em;
       color: var(--muted); margin: 0 0 12px; }
  .card { background: var(--panel); border: 1px solid var(--border);
          border-radius: 10px; padding: 18px 20px; margin-top: 22px;
          box-shadow: 0 1px 2px rgba(0,0,0,.45), 0 10px 28px rgba(0,0,0,.28); }
  table { border-collapse: collapse; width: 100%; font-size: 13px; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #232a33; }
  tbody tr { transition: background .12s ease; }
  tbody tr:hover { background: rgba(79,124,255,.06); }
  tbody tr:last-child td { border-bottom: 0; }
  th { color: var(--muted); font-weight: 600; font-size: 11px;
       text-transform: uppercase; letter-spacing: .06em; }
  input, select, textarea { background: var(--panel2); color: var(--text);
       border: 1px solid #39424e; border-radius: 6px; padding: 6px 8px;
       font-size: 13px;
       transition: border-color .12s ease, box-shadow .12s ease; }
  input:focus, select:focus, textarea:focus { outline: none;
       border-color: var(--accent); box-shadow: 0 0 0 3px rgba(79,124,255,.22); }
  button { background: var(--accent); color: #fff; border: 0; border-radius: 6px;
           padding: 6px 12px; font-size: 13px; font-weight: 600; cursor: pointer;
           transition: background .12s ease, transform .12s ease,
                       box-shadow .12s ease; }
  button:hover { background: var(--accent-hi); transform: translateY(-1px);
           box-shadow: 0 4px 14px rgba(79,124,255,.28); }
  button:active { transform: translateY(0); box-shadow: none; }
  button.sec { background: var(--panel2); border: 1px solid #39424e; }
  button.sec:hover { background: #242b36; box-shadow: 0 4px 12px rgba(0,0,0,.35); }
  .dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%;
         background: #5a6470; margin-right: 6px; }
  .dot.on { background: var(--ok); box-shadow: 0 0 8px rgba(63,185,80,.7); }
  .muted { color: var(--muted); font-size: 12px; }
  .warn { color: var(--warn); font-size: 12px; }
  .ok { color: var(--ok); } .fail { color: var(--fail); }
  #msg { margin-top: 18px; font-size: 15px; font-weight: 700; min-height: 22px;
         padding: 10px 14px; border: 1px solid var(--border); border-radius: 8px;
         background: var(--panel); }
  #msg.ok { border-color: rgba(63,185,80,.5); background: rgba(63,185,80,.08); }
  #msg.fail { border-color: rgba(248,81,73,.5); background: rgba(248,81,73,.08); }
  #msg.warn { border-color: rgba(210,153,34,.5); background: rgba(210,153,34,.08); }
  .spin { display: inline-block; width: 11px; height: 11px; margin-right: 5px;
          border: 2px solid #39424e; border-top-color: var(--accent);
          border-radius: 50%; animation: rot .7s linear infinite;
          vertical-align: -1px; }
  @keyframes rot { to { transform: rotate(360deg); } }
  #addform { background: var(--panel2); }
  #dead { display:none; position:fixed; inset:0; background:rgba(10,12,16,.92);
          z-index:99; text-align:center; padding-top:18vh; }
  #dead .box { display:inline-block; background: var(--panel);
               border:1px solid var(--fail); border-radius:10px;
               padding:24px 32px; max-width:520px;
               box-shadow: 0 20px 60px rgba(0,0,0,.5); }
</style>
</head>
<body>
<div id="dead"><div class="box">
  <h2 class="fail">Settings server is not running</h2>
  <p>This tab is talking to a server that has already exited.<br>
  Double-click <b>JotBeat Studio.bat</b> and use the <b>new</b> tab it opens —
  or go to <b>http://127.0.0.1:8787</b> if a server is already up.</p>
  <p><button onclick="location.reload()">Retry</button></p>
</div></div>
<h1>JotBeat Studio — Settings <span class="muted">· build __BUILD__</span></h1>
<p id="rootbanner" class="fail" style="display:none; font-weight:600">
SERVER STARTED IN THE WRONG FOLDER — saves are being refused.
Close this tab and relaunch via JotBeat Studio.bat.</p>
<p class="muted">Keys are masked on entry and never shown again. All writes go
through the same modules as the CLI. Non-OpenAI API? Run a local LiteLLM proxy
and add it here as family "openai" pointing at http://localhost:4000/v1.</p>

<section class="card">
<h2>1 · API Keys</h2>
<table id="keys"><thead><tr><th></th><th>Provider</th><th>Key</th><th>Status</th>
<th></th></tr></thead><tbody></tbody></table>
</section>

<section class="card">
<h2>2 · Providers</h2>
<table id="providers"><thead><tr><th>Name</th><th>Model</th><th>Family</th>
<th>Tier</th><th>$/M in</th><th>$/M out</th><th></th></tr></thead><tbody></tbody></table>
<p><button class="sec" onclick="document.getElementById('addform').style.display='block'">+ Add provider</button></p>
<div id="addform" style="display:none; border:1px solid #2a313a; padding:12px; border-radius:6px;">
  <p>1 · <select id="ppreset" onchange="presetFill()">
     <option value="">pick a provider…</option>
     <option>ollama</option><option>litellm</option><option>openrouter</option>
     <option>groq</option><option>deepseek</option><option>zai</option>
     <option>kimi</option><option>mistral</option><option>cerebras</option>
     <option>gemini</option><option>github-models</option><option>opencode</option>
     <option value="__custom">other (manual)</option>
     </select>
     <span id="pnote" class="muted"></span></p>
  <p id="pmodelrow" style="display:none">2 · model:
     <select id="pmodelsel" onchange="modelPicked()"></select>
     <input id="pmodelother" placeholder="model id" style="display:none"></p>
  <p id="pkeyrow" style="display:none">3 ·
     <input type="password" id="pkey" placeholder="paste API key (or save it later in §1)" size="42"
            autocomplete="new-password" data-1p-ignore data-lpignore="true"></p>
  <p id="paddrow" style="display:none"><button onclick="addProvider()">Add provider</button></p>
  <p><button class="sec" onclick="const a=document.getElementById('padv'); a.style.display = a.style.display==='none'?'block':'none'">advanced…</button></p>
  <div id="padv" style="display:none">
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
  </div>
</div>
</section>

<section class="card">
<h2>3 · Role Routing</h2>
<table id="roles"><thead><tr><th>Role</th><th>Primary</th><th>Fallback</th>
<th></th></tr></thead><tbody></tbody></table>
</section>
<p id="msg"></p>

<script>
let STATE = null;

async function api(path, body) {
  try {
    const r = await fetch(path, {method: body ? 'POST' : 'GET',
      headers: {'Content-Type': 'application/json'},
      body: body ? JSON.stringify(body) : undefined});
    document.getElementById('dead').style.display = 'none';
    return await r.json();
  } catch (e) {
    document.getElementById('dead').style.display = 'block';
    return {ok: false, error: 'cannot reach the settings server — see the overlay.'};
  }
}

function msg(text, cls) {
  const m = document.getElementById('msg');
  m.textContent = text; m.className = cls || '';
}

async function refresh() {
  STATE = await api('/api/state');
  if (STATE && STATE.root_ok === false)
    document.getElementById('rootbanner').style.display = 'block';
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
        '<td><input type="password" id="key-' + prov + '" placeholder="' + row.name + '"' +
        ' autocomplete="new-password" data-1p-ignore="true" data-lpignore="true"' +
        ' data-form-type="other" autocapitalize="off" spellcheck="false"></td>' +
        '<td class="muted">' + status + ' <span id="test-' + prov + '"></span></td>' +
        '<td><button onclick="saveKey(\\'' + prov + '\\',\\'' + row.name + '\\')">Save</button> ' +
        '<button class="sec" onclick="testProvider(\\'' + prov + '\\')">Test</button></td>';
      tb.appendChild(tr);
    }
  }
}

async function saveKey(prov, name) {
  const input = document.getElementById('key-' + prov);
  const st = document.getElementById('test-' + prov);
  const val = input.value;
  if (!val.trim()) { msg('empty value refused', 'fail'); return; }
  st.innerHTML = '<span class="spin"></span>saving…'; st.className = 'muted';
  const r = await api('/api/keys/set', {name: name, value: val});
  if (r.ok) {
    msg('SAVED ✓ ' + name + ' (' + r.chars + ' chars)', 'ok');
    st.textContent = 'saved ✓'; st.className = 'ok';
    input.value = '';
    refresh();
  } else {
    msg('SAVE FAILED: ' + r.error, 'fail');
    st.textContent = 'save FAILED'; st.className = 'fail';
  }
}

async function testProvider(prov) {
  const el = document.getElementById('test-' + prov);
  el.innerHTML = '<span class="spin"></span>testing…';
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

async function presetFill() {
  const preset = v('ppreset');
  for (const i of ['pmodelrow', 'pkeyrow', 'paddrow'])
    document.getElementById(i).style.display = 'none';
  document.getElementById('pnote').textContent = '';
  if (!preset) return;
  if (preset === '__custom') {
    document.getElementById('padv').style.display = 'block';
    document.getElementById('paddrow').style.display = 'block';
    document.getElementById('pnote').textContent =
      'manual entry — fill the advanced fields, then Add';
    return;
  }
  const r = await api('/api/providers/preset?name=' + encodeURIComponent(preset));
  if (!r.ok) { msg(r.error, 'fail'); return; }
  const f = r.fields;
  // fill the hidden advanced fields so Add sends complete data
  document.getElementById('pname').value = r.name;
  document.getElementById('pbase').value = f.base_url || '';
  document.getElementById('penv').value = f.env_key || '';
  document.getElementById('pfamily').value = f.family;
  document.getElementById('ptier').value = f.tier;
  document.getElementById('pfree').checked = !!f.free;
  document.getElementById('ppin').value = f.price_in != null ? f.price_in : '';
  document.getElementById('ppout').value = f.price_out != null ? f.price_out : '';
  document.getElementById('ppcached').value = f.price_cached_in != null ? f.price_cached_in : '';
  if (r.warning) { msg(r.warning, 'fail'); return; }
  const models = (r.models && r.models.length) ? r.models : (f.models || []);
  const sel = document.getElementById('pmodelsel');
  sel.innerHTML = '';
  for (const m of models) {
    const o = document.createElement('option'); o.textContent = m; sel.appendChild(o);
  }
  const other = document.createElement('option');
  other.value = '__other'; other.textContent = 'other (type it)…';
  sel.appendChild(other);
  document.getElementById('pmodelrow').style.display = 'block';
  if (!f.keyless) {
    document.getElementById('pkeyrow').style.display = 'block';
  } else {
    document.getElementById('pnote').textContent = 'keyless local server — no API key needed';
  }
  document.getElementById('paddrow').style.display = 'block';
  modelPicked();
}

function modelPicked() {
  const sel = document.getElementById('pmodelsel');
  const isOther = sel.value === '__other';
  document.getElementById('pmodelother').style.display = isOther ? 'inline-block' : 'none';
  document.getElementById('pmodel').value = isOther ? '' : sel.value;
}

async function addProvider() {
  const headers = {};
  for (const line of document.getElementById('pheaders').value.split('\\n')) {
    if (line.includes('=')) {
      const i = line.indexOf('=');
      headers[line.slice(0, i).trim()] = line.slice(i + 1).trim();
    }
  }
  const other = document.getElementById('pmodelother');
  const model = (other.style.display !== 'none' && other.value.trim())
    ? other.value.trim() : v('pmodel');
  const preset = v('ppreset');
  const r = await api('/api/providers/add', {
    preset: preset === '__custom' ? '' : preset,
    name: v('pname'), model: model, base_url: v('pbase'), env_key: v('penv'),
    family: v('pfamily'), tier: v('ptier'), free: document.getElementById('pfree').checked,
    price_in: parseFloat(v('ppin') || '0'), price_out: parseFloat(v('ppout') || '0'),
    price_cached_in: v('ppcached') ? parseFloat(v('ppcached')) : null,
    headers: headers,
  });
  if (!r.ok) { msg(r.error, 'fail'); return; }
  const key = document.getElementById('pkey').value.trim();
  if (key && document.getElementById('pkeyrow').style.display !== 'none') {
    const k = await api('/api/keys/set', {name: v('penv'), value: key});
    document.getElementById('pkey').value = '';
    if (k.ok) msg('provider added + key saved (' + k.chars + ' chars) — Test it in §1, then route it in §3', 'ok');
    else msg('provider added, but key save failed: ' + k.error + ' — save it in §1', 'fail');
  } else {
    msg('provider added — Test it, then route it in §3', 'ok');
  }
  refresh();
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
        providers.append(
            {
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
            }
        )
    roles = [{"name": r, "chain": cfg["chain"]} for r, cfg in routing["roles"].items()]
    # root_ok=False means the server was launched in the wrong folder —
    # every key write would be refused. The page shows a red banner.
    from tools.keys import assert_env_gitignored

    try:
        assert_env_gitignored(root)
        root_ok = True
    except Exception:
        root_ok = False
    return {
        "build": BUILD,
        "root_ok": root_ok,
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
            self.send_header(*NO_STORE)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _respond(self, data: dict, status: int = 200) -> None:
            """_json + one debug-log line. Logs outcome text only —
            request bodies (which carry key values) are never logged."""
            outcome = data.get("error") or "ok"
            _log(root, f"{self.command} {self.path} -> {status} {outcome}")
            self._json(data, status)

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
                body = PAGE.replace("__BUILD__", BUILD).encode("utf-8")
                _log(root, "GET / (page loaded)")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header(*NO_STORE)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif self.path == "/api/state":
                self._json(_state(root))
            elif self.path.startswith("/api/providers/preset"):
                from tools import routing as routing_mod
                from urllib.parse import parse_qs, urlparse

                q = parse_qs(urlparse(self.path).query)
                pres = routing_mod.detect_preset(q.get("name", [""])[0])
                if not pres:
                    self._json({"ok": False, "error": "unknown preset"}, 404)
                else:
                    pname, fields = pres
                    out = {"ok": True, "name": pname, "fields": fields}
                    if pname == "ollama":
                        try:
                            out["models"] = routing_mod.ollama_models()
                        except routing_mod.RoutingError as e:
                            out["models"] = []
                            out["warning"] = str(e)
                    self._json(out)
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
                    # sync the live process env — the server loaded .env at
                    # startup, so provider tests would otherwise miss keys
                    # saved during this session ("env key not set" bug)
                    os.environ[body["name"].strip()] = body["value"].strip()
                    self._respond({"ok": True, "chars": n})

                elif self.path == "/api/keys/remove":
                    removed = remove_key(root, body.get("name", ""))
                    if removed:
                        os.environ.pop(body["name"].strip(), None)
                    self._respond({"ok": True, "removed": removed})

                elif self.path == "/api/providers/add":
                    routing = models.load_routing()
                    # Preset merge: anything the form left blank falls back
                    # to the detected preset's fields (same path as the CLI).
                    pres = routing_mod.detect_preset(
                        body.get("preset") or body.get("name", "")
                    )
                    pf = pres[1] if pres else {}

                    def pick(key, default=""):
                        v = body.get(key)
                        return v if v not in (None, "") else pf.get(key, default)

                    model = pick("model")
                    if pres and pres[0] == "ollama":
                        available = routing_mod.ollama_models()
                        if not available:
                            raise routing_mod.RoutingError(
                                "Ollama is running but has no models — "
                                "run `ollama pull <model>` first"
                            )
                        if not model:
                            model = available[0]
                        elif model not in available:
                            raise routing_mod.RoutingError(
                                f"model '{model}' not installed — "
                                f"available: {', '.join(available)}"
                            )
                    entry = routing_mod.build_entry(
                        name=body.get("name", "") or (pres[0] if pres else ""),
                        env_key=pick("env_key"),
                        base_url=pick("base_url") or None,
                        model=model,
                        family=pick("family"),
                        tier=pick("tier"),
                        price_in=body.get("price_in")
                            if body.get("price_in") is not None
                            else pf.get("price_in", 0.0),
                        price_out=body.get("price_out")
                            if body.get("price_out") is not None
                            else pf.get("price_out", 0.0),
                        price_cached_in=body.get("price_cached_in")
                            if body.get("price_cached_in") is not None
                            else pf.get("price_cached_in"),
                        free=bool(body.get("free")) or bool(pf.get("free")),
                        headers=body.get("headers"),
                        keyless=bool(pf.get("keyless")),
                    )
                    routing_mod.add_provider(routing, entry)
                    routing_mod.save(routing, models.PROVIDERS_FILE)
                    self._respond({"ok": True})

                elif self.path == "/api/providers/remove":
                    routing = models.load_routing()
                    routing_mod.remove_provider(routing, body.get("name", ""))
                    routing_mod.save(routing, models.PROVIDERS_FILE)
                    self._respond({"ok": True})

                elif self.path == "/api/providers/test":
                    result = models.ping_provider(body.get("name", ""))
                    if result["ok"]:
                        routing = models.load_routing()
                        routing["providers"][body["name"]]["verified"] = True
                        routing_mod.save(routing, models.PROVIDERS_FILE)
                    self._respond(result)

                elif self.path == "/api/route/set":
                    chain = [
                        c for c in (body.get("primary"), body.get("fallback")) if c
                    ]
                    # de-dup preserving order (primary == fallback is pointless)
                    chain = list(dict.fromkeys(chain))
                    if not chain:
                        raise routing_mod.RoutingError("pick at least a primary")
                    routing = models.load_routing()
                    warnings = routing_mod.set_role_chain(
                        routing, body.get("role", ""), chain
                    )
                    routing_mod.save(routing, models.PROVIDERS_FILE)
                    self._respond({"ok": True, "warnings": warnings})

                else:
                    self._respond({"ok": False, "error": "not found"}, 404)

            except (KeysError, routing_mod.RoutingError) as e:
                self._respond({"ok": False, "error": str(e)}, 400)
            except Exception as e:
                self._respond({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)

    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    return httpd


DEFAULT_PORT = 8787  # fixed, bookmarkable: http://127.0.0.1:8787


def _probe_existing(port: int) -> bool:
    """True if a JotBeat settings server is already answering on `port`.
    Recognized by the /api/state shape (providers + roles) — works for
    older builds too, so reuse survives version skew."""
    import urllib.request

    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/state", timeout=2
        ) as r:
            data = json.loads(r.read().decode("utf-8"))
        return "providers" in data and "roles" in data
    except Exception:
        return False


def serve(root: Path) -> None:
    """Boot the settings panel and open the browser.

    Single-instance: if a JotBeat server already answers on DEFAULT_PORT,
    just open the browser at it and exit — no orphan servers, no dead tabs
    from stale ports. If the port is taken by something else, fall back to
    a random free port."""
    from cli import load_env  # populates os.environ from .env for provider tests

    load_env()

    fixed_url = f"http://127.0.0.1:{DEFAULT_PORT}"
    if _probe_existing(DEFAULT_PORT):
        _log(root, f"server already running at {fixed_url} — reusing it")
        webbrowser.open(fixed_url)
        return

    try:
        httpd = make_server(root, DEFAULT_PORT)
    except OSError:  # port held by a non-JotBeat process
        httpd = make_server(root, 0)
    url = f"http://127.0.0.1:{httpd.server_address[1]}"
    _log(root, f"server start build={BUILD} root={Path(root).resolve()} url={url}")
    # pythonw (double-click launcher) may have no stdout at all
    with suppress(Exception):
        print(f"JotBeat settings -> {url}  (loopback only; Ctrl+C to stop)")
    webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        with suppress(Exception):
            print("\nsettings UI stopped")
    finally:
        httpd.server_close()
