#!/usr/bin/env python3
"""Stamp the CARTO basemap key onto every map widget.

    python3 scripts/set_carto_key.py            # apply the key in data/carto-basemap-key.txt
    python3 scripts/set_carto_key.py --check    # verify only; exit 1 if any map is missing it

CARTO began requiring a key for its raster basemap endpoints in Aug 2026. Without
one every tile is stamped "API KEY REQUIRED" — which is what the live site showed
across all 144 maps until this was run.

The key lives in data/carto-basemap-key.txt, one line, and nowhere else. Rotating
it is: edit that file, run this, rebuild the exports, republish the widgets. That
is the whole reason this script exists rather than 144 hand edits.

This is a client-side basemap key. It ships in public HTML and is visible to
anyone who views source — that is how these keys work, and it is why CARTO lets
you restrict a key to specific domains. Restrict it; do not treat it as a secret.
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
KEY_FILE = ROOT / "data" / "carto-basemap-key.txt"
MAPS = ROOT / "maps"

# Any cartocdn raster tile URL, with or without a key already appended.
TILE = re.compile(r"(https://\{s\}\.basemaps\.cartocdn\.com/[^'\"\s]*?\.png)(\?key=[^'\"\s]*)?")


def read_key():
    if not KEY_FILE.exists():
        sys.exit(f"missing {KEY_FILE.relative_to(ROOT)} — put the CARTO key in it, one line")
    key = KEY_FILE.read_text().strip()
    if not key:
        sys.exit(f"{KEY_FILE.relative_to(ROOT)} is empty")
    return key


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify only; do not write")
    args = ap.parse_args()

    key = read_key()
    want = f"?key={key}"

    changed = missing = total = 0
    for p in sorted(MAPS.rglob("*.html")):
        s = p.read_text()
        hits = TILE.findall(s)
        if not hits:
            continue
        total += 1
        new = TILE.sub(lambda m: m.group(1) + want, s)
        if new == s:
            continue
        if args.check:
            missing += 1
            print(f"  missing/stale key: {p.relative_to(ROOT)}")
        else:
            p.write_text(new)
            changed += 1

    if args.check:
        print(f"{total} map files carry a CARTO tile URL; {missing} missing or stale")
        return 1 if missing else 0

    print(f"stamped the key onto {changed} of {total} map files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
