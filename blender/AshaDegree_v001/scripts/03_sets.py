"""AshaDegree sets. Every set sits in its own spot in one scene; hard cuts switch cameras (markers).
  ROOM (0,0)        living room, plaid wallpaper, French doors open onto the rainy night, toy-brick towers
  ROAD (100,0)      two-lane highway at night in the rain: street lamps, verge, tree line, sedan
  WOODS (200,0)     forest floor with fir trees, shrubs, ferns, a bench (night run + torch search)
  SHED (300,0)      daytime: white-sided shed on grass at the woods' edge
  SITE (400,0)      daytime construction site: dirt, gravel, cement bags, barrier, fallen school-crossing sign
  WALL (500,0)      warm wall with the framed portrait (generic girl, our own render)
blender -b work/dressed.blend --python 03_sets.py -- work/sets.blend"""
import bpy, bmesh, sys, math, random, glob, os
from mathutils import Vector, Matrix, Euler
out = sys.argv[sys.argv.index("--") + 1]
HERE = "/home/user/Muhammed/blender/AshaDegree_v001/"
AS = HERE + "assets/"; PH = AS + "ph/"
random.seed(6)
sc = bpy.context.scene
R_ = math.radians

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
def link(o, c):
    for uc in list(o.users_collection): uc.objects.unlink(o)
    c.objects.link(o)

def mat(name, rgb, rough=0.6, metal=0.0, emit=None, estr=0.0, alpha=1.0, sheen=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; P = m.node_tree.nodes["Principled BSDF"]
    P.inputs["Base Color"].default_value = (*rgb, 1); P.inputs["Roughness"].default_value = rough; P.inputs["Metallic"].default_value = metal
    if emit: P.inputs["Emission Color"].default_value = (*emit, 1); P.inputs["Emission Strength"].default_value = estr
    if alpha < 1: P.inputs["Alpha"].default_value = alpha
    if sheen: P.inputs["Sheen Weight"].default_value = sheen
    return m

def tex_mat(name, folder, scale=1.0, tint=None, rough=None, bump=0.3):
    """Poly Haven texture set -> clean material (diffuse + low-strength normal), box-mapped by object coords"""
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["UV"], mp.inputs[0])
    d = sorted(glob.glob(PH + folder + "/*diff*")) or sorted(glob.glob(PH + folder + "/textures/*diff*"))
    n = sorted(glob.glob(PH + folder + "/*nor_gl*")) or sorted(glob.glob(PH + folder + "/textures/*nor_gl*"))
    if d:
        ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = bpy.data.images.load(d[0], check_existing=True); nt.links.new(mp.outputs[0], ti.inputs[0])
        col = ti.outputs["Color"]
        if tint:
            mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1
            mx.inputs['B'].default_value = (*tint, 1); nt.links.new(col, mx.inputs['A']); col = mx.outputs['Result']
        nt.links.new(col, P.inputs["Base Color"])
    if n and not n[0].endswith(".exr"):
        tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = bpy.data.images.load(n[0], check_existing=True); tn.image.colorspace_settings.name = 'Non-Color'
        nt.links.new(mp.outputs[0], tn.inputs[0]); nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = bump
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs[0], P.inputs["Normal"])
    P.inputs["Roughness"].default_value = rough if rough is not None else 0.7
    return m

def plane(name, size, loc, material, c, rot=(0, 0, 0), uv_scale=1.0):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = (size[0], size[1], 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for l in o.data.uv_layers[0].data: l.uv = (l.uv[0] * size[0] / uv_scale, l.uv[1] * size[1] / uv_scale)
    o.data.materials.append(material); link(o, c); return o

def box(name, dims, loc, material, c, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = dims; bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = 3
    o.data.materials.append(material); link(o, c); return o

def import_glb(name, fn, c, size=None, axis=2, loc=(0, 0, 0), rot=(0, 0, 0), keep=None):
    """import a GLB, join its meshes, normalise so dimension[axis] == size, base on z=0, centred in xy"""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=AS + fn)
    new = [o for o in bpy.data.objects if o not in before]
    ms = [o for o in new if o.type == 'MESH' and (keep is None or keep(o))]
    bpy.context.view_layer.update()
    mws = {o.name: o.matrix_world.copy() for o in ms}
    for o in ms: o.parent = None
    for o in ms: o.matrix_world = mws[o.name]
    for o in new:
        if o not in ms: bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in ms: o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]
    if len(ms) > 1: bpy.ops.object.join()
    o = bpy.context.object; o.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    pts = [Vector(v.co) for v in o.data.vertices]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    s = size / (mx - mn)[axis] if size else 1.0
    off = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    o.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation(-off))
    o.location = loc; o.rotation_euler = rot; link(o, c)
    for p in o.data.polygons: p.use_smooth = True
    return o

def recolor(o, mapping):
    """mapping: {substring of material name: material}; unmatched slots keep their material"""
    for i, m in enumerate(o.data.materials):
        for k, v in mapping.items():
            if m and k.lower() in m.name.lower(): o.data.materials[i] = v

def lib_obj(blend, name, c, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0, linked_data=None):
    if linked_data is None:
        with bpy.data.libraries.load(blend) as (src, dst): dst.objects = [name]
        o = dst.objects[0]
    else:
        o = bpy.data.objects.new(name, linked_data)
    sc.collection.objects.link(o); link(o, c)
    o.location = loc; o.rotation_euler = rot; o.scale = (scale,) * 3
    return o

def inst(src, name, c, loc, rot=(0, 0, 0), scale=1.0):
    o = bpy.data.objects.new(name, src.data); c.objects.link(o)
    o.location = loc; o.rotation_euler = rot; o.scale = (scale,) * 3
    return o

def area(name, c, loc, rot, energy, size, col=(1, 1, 1), shape='RECTANGLE', size_y=None):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.size = size; l.color = col; l.shape = shape
    if size_y: l.size_y = size_y
    o = bpy.data.objects.new(name, l); c.objects.link(o); o.location = loc; o.rotation_euler = rot; return o

def point(name, c, loc, energy, col=(1, 0.85, 0.6), radius=0.1):
    l = bpy.data.lights.new(name, 'POINT'); l.energy = energy; l.color = col; l.shadow_soft_size = radius
    o = bpy.data.objects.new(name, l); c.objects.link(o); o.location = loc; return o

