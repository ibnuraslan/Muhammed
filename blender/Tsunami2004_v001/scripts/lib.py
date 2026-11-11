# Shared helpers for Tsunami2004 (exec'd by the build scripts).
import math, os, random
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix, Euler

ROOT = os.path.abspath(os.path.join(os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd()))
HERE = "/home/user/Muhammed/blender/Tsunami2004_v001"
ASSETS = HERE + "/assets"
FPS = 60
def F(t): return 1 + round(t * FPS)
def sstep(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

# ------------------------------------------------------------------ terrain height (also used by animation for foot plants)
SEA_EDGE = 425.0   # start of the drop-off to deep water
def _n(x, y):
    return (math.sin(x * 0.071 + y * 0.013) * 0.5 + math.sin(x * 0.023 - y * 0.041 + 1.3) * 0.5)
ROADS_X = [-62, -24, 34, 80]; ROADS_Y = [-24, -72, -134, -196, -258]
def terrain_h(x, y):
    if y < -45:      # town
        if any(abs(x - rx) < 4.5 for rx in ROADS_X) or any(abs(y - ry) < 4.5 for ry in ROADS_Y):
            return 0.55
        z = 0.6 + 0.12 * _n(x, y) + 0.06 * math.sin(x * 0.31) * math.sin(y * 0.27)
    elif y < -20:    # road / hotel apron (flat)
        z = 0.6
    elif y < 0:      # dry sand berm
        z = 0.6 - 0.3 * ((y + 20) / 20) ** 1.5 + 0.05 * _n(x * 3, y * 3)
    elif y < 25:     # wet sand
        z = 0.3 - 0.6 * (y / 25)
    elif y < SEA_EDGE:   # shallow seabed shelf
        u = (y - 25) / (SEA_EDGE - 25)
        z = -0.3 - 4.2 * u + 0.25 * _n(x * 0.7, y * 0.7) * min(1, u * 4) + 0.04 * math.sin(y * 2.1 + 0.3 * math.sin(x * 0.4))
    elif y < SEA_EDGE + 15:
        u = (y - SEA_EDGE) / 15
        z = -4.5 - 75.5 * sstep(u)
    else:
        z = -80.0
    return z

# ------------------------------------------------------------------ timeline (seconds)
def sea_level(t):
    return -4.6 * sstep(t / 4.5)

# ------------------------------------------------------------------ objects / materials
def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name); (parent or bpy.context.scene.collection).children.link(c)
    return c
def link(ob, c):
    for cc in ob.users_collection: cc.objects.unlink(ob)
    c.objects.link(ob); return ob
def mesh_obj(name, verts, faces, c, mats=()):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    ob = bpy.data.objects.new(name, me); c.objects.link(ob)
    for m in mats: me.materials.append(m)
    return ob
def box(name, c, size, loc, mat=None, rot=(0, 0, 0), bevel=0.0):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); c.objects.link(ob); ob.location = loc; ob.rotation_euler = rot
    if mat: me.materials.append(mat)
    if bevel:
        b = ob.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = 2
    return ob

def node_mat(name):
    m = bpy.data.materials.get(name)
    if m: return m, None
    m = bpy.data.materials.new(name); m.use_nodes = True
    return m, m.node_tree

def simple_mat(name, color, rough=0.6, metal=0.0, emit=None, alpha=1.0, trans=0.0):
    m, nt = node_mat(name)
    if nt is None: return m
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if trans: b.inputs["Transmission Weight"].default_value = trans
    if emit:
        b.inputs["Emission Color"].default_value = (*emit[0], 1); b.inputs["Emission Strength"].default_value = emit[1]
    if alpha < 1: b.inputs["Alpha"].default_value = alpha
    return m

def tex_files(tid):
    d = os.path.join(ASSETS, tid, "textures")
    fs = os.listdir(d)
    pick = lambda k: next((os.path.join(d, f) for f in fs if k in f), None)
    return pick("_diff_"), pick("_nor_gl_"), pick("_rough_")

def load_img(p, non_color=False):
    im = bpy.data.images.load(p, check_existing=True)
    if non_color: im.colorspace_settings.name = "Non-Color"
    return im

