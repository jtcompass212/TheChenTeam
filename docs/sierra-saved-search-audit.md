# Sierra saved searches — can our neighborhoods be targeted?

**Audited 2026-08-24.** Every one of our 124 mapped neighborhoods was queried
against Sierra Interactive's own location lookup (the typeahead behind the
saved-search builder), site `6466`, MLS region `146` — the San Mateo County
feed. Raw results: `data/sierra-location-audit.json`.

## The finding

Sierra targets listings by MLS **City**, **District** (called `areas` in the
API), **Subdivision**, or **Zip**. Our neighborhoods are hand-drawn polygons.
Most of them do not exist in the MLS under any name.

| | Count | Share |
|---|---:|---:|
| Exact name match | **14** | 11% |
| Approximate match only | **22** | 18% |
| No match at all | **88** | 71% |
| **Total** | **124** | |

**Only 14 of 124 neighborhoods can be targeted by name with confidence.**

## By city

| City | Neighborhoods | Exact | Approximate | None |
|---|---:|---:|---:|---:|
| Belmont | 9 | 0 | 0 | 9 |
| Burlingame | 13 | 0 | 3 | 10 |
| Foster City | 10 | 0 | 1 | 9 |
| Hillsborough | 15 | 1 | 2 | 12 |
| Millbrae | 13 | 2 | 1 | 10 |
| Redwood City | 13 | 1 | 2 | 10 |
| San Bruno | 17 | 7 | 3 | 7 |
| San Carlos | 6 | 0 | 3 | 3 |
| San Mateo | 28 | 3 | 7 | 18 |
| **Total** | **124** | **14** | **22** | **88** |

Belmont and Foster City are the extreme cases: **not one** of their 19
neighborhoods is addressable by name. San Bruno is the best covered, and even
there 7 of 17 are missing.

## The 14 that work

| Neighborhood | MLS match | Type |
|---|---|---|
| Hillsborough — Lakeview | `Lakeview` | District |
| Millbrae — Highlands | `Highlands` | District |
| Millbrae — Millwood | `Millwood` | District |
| Redwood City — Redwood Shores | `Redwood Shores` | **City** |
| San Bruno — Capuchino | `Capuchino` | District |
| San Bruno — Huntington Park | `Huntington Park` | District |
| San Bruno — Lomita Park | `Lomita Park` | District |
| San Bruno — Mills Park | `Mills Park` | District |
| San Bruno — Monte Verde | `Monte Verde` | District |
| San Bruno — Pacific Heights | `Pacific Heights` | Subdivision |
| San Bruno — Rollingwood | `Rollingwood` | District |
| San Mateo — Aragon | `Aragon` | District |
| San Mateo — Lauriedale | `Lauriedale` | District |
| San Mateo — Parkside | `Parkside` | Subdivision |

Two carry caveats even so:

- **Redwood Shores** matches as a *city*, not a neighborhood. Sierra treats it
  as its own city, so a saved search there behaves differently from the rest.
- **Highlands** is the ambiguity the README already flags. The MLS has a bare
  `Highlands` district with no city attached, which is exactly why we cannot
  confirm it belongs to Millbrae rather than San Mateo Highlands.

## Why the other 22 "matches" are not usable as-is

They fall into four failure modes, and none of them is a clean equivalent of
our polygon:

**Wrong neighborhood.** `Foster City — Bay Vista` fuzzy-matches to
`Bay Ridge/Linda Vista`, a different place. Using it would publish listings
from the wrong area. **Do not use.**

**Broader than us.** The MLS bundles neighborhoods under an `Etc` suffix:
`Carolands Etc`, `Dumbarton Etc`, `San Bruno Park Etc`, `Alder Manor Etc`,
`Beverly Terrace Etc`, `Baywood Park Etc`, `Beresford Manor Etc`,
`Bowie Estate Etc`. A search on these returns homes outside the neighborhood
the page describes.

**Narrower than us.** `Bayside Manor 2, 18` and `Crestmoor Park 3` are numbered
subsets; `Shelter Creek Condos` is condo-only. These miss homes the page counts.

**Truncated names.** The feed appears to cut district names at 20 characters:
`Burlingame Hills/Sky`, `Clearfield Park/N Re`, `North Shoreview/Dore`,
`San Mateo Park/El Ce`, `San Mateo Woods/Bayr`, `Pacific Heights/Sea`,
`Burlingame Gardens E`, `Burlingame Terrace-E`, `Farm Hills Estates E`. The
slash forms are compound districts covering more than one of our neighborhoods.

