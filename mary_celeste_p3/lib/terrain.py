"""Real elevation for the Strait of Gibraltar: Mapzen/Tilezen Terrarium tiles (AWS Open Data, see CREDITS.txt).

    hm, info = heightmap(lat0, lon0, lat1, lon1, zoom)      # metres, north up (row 0 = north)
    o = relief_mesh("rock", hm, info, origin=(lat, lon), scale=1.0, vex=1.0, res=400)

Coordinates: x east, y north, metres from `origin` times `scale`; z = elevation * vex * scale; sea level z = 0.
"""
import os, math, io, urllib.request
import numpy as np

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "terrain")
URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
R_EARTH = 6378137.0


def _tile_xy(lat, lon, z):
    n = 2 ** z
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return x, y


def _tile_latlon(x, y, z):
    n = 2 ** z
    lon = x / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lat, lon


def _get(z, x, y):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, f"{z}_{x}_{y}.png")
    if not os.path.exists(p):
        req = urllib.request.Request(URL.format(z=z, x=x, y=y), headers={"User-Agent": "seldom-film/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            open(p, "wb").write(r.read())
    try:
        from PIL import Image
        a = np.asarray(Image.open(p).convert("RGB"), np.float64)
    except ImportError:                       # inside Blender: decode with bpy (exact 8-bit values, no colour transform)
        import bpy
        img = bpy.data.images.load(p, check_existing=True); img.colorspace_settings.name = 'Non-Color'
        w, h = img.size; px = np.empty(w * h * img.channels, np.float32); img.pixels.foreach_get(px)
        a = np.round(px.reshape(h, w, img.channels)[::-1, :, :3] * 255.0).astype(np.float64)
        bpy.data.images.remove(img)
    return a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768


def heightmap(lat0, lon0, lat1, lon1, z):
    """Elevation grid (metres) covering the box; returns (hm, info) with info = dict(lat/lon of grid corners)."""
    xa, ya = _tile_xy(max(lat0, lat1), min(lon0, lon1), z)
    xb, yb = _tile_xy(min(lat0, lat1), max(lon0, lon1), z)
    tx0, ty0, tx1, ty1 = int(xa), int(ya), int(xb), int(yb)
    rows = []
    for ty in range(ty0, ty1 + 1):
        rows.append(np.concatenate([_get(z, tx, ty) for tx in range(tx0, tx1 + 1)], axis=1))
    big = np.concatenate(rows, axis=0)
    px0 = int((xa - tx0) * 256); py0 = int((ya - ty0) * 256)
    px1 = int((xb - tx0) * 256); py1 = int((yb - ty0) * 256)
    hm = big[py0:py1, px0:px1]
    la_n, lo_w = _tile_latlon(tx0 + px0 / 256, ty0 + py0 / 256, z)
    la_s, lo_e = _tile_latlon(tx0 + px1 / 256, ty0 + py1 / 256, z)
    return hm, dict(lat_n=la_n, lat_s=la_s, lon_w=lo_w, lon_e=lo_e)


def to_xy(lat, lon, origin):
    """Local metres (east, north) from origin (equirectangular, fine at these sizes)."""
    la0, lo0 = origin
    x = math.radians(lon - lo0) * R_EARTH * math.cos(math.radians(la0))
    y = math.radians(lat - la0) * R_EARTH
    return x, y


def relief_mesh(name, hm, info, origin, scale=1.0, vex=1.0, res=400, sea_floor=None, clip_low=None, mat=None, skirt=True):
    """Grid mesh of the heightmap (decimated to ~res cells on the long side)."""
    import bpy
    h, w = hm.shape
    step = max(1, int(max(h, w) / res))
    g = hm[::step, ::step].copy()
    if sea_floor is not None:
        g = np.where(g < 0, np.maximum(g, sea_floor), g)
    if clip_low is not None:
        g = np.where(g < 1.5, clip_low, g)           # sea and the wet foreshore sink under the water surface
    gh, gw = g.shape
    xw, yn = to_xy(info["lat_n"], info["lon_w"], origin)
    xe, ys = to_xy(info["lat_s"], info["lon_e"], origin)
    xs = np.linspace(xw, xe, gw) * scale; ys_ = np.linspace(yn, ys, gh) * scale
    X, Y = np.meshgrid(xs, ys_)
    Z = g * vex * scale
    verts = np.stack([X, Y, Z], -1).reshape(-1, 3)
    idx = np.arange(gh * gw).reshape(gh, gw)
    faces = np.stack([idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:], idx[:-1, :-1]], -1).reshape(-1, 4)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts.tolist(), [], faces.tolist()); me.update()
    me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
    uv = me.uv_layers.new(name="UVMap")
    U = np.stack([(X - X.min()) / max(1e-9, X.max() - X.min()), 1 - (Y.max() - Y) / max(1e-9, Y.max() - Y.min())], -1).reshape(-1, 2)
    loops = np.empty(len(me.loops), np.int64); me.loops.foreach_get("vertex_index", loops)
    uv.data.foreach_set("uv", U[loops].ravel())
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    if mat:
        me.materials.append(mat)
    o["elev_min"] = float(g.min()); o["elev_max"] = float(g.max())
    return o
