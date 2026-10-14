#!/usr/bin/env python3
"""Local dev server that adds COOP/COEP headers so DuckDB-WASM works."""

import os
from http.server import HTTPServer, SimpleHTTPRequestHandler


class COEPHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "credentialless")
        super().end_headers()

    def log_message(self, fmt, *args):
        pass  # quiet


PORT = int(os.environ.get("PLAYWRIGHT_PORT") or os.environ.get("PORT") or 9321)

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"Serving at http://127.0.0.1:{PORT}  (COOP + COEP headers enabled)")
HTTPServer(("127.0.0.1", PORT), COEPHandler).serve_forever()
