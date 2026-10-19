/* /api/canary/report?token=... - joins page fetches with canary hits.
 * THROWAWAY SPIKE, see tools/canary/canary-lib.js.
 *
 * Needs CANARY_READ_TOKEN set as an environment variable on the Pages project;
 * without it the route 404s. Reads only KV key listings (rows live in key
 * metadata), so a report costs a handful of list calls and no gets.
 */

import { CHANNELS } from "../../../tools/canary/canary-lib.js";

const MAX_PAGES = 10; // KV list pages of up to 1000 keys each

async function listAll(kv, prefix) {
  const rows = [];
  let cursor;
  for (let i = 0; i < MAX_PAGES; i++) {
    const page = await kv.list({ prefix, cursor, limit: 1000 });
    for (const k of page.keys) if (k.metadata) rows.push(k.metadata);
    if (page.list_complete || !page.cursor) break;
    cursor = page.cursor;
  }
  return rows;
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body, null, 2) + "\n", {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Robots-Tag": "noindex",
      "X-Content-Type-Options": "nosniff",
    },
  });
}

function uaFamily(ua) {
  // Crude grouping for the summary: product token before the first slash or space.
  const m = /^([A-Za-z][\w.-]{1,40})/.exec(ua || "");
  return m ? m[1] : "(none)";
}

export async function onRequestGet(context) {
  const { request, env } = context;
  const expected = env.CANARY_READ_TOKEN;
  if (!expected) return new Response("not found\n", { status: 404 });

  const url = new URL(request.url);
  const auth = request.headers.get("authorization") || "";
  const given = url.searchParams.get("token") || auth.replace(/^Bearer\s+/i, "");
  if (given !== expected) return json({ error: "unauthorised" }, 401);
  if (!env.CANARY) return json({ error: "CANARY KV binding missing" }, 503);

  const [pages, hits] = await Promise.all([listAll(env.CANARY, "p:"), listAll(env.CANARY, "h:")]);

  const hitsById = new Map();
  for (const h of hits) {
    if (!hitsById.has(h.id)) hitsById.set(h.id, []);
    hitsById.get(h.id).push(h.ch);
  }

  const summary = {};
  for (const p of pages) {
    const fam = uaFamily(p.ua);
    const s = (summary[fam] ??= { fetches: 0, obeyed: 0, channels: {}, bot: new Set(), asOrg: new Set() });
    s.fetches++;
    const chs = hitsById.get(p.id) || [];
    if (chs.length) s.obeyed++;
    for (const c of chs) s.channels[c] = (s.channels[c] || 0) + 1;
    if (p.bot) s.bot.add(p.bot);
    if (p.asOrg) s.asOrg.add(p.asOrg);
  }
  for (const s of Object.values(summary)) {
    s.bot = [...s.bot];
    s.asOrg = [...s.asOrg].slice(0, 5);
  }

  const orphanHits = hits.filter((h) => !pages.some((p) => p.id === h.id));

  return json({
    generated: new Date().toISOString(),
    channels: CHANNELS,
    counts: { pageFetches: pages.length, canaryHits: hits.length, fetchesWithAnyHit: [...hitsById.keys()].length, orphanHits: orphanHits.length },
    summary,
    pages: pages.map((p) => ({ ...p, hits: hitsById.get(p.id) || [] })),
    hits,
  });
}
