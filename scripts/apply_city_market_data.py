#!/usr/bin/env python3
"""Patch city pages with market figures from data/market/*.csv.

    python3 scripts/apply_city_market_data.py --dry-run
    python3 scripts/apply_city_market_data.py [slug ...]

City pages are not uniform the way neighborhood pages are, so this is
deliberately conservative:

  * Only stats whose label maps to a Compass field are touched. Anything else
    (Avg. Offers per Home, Sold Above Asking, BART to Downtown SF, Distinct
    Neighborhoods, ...) is reported and left exactly as-is.
  * Bar charts are only rewritten when they are actually quarterly. Oakland's
    chart compares neighborhoods, so it is skipped.
  * Footnotes keep their page-specific analytical caveat; only the source
    attribution ahead of it is replaced.
"""
import argparse
import csv
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
CITY = ROOT / "city-pages"
DATA = sorted((ROOT / "data" / "market").glob("market-data-*.csv"))[-1]
UPDATED = "20 August 2026"

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

# label -> (field, canonical label). A canonical label of None keeps the
# existing wording; used where the original is already accurate.
SNAPSHOT = {
    "Median Sale Price": ("medPrice", "Median Sold Price"),
    "Median List Price": ("medPrice", "Median Sold Price"),
    "Median Sold Price": ("medPrice", None),
    "Citywide Median Sale Price": ("medPrice", "Citywide Median Sold Price"),
    "Avg. Days on Market": ("medDom", "Median Days on Market"),
    "Median Days on Market": ("medDom", None),
    "Avg. $ / Sq. Ft.": ("medSqft", "Median $ / Sq. Ft."),
    "Median $ / Sq. Ft.": ("medSqft", None),
    "Homes Listed": ("newListings", "New Listings"),
    "New Listings": ("newListings", None),
    "Homes Sold": ("sales", None),
    "Homes Sold (Monthly Avg.)": ("sales", "Homes Sold"),
    "Avg. Sale-to-List": ("spLp", "Sold / Original List Price"),
}

SIDECARD = {
    "Sale-to-List Ratio": ("spLp", "Sold / Original List Price"),
    "Avg. Sale-to-List": ("spLp", "Sold / Original List Price"),
    "Sold / Original List Price": ("spLp", None),
    "Months of Inventory": ("moi", None),
    "Avg. Days on Market": ("medDom", "Median Days on Market"),
    "Median Days on Market": ("medDom", None),
    "Homes Sold Last Month": ("sales", None),
    "Homes Sold (Trailing Year)": ("sold12mo", None),
    "Active Listings": ("active", None),
    "Citywide Days on Market": ("medDom", "Citywide Median Days on Market"),
}

# Charts that are not a four-quarter series. Rewriting these would be wrong.
SKIP_CHART = {"oakland"}


def fmt(field, value, sidecard=False):
    v = float(value)
    if field == "medPrice":
        return f"${v / 1_000_000:.2f}M" if v >= 1_000_000 else f"${v:,.0f}"
    if field == "medSqft":
        return f"${int(v):,}"
    if field == "medDom":
        return f"{int(v)} days" if sidecard else f"{int(v)}"
    if field == "spLp":
        return f"{v:.0f}%"
    if field == "moi":
        return f"{v:.1f}"
    return f"{int(v):,}"


def load():
    with DATA.open() as fh:
        rows = {r["slug"]: r for r in csv.DictReader(fh) if r["kind"] == "city"}
    for r in rows.values():
        if r["moi"] and r["sales"]:
            r["active"] = str(round(float(r["moi"]) * float(r["sales"])))
        else:
            r["active"] = ""
    return rows


def period_label(period):
    year, month = period.split("-")
    return f"{MONTHS[int(month) - 1]} {year}"


# value div immediately followed by its label div
SNAP_RE = re.compile(
    r'(<div style="font-family: Fraunces, serif; font-size: 40px;[^"]*">)([^<]*)(</div>\s*'
    r'<div style="font-size: 13px; color: #7d8598; margin-top: 10px; letter-spacing: 0\.04em;">)([^<]*)(</div>)')

# side card: label div then value div
SIDE_RE = re.compile(
    r'(<div style="font-size: 14px; color: #7d8598;">)([^<]*)(</div>\s*'
    r'<div style="font-family: Fraunces, serif; font-size: 26px;[^"]*">)([^<]*)(</div>)')

FOOTNOTE_RE = re.compile(
    r'(<p style="font-size: 12px; color: #9ba3b5; margin: 10px 4px 0px;[^>]*>)(.*?)(</p>)', re.S)

CHART_FOOT_RE = re.compile(
    r'(<p style="font-size: 12px; color: #9ba3b5; margin: 18px 0px 0px;[^>]*>)(.*?)(</p>)', re.S)

