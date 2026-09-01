#!/usr/bin/env python3
"""Source and wire hero images for the 95 San Francisco neighborhood pages.

For each neighborhood, search Wikimedia Commons for a genuine, confidently
matched, freely-licensed photo (street view or scenic landmark) and require
the filename to independently confirm both the neighborhood name and "San
Francisco" -- a keyword hit alone is not evidence, per the same trap this
project's find_photos.py/triage_photos.py already document (a hit for
"Presidio" or "Portola" can easily be a different Presidio or Portola).

Falls back to a top-down satellite crop (Esri World Imagery, keyless) built
from the neighborhood's boundary in san-francisco-neighborhoods.geojson when
no photo confidently places itself in that specific SF neighborhood -- most
named residential tracts here have no dedicated photography, which is why
this is a fallback and not the first move.

Usage:
    python3 scripts/build_sf_hero_images.py            # do everything
    python3 scripts/build_sf_hero_images.py --dry-run   # search only, print picks
"""
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = ROOT / "neighborhood-pages" / "san-francisco"
IMGDIR = ROOT / "neighborhood-images" / "san-francisco"
GEOJSON = ROOT / "san-francisco-neighborhoods.geojson"
UA = "TheChenTeamPhotoResearch/1.0 (https://thechenteam.com; huangbrynt@gmail.com)"
API = "https://commons.wikimedia.org/w/api.php"
ESRI = ("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/"
        "MapServer/export")

FREE = re.compile(r"cc[- ]?(by|zero)|public domain|pd-|cc0", re.I)
OFFTOPIC = re.compile(
    r"\b(map|logo|seal|coat of arms|diagram|chart|graph|plaque|sign|signage|"
    r"portrait|headshot|gravestone|tombstone|panorama of the world|flag)\b", re.I)
DOCUMENT = re.compile(
    r"(the life of|history of|memoirs|annual report|environmental statement|"
    r"information-|proceedings|catalogue|directory|bulletin|\bvol\b|"
    r"\bpage \d|\bplate \d|title page|frontispiece|bulletin no)", re.I)
SURVEY_INTERIOR = re.compile(
    r"\b(first|second|third) floor\b|\binterior\b|\bdetail of\b|\bstairway detail\b|"
    r"\bhall of mirrors\b|\bfireplace\b|\bmantel\b|\bmeasured drawing\b", re.I)
NO_CREDIT_NEEDED = re.compile(r"public domain|cc0", re.I)

# Extra/alternate search terms for neighborhoods whose bare name under-searches
# their best-known landmark or reads as a generic word on Commons.
BOOST = {
    "alamo-square": ["Painted Ladies San Francisco"],
    "telegraph-hill": ["Coit Tower San Francisco"],
    "twin-peaks": ["Twin Peaks San Francisco view"],
    "golden-gate-park": ["Golden Gate Park San Francisco"],
    "presidio": ["Presidio of San Francisco"],
    "lincoln-park": ["Lincoln Park Lands End San Francisco"],
    "union-square": ["Union Square San Francisco California"],
    "civic-center": ["San Francisco City Hall Civic Center"],
    "mission-dolores": ["Mission Dolores San Francisco", "Mission San Francisco de Asis"],
    "mission-district": ["Mission District San Francisco street"],
    "dolores-park": ["Dolores Park San Francisco"],
    "eureka-valley-dolores-heights": ["Dolores Park San Francisco", "Castro Street San Francisco"],
    "haight-ashbury": ["Haight Street San Francisco"],
    "north-beach": ["North Beach San Francisco street"],
    "russian-hill": ["Russian Hill San Francisco", "Lombard Street San Francisco"],
    "nob-hill": ["Nob Hill San Francisco cable car"],
    "pacific-heights": ["Pacific Heights San Francisco mansion"],
    "marina-district": ["Marina District San Francisco"],
    "cow-hollow": ["Cow Hollow San Francisco Union Street"],
    "sea-cliff": ["Sea Cliff San Francisco"],
    "hayes-valley": ["Hayes Valley San Francisco"],
    "south-beach": ["South Beach San Francisco Oracle Park"],
    "potrero-hill": ["Potrero Hill San Francisco"],
    "bernal-heights": ["Bernal Heights San Francisco"],
    "glen-park": ["Glen Park San Francisco"],
    "west-portal": ["West Portal San Francisco"],
    "financial-district-barbary-coast": ["Financial District San Francisco skyline"],
    "yerba-buena": ["Yerba Buena Gardens San Francisco"],
    "noe-valley": ["Noe Valley San Francisco"],
    "buena-vista": ["Buena Vista Park San Francisco"],
    "mount-davidson-manor": ["Mount Davidson San Francisco cross"],
    "lake-merced-park": ["Lake Merced San Francisco"],
    "candlestick-point": ["Candlestick Point San Francisco"],
    "central-waterfront-dogpatch": ["Dogpatch San Francisco street"],
    "mission-bay": ["Mission Bay San Francisco"],
    "portola": ["Portola San Francisco"],
    "excelsior": ["Excelsior San Francisco"],
    "visitacion-valley": ["Visitacion Valley San Francisco"],
    "western-addition": ["Western Addition San Francisco"],
    "tenderloin": ["Tenderloin San Francisco street"],
    "north-panhandle": ["Panhandle Golden Gate Park San Francisco"],
    "panhandle": ["Panhandle Golden Gate Park San Francisco"],
    "duboce-triangle": ["Duboce Park San Francisco"],
    "corona-heights": ["Corona Heights San Francisco"],
    "diamond-heights": ["Diamond Heights San Francisco"],
    "forest-hill": ["Forest Hill San Francisco Muni station"],
    "saint-francis-wood": ["St Francis Wood San Francisco"],
    "cole-valley-parnassus-heights": ["Cole Valley San Francisco", "Parnassus Heights San Francisco"],
    "inner-sunset": ["Inner Sunset San Francisco"],
    "outer-sunset": ["Outer Sunset San Francisco"],
    "central-sunset": ["Sunset District San Francisco"],
    "inner-richmond": ["Inner Richmond San Francisco"],
    "outer-richmond": ["Outer Richmond San Francisco"],
    "central-richmond": ["Richmond District San Francisco"],
    "bayview": ["Bayview San Francisco"],
    "hunters-point": ["Hunters Point San Francisco"],
    "stonestown": ["Stonestown Galleria San Francisco"],
}