def spot(name, c, loc, rot, energy, angle=60, col=(1, 0.85, 0.6), blend=0.5, radius=0.05):
    l = bpy.data.lights.new(name, 'SPOT'); l.energy = energy; l.color = col; l.spot_size = R_(angle); l.spot_blend = blend; l.shadow_soft_size = radius
    o = bpy.data.objects.new(name, l); c.objects.link(o); o.location = loc; o.rotation_euler = rot; return o

# ------------------------------------------------------------------ rain (geometry nodes, falls continuously; no event timing)
def rain(name, c, center, size=(14, 14, 7), count=7000, speed=9.0):
    me = bpy.data.meshes.new(name + "_pts")
    me.from_pydata([(random.uniform(-size[0] / 2, size[0] / 2), random.uniform(-size[1] / 2, size[1] / 2), random.uniform(0, size[2])) for _ in range(count)], [], [])
    o = bpy.data.objects.new(name, me); c.objects.link(o); o.location = center
    streak = bpy.data.objects.get("RainStreak")
    if streak is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=4, radius=0.0007, depth=0.12)
        streak = bpy.context.object; streak.name = "RainStreak"
        m = bpy.data.materials.new("Rain"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        o_ = nt.nodes.new("ShaderNodeOutputMaterial"); mx = nt.nodes.new("ShaderNodeMixShader"); em = nt.nodes.new("ShaderNodeEmission"); tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        em.inputs["Color"].default_value = (0.75, 0.85, 1.0, 1); em.inputs["Strength"].default_value = 0.9; mx.inputs[0].default_value = 0.3
        nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o_.inputs[0])
        # streaks closer than ~2 m to the camera fade out (no white sticks across the lens)
        cd = nt.nodes.new("ShaderNodeCameraData"); mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs[1].default_value = 1.5; mr.inputs[2].default_value = 3.0; mr.inputs[3].default_value = 0.0; mr.inputs[4].default_value = 0.3
        nt.links.new(cd.outputs["View Z Depth"], mr.inputs[0]); nt.links.new(mr.outputs[0], mx.inputs[0])
        streak.data.materials.append(m)
        streak.hide_render = True; streak.hide_viewport = True; link(streak, coll("Lib"))
    ng = bpy.data.node_groups.get("RainFall")
    if ng is None:
        ng = bpy.data.node_groups.new("RainFall", 'GeometryNodeTree')
        ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
        ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
        N = ng.nodes; L = ng.links
        gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
        pos = N.new("GeometryNodeInputPosition"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(pos.outputs[0], sep.inputs[0])
        t = N.new("GeometryNodeInputSceneTime")
        mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = speed; L.new(t.outputs["Seconds"], mul.inputs[0])
        sub = N.new("ShaderNodeMath"); sub.operation = 'SUBTRACT'; L.new(sep.outputs[2], sub.inputs[0]); L.new(mul.outputs[0], sub.inputs[1])
        mod = N.new("ShaderNodeMath"); mod.operation = 'FLOORED_MODULO'; mod.inputs[1].default_value = size[2]; L.new(sub.outputs[0], mod.inputs[0])
        comb = N.new("ShaderNodeCombineXYZ"); L.new(sep.outputs[0], comb.inputs[0]); L.new(sep.outputs[1], comb.inputs[1]); L.new(mod.outputs[0], comb.inputs[2])
        sp = N.new("GeometryNodeSetPosition"); L.new(gi.outputs[0], sp.inputs["Geometry"]); L.new(comb.outputs[0], sp.inputs["Position"])
        m2p = N.new("GeometryNodeMeshToPoints"); L.new(sp.outputs[0], m2p.inputs[0])
        oi = N.new("GeometryNodeObjectInfo"); oi.inputs[0].default_value = streak
        iop = N.new("GeometryNodeInstanceOnPoints"); L.new(m2p.outputs[0], iop.inputs["Points"]); L.new(oi.outputs["Geometry"], iop.inputs["Instance"])
        L.new(iop.outputs[0], go.inputs[0])
    md = o.modifiers.new("Rain", 'NODES'); md.node_group = ng
    return o

# ------------------------------------------------------------------ toy bricks (our own simple model: bevelled block + studs, no text)
BRICK_COLS = [(0.9, 0.1, 0.1), (0.1, 0.35, 0.9), (0.98, 0.8, 0.1), (0.1, 0.65, 0.25), (0.98, 0.5, 0.1), (0.95, 0.95, 0.95), (0.6, 0.2, 0.75)]
def brick_mesh():
    me = bpy.data.meshes.get("ToyBrick")
    if me: return me
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(0.064, 0.032, 0.038), verts=bm.verts); bmesh.ops.translate(bm, vec=(0, 0, 0.019), verts=bm.verts)
    for ix in (-0.024, -0.008, 0.008, 0.024):
        for iy in (-0.008, 0.008):
            r = bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.0048, radius2=0.0048, depth=0.0034)
            bmesh.ops.translate(bm, vec=(ix, iy, 0.038 + 0.0017), verts=r['verts'])
    me = bpy.data.meshes.new("ToyBrick"); bm.to_mesh(me); bm.free(); me.materials.append(mat("Brick0", BRICK_COLS[0], 0.3))
    for p in me.polygons: p.use_smooth = False
    return me
BRICK_COLS = [(0.9, 0.1, 0.1), (0.1, 0.35, 0.9), (0.98, 0.8, 0.1), (0.1, 0.65, 0.25), (0.98, 0.5, 0.1), (0.95, 0.95, 0.95), (0.6, 0.2, 0.75)]
def brick_mats(): return [mat("Brick%d" % i, col, 0.3) for i, col in enumerate(BRICK_COLS)]
def tower(c, base, layers, rot=0.0, name="Tower"):
    me = brick_mesh(); bms = brick_mats()
    for k in range(layers):
        for j in (-1, 1):
            o = bpy.data.objects.new("%s_%02d%s" % (name, k, "ab"[j > 0]), me.copy() if False else me)
            c.objects.link(o)
            off = Vector((0, j * 0.016, 0)) if k % 2 == 0 else Vector((j * 0.016, 0, 0))
            o.rotation_euler = (0, 0, rot + (0 if k % 2 == 0 else R_(90)))
            o.location = Vector(base) + Matrix.Rotation(rot, 3, 'Z') @ off + Vector((0, 0, 0.038 * k))
            o.material_slots[0].link = 'OBJECT'; o.material_slots[0].material = random.choice(bms)