### Two collisions worth deciding on

- `San Mateo — Baywood` and `San Mateo — Baywood Park` **both** resolve to
  `Baywood Park Etc`. Two of our pages would publish identical results. (And
  `Baywood Knolls`, a third Baywood-family neighborhood, matches nothing.)
- `Burlingame — Burlingame Hills` and `Hillsborough — Burlingame Hills` both
  resolve to `Burlingame Hills/Sky` — the same straddle problem the README
  already documents for Mills Estates.

## The 88 with no match

<details>
<summary>Full list</summary>

- **Belmont (9):** Belmont Country Club · Belmont Heights · Cipriani · Downtown Belmont · Homeview · McDougal · Plateau-Skymont · Sterling Downs · Western Hills
- **Burlingame (10):** Burlingables · Burlingame Grove · Burlingame Park · Burlingame Village · Downtown Burlingame · Easton Addition · Ingoldmilldale · Lyon Hoag · Mills Estates · Ray Park
- **Foster City (9):** Carmel Village · Dolphin Bay · Harbor Side · Isle Cove · Marina Point · Sea Colony · The Islands · Treasure Isle · Vintage Park
- **Hillsborough (12):** Brewer Subdivision · Country Club Manor · Hillsborough Heights · Hillsborough Hills · Hillsborough Knolls · Hillsborough Oaks · Hillsborough Park · Homeplace · Parrot Drive Area · Ryan Tract · Skyfarm · Tobin Clark Estate
- **Millbrae (10):** Capuchino Village · Downtown Millbrae · Glenview Highlands · Green Hills · Green Hills Country Club · Lomita Hills · Meadow Glen · Millbrae Meadows · Mills Estates · Telescope Hills
- **Redwood City (10):** Bair Island · Centennial · Central Park · Clifford Heights · Cordilleras Heights · Downtown Redwood City · Eagle Hill · Edgewood Park · Horgan Ranch · Mt. Carmel
- **San Bruno (7):** Bayhill · Belle Air North · Belle Air Park · Downtown San Bruno · Golden Gate National Cemetery · Portola Highlands · Tanforan
- **San Carlos (3):** Cordes · El Sereno Corte · Howard Park
- **San Mateo (18):** Baywood Knolls · Eastern Addition · Fiesta Gardens · Foothill Terrace · Harbor Town · Hayward Park · Hillsdale "The Lanes" · Homestead · Lakeshore · Laurelwood & sugarloaf · Los Prados · San Mateo Highlands · San Mateo Knolls · San Mateo Terrace/Beresford · San Mateo Village · Shoreview · Sunnybrae · Westwood Knolls

</details>

Two of these are not residential areas and should never get a search:
**Golden Gate National Cemetery** and **Tanforan**, both San Bruno — the same
pair the README already sets aside.

## What this leaves

**Name-based saved searches cannot cover our neighborhood pages.** At best they
cover 14 of 124 honestly, and 12 more only if we accept publishing the wrong
homes.

The alternative Sierra supports is a **drawn-polygon search** — its map builder
has Draw and Save Map, and a saved polygon is exact. We already hold precise
boundaries for all 124 in `maps/*/*-map.html`, so the data side is solved.

The obstacle is entry, not data: Sierra's draw tool is click-per-vertex, and our
polygons run 20–50 vertices each — several thousand clicks across 124
neighborhoods. Doing this at scale means injecting the coordinates into Sierra's
map programmatically rather than clicking them.

### Recommended order

1. **The 14 exact matches** — safe to create by name today, with Redwood Shores
   and Highlands flagged as above.
2. **The 88 + 22** — polygon searches, pending a working injection path.
3. **Never** — Golden Gate National Cemetery, Tanforan, and `Bay Vista` via
   `Bay Ridge/Linda Vista`.

## Reproducing this

The lookup sits behind Cloudflare and rejects direct requests, so it has to be
called from an authenticated browser session on the Sierra admin:

```
POST https://mls-api.sierrainteractivedev.com/api/listings/lookup/locations
X-API-Key: <read from the admin page's own XHR — do not hardcode>
{"query":"<name>","siteId":"6466","mlsRegionIds":[146],
 "types":["cities","subdivisions","areas","counties","zips","states"],"limit":15}
```
