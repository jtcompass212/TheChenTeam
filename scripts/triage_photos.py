#!/usr/bin/env python3
"""Score Commons candidates for relevance and split them into accept / reject.

A keyword match is not evidence a photo shows the right place — "Seascape" and
"Rio del Mar" name places on several continents. A candidate is only accepted
when its filename independently confirms the location, which is the one signal
in the API response that is hard to match by accident.

Writes data/photo-shortlist.json (accepted, for review before download) and
prints the coverage split.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAND = json.loads((ROOT / "data" / "photo-candidates.json").read_text())
OUT = ROOT / "data" / "photo-shortlist.json"

CITY_NAME = {
    "south-san-francisco": "South San Francisco", "mill-valley": "Mill Valley",
    "foster-city": "Foster City", "redwood-city": "Redwood City",
    "san-bruno": "San Bruno", "san-carlos": "San Carlos",
    "san-francisco": "San Francisco", "san-jose": "San Jose",
    "san-mateo": "San Mateo", "san-rafael": "San Rafael",
    "mountain-view": "Mountain View", "palo-alto": "Palo Alto",
}

# Places whose names recur worldwide; a bare name match means nothing.
AMBIGUOUS = {
    "seacliff", "seascape", "rio del mar", "highlands", "the islands", "centennial",
    "lakeview", "homestead", "parkside", "shoreview", "lakeshore", "carmel village",
    "central park", "bayview", "sunnyside", "westwood", "fairview", "hillside",
    "riverside", "brookside", "eastside", "westside", "northside", "southside",
}

# Photos that would misrepresent a residential street even if the name matches.
OFFTOPIC = re.compile(
    r"\b(map|logo|seal|coat of arms|diagram|chart|graph|plaque|sign|signage|"
    r"portrait|headshot|gravestone|tombstone|panorama of the world|flag)\b", re.I)

# Scanned books and government documents dominate Commons text search and match
# place names constantly: "West Atherton" hit a biography, "Niles Essanay" hit
# a life of Col. Fremont, "Marina Point" hit an environmental impact statement.
DOCUMENT = re.compile(
    r"(the life of|history of|memoirs|annual report|environmental statement|"
    r"information-|proceedings|catalogue|directory|bulletin|\bvol\b|"
    r"\bpage \d|\bplate \d|title page|frontispiece|bulletin no)", re.I)

# HABS/HAER architectural surveys are free and well-labelled but are interior
# details and measured drawings, not streetscapes.
SURVEY_INTERIOR = re.compile(
    r"\b(first|second|third) floor\b|\binterior\b|\bdetail of\b|\bstairway detail\b|"
    r"\bhall of mirrors\b|\bfireplace\b|\bmantel\b|\bmeasured drawing\b", re.I)


def city_label(slug):
    return CITY_NAME.get(slug, slug.replace("-", " ").title())


def score(slot, cand):
    """Positive score means the filename itself places the photo."""
    title = cand["title"].replace("File:", "")
    low = title.lower()
    city = city_label(slot["city"]).lower()
    subject = slot["subject"].lower()
    pts, why = 0, []

    if OFFTOPIC.search(low):
        return -99, ["off-topic file type"]
    if DOCUMENT.search(low):
        return -99, ["scanned document or book, not a photograph"]
    if SURVEY_INTERIOR.search(low):
        return -99, ["architectural survey interior, not a streetscape"]

    if city in low:
        pts += 3
        why.append(f"names {city_label(slot['city'])}")
    if re.search(r"\bcalifornia\b|\bca\b", low):
        pts += 2
        why.append("names California")

    # Subject match only counts once the location is independently confirmed,
    # and never on its own for an ambiguous place name.
    head = re.split(r"\bor\b|,", subject)[0].strip()
    if head and len(head) > 4 and head in low:
        if head in AMBIGUOUS and pts == 0:
            why.append(f"'{head}' matched but is ambiguous and unplaced")
        else:
            pts += 1
            why.append(f"names '{head}'")

    if cand.get("width") and cand["width"] < 800:
        pts -= 2
        why.append(f"only {cand['width']}px wide")

    return pts, why


def main():
    accepted, rejected = [], []
    for slot in CAND:
        best = None
        for cand in slot.get("candidates", []):
            pts, why = score(slot, cand)
            cand = {**cand, "score": pts, "why": why}
            if best is None or pts > best["score"]:
                best = cand
        # Require the location to be confirmed by the filename (>=5 means the
        # city AND California both appear), not just a keyword collision.
        if best and best["score"] >= 5:
            accepted.append({**slot, "pick": best})
        else:
            rejected.append({**slot, "best": best})

    OUT.write_text(json.dumps(accepted, indent=1))
    print(f"accepted {len(accepted)} / {len(CAND)} slots "
          f"({len(accepted) / len(CAND) * 100:.0f}%)\n")
    from collections import Counter
    print("accepted by kind:", Counter(a["kind"] for a in accepted))
    print("needing a shoot: ", Counter(r["kind"] for r in rejected))
    print("\nAccepted picks:")
    for a in accepted:
        print(f"  {a['page']:28} {a['subject'][:34]:34} <- {a['pick']['title'][:60]}")
    if "-v" in sys.argv:
        print("\nNear misses (score 3-4):")
        for r in rejected:
            b = r.get("best")
            if b and 3 <= b["score"] < 5:
                print(f"  {r['page']:28} {r['subject'][:30]:30} ? {b['title'][:55]} "
                      f"[{', '.join(b['why'])}]")


if __name__ == "__main__":
    main()
