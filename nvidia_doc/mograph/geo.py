"""Real geography (Natural Earth 1:50m, public domain) projected for the map shots."""
import os, math
import numpy as np
import shapefile
from style import W, H

GEO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "geo")

CITIES = {  # name: (lon, lat)
    "WASHINGTON": (-77.04, 38.91), "BEIJING": (116.40, 39.90), "SHANGHAI": (121.47, 31.23),
    "SINGAPORE": (103.82, 1.35), "INDONESIA": (106.85, -6.21), "TAIPEI": (121.56, 25.03),
    "UNITED STATES": (-98.0, 39.0), "CHINA": (104.0, 35.0),
}

# camera views: centre lon/lat, pixels per degree at zoom 1, slow push factor across the beat
VIEWS = {
    "us_china": dict(lon=-160.0, lat=32.0, ppd=5.4, push=1.06),
    "pacific": dict(lon=-160.0, lat=30.0, ppd=5.0, push=1.08),
    "asia": dict(lon=113.0, lat=17.0, ppd=17.0, push=1.07),
    "sea": dict(lon=110.0, lat=3.0, ppd=30.0, push=1.08),
}

_cache = {}


def _load(name):
    if name not in _cache:
        sf = shapefile.Reader(os.path.join(GEO, name))
        shapes = []
        for rec, shp in zip(sf.records(), sf.shapes()):
            pts = np.array(shp.points, np.float64)
            parts = list(shp.parts) + [len(pts)]
            rings = [pts[parts[i]:parts[i + 1]] for i in range(len(parts) - 1)]
            shapes.append((rec.as_dict(), rings))
        _cache[name] = shapes
    return _cache[name]


def land():
    return [r for _, rings in _load("ne_50m_land") for r in rings]


def countries():
    return _load("ne_50m_admin_0_countries")


class Projection:
    """Mercator with a movable centre (wraps longitudes around the view centre, so the Pacific works)."""

    def __init__(self, lon, lat, ppd, zoom=1.0, cx=W / 2, cy=H / 2):
        self.lon0, self.lat0 = lon, lat
        self.s = ppd * zoom
        self.cx, self.cy = cx, cy
        self.y0 = self._merc(lat)

    @staticmethod
    def _merc(lat):
        lat = np.clip(lat, -84, 84)
        return np.degrees(np.log(np.tan(np.pi / 4 + np.radians(lat) / 2)))

    def __call__(self, lon, lat):
        dl = (np.asarray(lon) - self.lon0 + 540.0) % 360.0 - 180.0
        x = self.cx + dl * self.s
        y = self.cy - (self._merc(np.asarray(lat)) - self.y0) * self.s
        return x, y

    def ring(self, r):
        """Project a ring; split it where it jumps across the wrap seam."""
        x, y = self(r[:, 0], r[:, 1])
        jumps = np.nonzero(np.abs(np.diff(x)) > W * 0.5)[0]
        pieces, s0 = [], 0
        for j in jumps:
            pieces.append(np.stack([x[s0:j + 1], y[s0:j + 1]], 1)); s0 = j + 1
        pieces.append(np.stack([x[s0:], y[s0:]], 1))
        return [p for p in pieces if len(p) > 2]


def great_circle(a, b, n=90):
    """Points along the great circle from a to b (lon/lat degrees)."""
    def v(lon, lat):
        lo, la = math.radians(lon), math.radians(lat)
        return np.array([math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)])
    p, q = v(*a), v(*b)
    om = math.acos(max(-1.0, min(1.0, float(p @ q))))
    out = []
    for t in np.linspace(0, 1, n):
        if om < 1e-6:
            r = p
        else:
            r = (math.sin((1 - t) * om) * p + math.sin(t * om) * q) / math.sin(om)
        out.append((math.degrees(math.atan2(r[1], r[0])), math.degrees(math.asin(r[2]))))
    return out


def arc_screen(proj, a, b, lift=0.18, n=90):
    """Great circle in screen space, bowed upward a little so routes read as flight/shipping arcs."""
    pts = great_circle(a, b, n)
    xs, ys = proj(np.array([p[0] for p in pts]), np.array([p[1] for p in pts]))
    L = math.hypot(xs[-1] - xs[0], ys[-1] - ys[0])
    t = np.linspace(0, 1, n)
    ys = ys - np.sin(np.pi * t) * L * lift
    return list(zip(xs, ys))


def pacific_arc(proj, a, b, lift=0.10, n=90):
    """Shortest-longitude path in the projected plane (crosses the Pacific for US <-> China), gently bowed."""
    dl = (b[0] - a[0] + 540.0) % 360.0 - 180.0
    t = np.linspace(0, 1, n)
    lons = a[0] + dl * t; lats = a[1] + (b[1] - a[1]) * t
    xs, ys = proj(lons, lats)
    L = math.hypot(xs[-1] - xs[0], ys[-1] - ys[0])
    ys = ys - np.sin(np.pi * t) * L * lift
    return list(zip(xs, ys))
