"""Rasterise Natural Earth 1:50m countries (public domain) into approximate 1914 states for the war map.
python3 -I 03a_map_raster.py <ne_50m_admin_0_countries.geojson> <out_dir>
Writes map_state.png (R: ignite time 0..1 = film frames IGN0..IGN1, 1 = never; G: side 0 neutral / 0.5 Central / 1 Allied;
B: borders; A: land) and map_height.png (fake relief: land plateau + mountain ridges along the Alps, Carpathians, Dinarides,
Pyrenees, Balkans, Scandinavia, Caucasus). Map space: 1 Blender metre = 1 km, Sarajevo at the origin; no text anywhere."""
import sys, json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
src, out = sys.argv[1], sys.argv[2]
LON0, LAT0 = 18.41, 43.86
KX = 111.32 * math.cos(math.radians(46.0)); KY = 111.0
XMIN, XMAX, YMIN, YMAX = -2600.0, 2600.0, -2400.0, 3400.0     # km around Sarajevo
NX, NY = 4096, int(4096 * (YMAX - YMIN) / (XMAX - XMIN))
IGN0, IGN1 = 1400, 1826
def px(lon, lat):
    x = (lon - LON0) * KX; y = (lat - LAT0) * KY
    return ((x - XMIN) / (XMAX - XMIN) * NX, (YMAX - y) / (YMAX - YMIN) * NY)
