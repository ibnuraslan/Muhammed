# Shared helpers (exec'd by the build scripts).
import os, glob, math
import bpy
from mathutils import Vector, Matrix

R_ = math.radians
sc = bpy.context.scene


def img(path, nc=False):
    i = bpy.data.images.load(path, check_existing=True)
    if nc:
        i.colorspace_settings.name = 'Non-Color'
    return i


def _find(folder, keys):
    for k in keys:
        g = sorted(glob.glob(os.path.join(folder, "textures", "*_%s_*" % k)) + glob.glob(os.path.join(folder, "*_%s_*" % k)))
        if g:
            return g[0]
    return None


def pbr(name, folder, scale=1.0, tint=None, bump=1.0, rough_mul=1.0, rough_add=0.0, sat=1.0, val=1.0, coords='Object', disp=0.0):
    """Poly Haven texture set -> material (object or UV coordinates, box-projected for object coords)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    p = n["Principled BSDF"]
    tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / scale,) * 3
    l.new(tc.outputs[coords], mp.inputs['Vector'])
    proj = 'BOX' if coords == 'Object' else 'FLAT'
    def tex(path, nc):
        t = n.new('ShaderNodeTexImage'); t.image = img(path, nc); t.projection = proj; t.projection_blend = 0.2
        l.new(mp.outputs['Vector'], t.inputs['Vector']); return t
    d = _find(folder, ["diff", "col_1", "col", "diffuse"])
    if d:
        dt = tex(d, False)
        hsv = n.new('ShaderNodeHueSaturation'); hsv.inputs['Saturation'].default_value = sat; hsv.inputs['Value'].default_value = val
        l.new(dt.outputs['Color'], hsv.inputs['Color']); col = hsv.outputs['Color']
        if tint:
            mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
            mx.inputs['B'].default_value = (*tint, 1); l.new(col, mx.inputs['A']); col = mx.outputs['Result']
        l.new(col, p.inputs['Base Color'])
    r = _find(folder, ["rough", "roughness"])
    if r:
        rt = tex(r, True)
        rm = n.new('ShaderNodeMath'); rm.operation = 'MULTIPLY_ADD'; rm.inputs[1].default_value = rough_mul; rm.inputs[2].default_value = rough_add; rm.use_clamp = True
        l.new(rt.outputs['Color'], rm.inputs[0]); l.new(rm.outputs[0], p.inputs['Roughness'])
    nm = _find(folder, ["nor_gl"])
    if nm:
        nt = tex(nm, True)
        nmap = n.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = bump
        l.new(nt.outputs['Color'], nmap.inputs['Color']); l.new(nmap.outputs['Normal'], p.inputs['Normal'])
    return m


def mat(name, rgb, rough=0.5, metal=0.0, emit=None, estr=0.0, alpha=1.0, trans=0.0, ior=1.45, sss=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*rgb, 1); p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal; p.inputs['Alpha'].default_value = alpha
    p.inputs['Transmission Weight'].default_value = trans; p.inputs['IOR'].default_value = ior
    p.inputs['Coat Weight'].default_value = coat
    if sss:
        p.inputs['Subsurface Weight'].default_value = sss; p.inputs['Subsurface Radius'].default_value = (0.03, 0.01, 0.005)
    if emit:
        p.inputs['Emission Color'].default_value = (*emit, 1); p.inputs['Emission Strength'].default_value = estr
    return m


def emis(name, rgb, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n = m.node_tree.nodes; n.clear()
    o = n.new('ShaderNodeOutputMaterial'); e = n.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = (*rgb, 1); e.inputs['Strength'].default_value = strength
    m.node_tree.links.new(e.outputs[0], o.inputs[0]); return m


def coll(name, parent=None):
    c_ = bpy.data.collections.get(name)
    if c_ is None:
        c_ = bpy.data.collections.new(name); (parent or sc.collection).children.link(c_)
    return c_


def link(ob, c_):
    for c0 in list(ob.users_collection):
        c0.objects.unlink(ob)
    c_.objects.link(ob)
    return ob


def box(name, size, loc, m=None, c_=None, bevel=0.0, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    import bmesh
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); (c_ or sc.collection).objects.link(ob)
    ob.location = loc; ob.rotation_euler = rot
    if m:
        me.materials.append(m)
    if bevel:
        bv = ob.modifiers.new("bv", 'BEVEL'); bv.width = bevel; bv.segments = 2
    return ob


def cyl(name, r, h, loc, m=None, c_=None, verts=24, rot=(0, 0, 0)):
    import bmesh
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r, depth=h)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); (c_ or sc.collection).objects.link(ob)
    ob.location = loc; ob.rotation_euler = rot
    if m:
        me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = True
    return ob


def import_glb(path, name, height=None, length=None, loc=(0, 0, 0), rot_z=0.0, c_=None, join=True):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o.type != 'MESH':
            bpy.data.objects.remove(o, do_unlink=True)
    for o in bpy.data.objects:
        o.select_set(False)
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if join and len(meshes) > 1:
        bpy.ops.object.join()
        meshes = [bpy.context.view_layer.objects.active]
    pts = [Vector(v.co) for o in meshes for v in o.data.vertices]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    dims = mx - mn
    s = 1.0
    if height:
        s = height / dims.z
    elif length:
        s = length / max(dims.x, dims.y)
    for o in meshes:
        o.data.transform(Matrix.Translation(Vector((-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z))))
        o.data.transform(Matrix.Scale(s, 4))
        o.location = loc; o.rotation_euler = (0, 0, rot_z)
        if c_:
            link(o, c_)
    if join:
        meshes[0].name = name
        return meshes[0]
    for i, o in enumerate(meshes):
        o.name = "%s_%d" % (name, i)
    return meshes


def append_ph(blend, c_, loc=(0, 0, 0), rot_z=0.0, scale=1.0):
    with bpy.data.libraries.load(blend, link=False) as (src, dst):
        dst.objects = list(src.objects)
    obs = [o for o in dst.objects if o is not None]
    roots = [o for o in obs if o.parent is None]
    for o in obs:
        c_.objects.link(o)
    for o in roots:
        o.location = Vector(loc) + Matrix.Rotation(rot_z, 3, 'Z') @ (o.location * scale)
        o.rotation_euler.z += rot_z; o.scale = o.scale * scale
    return obs


def key_vis(obs, ranges, end=100000):
    """obs visible (render) only inside the given [(f0, f1), ...] frame ranges"""
    for ob in obs:
        ob.hide_render = True; ob.keyframe_insert("hide_render", frame=0)
        for f0, f1 in ranges:
            ob.hide_render = False; ob.keyframe_insert("hide_render", frame=f0)
            ob.hide_render = True; ob.keyframe_insert("hide_render", frame=f1 + 1)
        set_constant(ob)


def set_constant(ob, data=False):
    ad = (ob.data if data else ob).animation_data
    if not ad or not ad.action:
        return
    for layer in getattr(ad.action, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    if fc.data_path in ("hide_render", "hide_viewport"):
                        for kp in fc.keyframe_points:
                            kp.interpolation = 'CONSTANT'


def fcurves(id_):
    ad = id_.animation_data
    out = []
    if ad and ad.action:
        for layer in getattr(ad.action, "layers", []):
            for strip in layer.strips:
                for cb in strip.channelbags:
                    out += list(cb.fcurves)
    return out


def room(name, x0, x1, y0, y1, h, floor_m, wall_m, ceil_m, c_, holes=()):
    """closed room from 6 thin slabs; holes = [(wall, centre_u, z0, width, height)] cut with booleans.
    wall in 'N','S','E','W'"""
    t = 0.1
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; sx, sy = x1 - x0, y1 - y0
    obs = {}
    obs['F'] = box(name + "_Floor", (sx + 2 * t, sy + 2 * t, t), (cx, cy, -t / 2), floor_m, c_)
    obs['C'] = box(name + "_Ceil", (sx + 2 * t, sy + 2 * t, t), (cx, cy, h + t / 2), ceil_m, c_)
    obs['N'] = box(name + "_WallN", (sx + 2 * t, t, h), (cx, y1 + t / 2, h / 2), wall_m, c_)
    obs['S'] = box(name + "_WallS", (sx + 2 * t, t, h), (cx, y0 - t / 2, h / 2), wall_m, c_)
    obs['E'] = box(name + "_WallE", (t, sy, h), (x1 + t / 2, cy, h / 2), wall_m, c_)
    obs['W'] = box(name + "_WallW", (t, sy, h), (x0 - t / 2, cy, h / 2), wall_m, c_)
    for w, u, z0, wd, ht in holes:
        o = obs[w]
        if w in "NS":
            loc = (u, o.location.y, z0 + ht / 2); size = (wd, 0.5, ht)
        else:
            loc = (o.location.x, u, z0 + ht / 2); size = (0.5, wd, ht)
        cutter = box(name + "_cut_" + w, size, loc, None, c_)
        cutter.hide_render = True; cutter.hide_viewport = True; cutter.display_type = 'WIRE'
        bo = o.modifiers.new("hole", 'BOOLEAN'); bo.object = cutter; bo.operation = 'DIFFERENCE'; bo.solver = 'EXACT'
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier="hole")
        bpy.data.objects.remove(cutter, do_unlink=True)
    return obs
