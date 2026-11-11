"""Poly Haven (CC0) assets: download on first use into assets/polyhaven/ (git-ignored), then import.

  model(id)            -> list of imported objects (glTF, 2k textures), parented to an empty returned first
  hdri(id, res="4k")   -> path to the .hdr
  texture(id, ...)     -> a Principled material from the PBR maps (diffuse / normal / rough / arm)
"""
import os, json, urllib.request
import bpy

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "polyhaven")
API = "https://api.polyhaven.com/files/"
UA = {"User-Agent": "doc-renderer/1.0"}


def _get(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r, open(path + ".part", "wb") as f:
        f.write(r.read())
    os.replace(path + ".part", path)
    return path


def _files(aid):
    p = os.path.join(ROOT, aid, "files.json")
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with urllib.request.urlopen(urllib.request.Request(API + aid, headers=UA), timeout=60) as r:
            open(p, "wb").write(r.read())
    return json.load(open(p))


def fetch_model(aid, res="2k"):
    g = _files(aid)["gltf"][res]["gltf"]
    d = os.path.join(ROOT, aid)
    for rel, info in g.get("include", {}).items():
        _get(info["url"], os.path.join(d, rel))
    return _get(g["url"], os.path.join(d, os.path.basename(g["url"])))


def model(aid, loc=(0, 0, 0), rot_z=0.0, scale=1.0, res="2k"):
    """Import a model; returns the parent empty (move/rotate/scale it) and its mesh children."""
    path = fetch_model(aid, res)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(aid, None); bpy.context.collection.objects.link(root)
    for o in new:
        if o.parent is None:
            o.parent = root
    root.location = loc; root.rotation_euler = (0, 0, rot_z); root.scale = (scale, scale, scale)
    bpy.context.view_layer.update()
    return root, [o for o in new if o.type == 'MESH']


def bounds(meshes):
    from mathutils import Vector
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def hdri(aid, res="4k"):
    info = _files(aid)["hdri"][res]["hdr"]
    return _get(info["url"], os.path.join(ROOT, aid, os.path.basename(info["url"])))


def world_hdri(aid, strength=1.0, rot_z=0.0, res="4k"):
    w = bpy.data.worlds.new("World"); bpy.context.scene.world = w; w.use_nodes = True
    N = w.node_tree.nodes; L = w.node_tree.links; N.clear()
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs['Rotation'].default_value = (0, 0, rot_z)
    env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(hdri(aid, res))
    bg = N.new("ShaderNodeBackground"); bg.inputs['Strength'].default_value = strength
    out = N.new("ShaderNodeOutputWorld")
    L.new(tc.outputs['Generated'], mp.inputs['Vector']); L.new(mp.outputs[0], env.inputs['Vector'])
    L.new(env.outputs['Color'], bg.inputs['Color']); L.new(bg.outputs[0], out.inputs['Surface'])
    return w, bg, mp


def texture(aid, scale=1.0, res="2k", name=None, tint=None):
    f = _files(aid)
    d = os.path.join(ROOT, aid)
    def grab(key):
        if key not in f or res not in f[key]:
            return None
        info = f[key][res].get("jpg") or f[key][res].get("png")
        return _get(info["url"], os.path.join(d, os.path.basename(info["url"]))) if info else None
    diff, nor, rough, arm = grab("Diffuse"), grab("nor_gl"), grab("Rough"), grab("arm")
    m = bpy.data.materials.new(name or aid); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (scale, scale, scale)
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    def img(path, color=False):
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
        t.image.colorspace_settings.name = 'sRGB' if color else 'Non-Color'; t.projection = 'BOX'; t.projection_blend = 0.2
        L.new(mp.outputs[0], t.inputs['Vector']); return t
    if diff:
        t = img(diff, True)
        if tint:
            mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
            L.new(t.outputs['Color'], mx.inputs[6]); mx.inputs[7].default_value = (*tint, 1); L.new(mx.outputs[2], p.inputs['Base Color'])
        else:
            L.new(t.outputs['Color'], p.inputs['Base Color'])
    if rough:
        L.new(img(rough).outputs['Color'], p.inputs['Roughness'])
    elif arm:
        sep = N.new("ShaderNodeSeparateColor"); L.new(img(arm).outputs['Color'], sep.inputs[0])
        L.new(sep.outputs[1], p.inputs['Roughness']); L.new(sep.outputs[2], p.inputs['Metallic'])
    if nor:
        nm = N.new("ShaderNodeNormalMap"); L.new(img(nor).outputs['Color'], nm.inputs['Color']); L.new(nm.outputs[0], p.inputs['Normal'])
    return m
