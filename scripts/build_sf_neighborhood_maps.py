#!/usr/bin/env python3
"""Build one map widget per San Francisco neighborhood.

    python3 scripts/build_sf_neighborhood_maps.py

Writes maps/san-francisco/<slug>-map.html for all 95 neighborhoods, matching the
per-neighborhood widgets the Peninsula cities already have: the neighborhood
filled and outlined in gold, its neighbors in grey and clickable, CARTO Voyager
underneath, 420px frame.

Geometry and slugs come from san-francisco-neighborhoods.geojson, the same source
as the overview map, so the two agree and every link resolves to a real page.

Neighbors are computed, not curated. Two neighborhoods are neighbors when their
outlines come within 30 metres of each other. Exact shared vertices alone are not
enough: the source is not a clean tessellation, and Mission District — which
plainly borders SoMa, Potrero, Bernal, Noe, Eureka Valley and Mission Dolores —
shares vertices with only two of them. At 30m it finds all seven. The tolerance
is small enough that nothing across town creeps in.

The primary feature is written LAST so Leaflet paints it on top, which keeps its
border unbroken along every shared edge. That trick is inherited from the
Peninsula widgets and is why no bringToFront call is needed.

Unlike the Peninsula maps, the view fits the primary neighborhood's bounds rather
than the whole cluster: these are meant to be zoomed into one neighborhood, with
the neighbors as context around the edges.
"""
import json
import math
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "san-francisco-neighborhoods.geojson"
DEST = ROOT / "maps" / "san-francisco"
KEY_FILE = ROOT / "data" / "carto-basemap-key.txt"

BASE_PATH = "/san-francisco/"
DP = 5
TOL_M = 30.0
LAT = 37.76
M_PER_DEG_LAT = 111_320.0
M_PER_DEG_LON = 111_320.0 * math.cos(math.radians(LAT))


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower().replace("&", " and ")).strip("-")


def round_coords(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], DP), round(c[1], DP)]
    return [round_coords(x) for x in c]


def collect_points(c, out):
    if isinstance(c[0], (int, float)):
        out.append((c[0], c[1]))
    else:
        for x in c:
            collect_points(x, out)


def build_adjacency(feats):
    verts, bbox = {}, {}
    for f in feats:
        n = f["properties"]["name"]
        v = []
        collect_points(f["geometry"]["coordinates"], v)
        verts[n] = v
        xs = [p[0] for p in v]
        ys = [p[1] for p in v]
        bbox[n] = (min(xs), min(ys), max(xs), max(ys))

    padx = TOL_M / M_PER_DEG_LON
    pady = TOL_M / M_PER_DEG_LAT
    tol2 = TOL_M * TOL_M

    def bbox_near(a, b):
        ax0, ay0, ax1, ay1 = bbox[a]
        bx0, by0, bx1, by1 = bbox[b]
        return not (ax1 + padx < bx0 or bx1 + padx < ax0
                    or ay1 + pady < by0 or by1 + pady < ay0)

    names = list(verts)
    adj = {n: set() for n in names}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if not bbox_near(a, b):
                continue
            hit = False
            for pa in verts[a]:
                for pb in verts[b]:
                    dx = (pa[0] - pb[0]) * M_PER_DEG_LON
                    dy = (pa[1] - pb[1]) * M_PER_DEG_LAT
                    if dx * dx + dy * dy <= tol2:
                        hit = True
                        break
                if hit:
                    break
            if hit:
                adj[a].add(b)
                adj[b].add(a)
    return adj


