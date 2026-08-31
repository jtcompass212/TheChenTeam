#!/usr/bin/env python3
"""Build the 95 San Francisco neighborhood pages.

    python3 scripts/build_sf_neighborhood_pages.py

Content comes from data/sf-neighborhoods/*.json, market figures from
data/market/market-data-san-francisco-2026-08-31.csv, and the district name and
school list from data/sf-districts-content.json. Output goes to
neighborhood-pages/san-francisco/.

Unlike the Peninsula cities, these are generated rather than filled from a
scaffold — there was no scaffold to fill, and 95 pages by hand is how counts
drift. Re-running is safe and idempotent.

Three things differ from the Peninsula template, each for a reason:

  * No commute-times block. It is meaningless at this scale in a city where
    every neighborhood is twenty minutes from downtown by different means.
  * Schools are district-level and carry a lottery disclaimer. SFUSD assigns
    seats through a citywide choice process, not by address, so the Peninsula
    phrasing ("assigned to X Elementary") would be false on every SF page.
  * Sixteen neighborhoods have no single-family market and publish all-property-
    types figures instead, labeled on the page. See data/market/README.md.

Sale-count discipline matches the rest of the site: nothing publishes below 3
closed sales in the window. 17 of the 95 publish no median at all.
"""
import csv
import glob
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / "data" / "sf-neighborhoods"
MARKET = ROOT / "data" / "market" / "market-data-san-francisco-2026-08-31.csv"
DISTRICTS = ROOT / "data" / "sf-districts-content.json"
DEST = ROOT / "neighborhood-pages" / "san-francisco"

PERIOD = "Q2 2026"
PULLED = "31 August 2026"
MIN_SALES = 3

GOLD, NAVY, BODY, MUTED = "#a8823d", "#16233f", "#4b5468", "#7d8598"
RULE, PANEL, FAINT = "rgb(221, 225, 233)", "#f0f2f6", "#9ba3b5"

TYPE_LABEL = {"SF": "Single-Family Homes", "ALL": "All Property Types"}

REASON = {
    "thin": ("Too few sales for a median",
             "records only a handful of closed sales a year &mdash; too few in any recent "
             "quarter to support a median that would mean anything"),
    "not-residential": ("Not a residential area",
                        "is parkland or civic ground rather than a residential neighborhood, "
                        "and no meaningful volume of homes trades here"),
    "unattributed": ("No separately reported sales",
                     "has no sales attributed to it in the MLS data behind Compass Market "
                     "Insights for this window"),
}


def money(v):
    # Must match money() in scripts/verify_repo.py exactly — that function is
    # what checks these figures against the dataset. Sub-$1M renders in full
    # dollars, not K notation.
    v = float(v)
    return f"${v / 1_000_000:.2f}M" if v >= 1_000_000 else f"${v:,.0f}"


def load():
    nb = []
    for f in sorted(glob.glob(str(CONTENT / "*.json"))):
        nb += json.loads(pathlib.Path(f).read_text())["neighborhoods"]
    mk = {r["slug"]: r for r in csv.DictReader(open(MARKET))}
    dj = json.loads(DISTRICTS.read_text())["districts"]
    dist = {d["num"]: d for d in dj}
    return nb, mk, dist


def eyebrow(text):
    return (f'<p style="font-family: \'Inter\', sans-serif; font-size: 13px; letter-spacing: 0.22em; '
            f'text-transform: uppercase; color: {GOLD}; font-weight: 600; margin: 0px 0px 16px;">{text}</p>')


def h2(text, mb=24):
    return (f'<h2 style="font-family: Fraunces, serif; font-weight: 500; font-size: 30px; line-height: 1.18; '
            f'color: {NAVY}; margin: 0px 0px {mb}px; letter-spacing: -0.01em;">{text}</h2>')


