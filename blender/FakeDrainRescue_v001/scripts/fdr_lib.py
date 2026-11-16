# Shared helpers for FakeDrainRescue (exec'd by build scripts)
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
HERE = "/home/user/Muhammed/blender/FakeDrainRescue_v001/"
PH = HERE + "work/ph/"
def mat(name, rgb, rough=0.55, metal=0.0, spec=None, alpha=1.0, emit=None, sheen=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; P = m.node_tree.nodes["Principled BSDF"]
    P.inputs["Base Color"].default_value = (*rgb, 1); P.inputs["Roughness"].default_value = rough; P.inputs["Metallic"].default_value = metal
    if spec is not None: P.inputs["Specular IOR Level"].default_value = spec
    if alpha < 1: P.inputs["Alpha"].default_value = alpha
    if emit: P.inputs["Emission Color"].default_value = (*emit[0], 1); P.inputs["Emission Strength"].default_value = emit[1]
    if sheen: P.inputs["Sheen Weight"].default_value = sheen
    return m
def img_mat(name, path, rough=0.5, emit=0.0, alpha=False):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path); t.image.pack()
    nt.links.new(t.outputs["Color"], P.inputs["Base Color"]); P.inputs["Roughness"].default_value = rough
    if alpha: nt.links.new(t.outputs["Alpha"], P.inputs["Alpha"])
    if emit: nt.links.new(t.outputs["Color"], P.inputs["Emission Color"]); P.inputs["Emission Strength"].default_value = emit
    return m
def coll(name):
    c = bpy.data.collections.get(name)
    if not c: c = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c)
    return c
def link(o, cname):
    for uc in list(o.users_collection): uc.objects.unlink(o)
    coll(cname).objects.link(o); return o
def box(name, size, loc, m, cname="Set", rot=(0, 0, 0), bevel=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); coll(cname).objects.link(o)
    o.location = loc; o.rotation_euler = rot; me.materials.append(m)
    if bevel: b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = 2
    return o
def plane(name, sx, sy, loc, m, cname="Set", rot=(0, 0, 0), subdiv=0):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bm.loops.layers.uv.new('UVMap')
    bmesh.ops.create_grid(bm, x_segments=max(1, subdiv), y_segments=max(1, subdiv), size=0.5, calc_uvs=True)
    for v in bm.verts: v.co.x *= sx; v.co.y *= sy
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); coll(cname).objects.link(o)
    o.location = loc; o.rotation_euler = rot; me.materials.append(m); return o
def append_ph(blend, names, cname):
    with bpy.data.libraries.load(PH + blend, link=False) as (s, d): d.objects = [n for n in s.objects if n in names]
    out = []
    for o in d.objects:
        if o is None: continue
        coll(cname).objects.link(o); out.append(o)
    return out
def append_ph_mat(blend, name):
    with bpy.data.libraries.load(PH + blend, link=False) as (s, d): d.materials = [name]
    m = d.materials[0]
    for n in m.node_tree.nodes:   # soften: low bump / normal, roughness >= 0.35
        if n.type == 'BUMP': n.inputs["Strength"].default_value = min(n.inputs["Strength"].default_value, 0.3)
        if n.type == 'NORMAL_MAP': n.inputs["Strength"].default_value = 0.35
        if n.type == 'DISPLACEMENT': n.inputs["Scale"].default_value = 0.0
        if n.type == 'TEX_IMAGE' and n.image: n.image.pack()
    return m
def import_glb(name, path, size, axis, cname):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]; ms = [o for o in new if o.type == 'MESH']
    bpy.context.view_layer.update(); mws = {o.name: o.matrix_world.copy() for o in ms}
    for o in ms: o.parent = None
    for o in ms: o.matrix_world = mws[o.name]
    for o in new:
        if o not in ms: bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in ms: o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]
    if len(ms) > 1: bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active; o.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    pts = [Vector(v.co) for v in o.data.vertices]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    s = size / (mx - mn)[axis]
    c = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))   # origin at the bottom centre
    o.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation(-c)); o.location = (0, 0, 0)
    for p in o.data.polygons: p.use_smooth = True
    for img in bpy.data.images:
        if img.source == 'FILE' and not img.packed_file:
            try: img.pack()
            except Exception: pass
    link(o, cname); return o
def key_vis(names, ranges):
    """visible only inside [f0,f1] ranges; hide_render AND hide_viewport keyed together (constant)"""
    for n in names:
        o = bpy.data.objects[n] if isinstance(n, str) else n
        o.hide_render = True; o.hide_viewport = True
        o.keyframe_insert("hide_render", frame=0); o.keyframe_insert("hide_viewport", frame=0)
        for f0, f1 in ranges:
            o.hide_render = False; o.hide_viewport = False; o.keyframe_insert("hide_render", frame=f0); o.keyframe_insert("hide_viewport", frame=f0)
            o.hide_render = True; o.hide_viewport = True; o.keyframe_insert("hide_render", frame=f1 + 1); o.keyframe_insert("hide_viewport", frame=f1 + 1)