def pbr_nodes(nt, tid, scale, tint=None, coord=None, x=-900, y=0):
    """returns (color_socket, normal_socket, rough_socket) for a Poly Haven texture set"""
    N, L = nt.nodes, nt.links
    if coord is None:
        tc = N.new("ShaderNodeTexCoord"); tc.location = (x - 400, y); coord = tc.outputs["Object"]
    mp = N.new("ShaderNodeMapping"); mp.location = (x - 200, y); mp.inputs["Scale"].default_value = (1 / scale, 1 / scale, 1 / scale)
    L.new(coord, mp.inputs["Vector"])
    d, n, r = tex_files(tid)
    out = []
    ti = N.new("ShaderNodeTexImage"); ti.image = load_img(d); ti.location = (x, y); ti.projection = 'BOX'; ti.projection_blend = 0.2
    L.new(mp.outputs["Vector"], ti.inputs["Vector"]); col = ti.outputs["Color"]
    if tint:
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs["Factor"].default_value = 1
        mx.inputs["B"].default_value = (*tint, 1); L.new(col, mx.inputs["A"]); col = mx.outputs["Result"]; mx.location = (x + 250, y)
    tn = N.new("ShaderNodeTexImage"); tn.image = load_img(n, True); tn.location = (x, y - 280); tn.projection = 'BOX'; tn.projection_blend = 0.2
    L.new(mp.outputs["Vector"], tn.inputs["Vector"])
    nm = N.new("ShaderNodeNormalMap"); nm.location = (x + 250, y - 280); L.new(tn.outputs["Color"], nm.inputs["Color"])
    rs = None
    if r:
        tr = N.new("ShaderNodeTexImage"); tr.image = load_img(r, True); tr.location = (x, y - 560); tr.projection = 'BOX'; tr.projection_blend = 0.2
        L.new(mp.outputs["Vector"], tr.inputs["Vector"]); rs = tr.outputs["Color"]
    return col, nm.outputs["Normal"], rs

def pbr_mat(name, tid, scale, tint=None, rough_mul=1.0):
    m, nt = node_mat(name)
    if nt is None: return m
    b = nt.nodes["Principled BSDF"]
    c, n, r = pbr_nodes(nt, tid, scale, tint)
    nt.links.new(c, b.inputs["Base Color"]); nt.links.new(n, b.inputs["Normal"])
    if r:
        if rough_mul != 1.0:
            mm = nt.nodes.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = rough_mul
            nt.links.new(r, mm.inputs[0]); r = mm.outputs[0]
        nt.links.new(r, b.inputs["Roughness"])
    return m

def import_glb(name, target, axis="z", c=None, keep_origin=False):
    """import a GLB, join all meshes, scale so its size along `axis` (x,y,z or 'max') == target, origin bottom-centre"""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ASSETS, "models", name + ".glb"))
    new = [o for o in bpy.data.objects if o not in before]
    ms = [o for o in new if o.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in ms:
        o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]
    for o in ms:   # make single-user before applying transforms (instanced meshes in some GLBs)
        o.data = o.data.copy()
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(ms) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    keep = ob.name
    names = []
    for o in new:
        try: names.append(o.name)
        except ReferenceError: pass
    for nm in names:
        if nm != keep and nm in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
    vs = np.zeros(len(ob.data.vertices) * 3); ob.data.vertices.foreach_get("co", vs); vs = vs.reshape(-1, 3)
    lo, hi = vs.min(0), vs.max(0); size = hi - lo
    s = target / (size.max() if axis == "max" else size["xyz".index(axis)])
    cen = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])
    vs = (vs - cen) * s; ob.data.vertices.foreach_set("co", vs.ravel()); ob.data.update()
    ob.name = ob.data.name = "LIB_" + name
    if c: link(ob, c)
    for p in ob.data.polygons: p.use_smooth = True
    return ob

def inst(lib, name, c, loc, rot=(0, 0, 0), scale=1.0):
    ob = bpy.data.objects.new(name, lib.data); c.objects.link(ob)
    ob.location = loc; ob.rotation_euler = rot; ob.scale = (scale,) * 3 if isinstance(scale, (int, float)) else scale
    return ob

def key_tr(ob, f, loc=None, rot=None, scale=None):
    if loc is not None: ob.location = loc; ob.keyframe_insert("location", frame=f)
    if rot is not None: ob.rotation_euler = rot; ob.keyframe_insert("rotation_euler", frame=f)
    if scale is not None:
        ob.scale = (scale,) * 3 if isinstance(scale, (int, float)) else scale; ob.keyframe_insert("scale", frame=f)

def key_hide(ob, frames_states):
    for f, h in frames_states:
        ob.hide_render = h; ob.keyframe_insert("hide_render", frame=f)
        ob.hide_viewport = h; ob.keyframe_insert("hide_viewport", frame=f)

def set_interp(ob, kind='BEZIER'):
    ad = ob.animation_data
    if ad and ad.action:
        for fc in _fcurves(ad.action):
            for k in fc.keyframe_points: k.interpolation = kind

def _fcurves(action):
    try:
        return list(action.fcurves)
    except AttributeError:   # layered actions (Blender 4.4+)
        out = []
        for l in action.layers:
            for s in l.strips:
                for cb in s.channelbags: out += list(cb.fcurves)
        return out
