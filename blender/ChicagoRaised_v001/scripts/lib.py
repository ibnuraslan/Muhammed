# Shared helpers for the Love Canal build scripts (exec'd).
import os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Euler, Quaternion
R_ = math.radians
FILM = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ASSETS = os.path.join(FILM, "assets_src")
PH = os.path.join(ASSETS, "ph")
sc = bpy.context.scene

def coll(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name); sc.collection.children.link(c)
    return c

def link(o, c):
    for u in list(o.users_collection): u.objects.unlink(o)
    c.objects.link(o)
    return o

def bbox(objs):
    pts = []
    for o in objs:
        if o.type != 'MESH': continue
        mw = o.matrix_world; co = [0.0] * (3 * len(o.data.vertices)); o.data.vertices.foreach_get("co", co)
        xs, ys, zs = co[0::3], co[1::3], co[2::3]
        for c in ((min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)), (min(xs), max(ys), min(zs)), (max(xs), min(ys), max(zs)),
                  (min(xs), min(ys), max(zs)), (max(xs), max(ys), min(zs)), (min(xs), max(ys), max(zs)), (max(xs), min(ys), min(zs))):
            pts.append(mw @ Vector(c))
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])

def import_glb(name, keep=None):
    """import a GLB from assets_src; returns {part: object}. Meshes are made single-user with transforms applied, empties removed."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ASSETS, name + ".glb"))
    new = [o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    meshes = [o for o in new if o.type == 'MESH' and len(o.data.polygons) > 0 and o.name != "Cube"]
    mws = {o.name: o.matrix_world.copy() for o in meshes}
    for o in meshes:
        o.parent = None
    for o in meshes:
        o.data = o.data.copy(); o.data.transform(mws[o.name]); o.matrix_world = Matrix.Identity(4)
    for o in new:
        if o not in meshes: bpy.data.objects.remove(o, do_unlink=True)
    return meshes

def join(objs, name):
    objs = [o for o in objs if o]
    if len(objs) == 1:
        objs[0].name = name; return objs[0]
    with bpy.context.temp_override(active_object=objs[0], selected_editable_objects=objs, selected_objects=objs):
        bpy.ops.object.join()
    objs[0].name = name
    return objs[0]

def normalize(objs, size, axis=2, ground=True, center=True):
    """scale the group so its extent along `axis` (0,1,2 or 'max') equals size; bottom at z=0, centred in x,y"""
    mn, mx = bbox(objs); ext = mx - mn
    k = size / (max(ext) if axis == 'max' else ext[axis])
    off = Vector(((mn.x + mx.x) / 2 if center else 0, (mn.y + mx.y) / 2 if center else 0, mn.z if ground else 0))
    M = Matrix.Scale(k, 4) @ Matrix.Translation(-off)
    for o in objs: o.data.transform(M)
    return k

def place(o, loc, rz=0.0, parent=None):
    o.location = Vector(loc); o.rotation_euler = (0, 0, R_(rz))
    if parent: o.parent = parent
    return o

def set_origin(o, p):
    """move the object origin to world point p without moving the mesh"""
    p = Vector(p); o.data.transform(Matrix.Translation(-(p - o.location))); o.location = p

def mat(name, rgb, rough=0.5, metal=0.0, emit=None, emit_s=0.0, alpha=1.0, spec=0.3):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    P = m.node_tree.nodes["Principled BSDF"]
    P.inputs["Base Color"].default_value = (*rgb, 1); P.inputs["Roughness"].default_value = rough; P.inputs["Metallic"].default_value = metal
    P.inputs["Specular IOR Level"].default_value = spec
    if emit:
        P.inputs["Emission Color"].default_value = (*emit, 1); P.inputs["Emission Strength"].default_value = emit_s
    if alpha < 1: P.inputs["Alpha"].default_value = alpha
    return m

def pbr(name, folder, scale=1.0, tint=None, bump=0.3, rough_min=0.4, coords="UV"):
    """Poly Haven texture set (diff / nor_gl / rough) with Object or UV coordinates and a scale."""
    m = bpy.data.materials.get(name)
    if m: return m
    d = os.path.join(PH, folder); d = os.path.join(d, "textures") if os.path.isdir(os.path.join(d, "textures")) else d; files = os.listdir(d)
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    P = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale)
    L.new(tc.outputs[coords], mp.inputs[0])
    def tex(key, nc=False):
        f = [x for x in files if key in x.lower()]
        if not f: return None
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(d, f[0]), check_existing=True)
        if coords != "UV": t.projection = 'BOX'; t.projection_blend = 0.3
        if nc: t.image.colorspace_settings.name = "Non-Color"
        L.new(mp.outputs[0], t.inputs[0]); return t
    c = tex("diff")
    if c:
        if tint:
            mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1
            L.new(c.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (*tint, 1); L.new(mx.outputs[2], P.inputs["Base Color"])
        else:
            L.new(c.outputs[0], P.inputs["Base Color"])
    r = tex("rough", True)
    if r:
        mr = N.new("ShaderNodeMapRange"); mr.inputs[3].default_value = rough_min; L.new(r.outputs[0], mr.inputs[0]); L.new(mr.outputs[0], P.inputs["Roughness"])
    n = tex("nor_gl", True)
    if n:
        nm = N.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = bump; L.new(n.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], P.inputs["Normal"])
    return m

def box(name, size, loc, m=None, c=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.active_object; o.name = name
    o.scale = size; bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = 2
    if m: o.data.materials.append(m)
    if c: link(o, c)
    return o

def plane(name, size, loc, m=None, c=None, subdiv=0):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc); o = bpy.context.active_object; o.name = name
    o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if subdiv:
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.subdivide(number_cuts=subdiv); bpy.ops.object.mode_set(mode='OBJECT')
    if m: o.data.materials.append(m)
    if c: link(o, c)
    return o

def cyl(name, r, h, loc, m=None, c=None, verts=32, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot); o = bpy.context.active_object; o.name = name
    bpy.ops.object.shade_smooth()
    if m: o.data.materials.append(m)
    if c: link(o, c)
    return o

def copy_obj(o, name, loc=None, rz=None, c=None, linked=True):
    n = o.copy()
    if not linked: n.data = o.data.copy()
    n.name = name
    (c or o.users_collection[0]).objects.link(n)
    if loc is not None: n.location = Vector(loc)
    if rz is not None: n.rotation_euler = (0, 0, R_(rz))
    n.hide_render = False; n.hide_viewport = False
    return n

def key_vis(o, states):
    """[(frame, visible)] -> constant keys on hide_render AND hide_viewport (hidden objects still block rays otherwise)"""
    for f, v in states:
        o.hide_render = not v; o.hide_viewport = not v
        o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)

def constant_all(o):
    ad = o.animation_data
    if not ad or not ad.action: return
    for fc in fcurves_of(ad.action):
        for k in fc.keyframe_points: k.interpolation = 'CONSTANT'

def fcurves_of(action):
    """Blender 5 layered actions: collect the f-curves of every channelbag"""
    out = []
    if hasattr(action, "fcurves") and len(getattr(action, "fcurves", [])):
        return list(action.fcurves)
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []):
                out.extend(cb.fcurves)
    return out

def smooth(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
