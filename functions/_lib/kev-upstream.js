/* Shared by /api/kev and /api/exploited: the CISA catalog fetch, the cache
 * lifetimes and the response headers. Exports no onRequest handler, so Pages
 * builds no route from this file.
 */

export const UPSTREAM = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json";
export const USER_AGENT = "umbrasec-kev-api (+https://umbrasec.dev/api/kev)";

export const EDGE_TTL = 3600;          // seconds a live payload stays in the edge cache
export const BROWSER_TTL = 300;        // seconds a browser may reuse it without asking
export const FALLBACK_TTL = 300;       // seconds a snapshot fallback is cached during an outage
export const UPSTREAM_TIMEOUT_MS = 8000;

// CISA text can carry en and em dashes; the site uses plain hyphens only.
export const plain = (v) => (typeof v === "string" ? v.replace(/[\u2013\u2014]/g, "-") : v);

export function jsonHeaders(sourceHeader, source, overrides) {
  return {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": `public, max-age=${BROWSER_TTL}, s-maxage=${EDGE_TTL}`,
    "Access-Control-Allow-Origin": "*",
    "X-Content-Type-Options": "nosniff",
    [sourceHeader]: source,
    // _headers only applies to static assets; keep Function responses in step.
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    ...overrides,
  };
}

// One cache entry per origin+path; query strings must not fragment the cache.
export function cacheKeyFor(request) {
  const u = new URL(request.url);
  return new Request(u.origin + u.pathname, { method: "GET" });
}

export async function fetchCatalog() {
  const res = await fetch(UPSTREAM, {
    headers: { "User-Agent": USER_AGENT, "Accept": "application/json" },
    signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
    // Let Cloudflare cache the big upstream file too, so a burst of cache
    // misses across colos does not become a burst of 1.7 MB downloads. Only
    // successes are pinned: a 404/410 from CISA must not be held for 5 min.
    cf: { cacheEverything: true, cacheTtlByStatus: { "200-299": 300, "400-599": 0 } },
  });
  if (!res.ok) throw new Error("upstream " + res.status);
  const raw = await res.json();
  if (!raw || !Array.isArray(raw.vulnerabilities) || raw.vulnerabilities.length === 0) {
    throw new Error("upstream payload has no vulnerabilities array");
  }
  return raw;
}
