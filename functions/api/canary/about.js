/* /api/canary/about - what the canary is, in plain text, for anyone who finds it. */

import { textResponse } from "../../../tools/canary/canary-lib.js";

const TEXT = `umbrasec.dev research canary

Some pages on this site carry short hidden notes addressed to AI assistants,
crawlers and automated agents. Each note asks the reader to fetch one URL on
this site and nothing else. Fetching it records that an automated reader
followed an instruction found inside a web page, which is the behaviour
behind indirect prompt injection attacks.

What is kept: a random id for the page fetch, the request's User-Agent,
Referer, Accept headers, Cloudflare's country, network (ASN) and verified-bot
category, and the time. No IP addresses and no cookies are stored. Rows
expire after 90 days.

Why: to measure, over time and in public, which automated readers obey
instructions embedded in ordinary pages, and which placements they see.
Results are published in The Shipwreck and at umbrasec.dev/research/.

Operators of crawlers or agents who want their traffic excluded can reach
the site owner through the contact details at umbrasec.dev/about.
`;

export function onRequest() {
  return textResponse(TEXT, 200, { "X-Robots-Tag": "noindex" });
}