# ================================================================== ROOM
C = coll("SET_Room")
floor_m = tex_mat("RoomFloor", "laminate_floor_02", rough=0.45, tint=(1.05, 0.85, 0.65))
plane("Room_Floor", (7, 7), (0, 0, 0), floor_m, C, uv_scale=2.0)
# plaid wallpaper (procedural: two crossing stripe sets, warm orange on cream)
wp = bpy.data.materials.new("Wallpaper"); wp.use_nodes = True; nt = wp.node_tree; P = nt.nodes["Principled BSDF"]
tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sp.inputs[0])
def stripes(inp, freq, width):
    a = nt.nodes.new("ShaderNodeMath"); a.operation = 'MULTIPLY'; a.inputs[1].default_value = freq; nt.links.new(inp, a.inputs[0])
    f = nt.nodes.new("ShaderNodeMath"); f.operation = 'FRACT'; nt.links.new(a.outputs[0], f.inputs[0])
    lt = nt.nodes.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = width; nt.links.new(f.outputs[0], lt.inputs[0])
    return lt.outputs[0]
h1 = stripes(sp.outputs[0], 4.0, 0.22); h1b = stripes(sp.outputs[1], 4.0, 0.22); v1 = stripes(sp.outputs[2], 4.0, 0.22)
hmax = nt.nodes.new("ShaderNodeMath"); hmax.operation = 'MAXIMUM'; nt.links.new(h1, hmax.inputs[0]); nt.links.new(h1b, hmax.inputs[1])
add = nt.nodes.new("ShaderNodeMath"); add.operation = 'ADD'; nt.links.new(hmax.outputs[0], add.inputs[0]); nt.links.new(v1, add.inputs[1])
cr = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(add.outputs[0], cr.inputs[0])
cr.color_ramp.elements[0].color = (0.93, 0.86, 0.74, 1); cr.color_ramp.elements[1].position = 0.5; cr.color_ramp.elements[1].color = (0.86, 0.52, 0.28, 1)
e = cr.color_ramp.elements.new(1.0); e.color = (0.66, 0.3, 0.16, 1)
thin = stripes(sp.outputs[2], 16.0, 0.08)
mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs['B'].default_value = (0.8, 0.45, 0.32, 1); nt.links.new(cr.outputs[0], mx.inputs['A'])
mf = nt.nodes.new("ShaderNodeMath"); mf.operation = 'MULTIPLY'; mf.inputs[1].default_value = 0.5; nt.links.new(thin, mf.inputs[0]); nt.links.new(mf.outputs[0], mx.inputs['Factor'])
nt.links.new(mx.outputs['Result'], P.inputs["Base Color"]); P.inputs["Roughness"].default_value = 0.8
plane("Room_WallLeft", (7, 2.8), (-3.0, 0, 1.4), wp, C, rot=(R_(90), 0, R_(90)))
plane("Room_WallRight", (7, 2.8), (3.0, 0, 1.4), wp, C, rot=(R_(90), 0, R_(-90)))
plane("Room_WallFront", (7, 2.8), (0, -3.5, 1.4), wp, C, rot=(R_(90), 0, 0))
ceil_m = mat("Ceiling", (0.95, 0.94, 0.92), 0.9)
plane("Room_Ceiling", (7, 7), (0, 0, 2.8), ceil_m, C, rot=(R_(180), 0, 0))
# back wall with the French-door opening (x 0.05..1.55, z 0..2.25)
DX0, DX1, DZ = 0.05, 1.55, 2.25
for nm, x0, x1, z0, z1 in (("L", -3.5, DX0, 0, 2.8), ("R", DX1, 3.5, 0, 2.8), ("T", DX0, DX1, DZ, 2.8)):
    plane("Room_WallBack" + nm, (x1 - x0, z1 - z0), ((x0 + x1) / 2, 3.0, (z0 + z1) / 2), wp, C, rot=(R_(90), 0, R_(180)))
white = mat("DoorWhite", (0.95, 0.95, 0.93), 0.35)
skirt = mat("Skirting", (0.96, 0.96, 0.94), 0.4)
for nm, loc, dims in (("SkirtL", (-1.7, 2.99, 0.06), (2.6, 0.02, 0.12)), ("SkirtR", (2.3, 2.99, 0.06), (1.45, 0.02, 0.12)), ("SkirtLW", (-2.99, 0, 0.06), (0.02, 6.9, 0.12))):
    box("Room_" + nm, dims, loc, skirt, C)
# frame
box("Door_FrameL", (0.07, 0.16, DZ + 0.07), (DX0 - 0.035, 3.0, (DZ + 0.07) / 2), white, C, bevel=0.01)
box("Door_FrameR", (0.07, 0.16, DZ + 0.07), (DX1 + 0.035, 3.0, (DZ + 0.07) / 2), white, C, bevel=0.01)
box("Door_FrameT", (DX1 - DX0 + 0.14, 0.16, 0.07), ((DX0 + DX1) / 2, 3.0, DZ + 0.035), white, C, bevel=0.01)
glass = mat("DoorGlass", (0.8, 0.9, 1.0), 0.05); glass.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 1.0
def door_leaf(name, hinge_x, width, sign):
    """leaf built around its hinge (pivot = an empty at the hinge); sign +1 opens to +x side"""
    piv = bpy.data.objects.new(name, None); C.objects.link(piv); piv.location = (hinge_x, 3.0, 0)
    parts = []
    w = width; t = 0.045
    def part(nm, dims, loc, m):
        o = box(name + "_" + nm, dims, loc, m, C, bevel=0.006); o.parent = piv; o.location = Vector(loc); parts.append(o)
    cx = sign * w / 2
    part("StileA", (0.08, t, DZ), (sign * 0.04, 0, DZ / 2), white); part("StileB", (0.08, t, DZ), (sign * (w - 0.04), 0, DZ / 2), white)
    part("Bottom", (w, t, 0.22), (cx, 0, 0.11), white); part("Top", (w, t, 0.09), (cx, 0, DZ - 0.045), white)
    nrows, ncols = 5, 2
    gw = w - 0.16; gh = DZ - 0.31
    part("Glass", (gw, 0.008, gh), (cx, 0, 0.22 + gh / 2), glass)
    for r in range(1, nrows):
        part("Bar%d" % r, (gw, t * 0.8, 0.03), (cx, 0, 0.22 + gh * r / nrows), white)
    for k in range(1, ncols):
        part("Mull%d" % k, (0.03, t * 0.8, gh), (sign * (0.08 + gw * k / ncols), 0, 0.22 + gh / 2), white)
    knob = mat("Brass", (0.85, 0.65, 0.3), 0.3, metal=1.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.028, location=(0, 0, 0)); kb = bpy.context.object; kb.name = name + "_Knob"
    kb.data.materials.append(knob); link(kb, C); kb.parent = piv; kb.location = (sign * (w - 0.09), -0.045, 1.0); parts.append(kb)
    return piv
