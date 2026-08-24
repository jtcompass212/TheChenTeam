#!/usr/bin/env python3
"""Download the reviewed-and-accepted Commons photos and wire them into pages.

Every image carries attribution. CC BY / BY-SA require credit; public-domain
and CC0 files do not, but are credited anyway so the provenance of everything
on the page is visible in one place.
"""
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHORT = json.loads((ROOT / "data" / "photo-shortlist.json").read_text())
DEC = json.loads((ROOT / "data" / "photo-decisions.json").read_text())
IMGDIR = ROOT / "city-images" / "sourced"
UA = "TheChenTeamPhotoResearch/1.0 (https://thechenteam.com; huangbrynt@gmail.com)"
API = "https://commons.wikimedia.org/w/api.php"

NO_CREDIT_NEEDED = re.compile(r"public domain|cc0", re.I)


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48]


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


def main():
    IMGDIR.mkdir(parents=True, exist_ok=True)
    accepted = [(i, SHORT[i]) for i in DEC["accept"]]
    wired, credits = [], {}

    for idx, slot in accepted:
        pick = slot["pick"]
        city = slot["page"].split("/", 1)[1]
        name = f"{city}-{slugify(slot['subject'])}.jpg"
        dest = IMGDIR / name
        if not dest.exists():
            url = thumb_url(pick["title"])
            if not url:
                print(f"  !! no url for {pick['title']}")
                continue
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            dest.write_bytes(urllib.request.urlopen(req, timeout=60).read())
            time.sleep(0.3)
        wired.append((idx, slot, name))
        credits.setdefault(city, []).append((slot, pick))
        print(f"  {name}  ({dest.stat().st_size // 1024} KB)")

    # --- wire into the pages -------------------------------------------------
    THUMB_INNER = (
        '<div class="nb-thumb-inner" style="width: 100%; height: 100%; '
        'background-image: repeating-linear-gradient(135deg, rgb(226, 229, 236) 0px, '
        'rgb(226, 229, 236) 12px, rgb(237, 239, 243) 12px, rgb(237, 239, 243) 24px); '
        'display: flex; align-items: center; justify-content: center;">'
        '<span style="font-family: ui-monospace, monospace; font-size: 11px; '
        'color: #98a0b3;">[ IMAGE ]</span></div>')

    for city in sorted(credits):
        page = ROOT / "city-pages" / f"{city}.html"
        html = page.read_text()

        for _idx, slot, name in [w for w in wired if w[1]["page"].endswith("/" + city)]:
            alt = slot["subject"].split(" or ")[0].strip()
            img = (f'<img src="../city-images/sourced/{name}" alt="{alt}" '
                   f'style="width: 100%; height: 100%; object-fit: cover; display: block;">')

            if slot["kind"] == "feature":
                # feature placeholder: [ IMAGE ]<br>caption<br>size inside a span
                pat = re.compile(
                    r'<span style="font-family: ui-monospace, monospace; font-size: 12px; '
                    r'color: #98a0b3;[^"]*">\[ IMAGE \]<br>' + re.escape(slot["subject"]) +
                    r'<br>[^<]*</span>')
                html, n = pat.subn(img, html, count=1)
            else:
                # thumbnail: replace the first remaining striped placeholder that
                # sits immediately above this neighborhood's <h3>
                pat = re.compile(
                    r'<div class="nb-thumb-inner"[^>]*>\s*<span[^>]*>\[ IMAGE \]</span>\s*</div>'
                    r'(?=\s*</div>\s*<h3[^>]*>' + re.escape(slot["subject"]) + r'</h3>)', re.S)
                html, n = pat.subn(img, html, count=1)
                if not n:  # older markup: plain inline div, no nb-thumb-inner
                    pat = re.compile(
                        r'<div style="aspect-ratio: 4 / 3;[^"]*">\s*<span[^>]*>\[ IMAGE \]</span>\s*</div>'
                        r'(?=\s*<h3[^>]*>' + re.escape(slot["subject"]) + r'</h3>)', re.S)
                    html, n = pat.subn(
                        '<div style="aspect-ratio: 4 / 3; border-radius: 4px; overflow: hidden; '
                        'margin-bottom: 14px;">' + img + '</div>', html, count=1)
            print(f"    {city}/{slot['subject'][:34]:34} {'wired' if n else 'NOT MATCHED'}")

        # --- credits block ---------------------------------------------------
        rows = []
        for slot, pick in credits[city]:
            artist = re.sub(r"\s+", " ", pick["artist"]).strip() or "Unknown"
            artist = re.sub(r"^(Creator:|Related names:\s*)", "", artist).strip(" ,")
            title = pick["title"].replace("File:", "")
            if NO_CREDIT_NEEDED.search(pick["license"]):
                rows.append(f'<a href="{pick["descurl"]}">{title}</a> &mdash; {pick["license"]}')
            else:
                rows.append(f'<a href="{pick["descurl"]}">{title}</a> by {artist} '
                            f'&mdash; {pick["license"]}, via Wikimedia Commons')
        block = (
            '\n  <section style="max-width: 1180px; margin: 60px auto 0px; padding: 0px 32px;">'
            '\n    <p style="font-size: 11.5px; color: #9ba3b5; line-height: 1.7; margin: 0px; '
            'border-top: 1px solid rgb(237, 239, 243); padding-top: 14px;">'
            '<strong style="color: #7d8598; font-weight: 600;">Image credits:</strong> '
            + "; ".join(rows) + ".</p>\n  </section>")

        if "Image credits:" not in html:
            html = html.rstrip()
            assert html.endswith("</div>"), f"{city}: unexpected page ending"
            html = html[: -len("</div>")] + block + "\n</div>\n"
        page.write_text(html)

    print(f"\nwired {len(wired)} images across {len(credits)} city pages")


if __name__ == "__main__":
    main()