# id: (members, side 1 Central / 2 Allied, ignite frame, entry lon/lat): the war spreads from the two first countries outward
STATES = {
    1: (["Austria", "Hungary", "Czechia", "Slovakia", "Slovenia", "Croatia", "Bosnia and Herzegovina"], 1, 1460, (18.41, 43.86)),
    2: (["Republic of Serbia", "Kosovo", "North Macedonia"], 2, 1478, (20.46, 44.8)),
    15: (["Montenegro"], 2, 1560, (19.26, 42.44)),
    3: (["Russia", "Belarus", "Ukraine", "Moldova", "Lithuania", "Latvia", "Estonia", "Finland", "Poland", "Georgia", "Armenia", "Azerbaijan"], 2, 1520, (24.0, 50.0)),
    4: (["Germany", "Luxembourg"], 1, 1545, (13.4, 50.5)),
    5: (["France", "Monaco"], 2, 1590, (7.5, 48.5)),
    6: (["Belgium"], 2, 1585, (6.1, 50.4)),
    7: (["United Kingdom", "Ireland", "Isle of Man", "Jersey", "Guernsey"], 2, 1625, (1.3, 51.2)),
    8: (["Turkey", "Syria", "Iraq", "Lebanon", "Israel", "Palestine", "Jordan", "Northern Cyprus"], 1, 1660, (28.9, 41.1)),
    9: (["Bulgaria"], 1, 1700, (22.9, 43.4)),
    10: (["Italy", "San Marino", "Vatican"], 2, 1720, (12.5, 46.4)),
    11: (["Romania"], 2, 1745, (23.5, 45.6)),
    12: (["Portugal"], 2, 1765, (-8.0, 40.5)),
    13: (["Greece"], 2, 1780, (22.0, 40.8)),
}
NEUTRAL = 20
member = {m: sid for sid, (ms, side, t, e) in STATES.items() for m in ms}
ids = Image.new("I", (NX, NY), 0); dr = ImageDraw.Draw(ids)
border = Image.new("L", (NX, NY), 0); db = ImageDraw.Draw(border)
d = json.load(open(src))
for ft in d["features"]:
    nm = ft["properties"]["ADMIN"]; g = ft["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    sid = member.get(nm, NEUTRAL)
    for poly in polys:
        ring = poly[0]
        if all(not (-30 < p[0] < 70 and 25 < p[1] < 75) for p in ring): continue
        pts = [px(*p) for p in ring]
        if len(pts) < 3: continue
        dr.polygon(pts, fill=sid)
for ft in d["features"]:
    g = ft["geometry"]; nm = ft["properties"]["ADMIN"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    for poly in polys:
        ring = poly[0]
        if all(not (-30 < p[0] < 70 and 25 < p[1] < 75) for p in ring): continue
        pts = [px(*p) for p in ring]
        if len(pts) >= 2: db.line(pts + [pts[0]], fill=255, width=2)
I = np.array(ids, dtype=np.int32)
land = (I > 0)
# internal state borders only where the state id changes (coastlines are not drawn as borders)
st = I.copy()
edge = np.zeros_like(land)
for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
    sh = np.roll(np.roll(st, dy, 0), dx, 1)
    edge |= (st != sh) & (st > 0) & (sh > 0)
edge_img = Image.fromarray((edge * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
# ignite time per pixel: the state's ignite frame + distance from its entry point / spread speed (fire spreading in)
yy, xx = np.mgrid[0:NY, 0:NX].astype(np.float32)
kmx = (XMAX - XMIN) / NX; kmy = (YMAX - YMIN) / NY
T = np.full((NY, NX), 1e9, np.float32); SIDE = np.zeros((NY, NX), np.float32)
SPEED = 38.0     # km per frame
for sid, (ms, side, t0, (elon, elat)) in STATES.items():
    m = (I == sid)
    if not m.any(): continue
    ex, ey = px(elon, elat)
    dist = np.hypot((xx - ex) * kmx, (yy - ey) * kmy)
    T[m] = t0 + dist[m] / SPEED
    SIDE[m] = 0.5 if side == 1 else 1.0
R = np.clip((T - IGN0) / (IGN1 - IGN0), 0, 1)
R[T > 1e8] = 1.0
G = SIDE
B = np.asarray(edge_img, np.float32) / 255.0
A = land.astype(np.float32)
rgba = np.stack([R, G, B, A], -1)
Image.fromarray((rgba * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(out, "map_state.png"))
# fake relief (heights 0..1): a low land plateau + gaussian ridges along the big ranges
H = np.zeros((NY, NX), np.float32)
RANGES = {   # (lon, lat) polylines, peak 0..1, half-width km
    "alps": ([(5.8, 44.2), (7.0, 45.9), (8.5, 46.4), (10.5, 46.6), (12.5, 47.0), (14.5, 47.3), (16.0, 47.6)], 1.0, 110),
    "carpathians": ([(17.5, 48.6), (20.0, 49.3), (22.5, 49.0), (24.5, 47.8), (25.5, 46.5), (25.8, 45.5), (24.0, 45.4), (22.5, 45.3)], 0.55, 90),
    "dinarides": ([(14.5, 45.6), (16.0, 44.6), (17.5, 43.6), (19.0, 42.8), (20.0, 42.2)], 0.55, 80),
    "balkan": ([(22.5, 43.3), (24.5, 42.8), (26.5, 42.7)], 0.4, 60),
    "pyrenees": ([(-1.8, 43.1), (0.5, 42.7), (2.5, 42.5)], 0.6, 60),
    "scandes": ([(6.0, 59.0), (8.5, 61.5), (12.5, 63.5), (15.0, 66.0), (18.0, 68.5)], 0.6, 120),
    "caucasus": ([(38.0, 44.0), (42.0, 43.0), (46.0, 41.8), (49.0, 40.8)], 0.85, 90),
    "apennines": ([(8.5, 44.4), (11.0, 44.0), (13.0, 42.5), (15.5, 40.5), (16.3, 39.0)], 0.35, 60),
    "anatolia": ([(28.0, 39.0), (32.0, 39.0), (36.0, 39.0), (40.0, 39.5)], 0.45, 220),
    "iberia": ([(-6.0, 40.5), (-3.5, 40.0), (-1.0, 40.5)], 0.35, 220),
}
for nm_, (line, pk, hw) in RANGES.items():
    pts = [px(*p) for p in line]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        vx, vy = x1 - x0, y1 - y0; L2 = vx * vx + vy * vy
        t = np.clip(((xx - x0) * vx + (yy - y0) * vy) / L2, 0, 1)
        dd = np.hypot((xx - (x0 + t * vx)) * kmx, (yy - (y0 + t * vy)) * kmy)
        H = np.maximum(H, pk * np.exp(-(dd / hw) ** 2))
rng = np.random.default_rng(4)
noise = np.asarray(Image.fromarray((rng.random((NY // 16, NX // 16)) * 255).astype(np.uint8)).resize((NX, NY), Image.BICUBIC), np.float32) / 255.0
noise2 = np.asarray(Image.fromarray((rng.random((NY // 4, NX // 4)) * 255).astype(np.uint8)).resize((NX, NY), Image.BICUBIC), np.float32) / 255.0
coast = np.asarray(Image.fromarray((land * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4)), np.float32) / 255.0
Hl = (0.08 + 0.10 * noise + H * (0.75 + 0.5 * noise2)) * coast
# flat under the city set (Sarajevo at the origin): no relief within ~25 km so nothing rises through the streets
sx, sy = px(LON0, LAT0)
dS = np.hypot((xx - sx) * kmx, (yy - sy) * kmy)
Hl = Hl * np.clip((dS - 250.0) / 150.0, 0, 1)    # v009: wide flat zone so the coarse subdivision + smoothing never lifts the map into the set
Image.fromarray((np.clip(Hl, 0, 1) * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(1.2)).save(os.path.join(out, "map_height.png"))
print("MAP", NX, NY, "states", {k: int((I == k).sum()) for k in STATES})