DoorL = door_leaf("DoorLeafL", DX0, (DX1 - DX0) / 2, +1)
DoorR = door_leaf("DoorLeafR", DX1, (DX1 - DX0) / 2, -1)
# outside the door: wet patio, rain, bushes, dark garden (readable blue night)
patio = mat("WetPatio", (0.22, 0.24, 0.28), 0.18)
plane("Yard_Patio", (8, 6), (0.8, 6.0, 0.0), patio, C)
lawn = mat("NightLawn", (0.08, 0.16, 0.08), 0.8)
plane("Yard_Lawn", (30, 20), (0.8, 19.0, -0.01), lawn, C)
fence_m = mat("Fence", (0.42, 0.33, 0.25), 0.7)
for i in range(16):
    box("Yard_Fence%02d" % i, (0.09, 0.03, 1.6), (-3.2 + i * 0.5, 8.5, 0.8), fence_m, C)
box("Yard_FenceRail", (8.0, 0.04, 0.08), (0.55, 8.48, 1.3), fence_m, C)
rain("Rain_Room", C, (0.8, 6.0, 0.0), size=(7, 6, 4), count=3000)
area("Yard_Moon", C, (0.8, 7.5, 4.5), (R_(-30), 0, 0), 300, 6, col=(0.55, 0.65, 1.0))
# furniture: floor lamp (warm light), rug, toy-brick towers, book stack, toy box
lamp = import_glb("Room_FloorLamp", "floorlamp.glb", C, size=1.65, loc=(2.3, 2.45, 0))
point("Room_LampBulb", C, (2.3, 2.45, 1.45), 60, col=(1.0, 0.8, 0.55), radius=0.15)
rug = bpy.data.materials.new("Rug"); rug.use_nodes = True; nt = rug.node_tree; P = nt.nodes["Principled BSDF"]
tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 3.0; wv.wave_profile = 'SAW'
nt.links.new(tc.outputs["UV"], wv.inputs[0]); cr = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(wv.outputs["Fac"], cr.inputs[0])
cr.color_ramp.interpolation = 'CONSTANT'
for pos_, col_ in ((0.0, (0.95, 0.9, 0.8)), (0.2, (0.9, 0.4, 0.3)), (0.4, (0.95, 0.75, 0.3)), (0.6, (0.3, 0.6, 0.75)), (0.8, (0.95, 0.9, 0.8))):
    el = cr.color_ramp.elements.new(pos_) if pos_ not in (0.0,) else cr.color_ramp.elements[0]; el.color = (*col_, 1)
nt.links.new(cr.outputs[0], P.inputs["Base Color"]); P.inputs["Roughness"].default_value = 0.95; P.inputs["Sheen Weight"].default_value = 0.5
r_ = plane("Room_Rug", (2.6, 1.9), (0.1, 0.1, 0.004), rug, C)
tower(C, (-0.75, -0.55, 0.004), 14, 0.3, "TowerA"); tower(C, (0.95, -0.25, 0.004), 10, -0.2, "TowerB")
tower(C, (-0.45, 0.95, 0.004), 12, 0.6, "TowerC") if False else tower(C, (-0.15, 1.25, 0.004), 12, 0.6, "TowerC"); tower(C, (1.25, 0.85, 0.004), 8, 0.1, "TowerD")
for i in range(18):   # loose bricks on the rug
    o = bpy.data.objects.new("LooseBrick%02d" % i, brick_mesh()); C.objects.link(o)
    o.location = (random.uniform(-1.0, 1.3), random.uniform(-0.9, 0.9), 0.004); o.rotation_euler = (0, 0, random.uniform(0, 6.3))
    if (Vector(o.location) - Vector((0, 0.15, 0))).length < 0.55: o.location.x += 0.7
    o.material_slots[0].link = 'OBJECT'; o.material_slots[0].material = random.choice(brick_mats())
book_cols = [(0.2, 0.45, 0.8), (0.85, 0.75, 0.2), (0.3, 0.7, 0.4), (0.8, 0.3, 0.3)]
for i, col in enumerate(book_cols):   # a stack of plain school books beside her
    box("Room_Book%d" % i, (0.21, 0.28, 0.025), (0.5, 0.45, 0.004 + 0.0125 + 0.026 * i), mat("Book%d" % i, col, 0.5), C, bevel=0.003, rot=(0, 0, R_(8 * i - 10)))