SKIP_NAME_WORDS = {"and", "san", "francisco", "the", "of"}


def load_geojson_bbox():
    data = json.loads(GEOJSON.read_text())
    out = {}
    for feat in data["features"]:
        name = feat["properties"]["name"]
        slug = re.sub(r"[^a-z0-9]+", "-", name.replace("/", "-").lower()).strip("-")
        coords = feat["geometry"]["coordinates"]
        lons, lats = [], []

        def walk(c):
            if isinstance(c[0], (int, float)):
                lons.append(c[0])
                lats.append(c[1])
            else:
                for x in c:
                    walk(x)
        walk(coords)
        out[slug] = (min(lons), min(lats), max(lons), max(lats))
    return out


def page_display_name(slug):
    html = (PAGES / f"{slug}.html").read_text()
    m = re.search(r"<h1[^>]*>([^<]+) Homes &amp; Real Estate", html)
    return m.group(1).strip()


def commons_search(q, limit=6):
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
            "title": p["title"], "license": lic, "artist": artist[:120],
            "descurl": ii.get("descriptionurl", ""), "thumb": ii.get("thumburl", ""),
            "width": ii.get("width"), "height": ii.get("height"),
        })
    return hits


def name_tokens(name):
    parts = re.split(r"[&/]|\bor\b", name)
    toks = []
    for p in parts:
        w = [t for t in re.findall(r"[a-z0-9]+", p.lower()) if t not in SKIP_NAME_WORDS]
        if w:
            toks.append(w)
    return toks


def score(name, cand):
    low = cand["title"].replace("File:", "").lower()
    if OFFTOPIC.search(low) or DOCUMENT.search(low) or SURVEY_INTERIOR.search(low):
        return -99, "off-topic/document/interior"
    pts, why = 0, []
    if "san francisco" in low:
        pts += 2
        why.append("names San Francisco")
    for group in name_tokens(name):
        if all(w in low for w in group):
            pts += 3
            why.append(f"names {' '.join(group)}")
            break
    if cand.get("width") and cand["width"] < 800:
        pts -= 2
        why.append("low-res")
    return pts, "; ".join(why)


def find_photo(slug, name):
    queries = [f"{name.replace(' & ', ' ')} San Francisco California"]
    queries += BOOST.get(slug, [])
    for part in name.split(" & "):
        if part.strip() != name:
            queries.append(f"{part.strip()} San Francisco")
    seen, best = set(), None
    for q in queries:
        for cand in commons_search(q):
            if "error" in cand or cand["title"] in seen:
                continue
            seen.add(cand["title"])
            pts, why = score(name, cand)
            cand = {**cand, "score": pts, "why": why, "query": q}
            if best is None or pts > best["score"]:
                best = cand
        time.sleep(0.2)
    if best and best["score"] >= 5:
        return best
    return None


