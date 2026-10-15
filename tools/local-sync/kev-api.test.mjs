// Tests for functions/api/kev.js (the Pages Function behind /api/kev).
// Zero dependencies: npm test   (node --test 'tools/**/*.test.mjs')
//
// The function is exercised with mocked globals: `fetch` for the CISA upstream,
// `caches.default` for the edge cache, and `env.ASSETS` for the committed
// snapshot. Each test installs its own mocks before calling the handler.

import { test } from "node:test";
import assert from "node:assert/strict";
import { onRequestGet, onRequestHead, trim } from "../../functions/api/kev.js";

const SNAPSHOT = {
  source: "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
  catalogVersion: "2026.10.02",
  synced: "2026-10-03",
  count: 1733,
  vulnerabilities: [{ cveID: "CVE-2026-1", vendorProject: "Snap", product: "Shot", vulnerabilityName: "n", dateAdded: "2026-10-02", knownRansomwareCampaignUse: "Unknown" }],
};
const SNAPSHOT_TEXT = JSON.stringify(SNAPSHOT, null, 2) + "\n";

// 12 entries with deliberately unsorted dates and extra fields that must be dropped.
const UPSTREAM = {
  title: "CISA Catalog of Known Exploited Vulnerabilities",
  catalogVersion: "2026.10.14",
  dateReleased: "2026-10-14T19:27:28.0105Z",
  count: 12,
  vulnerabilities: Array.from({ length: 12 }, (_, i) => ({
    cveID: `CVE-2026-${1000 + i}`,
    vendorProject: "Vendor" + i,
    product: "Product" + i,
    vulnerabilityName: "Vuln " + i,
    dateAdded: `2026-10-${String(1 + (i * 7) % 28).padStart(2, "0")}`,
    shortDescription: "drop me",
    requiredAction: "drop me",
    dueDate: "2026-11-01",
    knownRansomwareCampaignUse: i % 3 ? "Unknown" : "Known",
    notes: "",
    cwes: [],
  })),
};

function installCache(hit) {
  const puts = [], matches = [];
  globalThis.caches = {
    default: {
      match: async (k) => { matches.push(k); return hit; },
      put: async (k, r) => { puts.push([k, r]); },
    },
  };
  return { puts, matches };
}

function installFetch(impl) {
  const calls = [];
  globalThis.fetch = async (u, init) => { calls.push([String(u), init]); return impl(u, init); };
  return calls;
}

function makeContext({ url = "https://umbrasec.dev/api/kev", method = "GET", assets } = {}) {
  const pending = [];
  const env = {
    ASSETS: assets || { fetch: async () => new Response(SNAPSHOT_TEXT, { status: 200, headers: { "content-type": "application/json" } }) },
  };
  return { ctx: { request: new Request(url, { method }), env, waitUntil: (p) => pending.push(p) }, pending };
}

const okUpstream = () => new Response(JSON.stringify(UPSTREAM), { status: 200, headers: { "content-type": "application/json" } });

test("live path: fetches upstream, trims to the 10 newest, caches, sets headers", async () => {
  const { puts } = installCache(undefined);
  const calls = installFetch(okUpstream);
  const { ctx, pending } = makeContext();

  const res = await onRequestGet(ctx);
  await Promise.all(pending);

  assert.equal(res.status, 200);
  assert.equal(res.headers.get("content-type"), "application/json; charset=utf-8");
  assert.equal(res.headers.get("access-control-allow-origin"), "*");
  assert.equal(res.headers.get("x-kev-source"), "live");
  assert.match(res.headers.get("cache-control"), /s-maxage=\d+/);
  assert.equal(calls.length, 1);
  assert.match(calls[0][0], /cisa\.gov/);

  const text = await res.text();
  const body = JSON.parse(text);
  assert.equal(body.mode, "live");
  assert.equal(body.catalogVersion, "2026.10.14");
  assert.equal(body.dateReleased, "2026-10-14T19:27:28.0105Z");
  assert.equal(body.count, 12);
  assert.match(body.synced, /^\d{4}-\d{2}-\d{2}$/);
  assert.equal(body.vulnerabilities.length, 10);
  assert.equal(body.vulnerabilities[0].dateAdded, "2026-10-22");
  assert.equal(body.vulnerabilities[9].dateAdded, "2026-10-01");
  for (let i = 1; i < body.vulnerabilities.length; i++) {
    assert.ok(body.vulnerabilities[i - 1].dateAdded >= body.vulnerabilities[i].dateAdded, "sorted newest first");
  }
  assert.deepEqual(Object.keys(body.vulnerabilities[0]),
    ["cveID", "vendorProject", "product", "vulnerabilityName", "dateAdded", "knownRansomwareCampaignUse"]);

  assert.equal(puts.length, 1, "trimmed response was written to the edge cache");
  assert.equal(await puts[0][1].text(), text, "cached body is byte-identical to the served body");
});

