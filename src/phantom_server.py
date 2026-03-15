"""
Local server for Phantom wallet connect and sign flow.
Serves a page that connects to Phantom and signs transactions; GUI communicates via REST.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

# Minimal server without Flask: use stdlib only so we don't require flask
# We'll use a single module that can run a thread with BaseHTTPRequestHandler

PHANTOM_HTML = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Phantom — Startup CLI</title>
  <script src="https://unpkg.com/@solana/web3.js@1.73.0/lib/index.iife.min.js"></script>
  <style>
    body { font-family: system-ui; max-width: 480px; margin: 2rem auto; padding: 1rem; }
    button { padding: 0.5rem 1rem; margin: 0.25rem; cursor: pointer; }
    .status { margin: 1rem 0; padding: 0.5rem; background: #eee; border-radius: 6px; }
    .ok { color: green; }
    .err { color: red; }
  </style>
</head>
<body>
  <h1>Phantom — Startup CLI</h1>
  <p class="ok" style="background:#e8f5e9;padding:8px;border-radius:6px;margin-bottom:1rem;"><strong>Use Devnet (testnet):</strong> In Phantom: Settings → Developer Settings → turn on <strong>Testnet Mode</strong> → under Solana choose <strong>Devnet</strong>. This app builds and sends all transactions to Solana Devnet only (never mainnet).</p>
  <p style="background:#fff3e0;padding:8px;border-radius:6px;margin-bottom:1rem;font-size:0.9em;"><strong>Need SOL for fees?</strong> Your Phantom wallet pays the small tx fee (~0.0001 SOL). Get free Devnet SOL at <a href="https://faucet.solana.com/" target="_blank" rel="noopener">faucet.solana.com</a> (choose Devnet, paste your wallet address).</p>
  <p>Connect your Phantom wallet to buy/sell from the app.</p>
  <button id="connectBtn">Connect Phantom</button>
  <div id="status" class="status"></div>
  <div id="signStatus" class="status" style="display:none;">Waiting for transaction to sign… Approve in Phantom.</div>
  <script>
    const SERVER = window.location.origin;
    let pubkey = null;

    async function connect() {
      const status = document.getElementById('status');
      if (window.solana && window.solana.isPhantom) {
        try {
          const resp = await window.solana.connect();
          pubkey = resp.publicKey ? resp.publicKey.toString() : null;
          if (pubkey) {
            await fetch(SERVER + '/api/connected', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ pubkey: pubkey })
            });
            status.innerHTML = '<span class="ok">Connected: ' + pubkey.slice(0,8) + '…' + pubkey.slice(-8) + '</span>';
            document.getElementById('connectBtn').textContent = 'Disconnect';
            document.getElementById('connectBtn').onclick = disconnect;
          }
        } catch (e) {
          status.innerHTML = '<span class="err">' + e.message + '</span>';
        }
      } else {
        status.innerHTML = '<span class="err">Install Phantom (phantom.app) and refresh.</span>';
      }
    }

    async function disconnect() {
      if (window.solana) try { await window.solana.disconnect(); } catch (_) {}
      pubkey = null;
      await fetch(SERVER + '/api/connected', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ pubkey: null }) });
      document.getElementById('status').innerHTML = '';
      document.getElementById('connectBtn').textContent = 'Connect Phantom';
      document.getElementById('connectBtn').onclick = connect;
    }

    document.getElementById('connectBtn').onclick = connect;

    async function pollAndSign() {
      const signStatus = document.getElementById('signStatus');
      try {
        const r = await fetch(SERVER + '/api/pending_tx');
        const data = await r.json();
        if (data.transaction && window.solana && window.solana.isPhantom) {
          signStatus.style.display = 'block';
          const buf = Uint8Array.from(atob(data.transaction), c => c.charCodeAt(0));
          const tx = solanaWeb3.Transaction.from(buf);
          const signed = await window.solana.signTransaction(tx);
          const serialized = signed.serialize({ requireAllSignatures: false });
          const b64 = btoa(String.fromCharCode.apply(null, serialized));
          await fetch(SERVER + '/api/signed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ signed: b64 })
          });
          signStatus.innerHTML = '<span class="ok">Signed. You can close this tab.</span>';
        }
      } catch (e) {
        signStatus.innerHTML = '<span class="err">' + e.message + '</span>';
      }
    }
    setInterval(pollAndSign, 2000);
  </script>
</body>
</html>
"""


