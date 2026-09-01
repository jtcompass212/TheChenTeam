#!/usr/bin/env python3
"""Apply the reviewed picks from build_sf_hero_images.py's search pass.

The search pass (data/sf-hero-image-log.json) got 57/95 Commons candidates,
but a human pass over thumbnails of all 57 found 25 that were off-brand for
a real estate site (graffiti, a coffee-shop interior, a gravestone, B&W
archival scans, a mall interior, freeway signage, identifiable strangers in
a political photo-op...). A second, more targeted search round fixed 19 of
those with a genuine photo of the neighborhood; the other 6 have no free
photo worth using and fall back to the satellite crop like the rest.

data/sf-hero-overrides.json holds the 19 corrected picks (fetched with full
imageinfo/extmetadata via this script's sibling). This script is the one
that actually downloads and wires all 95 pages.
"""
import json
import pathlib
import re
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_sf_hero_images as b  # noqa: E402

LOG = json.loads((ROOT / "data" / "sf-hero-image-log.json").read_text())
OVERRIDES = json.loads((ROOT / "data" / "sf-hero-overrides.json").read_text())

# Reviewed and rejected with no better free photo found on a second search
# pass either -- these fall back to the satellite crop.
FORCE_SATELLITE = {
    "duboce-triangle", "lakeside", "panhandle", "parkside", "portola", "stonestown",
}


def main():
    bboxes = b.load_geojson_bbox()
    b.IMGDIR.mkdir(parents=True, exist_ok=True)

    results = []
    for i, entry in enumerate(LOG, 1):
        slug = entry["slug"]
        name = entry["name"]
        if slug in FORCE_SATELLITE:
            source, pick = "satellite", None
        elif slug in OVERRIDES:
            source, pick = "commons", OVERRIDES[slug]
        elif entry["source"] == "commons":
            source, pick = "commons", entry["pick"]
        else:
            source, pick = "satellite", None

        filename = f"{slug}-hero.jpg"
        dest = b.IMGDIR / filename

        if source == "commons":
            url = b.thumb_url(pick["title"], width=1600) if "thumb" not in pick or not pick.get("thumb") else pick["thumb"]
            if not url:
                url = b.thumb_url(pick["title"], width=1600)
            req = urllib.request.Request(url, headers={"User-Agent": b.UA})
            dest.write_bytes(urllib.request.urlopen(req, timeout=60).read())
            artist = pick["artist"] or "Unknown"
            title = pick["title"].replace("File:", "")
            if b.NO_CREDIT_NEEDED.search(pick["license"]):
                caption = f'Photo: <a href="{pick["descurl"]}">{title}</a> &mdash; {pick["license"]}, via Wikimedia Commons'
            else:
                caption = (f'Photo: <a href="{pick["descurl"]}">{title}</a> by {artist} '
                           f'&mdash; {pick["license"]}, via Wikimedia Commons')
            alt = f"{name}, San Francisco, CA"
            credit = {"alt": alt, "caption": caption}
        else:
            bbox = bboxes.get(slug)
            if not bbox:
                print(f"  !! no geometry for {slug}")
                continue
            b.fetch_satellite(slug, bbox, dest)
            alt = f"Satellite view of the {name} neighborhood in San Francisco, CA"
            caption = "Imagery: Esri World Imagery (Maxar, Earthstar Geographics)"
            credit = {"alt": alt, "caption": caption}

        ok = b.wire_page(slug, name, filename, credit)
        size_kb = dest.stat().st_size // 1024 if dest.exists() else 0
        print(f"[{i:3}/{len(LOG)}] {slug:36} {source:10} {size_kb:4}KB {'' if ok else 'WIRE FAILED'}")
        results.append({"slug": slug, "name": name, "source": source, "kb": size_kb, "wired": ok})
        time.sleep(0.1)

    commons_n = sum(1 for r in results if r["source"] == "commons")
    fails = [r["slug"] for r in results if not r["wired"]]
    print(f"\n{commons_n}/{len(results)} Commons photos, {len(results)-commons_n}/{len(results)} satellite")
    if fails:
        print("WIRING FAILURES:", fails)
    (ROOT / "data" / "sf-hero-image-final-log.json").write_text(json.dumps(results, indent=1))


if __name__ == "__main__":
    main()
