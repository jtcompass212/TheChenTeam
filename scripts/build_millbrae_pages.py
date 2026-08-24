#!/usr/bin/env python3
"""Fill the 13 Millbrae neighborhood scaffolds from data/millbrae-content.json.

The scaffolds in maps/millbrae/ carry the right structure but every content
slot reads "[ PLACEHOLDER ]". This writes the researched content into them and
moves the result to neighborhood-pages/millbrae/, matching where every other
written page lives.

Market figures are NOT set here — run scripts/apply_market_data.py afterwards
so Millbrae goes through the same sale-count thresholds as everywhere else.
"""
import json
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "maps" / "millbrae"
DEST = ROOT / "neighborhood-pages" / "millbrae"
CONTENT = json.loads((ROOT / "data" / "millbrae-content.json").read_text())
SHARED = CONTENT["_shared"]
SIMILAR = CONTENT["_similar"]


def fill_intro(html, text):
    """Replace the bracketed intro placeholder, keeping the closing sentence
    pattern the other neighborhood pages use."""
    name = re.search(r'<h1[^>]*>([^<]+?) Homes', html)
    nb = name.group(1) if name else "this neighborhood"
    closing = (f" Below you&rsquo;ll find current homes for sale in {nb}, "
               f"updated throughout the day.")
    return re.sub(
        r'(<p style="margin: 0px 0px 18px;">)\[ PLACEHOLDER[^\]]*\](</p>)',
        lambda m: m.group(1) + text + closing + m.group(2), html, count=1)


def fill_amenities(html, rows):
    """Four cards, in the scaffold's order: Parks, Grocery, Dining, Library."""
    rows = [r if r else SHARED["library"] for r in rows]
    it = iter(rows)

    def one(m):
        title, desc = next(it)
        return f"{m.group(1)}{title}{m.group(2)}{desc}{m.group(3)}"

    return re.sub(
        r'(margin-bottom: 4px;">)\[ name \](</p>|</div>\s*<p[^>]*>)\[ short description \](</p>)',
        one, html, count=4)


def fill_commute(html, rows):
    it = iter(rows)

    def one(m):
        mins, label = next(it)
        return f"{m.group(1)}{mins}{m.group(2)}{label}{m.group(3)}"

    return re.sub(
        r'(font-size: 30px; color: #16233f;">)\[ ~X min \](</div>\s*<div[^>]*>)\[[^\]]*\](</div>)',
        one, html, count=3)


def fill_similar(html):
    def one(m):
        nb = m.group(1)
        return m.group(0).replace(
            re.search(r'\[ PLACEHOLDER[^\]]*\]', m.group(0)).group(0),
            SIMILAR.get(nb, ""))
    return re.sub(
        r'<h3[^>]*>([^<]+)</h3>\s*<p[^>]*>\[ PLACEHOLDER[^\]]*\]</p>',
        one, html)


def fill_schools(html, rows):
    rows = [SHARED[r] if isinstance(r, str) else r for r in rows]
    it = iter(rows)

    def one(m):
        name, note = next(it)
        return f"{m.group(1)}{name}{m.group(2)}{note}{m.group(3)}"

    return re.sub(
        r'(font-weight: 600;">)\[ School name \](</div>\s*<div[^>]*>)\[[^\]]*\](</div>)',
        one, html, count=3)


def main():
    if not SRC.exists():
        print("no maps/millbrae/ scaffolds found"); return 1
    DEST.mkdir(parents=True, exist_ok=True)
    done, problems = [], []

    for slug, spec in CONTENT.items():
        if slug.startswith("_"):
            continue
        src = SRC / f"{slug}.html"
        if not src.exists():
            problems.append(f"{slug}: no scaffold at {src}")
            continue
        html = src.read_text()
        html = fill_intro(html, spec["intro"])
        html = fill_amenities(html, spec["amenities"])
        html = fill_commute(html, spec["commute"])
        html = fill_similar(html)
        html = fill_schools(html, spec["schools"])
        html = html.replace("<!-- 2. MARKET SNAPSHOT (PLACEHOLDER DATA) -->",
                            "<!-- 2. MARKET SNAPSHOT -->")

        # The scaffold's own header tells the author to fill the bracketed
        # sections. Once filled, swap it for the header the written pages use.
        html = re.sub(
            r'^<!-- [^\n]*PLACEHOLDER SCAFFOLD\).*?Content Area block\. -->\n',
            '<!-- Paste everything below into TinyMCE\'s Source Code view (the "<>" icon '
            'in the toolbar), not the WYSIWYG pane. -->'
            '<!-- NOTE: The interactive neighborhood MAP is a separate Shared HTML Widget '
            '— add it as a NEW page component\n     positioned AFTER this entire '
            'Content Area block. -->\n',
            html, count=1, flags=re.S)

        leftover = re.findall(r'\[ (?!HERO IMAGE|Month Year|\$X|&plusmn;)[^\]]{0,60}\]', html)
        if leftover:
            problems.append(f"{slug}: unfilled {leftover}")
        (DEST / f"{slug}.html").write_text(html)
        done.append(slug)

    print(f"wrote {len(done)} pages to {DEST.relative_to(ROOT)}/")
    for s in done:
        print("  " + s)
    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print("  " + p)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