def thumb_url(title, width=1600):
    q = {"action": "query", "titles": title, "prop": "imageinfo",
         "iiprop": "url", "iiurlwidth": str(width), "format": "json"}
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(q),
                                  headers={"User-Agent": UA})
    d = json.load(urllib.request.urlopen(req, timeout=30))
    for p in (d.get("query") or {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        return (ii.get("thumburl") or ii.get("url", "")).split("?")[0]
    return ""


def fetch_satellite(slug, bbox, dest):
    xmin, ymin, xmax, ymax = bbox
    # Pad ~12% so the crop shows context beyond the boundary edge, then clamp
    # to a 900:650 aspect box centered on the neighborhood.
    cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
    w, h = (xmax - xmin) * 1.25, (ymax - ymin) * 1.25
    aspect = 900 / 650
    if w / h > aspect:
        h = w / aspect
    else:
        w = h * aspect
    bbox_s = f"{cx - w/2},{cy - h/2},{cx + w/2},{cy + h/2}"
    url = (f"{ESRI}?bbox={bbox_s}&bboxSR=4326&size=900,650&format=jpg&f=image")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    dest.write_bytes(urllib.request.urlopen(req, timeout=60).read())


PLACEHOLDER = re.compile(
    r'<div style="align-self: stretch; min-height: 280px; border-radius: 4px; '
    r'overflow: hidden; background: #f0f2f6; display: flex; align-items: center; '
    r'justify-content: center;"><span style="font-size: 13px; color: #9ba3b5; '
    r'text-align: center; letter-spacing: 0.04em;">\[ HERO IMAGE \]<br>'
    r'A representative [^<]+ street or view<br>~900&times;650</span></div>')


def wire_page(slug, name, filename, credit_html):
    page = PAGES / f"{slug}.html"
    html = page.read_text()
    img = (f'<img src="../../neighborhood-images/san-francisco/{filename}" '
           f'alt="{credit_html["alt"]}" style="width: 100%; height: 100%; '
           f'object-fit: cover; display: block;">')
    if credit_html.get("caption"):
        block = (
            '<div style="align-self: stretch; display: flex; flex-direction: column; '
            'gap: 6px;"><div style="flex: 1 1 auto; min-height: 200px; border-radius: 4px; '
            f'overflow: hidden;">{img}</div>'
            f'<p style="font-size: 11px; color: #9ba3b5; line-height: 1.5; margin: 0px 2px;">'
            f'{credit_html["caption"]}</p></div>')
    else:
        block = ('<div style="align-self: stretch; min-height: 280px; border-radius: 4px; '
                  f'overflow: hidden;">{img}</div>')
    new_html, n = PLACEHOLDER.subn(block, html, count=1)
    if not n:
        print(f"  !! placeholder not found for {slug}")
        return False
    page.write_text(new_html)
    return True


def main():
    dry = "--dry-run" in sys.argv
    only = None
    for a in sys.argv[1:]:
        if a.startswith("--only="):
            only = set(a.split("=", 1)[1].split(","))

    bboxes = load_geojson_bbox()
    slugs = sorted(p.stem for p in PAGES.glob("*.html"))
    if only:
        slugs = [s for s in slugs if s in only]
    IMGDIR.mkdir(parents=True, exist_ok=True)

    log = []
    for i, slug in enumerate(slugs, 1):
        name = page_display_name(slug)
        pick = find_photo(slug, name)
        source = "commons" if pick else "satellite"
        print(f"[{i:3}/{len(slugs)}] {slug:36} {name[:32]:32} -> {source}"
              + (f"  ({pick['title'][:50]})" if pick else ""))
        log.append({"slug": slug, "name": name, "source": source,
                     "pick": pick})
        if dry:
            continue

        filename = f"{slug}-hero.jpg"
        dest = IMGDIR / filename
        if source == "commons":
            url = thumb_url(pick["title"])
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            dest.write_bytes(urllib.request.urlopen(req, timeout=60).read())
            artist = pick["artist"] or "Unknown"
            title = pick["title"].replace("File:", "")
            if NO_CREDIT_NEEDED.search(pick["license"]):
                caption = f'Photo: <a href="{pick["descurl"]}">{title}</a> &mdash; {pick["license"]}, via Wikimedia Commons'
            else:
                caption = (f'Photo: <a href="{pick["descurl"]}">{title}</a> by {artist} '
                           f'&mdash; {pick["license"]}, via Wikimedia Commons')
            alt = f"{name}, San Francisco, CA"
            credit = {"alt": alt, "caption": caption}
        else:
            bbox = bboxes.get(slug)
            if not bbox:
                print(f"  !! no geometry for {slug}, skipping")
                continue
            fetch_satellite(slug, bbox, dest)
            alt = f"Satellite view of the {name} neighborhood in San Francisco, CA"
            caption = "Imagery: Esri World Imagery (Maxar, Earthstar Geographics)"
            credit = {"alt": alt, "caption": caption}
        time.sleep(0.15)
        wire_page(slug, name, filename, credit)

    (ROOT / "data" / "sf-hero-image-log.json").write_text(json.dumps(log, indent=1))
    commons_n = sum(1 for x in log if x["source"] == "commons")
    print(f"\n{commons_n}/{len(log)} from Wikimedia Commons, "
          f"{len(log) - commons_n}/{len(log)} satellite fallback")


if __name__ == "__main__":
    main()
