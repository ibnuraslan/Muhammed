"""Rasterise Natural Earth 1:50m countries (public domain) into approximate 1914 states, heights and ignite frames.
python3 -I 06a_map_raster.py <ne_50m_admin_0_countries.geojson> <out.npz>
Map space: metres in the Blender scene, Sarajevo at the origin. x = (lon-18.41)*7.98, y = (lat-43.86)*11.1 (1 m ~ 10 km)."""
import sys, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
src, out = sys.argv[1], sys.argv[2]
LON0, LAT0, KX, KY = 18.41, 43.86, 7.98, 11.1
XMIN, XMAX, YMIN, YMAX = -270.0, 300.0, -150.0, 335.0
NX, NY = 1200, 1022
def px(lon, lat):
    x = (lon - LON0) * KX; y = (lat - LAT0) * KY
    return ((x - XMIN) / (XMAX - XMIN) * NX, (YMAX - y) / (YMAX - YMIN) * NY)
STATES = {   # id: (name, members, ignite seconds of film, entry lon/lat)
    1: ("AustriaHungary", ["Austria", "Hungary", "Czechia", "Slovakia", "Slovenia", "Croatia", "Bosnia and Herzegovina"], 29.55, (18.41, 43.86)),
    2: ("Serbia", ["Republic of Serbia", "Montenegro", "Kosovo", "North Macedonia"], 29.75, (19.3, 44.4)),
    3: ("Russia", ["Russia", "Belarus", "Ukraine", "Moldova", "Lithuania", "Latvia", "Estonia", "Finland", "Poland", "Georgia", "Armenia", "Azerbaijan"], 30.2, (23.5, 49.5)),
    4: ("Germany", ["Germany", "Luxembourg"], 30.5, (13.0, 50.3)),
    5: ("France", ["France", "Monaco"], 30.9, (7.2, 48.6)),
    6: ("Belgium", ["Belgium"], 30.85, (6.1, 50.4)),
    7: ("Britain", ["United Kingdom", "Ireland", "Isle of Man", "Jersey", "Guernsey"], 31.3, (1.3, 51.2)),
    8: ("Ottoman", ["Turkey", "Syria", "Iraq", "Lebanon", "Israel", "Palestine", "Jordan", "Northern Cyprus"], 31.7, (28.9, 41.1)),
    9: ("Bulgaria", ["Bulgaria"], 32.2, (22.9, 43.4)),
    10: ("Italy", ["Italy", "San Marino", "Vatican"], 32.4, (12.5, 46.4)),
    11: ("Romania", ["Romania"], 32.8, (23.5, 45.6)),
    12: ("Portugal", ["Portugal"], 33.1, (-8.0, 40.5)),
    13: ("Greece", ["Greece"], 33.3, (22.0, 40.8)),
    14: ("Montenegro", [], 99, (0, 0)),
}
NEUTRAL = 20
member = {m: sid for sid, (nm, ms, t, e) in STATES.items() for m in ms}
im = Image.new("I", (NX, NY), 0); dr = ImageDraw.Draw(im)
border = Image.new("L", (NX, NY), 0); db = ImageDraw.Draw(border)
d = json.load(open(src))
for ft in d["features"]:
    nm = ft["properties"]["ADMIN"]; g = ft["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    sid = member.get(nm, NEUTRAL)
    for poly in polys:
        ring = poly[0]
        lons = [p[0] for p in ring]; lats = [p[1] for p in ring]
        if max(lons) < -25 or min(lons) > 60 or max(lats) < 28 or min(lats) > 75: continue
        pts = [px(lo, la) for lo, la in ring]
        dr.polygon(pts, fill=sid)
        for hole in poly[1:]:
            dr.polygon([px(lo, la) for lo, la in hole], fill=0)
        db.line(pts + [pts[0]], fill=255, width=2)
sid = np.array(im, dtype=np.int32)
# state borders only (grouped states), plus coasts
bd = np.zeros(sid.shape, bool)
for dy, dx in ((0, 1), (1, 0), (1, 1)):
    a = sid[:sid.shape[0] - dy, :sid.shape[1] - dx]; b = sid[dy:, dx:]
    e = (a != b) & ((a > 0) & (b > 0))
    bd[:sid.shape[0] - dy, :sid.shape[1] - dx] |= e; bd[dy:, dx:] |= e
border = Image.fromarray((bd * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))
land = (sid > 0).astype(np.float32)
# relief: coast shelf + mountain ridges + noise
yy, xx = np.mgrid[0:NY, 0:NX].astype(np.float32)
X = XMIN + (xx + 0.5) / NX * (XMAX - XMIN); Y = YMAX - (yy + 0.5) / NY * (YMAX - YMIN)
lb = np.array(Image.fromarray((land * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), dtype=np.float32) / 255
RIDGES = [([(6, 44.3), (7.5, 46), (10, 46.6), (13, 47), (16, 47.6)], 3.2, 9),
          ([(17.5, 49.2), (20, 49.3), (23, 48.6), (25, 47.5), (25.8, 45.6), (23, 45.4), (22.4, 44.7)], 2.0, 8),
          ([(14.5, 45.6), (17, 44.2), (19, 42.9), (20.5, 41.5)], 2.0, 8), ([(-1.5, 43), (1, 42.7), (3, 42.5)], 2.4, 6),
          ([(22.5, 43.3), (26, 42.7)], 1.5, 6), ([(6, 59), (8, 61.5), (13, 64), (16, 67), (19, 69)], 2.0, 10),
          ([(38, 44), (42, 43), (46, 41.5)], 3.0, 8), ([(9, 44.3), (12, 43.5), (14, 42), (16, 40), (16.3, 38.5)], 1.6, 6),
          ([(28, 39), (33, 38.8), (40, 39.5), (44, 39)], 1.6, 18), ([(21, 40.2), (21.5, 38.5)], 1.6, 5),
          ([(12.5, 50.4), (16, 50.6)], 1.0, 5), ([(-5, 57), (-4, 57.8)], 1.1, 6), ([(-6, 40.5), (-3, 40.3), (-1, 38.5)], 1.4, 10),
          ([(57, 50), (59, 56), (59.5, 62)], 1.6, 8), ([(36, 36.5), (33, 37.2)], 1.6, 6)]
H = np.zeros_like(X)
for pts, amp, wid in RIDGES:
    P = [((lo - LON0) * KX, (la - LAT0) * KY) for lo, la in pts]
    dmin = np.full_like(X, 1e9)
    for (ax, ay), (bx, by) in zip(P, P[1:]):
        vx, vy = bx - ax, by - ay; L2 = vx * vx + vy * vy
        t = np.clip(((X - ax) * vx + (Y - ay) * vy) / L2, 0, 1)
        dmin = np.minimum(dmin, np.hypot(X - ax - t * vx, Y - ay - t * vy))
    H = np.maximum(H, amp * np.exp(-(dmin / wid) ** 2))
rng = np.random.default_rng(3)
def vnoise(scale, amp):
    g = rng.random((int(NY / scale) + 3, int(NX / scale) + 3)).astype(np.float32)
    gi = np.array(Image.fromarray((g * 255).astype(np.uint8)).resize((NX, NY), Image.BICUBIC), dtype=np.float32) / 255
    return (gi - 0.5) * amp
rough = vnoise(6, 0.6) + vnoise(18, 0.8) + vnoise(60, 0.8)
height = -1.1 + 1.45 * lb + lb * (H * (0.8 + 0.5 * np.clip(rough + 0.5, 0, 1.2)) + 0.25 * np.clip(rough, 0, None))
# ignite frame per pixel: state time + distance from entry / spread speed (m per second)
FPS = 60
ign = np.full_like(X, 99999.0)
for s_, (nm, ms, t, e) in STATES.items():
    if t > 90: continue
    ex, ey = (e[0] - LON0) * KX, (e[1] - LAT0) * KY
    dist = np.hypot(X - ex, Y - ey)
    sp = 140.0 if s_ == 3 else 95.0
    m = sid == s_
    ign[m] = (1 + (t + dist[m] / sp) * FPS)
np.savez_compressed(out, sid=sid.astype(np.int16), height=height.astype(np.float32), ignite=ign.astype(np.float32),
                    border=(np.array(border) > 0).astype(np.uint8), ext=np.array([XMIN, XMAX, YMIN, YMAX], np.float32))
print("MAP", sid.shape, "land", land.mean(), "h", height.min(), height.max(), {nm: int((sid == k).sum()) for k, (nm, *_) in STATES.items()})
