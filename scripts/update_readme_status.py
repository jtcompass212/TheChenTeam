#!/usr/bin/env python3
"""Regenerate the "Work remaining" section of README.md from the repo.

    python3 scripts/update_readme_status.py
    python3 scripts/update_readme_status.py --check   # fail if stale, for CI

Every count is read from the working tree, never hand-maintained. The README
was once eight cities and fourteen neighborhoods out of date because those
numbers were typed by hand; this exists so that cannot happen again.

Rewrites only the block between the STATUS markers. The rest of the README is
prose and is left alone.
"""
import argparse
import csv
import glob
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
BEGIN, END = "<!-- STATUS:BEGIN -->", "<!-- STATUS:END -->"

# Judgment calls that need a human, not a count. Kept here so regenerating the
# section never drops them.
DECISIONS = [
    ("Team production stats", "27 city pages",
     "`$48M+` / `100% of list` / `12 days` / `5.0★` are sample figures and have never been "
     "touched. They need your verified numbers."),
    ("Shoreview's +38.6%", "1 page",
     "Clears the 8-sale threshold honestly on 13 sales, but it is the largest swing published "
     "anywhere on the site."),
    ("\"Highlands\" identity", "1 page",
     "Compass lists it separately from San Mateo Highlands so the match to Millbrae Highlands "
     "is probable, but the API cannot confirm which city a neighborhood belongs to."),
    ("Mills Estates, twice", "2 pages",
     "One Compass neighborhood straddling the Millbrae–Burlingame line, so both pages publish "
     "identical figures. Correct, but deliberate."),
    ("Image hosting", "51 images",
     "Served via jsDelivr off this public repo. Rebuild with `--image-base` against Sierra's "
     "media library to drop the GitHub dependency."),
    ("Hillsborough boundary feature", "1 geojson",
     "A 95-vertex polygon named `Hillsborough` sits in the neighborhood layer, larger than any "
     "real neighborhood — almost certainly a city outline that got mixed in."),
]

NOT_RESIDENTIAL = [
    ("Golden Gate National Cemetery", "san-bruno"),
    ("Tanforan", "san-bruno"),
]


