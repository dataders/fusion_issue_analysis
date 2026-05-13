// Minimal service worker: adds COOP + COEP (credentialless) to all navigation
// responses so DuckDB-WASM has access to SharedArrayBuffer on GitHub Pages.
// credentialless (not require-corp) allows CDN resources to load without CORP headers.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));
self.addEventListener("fetch", (e) => {
  if (e.request.mode !== "navigate") return;
  e.respondWith(
    fetch(e.request).then((r) => {
      const h = new Headers(r.headers);
      h.set("Cross-Origin-Opener-Policy", "same-origin");
      h.set("Cross-Origin-Embedder-Policy", "credentialless");
      return new Response(r.body, { status: r.status, statusText: r.statusText, headers: h });
    })
  );
});
