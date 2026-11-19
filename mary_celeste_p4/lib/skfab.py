"""Sketchfab models (CC-BY / CC0 only; no NC, ND or SA) with automatic credits.

    model(uid, height=None) -> (root empty, meshes): downloads the GLB once into assets/sketchfab/, imports it,
    optionally scales it to a real-world height (m), sits it on z=0 centred on the origin, and records the credit
    (title, author, licence, URL) in assets/sketchfab/credits.json. The API token is injected by the studio proxy.
"""
import os, json, urllib.request, zipfile, io
import bpy
from mathutils import Vector, Matrix

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "sketchfab")
API = "https://api.sketchfab.com/v3/models/"
OK = ("CC Attribution", "CC0 Public Domain")


def _json(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "doc-renderer/1.0"}), timeout=60))


def fetch(uid):
    os.makedirs(ROOT, exist_ok=True)
    glb = os.path.join(ROOT, uid + ".glb")
    cred = os.path.join(ROOT, "credits.json")
    credits = json.load(open(cred)) if os.path.exists(cred) else {}
    if uid not in credits:
        info = _json(API + uid)
        lic = info["license"]["label"]
        if lic not in OK:
            raise RuntimeError(f"{uid}: licence {lic} not allowed")
        credits[uid] = dict(title=info["name"], author=info["user"]["displayName"], user=info["user"]["username"],
                            license=lic, url=info["viewerUrl"])
        json.dump(credits, open(cred, "w"), indent=1)
    if not os.path.exists(glb):
        d = _json(API + uid + "/download")
        if "glb" in d:
            open(glb, "wb").write(urllib.request.urlopen(d["glb"]["url"], timeout=300).read())
        else:
            z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(d["gltf"]["url"], timeout=300).read()))
            z.extractall(os.path.join(ROOT, uid))
            glb = os.path.join(ROOT, uid, "scene.gltf")
    return glb


def model(uid, height=None, name=None):
    path = fetch(uid)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(name or f"skf_{uid[:8]}", None); bpy.context.scene.collection.objects.link(root)
    for o in new:
        if o.parent is None:
            o.parent = root
    bpy.context.view_layer.update()
    meshes = [o for o in new if o.type == 'MESH']
    lo = Vector((1e9, 1e9, 1e9)); hi = -lo
    for o in meshes:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    k = (height / (hi.z - lo.z)) if height else 1.0
    ctr = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for o in new:
        if o.parent is root:
            o.matrix_world = Matrix.Diagonal((k, k, k, 1)) @ Matrix.Translation(-ctr) @ o.matrix_world
    bpy.context.view_layer.update()
    root["dims"] = list((hi - lo) * k)
    return root, meshes


def credits_text():
    p = os.path.join(ROOT, "credits.json")
    if not os.path.exists(p):
        return ""
    c = json.load(open(p))
    return "\n".join(f"  \"{v['title']}\" by {v['author']} ({v['user']}), {v['license']}, {v['url']}" for v in c.values())
