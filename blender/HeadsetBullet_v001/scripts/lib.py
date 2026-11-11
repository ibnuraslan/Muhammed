# Shared helpers for HeadsetBullet (exec'd by the build scripts).
import math, os, random
import bpy, bmesh
from mathutils import Vector, Matrix, Euler

R_ = math.radians
sc = bpy.context.scene
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")

def coll(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name); sc.collection.children.link(c)
    return c

def link(o, c="Set"):
    for cc in o.users_collection: cc.objects.unlink(o)
    coll(c).objects.link(o); return o

def img(path, non_color=False):
    i = bpy.data.images.load(path, check_existing=True)
    if non_color: i.colorspace_settings.name = "Non-Color"
    return i

def tex_paths(aid):
    d = os.path.join(ASSETS, aid, "textures")
    if not os.path.isdir(d): d = os.path.join(ASSETS, aid)
    fs = os.listdir(d); g = lambda k: next((os.path.join(d, f) for f in fs if "_" + k + "_" in f), None)
    return g("diff"), g("nor_gl"), g("rough")

def pbr(name, aid, scale=1.0, tint=None, rough_mul=1.0, box=False, normal=1.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links
    bs = N["Principled BSDF"]
    diff, nor, rough = tex_paths(aid)
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale)
    L.new(tc.outputs["Object" if box else "UV"], mp.inputs[0])
    def T(p, nc):
        t = N.new("ShaderNodeTexImage"); t.image = img(p, nc); L.new(mp.outputs[0], t.inputs[0])
        if box: t.projection = 'BOX'; t.projection_blend = 0.2
        return t
    if diff:
        t = T(diff, False)
        if tint:
            mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
            L.new(t.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (*tint, 1); L.new(mx.outputs[2], bs.inputs["Base Color"])
        else:
            L.new(t.outputs[0], bs.inputs["Base Color"])
    if rough:
        t = T(rough, True); mth = N.new("ShaderNodeMath"); mth.operation = 'MULTIPLY'; mth.inputs[1].default_value = rough_mul
        L.new(t.outputs[0], mth.inputs[0]); L.new(mth.outputs[0], bs.inputs["Roughness"])
    if nor:
        t = T(nor, True); nm = N.new("ShaderNodeNormalMap"); nm.inputs[0].default_value = normal
        L.new(t.outputs[0], nm.inputs[1]); L.new(nm.outputs[0], bs.inputs["Normal"])
    return m

def mat(name, col, rough=0.5, metal=0.0, emit=None, estr=0.0, alpha=1.0, trans=0.0, ior=1.45, coat=0.0, sss=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    b.inputs["Transmission Weight"].default_value = trans; b.inputs["IOR"].default_value = ior
    b.inputs["Coat Weight"].default_value = coat
    if sss: b.inputs["Subsurface Weight"].default_value = sss
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = estr
    m.diffuse_color = (*col, 1)
    return m

def box(name, size, loc, m=None, c="Set", bevel=0.0, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.location = loc; o.rotation_euler = rot
    link(o, c)
    if m: me.materials.append(m)
    if bevel:
        bv = o.modifiers.new("bev", 'BEVEL'); bv.width = bevel; bv.segments = 2; bv.limit_method = 'ANGLE'
    return o

def cyl(name, r, h, loc, m=None, c="Set", seg=32, rot=(0, 0, 0), r2=None):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.location = loc; o.rotation_euler = rot; link(o, c)
    if m: me.materials.append(m)
    return o

def from_pydata(name, verts, faces, m=None, c="Set"):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); link(o, c)
    if m: me.materials.append(m)
    return o

def append_objects(blend, c="Set"):
    with bpy.data.libraries.load(blend, link=False) as (src, dst):
        dst.objects = list(src.objects)
    out = []
    for o in dst.objects:
        if o is None: continue
        link(o, c); out.append(o)
    return out

def import_glb(path, c="Set"):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new: link(o, c)
    return new

def bounds(objs):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(b) for o in objs if o.type == 'MESH' for b in o.bound_box]
    return (Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)]))

def group(objs, name, c="Set"):
    """parent loose imported objects under one empty at world origin"""
    e = bpy.data.objects.new(name, None); link(e, c)
    for o in objs:
        if o.parent is None or o.parent not in objs:
            mw = o.matrix_world.copy(); o.parent = e; o.matrix_world = mw
    return e

