/* / - the home page, served through a Function so each fetch carries a unique
 * research canary. THROWAWAY SPIKE, see tools/canary/canary-lib.js.
 *
 * Fetches the static index.html from the ASSETS binding, appends three hidden
 * placements with a fresh id, logs the fetch to KV, and returns the page.
 * If the asset is not HTML or not 200 it is passed through untouched.
 */

import { newId, describe, record, canaryMarkup } from "../tools/canary/canary-lib.js";

// Mirror _headers: that file only applies to static responses, not to a page
// served by a Function.
const PAGE_HEADERS = {
  "Cache-Control": "public, max-age=0, must-revalidate",
  "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
  "X-Frame-Options": "DENY",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
  "Content-Security-Policy": "object-src 'none'; base-uri 'self'; frame-ancestors 'none'",
};

export async function onRequestGet(context) {
  const { request, env } = context;
  const url = new URL(request.url);

  // A bare GET, so a browser's If-None-Match never yields a 304 that would
  // skip the injection.
  const asset = await env.ASSETS.fetch(new Request(url.origin + "/", { method: "GET" }));
  const type = asset.headers.get("content-type") || "";
  if (!asset.ok || !type.includes("text/html")) return asset;

  const id = newId();
  context.waitUntil(record(env, "p", { id, path: url.pathname, ...describe(request) }));

  const markup = canaryMarkup(url.origin, id);
  const out = new HTMLRewriter()
    .on("body", { element(el) { el.append(markup, { html: true }); } })
    .transform(asset);

  const headers = new Headers(out.headers);
  headers.delete("etag");          // body changed, the asset's tag is wrong now
  headers.delete("content-length");
  for (const [k, v] of Object.entries(PAGE_HEADERS)) headers.set(k, v);
  headers.set("X-Canary", "1");
  return new Response(out.body, { status: out.status, headers });
}

export const onRequestHead = onRequestGet;