BARS_RE = re.compile(
    r'(<div style="flex: 1 1 0%; min-height: 200px; display: flex; align-items: flex-end; gap: 14px; padding-top: 10px;">)(.*?)(</div>\s*<p style="font-size: 12px; color: #9ba3b5; margin: 18px)',
    re.S)

# The 19 newer pages use a .bar-wrap/.bar-col/.bar structure with hover values.
BARWRAP_RE = re.compile(r'(<div class="bar-wrap">)(.*?)(</div>\s*<p style="font-size: 12px)', re.S)

# Scoped to the chart header so it can't hit the side cards. Some pages label
# this with a different metric entirely (Palo Alto "YoY ($/sqft)", Gilroy
# "3-mo. trend"); since every chart is rebuilt as quarterly median sold price,
# the caption is normalised to match the series actually drawn.
YOY_RE = re.compile(
    r'(<div style="display: flex; justify-content: space-between; align-items: baseline; '
    r'margin-bottom: \d+px;"><span style="font-family: Fraunces, serif; font-size: 20px; '
    r'color: #16233f;">)([^<]*)(</span> <span style="font-size: 13px; color: )'
    r'(#[0-9a-f]{6})(; font-weight: 600;">)([^<]*)(</span>)')


def caveat_of(footnote):
    """Keep the page-specific analytical note, drop the boilerplate source."""
    text = re.sub(r'^//\s*', '', footnote.strip())
    # Everything after the first em-dash is usually the editorial caveat.
    parts = re.split(r'&mdash;', text, maxsplit=1)
    if len(parts) < 2:
        return ""
    tail = parts[1].strip()
    # Drop the recurring "connect to your live Sierra feed" instruction.
    tail = re.sub(r'[;.]?\s*connect to your live Sierra feed[^;.]*[.;]?\s*$', '', tail,
                  flags=re.I).strip()
    tail = re.sub(r'^(with|note:)\s*', lambda m: m.group(1).capitalize() + " ",
                  tail, flags=re.I)
    if tail and not tail.endswith('.'):
        tail += '.'
    return tail[0].upper() + tail[1:] if tail else ""


def _bar(q, peak, scale):
    """Height, quarter label and display value for one bar. Zero-based scale."""
    price = float(q["price"])
    year, qn = q["q"].split("-")
    value = f"${price / 1_000_000:.2f}M" if price >= 1_000_000 else f"${price / 1000:.0f}K"
    return round(price / peak * scale), f"{qn} &rsquo;{year[2:]}", value


def bars_html(quarters):
    shades = ["#e4d5b7", "#d2b888", "#e4d5b7", "#a8823d"]
    peak = max(float(q["price"]) for q in quarters)
    out = []
    for i, q in enumerate(quarters):
        height, label, value = _bar(q, peak, 190)
        out.append(
            '\n          <div style="flex: 1 1 0%; display: flex; flex-direction: column; align-items: center; gap: 8px;">'
            f'\n            <span style="font-size: 12px; color: #16233f; font-weight: 600;">{value}</span>'
            f'\n            <div style="width: 100%; height: {height}px; background: {shades[i]}; border-radius: 3px 3px 0px 0px;">&nbsp;</div>'
            f'\n            <span style="font-size: 11px; color: #7d8598;">{label}</span>'
            '\n          </div>')
    return "".join(out) + "\n        "


