#!/usr/bin/env python3
"""Patch neighborhood pages with market figures from data/market/*.csv.

Usage:
    python3 scripts/apply_market_data.py            # all neighborhood pages
    python3 scripts/apply_market_data.py aragon ... # just these slugs

Only touches the Market Snapshot block. Prose, images and every other section
are left alone. Re-running is safe: the block is rewritten from the CSV each
time, so a data refresh is a re-run rather than a re-edit.
"""
import csv
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
NBHD = ROOT / "neighborhood-pages" / "san-mateo"
DATA = sorted((ROOT / "data" / "market").glob("market-data-*.csv"))[-1]
UPDATED = "20 August 2026"

DISCLAIMER = (
    "Compass is a real estate broker licensed by the State of California and makes no "
    "representation as to the accuracy or completeness of this information. "
    "Equal Housing Opportunity."
)

# A year-over-year figure can be real arithmetic and still a misleading
# headline: below a certain sale count the median tracks which specific homes
# traded, not the direction of the market. Quarter-over-quarter on the same
# data swung +37% and -32%, which is what that noise looks like.
#
# The median, the window and the sale count always publish. Only the
# percentage arrow is withheld, and the footnote says why.
MIN_SALES_FOR_DELTA = 8

# Pages suppressed despite clearing the threshold, with the reason attached so
# it survives the next data refresh.
SUPPRESS_DELTA = {
    "san-mateo-park": "a 10-sale quarter in a luxury enclave where one estate "
                      "moves the median several hundred thousand dollars",
}


def money(v):
    """$3.45M above a million, else $825,000 — matches the card's display width."""
    v = float(v)
    return f"${v / 1_000_000:.2f}M" if v >= 1_000_000 else f"${v:,.0f}"


def period_label(basis, period):
    if basis == "quarter":
        year, q = period.split("-")
        return f"{q} {year}"
    if basis == "year":
        return period
    year, month = period.split("-")
    name = ["January", "February", "March", "April", "May", "June", "July",
            "August", "September", "October", "November", "December"][int(month) - 1]
    return f"{name} {year}"


def prior_label(basis, period):
    """The comparison window, for the YoY caption."""
    if basis == "quarter":
        year, q = period.split("-")
        return f"{q} {int(year) - 1}"
    if basis == "year":
        return str(int(period) - 1)
    year, month = period.split("-")
    return period_label(basis, f"{int(year) - 1}-{month}")


def load():
    with DATA.open() as fh:
        return {r["slug"]: r for r in csv.DictReader(fh) if r["kind"] == "nbhd"}