class PhantomHandler:
    """State and HTTP handler for Phantom connect/sign."""

    def __init__(self) -> None:
        self.connected_pubkey: str | None = None
        self.pending_tx_b64: str | None = None
        self.signed_tx_b64: str | None = None
        self._lock = threading.Lock()
        self._signed_event = threading.Event()

    def set_connected(self, pubkey: str | None) -> None:
        with self._lock:
            self.connected_pubkey = pubkey

    def get_wallet(self) -> dict[str, Any]:
        with self._lock:
            return {"connected": self.connected_pubkey is not None, "pubkey": self.connected_pubkey}

    def set_pending_tx(self, tx_base64: str) -> None:
        with self._lock:
            self.pending_tx_b64 = tx_base64
            self.signed_tx_b64 = None
            self._signed_event.clear()

    def get_pending_tx(self) -> str | None:
        with self._lock:
            out = self.pending_tx_b64
            self.pending_tx_b64 = None
            return out

    def set_signed(self, signed_base64: str) -> None:
        with self._lock:
            self.signed_tx_b64 = signed_base64
            self._signed_event.set()

    def wait_for_signed(self, timeout: float = 120.0) -> str | None:
        if self._signed_event.wait(timeout=timeout):
            with self._lock:
                return self.signed_tx_b64
        return None


# Global state (shared with request handler)
_phantom_state = PhantomHandler()


def _make_handler(state: PhantomHandler) -> type[BaseHTTPRequestHandler]:
    """Build a BaseHTTPRequestHandler that uses the given state."""

    class _PhantomHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split("?")[0]
            if path == "/" or path == "/index.html":
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(PHANTOM_HTML.encode("utf-8"))
                return
            if path == "/api/wallet":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(state.get_wallet()).encode("utf-8"))
                return
            if path == "/api/pending_tx":
                tx = state.get_pending_tx()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"transaction": tx}).encode("utf-8"))
                return
            self.send_response(404)
            self.end_headers()

        def do_POST(self):
            path = self.path.split("?")[0]
            if path == "/api/connected":
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8") if length else "{}"
                try:
                    data = json.loads(body)
                    state.set_connected(data.get("pubkey"))
                except Exception:
                    pass
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
                return
            if path == "/api/signed":
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8") if length else "{}"
                try:
                    data = json.loads(body)
                    state.set_signed(data.get("signed", ""))
                except Exception:
                    pass
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
                return
            self.send_response(404)
            self.end_headers()

        def log_message(self, format, *args):
            pass

    return _PhantomHandler


_server: HTTPServer | None = None
_server_thread: threading.Thread | None = None
_port: int = 0


def get_phantom_state() -> PhantomHandler:
    return _phantom_state


def start_phantom_server(port: int = 0) -> int:
    """Start the Phantom connect/sign server in a daemon thread. Returns actual port."""
    global _server, _server_thread, _port
    if _server is not None:
        return _port
    _server = HTTPServer(("127.0.0.1", port), _make_handler(_phantom_state))
    _port = _server.server_address[1]

    def run():
        assert _server is not None
        _server.serve_forever()

    _server_thread = threading.Thread(target=run, daemon=True)
    _server_thread.start()
    return _port


def phantom_server_url(port: int | None = None) -> str:
    p = port if port is not None else _port
    return f"http://127.0.0.1:{p}"


def set_pending_tx_for_phantom(tx_base64: str) -> None:
    _phantom_state.set_pending_tx(tx_base64)


def wait_for_phantom_signed(timeout: float = 120.0) -> str | None:
    """Returns base64 signed transaction or None on timeout."""
    return _phantom_state.wait_for_signed(timeout=timeout)
