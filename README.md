# The Chen Team — Peninsula & Bay Area Pages

Static HTML for The Chen Team's Sierra Interactive site: city pages,
neighborhood pages, and interactive Leaflet neighborhood maps.

Everything here is plain HTML with figures hardcoded at build time — no
scripts, no runtime data fetching. Paste-ready output lives in
`sierra-export/`.

## Contents

| Directory | What's in it |
|---|---|
| `city-pages/` | 27 city pages |
| `neighborhood-pages/` | 59 neighborhood pages across 4 cities |
| `maps/` | Leaflet map widgets for 9 cities, plus unwritten page scaffolds |
| `sierra-export/` | 86 paste-ready files with absolute image URLs |
| `city-images/` | Hero photos, plus `sourced/` for freely-licensed images |
| `data/market/` | Compass market data behind the pages, and how to refresh it |
| `docs/` | Photo shot list and design specs |
| `scripts/` | Build and refresh tooling |

Two further neighborhood maps sit at the repo root in a different format,
generated from a wider dataset rather than hand-drawn:

- `san-francisco-neighborhoods.{geojson,html}` — 95 neighborhoods
- `south-san-francisco-neighborhoods.{geojson,html}` — 16 neighborhoods

<!-- STATUS:BEGIN -->

## Work remaining

Market data is complete: all **148 published pages** carry verified Compass figures. What is left falls into three piles.

| | Count | |
|---|---:|---|
| Neighborhoods with no page | **3** | blank scaffolds in `maps/`, prose included |
| Empty photo slots | **2** | of 256 total; 254 filled so far |
| Team stat blocks | **27** | still showing sample figures |

### Neighborhood page coverage

124 neighborhoods are mapped; 121 have a written page.

| City | Written | Mapped | Remaining |
|---|---:|---:|---:|
| San Mateo | 25 | 28 | 3 |
| Belmont | 9 | 9 | — |
| Burlingame | 13 | 13 | — |
| Foster City | 10 | 10 | — |
| Hillsborough | 15 | 15 | — |
| Millbrae | 13 | 13 | — |
| Redwood City | 13 | 13 | — |
| San Bruno | 17 | 17 | — |
| San Carlos | 6 | 6 | — |
| **Total** | **121** | **124** | **3** |

Scaffolds are templates, not publishable pages — every slot still reads `[ PLACEHOLDER ]`. **Publish from `neighborhood-pages/` or `sierra-export/`, never from `maps/`.**

Two of the remaining entries are not residential neighborhoods — **Golden Gate National Cemetery** (San Bruno) and **Tanforan** (San Bruno). Green Hills Country Club was the same case and is handled by saying so on the page rather than inventing a median; these deserve the same decision before anyone writes them.

### Photography

Every written page renders a placeholder where a photo belongs. Named residential tracts have no archive coverage, so these need original photography — `docs/photo-shot-list.md` briefs them.

| Area | Empty slots |
|---|---:|
| City Pages | 2 |
| **Total** | **2** |

> **The shot list is out of date.** It briefs 135 slots against an actual 2 — it predates the newer city directories. Regenerate with `python3 scripts/write_shot_list.py`.

### Calls that need you

None of these block anything. Each is a judgment about the business or the market.

| Item | Scope | What's needed |
|---|---|---|
| **Team production stats** | 27 city pages | `$48M+` / `100% of list` / `12 days` / `5.0★` are sample figures and have never been touched. They need your verified numbers. |
| **Shoreview's +38.6%** | 1 page | Clears the 8-sale threshold honestly on 13 sales, but it is the largest swing published anywhere on the site. |
| **"Highlands" identity** | 1 page | Compass lists it separately from San Mateo Highlands so the match to Millbrae Highlands is probable, but the API cannot confirm which city a neighborhood belongs to. |
| **Mills Estates, twice** | 2 pages | One Compass neighborhood straddling the Millbrae–Burlingame line, so both pages publish identical figures. Correct, but deliberate. |
| **Image hosting** | 51 images | Served via jsDelivr off this public repo. Rebuild with `--image-base` against Sierra's media library to drop the GitHub dependency. |
| **Hillsborough boundary feature** | 1 geojson | A 95-vertex polygon named `Hillsborough` sits in the neighborhood layer, larger than any real neighborhood — almost certainly a city outline that got mixed in. |