# cardboard toy box with our logo (neutral opening moment, never in the sad beats)
cb = mat("Cardboard", (0.72, 0.52, 0.32), 0.85)
tb = box("Room_ToyBox", (0.55, 0.4, 0.38), (-1.05, 1.75, 0.19), cb, C, bevel=0.01, rot=(0, 0, R_(28)))
logo = bpy.data.images.load(HERE + "../assets/brand/DaKrasFilms_logo_dark.png", check_existing=True)
lm = bpy.data.materials.new("LogoDecal_Box"); lm.use_nodes = True; nt = lm.node_tree; P = nt.nodes["Principled BSDF"]
ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = logo; nt.links.new(ti.outputs["Color"], P.inputs["Base Color"]); nt.links.new(ti.outputs["Alpha"], P.inputs["Alpha"])
P.inputs["Roughness"].default_value = 0.8
if hasattr(lm, "blend_method"): lm.blend_method = 'HASHED'
bpy.ops.mesh.primitive_plane_add(size=1); dec = bpy.context.object; dec.name = "Room_ToyBoxLogo"
dec.scale = (0.46, 0.46 * 414 / 967, 1); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
dec.data.materials.append(lm); link(dec, C)
dec.rotation_euler = (R_(90), 0, R_(28)); dec.location = Vector(tb.location) + Matrix.Rotation(R_(28), 3, 'Z') @ Vector((0, -0.203, 0.02))
bpy.context.view_layer.update(); dec.parent = tb; dec.matrix_parent_inverse = tb.matrix_world.inverted()
# light the room: warm key from the lamp side, soft fill from the camera side (faces <= 10 W fill rule is for face fills)
area("Room_Key", C, (2.2, -1.2, 2.6), (R_(50), 0, R_(55)), 260, 2.5, col=(1.0, 0.88, 0.75))
area("Room_Fill", C, (-1.5, -2.8, 2.0), (R_(65), 0, R_(-30)), 120, 3.0, col=(0.9, 0.93, 1.0))
area("Room_Ceil", C, (0, 0.3, 2.75), (0, 0, 0), 150, 3.5, col=(1.0, 0.95, 0.88))

# ================================================================== ROAD (night, rain)
C = coll("SET_Road"); X = 100.0
asph = tex_mat("Asphalt", "asphalt_02", rough=0.25, tint=(0.55, 0.58, 0.65))
plane("Road_Asphalt", (8, 220), (X, 0, 0), asph, C, uv_scale=4.0)
lane = mat("LaneWhite", (0.9, 0.9, 0.85), 0.4)
for i in range(-36, 37):
    plane("Road_Dash%03d" % (i + 36), (0.14, 1.6), (X, i * 3.0, 0.003), lane, C)
plane("Road_EdgeL", (0.14, 220), (X - 3.7, 0, 0.003), lane, C); plane("Road_EdgeR", (0.14, 220), (X + 3.7, 0, 0.003), lane, C)
walk_m = tex_mat("Sidewalk", "gravel_concrete_03", rough=0.3, tint=(0.75, 0.75, 0.8), bump=0.2)
box("Road_Curb", (0.16, 220, 0.06), (X + 4.08, 0, 0.03), mat("Curb", (0.6, 0.6, 0.62), 0.5), C)
plane("Road_Sidewalk", (1.6, 220), (X + 4.96, 0, 0.004), walk_m, C, uv_scale=1.5)
grass = tex_mat("Verge", "brown_mud_leaves_01", rough=0.6, tint=(0.55, 0.75, 0.45), bump=0.2)
plane("Road_VergeR", (14, 220), (X + 12.76, 0, 0.002), grass, C, uv_scale=3.0)
plane("Road_VergeL", (14, 220), (X - 11.0, 0, 0.0), grass, C, uv_scale=3.0)
lampm = import_glb("Road_LampSrc", "streetlamp.glb", coll("Lib"), size=6.5)
recolor(lampm, {"uv_grid": mat("LampPole", (0.35, 0.37, 0.4), 0.4, metal=0.6)})
lampm.hide_render = True; lampm.hide_viewport = True
# arm points to -y in the source; rotate so the head hangs over the road (-x)
for i, yy in enumerate(range(-90, 100, 22)):
    o = inst(lampm, "Road_Lamp%02d" % i, C, (X + 6.0, yy, 0.0), rot=(0, 0, R_(-90)))
    l = spot("Road_LampLight%02d" % i, C, (X + 3.2, yy, 6.2), (0, 0, 0), 1400, angle=110, col=(1.0, 0.82, 0.55), blend=0.6, radius=0.25)
    bulb = mat("LampHead", (1, 0.9, 0.7), 0.3, emit=(1.0, 0.85, 0.6), estr=25)
    bh = box("Road_LampHead%02d" % i, (0.25, 0.5, 0.05), (X + 3.2, yy, 6.27), bulb, C)
firs = []
for k in "abc":
    o = lib_obj(PH + "fir_tree_01/fir_tree_01_1k.blend", "fir_tree_01_%s_LOD1" % k, coll("Lib")); o.hide_render = True; o.hide_viewport = True; firs.append(o)
shrubs = []
for k in "hig":
    o = lib_obj(PH + "shrub_01/shrub_01_1k.blend", "shrub_01_%s_LOD2" % k, coll("Lib")); o.hide_render = True; o.hide_viewport = True; shrubs.append(o)
ferns = []
for k in "abcd":
    o = lib_obj(PH + "fern_02/fern_02_1k.blend", "fern_02_%s" % k, coll("Lib")); o.hide_render = True; o.hide_viewport = True; ferns.append(o)
for i in range(70):   # tree line on the girl's side, beyond the sidewalk
    yy = -100 + i * 3.0 + random.uniform(-1, 1); xx = X + random.uniform(9.0, 22.0)
    inst(random.choice(firs), "Road_Tree%02d" % i, C, (xx, yy, 0.0), rot=(0, 0, random.uniform(0, 6.3)), scale=random.uniform(0.7, 1.0))
for i in range(50):
    yy = -100 + i * 4.0 + random.uniform(-1, 1); xx = X - random.uniform(10.0, 25.0)
    inst(random.choice(firs), "Road_TreeL%02d" % i, C, (xx, yy, 0.0), rot=(0, 0, random.uniform(0, 6.3)), scale=random.uniform(0.7, 1.0))
for i in range(160):
    yy = random.uniform(-100, 100); xx = X + random.uniform(6.2, 10.0)
    inst(random.choice(shrubs), "Road_Shrub%03d" % i, C, (xx, yy, 0.0), rot=(0, 0, random.uniform(0, 6.3)), scale=random.uniform(2.5, 4.0))
rain("Rain_Road", C, (X + 3, -20, 0.0), size=(16, 60, 8), count=14000)
rain("Rain_Road2", C, (X + 3, 30, 0.0), size=(16, 40, 8), count=9000)
area("Road_Moon", C, (X - 10, -10, 20), (R_(-35), R_(-25), 0), 4000, 30, col=(0.5, 0.62, 1.0))
def _cx(o):
    return (sum((o.matrix_world @ Vector(b) for b in o.bound_box), Vector()) / 8).x