def snapshot(n, r):
    """Market block. Three shapes: full (median + $/sqft), partial (median +
    sale count, where $/sqft was never pulled), and none (a stated reason)."""
    name, types = n["name"], r["types"]
    head = (f'<div style="background: {PANEL}; padding: 15px 26px; border-bottom: 1px solid {RULE}; '
            f'display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap;">'
            f'<span style="font-family: Fraunces, serif; font-size: 20px; color: {NAVY}; font-weight: 500;">{name}</span> '
            f'<span style="font-size: 13px; color: {MUTED};">Market Snapshot &middot; {TYPE_LABEL[types]}, {PERIOD}</span></div>')

    if r["basis"] == "none":
        title, why = REASON[r["noData"]]
        body = (f'      <div style="padding: 32px 26px; text-align: center;">\n'
                f'        <div style="font-family: Fraunces, serif; font-size: 20px; color: {NAVY}; line-height: 1.4;">{title}</div>\n'
                f'        <div style="font-size: 13.5px; color: {MUTED}; margin-top: 10px; max-width: 60ch; margin-left: auto; margin-right: auto;">{name} {why}.</div>\n'
                f'      </div>')
        note = (f"Source: Compass Market Insights &mdash; {TYPE_LABEL[types].lower()} in {name}, {PERIOD}. "
                f"No median is published here: {why}. For a valuation in this area, get in touch and "
                f"we&rsquo;ll pull the specific comparables.")
        return head, body, note

    sales, med = int(r["sales"]), r["medPrice"]
    if sales < MIN_SALES:
        raise SystemExit(f"{n['slug']}: {sales} sales is below the {MIN_SALES}-sale floor")

    left = (f'        <div style="padding: 32px 26px; text-align: center; border-right: 1px solid rgb(237, 239, 243);">\n'
            f'          <div style="font-family: Fraunces, serif; font-size: 44px; color: {NAVY}; line-height: 1;">{money(med)}</div>\n'
            f'          <div style="font-size: 13px; color: {MUTED}; margin-top: 10px; letter-spacing: 0.04em;">Median Sold Price</div>\n'
            f'          <div style="font-size: 13px; color: {MUTED}; margin-top: 6px;">{PERIOD}</div>\n'
            f'        </div>')
    if r["medSqft"]:
        right_v, right_l, right_s = f"${int(r['medSqft']):,}", "Median Price / Sq. Ft.", f"{sales} closed sales"
    else:
        right_v, right_l, right_s = str(sales), "Closed Sales", PERIOD
    right = (f'        <div style="padding: 32px 26px; text-align: center;">\n'
             f'          <div style="font-family: Fraunces, serif; font-size: 44px; color: {NAVY}; line-height: 1;">{right_v}</div>\n'
             f'          <div style="font-size: 13px; color: {MUTED}; margin-top: 10px; letter-spacing: 0.04em;">{right_l}</div>\n'
             f'          <div style="font-size: 13px; color: {MUTED}; margin-top: 6px;">{right_s}</div>\n'
             f'        </div>')
    body = f'      <div style="display: grid; grid-template-columns: repeat(2, 1fr);">\n{left}\n{right}\n      </div>'

    note = (f"Source: Compass Market Insights &mdash; {TYPE_LABEL[types].lower()} in {name}, {PERIOD} "
            f"({sales} closed sales). Neighborhood figures are reported quarterly because monthly "
            f"sale counts here are too small to be meaningful. A year-over-year change is not shown "
            f"for this window.")
    if types == "ALL":
        note += (f" {name} has no meaningful single-family market, so this figure covers single-family "
                 f"homes, condominiums and townhouses together.")
    if r["noDataDetail"]:
        note += f" {r['noDataDetail'][0].upper()}{r['noDataDetail'][1:]}."
    return head, body, note


