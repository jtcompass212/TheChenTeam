# Filling Placeholder Content — City & Neighborhood Pages

**Date:** 2026-08-20
**Branch:** `fill-page-content`

## Premise correction

The prose on these pages is *not* placeholder. All 27 city pages and all 24 San Mateo
neighborhood pages already carry specific, researched copy — real history, street names,
school names, architectural periods. Three things are genuinely unfilled:

| Gap | Count | Marker in source |
|---|---|---|
| City page images | 135 (27 × 5) | `[ IMAGE ]` |
| Neighborhood hero images | 24 | `[ HERO IMAGE ]` |
| Market stat blocks | 51 pages | `// Placeholder figures — swap with live Sierra market data` |
| Chen Team production stats | 27 | `// Replace with your verified production figures` |

City hero photos are already done — every city page points at a real file in `city-images/`.

## Scope

In scope: market stat blocks, and photos for the image slots.

**Out of scope — deliberately:** the Chen Team production stats (`$48M+ sold`,
`100% of list`, `12 days to offer`, `5.0★`). These are verified business figures, not
market data. Filling them would mean inventing them. They keep their existing
`// Replace with your verified production figures` marker.

## 1. Market data

### Source

Compass Market Insights (`compass.com/market-insights/`), authenticated as Bryant Huang.
Verified available and covering the needed geography:

- **Counties:** San Mateo, Santa Clara, Alameda, Marin, Santa Cruz, San Francisco — all present.
- **Neighborhood taxonomy:** 363 entries for San Mateo County alone. Spot-checked against the
  repo's names: Aragon, Baywood, Baywood Knolls, Baywood Park, Beresford Manor, Bowie Estate,
  Burlingables, Burlingame Park, Cipriani, Carolands all present. Coverage is strong but not
  guaranteed 1:1 — Compass has its own spellings (e.g. `Downtown Millbrea`, a Compass-side typo).
  Unmatched names get resolved by hand during collection.
- **Date ranges:** weekly, monthly, quarterly, out to 4 years.

### Fields

The Table view (not Graph) returns scrapeable rows:

```
Date | Median sold price | Median sold price per sqft | Median days on market | Active | Sold | Under contract
```

The `Days on Market - Sold/List Price%` tab adds sale-to-list ratio.
Months of inventory is derived: `Active ÷ avg monthly closed sales`.

### Safety constraints

Collection is read-only. **Do not click** `Save analysis`, `Create report`, or the delete
(trash) icon. Work inside a scratch analysis via `Create new analysis` rather than inside a
saved one, so a stray save cannot overwrite the existing `District 4` or `Westwood Highlands`
analyses. Changing filters and clicking `Apply` does not persist — the `Reset to last saved`
affordance confirms this.

### Thin-data rule

Neighborhood medians go sparse fast. Aragon — a well-established neighborhood — recorded zero
sales in Jan '26 and Feb '26. Smaller tracts will have 2–3 sales a year.

Rule, applied per page:

- If the **most recent month has ≥3 closed sales**, report that month. Label: `Month YYYY`.
- Otherwise widen to a **trailing 12-month figure**, labeled with its window and sale count,
  e.g. `12-mo. through Jul 2026 · 9 sales`.
- If trailing 12 months yields **fewer than 3 sales**, the stat block is suppressed entirely
  rather than shown with a meaningless median. The page keeps its prose; it loses the stat card.

**Open implementation detail, to resolve in the pilot:** Compass returns *monthly medians*, not
underlying sales. A true 12-month median is therefore not directly available. First check
whether a date-range option aggregates to a single bucket. If not, compute a sales-weighted
average of monthly medians and label it precisely as that — never as "median" — so the page
does not claim a statistic it isn't.

### Labeling corrections

Two existing labels are wrong relative to what Compass returns, and get fixed rather than
populated with mismatched data:

- City pages: `Median List Price` → `Median Sold Price` (Compass returns sold, not list).
- City pages: `Avg. $ / Sq. Ft.` → `Median $ / Sq. Ft.` (Compass returns median).

### Attribution

Each `// Placeholder figures` comment is replaced with a real source-and-date line, and each
page carries the Compass broker disclaimer once. Compass's own report footer requires it —
the platform stamps it on every generated report, so republished figures should carry it too.

### Two-stage, not one

1. **Collect** to `data/market/<slug>.json` — one file per city and per neighborhood.
2. **Wire** the JSON into the HTML.

The split gives a review gate on every number before it goes live, and makes next month's
refresh a re-scrape rather than a re-edit of 51 hand-tuned HTML files.

## 2. Photos

Source freely-licensed imagery (Wikimedia Commons, Flickr CC) per slot. Download hits to
`city-images/` and a new `neighborhood-images/`, wire in with attribution.

For the misses, write `docs/photo-shot-list.md` keyed to each unfilled slot. The neighborhood
pages already carry art direction inside their placeholder captions — e.g. *"Eichler-style home
in San Mateo Highlands, or the pool at Highlands Recreation Center"* — which carries over
verbatim as the brief.

**Expected coverage: 30–50% of 159 slots.** City-level and landmark shots will mostly land.
Named residential tracts — Baywood Knolls, Bowie Estate, Westwood Knolls — almost certainly
have no freely-licensed photography. A shot list is the correct deliverable for those; wiring
in a photo of the wrong place is worse than an empty slot on a licensed agent's site.

Any image whose license requires attribution gets it. No AI-generated imagery — these pages
depict real places a buyer may visit.

## 3. Execution order

**Pilot** — San Mateo city page + 3 neighborhood pages (Aragon, San Mateo Park, Sunnybrae),
collected and wired end to end. Confirms the JSON shape, the thin-data rule, the rendered
result, and the numbers. Reviewed before proceeding.

**Remainder** — the other 47 pages, run against the confirmed format.

## Verification

- Every figure in a wired page traces to a value in its `data/market/*.json`.
- No page shows a stat built on fewer than 3 sales.
- No `[ IMAGE ]` / `[ HERO IMAGE ]` slot points at a photo of a different place.
- Every wired image file exists on disk and its `src` path resolves from the page's location.
- Chen Team stat blocks are untouched.