car = import_glb("Car", "car.glb", C, size=None, keep=lambda o: _cx(o) < 200)
_d = car.dimensions; _ax = 0 if _d.x > _d.y else 1
_s = 4.7 / max(_d.x, _d.y); car.data.transform(Matrix.Scale(_s, 4))
if _ax == 0: car.data.transform(Matrix.Rotation(R_(90), 4, 'Z'))   # length along y, nose to -y checked in 04
recolor(car, {"number_plate": mat("PlateBlank", (0.85, 0.85, 0.82), 0.5), "main_body": mat("CarBlue", (0.12, 0.2, 0.45), 0.25, metal=0.4)})
car.location = (X + 1.8, 60, 0)
# =================================================================== WOODS (night run / torch search)
C = coll("SET_Woods"); X = 200.0
ground = tex_mat("ForestFloor", "forest_leaves_02", rough=0.7, tint=(0.9, 0.95, 0.85), bump=0.25)
plane("Woods_Ground", (80, 80), (X, 0, 0), ground, C, uv_scale=2.5)
for i in range(240):
    for _ in range(20):
        xx = X + random.uniform(-30, 30); yy = random.uniform(-30, 38)
        # keep running lane (x -2..2 around X, y -10..30) and search clearing (around (X+12, 10)) open
        if abs(xx - X) < 2.5 and -12 < yy < 32: continue
        if (Vector((xx, yy)) - Vector((X + 12, 10))).length < 6: continue
        break
    inst(random.choice(firs), "Woods_Tree%03d" % i, C, (xx, yy, 0), rot=(0, 0, random.uniform(0, 6.3)), scale=random.uniform(0.6, 1.0))
for i in range(420):
    xx = X + random.uniform(-22, 22); yy = random.uniform(-25, 35)
    if abs(xx - X) < 1.2 and -12 < yy < 32: continue
    inst(random.choice(shrubs + ferns), "Woods_Under%03d" % i, C, (xx, yy, 0), rot=(0, 0, random.uniform(0, 6.3)), scale=random.uniform(2.0, 3.5))
bench = lib_obj(PH + "painted_wooden_bench/painted_wooden_bench_1k.blend", "painted_wooden_bench", C, loc=(X + 11.5, 8.5, 0), rot=(0, 0, R_(20)))
trunk = lib_obj(PH + "dead_tree_trunk/dead_tree_trunk_1k.blend", "dead_tree_trunk", C, loc=(X + 9.0, 12.5, 0), rot=(0, 0, R_(70)))
rain("Rain_Woods", C, (X, 6, 0), size=(14, 40, 8), count=12000)
area("Woods_Moon", C, (X - 6, -6, 18), (R_(-30), R_(-20), 0), 9000, 25, col=(0.5, 0.62, 1.0))
area("Woods_Clearing", C, (X + 12, 8, 7), (0, 0, 0), 2200, 10, col=(0.6, 0.7, 1.0))
area("Woods_Fill", C, (X + 8, 0, 6), (R_(-50), R_(30), 0), 2500, 12, col=(0.55, 0.65, 1.0))
for yy in range(-12, 36, 3):
    for sgn in (-1, 1):
        inst(random.choice(firs), "Woods_LaneTree%02d%s" % (yy + 12, "LR"[sgn > 0]), C, (X + sgn * random.uniform(3.2, 6.5), yy + random.uniform(-1, 1), 0), rot=(0, 0, random.uniform(0, 6.3)), scale=random.uniform(0.55, 0.8))
# =================================================================== SHED (day)
C = coll("SET_Shed"); X = 300.0
plane("Shed_Grass", (60, 60), (X, 0, 0), tex_mat("ShedGround", "brown_mud_leaves_01", rough=0.8, tint=(0.75, 0.95, 0.55), bump=0.2), C, uv_scale=2.5)
siding = bpy.data.materials.new("ShedSiding"); siding.use_nodes = True; nt = siding.node_tree; P = nt.nodes["Principled BSDF"]
tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sp.inputs[0])
m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; m1.inputs[1].default_value = 1 / 0.14; nt.links.new(sp.outputs[2], m1.inputs[0])
fr_ = nt.nodes.new("ShaderNodeMath"); fr_.operation = 'FRACT'; nt.links.new(m1.outputs[0], fr_.inputs[0])
cr = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(fr_.outputs[0], cr.inputs[0])
cr.color_ramp.elements[0].color = (0.55, 0.53, 0.48, 1); cr.color_ramp.elements[1].position = 0.1; cr.color_ramp.elements[1].color = (0.96, 0.94, 0.87, 1)
nt.links.new(cr.outputs[0], P.inputs["Base Color"]); bp_ = nt.nodes.new("ShaderNodeBump"); bp_.inputs["Strength"].default_value = 0.4; bp_.inputs["Distance"].default_value = 0.01
nt.links.new(fr_.outputs[0], bp_.inputs["Height"]); nt.links.new(bp_.outputs[0], P.inputs["Normal"]); P.inputs["Roughness"].default_value = 0.6
trim = mat("ShedTrim", (0.97, 0.97, 0.95), 0.45); roofm = mat("ShedRoof", (0.25, 0.27, 0.3), 0.6)
SW, SD, SH, DW, DH = 2.4, 1.8, 2.0, 0.9, 1.85
cx, cy = X, 2.0
# walls (front wall split around the door)
box("Shed_WallBack", (SW, 0.06, SH), (cx, cy + SD / 2, SH / 2), siding, C)
box("Shed_WallL", (0.06, SD, SH), (cx - SW / 2, cy, SH / 2), siding, C); box("Shed_WallR", (0.06, SD, SH), (cx + SW / 2, cy, SH / 2), siding, C)
sidew = (SW - DW) / 2
box("Shed_FrontL", (sidew, 0.06, SH), (cx - DW / 2 - sidew / 2, cy - SD / 2, SH / 2), siding, C)
box("Shed_FrontR", (sidew, 0.06, SH), (cx + DW / 2 + sidew / 2, cy - SD / 2, SH / 2), siding, C)
box("Shed_FrontTop", (DW, 0.06, SH - DH), (cx, cy - SD / 2, DH + (SH - DH) / 2), siding, C)
for nm, dims, loc in (("TrimDL", (0.08, 0.09, DH), (cx - DW / 2 - 0.04, cy - SD / 2, DH / 2)), ("TrimDR", (0.08, 0.09, DH), (cx + DW / 2 + 0.04, cy - SD / 2, DH / 2)),
                      ("TrimDT", (DW + 0.16, 0.09, 0.08), (cx, cy - SD / 2, DH + 0.04)),
                      ("TrimC1", (0.09, 0.09, SH), (cx - SW / 2, cy - SD / 2, SH / 2)), ("TrimC2", (0.09, 0.09, SH), (cx + SW / 2, cy - SD / 2, SH / 2))):
    box("Shed_" + nm, dims, loc, trim, C)