def collect():
    d = {}
    written = {}
    for p in ROOT.glob("neighborhood-pages/*/*.html"):
        written[p.parent.name] = written.get(p.parent.name, 0) + 1

    mapped, scaffolds = {}, {}
    for gj in sorted(ROOT.glob("maps/*/map/*.geojson")):
        city = gj.parts[-3]
        feats = json.loads(gj.read_text())["features"]
        mapped[city] = sum(
            1 for f in feats
            if not (city == "hillsborough" and f["properties"].get("name") == "Hillsborough"))
    for p in ROOT.glob("maps/*/*.html"):
        if not p.stem.endswith("-map"):
            scaffolds[p.parent.name] = scaffolds.get(p.parent.name, 0) + 1

    photos = {}
    for p in list(ROOT.glob("neighborhood-pages/*/*.html")) + list(ROOT.glob("city-pages/*.html")):
        key = "City pages" if p.parent.name == "city-pages" else p.parent.name
        t = p.read_text()
        photos[key] = photos.get(key, 0) + len(re.findall(r"\[ (?:HERO )?IMAGE \]", t))

    d.update(
        written=written, mapped=mapped, scaffolds=scaffolds, photos=photos,
        city_pages=len(list(ROOT.glob("city-pages/*.html"))),
        nbhd_pages=sum(written.values()),
        exported=len(list(ROOT.glob("sierra-export/**/*.html"))),
        # Filled slots live in two places: city-images/sourced/ for the
        # freely-licensed city photos, neighborhood-images/ for hero shots.
        # city-images/*.jpg at the top level are the original city heroes and
        # were never placeholder slots, so they are not counted.
        sourced_images=(len(list(ROOT.glob("city-images/sourced/*")))
                        + len([p for p in ROOT.glob("neighborhood-images/**/*")
                               if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")])),
        chen_stats=sum(1 for p in ROOT.glob("city-pages/*.html")
                       if "Replace with your verified production figures" in p.read_text()),
    )
    d["no_figures"] = [
        ((r.get("city") or "san-mateo"), r["slug"], r.get("noData") or "unattributed")
        for f in sorted(glob.glob(str(ROOT / "data/market/market-data-*.csv")))
        for r in csv.DictReader(open(f))
        if r.get("kind", "nbhd") == "nbhd" and r["basis"] == "none"
    ]
    # shot list currency
    m = re.search(r"\*\*(\d+) of (\d+) image slots\*\*",
                  (ROOT / "docs/photo-shot-list.md").read_text())
    d["shotlist_claim"] = int(m.group(1)) if m else None

    # Neighborhood pages carry exactly one hero slot each (no thumb/feature),
    # so every remaining "[ HERO IMAGE ]" match names a page still needed.
    hero_missing = []
    for p in ROOT.glob("neighborhood-pages/*/*.html"):
        t = p.read_text()
        if "[ HERO IMAGE ]" not in t:
            continue
        m = re.search(r"<h1[^>]*>(.*?)</h1>", t, re.S)
        name = html.unescape(m.group(1)) if m else p.stem.replace("-", " ").title()
        name = re.sub(r"\s+Homes\s+&?\s*Real Estate\s*$", "", name).strip()
        hero_missing.append((p.parent.name, p.stem, name))
    d["hero_missing"] = sorted(hero_missing, key=lambda r: (r[0], r[2]))
    return d


def title(city):
    return city.replace("-", " ").title()


def render(d):
    total_mapped = sum(d["mapped"].values())
    total_scaffold = sum(d["scaffolds"].values())
    total_photos = sum(d["photos"].values())
    L = [BEGIN, "", "## Work remaining", "",
         f"Market data is complete: all **{d['city_pages'] + d['nbhd_pages']} published pages** "
         f"carry verified Compass figures. What is left falls into three piles.", "",
         f"| | Count | |", "|---|---:|---|",
         f"| Neighborhoods with no page | **{total_scaffold}** | blank scaffolds in `maps/`, prose included |",
         f"| Empty photo slots | **{total_photos}** | of {total_photos + d['sourced_images']} "
         f"total; {d['sourced_images']} filled so far |",
         f"| Team stat blocks | **{d['chen_stats']}** | still showing sample figures |", ""]

    # coverage
    L += ["### Neighborhood page coverage", "",
          f"{total_mapped} neighborhoods are mapped; {d['nbhd_pages']} have a written page.", "",
          "| City | Written | Mapped | Remaining |", "|---|---:|---:|---:|"]
    for city in sorted(d["mapped"], key=lambda c: (-d["scaffolds"].get(c, 0), c)):
        w, m_ = d["written"].get(city, 0), d["mapped"][city]
        rem = d["scaffolds"].get(city, 0)
        L.append(f"| {title(city)} | {w} | {m_} | {'—' if not rem else rem} |")
    L.append(f"| **Total** | **{d['nbhd_pages']}** | **{total_mapped}** | **{total_scaffold}** |")
    L += ["",
          "Scaffolds are templates, not publishable pages — every slot still reads "
          "`[ PLACEHOLDER ]`. **Publish from `neighborhood-pages/` or `sierra-export/`, never "
          "from `maps/`.**", ""]

    if NOT_RESIDENTIAL:
        names = " and ".join(f"**{n}** ({title(c)})" for n, c in NOT_RESIDENTIAL)
        L += [f"Two of the remaining entries are not residential neighborhoods — {names}. "
              f"Green Hills Country Club was the same case and is handled by saying so on the "
              f"page rather than inventing a median; these deserve the same decision before "
              f"anyone writes them.", ""]

    # photos
    L += ["### Photography", "",
          "Every written page renders a placeholder where a photo belongs. Named residential "
          "tracts have no archive coverage, so these need original photography — "
          "`docs/photo-shot-list.md` briefs them.", "",
          "| Area | Empty slots |", "|---|---:|"]
    for k in sorted(d["photos"], key=lambda k: -d["photos"][k]):
        if d["photos"][k]:
            L.append(f"| {title(k)} | {d['photos'][k]} |")
    L.append(f"| **Total** | **{total_photos}** |")
    L.append("")
    if d["shotlist_claim"] and d["shotlist_claim"] != total_photos:
        L += [f"> **The shot list is out of date.** It briefs {d['shotlist_claim']} slots against "
              f"an actual {total_photos} — it predates the newer city directories. Regenerate "
              f"with `python3 scripts/write_shot_list.py`.", ""]

    # hero placeholders, by neighborhood page
    if d["hero_missing"]:
        by_city = {}
        for city, slug, name in d["hero_missing"]:
            by_city.setdefault(city, []).append((slug, name))
        L += [f"### Neighborhood hero images still needed ({len(d['hero_missing'])})", "",
              "One hero slot per neighborhood page; these still render "
              "`[ HERO IMAGE ]` instead of a photo.", ""]
        for city in sorted(by_city, key=lambda c: (-len(by_city[c]), c)):
            names = ", ".join(
                f"[{name}](neighborhood-pages/{city}/{slug}.html)"
                for slug, name in by_city[city])
            L.append(f"- **{title(city)}** ({len(by_city[city])}): {names}")
        L.append("")

    # decisions
    L += ["### Calls that need you", "",
          "None of these block anything. Each is a judgment about the business or the market.", "",
          "| Item | Scope | What's needed |", "|---|---|---|"]
    for name, scope, why in DECISIONS:
        L.append(f"| **{name}** | {scope} | {why} |")
    L.append("")

    if d["no_figures"]:
        L += ["### Pages that publish no market figures — on purpose", "",
              "Each states its reason on the page rather than borrowing a citywide median.", "",
              "| Page | Reason |", "|---|---|"]
        reason = {"thin": "Too few sales a year to support a median",
                  "not-residential": "Not a residential area",
                  "unattributed": "No sales attributed to it in the MLS",
                  # Distinct from "unattributed": Compass has no reporting area
                  # under this name at all, which is not evidence about whether
                  # sales happened on these streets. See data/market/README.md.
                  "unresolved": "No separate Compass reporting area for it"}
        for city, slug, r in d["no_figures"]:
            L.append(f"| `{city}/{slug}` | {reason.get(r, r)} |")
        L.append("")

    L.append(END)
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    text = README.read_text()
    block = render(collect())

    if BEGIN in text and END in text:
        new = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), lambda _m: block, text, flags=re.S)
    else:  # first run — insert after the Contents section
        anchor = "\n## City pages"
        new = text.replace(anchor, "\n" + block + "\n" + anchor, 1)

    if args.check:
        print("README status block is STALE — run scripts/update_readme_status.py"
              if new != text else "README status block is current")
        return 1 if new != text else 0
    README.write_text(new)
    print("README status block regenerated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
