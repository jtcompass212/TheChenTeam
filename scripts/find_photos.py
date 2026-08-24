#!/usr/bin/env python3
"""Search Wikimedia Commons for a freely-licensed photo for each image slot.

Writes data/photo-candidates.json. Finds candidates only — it does not
download or wire anything up. Relevance still needs a human eye: a hit for
"Seacliff California" may be a different Seacliff.
"""
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
SLOTS = json.loads((ROOT / "data" / "photo-slots.json").read_text())
OUT = ROOT / "data" / "photo-candidates.json"
API = "https://commons.wikimedia.org/w/api.php"
UA = "TheChenTeam-photo-research/1.0 (huangbrynt@gmail.com)"

FREE = re.compile(r"cc[- ]?(by|zero)|public domain|pd-|cc0", re.I)

CITY_NAME = {
    "south-san-francisco": "South San Francisco", "mill-valley": "Mill Valley",
    "foster-city": "Foster City", "redwood-city": "Redwood City",
    "san-bruno": "San Bruno", "san-carlos": "San Carlos",
    "san-francisco": "San Francisco", "san-jose": "San Jose",
    "san-mateo": "San Mateo", "san-rafael": "San Rafael",
    "mountain-view": "Mountain View", "palo-alto": "Palo Alto",
}


def city_label(slug):
    return CITY_NAME.get(slug, slug.replace("-", " ").title())


def queries(slot):
    """Art direction often reads 'A or B'; try each alternative separately."""
    subject = re.sub(r"^(a|an|the)\s+", "", slot["subject"], flags=re.I)
    subject = re.sub(r"\s*~\d+.*$", "", subject).strip(" ,.")
    parts = [p.strip(" ,.") for p in re.split(r"\bor\b|,", subject) if p.strip(" ,.")]
    city = city_label(slot["city"])
    out = []
    for part in parts[:2]:
        part = re.sub(r"\s+", " ", part)
        if len(part) < 4:
            continue
        out.append(f"{part} {city} California")
        out.append(f"{part} California")
    if slot["kind"] == "thumb":
        out.insert(0, f"{slot['subject']} {city} California")
    return list(dict.fromkeys(out))[:3]


def search(q, limit=4):
    params = {
        "action": "query", "generator": "search", "gsrsearch": q,
        "gsrnamespace": "6", "gsrlimit": str(limit), "prop": "imageinfo",
        "iiprop": "url|extmetadata|size", "iiurlwidth": "1400", "format": "json",
    }
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=25) as fh:
            data = json.load(fh)
    except Exception as exc:
        return [{"error": str(exc)}]
    pages = (data.get("query") or {}).get("pages", {})
    hits = []
    for p in pages.values():
        ii = (p.get("imageinfo") or [{}])[0]
        em = ii.get("extmetadata", {})
        lic = em.get("LicenseShortName", {}).get("value", "")
        if not FREE.search(lic):
            continue
        artist = re.sub(r"<[^>]+>", "", em.get("Artist", {}).get("value", "")).strip()
        hits.append({
            "title": p["title"],
            "license": lic,
            "artist": artist[:120],
            "descurl": ii.get("descriptionurl", ""),
            "thumb": ii.get("thumburl", ""),
            "width": ii.get("width"), "height": ii.get("height"),
        })
    return hits


def main():
    results = []
    for i, slot in enumerate(SLOTS, 1):
        found, seen = [], set()
        for q in queries(slot):
            for hit in search(q):
                if "error" in hit:
                    continue
                if hit["title"] in seen:
                    continue
                seen.add(hit["title"])
                hit["query"] = q
                found.append(hit)
            time.sleep(0.25)
        results.append({**slot, "candidates": found})
        print(f"[{i:3}/{len(SLOTS)}] {slot['page']:28} {slot['subject'][:44]:44} "
              f"-> {len(found)}", flush=True)
    OUT.write_text(json.dumps(results, indent=1))
    hit = sum(1 for r in results if r["candidates"])
    print(f"\n{hit}/{len(results)} slots have at least one free-licensed candidate")


if __name__ == "__main__":
    main()
