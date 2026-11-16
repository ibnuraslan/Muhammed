"""B20 SafetyPin: shared helpers (paths, materials, primitives, asset append)."""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix
SCR = "/tmp/claude-0/-home-user-Muhammed/80503e31-c2cf-50aa-88df-299f2fd2a88d/scratchpad"
W = SCR + "/work/"
A = SCR + "/assets/"
REPO = "/home/user/Muhammed/blender/"
PIPE = REPO + "pipeline/"
V = REPO + "SafetyPin_v001/"
BRAND = REPO + "assets/brand/"
R_ = math.radians
sc = bpy.context.scene
os.makedirs(W, exist_ok=True)

def col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c

def mat(name, rgb, rough=0.5, metal=0.0, emit=None, coat=0.0, spec=0.5):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    P = m.node_tree.nodes["Principled BSDF"]
    P.inputs["Base Color"].default_value = (*rgb, 1); P.inputs["Roughness"].default_value = rough
    P.inputs["Metallic"].default_value = metal; P.inputs["Coat Weight"].default_value = coat
    P.inputs["Specular IOR Level"].default_value = spec
    if emit: P.inputs["Emission Color"].default_value = (*emit[0], 1); P.inputs["Emission Strength"].default_value = emit[1]
    return m

def img_mat(name, path, rough=0.6, alpha=False, emit=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    P = nt.nodes["Principled BSDF"]; t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path)
    t.extension = 'CLIP' if alpha else 'REPEAT'
    nt.links.new(t.outputs["Color"], P.inputs["Base Color"]); P.inputs["Roughness"].default_value = rough
    if emit:
        nt.links.new(t.outputs["Color"], P.inputs["Emission Color"]); P.inputs["Emission Strength"].default_value = emit
    if alpha: nt.links.new(t.outputs["Alpha"], P.inputs["Alpha"])
    return m

def link(o, c):
    for cc in list(o.users_collection): cc.objects.unlink(o)
    c.objects.link(o)

def box(name, c, loc, size, m, bevel=0.01, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); o = bpy.context.object; o.name = name
    o.scale = size; bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("Bevel", 'BEVEL'); b.width = bevel; b.segments = 3; b.limit_method = 'ANGLE'
    o.data.materials.append(m); link(o, c)
    return o

def plane(name, c, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot); o = bpy.context.object; o.name = name
    o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m); link(o, c); return o

def bounds(obs):
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for o in obs:
        if o.type != 'MESH': continue
        for cc in o.bound_box:
            w = o.matrix_world @ Vector(cc); mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
    return mn, mx

def append_asset(aid, name, c, loc=(0, 0, 0), rotz=0.0, height=None, scale=None, keep=None):
    """append every mesh of a Poly Haven .blend under an empty `name`; scale to `height` (m) if given"""
    import glob
    f = glob.glob(A + aid + "/*.blend")[0]
    with bpy.data.libraries.load(f, link=False) as (fd, td): td.objects = list(fd.objects)
    obs = [o for o in td.objects if o and o.type == 'MESH' and (keep is None or keep(o))]
    for o in td.objects:
        if o and o not in obs: bpy.data.objects.remove(o)
    root = bpy.data.objects.new(name, None); c.objects.link(root)
    for o in obs:
        c.objects.link(o)
        if o.parent is None or o.parent not in obs:
            mw = o.matrix_world.copy(); o.parent = root; o.matrix_world = mw
    bpy.context.view_layer.update()
    mn, mx = bounds(obs)
    s = scale or (height / (mx.z - mn.z) if height else 1.0)
    root.scale = (s,) * 3; root.rotation_euler.z = rotz
    root.location = Vector(loc) - Vector((0, 0, mn.z * s))
    bpy.context.view_layer.update()
    for o in obs:
        for m in o.data.materials:
            if m and m.node_tree:
                for nd in m.node_tree.nodes:
                    if nd.type == 'TEX_IMAGE' and nd.image and not nd.image.filepath.startswith("//"): pass
    return root, obs

def bend_path(obj):
    return obj
