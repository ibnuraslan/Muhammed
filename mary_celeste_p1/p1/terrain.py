"""Copied unchanged from branch claude/mary-celeste-p4, mary_celeste_p4/lib/terrain.py (P4 chart-table look, reused across the film)."""
"""Real terrain and bathymetry from the public AWS Terrain Tiles (Mapzen 'terrarium' encoding:
elevation = R*256 + G + B/256 - 32768 metres; sources SRTM, GMTED, ETOPO1/GEBCO; open data, see CREDITS.txt).

    grid(lon0, lat0, lon1, lat1, zoom) -> (elev[H, W] metres, lon[W], lat[H])
    relief_mesh(name, elev, size_x, size_y, land_k, sea_k, mat) -> a mesh of the grid (a real 3D table map)
    lonlat_to_map(lon, lat, bbox, size) -> map-local (x, y)
"""
import os, math, io, urllib.request
import numpy as np
import bpy

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "terrain")
URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"


def _tile(z, x, y):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, f"{z}_{x}_{y}.png")
    if not os.path.exists(p):
        req = urllib.request.Request(URL.format(z=z, x=x, y=y), headers={"User-Agent": "doc-renderer/1.0"})
        open(p, "wb").write(urllib.request.urlopen(req, timeout=60).read())
    im = bpy.data.images.load(p, check_existing=True); im.colorspace_settings.name = 'Non-Color'
    w, h = im.size; px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px)
    a = np.round(px.reshape(h, w, 4)[::-1, :, :3].astype(np.float64) * 255.0)
    bpy.data.images.remove(im)
    return a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768


def _xy(lon, lat, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def grid(lon0, lat0, lon1, lat1, zoom, out_w=None):
    x0, y1 = _xy(lon0, lat0, zoom); x1, y0 = _xy(lon1, lat1, zoom)
    tx0, tx1, ty0, ty1 = int(x0), int(x1), int(y0), int(y1)
    rows = []
    for ty in range(ty0, ty1 + 1):
        rows.append(np.concatenate([_tile(zoom, tx, ty) for tx in range(tx0, tx1 + 1)], axis=1))
    big = np.concatenate(rows, axis=0)
    # crop to the bbox (pixel coords in the mosaic), then resample on a regular lon/lat grid
    W = out_w or int((x1 - x0) * 256)
    lat_span = lat1 - lat0; lon_span = lon1 - lon0
    Hh = max(2, int(round(W * lat_span / (lon_span * math.cos(math.radians((lat0 + lat1) / 2))))))
    lons = np.linspace(lon0, lon1, W); lats = np.linspace(lat1, lat0, Hh)
    px = np.array([(_xy(l, lat0, zoom)[0] - tx0) * 256 for l in lons])
    py = np.array([(_xy(lon0, la, zoom)[1] - ty0) * 256 for la in lats])
    px = np.clip(px, 0, big.shape[1] - 1.001); py = np.clip(py, 0, big.shape[0] - 1.001)
    ix = px.astype(int); iy = py.astype(int); fx = px - ix; fy = py - iy
    a = big[np.ix_(iy, ix)]; b = big[np.ix_(iy, ix + 1)]; c = big[np.ix_(iy + 1, ix)]; d = big[np.ix_(iy + 1, ix + 1)]
    fx = fx[None, :]; fy = fy[:, None]
    e = a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy
    return e, lons, lats


def relief_mesh(name, elev, size_x, size_y, land_k, sea_k, mat=None, z0=0.0, skirt=0.0):
    """Grid mesh: x across (west->east), y up the map (south->north). Land heights scaled by land_k (m -> map units),
    sea depths by sea_k. Vertex attribute 'elev' (metres) drives the colour ramp. skirt>0 adds side walls down to -skirt."""
    Hh, W = elev.shape
    xs = np.linspace(-size_x / 2, size_x / 2, W); ys = np.linspace(size_y / 2, -size_y / 2, Hh)
    X, Y = np.meshgrid(xs, ys)
    Z = np.where(elev > 0, elev * land_k, elev * sea_k) + z0
    V = np.stack([X, Y, Z], -1).reshape(-1, 3)
    idx = np.arange(Hh * W).reshape(Hh, W)
    F = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]], -1).reshape(-1, 4)
    me = bpy.data.meshes.new(name)
    verts = V.tolist(); faces = F.tolist()
    if skirt:
        base = len(verts)
        ring = list(idx[0, :]) + list(idx[:, -1][1:]) + list(idx[-1, ::-1][1:]) + list(idx[::-1, 0][1:-1])
        for k in ring:
            v = V[k]; verts.append([v[0], v[1], -skirt])
        n = len(ring)
        for i in range(n):
            a, b = ring[i], ring[(i + 1) % n]
            faces.append([a, b, base + (i + 1) % n, base + i])
    me.from_pydata(verts, [], faces); me.update()
    me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
    at = me.attributes.new("elev", 'FLOAT', 'POINT')
    ev = np.concatenate([elev.reshape(-1), np.full(len(verts) - Hh * W, -6000.0)])
    at.data.foreach_set("value", ev.astype(np.float32))
    uv = me.uv_layers.new(name="UVMap")
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    if mat:
        me.materials.append(mat)
    return o


