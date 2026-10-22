<p align="center">
  <a href="https://umbrasec.dev"><img src="assets/umbra-icon-v2.png" alt="UMBRASEC logo" width="96" height="96"></a>
</p>

# UMBRASEC

**The open-source tooling behind [umbrasec.dev](https://umbrasec.dev)** - runnable Sigma
rules and KQL queries, a zero-dependency CISA KEV monitor, a trimmed KEV feed, and a
single-page blue-team reference. Defensive in scope, every claim tied to a primary source.

These are artefacts from the published research, not a product line.

[![License: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![Site](https://img.shields.io/badge/site-umbrasec.dev-8a2be2)](https://umbrasec.dev)

## Try it in 10 seconds

`kev-watch` needs Python 3.9+ and nothing else - no packages, no install step:

```bash
git clone https://github.com/umbrasec-labs/umbrasec.dev
python3 Umbrasec/tools/kev-watch/kev_watch.py --watch fortinet ivanti citrix
```

That prints newly-added, **actively exploited** CVEs from CISA's Known Exploited
Vulnerabilities catalog, filtered to the vendors you actually run:

```text
CISA KEV catalog 2026.06.11 · 1618 total entries · mode: since

CVE-2026-10520
  Ivanti Sentry - Ivanti Sentry OS Command Injection Vulnerability
  added 2026-06-11   remediate by 2026-06-14
  action: Apply mitigations in accordance with vendor instructions ...
  https://nvd.nist.gov/vuln/detail/CVE-2026-10520

1 item(s) reported.
```

Public data only; it reads one JSON feed and never touches a target system.

## What's inside

| | What it is |
|---|---|
| [`tools/kev-watch/`](tools/kev-watch/) | Zero-dependency Python monitor for the CISA KEV catalog. Tracks newly added, actively exploited CVEs, filters to your stack, flags ransomware-linked entries, warns on remediation deadlines. |
| [`tools/sigma-pack/`](tools/sigma-pack/) | The detection rules from the research writeups as runnable files: Kerberoasting Sigma rules (T1558.003), OAuth consent-phishing KQL queries (T1528), LiteLLM command-injection Sigma rules (CVE-2026-42271, T1190), N-central post-exploitation rules (svchost masquerading T1036.005, cloudflared tunnel service install T1543.003 / T1572) and a Metabase reset-password SQL injection rule (CVE-2026-72898, T1190), each with tuning and false-positive notes. A per-rule [ATT&CK coverage table](tools/sigma-pack/#attck-coverage) maps every artifact to its technique. |
| [`functions/api/kev.js`](functions/api/kev.js) | The `/api/kev` endpoint behind the homepage ticker: a Cloudflare Pages Function that serves the 10 newest CISA KEV entries live, edge-cached, with the committed snapshot as fallback. Tests: `npm test`. |
| [`tools/blue-team-mapper/`](tools/blue-team-mapper/) | A single-page defender reference covering the defensive lifecycle: SIEM/log-source priority, detection engineering, IR flow chains, threat hunting, identity and cloud hardening, SOAR playbooks - ATT&CK-aligned. [Use it live](https://umbrasec.dev/tools/blue-team-mapper/). |
| [`research/`](https://umbrasec.dev/research/) | Detection and threat writeups: [Kerberoasting](https://umbrasec.dev/research/detecting-kerberoasting.html), [OAuth consent phishing in M365](https://umbrasec.dev/research/detecting-oauth-consent-phishing.html), [OWASP LLM Top 10 for defenders](https://umbrasec.dev/research/owasp-llm-top-10-for-defenders.html), [Securing AI agents](https://umbrasec.dev/research/securing-ai-agents.html), [LiteLLM command injection (CVE-2026-42271)](https://umbrasec.dev/research/detecting-litellm-command-injection.html), plus threat profiles and incident analyses aimed at Australian SMBs - [INC Ransom](https://umbrasec.dev/research/inc-ransom-australian-smb.html), [SafePay](https://umbrasec.dev/research/safepay-australian-smb.html), [the N-able N-central MSP compromise](https://umbrasec.dev/research/n-able-ncentral-msp-supply-chain.html) and [the Mathspace / Metabase breach](https://umbrasec.dev/research/mathspace-metabase-internal-tooling.html). Every rule in `sigma-pack` comes from one of the detection writeups. |
| [`guide/`](https://umbrasec.dev/guide/) | A free, staged security guide for small and mid-sized businesses - from zero to a defensible baseline, with every recommendation mapped to the ASD Essential Eight, ISO 27001:2022, and NIST CSF 2.0, and each step explained as what it is, why it matters, and what it costs. |

## The KEV feed, as a feed

A small JSON endpoint holding the **10 most recently added** actively-exploited
CVEs, newest first - handy for dashboards, tickers, and "what just got exploited"
checks without hitting cisa.gov yourself. It sends `Access-Control-Allow-Origin: *`,
so a browser page can read it directly:

```
https://umbrasec.dev/api/kev
```

```bash
# the five most recently added actively-exploited CVEs
curl -s https://umbrasec.dev/api/kev |
  jq -r '.vulnerabilities[:5][] | "\(.dateAdded)  \(.cveID)  \(.vendorProject) \(.product)"'
```

It is live: [`functions/api/kev.js`](functions/api/kev.js) is a Cloudflare Pages
Function that fetches CISA's catalog on demand, trims it, and caches the result at
the edge for an hour. If CISA is unreachable it serves the committed snapshot at
`/assets/kev-latest.json` instead (refreshed now and then with
[`tools/local-sync/sync-kev.py`](tools/local-sync/sync-kev.py)). The `X-KEV-Source`
response header says which one answered: `live`, `cache`, `snapshot`.

Fields per entry: `cveID`, `vendorProject`, `product`, `vulnerabilityName`,
`dateAdded`, `knownRansomwareCampaignUse`. Top level carries `catalogVersion`,
`dateReleased`, `synced`, `mode`, and `count` (the full catalog's entry count, not
this file's). It is deliberately a recent-entries feed, not a mirror - for the full
catalog, go to [CISA](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
or run `kev-watch`, which queries CISA's feed directly.

## Focus right now

- **Detection engineering** - writeups with rules you can actually run (Sigma, mapped to
  real event IDs and MITRE ATT&CK techniques), plus tuning and false-positive notes.
- **Honest threat analysis** - technical breakdowns of real techniques and CVEs, every
  claim tied to a primary source.
- **Open-source defensive tooling** - small, useful tools for defenders, built in the open.
- **LLM / AI security** - defensive coverage of prompt injection, the OWASP LLM Top 10,
  and securing tool-calling AI agents as a class of risk (several writeups live).
- **SMB security guidance** - a free, framework-grounded [guide](https://umbrasec.dev/guide/)
  taking a small business from zero to a defensible baseline, one stage at a time (plus a
  paid [vCISO service](https://umbrasec.dev/services) for businesses that want
  hands-on help getting there).

## Who's behind it

UMBRASEC is an independent defensive security practice run by **0xdev1**.
Seven years in governance, risk and compliance and in detection
engineering, including regulated and public-sector environments; the public practice started in
2026 and publishes under a handle because of that background.

The research and tools here are free and open; there is also a
[vCISO advisory service](https://umbrasec.dev/services) for small and mid-sized
businesses, with a Microsoft 365 / Entra ID review as the usual entry point. The
approach is the straightforward one - publish genuinely useful, well-sourced work,
and let it be checked.

Everything published is **defensive in scope**. The research explains how attacks work
*so defenders can detect and stop them* - no working exploits, malware, or offensive
tooling ships from here.

Site: **[umbrasec.dev](https://umbrasec.dev)** - contact details are on the site.

## Roadmap (later)

Planned directions as the project grows - not live yet, listed honestly as intent:

- **Threat intelligence** - tracking and analysis of real-world campaigns and infrastructure.

## Working on this repo

The research lists - the `index.html` featured trio, the `research/index.html` grid,
`feed.xml`, `sitemap.xml`, and each article's prev/next footer nav - are **generated**
from `research/articles.json` by `tools/site-build/build_indexes.py`. That manifest is the
single source of truth; the pre-commit hook blocks the commit if any derived file drifts
from it, or if a `research/*.html` page exists that the manifest does not list (an orphan).

A tracked pre-commit hook keeps them in sync: it regenerates the derived files and stages
them on every commit. Enable it once per clone:

```bash
git config core.hooksPath .githooks
```

Or regenerate by hand any time with `python3 tools/site-build/build_indexes.py` (add
`--check` to verify without writing). `npm test` runs the Pages Function tests
(`node --test`, no packages beyond the pinned wrangler); `npx wrangler pages dev .`
previews the site with `/api/kev` running locally. When you add an article, add it to
`research/articles.json` - dropping an HTML file into `research/` alone will not list it,
and the hook will flag it as an orphan until you do.

## Forking the site

This repo is also the source of [umbrasec.dev](https://umbrasec.dev). If you fork it
for your own project, swap these for your own details:

- **Scheduling link** - `services.html` has a `Book a scoping call` button pointing at
  `https://cal.com/0xdev1`. To change it, edit that one URL (marked with a
  `<!-- SCHEDULING: ... -->` comment).
- **Contact email** - the practice address is set in `index.html`, `services.html`,
  `about.html`, the palette in `assets/umbra.js`, and the hand-written footer of
  `tools/blue-team-mapper/index.html` (the site generator does not rewrite it).
- **GitHub** - `github.com/umbrasec-labs/umbrasec.dev` throughout.

## Corrections

Found a detection that misbehaves, a wrong citation, or an analysis that's off? That
feedback is welcome - [open an issue](https://github.com/umbrasec-labs/umbrasec.dev/issues).
Corrections are credited.

## License

Code and tools: MIT. Written research/content: © UMBRASEC, free to read.
