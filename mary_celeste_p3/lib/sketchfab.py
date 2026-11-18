"""CC-BY / CC0 props from Sketchfab (the studio's API token is injected by the network proxy for api.sketchfab.com).

    objs = model("eff849bb58864ce19987fe9b7b5e28cc", size=0.36, axis="z")   # fitted: longest side (or `axis`) = size
Downloads the glTF once into assets/sketchfab/<uid>/, records the credit in assets/sketchfab/credits.json, imports,
joins into one object with its origin at the bottom centre, and scales it to a real size."""
import os, json, zipfile, io, urllib.request
try:
    import bpy
except ImportError:
    bpy = None
try:
    from mathutils import Vector, Matrix
except ImportError:
    pass

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "sketchfab")
API = "https://api.sketchfab.com/v3/models/"

PROPS = {   # uid, real size (m) along `axis`, axis
    "diving_helmet": ("eff849bb58864ce19987fe9b7b5e28cc", 0.46, "z"),
    "oil_lamp": ("c932f6165fef40029c3f18afe19b9934", 0.42, "z"),
    "inkwell_quill": ("64812fa9b17248e0aacb1800a278972b", 0.24, "z"),
    "row_boat": ("3e9093b6f0ce474da4d8cfea7e01f420", 5.4, "x"),
}


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "seldom-film/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def fetch(uid):
    d = os.path.join(ROOT, uid)
    if os.path.exists(os.path.join(d, "scene.gltf")) or any(f.endswith(".glb") for f in (os.listdir(d) if os.path.isdir(d) else [])):
        return d
    os.makedirs(d, exist_ok=True)
    meta = json.loads(_get(API + uid))
    dl = json.loads(_get(API + uid + "/download"))
    url = (dl.get("gltf") or dl.get("glb"))["url"]
    data = _get(url)
    if data[:2] == b"PK":
        zipfile.ZipFile(io.BytesIO(data)).extractall(d)
    else:
        open(os.path.join(d, "model.glb"), "wb").write(data)
    cr_path = os.path.join(ROOT, "credits.json")
    cr = json.load(open(cr_path)) if os.path.exists(cr_path) else {}
    cr[uid] = dict(name=meta.get("name"), author=meta.get("user", {}).get("displayName"),
                   author_url=meta.get("user", {}).get("profileUrl"), license=(meta.get("license") or {}).get("label"),
                   url=meta.get("viewerUrl"))
    json.dump(cr, open(cr_path, "w"), indent=1)
    return d


def model(key, size=None, axis="auto", name=None):
    """Import a prop, joined, origin at bottom centre, scaled to `size` (m) along `axis` (None/'auto' = longest)."""
    uid, sz, ax = PROPS[key] if key in PROPS else (key, size or 1.0, None)
    size = size or sz; axis = ax if axis == "auto" else axis
    d = fetch(uid)
    f = os.path.join(d, "scene.gltf") if os.path.exists(os.path.join(d, "scene.gltf")) else \
        next(os.path.join(d, x) for x in os.listdir(d) if x.endswith(".glb"))
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=f)
    new = [o for o in bpy.data.objects if o not in before]
    new_names = [o.name for o in new]
    meshes = [o for o in new if o.type == 'MESH']
    bpy.context.view_layer.update()
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    for nm in new_names:
        o = bpy.data.objects.get(nm)
        if o is not None and o != ob:
            bpy.data.objects.remove(o)
    ob.name = name or key
    co = [v.co for v in ob.data.vertices]
    mn = Vector((min(c.x for c in co), min(c.y for c in co), min(c.z for c in co)))
    mx = Vector((max(c.x for c in co), max(c.y for c in co), max(c.z for c in co)))
    dim = mx - mn
    s = size / (dim["xyz".index(axis)] if axis else max(dim))
    ob.data.transform(Matrix.Diagonal((s, s, s, 1)) @ Matrix.Translation(-Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))))
    ob.matrix_world = Matrix.Identity(4)
    ob["dims"] = list(dim * s)
    return ob