def place_group(objs, name, target_size, axis, base_loc, rot_z=0.0, c="Set", align="bottom"):
    """scale imported objects so bbox[axis] = target_size, then put bbox bottom-centre at base_loc"""
    e = group(objs, name, c)
    mn, mx = bounds(objs)
    s = target_size / (mx - mn)[axis]
    ctr = (mn + mx) / 2
    off = Vector((ctr.x, ctr.y, mn.z if align == "bottom" else ctr.z))
    for o in objs:
        if o.parent == e:
            o.matrix_world = Matrix.Translation(-off) @ o.matrix_world
    e.scale = (s, s, s); e.rotation_euler = (0, 0, rot_z); e.location = base_loc
    bpy.context.view_layer.update()
    return e

def key_vis(o, keys):
    """keys: [(frame, visible)] for render + viewport"""
    for f, v in keys:
        o.hide_render = not v; o.keyframe_insert("hide_render", frame=f)
        o.hide_viewport = not v; o.keyframe_insert("hide_viewport", frame=f)

def constant_interp(o):
    ad = o.animation_data
    if not ad or not ad.action: return
    for layer in getattr(ad.action, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    if fc.data_path in ("hide_render", "hide_viewport"):
                        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'

def fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    out = []
    for layer in getattr(ad.action, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                out += list(cb.fcurves)
    return out

def linear_all(idb):
    for fc in fcurves(idb):
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

def smooth(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

def catmull(keys):
    xs = [k[0] for k in keys]; ys = [k[1] for k in keys]
    def f(x):
        if x <= xs[0]: return ys[0]
        if x >= xs[-1]: return ys[-1]
        i = max(j for j in range(len(xs) - 1) if xs[j] <= x)
        x0, x1 = xs[i], xs[i + 1]
        p0 = ys[i - 1] if i > 0 else ys[i] - (ys[i + 1] - ys[i])
        p3 = ys[i + 2] if i + 2 < len(ys) else ys[i + 1] + (ys[i + 1] - ys[i])
        t0 = xs[i - 1] if i > 0 else x0 - (x1 - x0)
        t3 = xs[i + 2] if i + 2 < len(xs) else x1 + (x1 - x0)
        p1, p2 = ys[i], ys[i + 1]
        m1 = (p2 - p0) * ((x1 - x0) / (x1 - t0)); m2 = (p3 - p1) * ((x1 - x0) / (t3 - x0))
        t = (x - x0) / (x1 - x0)
        return p1 * (2*t**3 - 3*t**2 + 1) + m1 * (t**3 - 2*t**2 + t) + p2 * (-2*t**3 + 3*t**2) + m2 * (t**3 - t**2)
    return f

def pchip(keys):
    xs = [k[0] for k in keys]; ys = [k[1] for k in keys]; n = len(xs)
    if n == 1: return lambda x: ys[0]
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    dl = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    for i in range(1, n - 1):
        if dl[i - 1] * dl[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / dl[i - 1] + w2 / dl[i])
    def f(x):
        if x <= xs[0]: return ys[0]
        if x >= xs[-1]: return ys[-1]
        i = max(j for j in range(n - 1) if xs[j] <= x)
        t = (x - xs[i]) / h[i]
        return ((1 + 2*t) * (1 - t)**2 * ys[i] + t * (1 - t)**2 * h[i] * m[i]
                + t*t * (3 - 2*t) * ys[i + 1] + t*t * (t - 1) * h[i] * m[i + 1])
    return f

def keep_lod(objs, prefer=(2, 1, 0)):
    """Poly Haven assets ship several LODs stacked in place: keep one per part, delete the rest"""
    import re
    groups = {}
    for o in objs:
        m = re.match(r"(.*)_LOD(\d+)$", o.name)
        if m: groups.setdefault(m.group(1), []).append((int(m.group(2)), o))
    out = [o for o in objs if not re.match(r".*_LOD\d+$", o.name)]
    for base, lst in groups.items():
        have = dict(lst); keep = next((have[p] for p in prefer if p in have), min(lst)[1])
        for k, o in lst:
            if o is keep: out.append(o)
            else: bpy.data.objects.remove(o, do_unlink=True)
    return out