# gable roof: two slabs
for sgn in (-1, 1):
    box("Shed_Roof" + ("L" if sgn < 0 else "R"), (SW / 2 / math.cos(R_(25)) + 0.15, SD + 0.3, 0.05), (cx + sgn * SW / 4, cy, SH + SW / 4 * math.tan(R_(25))), roofm, C, rot=(0, R_(25 * sgn), 0))
# gable triangles
gb = bpy.data.meshes.new("ShedGable"); hh = SW / 2 * math.tan(R_(25))
gb.from_pydata([(-SW / 2, 0, 0), (SW / 2, 0, 0), (0, 0, hh)], [], [(0, 1, 2)])
for yy in (cy - SD / 2, cy + SD / 2):
    g_ = bpy.data.objects.new("Shed_Gable", gb); C.objects.link(g_); g_.location = (cx, yy, SH); g_.modifiers.new("s", 'SOLIDIFY').thickness = 0.06
gb.materials.append(siding)
box("Shed_Floor", (SW - 0.1, SD - 0.1, 0.06), (cx, cy, 0.03), mat("ShedFloor", (0.55, 0.42, 0.3), 0.8), C)
# open door leaf, swung outward to the right
piv = bpy.data.objects.new("Shed_DoorPivot", None); C.objects.link(piv); piv.location = (cx + DW / 2, cy - SD / 2 - 0.03, 0)
dl = box("Shed_Door", (DW - 0.04, 0.04, DH - 0.03), (-(DW - 0.04) / 2, 0, DH / 2), siding, C); dl.parent = piv; dl.location = (-(DW - 0.04) / 2, 0, DH / 2)
piv.rotation_euler = (0, 0, R_(-105))
area("Shed_Inside", C, (cx, cy + 0.1, SH - 0.1), (0, 0, 0), 40, 1.2, col=(1.0, 0.92, 0.8))
# stuff inside: a few boxes and a shelf so the interior reads
box("Shed_Shelf", (1.8, 0.35, 0.04), (cx, cy + SD / 2 - 0.22, 1.2), mat("ShelfWood", (0.6, 0.45, 0.3), 0.7), C)
for i in range(3):
    box("Shed_Crate%d" % i, (0.4, 0.3, 0.3), (cx - 0.7 + i * 0.55, cy + SD / 2 - 0.3, 0.15 + 0.06), mat("Cardboard", (0.72, 0.52, 0.32), 0.85), C, bevel=0.01)
for i in range(28):
    a_ = random.uniform(0, 6.3); r = random.uniform(9, 25)
    inst(random.choice(firs), "Shed_Tree%02d" % i, C, (X + r * math.cos(a_), 6 + r * abs(math.sin(a_)), 0), rot=(0, 0, a_), scale=random.uniform(0.6, 0.9))
for i in range(60):
    inst(random.choice(shrubs + ferns), "Shed_Under%02d" % i, C, (X + random.uniform(-12, 12), random.uniform(0, 15), 0), rot=(0, 0, random.uniform(0, 6.3)), scale=random.uniform(2.0, 3.0))