TEMPLATE = """<!-- NOTE: Paste this into a Shared HTML Widget (Content > Manage Shared HTML Widgets), NOT the inline TinyMCE page editor. TinyMCE strips <script> tags; Shared HTML Widgets don't. -->
<style>
  .{slug}-map-wrap {{ position: relative; width: 100%; height: 420px; border-radius: 8px; overflow: hidden; border: 1px solid #dde1e9; font-family: 'Inter', system-ui, sans-serif; }}
  .{slug}-map-wrap #{slug}-map {{ width: 100%; height: 100%; }}
  .{slug}-map-wrap .pk-label {{ background: transparent; border: none; box-shadow: none; font-weight: 600; font-size: 12px; color: #16233f; text-shadow: 0 1px 2px rgba(255,255,255,0.9), 0 -1px 2px rgba(255,255,255,0.9); white-space: nowrap; }}
  .{slug}-map-wrap .pk-legend {{ position: absolute; bottom: 14px; left: 14px; background: #ffffff; border: 1px solid #dde1e9; border-radius: 6px; padding: 10px 14px; font-size: 12px; color: #4b5468; z-index: 1000; display: flex; flex-direction: column; gap: 6px; }}
  .{slug}-map-wrap .pk-legend span {{ display: inline-flex; align-items: center; gap: 6px; }}
  .{slug}-map-wrap .pk-swatch {{ width: 12px; height: 12px; border-radius: 3px; display: inline-block; }}
</style>
<div class="{slug}-map-wrap">
  <div id="{slug}-map"></div>
  <div class="pk-legend">
    <span><span class="pk-swatch" style="background:#a8823d;"></span> {name_html}</span>
    <span><span class="pk-swatch" style="background:#c7cedb;"></span> Neighboring areas (click to explore)</span>
  </div>
</div>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script>
(function() {{
  var BASE_PATH = "{base_path}";

  // The primary neighborhood is listed LAST on purpose: Leaflet draws each feature's SVG path in array
  // order, so whatever comes last is drawn on top. This guarantees the primary border wins along every
  // shared edge — no separate "bring to front" call needed.
  var neighborhoodData = {geojson};

  var map = L.map('{slug}-map', {{ scrollWheelZoom: false, zoomControl: true }});

  // CARTO Voyager — same basemap as the citywide map. The ?key= is required; without
  // it every tile is stamped "API KEY REQUIRED". Key lives in data/carto-basemap-key.txt.
  L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png?key={carto_key}', {{
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    maxZoom: 19
  }}).addTo(map);

  var primaryLayer = null;

  var geoLayer = L.geoJSON(neighborhoodData, {{
    style: function(feature) {{
      var primary = feature.properties.primary;
      return {{
        color: primary ? '#8c6930' : '#9aa3b8',
        weight: primary ? 2.5 : 1.5,
        opacity: 1,
        fillColor: primary ? '#a8823d' : '#c7cedb',
        fillOpacity: primary ? 0.45 : 0.28
      }};
    }},
    onEachFeature: function(feature, layer) {{
      layer.bindTooltip(feature.properties.name, {{ permanent: true, direction: 'center', className: 'pk-label' }});
      if (feature.properties.primary) {{
        primaryLayer = layer;
      }} else {{
        layer.on('mouseover', function() {{ layer.setStyle({{ fillOpacity: 0.45 }}); }});
        layer.on('mouseout', function() {{ layer.setStyle({{ fillOpacity: 0.28 }}); }});
        layer.on('click', function() {{ window.location.href = BASE_PATH + feature.properties.slug + "/"; }});
        if (layer.getElement()) layer.getElement().style.cursor = 'pointer';
      }}
    }}
  }}).addTo(map);

  // Fit the neighborhood itself, not the whole cluster — the neighbors are context.
  map.fitBounds((primaryLayer || geoLayer).getBounds(), {{ padding: [28, 28] }});
}})();
</script>
"""


def main():
    gj = json.loads(SRC.read_text())
    feats = gj["features"]
    adj = build_adjacency(feats)
    by_name = {f["properties"]["name"]: f for f in feats}
    key = KEY_FILE.read_text().strip()

    DEST.mkdir(parents=True, exist_ok=True)
    written = 0
    neighbor_counts = []

    for name, f in sorted(by_name.items()):
        slug = slugify(name)
        neighbors = sorted(adj[name])
        neighbor_counts.append(len(neighbors))

        def feature(n, primary):
            g = by_name[n]["geometry"]
            return {
                "type": "Feature",
                "properties": {"name": n, "slug": slugify(n), "primary": primary},
                "geometry": {"type": g["type"],
                             "coordinates": round_coords(g["coordinates"])},
            }

        # primary last so Leaflet paints it on top
        collection = {
            "type": "FeatureCollection",
            "features": [feature(n, False) for n in neighbors] + [feature(name, True)],
        }

        html = TEMPLATE.format(
            slug=slug,
            name_html=name.replace("&", "&amp;"),
            base_path=BASE_PATH,
            carto_key=key,
            geojson=json.dumps(collection, separators=(",", ":")),
        )
        (DEST / f"{slug}-map.html").write_text(html)
        written += 1

    nc = sorted(neighbor_counts)
    print(f"{written} neighborhood maps -> {DEST.relative_to(ROOT)}/")
    print(f"  neighbors per map: min {nc[0]}, median {nc[len(nc)//2]}, max {nc[-1]}")


if __name__ == "__main__":
    main()
