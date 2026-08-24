#!/usr/bin/env python3
"""Write docs/photo-shot-list.md — the per-slot brief for slots no freely
licensed photo covers.

Art direction already lives in the page placeholders ("Eichler-style home in
San Mateo Highlands, or the pool at Highlands Recreation Center"); it is
carried through verbatim rather than reinvented.
"""
import json
import pathlib
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAND = json.loads((ROOT / "data" / "photo-candidates.json").read_text())
SHORT = json.loads((ROOT / "data" / "photo-shortlist.json").read_text())
OUT = ROOT / "docs" / "photo-shot-list.md"

covered = {(s["page"], s["subject"]) for s in SHORT}

SPEC = {
    "hero": ("~900x650", "landscape", "Sits beside the intro copy; the tallest "
             "image on the page and the first thing a visitor sees."),
    "feature": ("~800x800", "square", "Paired with the 'About the Community' "
                "copy in a two-column block."),
    "thumb": ("4:3", "landscape", "Neighborhood card thumbnail, roughly 260px "
              "wide as rendered."),
}


def main():
    todo = [s for s in CAND if (s["page"], s["subject"]) not in covered]
    by_page = defaultdict(list)
    for s in todo:
        by_page[s["page"]].append(s)

    lines = [
        "# Photo shot list",
        "",
        f"**{len(todo)} of {len(CAND)} image slots** need original photography. "
        f"The other {len(covered)} are filled from freely-licensed sources "
        "(see `data/photo-shortlist.json`).",
        "",
        "Most of what's missing is named residential tracts — Baywood Knolls, "
        "Bowie Estate, Westwood Knolls. No stock or archive library covers a "
        "specific subdivision, which is exactly why these are a shoot rather "
        "than a search.",
        "",
        "## How to use this",
        "",
        "Each row is one slot on one page. The **Brief** column is the art "
        "direction already written into the page placeholder — it names the "
        "specific street, park or building intended.",
        "",
        "Shooting notes that apply throughout:",
        "",
        "- **Golden hour.** These are all exteriors; midday sun blows out "
        "stucco and flattens the tree canopy that gives most of these "
        "neighborhoods their character.",
        "- **No identifiable people, no readable plates, no house numbers.** "
        "Photographing from the public right-of-way keeps this simple.",
        "- **Landscape unless noted.** The feature slots are square-cropped.",
        "- **Shoot wider than the final crop** so the same frame can serve the "
        "hero and thumbnail aspect ratios.",
        "- One frame can cover several slots when a street reads as typical of "
        "the whole tract.",
        "",
    ]

    for page in sorted(by_page):
        slots = by_page[page]
        kind = "City page" if page.startswith("city/") else "Neighborhood page"
        name = page.split("/", 1)[1].replace("-", " ").title()
        lines += [f"## {name} — {kind}", "",
                  "| Slot | Size | Brief |", "|---|---|---|"]
        for s in slots:
            size, _orient, _note = SPEC[s["kind"]]
            brief = s["subject"] or "—"
            if s.get("blurb"):
                brief += f" — *{s['blurb']}*"
            lines.append(f"| {s['kind']} | {size} | {brief} |")
        lines.append("")

    lines += [
        "## Slot types",
        "",
        "| Type | Size | Where it appears |",
        "|---|---|---|",
    ]
    for kind, (size, _o, note) in SPEC.items():
        lines.append(f"| `{kind}` | {size} | {note} |")
    lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT} — {len(todo)} slots across {len(by_page)} pages")


if __name__ == "__main__":
    main()