### Pages that publish no market figures — on purpose

Each states its reason on the page rather than borrowing a citywide median.

| Page | Reason |
|---|---|
| `burlingame/ingoldmilldale` | No sales attributed to it in the MLS |
| `foster-city/vintage-park` | Not a residential area |
| `hillsborough/parrot-drive-area` | Too few sales a year to support a median |
| `millbrae/green-hills` | Too few sales a year to support a median |
| `millbrae/green-hills-country-club` | Not a residential area |
| `redwood-city/downtown-redwood-city` | No sales attributed to it in the MLS |
| `redwood-city/bair-island` | Not a residential area |
| `san-bruno/belle-air-north` | No sales attributed to it in the MLS |
| `san-bruno/downtown-san-bruno` | No sales attributed to it in the MLS |
| `san-bruno/bayhill` | Not a residential area |
| `san-bruno/tanforan` | Not a residential area |
| `san-bruno/golden-gate-national-cemetery` | Not a residential area |

<!-- STATUS:END -->

## City pages (27)

aptos · atherton · belmont · brisbane · burlingame · cupertino · foster-city ·
fremont · gilroy · hillsborough · mill-valley · millbrae · mountain-view ·
newark · oakland · pacifica · palo-alto · redwood-city · san-bruno ·
san-carlos · san-francisco · san-jose · san-mateo · san-rafael ·
south-san-francisco · sunnyvale · woodside

Each carries a market snapshot, a quarterly price chart, neighborhood cards
and a schools/history block. Market figures come from Compass Market Insights
— see `data/market/README.md`.

## Neighborhood pages (59)

| City | Pages | Mapped neighborhoods |
|---|---|---|
| San Mateo | 24 | 28 |
| Burlingame | 13 | 13 |
| Millbrae | 13 | 13 |
| Belmont | 9 | 9 |

San Mateo's four gaps are its three hidden entries plus **Los Prados**, the
only visible neighborhood without a page.

