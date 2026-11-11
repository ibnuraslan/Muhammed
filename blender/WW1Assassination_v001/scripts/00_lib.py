# Shared helpers for WW1Assassination build scripts (exec'd by the others).
import os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix

ASSETS = os.environ.get("WW1_ASSETS", "/tmp/claude-0/-home-user-Muhammed/5f5efa17-861e-5fc3-aa91-c5b707b080e0/scratchpad/assets")
MODELS = os.environ.get("WW1_MODELS", "/tmp/claude-0/-home-user-Muhammed/5f5efa17-861e-5fc3-aa91-c5b707b080e0/scratchpad/models")
R_ = math.radians
V = lambda *a: Vector(a)

def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name); (parent or bpy.context.scene.collection).children.link(c)
    return c

def link(o, c):
    for uc in list(o.users_collection): uc.objects.unlink(o)
    c.objects.link(o)
    return o

def nodes_of(m):
    try: m.use_nodes = True
    except Exception: pass
    return m.node_tree.nodes, m.node_tree.links

def img(path, non_color=False):
    i = bpy.data.images.load(path, check_existing=True)
    if non_color: i.colorspace_settings.name = "Non-Color"
    return i

def tex_files(asset):
    d = os.path.join(ASSETS, asset)
    if os.path.isdir(os.path.join(d, "textures")): d = os.path.join(d, "textures")
    fs = sorted(os.listdir(d))
    pick = lambda k: next((os.path.join(d, f) for f in fs if k in f and not f.endswith(".exr")), None)
    return pick("_diff_") or pick("_diff"), pick("_nor_gl"), pick("_rough")

def pbr(name, asset, scale=1.0, tint=None, rough_mul=1.0, bump=1.0, coord="Object", box=True):
    """Image-based PBR with box projection in object (or generated) space; scale = repeats per metre."""
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); n, l = nodes_of(m); n.clear()
    out = n.new('ShaderNodeOutputMaterial'); bs = n.new('ShaderNodeBsdfPrincipled')
    l.new(bs.outputs[0], out.inputs[0])
    tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale,) * 3
    l.new(tc.outputs[coord], mp.inputs['Vector'])
    d, nr, r = tex_files(asset)
    def T(p, nc):
        t = n.new('ShaderNodeTexImage'); t.image = img(p, nc)
        if box: t.projection = 'BOX'; t.projection_blend = 0.25
        l.new(mp.outputs[0], t.inputs['Vector']); return t
    td = T(d, False); col = td.outputs['Color']
    if tint:
        mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        mx.inputs['B'].default_value = (*tint, 1); l.new(col, mx.inputs['A']); col = mx.outputs['Result']
    l.new(col, bs.inputs['Base Color'])
    if r:
        tr = T(r, True); mm = n.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = rough_mul
        l.new(tr.outputs['Color'], mm.inputs[0]); l.new(mm.outputs[0], bs.inputs['Roughness'])
    if nr:
        tn = T(nr, True); nm = n.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = bump
        l.new(tn.outputs['Color'], nm.inputs['Color']); l.new(nm.outputs[0], bs.inputs['Normal'])
    return m

def flat(name, rgb, rough=0.6, metal=0.0, emit=None, emit_str=0.0, alpha=1.0, trans=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); n, l = nodes_of(m)
    bs = next(x for x in n if x.type == 'BSDF_PRINCIPLED')
    bs.inputs['Base Color'].default_value = (*rgb, 1); bs.inputs['Roughness'].default_value = rough
    bs.inputs['Metallic'].default_value = metal
    if emit:
        bs.inputs['Emission Color'].default_value = (*emit, 1); bs.inputs['Emission Strength'].default_value = emit_str
    if trans: bs.inputs['Transmission Weight'].default_value = trans
    if alpha < 1: bs.inputs['Alpha'].default_value = alpha
    m.diffuse_color = (*rgb, 1)
    return m

def mesh_obj(name, bm, mats, c):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for mt in mats: me.materials.append(mt)
    o = bpy.data.objects.new(name, me); c.objects.link(o)
    return o

def add_box(bm, mn, mx, mat=0):
    """axis-aligned box into bmesh with material index"""
    xs, ys, zs = (mn.x, mx.x), (mn.y, mx.y), (mn.z, mx.z)
    vs = [bm.verts.new((xs[i], ys[j], zs[k])) for i in (0, 1) for j in (0, 1) for k in (0, 1)]
    idx = lambda i, j, k: vs[i * 4 + j * 2 + k]
    faces = [((0,0,0),(0,1,0),(1,1,0),(1,0,0)), ((0,0,1),(1,0,1),(1,1,1),(0,1,1)),
             ((0,0,0),(1,0,0),(1,0,1),(0,0,1)), ((0,1,0),(0,1,1),(1,1,1),(1,1,0)),
             ((0,0,0),(0,0,1),(0,1,1),(0,1,0)), ((1,0,0),(1,1,0),(1,1,1),(1,0,1))]
    for fc in faces:
        f = bm.faces.new([idx(*p) for p in fc]); f.material_index = mat; f.smooth = False
    return vs

def shade_smooth(o, angle=35):
    for p in o.data.polygons: p.use_smooth = True
    try:
        o.modifiers.new("Smooth", 'SMOOTH_BY_ANGLE')
    except Exception:
        pass

def import_glb(path, c, name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new: link(o, c)
    root = bpy.data.objects.new(name, None); c.objects.link(root)
    for o in new:
        if o.parent is None: o.parent = root
    return root, new
