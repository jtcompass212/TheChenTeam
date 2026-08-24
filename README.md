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
| `neighborhood-pages/` | 46 neighborhood pages across 3 cities |
| `maps/` | Leaflet neighborhood maps for 9 cities |
| `sierra-export/` | 73 paste-ready files with absolute image URLs |
| `city-images/` | Hero photos, plus `sourced/` for freely-licensed images |
| `data/market/` | Compass market data behind the pages, and how to refresh it |
| `docs/` | Photo shot list and design specs |
| `scripts/` | Build and refresh tooling |

Two further neighborhood maps sit at the repo root in a different format,
generated from a wider dataset rather than hand-drawn:

- `san-francisco-neighborhoods.{geojson,html}` — 95 neighborhoods
- `south-san-francisco-neighborhoods.{geojson,html}` — 16 neighborhoods

## City pages (27)

aptos · atherton · belmont · brisbane · burlingame · cupertino · foster-city ·
fremont · gilroy · hillsborough · mill-valley · millbrae · mountain-view ·
newark · oakland · pacifica · palo-alto · redwood-city · san-bruno ·
san-carlos · san-francisco · san-jose · san-mateo · san-rafael ·
south-san-francisco · sunnyvale · woodside

Each carries a market snapshot, a quarterly price chart, neighborhood cards
and a schools/history block. Market figures come from Compass Market Insights
— see `data/market/README.md`.

## Neighborhood pages (46)

| City | Pages | Mapped neighborhoods |
|---|---|---|
| San Mateo | 24 | 28 |
| Burlingame | 13 | 13 |
| Belmont | 9 | 9 |

San Mateo's four gaps are its three hidden entries plus **Los Prados**, the
only visible neighborhood without a page.

Six mapped cities have no neighborhood pages yet — Foster City (10),
Hillsborough (15), Millbrae (13), Redwood City (13), San Bruno (17) and
San Carlos (6): 74 neighborhoods mapped but not written.

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
```

`data/market/README.md` documents the Compass API contract, the metric codes,
and the rules governing which figures publish — including the sale-count
thresholds that decide when a year-over-year change is withheld.

## Photos

24 of 159 image slots are filled from freely-licensed sources, each credited
on its page. The rest need original photography; `docs/photo-shot-list.md`
briefs every remaining slot.
