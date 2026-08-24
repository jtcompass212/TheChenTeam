# Choosing the window and property type for a neighborhood figure

Written down because getting this wrong is not obvious from the output — a
plausible-looking median can describe the wrong housing or the wrong year, and
nothing about the page tells you.

## The order

For each neighborhood, take the first of these that yields at least **3 closed
sales**:

1. Single-family, most recent complete quarter
2. **All property types**, most recent complete quarter
3. Single-family, most recent full year
4. All property types, most recent full year
5. Single-family, any of the last four quarters, newest first
6. All property types, same
7. Either, the year before last

If none qualify, publish no figure and say why on the page.

## Why recency outranks property type

The first version of this tried every single-family window before considering
all property types. That gave **Isle Cove** a 2024 figure while it had 13
closed sales in the most recent quarter — Isle Cove is a condominium
neighborhood, so filtering to detached houses found almost nothing and the
chain fell back two years rather than sideways one step.

A stale number is worse than a broader one. The window is stated on the page
either way; a reader can see "2024" and discount it, but only if we don't bury
it behind a filter that made the recent data invisible.

## Why property type is not a free choice either

Widening to all property types is not harmless. It changes what the number
means, and in a mixed neighborhood it produces a median that describes
neither half:

| Foster City neighborhood | Detached share of 2025 sales | Correct cut |
|---|---:|---|
| Sea Colony | 100% | single-family |
| Dolphin Bay | 85% | single-family |
| Carmel Village | 81% | single-family |
| Bay Vista | 74% | single-family |
| Harbor Side | 60% | single-family |
| Treasure Isle | 44% | single-family |
| **Marina Point** | **9%** | all types |
| **The Islands** | **7%** | all types |
| **Isle Cove** | **6%** | all types |

Marina Point is the instructive one. It reads as a detached neighborhood —
cul-de-sacs, family housing, and that is how other sites describe it — but
three of its thirty-three 2025 sales were detached. Its single-family median
is $2.46M and its all-types median is $878K. Publishing the first would
describe 9% of the market; publishing the second without saying so would
mislead anyone comparing it to Sea Colony.

So: **use all property types only where detached housing is genuinely
marginal**, and say so on the page when you do. The generated footnote does
this automatically for any row marked `ALL`.

## Sanity checks worth running

- A median far below the rest of its city usually means the property-type cut
  changed, not that the market moved.
- An unrecognised neighborhood name returns region-wide data rather than an
  error. Screen every new name against the sentinel first — see
  `data/market/README.md`.
- A neighborhood with a plausible median but a very old period is the Isle
  Cove symptom: check whether it has attached housing the filter is hiding.
