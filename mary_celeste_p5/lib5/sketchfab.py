"""Sketchfab (CC-BY / CC0) models: download on first use into mary_celeste_p5/assets/sketchfab/<uid>/ (git-ignored),
import the glTF, record the credit line in assets/sketchfab/credits.json (CREDITS.txt is built from it).
The studio proxy injects the API token for api.sketchfab.com.

    root, meshes = model(uid, size=0.3, axis=2, at=(x, y, z), rot_z=0)
"""
import os, json, zipfile, urllib.request
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "assets", "sketchfab")
API = "https://api.sketchfab.com/v3/models/"
UA = {"User-Agent": "doc-renderer/1.0"}
OK_LICENCES = ("CC Attribution", "CC0 Public Domain", "Free Standard")


def _json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def fetch(uid):
    d = os.path.join(ROOT, uid); os.makedirs(d, exist_ok=True)
    meta_p = os.path.join(d, "meta.json")
    if not os.path.exists(meta_p):
        m = _json(API + uid)
        meta = dict(uid=uid, name=m["name"], author=m["user"]["displayName"] or m["user"]["username"],
                    url=m["viewerUrl"], license=(m.get("license") or {}).get("label", ""))
        if not meta["license"].startswith(OK_LICENCES):
            raise RuntimeError(f"licence not allowed for {uid}: {meta['license']}")
        json.dump(meta, open(meta_p, "w"), indent=1)
    meta = json.load(open(meta_p))
    gl = [os.path.join(dp, f) for dp, _, fs in os.walk(d) for f in fs if f.endswith((".gltf", ".glb"))]
    if not gl:
        dl = _json(API + uid + "/download")
        url = (dl.get("gltf") or dl.get("glb"))["url"]
        z = os.path.join(d, "model.zip")
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=600) as r, open(z, "wb") as f:
            f.write(r.read())
        if zipfile.is_zipfile(z):
            zipfile.ZipFile(z).extractall(d)
        else:
            os.replace(z, os.path.join(d, "model.glb"))
        gl = [os.path.join(dp, f) for dp, _, fs in os.walk(d) for f in fs if f.endswith((".gltf", ".glb"))]
    _credit(meta)
    return gl[0], meta


def _credit(meta):
    p = os.path.join(ROOT, "credits.json")
    c = json.load(open(p)) if os.path.exists(p) else {}
    c[meta["uid"]] = meta
    json.dump(c, open(p, "w"), indent=1)


def bounds(ms):
    bpy.context.view_layer.update()
    lo = Vector((1e9,) * 3); hi = -lo
    for o in ms:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    return lo, hi


def model(uid, at=(0, 0, 0), rot_z=0.0, size=None, axis=2, rot=None):
    """Import, scale so the extent along `axis` is `size`, stand its lowest point on at.z, centred on at.xy."""
    path, meta = fetch(uid)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new("sf_" + uid[:8], None); bpy.context.collection.objects.link(root)
    for o in new:
        if o.parent is None:
            o.parent = root
    ms = [o for o in new if o.type == 'MESH']
    if rot is not None:
        root.rotation_euler = rot
    bpy.context.view_layer.update()
    lo, hi = bounds(ms)
    s = 1.0 if size is None else size / max(1e-6, (hi - lo)[axis])
    root.scale = (s, s, s)
    e = root.rotation_euler.copy(); e.z += rot_z; root.rotation_euler = e
    bpy.context.view_layer.update()
    lo, hi = bounds(ms); c = (lo + hi) / 2
    root.location += Vector((at[0] - c.x, at[1] - c.y, at[2] - lo.z))
    bpy.context.view_layer.update()
    return root, ms