def snapshot_html(name, rec):
    basis, period, slug = rec["basis"], rec["period"], rec["slug"]
    label = period_label(basis, period)
    sales = int(rec["sales"])
    types = ("Single-Family Homes" if rec["types"] == "SF"
             else "All Property Types")

    # Delta only when the comparison window itself cleared the sale-count bar,
    # and not where the swing is a mix effect rather than a market move.
    thin = sales < MIN_SALES_FOR_DELTA
    if slug in SUPPRESS_DELTA or thin:
        delta = ('<div style="font-size: 13px; color: #7d8598; margin-top: 6px;">'
                 f'{label}</div>')
    elif rec["yoyPct"]:
        pct = float(rec["yoyPct"])
        colour = "#3f8a5f" if pct >= 0 else "#b0433f"
        arrow = "&#9650;" if pct >= 0 else "&#9660;"
        delta = (f'<div style="font-size: 13px; color: {colour}; font-weight: 600; '
                 f'margin-top: 6px;">{arrow} {abs(pct):.1f}% vs {prior_label(basis, period)}</div>')
    else:
        delta = ('<div style="font-size: 13px; color: #7d8598; margin-top: 6px;">'
                 'No prior-year comparison</div>')

    note = ""
    if slug in SUPPRESS_DELTA:
        note += (f" A year-over-year change is not shown: this is "
                 f"{SUPPRESS_DELTA[slug]}, so the figure would describe which homes "
                 f"sold rather than where the market moved.")
    elif thin and rec["yoyPct"]:
        note += (f" A year-over-year change is not shown: with {sales} closed sales in "
                 f"the window, the median reflects which specific homes traded rather "
                 f"than the direction of the market.")
    if rec["types"] != "SF":
        note = (f" {name} has effectively no detached single-family market, so these figures "
                f"cover single-family homes, condominiums and townhouses together.")
    if basis == "year":
        note += (f" Reported over a full year because quarterly sale counts in {name} "
                 f"are too small to support a median.")
    elif period != "2026-Q2":
        note += (f" {label} is the most recent window with enough closed sales to report.")

    source = (f"Source: Compass Market Insights &mdash; {types.lower()} in {name}, {label} "
              f"({sales} closed sale{'s' if sales != 1 else ''}). Neighborhood figures are "
              f"reported quarterly because monthly sale counts here are too small to be "
              f"meaningful.{note} Updated {UPDATED}. {DISCLAIMER}")

    return f'''<span style="font-size: 13px; color: #7d8598;">Market Snapshot &middot; {types}, {label}</span></div>
      <div style="display: grid; grid-template-columns: repeat(2, 1fr);">
        <div style="padding: 32px 26px; text-align: center; border-right: 1px solid rgb(237, 239, 243);">
          <div style="font-family: Fraunces, serif; font-size: 44px; color: #16233f; line-height: 1;">{money(rec["medPrice"])}</div>
          <div style="font-size: 13px; color: #7d8598; margin-top: 10px; letter-spacing: 0.04em;">Median Sold Price</div>
          {delta}
        </div>
        <div style="padding: 32px 26px; text-align: center;">
          <div style="font-family: Fraunces, serif; font-size: 44px; color: #16233f; line-height: 1;">${int(rec["medSqft"]):,}</div>
          <div style="font-size: 13px; color: #7d8598; margin-top: 10px; letter-spacing: 0.04em;">Median Price / Sq. Ft.</div>
          <div style="font-size: 13px; color: #7d8598; margin-top: 6px;">{sales} closed sale{"s" if sales != 1 else ""}</div>
        </div>
      </div>
    </div>
    <p style="font-size: 12px; color: #9ba3b5; margin: 10px 4px 0px;">{source}</p>'''


# Spans from the snapshot header's trailing <span> through the placeholder footnote.
BLOCK = re.compile(
    r'<span style="font-size: 13px; color: #7d8598;">Market Snapshot.*?'
    r'<p style="font-size: 12px; color: #9ba3b5;[^>]*>.*?</p>',
    re.S,
)


def main():
    records = load()
    wanted = sys.argv[1:] or sorted(records)
    changed, skipped = [], []

    for slug in wanted:
        page = NBHD / f"{slug}.html"
        rec = records.get(slug)
        if not page.exists():
            skipped.append((slug, "no page"))
            continue
        if not rec or rec["basis"] == "none" or not rec["medPrice"]:
            skipped.append((slug, "no usable data"))
            continue

        html = page.read_text()
        name_match = re.search(
            r'font-weight: 500;">([^<]+)</span> <span style="font-size: 13px; '
            r'color: #7d8598;">Market Snapshot', html)
        if not name_match:
            skipped.append((slug, "header not matched"))
            continue

        new_html, n = BLOCK.subn(
            lambda _m: snapshot_html(name_match.group(1), rec), html, count=1)
        if n != 1:
            skipped.append((slug, "snapshot block not matched"))
            continue

        new_html = new_html.replace("<!-- 2. MARKET SNAPSHOT (PLACEHOLDER DATA) -->",
                                    "<!-- 2. MARKET SNAPSHOT -->")
        page.write_text(new_html)
        changed.append(f"{slug}: {money(rec['medPrice'])} / ${int(rec['medSqft']):,} "
                       f"({period_label(rec['basis'], rec['period'])}, {rec['sales']} sales)")

    print(f"source: {DATA.name}")
    print(f"\nupdated {len(changed)}:")
    for line in changed:
        print("  " + line)
    if skipped:
        print(f"\nskipped {len(skipped)}:")
        for slug, why in skipped:
            print(f"  {slug}: {why}")


if __name__ == "__main__":
    main()
