#!/usr/bin/env python3
"""Build the San Francisco overview map widget.

    python3 scripts/build_sf_overview_map.py

Writes maps/san-francisco/map/san-francisco-overview-map.html, a Shared HTML
Widget in the same house style as the nine Peninsula overview maps.

Geometry comes from san-francisco-neighborhoods.geojson at the repo root. That
file is the right source and the previous hand-built widget was not: it carried
82 polygons on a different taxonomy, so nine of its shapes linked to pages that
do not exist (cole-valley, dogpatch, financial-district ...) while twenty-two
written neighborhoods had no shape at all. Slugifying the `name` property of the
root file matches all 95 pages exactly, which is why `name` is the only property
carried through.

Coordinates are rounded to five decimals, about a metre here. That is far finer
than a neighborhood boundary needs and takes the embedded geometry from 384KB to
roughly 54KB, which matters because the whole thing is pasted into a CMS field.

Two deliberate departures from the Peninsula maps, both forced by scale — 95
neighborhoods against Millbrae's 13:

  * A search box. Hunting for one neighborhood among 95 polygons by eye is not
    reasonable; the Peninsula maps do not need one.
  * 11px labels rather than 12px, with nowrap. 95 permanent labels crowd each
    other at 12px.

Everything else — 520px frame, palette, CARTO Voyager basemap, hover weights,
disabled scroll-wheel zoom, legend markup — matches the Peninsula widgets.
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "san-francisco-neighborhoods.geojson"
DEST = ROOT / "maps" / "san-francisco" / "map" / "san-francisco-overview-map.html"

# Pages live at /san-francisco/<slug>/ — the section is "san-francisco" and each
# page's filename is the slug. Anything else here produces a map full of 404s.
BASE_PATH = "/san-francisco/"
DP = 5


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower().replace("&", " and ")).strip("-")


def round_coords(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], DP), round(c[1], DP)]
    return [round_coords(x) for x in c]


def build_geojson():
    gj = json.loads(SRC.read_text())
    feats = []
    for f in gj["features"]:
        name = f["properties"]["name"]
        feats.append({
            "type": "Feature",
            "properties": {"name": name, "slug": slugify(name)},
            "geometry": {
                "type": f["geometry"]["type"],
                "coordinates": round_coords(f["geometry"]["coordinates"]),
            },
        })
    feats.sort(key=lambda f: f["properties"]["name"])
    return {"type": "FeatureCollection", "features": feats}


TEMPLATE = """<!-- NOTE: Paste this into a Shared HTML Widget (Content > Manage Shared HTML Widgets), NOT the inline TinyMCE page editor. TinyMCE strips <script> tags; Shared HTML Widgets don't. -->
<style>
  .sf-overview-wrap {{ position: relative; width: 100%; height: 520px; border-radius: 8px; overflow: hidden; border: 1px solid #dde1e9; font-family: 'Inter', system-ui, sans-serif; }}
  .sf-overview-wrap #sf-overview-map {{ width: 100%; height: 100%; }}
  .sf-overview-wrap .pk-label {{ background: transparent; border: none; box-shadow: none; font-weight: 600; font-size: 11px; color: #16233f; text-shadow: 0 1px 2px rgba(255,255,255,0.9), 0 -1px 2px rgba(255,255,255,0.9); white-space: nowrap; }}
  .sf-overview-wrap .pk-bottom-stack {{ position: absolute; bottom: 14px; left: 14px; z-index: 1000; display: flex; flex-direction: column; gap: 8px; width: 220px; max-width: calc(100% - 24px); }}
  .sf-overview-wrap .pk-legend {{ background: #ffffff; border: 1px solid #dde1e9; border-radius: 6px; padding: 10px 14px; font-size: 12px; color: #4b5468; display: flex; flex-direction: column; gap: 6px; }}
  .sf-overview-wrap .pk-legend span {{ display: inline-flex; align-items: center; gap: 6px; }}
  .sf-overview-wrap .pk-swatch {{ width: 12px; height: 12px; border-radius: 3px; display: inline-block; }}
  .sf-overview-wrap .pk-search {{ position: relative; width: 100%; }}
  .sf-overview-wrap .pk-search-input {{ width: 100%; box-sizing: border-box; padding: 9px 12px; font-size: 13px; font-family: inherit; border: 1px solid #dde1e9; border-radius: 6px; background: #ffffff; color: #16233f; box-shadow: 0 1px 3px rgba(22,35,63,0.12); outline: none; }}
  .sf-overview-wrap .pk-search-input:focus {{ border-color: #a8823d; }}
  .sf-overview-wrap .pk-search-results {{ position: absolute; left: 0; right: 0; bottom: calc(100% + 4px); background: #ffffff; border: 1px solid #dde1e9; border-radius: 6px; box-shadow: 0 4px 10px rgba(22,35,63,0.15); max-height: 240px; overflow-y: auto; display: none; }}
  .sf-overview-wrap .pk-search-results.open {{ display: block; }}
  .sf-overview-wrap .pk-search-item {{ padding: 8px 12px; font-size: 13px; color: #16233f; cursor: pointer; }}
  .sf-overview-wrap .pk-search-item:hover, .sf-overview-wrap .pk-search-item.active {{ background: #f4ede0; }}
  .sf-overview-wrap .pk-search-empty {{ padding: 8px 12px; font-size: 12.5px; color: #9aa1b3; }}
  @media (max-width: 480px) {{
    .sf-overview-wrap .pk-bottom-stack {{ width: 170px; }}
    .sf-overview-wrap .pk-search-input {{ padding: 7px 10px; font-size: 12.5px; }}
  }}
</style>
<div class="sf-overview-wrap">
  <div id="sf-overview-map"></div>
  <div class="pk-bottom-stack">
    <div class="pk-search">
      <input class="pk-search-input" type="text" placeholder="Search a neighborhood..." autocomplete="off" />
      <div class="pk-search-results"></div>
    </div>
    <div class="pk-legend">
      <span><span class="pk-swatch" style="background:#a8823d;"></span> San Francisco neighborhoods (click to explore)</span>
    </div>
  </div>
</div>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script>
(function() {{
  var BASE_PATH = "{base_path}";

  var neighborhoodData = {geojson};

  var map = L.map('sf-overview-map', {{ scrollWheelZoom: false, zoomControl: true }});

  // CARTO Voyager — colorful, labeled basemap (matches the per-neighborhood mini-maps).
  // HEADS UP: as of Aug 2026 CARTO requires a free API key for this raster endpoint.
  // Without one every tile is stamped "API KEY REQUIRED" — verified on the live site.
  // Append ?key=YOUR_KEY below once you have one. This affects all 144 map files,
  // not just this one, so whatever is decided here should be applied across maps/.
  L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png', {{
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    maxZoom: 19
  }}).addTo(map);

  var base = {{ color: '#8c6930', weight: 1.4, opacity: 1, fillColor: '#a8823d', fillOpacity: 0.26 }};
  var highlight = {{ color: '#8c2f22', weight: 2.6, opacity: 1, fillColor: '#c0392b', fillOpacity: 0.45 }};

  var layerByName = {{}};
  var geoLayer = L.geoJSON(neighborhoodData, {{
    style: function() {{ return base; }},
    onEachFeature: function(feature, layer) {{
      var name = feature.properties.name;
      layerByName[name] = layer;
      layer.bindTooltip(name, {{ permanent: true, direction: 'center', className: 'pk-label' }});
      layer.on('mouseover', function() {{ layer.setStyle({{ fillOpacity: 0.5, weight: 2.2 }}); layer.bringToFront(); }});
      layer.on('mouseout',  function() {{ layer.setStyle(base); }});
      layer.on('click',     function() {{ window.location.href = BASE_PATH + feature.properties.slug + "/"; }});
      if (layer.getElement()) layer.getElement().style.cursor = 'pointer';
    }}
  }}).addTo(map);

  map.fitBounds(geoLayer.getBounds(), {{ padding: [24, 24] }});

  // --- Search box ---------------------------------------------------------
  var names = Object.keys(layerByName).sort();
  var wrap = document.querySelector('.sf-overview-wrap');
  var input = wrap.querySelector('.pk-search-input');
  var results = wrap.querySelector('.pk-search-results');
  var lastHighlighted = null;
  var activeIndex = -1;

  function clearHighlight() {{
    if (lastHighlighted) {{ lastHighlighted.setStyle(base); lastHighlighted = null; }}
  }}

  function selectNeighborhood(name) {{
    var layer = layerByName[name];
    if (!layer) return;
    clearHighlight();
    layer.setStyle(highlight);
    layer.bringToFront();
    lastHighlighted = layer;
    map.fitBounds(layer.getBounds(), {{ padding: [60, 60], maxZoom: 16 }});
    input.value = name;
    closeResults();
  }}

  function closeResults() {{
    results.classList.remove('open');
    results.innerHTML = '';
    activeIndex = -1;
  }}

  function renderResults(matches) {{
    results.innerHTML = '';
    if (!matches.length) {{
      var empty = document.createElement('div');
      empty.className = 'pk-search-empty';
      empty.textContent = 'No matching neighborhood';
      results.appendChild(empty);
      results.classList.add('open');
      return;
    }}
    matches.slice(0, 8).forEach(function(name) {{
      var item = document.createElement('div');
      item.className = 'pk-search-item';
      item.textContent = name;
      item.addEventListener('mousedown', function(e) {{ e.preventDefault(); selectNeighborhood(name); }});
      results.appendChild(item);
    }});
    results.classList.add('open');
  }}

  input.addEventListener('input', function() {{
    var q = input.value.trim().toLowerCase();
    if (!q) {{ closeResults(); return; }}
    renderResults(names.filter(function(n) {{ return n.toLowerCase().indexOf(q) !== -1; }}));
  }});

  input.addEventListener('keydown', function(e) {{
    var items = results.querySelectorAll('.pk-search-item');
    if (!items.length) return;
    if (e.key === 'ArrowDown') {{
      e.preventDefault();
      activeIndex = Math.min(activeIndex + 1, items.length - 1);
    }} else if (e.key === 'ArrowUp') {{
      e.preventDefault();
      activeIndex = Math.max(activeIndex - 1, 0);
    }} else if (e.key === 'Enter') {{
      e.preventDefault();
      selectNeighborhood(items[activeIndex >= 0 ? activeIndex : 0].textContent);
      return;
    }} else if (e.key === 'Escape') {{
      closeResults();
      return;
    }} else {{
      return;
    }}
    items.forEach(function(el, i) {{ el.classList.toggle('active', i === activeIndex); }});
  }});

  input.addEventListener('blur', function() {{ setTimeout(closeResults, 120); }});
  input.addEventListener('focus', function() {{ if (input.value.trim()) input.dispatchEvent(new Event('input')); }});
}})();
</script>
"""


def main():
    gj = build_geojson()
    html = TEMPLATE.format(
        base_path=BASE_PATH,
        geojson=json.dumps(gj, separators=(",", ":")),
    )
    DEST.write_text(html)
    print(f"{len(gj['features'])} neighborhoods -> {DEST.relative_to(ROOT)}")
    print(f"  {len(html):,} bytes  (links to {BASE_PATH}<slug>/)")


if __name__ == "__main__":
    main()
