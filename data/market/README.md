# Market data

`market-data-YYYY-MM-DD.csv` — one row per page (27 cities, 24 San Mateo neighborhoods).

## Source

Compass Market Insights, pulled 2026-08-20 from `compass.com/market-insights` while signed
in as Bryant Huang. Underlying endpoint: `POST /api/v3/trend_chart/get_xy_chart_data`.

Compass's own report footer names the data sources as `lake_tahoe_metrolist_reso`,
`sf_mlslistings`, `sf_ebrd`, `sf_rebareis`.

## Refreshing

Request body shape:

```json
{
  "chartQuery": {
    "state": "CA",
    "propertyTypes": ["Single Family"],
    "counties": ["San Mateo County"],
    "cities": ["San Mateo"]
  },
  "timeRange": "2", "chartType": 1, "chartName": 11,
  "geoId": "sf", "timeGranularity": 3
}
```

Swap `cities` for `neighborhoods` to go one level down. Granularity pairs:

| Granularity | `timeRange` | `timeGranularity` |
|---|---|---|
| Monthly (15 mo) | `"2"` | `3` |
| Quarterly (3 yr) | `"10"` | `4` |
| Yearly (15 yr) | `"7"` | `5` |

`chartName` codes, confirmed against the UI:

| Code | Metric |
|---|---|
| 1 | Average sold price |
| 2 | Average $/sqft |
| 3 | Average days on market |
| 4 | Homes sold |
| 10 | New listings |
| 11 / 21 | **Median sold price** |
| 12 | **Median days on market** |
| 13 | **Median sold price ÷ original list price %** |
| 14 | **Months of inventory** |
| 16 | **Median $/sqft** |
| 22 | Under contract |

Active listings is not its own code — it equals `round(chartName14 × chartName4)`.
Verified: San Mateo 2026-07 → `0.4827586 × 58 = 28`, matching the UI's "Homes for sale 28".

## Column notes

- `basis` / `period` — the window each figure describes. Cities use the latest month;
  neighborhoods use the latest quarter, because monthly medians on 3–6 sales are noise.
- `sales` — closed sales in that window. **This is the number that qualifies the figure.**
  Nothing is published below 3.
- `types` — `SF` = single family only. `ALL` = single family + condo + townhouse, used only
  where a neighborhood has essentially no detached stock (see below).
- `yoyPct` — year-over-year, populated only when the comparison window also had ≥3 sales.
  Blank means there was no honest comparison to draw.
- `moi` / `newListings` — cities only; too sparse to mean anything at neighborhood scale.

## Known data-quality issues

**Neighborhood-level DOM and sold/list % are unreliable.** Compass returns `0` for both in
many neighborhood-months — Aragon shows `0` median DOM for 2026-07 despite 3 closed sales, and
its sold/list series flatlines at `0` across 2026-01 through 2026-03. That is missing data,
not same-day sales. Both fields are solid at city scale (San Mateo runs 7–17 days). **Do not
publish DOM or sold/list on neighborhood pages.**

**Two neighborhoods have no single-family market:**

- `harbor-town` — 0 detached sales in three years. Harbortown is townhomes and condos.
  Uses all property types, full-year 2025 (10 sales).
- `san-mateo-woods-bayridge` — 1–2 detached sales a year. The Bayridge Way townhomes are the
  market here. Uses all property types, 2026-Q2 (6 sales).

Both are labeled `ALL` and their pages must say so. Mixing property types elsewhere would
badly distort: Bowie Estate reads $1.67M detached but $740k all-types, because it is heavily
condo.

**Three rows fall back to an older window** for lack of recent volume. Each is labeled with
its actual period and must be rendered with that period visible, never as "current":

| Slug | Period | Why |
|---|---|---|
| `beresford-manor` | 2025-Q4 | 2026 quarters had 1 and 2 sales |
| `hayward-park` | 2026-Q1 | 2026-Q2 had 1 sale |
| `lakeshore` | 2025 (year) | never reaches 3 in a quarter |

**Small-sample volatility is real.** `bowie-estate` +34.9% and `eastern-addition` +35.2% YoY
are 5-sale quarters, not market moves. Sale counts are published alongside every figure so a
reader can weigh them. Quarter-over-quarter was rejected outright for neighborhoods — it swung
+37% / −32% on the same data.
