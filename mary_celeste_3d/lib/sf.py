"""Sketchfab (CC-BY / CC0 only) assets: download on first use into assets/sketchfab/ (git-ignored) and import.
Needs the studio environment's Sketchfab token (the network proxy injects it for api.sketchfab.com).

    path = sf.fetch(uid)              # -> .glb path (records name/author/licence next to it)
    root, meshes = sf.model(uid, loc, rot_z, height=None)   # import; optional uniform scale to a height in metres
    sf.CATALOG                        # vetted assets with credits (keep README CREDITS in sync)
"""
import os, json, urllib.request
import bpy
from mathutils import Vector

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "sketchfab")
API = "https://api.sketchfab.com/v3/models/"

CATALOG = {
    "leather_boots": ("988f94a8fc6945749e2b2ffdcce05e98", "Leather boots", "kifir", "CC-BY 4.0"),
    "sextant": ("39a7bf5a9da94c2c9ca2d9a34d71435f", "Vintage Sextant", "see .json", "CC-BY 4.0"),
    "sextant_aged": ("a572c2af465f4ffb850d3aac0e05054f", "Aged sextant", "see .json", "CC-BY 4.0"),
}


def fetch(uid):
    os.makedirs(ROOT, exist_ok=True)
    path = os.path.join(ROOT, uid + ".glb")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    d = json.load(urllib.request.urlopen(API + uid + "/download", timeout=60))
    k = "glb" if "glb" in d else "gltf"
    urllib.request.urlretrieve(d[k]["url"], path + ".part"); os.replace(path + ".part", path)
    m = json.load(urllib.request.urlopen(API + uid, timeout=60))
    lic = m["license"]["label"]
    if "NonCommercial" in lic or "NoDerivs" in lic:
        raise RuntimeError(f"{uid}: licence {lic} not allowed")
    json.dump({"name": m["name"], "author": m["user"]["username"], "license": lic, "url": m["viewerUrl"]},
              open(os.path.join(ROOT, uid + ".json"), "w"))
    return path


def model(uid, loc=(0, 0, 0), rot_z=0.0, height=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=fetch(uid))
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new("sf_" + uid[:8], None); bpy.context.collection.objects.link(root)
    for o in new:
        if o.parent is None:
            o.parent = root
    bpy.context.view_layer.update()
    ms = [o for o in new if o.type == 'MESH']
    if height:
        pts = [o.matrix_world @ Vector(c) for o in ms for c in o.bound_box]
        hz = max(p.z for p in pts) - min(p.z for p in pts); s = height / max(hz, 1e-6)
        root.scale = (s, s, s)
    root.location = loc; root.rotation_euler = (0, 0, rot_z)
    bpy.context.view_layer.update()
    return root, ms