def barwrap_html(quarters):
    """Same data in the .bar-col structure. The value rides on data-value,
    which the page's own CSS reveals on hover."""
    peak = max(float(q["price"]) for q in quarters)
    out = []
    for q in quarters:
        height, label, value = _bar(q, peak, 156)
        out.append(
            '\n          <div class="bar-col">'
            f'\n            <div class="bar" style="height: {height}px;" data-value="{value}">&nbsp;</div>'
            f'\n            <span style="font-size: 11px; color: #7d8598;">{label}</span>'
            '\n          </div>')
    return "".join(out) + "\n        "


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    records = load()
    wanted = args.slugs or sorted(records)
    report, unmapped = [], {}

    for slug in wanted:
        page = CITY / f"{slug}.html"
        rec = records.get(slug)
        if not page.exists() or not rec:
            report.append((slug, ["NO PAGE OR DATA"]))
            continue

        html = page.read_text()
        notes = []
        quarters = [dict(zip(("q", "price", "sold"), part.split("~")))
                    for part in rec["quarters"].split(";")] if rec["quarters"] else []

        def snap(m):
            pre, _old, mid, label, end = m.groups()
            if label not in SNAPSHOT:
                unmapped.setdefault(label, []).append(slug)
                return m.group(0)
            field, canon = SNAPSHOT[label]
            if not rec.get(field):
                notes.append(f"{label}: no data")
                return m.group(0)
            new_label = canon or label
            notes.append(f"{label} -> {new_label} = {fmt(field, rec[field])}")
            return f"{pre}{fmt(field, rec[field])}{mid}{new_label}{end}"

        def side(m):
            pre, label, mid, _old, end = m.groups()
            if label not in SIDECARD:
                unmapped.setdefault(label, []).append(slug)
                return m.group(0)
            field, canon = SIDECARD[label]
            if not rec.get(field):
                notes.append(f"[card] {label}: no data")
                return m.group(0)
            new_label = canon or label
            notes.append(f"[card] {label} -> {new_label} = {fmt(field, rec[field], True)}")
            return f"{pre}{new_label}{mid}{fmt(field, rec[field], True)}{end}"

        html = SNAP_RE.sub(snap, html)
        html = SIDE_RE.sub(side, html)

        # Snapshot footnote: new attribution, original caveat preserved.
        def foot(m):
            caveat = caveat_of(m.group(2))
            src = (f"Source: Compass Market Insights, single-family homes in "
                   f"{rec['slug'].replace('-', ' ').title()}, {period_label(rec['period'])} "
                   f"&mdash; {rec['sales']} closed sales. Updated {UPDATED}.")
            if caveat:
                src += f" {caveat}"
                notes.append("footnote: caveat preserved")
            return f"{m.group(1)}{src}{m.group(3)}"

        html, nfoot = FOOTNOTE_RE.subn(foot, html, count=1)
        if not nfoot:
            notes.append("footnote: NOT MATCHED")

        # Quarterly bar chart.
        if slug in SKIP_CHART:
            notes.append("chart: SKIPPED (not a quarterly series)")
        elif quarters:
            html, nbars = BARS_RE.subn(
                lambda m: m.group(1) + bars_html(quarters) + m.group(3), html, count=1)
            if not nbars:
                html, nbars = BARWRAP_RE.subn(
                    lambda m: m.group(1) + barwrap_html(quarters) + m.group(3), html, count=1)
            notes.append("chart: rebuilt" if nbars else "chart: NOT MATCHED")

            # Compare quarter-to-same-quarter, matching the series the chart
            # draws. Month-on-month-a-year-ago is far noisier at city scale:
            # Aptos reads +17.1% monthly but -10.6% quarterly, on 22 sales
            # versus 65. Fall back to monthly only if the quarterly pair is
            # missing.
            headline = rec["qYoYPct"] or rec["yoyPct"]
            if headline:
                pct = float(headline)
                colour = "#3f8a5f" if pct >= 0 else "#b0433f"
                arrow = "&#9650;" if pct >= 0 else "&#9660;"

                def yoy(m):
                    if m.group(6).strip() not in ("", None):
                        notes.append(f'chart caption: "{m.group(6)}" -> '
                                     f'"{arrow} {abs(pct):.1f}% YoY"')
                    return (f"{m.group(1)}Median Sold Price{m.group(3)}{colour}"
                            f"{m.group(5)}{arrow} {abs(pct):.1f}% YoY{m.group(7)}")

                html, nyoy = YOY_RE.subn(yoy, html, count=1)
                if not nyoy:
                    notes.append("YoY: NOT MATCHED")

            def cfoot(m):
                caveat = caveat_of(m.group(2))
                txt = ("Quarterly median sold price, single-family homes. Bars are drawn to "
                       "scale from zero.")
                if rec["qYoYPct"]:
                    txt += (f" Year-over-year compares Q2 2026 ({rec['qCurSales']} closed "
                            f"sales) with Q2 2025 ({rec['qPrevSales']}).")
                elif rec["yoyPeriod"]:
                    txt += (f" Year-over-year compares {period_label(rec['period'])} with "
                            f"{period_label(rec['yoyPeriod'])}.")
                if caveat:
                    txt += f" {caveat}"
                return f"{m.group(1)}{txt}{m.group(3)}"

            html = CHART_FOOT_RE.sub(cfoot, html, count=1)

        html = (html.replace("▲", "&#9650;").replace("▼", "&#9660;")
                    .replace("★", "&#9733;"))

        if not args.dry_run:
            page.write_text(html)
        report.append((slug, notes))

    print(f"source: {DATA.name}{'   [DRY RUN]' if args.dry_run else ''}\n")
    for slug, notes in report:
        flags = [n for n in notes if "NOT MATCHED" in n or "no data" in n or "SKIPPED" in n]
        print(f"{slug}  {'  <-- ' + '; '.join(flags) if flags else ''}")
        for n in notes:
            print("    " + n)
    if unmapped:
        print("\nLEFT UNTOUCHED (no Compass equivalent):")
        for label, slugs in sorted(unmapped.items()):
            print(f"  {label}  [{', '.join(sorted(set(slugs)))}]")


if __name__ == "__main__":
    main()