# belongings found in the shed (generic, no text): a pencil, a marker, a hair bow, a candy wrapper
box("Shed_Pencil", (0.006, 0.17, 0.006), (X - 0.2, 1.55, 0.065), mat("PencilYellow", (0.95, 0.75, 0.1), 0.4), C, rot=(0, 0, R_(30)))
box("Shed_Marker", (0.014, 0.13, 0.014), (X + 0.15, 1.4, 0.067), mat("MarkerBlue", (0.15, 0.35, 0.85), 0.4), C, rot=(0, 0, R_(-50)))
bpy.ops.mesh.primitive_torus_add(major_radius=0.025, minor_radius=0.01, location=(X + 0.0, 1.75, 0.07)); bw = bpy.context.object; bw.name = "Shed_HairBow"
bw.data.materials.append(mat("BowPink", (0.95, 0.3, 0.6), 0.5)); link(bw, C)
sun = bpy.data.lights.new("Sun", 'SUN'); sun.energy = 0.0; sun.angle = R_(3); sun.color = (1.0, 0.95, 0.85)
so = bpy.data.objects.new("Sun", sun); sc.collection.objects.link(so); so.rotation_euler = (R_(48), R_(8), R_(-35))
# =================================================================== SITE (day)
C = coll("SET_Site"); X = 400.0
plane("Site_Dirt", (60, 60), (X, 0, 0), tex_mat("SiteDirt", "rocky_trail", rough=0.85, tint=(1.0, 0.85, 0.7), bump=0.3), C, uv_scale=2.0)
for i in range(8):
    o = lib_obj(PH + "cement_bag/cement_bag_1k.blend", "cement_bag", C, loc=(X - 2.0 + (i % 4) * 0.55, 3.0 + (i // 4) * 0.45, 0.0 + 0.0), rot=(0, 0, R_(random.uniform(-8, 8))))
bar = import_glb("Site_Barrier", "barrier.glb", C, size=2.0, axis=0, loc=(X + 2.2, 3.5, 0), rot=(0, 0, R_(-15)))
bar2 = import_glb("Site_Barrier2", "barrier.glb", C, size=2.0, axis=0, loc=(X - 3.5, 1.2, 0), rot=(0, 0, R_(70)))
# the school-crossing sign lying on the dirt: yellow pentagon with a simple walking-children picture (no text)
sign_img = bpy.data.images.new("CrossingPictogram", 512, 512, alpha=True)
import array
px = array.array('f', [0.0] * (512 * 512 * 4))
def fill_rect(x0, y0, x1, y1, col):
    for y in range(max(0, y0), min(512, y1)):
        for x in range(max(0, x0), min(512, x1)):
            i = (y * 512 + x) * 4; px[i:i + 4] = array.array('f', col)
def fill_circle(cx, cy, r, col):
    for y in range(cy - r, cy + r):
        for x in range(cx - r, cx + r):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r and 0 <= x < 512 and 0 <= y < 512:
                i = (y * 512 + x) * 4; px[i:i + 4] = array.array('f', col)
def fill_poly(pts, col):
    ys = [p[1] for p in pts]
    for y in range(int(min(ys)), int(max(ys)) + 1):
        xs = []
        for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
            if (y1 <= y < y2) or (y2 <= y < y1): xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for a, b in zip(xs[::2], xs[1::2]):
            for x in range(int(a), int(b) + 1):
                if 0 <= x < 512 and 0 <= y < 512: i = (y * 512 + x) * 4; px[i:i + 4] = array.array('f', col)
YEL = (1.0, 0.82, 0.05, 1.0); BLK = (0.08, 0.06, 0.05, 1.0)
fill_poly([(256, 500), (500, 330), (500, 12), (12, 12), (12, 330)], BLK)
fill_poly([(256, 482), (484, 324), (484, 28), (28, 28), (28, 324)], YEL)
for ox, s in ((190, 1.0), (320, 0.85)):   # two walking figures
    hx = ox; fill_circle(hx, int(330 * 1) - int(0 * s), int(26 * s), BLK)
    fill_poly([(hx - 26 * s, 300), (hx + 26 * s, 300), (hx + 30 * s, 190), (hx - 30 * s, 190)], BLK)
    fill_poly([(hx - 20 * s, 195), (hx - 4 * s, 195), (hx - 40 * s, 80), (hx - 58 * s, 85)], BLK)
    fill_poly([(hx + 4 * s, 195), (hx + 20 * s, 195), (hx + 50 * s, 85), (hx + 32 * s, 80)], BLK)
    fill_poly([(hx + 22 * s, 290), (hx + 30 * s, 275), (hx + 70 * s, 220), (hx + 60 * s, 210)], BLK)
fill_rect(60, 60, 452, 74, BLK)
sign_img.pixels = px[:]; sign_img.pack()
sm = bpy.data.materials.new("CrossingSign"); sm.use_nodes = True; nt = sm.node_tree; P = nt.nodes["Principled BSDF"]
ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = sign_img; nt.links.new(ti.outputs["Color"], P.inputs["Base Color"]); nt.links.new(ti.outputs["Alpha"], P.inputs["Alpha"])
P.inputs["Roughness"].default_value = 0.35; P.inputs["Metallic"].default_value = 0.2
bpy.ops.mesh.primitive_plane_add(size=0.9, location=(X + 0.75, -0.55, 0.012), rotation=(0, 0, R_(25))); sg = bpy.context.object; sg.name = "Site_CrossingSign"
sg.data.materials.append(sm); link(sg, C); s_ = sg.modifiers.new("t", 'SOLIDIFY'); s_.thickness = 0.008
sgb = box("Site_SignBack", (0.86, 0.86, 0.004), (X + 0.75, -0.55, 0.006), mat("SignMetal", (0.6, 0.62, 0.65), 0.4, metal=0.7), C, rot=(0, 0, R_(25)))
# the found bag: pink book bag wrapped in clear plastic (own model + downloaded bag)
for i in range(10):
    inst(random.choice(firs), "Site_Tree%02d" % i, C, (X + random.uniform(-25, 25), random.uniform(14, 30), 0), rot=(0, 0, random.uniform(0, 6.3)), scale=random.uniform(0.6, 0.9))
# =================================================================== WALL (portrait)
C = coll("SET_Wall"); X = 500.0
wallm = mat("WarmWall", (0.42, 0.28, 0.18), 0.85)
nt = wallm.node_tree; P = nt.nodes["Principled BSDF"]; ns = nt.nodes.new("ShaderNodeTexNoise"); ns.inputs["Scale"].default_value = 3.0
cr = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(ns.outputs["Fac"], cr.inputs[0]); cr.color_ramp.elements[0].color = (0.36, 0.23, 0.15, 1); cr.color_ramp.elements[1].color = (0.5, 0.34, 0.22, 1)
nt.links.new(cr.outputs[0], P.inputs["Base Color"])
plane("Wall_Back", (6, 6), (X, 0.05, 2.5), wallm, C, rot=(R_(90), 0, R_(180)))
# frame moulding: a bevelled rectangle ring (our own), photo plane inside
fw, fh, fb = 0.62, 0.78, 0.07
fr = mat("FrameWood", (0.78, 0.68, 0.5), 0.45)
for nm, dims, loc in (("T", (fw + 2 * fb, 0.045, fb), (0, 0, fh / 2 + fb / 2)), ("B", (fw + 2 * fb, 0.045, fb), (0, 0, -fh / 2 - fb / 2)),
                      ("L", (fb, 0.045, fh), (-fw / 2 - fb / 2, 0, 0)), ("R", (fb, 0.045, fh), (fw / 2 + fb / 2, 0, 0))):
    o = box("Frame_" + nm, dims, (X + loc[0], 0.0, 2.5 + loc[2]), fr, C, bevel=0.012)
mat_board = mat("FrameMat", (0.93, 0.91, 0.86), 0.7)
box("Frame_Mat", (fw, 0.01, fh), (X, 0.012, 2.5), mat_board, C)
ph_m = bpy.data.materials.new("PortraitPhoto"); ph_m.use_nodes = True
bpy.ops.mesh.primitive_plane_add(size=1, location=(X, -0.0, 2.5), rotation=(R_(90), 0, 0)); po = bpy.context.object; po.name = "Frame_Photo"
po.scale = (fw * 0.82, fh * 0.84, 1); po.data.materials.append(ph_m); link(po, C)
spot("Wall_Picture", C, (X + 0.3, -1.6, 4.2), (R_(42), 0, R_(10)), 500, angle=35, col=(1.0, 0.82, 0.6), blend=0.8, radius=0.3)
area("Wall_Fill", C, (X - 1.5, -3.0, 2.2), (R_(85), 0, R_(-30)), 60, 2.0, col=(1.0, 0.9, 0.8))
# =================================================================== world, colour
w = bpy.data.worlds.new("AshaWorld"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (0.03, 0.045, 0.09, 1); bg.inputs["Strength"].default_value = 1.0
sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920; sc.render.fps = 60
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("SETS_DONE")