test("cache hit: served from the edge cache without touching upstream", async () => {
  const cached = new Response('{"mode":"live","vulnerabilities":[]}', { status: 200, headers: { "content-type": "application/json; charset=utf-8", "x-kev-source": "live" } });
  installCache(cached);
  const calls = installFetch(() => { throw new Error("must not be called"); });
  const { ctx } = makeContext();

  const res = await onRequestGet(ctx);
  assert.equal(res.status, 200);
  assert.equal(res.headers.get("x-kev-source"), "cache");
  assert.equal(calls.length, 0);
  assert.deepEqual(await res.json(), { mode: "live", vulnerabilities: [] });
});

test("cache key ignores the query string", async () => {
  const { matches, puts } = installCache(undefined);
  installFetch(okUpstream);
  const { ctx, pending } = makeContext({ url: "https://umbrasec.dev/api/kev?cachebust=1&x=y" });
  await onRequestGet(ctx);
  await Promise.all(pending);
  assert.equal(new URL(matches[0].url).search, "");
  assert.equal(new URL(puts[0][0].url).pathname, "/api/kev");
});

for (const [name, impl] of [
  ["network error", () => { throw new TypeError("fetch failed"); }],
  ["upstream 503", () => new Response("down", { status: 503 })],
  ["upstream not JSON", () => new Response("<html>maintenance</html>", { status: 200 })],
  ["upstream wrong shape", () => new Response('{"hello":"world"}', { status: 200 })],
]) {
  test(`fallback on ${name}: serves the committed snapshot`, async () => {
    const { puts } = installCache(undefined);
    installFetch(impl);
    const { ctx, pending } = makeContext();
    const res = await onRequestGet(ctx);
    await Promise.all(pending);
    assert.equal(res.status, 200);
    assert.equal(res.headers.get("x-kev-source"), "snapshot");
    assert.equal(res.headers.get("access-control-allow-origin"), "*");
    assert.equal(await res.text(), SNAPSHOT_TEXT);
    assert.equal(puts.length, 1, "snapshot fallback is cached briefly so an outage does not re-hit upstream per request");
    assert.match(puts[0][1].headers.get("cache-control"), /s-maxage=300/);
  });
}

test("upstream and snapshot both unavailable: 503 JSON, not cached", async () => {
  const { puts } = installCache(undefined);
  installFetch(() => { throw new Error("boom"); });
  const { ctx, pending } = makeContext({ assets: { fetch: async () => new Response("nope", { status: 404 }) } });
  const res = await onRequestGet(ctx);
  await Promise.all(pending);
  assert.equal(res.status, 503);
  assert.equal(res.headers.get("cache-control"), "no-store");
  assert.equal(res.headers.get("x-kev-source"), "none");
  const body = await res.json();
  assert.equal(body.error, "KEV data unavailable");
  assert.equal(puts.length, 0);
});

test("HEAD is handled by the same code path and fills the GET-keyed cache", async () => {
  const { puts } = installCache(undefined);
  installFetch(okUpstream);
  const { ctx, pending } = makeContext({ method: "HEAD" });
  const res = await onRequestHead(ctx);
  await Promise.all(pending);
  assert.equal(res.status, 200);
  assert.equal(res.headers.get("x-kev-source"), "live");
  assert.equal(puts.length, 1);
  assert.equal(puts[0][0].method, "GET"); // cache.put rejects non-GET keys
});

test("trim(): tolerates missing fields and never emits undefined", () => {
  const out = trim({ vulnerabilities: [{ cveID: "CVE-1" }, { cveID: "CVE-2", dateAdded: "2026-01-01" }] });
  assert.equal(out.catalogVersion, null);
  assert.equal(out.count, 2);
  assert.equal(out.vulnerabilities[0].cveID, "CVE-2");
  assert.equal(out.vulnerabilities[1].vendorProject, "");
  for (const v of out.vulnerabilities) {
    for (const k of ["cveID", "vendorProject", "product", "vulnerabilityName", "dateAdded", "knownRansomwareCampaignUse"]) {
      assert.notEqual(v[k], undefined, k + " must be present, never undefined");
    }
  }
});