def lonlat_to_map(lon, lat, bbox, size):
    lon0, lat0, lon1, lat1 = bbox
    return ((lon - lon0) / (lon1 - lon0) - 0.5) * size[0], ((lat - lat0) / (lat1 - lat0) - 0.5) * size[1]


def height_at(elev, lons, lats, lon, lat):
    i = int(np.clip(np.searchsorted(-lats, -lat), 0, len(lats) - 1)); j = int(np.clip(np.searchsorted(lons, lon), 0, len(lons) - 1))
    return float(elev[i, j])


def map_material(name="tablemap"):
    """Antique painted relief: deep ocean ink blue-green, shelves lighter, coast cream, land ochre to umber,
    a fine paper/plaster texture and a satin varnish."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    a = N.new("ShaderNodeAttribute"); a.attribute_name = "elev"
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = -5500; mr.inputs['From Max'].default_value = 2400
    L.new(a.outputs['Fac'], mr.inputs['Value'])
    cr = N.new("ShaderNodeValToRGB"); e = cr.color_ramp
    stops = [(0.0, (0.008, 0.02, 0.04)), (0.45, (0.015, 0.045, 0.075)), (0.66, (0.04, 0.11, 0.13)), (0.694, (0.16, 0.30, 0.30)),
             (0.6965, (0.62, 0.52, 0.34)), (0.70, (0.50, 0.42, 0.22)), (0.76, (0.33, 0.30, 0.13)), (0.86, (0.36, 0.22, 0.10)), (1.0, (0.55, 0.45, 0.36))]
    e.elements[0].position, e.elements[0].color = stops[0][0], (*stops[0][1], 1)
    e.elements[1].position, e.elements[1].color = stops[-1][0], (*stops[-1][1], 1)
    for pos, c in stops[1:-1]:
        el = e.elements.new(pos); el.color = (*c, 1)
    L.new(mr.outputs[0], cr.inputs['Fac'])
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 60; nz.inputs['Detail'].default_value = 10
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'OVERLAY'; mx.inputs['Factor'].default_value = 0.25
    L.new(cr.outputs['Color'], mx.inputs[6]); L.new(nz.outputs['Color'], mx.inputs[7])
    L.new(mx.outputs[2], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.42
    p.inputs['Coat Weight'].default_value = 0.25; p.inputs['Coat Roughness'].default_value = 0.25
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.08; L.new(nz.outputs['Fac'], b.inputs['Height'])
    L.new(b.outputs['Normal'], p.inputs['Normal'])
    return m
