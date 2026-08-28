#!/usr/bin/env python3
"""Build the San Francisco MLS district pages from data/sf-districts-content.json.

    python3 scripts/build_district_pages.py

Writes district-pages/san-francisco/district-<n>.html for all ten districts,
in the same visual language as neighborhood-pages/ — same palette, type scale,
card treatments and reveal animations, with a per-district CSS namespace so
several pages can coexist in one Sierra site.

Market figures are embedded here rather than in data/market/*.csv because the
district geo is a different Compass query shape (neighborhoods:["District N"]
against San Francisco County). See data/market/README.md for the trap that
makes that query dangerous if the geo string is ever changed.

Sale-count discipline matches the rest of the site:
  * nothing publishes below 3 closed sales in the window
  * year-over-year is suppressed unless the comparison quarter also cleared 8

Two districts fail that second test (D6 on 7 sales, D8 on 5) and render without
a YoY line. D8's raw YoY would have read +179.7%.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / "data" / "sf-districts-content.json"
DEST = ROOT / "district-pages" / "san-francisco"

# Placeholder for Sierra's IDX search URL. Replace with the real pattern once
# known, e.g. "/san-francisco/homes-for-sale/?neighborhood=".
IDX = "[IDX]"

QUARTERS = ["2025-Q2", "2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2"]
CUR, BASE = -1, 0
MIN_SALES = 3      # nothing publishes below this
MIN_YOY_BASE = 8   # YoY needs this many in the comparison quarter

# Compass Market Insights, pulled 2026-08-28. Quarterly, Single Family,
# counties=["San Francisco County"], neighborhoods=["District N"], geoId "sf".
MARKET = {
    1:  dict(med=[2495000, 2025000, 2325000, 2610000, 3015000], n=[64, 37, 52, 35, 81],
             sqft=[1082, 1106, 1134, 1145, 1325], dom=[12, 11, 13, 12, 11], splp=[113, 113, 116, 116, 126]),
    2:  dict(med=[1650000, 1660000, 1695000, 1851000, 2000000], n=[135, 95, 104, 99, 139],
             sqft=[1045, 1053, 1063, 1134, 1188], dom=[13, 13, 13, 11, 12], splp=[121, 119, 124, 127, 136]),
    3:  dict(med=[1375000, 1400000, 1300000, 1550000, 1580000], n=[44, 32, 42, 28, 45],
             sqft=[875, 884, 905, 990, 912], dom=[14, 13, 14, 13, 13], splp=[111, 116, 112, 115, 120]),
    4:  dict(med=[2050000, 1875000, 2200000, 2400000, 2474227], n=[100, 79, 91, 56, 110],
             sqft=[1054, 1027, 1052, 1128, 1220], dom=[13, 14, 13, 12, 11], splp=[113, 113, 113, 120, 123]),
    5:  dict(med=[2587000, 2435000, 2533000, 3300000, 3200000], n=[107, 65, 95, 54, 126],
             sqft=[1295, 1226, 1388, 1655, 1655], dom=[14, 13, 13, 12, 12], splp=[109, 110, 114, 122, 126]),
    6:  dict(med=[3200000, 2150000, 3800000, 5650000, 3900000], n=[7, 9, 9, 2, 19],
             sqft=[1211, 1018, 1130, 1638, 1295], dom=[13, 91, 22, 10, 17], splp=[107, 100, 103, 115, 119]),
    7:  dict(med=[5437000, 4900000, 6500000, 7559125, 7885000], n=[35, 26, 35, 31, 35],
             sqft=[1589, 1576, 1656, 1642, 2000], dom=[19, 32, 30, 12, 12], splp=[99, 102, 101, 105, 113]),
    8:  dict(med=[1895000, 3700000, 2900000, 5101250, 5300000], n=[5, 9, 11, 3, 18],
             sqft=[1325, 1053, 1235, 1372, 2000], dom=[9, 20, 34, 19, 11], splp=[100, 94, 109, 100, 104]),
    9:  dict(med=[1705000, 1625000, 1600000, 1653325, 2060000], n=[75, 58, 77, 50, 77],
             sqft=[1066, 1138, 1083, 1145, 1343], dom=[14, 13, 14, 12, 13], splp=[112, 117, 114, 118, 129]),
    10: dict(med=[1080000, 1075000, 1050000, 1125000, 1250000], n=[108, 130, 125, 73, 145],
             sqft=[786, 724, 773, 808, 868], dom=[15, 17, 18, 13, 13], splp=[110, 109, 108, 115, 119]),
}

# Districts whose single-family sample describes only a sliver of a market that
# is overwhelmingly condominium/co-op. Their source note says so explicitly.
CONDO_HEAVY = {6, 8}

GOLD, NAVY, BODY, MUTED = "#a8823d", "#16233f", "#4b5468", "#7d8598"
RULE, PANEL, GREEN = "rgb(221, 225, 233)", "#f0f2f6", "#3f8a5f"


def money(v):
    """$3.20M / $985K, matching how the sibling pages render medians."""
    return f"${v / 1_000_000:.2f}M" if v >= 1_000_000 else f"${round(v / 1000):,}K"


def qlabel(q):
    """2026-Q2 -> Q2 2026."""
    y, quarter = q.split("-")
    return f"{quarter} {y}"


def eyebrow(text):
    return (f'<p style="font-family: \'Inter\', sans-serif; font-size: 13px; letter-spacing: 0.22em; '
            f'text-transform: uppercase; color: {GOLD}; font-weight: 600; margin: 0px 0px 16px;">{text}</p>')


def h2(text, mb=24):
    return (f'<h2 style="font-family: Fraunces, serif; font-weight: 500; font-size: 30px; line-height: 1.18; '
            f'color: {NAVY}; margin: 0px 0px {mb}px; letter-spacing: -0.01em;">{text}</h2>')


def stat(value, label, sub, sub_color=MUTED, bold_sub=False, last=False):
    border = "" if last else f" border-right: 1px solid rgb(237, 239, 243);"
    weight = " font-weight: 600;" if bold_sub else ""
    return (f'        <div style="padding: 32px 26px; text-align: center;{border}">\n'
            f'          <div style="font-family: Fraunces, serif; font-size: 44px; color: {NAVY}; line-height: 1;">{value}</div>\n'
            f'          <div style="font-size: 13px; color: {MUTED}; margin-top: 10px; letter-spacing: 0.04em;">{label}</div>\n'
            f'          <div style="font-size: 13px; color: {sub_color};{weight} margin-top: 6px;">{sub}</div>\n'
            f'        </div>')


def snapshot(d, m):
    """The market block, plus the source note that qualifies every figure."""
    cur_q, base_q = QUARTERS[CUR], QUARTERS[BASE]
    med, n = m["med"][CUR], m["n"][CUR]
    base_med, base_n = m["med"][BASE], m["n"][BASE]

    if n < MIN_SALES:
        raise SystemExit(f"D{d['num']}: {n} sales in {cur_q} is below the {MIN_SALES}-sale floor")

    if base_n >= MIN_YOY_BASE:
        pct = (med - base_med) / base_med * 100
        arrow = "&#9650;" if pct >= 0 else "&#9660;"
        sub, color, bold = f"{arrow} {abs(pct):.1f}% vs {qlabel(base_q)}", GREEN if pct >= 0 else "#b4453c", True
        yoy_note = (f" The year-over-year change compares {qlabel(cur_q)} against {qlabel(base_q)} "
                    f"({base_n} closed sales); both windows clear the sale-count threshold used across this site.")
    else:
        sub, color, bold = qlabel(cur_q), MUTED, False
        yoy_note = (f" A year-over-year change is not shown: {qlabel(base_q)} recorded only {base_n} closed "
                    f"single-family sales, too few to compare against honestly.")

    condo_note = (f" District {d['num']} is overwhelmingly a condominium and co-operative market, and these "
                  f"single-family figures describe only a small part of what trades here."
                  if d["num"] in CONDO_HEAVY else
                  f" District {d['num']} also contains a condominium market that these single-family figures "
                  f"do not describe.")

    cells = "\n".join([
        stat(money(med), "Median Sold Price", sub, color, bold),
        stat(f"${m['sqft'][CUR]:,}", "Median Price / Sq. Ft.", f"{n} closed sales"),
        stat(str(m["dom"][CUR]), "Median Days to Offer", qlabel(cur_q)),
        stat(f"{m['splp'][CUR]}%", "Sold / List Price", qlabel(cur_q), last=True),
    ])

    return f'''  <!-- 2. MARKET SNAPSHOT -->
  <section class="scroll-reveal" style="max-width: 1180px; margin: 70px auto 0px; padding: 0px 32px;">
    <div style="border: 1px solid {RULE}; border-top: 3px solid rgb(168, 130, 61); border-radius: 6px; overflow: hidden; background: #ffffff;">
      <div style="background: {PANEL}; padding: 15px 26px; border-bottom: 1px solid {RULE}; display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap;"><span style="font-family: Fraunces, serif; font-size: 20px; color: {NAVY}; font-weight: 500;">District {d['num']} &middot; {d['name']}</span> <span style="font-size: 13px; color: {MUTED};">Market Snapshot &middot; Single-Family Homes, {qlabel(cur_q)}</span></div>
      <div style="display: grid; grid-template-columns: repeat(4, 1fr);">
{cells}
      </div>
    </div>
    <p style="font-size: 12px; color: #9ba3b5; margin: 10px 4px 0px;">Source: Compass Market Insights &mdash; single-family homes in San Francisco MLS District {d['num']}, {qlabel(cur_q)} ({n} closed sales). District figures are reported quarterly.{yoy_note}{condo_note} Compass is a real estate broker licensed by the State of California and makes no representation as to the accuracy or completeness of this information. Equal Housing Opportunity.</p>
  </section>'''


def build(d, m):
    num, name, ns = d["num"], d["name"], f"sf-d{d['num']}"
    kf = f"sfd{num}"

    cards = "\n".join(
        f'''      <div class="stat-card" style="background: #ffffff; border: 1px solid {RULE}; border-radius: 8px; padding: 22px 22px;">
        <div style="width: 44px; height: 44px; border-radius: 50%; background-color: #f4ead9; display: flex; align-items: center; justify-content: center; margin-bottom: 14px;"><img style="width: 22px; height: 22px; display: block;" src="https://cdn.jsdelivr.net/npm/@tabler/icons@latest/icons/{icon}.svg" alt=""></div>
        <div style="font-size: 13px; letter-spacing: 0.06em; text-transform: uppercase; color: {GOLD}; font-weight: 600; margin-bottom: 8px;">{kicker}</div>
        <div style="font-size: 15px; color: {NAVY}; font-weight: 600; margin-bottom: 4px;">{title}</div>
        <p style="font-size: 13.5px; color: {MUTED}; margin: 0px;">{blurb}</p>
      </div>''' for icon, kicker, title, blurb in d["cards"])

    roster = "".join(
        f'''<a class="nb-card-link" style="display: block; border: 1px solid {RULE}; border-radius: 8px; padding: 24px 22px; text-decoration: none;" href="{IDX}{slug}">
        <h3 style="font-family: Fraunces, serif; font-weight: 500; font-size: 19px; color: {NAVY}; margin: 0px 0px 6px;">{label}</h3>
        <p style="font-size: 13.5px; color: {MUTED}; margin: 0px;">{blurb}</p>
      </a>''' for label, slug, blurb in d["roster"])

    schools = "\n".join(
        f'''        <div class="stat-card" style="background: #ffffff; border: 1px solid {RULE}; border-radius: 8px; padding: 22px 24px;">
          <div style="font-size: 15px; color: {NAVY}; font-weight: 600;">{sname}</div>
          <div style="font-size: 13px; color: {MUTED}; margin-top: 4px;">{detail}</div>
        </div>''' for sname, detail in d["schools"])

    return f'''<!-- Paste everything below into TinyMCE's Source Code view (the "<>" icon in the toolbar), not the WYSIWYG pane. --><!-- NOTE: The interactive district MAP is a separate Shared HTML Widget — add it as a NEW page component
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
    <h1 class="fade-in d2" style="font-family: Fraunces, serif; font-weight: 500; font-size: 56px; line-height: 1.06; letter-spacing: -0.01em; color: {NAVY}; margin: 0px 0px 28px; max-width: 16ch; text-wrap: balance;">District {num} Homes &amp; Real Estate</h1>
    <div style="display: grid; grid-template-columns: 1.15fr 1fr; gap: 56px; align-items: start; margin-bottom: 24px;">
      <div class="fade-in d3" style="font-size: 17px; line-height: 1.75; color: {BODY};">
        <p style="margin: 0px 0px 18px;">{d['intro']} Below you&rsquo;ll find current homes for sale across District {num}, updated throughout the day.</p>
        <p style="margin: 0px;">If you'd like more information on any of these listings, just reach out &mdash; we're happy to share disclosures, recent sales, and pricing history. Looking beyond District {num}? Browse <a href="/san-francisco/">San Francisco real estate</a> or the <a href="#neighborhoods-in-district">neighborhoods within this district</a>.</p>
      </div>
      <div style="align-self: stretch; min-height: 280px; border-radius: 4px; overflow: hidden; background: {PANEL}; display: flex; align-items: center; justify-content: center;"><span style="font-size: 13px; color: #9ba3b5; text-align: center; letter-spacing: 0.04em;">[ HERO IMAGE ]<br>A representative District {num} street or view<br>~900&times;650</span></div>
    </div>
  </section>
{snapshot(d, m)}
  <!-- 3. WHAT DEFINES THIS DISTRICT -->
  <section class="scroll-reveal" style="max-width: 1180px; margin: 80px auto 0px; padding: 0px 32px;">
    {eyebrow('What Defines It')}
    {h2(f'The character of District {num}')}
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px;">
{cards}
    </div>
  </section>
  <!-- 4. NEIGHBORHOODS IN THIS DISTRICT -->
  <section id="neighborhoods-in-district" class="scroll-reveal" style="max-width: 1180px; margin: 80px auto 0px; padding: 0px 32px;">
    {eyebrow('Explore Within')}
    {h2(f'Neighborhoods in District {num}')}
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">{roster}</div>
  </section>
  <!-- 5. SCHOOLS -->
  <section class="scroll-reveal" style="background: {PANEL}; margin-top: 90px; padding: 70px 0px;">
    <div style="max-width: 1180px; margin: 0px auto; padding: 0px 32px;">
      {eyebrow('Schools')}
      {h2(f'Schools serving District {num}', mb=12)}
      <p style="font-size: 15px; line-height: 1.7; color: {BODY}; margin: 0px 0px 24px; max-width: 78ch;">San Francisco Unified assigns elementary seats through a citywide choice-and-lottery process rather than by home address, so no San Francisco home guarantees enrolment at any particular school. The schools below are those located in and around District {num}.</p>
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
{schools}
      </div>
    </div>
  </section>
  <!-- 6. BOUNDARIES (heading only — map widget is the NEXT page component, right after this Content Area) -->
  <section class="scroll-reveal" style="max-width: 1180px; margin: 90px auto 40px; padding: 0px 32px;">
    {eyebrow('Boundaries')}
    {h2(f'Where District {num} sits', mb=0)}
  </section>
</div>
'''


def main():
    data = json.loads(CONTENT.read_text())
    DEST.mkdir(parents=True, exist_ok=True)
    for d in data["districts"]:
        m = MARKET[d["num"]]
        (DEST / f"district-{d['num']}.html").write_text(build(d, m))
        base_n = m["n"][BASE]
        flag = "" if base_n >= MIN_YOY_BASE else f"  (YoY suppressed — {base_n}-sale base)"
        print(f"  district-{d['num']}.html  {money(m['med'][CUR])}  {m['n'][CUR]} sales{flag}")
    print(f"\n{len(data['districts'])} pages -> {DEST.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
