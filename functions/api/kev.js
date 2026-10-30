/* /api/kev - the homepage CISA KEV ticker, served live.
 *
 * A Cloudflare Pages Function. On each cache miss it fetches CISA's public
 * Known Exploited Vulnerabilities catalog (about 1.7 MB), keeps the 10 most
 * recently added entries with the six fields the ticker shows, and stores that
 * small payload in the edge cache for EDGE_TTL seconds. Every other request in
 * that window is a cache hit that never touches CISA and costs no CPU.
 *
 * Failure handling, in order:
 *   1. upstream unreachable / slow / non-200 / not JSON  -> serve the committed
 *      snapshot at /assets/kev-latest.json (kept by tools/local-sync/sync-kev.py)
 *   2. snapshot missing too                              -> 503 JSON, not cached
 *
 * The response schema is the snapshot's schema plus "mode" and "dateReleased",
 * so assets/umbra.js and anyone curling the old file can read either. The
 * X-KEV-Source header says which path answered: live | snapshot | none, or
 * cache-live / cache-snapshot for an edge-cache hit on either of the first two.
 *
 * No secrets, no bindings beyond the built-in ASSETS, no cron: the data stays
 * fresh because the edge cache expires, not because anything runs on a schedule.
 * Ships with tools/local-deploy/deploy.sh (wrangler compiles functions/ from the
 * staged archive). Tests: npm test
 */

const UPSTREAM = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json";
const SNAPSHOT_PATH = "/assets/kev-latest.json";

// Same field list and limit as sync-kev.py, so live and snapshot look alike.
const KEEP = ["cveID", "vendorProject", "product", "vulnerabilityName", "dateAdded", "knownRansomwareCampaignUse"];
const LIMIT = 10;

const EDGE_TTL = 3600;          // seconds a live payload stays in the edge cache
const BROWSER_TTL = 300;        // seconds a browser may reuse it without asking
const FALLBACK_TTL = 300;       // seconds a snapshot fallback is cached during an outage
const UPSTREAM_TIMEOUT_MS = 8000;
const USER_AGENT = "umbrasec-kev-api (+https://umbrasec.dev/api/kev)";

// CISA text can carry en and em dashes; the site uses plain hyphens only.
const plain = (v) => (typeof v === "string" ? v.replace(/[\u2013\u2014]/g, "-") : v);

function headers(source, overrides) {
  return {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": `public, max-age=${BROWSER_TTL}, s-maxage=${EDGE_TTL}`,
    "Access-Control-Allow-Origin": "*",
    "X-Content-Type-Options": "nosniff",
    "X-KEV-Source": source,
    // _headers only applies to static assets; keep Function responses in step.
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    ...overrides,
  };
}

// Reduce the full catalog to the ticker payload. Exported for tests.
export function trim(raw) {
  const vulns = Array.isArray(raw.vulnerabilities) ? raw.vulnerabilities : [];
  const newest = vulns
    .slice()
    .sort((a, b) => String(b.dateAdded || "").localeCompare(String(a.dateAdded || "")))
    .slice(0, LIMIT);
  return {
    source: UPSTREAM,
    mode: "live",
    catalogVersion: raw.catalogVersion ?? null,
    dateReleased: raw.dateReleased ?? null,
    synced: new Date().toISOString().slice(0, 10),
    count: typeof raw.count === "number" ? raw.count : vulns.length,
    vulnerabilities: newest.map((v) => Object.fromEntries(KEEP.map((k) => [k, plain(v[k] ?? "")]))),
  };
}

// One cache entry per origin+path; query strings must not fragment the cache.
function cacheKeyFor(request) {
  const u = new URL(request.url);
  return new Request(u.origin + u.pathname, { method: "GET" });
}

async function fetchLive() {
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
  return trim(raw);
}

async function fetchSnapshot(request, env) {
  const target = new URL(SNAPSHOT_PATH, request.url).toString();
  const res = await env.ASSETS.fetch(new Request(target, { method: "GET" }));
  if (!res.ok) throw new Error("snapshot " + res.status);
  return res.text();
}

export async function onRequestGet(context) {
  const { request, env } = context;
  const cache = caches.default;
  const key = cacheKeyFor(request);

  const hit = await cache.match(key);
  if (hit) {
    const out = new Response(hit.body, hit);
    // keep what the cached copy was, so a cached outage fallback is visible
    out.headers.set("X-KEV-Source", "cache-" + (hit.headers.get("X-KEV-Source") || "unknown"));
    return out;
  }

  let liveError;
  try {
    const body = JSON.stringify(await fetchLive(), null, 2) + "\n";
    const res = new Response(body, { status: 200, headers: headers("live") });
    context.waitUntil(cache.put(key, res.clone()));
    return res;
  } catch (err) {
    liveError = err;
  }

  try {
    const body = await fetchSnapshot(request, env);
    const res = new Response(body, {
      status: 200,
      headers: headers("snapshot", { "Cache-Control": `public, max-age=60, s-maxage=${FALLBACK_TTL}` }),
    });
    context.waitUntil(cache.put(key, res.clone()));
    return res;
  } catch (err) {
    // The reasons go to the Functions log, not the public body.
    const detail = [liveError, err].map((e) => (e && e.message) || String(e)).join("; ");
    console.error("kev: " + detail);
    return new Response(JSON.stringify({ error: "KEV data unavailable" }) + "\n", {
      status: 503,
      headers: headers("none", { "Cache-Control": "no-store" }),
    });
  }
}

// HEAD shares the GET path; the runtime drops the body.
export const onRequestHead = onRequestGet;