`maps/<city>/<neighborhood>.html` holds an unwritten scaffold for every
neighborhood that has no page yet. See [Work remaining](#work-remaining) for
the current counts, which cities are outstanding, and which pages deliberately
publish no market figures.

## Maps: neighborhoods by city (124 total)

Alphabetized per city; names match what each map renders. Entries marked
_(hidden)_ carry `"hidden": true` and render dimmed.

> **Note:** `maps/hillsborough/map/hillsborough-map.geojson` also contains a
> feature named `Hillsborough` that is not a neighborhood — a 95-vertex
> MultiPolygon larger than any neighborhood in the file, which looks like a
> city-boundary outline sitting in the neighborhood layer. It is excluded
> from the count below.

### Belmont (9)

- Belmont Country Club
- Belmont Heights
- Cipriani
- Downtown Belmont
- Homeview
- McDougal
- Plateau-Skymont
- Sterling Downs
- Western Hills

### Burlingame (13)

- Burlingables _(hidden)_
- Burlingame Gardens
- Burlingame Grove
- Burlingame Hills
- Burlingame Park
- Burlingame Terrace
- Burlingame Village
- Downtown Burlingame
- Easton Addition
- Ingoldmilldale
- Lyon Hoag
- Mills Estates
- Ray Park

### Foster City (10)

- Bay Vista
- Carmel Village
- Dolphin Bay
- Harbor Side
- Isle Cove
- Marina Point
- Sea Colony
- The Islands
- Treasure Isle
- Vintage Park

### Hillsborough (15)

- Brewer Subdivision
- Burlingame Hills
- Carolands
- Country Club Manor
- Hillsborough Heights
- Hillsborough Hills
- Hillsborough Knolls
- Hillsborough Oaks
- Hillsborough Park
- Homeplace
- Lakeview
- Parrot Drive Area
- Ryan Tract
- Skyfarm
- Tobin Clark Estate

### Millbrae (13)

- Bayside Manor
- Capuchino Village
- Downtown Millbrae
- Glenview Highlands
- Green Hills
- Green Hills Country Club
- Highlands
- Lomita Hills
- Meadow Glen
- Millbrae Meadows
- Mills Estates
- Millwood
- Telescope Hills

### Redwood City (13)

- Bair Island
- Centennial
- Central Park
- Clifford Heights
- Cordilleras Heights
- Downtown Redwood City
- Dumbarton
- Eagle Hill
- Edgewood Park
- Farm Hills Estates
- Horgan Ranch
- Mt. Carmel
- Redwood Shores

### San Bruno (17)

- Bayhill
- Belle Air North
- Belle Air Park
- Capuchino
- Crestmoor
- Downtown San Bruno
- Golden Gate National Cemetery
- Huntington Park
- Lomita Park
- Mills Park
- Monte Verde
- Pacific Heights
- Portola Highlands
- Rollingwood
- San Bruno Park
- Shelter Creek
- Tanforan

### San Carlos (6)

- Alder Manor
- Beverly Terrace
- Clearfield Park
- Cordes
- El Sereno Corte
- Howard Park

### San Mateo (28)

- Aragon
- Baywood
- Baywood Knolls
- Baywood Park
- Beresford Manor
- Bowie Estate
- Eastern Addition
- Fiesta Gardens
- Foothill Terrace
- Harbor Town
- Hayward Park
- Hillsdale "The Lanes" _(hidden)_
- Homestead
- Lakeshore
- Laurelwood & sugarloaf
- Lauriedale _(hidden)_
- Los Prados
- North Shoreview
- Parkside
- San Mateo Highlands
- San Mateo Knolls
- San Mateo Park
- San Mateo Terrace/Beresford _(hidden)_
- San Mateo Village
- San Mateo Woods/Bayridge
- Shoreview
- Sunnybrae
- Westwood Knolls

## Refreshing market data

Figures are pulled from Compass Market Insights and written into the pages by
script, so an update is a re-scrape plus a re-run rather than hand-editing
dozens of files:

```
python3 scripts/apply_market_data.py       # neighborhood pages
python3 scripts/apply_city_market_data.py  # city pages
python3 scripts/build_sierra.py            # regenerate sierra-export/
python3 scripts/update_readme_status.py    # refresh "Work remaining" above
```

Run the last one after anything that changes page counts. Every number in the
[Work remaining](#work-remaining) section is read from the working tree, so it
cannot drift the way hand-typed counts did.

## Keeping the project status honest

Two things guard it, so nobody has to remember.

**A pre-push hook.** Enable it once per clone:

```
git config core.hooksPath .githooks
```

From then on, `git push` regenerates the status block if it is stale and stops
so you can commit it, then runs the page checks. `git push --no-verify` skips
it when you genuinely need to.

**CI.** `.github/workflows/project-status.yml` runs the same checks on every
push to `main` and every pull request. The hook is opt-in per clone, so this is
the backstop that covers everyone — including edits made through the GitHub web
interface.

Both call the same two scripts, which you can also run by hand:

```
python3 scripts/update_readme_status.py --check   # is the backlog current?
python3 scripts/verify_repo.py                    # do the pages hold together?
```

`verify_repo.py` checks what has actually broken here before: figures drifting
from the dataset they cite, placeholder text reaching a publishable page, a
stale scaffold in `maps/` shadowing a written page, markup left unbalanced by a
bad substitution, and export URLs that look absolute but contain a traversal
and 404 on paste.

`data/market/README.md` documents the Compass API contract, the metric codes,
and the rules governing which figures publish — including the sale-count
thresholds that decide when a year-over-year change is withheld.

## Photos

24 of 159 image slots are filled from freely-licensed sources, each credited
on its page. The rest need original photography; `docs/photo-shot-list.md`
briefs every remaining slot.
