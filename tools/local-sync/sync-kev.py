#!/usr/bin/env python3
"""
Refresh assets/kev-latest.json from the public CISA KEV catalog.

This is the homepage ticker's data. It used to run twice a day from a GitHub
Action; that repo is gone and this site has no CI by design, so the sync is a
deliberate local step now: run this, check the diff, commit, deploy.

Zero dependencies - standard library only.

Usage:
    tools/local-sync/sync-kev.py           # fetch and write if changed
    tools/local-sync/sync-kev.py --check   # report drift, write nothing
    tools/local-sync/sync-kev.py --quiet   # for cron: silent unless it wrote

Exit status:
    0  file is current, or was updated
    1  fetch failed (always 0 under --quiet)
    2  --check found the file is stale

Cron it hourly, staying silent until CISA actually publishes something:

    17 * * * * cd /path/to/umbrasec && python3 tools/local-sync/sync-kev.py --quiet

That only refreshes the file on disk. Committing and deploying stay manual, so
nothing reaches the repo or the live site without you looking at it first - run
`git status`, then `tools/local-deploy/deploy.sh`.
"""

import argparse
import datetime
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
TARGET = Path(__file__).resolve().parents[2] / "assets" / "kev-latest.json"

# The ticker shows the 10 most recent additions, and only these fields. Trimming
# here keeps the file small - the full catalog is several megabytes.
KEEP = ["cveID", "vendorProject", "product", "vulnerabilityName",
        "dateAdded", "knownRansomwareCampaignUse"]
LIMIT = 10


def build():
    req = urllib.request.Request(URL, headers={"User-Agent": "umbrasec-kev-sync"})
    raw = json.load(urllib.request.urlopen(req, timeout=60))

    vulns = sorted(raw["vulnerabilities"], key=lambda v: v["dateAdded"], reverse=True)[:LIMIT]
    return {
        "source": URL,
        "catalogVersion": raw.get("catalogVersion"),
        "synced": datetime.date.today().isoformat(),
        "count": raw.get("count"),
        "vulnerabilities": [{k: v.get(k, "") for k in KEEP} for v in vulns],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="report whether the file is stale; write nothing")
    ap.add_argument("--quiet", action="store_true",
                    help="say nothing unless the file changed; for cron")
    args = ap.parse_args()

    try:
        fresh = build()
    except (urllib.error.URLError, OSError, KeyError, ValueError) as exc:
        # Under cron a transient network failure is not worth an email - the
        # next run picks it up. Stay silent and exit clean.
        if args.quiet:
            return 0
        print(f"sync-kev: fetch failed: {exc}", file=sys.stderr)
        return 1

    new_text = json.dumps(fresh, indent=2) + "\n"
    old_text = TARGET.read_text() if TARGET.exists() else ""

    # "synced" is today's date, so it always differs. Compare everything else,
    # otherwise a run on a quiet day produces a commit with no real change.
    old_data = json.loads(old_text) if old_text else {}
    same = {k: v for k, v in fresh.items() if k != "synced"} == \
           {k: v for k, v in old_data.items() if k != "synced"}

    if same:
        if not args.quiet:
            print(f"sync-kev: already current - catalog {fresh['catalogVersion']}, "
                  f"{fresh['count']} entries. Nothing written.")
        return 0

    if args.check:
        print(f"sync-kev: STALE - local catalog "
              f"{old_data.get('catalogVersion', 'none')} vs upstream {fresh['catalogVersion']}",
              file=sys.stderr)
        return 2

    TARGET.write_text(new_text)
    print(f"sync-kev: updated {TARGET.name} - catalog {fresh['catalogVersion']}, "
          f"{fresh['count']} entries, {len(fresh['vulnerabilities'])} shown.")
    print("sync-kev: review with 'git diff', then commit and deploy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