def build(n, r, d, by_slug):
    slug, name, num = n["slug"], n["name"], n["d"]
    # @keyframes names are global, not scoped by the wrapper class, so several
    # of these pages pasted into one Sierra site would fight over them. Initials
    # collided (bayview-heights and bernal-heights both gave "sfbh"), so use the
    # whole slug — unique by construction.
    ns, kf = f"sf-{slug}", "sf" + slug.replace("-", "")
    head, body, note = snapshot(n, r)

    cards = "\n".join(
        f'''      <div class="stat-card" style="background: #ffffff; border: 1px solid {RULE}; border-radius: 8px; padding: 22px 22px;">
        <div style="width: 44px; height: 44px; border-radius: 50%; background-color: #f4ead9; display: flex; align-items: center; justify-content: center; margin-bottom: 14px;"><img style="width: 22px; height: 22px; display: block;" src="https://cdn.jsdelivr.net/npm/@tabler/icons@latest/icons/{icon}.svg" alt=""></div>
        <div style="font-size: 13px; letter-spacing: 0.06em; text-transform: uppercase; color: {GOLD}; font-weight: 600; margin-bottom: 8px;">{kicker}</div>
        <div style="font-size: 15px; color: {NAVY}; font-weight: 600; margin-bottom: 4px;">{title}</div>
        <p style="font-size: 13.5px; color: {MUTED}; margin: 0px;">{blurb}</p>
      </div>''' for icon, kicker, title, blurb in n["near"])

    similar = "".join(
        f'''<a class="nb-card-link" style="display: block; border: 1px solid {RULE}; border-radius: 8px; padding: 24px 22px; text-decoration: none;" href="/san-francisco/{s}/">
        <h3 style="font-family: Fraunces, serif; font-weight: 500; font-size: 19px; color: {NAVY}; margin: 0px 0px 6px;">{by_slug[s]['name']}</h3>
        <p style="font-size: 13.5px; color: {MUTED}; margin: 0px;">{by_slug[s]['intro'].split(". ")[0]}.</p>
      </a>''' for s in n["similar"])

    schools = "\n".join(
        f'''        <div class="stat-card" style="background: #ffffff; border: 1px solid {RULE}; border-radius: 8px; padding: 22px 24px;">
          <div style="font-size: 15px; color: {NAVY}; font-weight: 600;">{sn}</div>
          <div style="font-size: 13px; color: {MUTED}; margin-top: 4px;">{detail}</div>
        </div>''' for sn, detail in d["schools"])

    return f'''<!-- Paste everything below into TinyMCE's Source Code view (the "<>" icon in the toolbar), not the WYSIWYG pane. --><!-- NOTE: The interactive neighborhood MAP is a separate Shared HTML Widget — add it as a NEW page component
     positioned AFTER this entire Content Area block. -->
<style>
  .{ns}-page, .{ns}-page * {{ box-sizing: border-box; }}
  .{ns}-page a {{ color: {GOLD}; text-decoration: none; }}
  .{ns}-page a:hover {{ color: #8c6930; text-decoration: underline; }}
  .{ns}-page ::selection {{ background: #eee6d8; }}

  .{ns}-page .stat-card {{ transition: transform 200ms ease, box-shadow 200ms ease, border-color 200ms ease; }}
  .{ns}-page .stat-card:hover {{ transform: translateY(-4px); box-shadow: 0 10px 20px -8px rgba(22,35,63,0.14); border-color: {GOLD}; }}

  .{ns}-page .nb-card-link {{ transition: transform 220ms ease, box-shadow 220ms ease; }}
  .{ns}-page .nb-card-link:hover {{ transform: translateY(-5px); box-shadow: 0 12px 22px -10px rgba(22,35,63,0.16); }}

  .{ns}-page .fade-in {{ opacity: 0; transform: translateY(16px); animation: {kf}FadeIn 700ms ease forwards; }}
  .{ns}-page .fade-in.d1 {{ animation-delay: 80ms; }}
  .{ns}-page .fade-in.d2 {{ animation-delay: 160ms; }}
  .{ns}-page .fade-in.d3 {{ animation-delay: 240ms; }}
  @keyframes {kf}FadeIn {{ to {{ opacity: 1; transform: translateY(0); }} }}

  .{ns}-page .scroll-reveal {{ opacity: 1; }}
  @supports (animation-timeline: view()) {{
    .{ns}-page .scroll-reveal {{ opacity: 0; animation: {kf}ScrollReveal linear both; animation-timeline: view(); animation-range: entry 0% cover 30%; }}
    @keyframes {kf}ScrollReveal {{ from {{ opacity: 0; transform: translateY(28px); }} to {{ opacity: 1; transform: translateY(0); }} }}
  }}
</style>
<div class="{ns}-page" style="font-family: 'Inter', system-ui, sans-serif; color: {BODY}; background: #ffffff; -webkit-font-smoothing: antialiased; line-height: 1.6;">
  <!-- 1. EYEBROW + H1 + INTRO -->
  <section style="max-width: 1180px; margin: 0px auto; padding: 40px 32px 0px;">
    <p class="fade-in d1" style="font-family: 'Inter', sans-serif; font-size: 13px; letter-spacing: 0.22em; text-transform: uppercase; color: {GOLD}; font-weight: 600; margin: 0px 0px 18px;">San Francisco &middot; District {num} &middot; {name}</p>
    <h1 class="fade-in d2" style="font-family: Fraunces, serif; font-weight: 500; font-size: 56px; line-height: 1.06; letter-spacing: -0.01em; color: {NAVY}; margin: 0px 0px 28px; max-width: 16ch; text-wrap: balance;">{name} Homes &amp; Real Estate</h1>
    <div style="display: grid; grid-template-columns: 1.15fr 1fr; gap: 56px; align-items: start; margin-bottom: 24px;">
      <div class="fade-in d3" style="font-size: 17px; line-height: 1.75; color: {BODY};">
        <p style="margin: 0px 0px 18px;">{n['intro']} Below you&rsquo;ll find current homes for sale in {name}, updated throughout the day.</p>
        <p style="margin: 0px;">If you'd like more information on any of these listings, just reach out &mdash; we're happy to share disclosures, recent sales, and pricing history. Looking beyond {name}? Browse <a href="/san-francisco/">San Francisco real estate</a> or <a href="#similar-neighborhoods">nearby neighborhoods</a>.</p>
      </div>
      <div style="align-self: stretch; min-height: 280px; border-radius: 4px; overflow: hidden; background: {PANEL}; display: flex; align-items: center; justify-content: center;"><span style="font-size: 13px; color: {FAINT}; text-align: center; letter-spacing: 0.04em;">[ HERO IMAGE ]<br>A representative {name} street or view<br>~900&times;650</span></div>
    </div>
  </section>
  <!-- 2. MARKET SNAPSHOT -->
  <section class="scroll-reveal" style="max-width: 1180px; margin: 70px auto 0px; padding: 0px 32px;">
    <div style="border: 1px solid {RULE}; border-top: 3px solid rgb(168, 130, 61); border-radius: 6px; overflow: hidden; background: #ffffff;">
      {head}
{body}
    </div>
    <p style="font-size: 12px; color: {FAINT}; margin: 10px 4px 0px;">{note} Updated {PULLED}. Compass is a real estate broker licensed by the State of California and makes no representation as to the accuracy or completeness of this information. Equal Housing Opportunity.</p>
  </section>
  <!-- 3. NEARBY -->
  <section class="scroll-reveal" style="max-width: 1180px; margin: 80px auto 0px; padding: 0px 32px;">
    {eyebrow('Nearby')}
    {h2(f"What&rsquo;s around {name}")}
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
{cards}
    </div>
  </section>
  <!-- 4. SIMILAR NEIGHBORHOODS -->
  <section id="similar-neighborhoods" class="scroll-reveal" style="max-width: 1180px; margin: 80px auto 0px; padding: 0px 32px;">
    {eyebrow('Explore Nearby')}
    {h2('Similar Neighborhoods')}
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">{similar}</div>
  </section>
  <!-- 5. SCHOOLS -->
  <section class="scroll-reveal" style="background: {PANEL}; margin-top: 90px; padding: 70px 0px;">
    <div style="max-width: 1180px; margin: 0px auto; padding: 0px 32px;">
      {eyebrow('Schools')}
      {h2(f'Schools serving {name}', mb=12)}
      <p style="font-size: 15px; line-height: 1.7; color: {BODY}; margin: 0px 0px 24px; max-width: 78ch;">San Francisco Unified assigns elementary seats through a citywide choice-and-lottery process rather than by home address, so no San Francisco home guarantees enrollment at any particular school. The schools below are those located in and around District {num}.</p>
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
{schools}
      </div>
    </div>
  </section>
  <!-- 6. STREETS & BOUNDARIES (heading only — map widget is the NEXT page component, right after this Content Area) -->
  <section class="scroll-reveal" style="max-width: 1180px; margin: 90px auto 40px; padding: 0px 32px;">
    {eyebrow('Streets &amp; Boundaries')}
    {h2(f'Where {name} sits', mb=0)}
  </section>
</div>
'''


def main():
    nb, mk, dist = load()
    by_slug = {n["slug"]: n for n in nb}
    DEST.mkdir(parents=True, exist_ok=True)
    pub = nomed = 0
    for n in sorted(nb, key=lambda x: (x["d"], x["slug"])):
        r = mk[n["slug"]]
        (DEST / f"{n['slug']}.html").write_text(build(n, r, dist[n["d"]], by_slug))
        if r["basis"] == "none":
            nomed += 1
        else:
            pub += 1
    print(f"  {len(nb)} pages -> {DEST.relative_to(ROOT)}/")
    print(f"  {pub} publish a median, {nomed} state a reason instead")


if __name__ == "__main__":
    main()
