#!/usr/bin/env python3
"""Check the invariants that have actually broken in this repo.

    python3 scripts/verify_repo.py          # all checks
    python3 scripts/verify_repo.py --quick  # skip the export checks

Exits non-zero on the first category with failures, so it works as a pre-push
hook or a CI step. Every check here exists because the thing it tests went
wrong at least once:

  * figures drifting from the dataset they claim to come from
  * placeholder text surviving into a publishable page
  * a stale scaffold in maps/ shadowing a written page
  * unbalanced markup from a bad regex substitution
  * export paths that look absolute but contain a traversal and 404
  * an image URL pointing at a file that is not in the repo
"""
import argparse
import csv
import glob
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://cdn.jsdelivr.net/gh/jtcompass212/TheChenTeam@main"


def money(v):
    v = float(v)
    return f"${v / 1_000_000:.2f}M" if v >= 1_000_000 else f"${v:,.0f}"


def published():
    return (sorted(ROOT.glob("city-pages/*.html"))
            + sorted(ROOT.glob("neighborhood-pages/*/*.html")))


def load_records():
    recs = {}
    for f in sorted(glob.glob(str(ROOT / "data/market/market-data-*.csv"))):
        for r in csv.DictReader(open(f)):
            if r.get("kind", "nbhd") != "nbhd":
                continue
            recs[((r.get("city") or "san-mateo"), r["slug"])] = r
    return recs


def check_figures():
    out, n = [], 0
    for (city, slug), r in load_records().items():
        p = ROOT / "neighborhood-pages" / city / f"{slug}.html"
        if not p.exists():
            out.append(f"{city}/{slug}: data row has no page")
            continue
        h = p.read_text()
        if r["basis"] == "none":
            continue
        # A blank medSqft is a gap in the pull, not a broken page — check the
        # figures that exist rather than crashing on the ones that do not.
        wanted = [money(r["medPrice"]), f"{r['sales']} closed sale"]
        if r["medSqft"]:
            wanted.append(f"${int(r['medSqft']):,}")
        for want in wanted:
            n += 1
            if want not in h:
                out.append(f"{city}/{slug}: {want!r} not on the page")
        if int(r["sales"]) < 3:
            out.append(f"{city}/{slug}: publishes on {r['sales']} closed sales")
    return out, f"{n} figures trace to the datasets"


def check_placeholders():
    out = []
    for p in published():
        for tok in re.findall(r"\[ (?!HERO IMAGE\b|IMAGE\b)[^\]]{0,60}\]", p.read_text()):
            out.append(f"{p.relative_to(ROOT)}: placeholder {tok!r}")
    return out, f"{len(published())} pages free of placeholder text"


def check_stale_scaffolds():
    out = []
    written = {(p.parent.name, p.stem) for p in ROOT.glob("neighborhood-pages/*/*.html")}
    for p in ROOT.glob("maps/*/*.html"):
        if p.stem.endswith("-map"):
            continue
        if (p.parent.name, p.stem) in written:
            out.append(f"{p.relative_to(ROOT)} shadows a written page — delete it")
    return out, "no scaffold shadows a written page"


def check_markup():
    out = []
    for p in published():
        h = p.read_text()
        if len(re.findall(r"<div\b", h)) != h.count("</div>"):
            out.append(f"{p.relative_to(ROOT)}: unbalanced <div>")
    return out, "markup balanced"


def check_export():
    out = []
    srcs = [(p, p.name if p.parent.name == "city-pages"
             else f"{p.parent.name}/{p.name}") for p in published()]
    for _src, rel in srcs:
        e = ROOT / "sierra-export" / rel
        if not e.exists():
            out.append(f"sierra-export/{rel} missing — run scripts/build_sierra.py")
            continue
        t = e.read_text()
        if re.search(r'(?:src|href)="(?!https?://|#|/|mailto:|tel:)', t):
            out.append(f"sierra-export/{rel}: relative path would 404 on paste")
        for bad in re.findall(r'(?:src|href)="(https?://[^"]*/\.\./[^"]*)"', t):
            out.append(f"sierra-export/{rel}: traversal in URL {bad!r}")
        for url in re.findall(rf'src="{re.escape(BASE)}/([^"]+)"', t):
            if not (ROOT / url).exists():
                out.append(f"sierra-export/{rel}: image not in repo — {url}")
    return out, f"{len(srcs)} exported pages resolve"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="skip export checks")
    args = ap.parse_args()

    checks = [("market figures", check_figures),
              ("placeholder text", check_placeholders),
              ("stale scaffolds", check_stale_scaffolds),
              ("markup", check_markup)]
    if not args.quick:
        checks.append(("sierra export", check_export))

    failed = 0
    for label, fn in checks:
        problems, summary = fn()
        if problems:
            failed += len(problems)
            print(f"FAIL  {label}")
            for p in problems[:12]:
                print(f"        {p}")
            if len(problems) > 12:
                print(f"        ... and {len(problems) - 12} more")
        else:
            print(f"ok    {label:18} {summary}")

    if failed:
        print(f"\n{failed} problem(s). Nothing was changed.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
