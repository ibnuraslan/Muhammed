"""PopeShot animation: characters, crowd, x-ray, lights, one continuous camera.
blender -b scene.blend --python 03_animate.py -- <pipeline_dir> <out.blend>"""
import sys, os, math, random, bpy, bmesh
from mathutils import Vector, Matrix, Quaternion, Euler
a = sys.argv[sys.argv.index("--") + 1:]
PIPE, OUT = a[0], a[1]
exec(open(os.path.join(PIPE, "anim_lib.py")).read())
random.seed(31)
sc = bpy.context.scene
O = bpy.data.objects
FPS = 60
def F(t): return 1 + round(t * FPS)

def set_interp(o, frame, kind='CONSTANT', paths=None):
    ad = o.animation_data
    if not ad or not ad.action: return
    for fc in fcurves(ad.action):
        if paths and fc.data_path not in paths: continue
        for kp in fc.keyframe_points:
            if abs(kp.co.x - frame) < 0.5: kp.interpolation = kind
def fcurves(act):
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []):
                out += list(cb.fcurves)
    if not out and hasattr(act, "fcurves"): out = list(act.fcurves)
    return out
def key_obj(o, f, loc=None, rot=None, interp='BEZIER'):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = rot; o.keyframe_insert("rotation_euler", frame=f)
    set_interp(o, f, interp, ("location", "rotation_euler"))
def key_vis(o, keys):
    for f, vis in keys:
        o.hide_render = not vis; o.keyframe_insert("hide_render", frame=f)
        o.hide_viewport = not vis; o.keyframe_insert("hide_viewport", frame=f)
    set_interp(o, -1)
    for fc in fcurves(o.animation_data.action):
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
def yaw_to(dx, dy): return math.degrees(math.atan2(dx, -dy))   # MPFB faces -Y
def ray_down(obj, x, y, z0=5.0):
    dg = bpy.context.evaluated_depsgraph_get(); ev_ = obj.evaluated_get(dg)
    inv = obj.matrix_world.inverted()
    ok, loc, n, i = ev_.ray_cast(inv @ Vector((x, y, z0)), (inv.to_3x3() @ Vector((0, 0, -1))).normalized())
    return (obj.matrix_world @ loc).z if ok else None
def bone_w(rig, b, part="head"):
    pb = rig.pose.bones[b]; return rig.matrix_world @ (pb.head if part == "head" else pb.tail)

# ------------------------------------------------------------------ materials needed here
def emis(name, col, s):
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree.nodes
    for x in list(n): n.remove(x)
    e = n.new('ShaderNodeEmission'); e.inputs['Color'].default_value = tuple(col) + (1,); e.inputs['Strength'].default_value = s
    o = n.new('ShaderNodeOutputMaterial'); m.node_tree.links.new(e.outputs[0], o.inputs[0]); return m, e

# ------------------------------------------------------------------ cassock (skirt), skullcap, gloves, masks: fitted to the MPFB body
def body_of(rig): return next(c for c in rig.children if c.name.endswith(".body"))
def transfer_weights(dst, body, rig):
    for vg in body.vertex_groups: dst.vertex_groups.new(name=vg.name)
    dt = dst.modifiers.new("dt", 'DATA_TRANSFER'); dt.object = body; dt.use_vert_data = True
    dt.data_types_verts = {'VGROUP_WEIGHTS'}; dt.vert_mapping = 'POLYINTERP_NEAREST'
    bpy.context.view_layer.objects.active = dst
    bpy.ops.object.datalayout_transfer(modifier="dt"); bpy.ops.object.modifier_apply(modifier="dt")
    am = dst.modifiers.new("arm", 'ARMATURE'); am.object = rig
    dst.parent = rig
def cassock(rig, mat):
    body = body_of(rig); vs = [v.co for v in body.data.vertices]
    H = max(v.z for v in vs); seg = 72
    zs = [0.07 * H + (0.6 * H - 0.07 * H) * i / 22 for i in range(23)]
    prof = []
    cy = rig.data.bones["root"].head_local.y
    for z in zs:
        band = [v for v in vs if abs(v.z - z) < 0.02 and abs(v.x) < 0.32]
        rx = max((abs(v.x) for v in band), default=0.15); ry = max((abs(v.y - cy) for v in band), default=0.12)
        prof.append([z, rx + 0.05, ry + 0.06])
    for i in range(len(prof) - 2, -1, -1):        # only widen going down (hangs from the hips)
        prof[i][1] = max(prof[i][1], prof[i + 1][1] + 0.004); prof[i][2] = max(prof[i][2], prof[i + 1][2] + 0.003)
    me = bpy.data.meshes.new(rig.name + "_Cassock"); bm = bmesh.new(); rings = []
    for k, (z, rx, ry) in enumerate(prof):
        ring = []
        for i in range(seg):
            t = 2 * math.pi * i / seg
            fold = 1 + (0.035 + 0.05 * (1 - k / len(prof))) * math.sin(13 * t + 0.9 * math.sin(3 * t)) * (0.6 + 0.4 * math.sin(5 * t + k * 0.3))
            ring.append(bm.verts.new((rx * fold * math.cos(t), cy + ry * fold * math.sin(t), z)))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(seg): bm.faces.new((r0[i], r0[(i + 1) % seg], r1[(i + 1) % seg], r1[i]))
    bm.to_mesh(me); o = bpy.data.objects.new(rig.name + "_Cassock", me); me.materials.append(mat)
    for p in me.polygons: p.use_smooth = True
    for c in rig.users_collection: c.objects.link(o)
    transfer_weights(o, body, rig)
    s = o.modifiers.new("sol", 'SOLIDIFY'); s.thickness = 0.012
    o.modifiers.new("sub", 'SUBSURF').levels = 1
    # sash at the waist
    return o
def shell(rig, name, pred, offset, mat, keep_groups=True):
    body = body_of(rig)
    me = body.data.copy(); o = bpy.data.objects.new(rig.name + "_" + name, me)
    for c in rig.users_collection: c.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(me)
    dl = bm.verts.layers.deform.active
    names = {vg.index: vg.name for vg in body.vertex_groups}
    keep = set()
    for f in bm.faces:
        if all(pred(v.co, ({names[k]: w for k, w in v[dl].items()} if dl else {})) for v in f.verts): keep.add(f)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f not in keep], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.normal_update()
    for v in bm.verts: v.co += v.normal * offset
    bm.to_mesh(me); me.materials.clear(); me.materials.append(mat)
    for vg in body.vertex_groups: o.vertex_groups.new(name=vg.name)
    o.parent = rig; am = o.modifiers.new("arm", 'ARMATURE'); am.object = rig
    s = o.modifiers.new("sol", 'SOLIDIFY'); s.thickness = 0.004; s.offset = 1
    o.modifiers.new("sub", 'SUBSURF').levels = 1
    return o
HANDG = ("wrist", "finger", "metacarpal")
def is_hand(co, w): return sum(v for k, v in w.items() if k.startswith(HANDG)) > 0.5
skull_m = bpy.data.materials["WhiteWool"]
latex = bpy.data.materials.new("Latex"); latex.use_nodes = True
lb = latex.node_tree.nodes["Principled BSDF"]; lb.inputs['Base Color'].default_value = (0.75, 0.7, 0.55, 1); lb.inputs['Roughness'].default_value = 0.3
lb.inputs['Subsurface Weight'].default_value = 0.3
maskm = bpy.data.materials["SurgDrape"]

def setup_heroes():
    pope = O["Pope"]
    cassock(pope, bpy.data.materials["WhiteWool"])
    hb = pope.data.bones["head"]; ht = hb.tail_local
    shell(pope, "Zucchetto", lambda co, w: co.z > ht.z - 0.075 and co.y > ht.y - 0.06, 0.03, skull_m)
    for nm in ("SurgA", "SurgB", "SurgC", "Nurse"):
        r = O[nm]; hb = r.data.bones["head"]; hh, ht = hb.head_local, hb.tail_local
        shell(r, "Gloves", is_hand, 0.003, latex)
        shell(r, "Cap", lambda co, w, ht=ht: co.z > ht.z - 0.09, 0.025, maskm)
        shell(r, "Mask", lambda co, w, hh=hh: hh.z - 0.06 < co.z < hh.z + 0.075 and co.y < hh.y - 0.04 and abs(co.x) < 0.075, 0.012, bpy.data.materials["WhiteWool"])
        for c in r.children:     # hide hair under the cap
            if c.name.split(".")[-1] in ("bob01",): c.hide_render = True
setup_heroes()
pope_ = O["Pope"]
for ch in pope_.children:
    key = ch.name.split(".")[-1]
    if key in ("male_elegantsuit01", "short02", "eyebrow001"):
        for i, m in enumerate(ch.data.materials):
            if not m or not m.node_tree: continue
            m2 = m.copy(); m2.name = "Pope_" + key; ch.data.materials[i] = m2
            nt = m2.node_tree; bs = next(x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED')
            tex = next((x for x in nt.nodes if x.type == 'TEX_IMAGE' and x.image and "diffuse" in x.image.name.lower()), None)
            if key == "male_elegantsuit01":
                wl = bpy.data.materials["WhiteWool"].node_tree
                nl = nt.nodes.new('ShaderNodeTexNoise'); nl.inputs['Scale'].default_value = 220; nl.inputs['Detail'].default_value = 8
                mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.78; mr.inputs['To Max'].default_value = 0.9
                nt.links.new(nl.outputs['Fac'], mr.inputs['Value'])
                cm = nt.nodes.new('ShaderNodeCombineColor'); nt.links.new(mr.outputs['Result'], cm.inputs[0]); nt.links.new(mr.outputs['Result'], cm.inputs[1])
                m3 = nt.nodes.new('ShaderNodeMath'); m3.operation = 'MULTIPLY'; m3.inputs[1].default_value = 0.95; nt.links.new(mr.outputs['Result'], m3.inputs[0]); nt.links.new(m3.outputs[0], cm.inputs[2])
                nt.links.new(cm.outputs[0], bs.inputs['Base Color']); bs.inputs['Roughness'].default_value = 0.85
            elif tex:
                bw = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(tex.outputs['Color'], bw.inputs[0])
                mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.55; mr.inputs['To Max'].default_value = 0.85
                nt.links.new(bw.outputs[0], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], bs.inputs['Base Color'])
    if key == "body" and ch.data.shape_keys:
        for kb in ch.data.shape_keys.key_blocks:
            if "-old" in kb.name: kb.value = min(1.0, kb.value * 1.6 + 0.2)
# patch shirt prints: clothes take a solid tinted fabric (prints removed), keep the normal maps
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.parent or o.parent.type != 'ARMATURE': continue
    key = o.name.split(".")[-1]
    if not any(k in key for k in ("casualsuit", "sportsuit", "worksuit")): continue
    for m in o.data.materials:
        if not m or not m.node_tree: continue
        for nd in m.node_tree.nodes:
            if nd.type == 'MIX' and nd.blend_type == 'MULTIPLY' and nd.inputs['A'].links:
                hs = nd.inputs['A'].links[0].from_node
                if hs.type == 'HUE_SAT':
                    blur = m.node_tree.nodes.new('ShaderNodeTexNoise'); blur.inputs['Scale'].default_value = 300; blur.inputs['Detail'].default_value = 4
                    mr = m.node_tree.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.42; mr.inputs['To Max'].default_value = 0.55
                    m.node_tree.links.new(blur.outputs['Fac'], mr.inputs['Value']); m.node_tree.links.new(mr.outputs['Result'], nd.inputs['A'])

# ------------------------------------------------------------------ rigs
HUM = {}
for nm in ("Pope", "Prisoner", "AideA", "AideB", "GuardA", "GuardB", "SurgA", "SurgB", "SurgC", "Nurse"):
    rig = O[nm]; loc = rig.location.copy()
    R = make_human_ctrl(rig); rig.location = loc
    HUM[nm] = Human(R)
P = HUM["Pope"]
def stand(h, f, pos=None, yaw=0.0, flex=0.0, twist=0.0, side=0.0, head=(0.0, 0.0), sway=0.0, feet=True, crouch=0.0, spread=1.0):
    rh = h.root_head
    p = Vector((rh.x + sway * math.sin(f * 0.05), rh.y, rh.z - crouch)) if pos is None else pos
    h.key_root(f, p, yaw=0.0, flex=flex * 0.3, side=side * 0.3)
    h.key_spine(f, flex=flex, twist=twist, side=side, head=head)
    if feet:
        for s in "LR":
            xy = Vector((h.ankle[s].x * spread, h.ankle[s].y)); h.key_foot(s, f, xy, 0.0)
def hand_at(h, s, f, W, d=(0, 0, -1), n=(0, -1, 0), pole=None):
    sx = 1 if s == "L" else -1
    if pole is None: pole = Vector((W[0] + 0.3 * sx, W[1] + 0.5, W[2] - 0.2))
    h.key_hand(s, f, Vector(W), Vector(d), Vector(n), pole=Vector(pole))
def arms_down(h, f, sw=0.0):
    for s, sx in (("L", 1), ("R", -1)):
        hand_at(h, s, f, (sx * 0.24, -0.02 + sw * math.sin(f * 0.07 + sx), 0.86), d=(0, 0, -1), n=(sx, 0, 0))
def face(rig, f, brow=0.0, lids=0.0, jaw=0.0, smile=0.0):
    """MPFB face bones: brow>0 raised (<0 frown), lids>0 closing, jaw open (deg), smile>0 corners up"""
    R = Rig(rig)
    for s in "LR":
        sx = 1 if s == "L" else -1
        for b in ("oculi01." + s, "oculi02." + s):
            pb = R.PB[b]; pb.location = (0, 0, 0); pb.location.z = 0; pb.location = Vector((0, brow * 0.006, 0)); pb.keyframe_insert("location", frame=f)
        for b in ("orbicularis03." + s,):
            R.key_rot(b, f, [("X", lids * 25)])
        for b in ("risorius03." + s,):
            pb = R.PB[b]; pb.location = Vector((0, smile * 0.005, 0)); pb.keyframe_insert("location", frame=f)
    R.key_rot("jaw", f, [("X", -jaw)])

# ------------------------------------------------------------------ JEEP + POPE (square) frames 1..630
jeep = O["jeep"]; jeep.rotation_euler = (0, 0, R_(90))
JY = pchip([(1, -12.0), (120, -7.6), (250, -3.6), (330, -2.2), (380, -2.0)])
for f in range(1, 640, 4):
    key_obj(jeep, f, loc=(0, JY(f) if f < 380 else -2.0, 0), rot=(0, 0, R_(90)))
for fc in fcurves(jeep.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
ev(1)
floor = None
for z0 in (1.6, 1.4):
    floor = ray_down(jeep, 0.0, -12.0 - 0.9, z0) or floor
FLOOR = floor if floor and floor < 1.2 else 0.62
print("JEEP floor", FLOOR)
pope = O["Pope"]
POPE_YAW = R_(yaw_to(-0.95, 0.35))
REAR = -0.85       # stands at the rear of the bed
def pope_root_obj(f):
    return Vector((0.0, (JY(f) if f < 380 else -2.0) + REAR, FLOOR))
# grab rail in front of him (metal, mounted on the jeep)
rail_m = bpy.data.materials["MetalPlate"]
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.018, depth=0.9, location=(0, 0, 0), rotation=(0, R_(90), 0))
rail = bpy.context.object; rail.name = "GrabRail"; rail.hide_render = True; rail.data.materials.append(rail_m)
for c in list(rail.users_collection): c.objects.unlink(rail)
bpy.data.collections["Square"].objects.link(rail)
# rail in Pope-local terms: ahead of him at 1.0 m, built in jeep space
cr = rail.constraints.new('CHILD_OF'); cr.target = jeep
ev(1); cr.inverse_matrix = jeep.matrix_world.inverted()
rail.location = (0.0, -12.0 + REAR - 0.0, FLOOR + 1.0)
RAIL_LOCAL = None
for f in range(1, 506, 4):
    key_obj(pope, f, loc=pope_root_obj(f), rot=(0, 0, POPE_YAW))
for fc in fcurves(pope.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
# rail world position relative to pope (local) : in front of him at hip height
RL = Vector((0.12, -0.36, 1.02))
Mrot = Matrix.Rotation(POPE_YAW, 4, 'Z')
rail.location = (Mrot @ RL) + Vector((0, -12.0 + REAR, FLOOR)); rail.rotation_euler = (0, R_(90), POPE_YAW)
# Pope: waving with the right hand, left hand on the rail; slow-motion from 255 to 330 (the bullet ride)
def tw(f):
    """story time warp for the square: slow motion 255..500 (x-ray), returns 'acting' frame"""
    if f < 255: return f
    if f < 500: return 255 + (f - 255) * 0.12
    return 284 + (f - 500)
for f in list(range(1, 505, 3)) + [505]:
    t = tw(f)
    wave = math.sin(t * 0.16)
    stand(P, f, flex=4 + 2 * math.sin(t * 0.03), twist=8 * math.sin(t * 0.02), head=(-4 + 3 * math.sin(t * 0.05), 10 * math.sin(t * 0.025)))
    hand_at(P, "R", f, (-0.32 + 0.07 * wave, -0.12, 1.72 + 0.03 * math.cos(t * 0.16)), d=(0, 0, 1), n=(0, -1, 0.2), pole=(-0.6, 0.3, 1.2))
    if f < 200:
        hand_at(P, "L", f, (0.13, -0.33, 1.06), d=(0, -0.6, -0.8), n=(0, -0.2, -1), pole=(0.6, 0.2, 1.0))
    else:   # raises left hand too (greeting) -> hit in the hand
        u = smooth((t - 200) / 30)
        hand_at(P, "L", f, (0.13 + 0.2 * u, -0.33 + 0.05 * u, 1.06 + 0.5 * u), d=(0, -0.6 * (1 - u), -0.8 + 1.8 * u), n=(0, -1, 0), pole=(0.6, 0.2, 1.0))
    face(pope, f, brow=0.4, smile=0.6)
# hit + collapse 500..630 into the aides
for f in range(505, 640, 3):
    u = smooth((f - 500) / 25); v = smooth((f - 520) / 70)
    rh = P.root_head
    p = Vector((rh.x - 0.05 * v, rh.y + 0.25 * v, rh.z - 0.45 * v - 0.04 * u))
    P.key_root(f, p, flex=10 * u - 5 * v, side=-6 * v)
    P.key_spine(f, flex=28 * u - 20 * v, twist=-10 * v, side=-8 * v, head=(25 * u - 35 * v, -15 * v))
    for s in "LR":
        P.key_foot(s, f, Vector((P.ankle[s].x * (1 + 0.4 * v), P.ankle[s].y - 0.12 * v)), 0.0)
    hand_at(P, "L", f, (0.08, -0.22 + 0.06 * v, 1.0 - 0.25 * v), d=(-0.6, -0.2, -0.6), n=(0, 1, 0), pole=(0.6, -0.3, 1.0))
    hand_at(P, "R", f, (-0.06, -0.2 + 0.06 * v, 0.98 - 0.25 * v), d=(0.6, -0.2, -0.6), n=(0, 1, 0), pole=(-0.6, -0.3, 1.0))
    face(pope, f, brow=-0.8 * u, lids=0.6 * v, jaw=10 * u)
# aides stand behind him in the bed, catch under the arms
AIDES = (("AideA", Vector((0.42, 0.55))), ("AideB", Vector((-0.42, 0.55))))
for nm, off in AIDES:
    r = O[nm]; h = HUM[nm]
    yaw = POPE_YAW
    for f in range(1, 640, 4):
        key_obj(r, f, loc=pope_root_obj(min(f, 505)) + Mrot.to_3x3() @ Vector((off.x, off.y, 0)), rot=(0, 0, yaw))
    for fc in fcurves(r.animation_data.action):
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
for f in list(range(1, 640, 3)):
    for nm, off in AIDES:
        r = O[nm]; h = HUM[nm]; sx = 1 if off.x > 0 else -1
        t = tw(f) if f < 505 else f
        if f < 505:
            stand(h, f, flex=3, head=(0, 15 * math.sin(t * 0.02 + sx)), twist=6 * math.sin(t * 0.017))
            arms_down(h, f, sw=0.01)
        else:
            ev(f)
            # Pope armpit (upperarm01 head) in the aide's local space
            side = "R" if sx < 0 else "L"
            W = r.matrix_world.inverted() @ bone_w(pope, "upperarm01." + side)
            W2 = r.matrix_world.inverted() @ bone_w(pope, "spine02")
            u = smooth((f - 505) / 18)
            stand(h, f, flex=10 + 25 * u, head=(20 * u, 0), crouch=0.25 * u)
            base_o = Vector((sx * 0.24, -0.02, 0.86))
            hand_at(h, "R" if sx < 0 else "L", f, tuple(base_o.lerp(W + Vector((0, 0.04, -0.05)), u)), d=(-sx * 0.3, -0.5, 0.5), n=(-sx, 0, 0))
            hand_at(h, "L" if sx < 0 else "R", f, tuple(Vector((-sx * 0.24, -0.02, 0.86)).lerp(W2 + Vector((sx * 0.08, 0.1, 0)), u)), d=(0, -1, 0), n=(0, 1, 0))
        face(r, f, brow=(-0.5 if f > 505 else 0.0), jaw=(8 if f > 510 else 0))
# guards: walk beside, then rush in
for i, nm in enumerate(("GuardA", "GuardB")):
    r = O[nm]; h = HUM[nm]; sx = 1 if i == 0 else -1
    r.location = (0, 0, 0); r.rotation_euler = (0, 0, 0)
    path = lambda f, sx=sx: Vector((sx * 1.4, (JY(tw(f)) if tw(f) < 380 else -2.0) + 0.4, 0)) if f < 505 else \
        Vector((sx * (1.4 - 0.5 * smooth((f - 505) / 60)), -2.0 + 0.4 - 0.6 * smooth((f - 505) / 60), 0))
    h.walk(path, lambda f: 180.0 if f < 505 else 180.0 + sx * 40, 1, 638, stride=0.7, step=3)
    for f in range(1, 640, 6):
        arms_down(h, f, sw=0.06)

# ------------------------------------------------------------------ CROWD (instances of 8 base people, FK acting)
def copy_human(src, name):
    r = src.copy(); r.name = name; r.animation_data_clear()
    for c in src.users_collection: c.objects.link(r)
    for ch in src.children:
        if ch.type != 'MESH': continue
        cc = ch.copy(); cc.name = name + "." + ch.name.split(".")[-1]; cc.parent = r
        for m in cc.modifiers:
            if m.type == 'ARMATURE': m.object = r
        for c in ch.users_collection: c.objects.link(cc)
    return r
crowd = []
for side in (-1, 1):
    for row in range(3):
        for k in range(8):
            y = -17 + k * 3.9 + random.uniform(-0.6, 0.6) + row * 1.3
            x = side * (3.5 + row * 0.85 + random.uniform(-0.15, 0.15))
            crowd.append((x, y))
SHOOTER = Vector((-3.45, 1.6))
crowd = [c for c in crowd if (Vector(c) - SHOOTER).length > 0.8]
CR = []
for i, (x, y) in enumerate(crowd):
    src = O["Crowd%d" % (i % 8)]
    r = src if i < 8 else copy_human(src, "CrowdP%d" % i)
    CR.append((r, x, y, random.choice(("wave", "wave", "cheer", "idle", "clap")), random.uniform(0, 6)))
shooter = copy_human(O["Crowd6"], "Shooter")
def fk_pose(R, f, kind, ph, t, gasp=0.0, look=0.0):
    w = math.sin(t * 0.18 + ph); s = math.sin(t * 0.04 + ph)
    for nm_, wgt in Human.SPINE_W.items():
        R.key_rot(nm_, f, [("X", (4 * s - 18 * gasp) * wgt), ("Z", (8 * math.sin(t * 0.02 + ph) + look) * wgt)])
    for nm_, wgt in Human.HEAD_W.items():
        R.key_rot(nm_, f, [("X", (-6 - 10 * gasp) * wgt), ("Z", (10 * math.sin(t * 0.03 + ph) + look) * wgt)])
    # arms: angles relative to the A-pose (Y rot lowers/raises sideways, X swings forward)
    if gasp > 0.01:
        aL = ("Y", 40 - 60 * gasp); aR = ("Y", -40 + 60 * gasp)
        R.key_rot("upperarm01.L", f, [aL, ("X", -55 * gasp)]); R.key_rot("upperarm01.R", f, [aR, ("X", -55 * gasp)])
        R.key_rot("lowerarm01.L", f, [("X", -120 * gasp), ("Z", 30 * gasp)]); R.key_rot("lowerarm01.R", f, [("X", -120 * gasp), ("Z", -30 * gasp)])
        return
    if kind == "wave":
        R.key_rot("upperarm01.R", f, [("Y", -140 + 10 * w)]); R.key_rot("lowerarm01.R", f, [("Y", -20 + 25 * w)])
        R.key_rot("upperarm01.L", f, [("Y", 42)]); R.key_rot("lowerarm01.L", f, [("X", -10)])
    elif kind == "cheer":
        R.key_rot("upperarm01.R", f, [("Y", -125 + 12 * w)]); R.key_rot("upperarm01.L", f, [("Y", 125 - 12 * w)])
        R.key_rot("lowerarm01.R", f, [("Y", -15)]); R.key_rot("lowerarm01.L", f, [("Y", 15)])
    elif kind == "clap":
        c = 0.5 + 0.5 * math.sin(t * 0.35 + ph)
        R.key_rot("upperarm01.L", f, [("Y", 30), ("X", -45)]); R.key_rot("upperarm01.R", f, [("Y", -30), ("X", -45)])
        R.key_rot("lowerarm01.L", f, [("X", -70), ("Z", 40 + 20 * c)]); R.key_rot("lowerarm01.R", f, [("X", -70), ("Z", -40 - 20 * c)])
    else:
        R.key_rot("upperarm01.L", f, [("Y", 42 + 3 * s)]); R.key_rot("upperarm01.R", f, [("Y", -42 - 3 * s)])
        R.key_rot("lowerarm01.L", f, [("X", -15)]); R.key_rot("lowerarm01.R", f, [("X", -15)])
for pb in shooter.pose.bones: pb.rotation_mode = 'QUATERNION'
for (r, x, y, kind, ph) in CR:
    for pb in r.pose.bones: pb.rotation_mode = 'QUATERNION'
    R = Rig(r)
    # square: face the lane; years later (balcony beat) the same people stand below the balcony facing the facade
    yaw_sq = R_(yaw_to(-x, 0.6 * random.uniform(-1, 1)))
    bx, by = random.uniform(-9, 9), random.uniform(18, 31)
    key_obj(r, 1, loc=(x, y, 0), rot=(0, 0, yaw_sq), interp='CONSTANT')
    key_obj(r, 700, loc=(bx, by, 0), rot=(0, 0, R_(yaw_to(-bx * 0.2, 33 - by)) + random.uniform(-0.3, 0.3)), interp='CONSTANT')
    for f in list(range(1, 640, 6)) + list(range(700, 1020, 6)):
        t = tw(f) if f < 640 else f
        g = smooth((f - 512) / 18) if 505 < f < 640 else 0.0
        look = 0.0
        fk_pose(R, f, kind if f < 640 else random.choice(("wave", "cheer", "clap")) if f == 700 else kind, ph, t, gasp=g)
# shooter: in the second row on the left, gun hand rising from the crowd (seen from behind)
Rs = Rig(shooter)
key_obj(shooter, 1, loc=(SHOOTER.x, SHOOTER.y, 0), rot=(0, 0, R_(yaw_to(1.0, -0.9))), interp='CONSTANT')
key_obj(shooter, 700, loc=(0, 0, -60), interp='CONSTANT')
for f in range(1, 640, 3):
    t = tw(f); u = smooth((t - 20) / 60)
    for nm_, wgt in Human.SPINE_W.items(): Rs.key_rot(nm_, f, [("X", 6 * u * wgt)])
    Rs.key_rot("upperarm01.R", f, [("Y", -40 + 10 * u), ("X", -95 * u)])
    Rs.key_rot("lowerarm01.R", f, [("X", -8 * u)])
    Rs.key_rot("upperarm01.L", f, [("Y", 42)])
    kick = math.exp(-max(0, f - 255) / 6.0) if f >= 255 else 0.0
    Rs.key_rot("wrist.R", f, [("X", 25 * kick)])
pistol = O["pistol"]
pc = pistol.constraints.new('CHILD_OF'); pc.target = shooter; pc.subtarget = "wrist.R"
ev(300)
wr = shooter.pose.bones["wrist.R"]; fw = shooter.pose.bones["finger3-1.R"]
Wm = shooter.matrix_world @ wr.matrix
gp = shooter.matrix_world @ (fw.head)
fwd = (shooter.matrix_world.to_3x3() @ (wr.tail - wr.head)).normalized()
pistol.matrix_world = Matrix.Translation(gp - fwd * 0.03) @ (fwd.to_track_quat('Y', 'Z').to_matrix().to_4x4())
pc.inverse_matrix = Wm.inverted()
ev(300)
MUZZLE = pistol.matrix_world @ Vector((0, 0.11, 0.04))
# muzzle flash (two short flashes: 255 slow-mo shot... flash sprite + light)
fl = bpy.data.objects.new("MuzzleLight", bpy.data.lights.new("MuzzleLight", 'POINT')); bpy.data.collections["Square"].objects.link(fl)
fl.data.color = (1.0, 0.75, 0.4); fl.location = MUZZLE; fl.data.shadow_soft_size = 0.05
for f, e in ((1, 0), (254, 0), (256, 800), (262, 300), (275, 0)):
    fl.data.energy = e; fl.data.keyframe_insert("energy", frame=f)
fm_, fe = emis("FlashMat", (1.0, 0.8, 0.45), 0.0)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.06, location=MUZZLE); flash = bpy.context.object; flash.name = "MuzzleFlash"
flash.data.materials.append(fm_); flash.scale = (1, 2.5, 1)
tx = bpy.data.textures.new("FlashNoise", 'CLOUDS'); tx.noise_scale = 0.03
dmod = flash.modifiers.new("d", 'DISPLACE'); dmod.texture = tx; dmod.strength = 0.05
for f, e in ((1, 0), (254, 0), (256, 60), (262, 25), (272, 0)):
    fe.inputs['Strength'].default_value = e; fe.inputs['Strength'].keyframe_insert("default_value", frame=f)
flash.visible_shadow = False

# ------------------------------------------------------------------ X-RAY (Pope torso + left hand)
pope = O["Pope"]
def child_of(o, rig, bone, M):
    o.matrix_world = M
    c = o.constraints.new('CHILD_OF'); c.target = rig; c.subtarget = bone
    ev(); c.inverse_matrix = (rig.matrix_world @ rig.pose.bones[bone].matrix).inverted()
    o.matrix_world = M
def rest_world(rig, M):    # place anatomy in rest coords then attach at current frame via bones
    return M
ev(330)
XC = bpy.data.objects.new("XRayTorso", None); bpy.data.collections["XRay"].objects.link(XC)
XH = bpy.data.objects.new("XRayHand", None); bpy.data.collections["XRay"].objects.link(XH)
sp4 = pope.pose.bones["spine04"]
Msp = pope.matrix_world @ sp4.matrix
child_of(XC, pope, "spine04", Msp @ Matrix.Translation(Vector((0, 0.06, -0.02))))
wl = pope.pose.bones["wrist.L"]; Mwl = pope.matrix_world @ wl.matrix
child_of(XH, pope, "wrist.L", Mwl @ Matrix.Translation(Vector((0, 0.06, 0))))
# anatomy: build in the Pope's rest frame then attach with the bone's current matrix
def attach_rest(o, bone, restM):
    """restM: object matrix in armature rest space"""
    B = pope.data.bones[bone]; PBm = pope.pose.bones[bone].matrix
    o.matrix_world = pope.matrix_world @ PBm @ B.matrix_local.inverted() @ restM
    c = o.constraints.new('CHILD_OF'); c.target = pope; c.subtarget = bone
    c.inverse_matrix = (pope.matrix_world @ PBm).inverted()
    o.matrix_world = pope.matrix_world @ PBm @ B.matrix_local.inverted() @ restM
skel, aorta, guts, hand = O["skeleton"], O["aorta"], O["guts"], O["handbones"]
H = max(v.co.z for v in body_of(pope).data.vertices)
attach_rest(skel, "spine04", Matrix.Translation((0, 0.03, 0)) @ Matrix.Scale(H / 1.70 * 0.98, 4) @ Matrix.Rotation(R_(180), 4, 'Z'))
attach_rest(aorta, "spine04", Matrix.Translation((0.0, 0.03, 0.86)) @ Matrix.Rotation(R_(180), 4, 'Z'))
attach_rest(guts, "spine04", Matrix.Translation((0.0, -0.03, 0.88)) @ Matrix.Scale(1.0, 4) @ Matrix.Rotation(R_(180), 4, 'Z'))
wb = pope.data.bones["wrist.L"]; fb = pope.data.bones["finger3-1.L"]
dirh = (fb.head_local - wb.head_local).normalized()
hand.data.transform(Matrix.Translation((0, 0, 0)))
attach_rest(hand, "wrist.L", Matrix.Translation(wb.head_local + dirh * 0.0) @ dirh.to_track_quat('Z', 'Y').to_matrix().to_4x4() @ Matrix.Translation((0, 0, 0.0)))
for o in (skel, aorta, guts, hand):
    for p in o.data.polygons: p.use_smooth = True
XR_T = ((1, 0.0), (322, 0.0), (330, 1.0), (488, 1.0), (500, 0.0), (1395, 0.0), (1410, 1.0), (1515, 1.0), (1535, 0.0))
XR_H = ((1, 0.0), (420, 0.0), (430, 1.0), (488, 1.0), (500, 0.0))
def mask_nodes(nt, xr_t=True):
    n, l = nt.nodes, nt.links
    def sph(empty, r0, r1, valname, keys):
        tc = n.new('ShaderNodeTexCoord'); tc.object = empty
        ln = n.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; l.new(tc.outputs['Object'], ln.inputs[0])
        mr = n.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = r0; mr.inputs['From Max'].default_value = r1
        mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.0; l.new(ln.outputs['Value'], mr.inputs['Value'])
        v = n.new('ShaderNodeValue'); v.name = valname
        for f, x in keys: v.outputs[0].default_value = x; v.outputs[0].keyframe_insert("default_value", frame=f)
        mu = n.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; l.new(mr.outputs['Result'], mu.inputs[0]); l.new(v.outputs[0], mu.inputs[1])
        return mu
    a_ = sph(XC, 0.16, 0.26, "XRT", XR_T); b_ = sph(XH, 0.07, 0.12, "XRH", XR_H)
    mx = n.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'; l.new(a_.outputs[0], mx.inputs[0]); l.new(b_.outputs[0], mx.inputs[1])
    return mx
done = set()
for ob in [c for c in O if c.parent == pope and c.type == 'MESH']:
    for m in ob.data.materials:
        if not m or m.name in done or not m.node_tree: continue
        if m.users > 1 and m.name in ("WhiteWool",):
            m2 = m.copy(); m2.name = "PopeWool"; ob.data.materials[0] = m2; m = m2
        done.add(m.name)
        nt = m.node_tree; out = next((x for x in nt.nodes if x.type == 'OUTPUT_MATERIAL' and x.is_active_output), None)
        if not out or not out.inputs['Surface'].links: continue
        src = out.inputs['Surface'].links[0].from_socket
        mk = mask_nodes(nt)
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); tr.inputs['Color'].default_value = (0.7, 0.9, 1.0, 1)
        ms = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(mk.outputs[0], ms.inputs['Fac']); nt.links.new(src, ms.inputs[1]); nt.links.new(tr.outputs['BSDF'], ms.inputs[2])
        nt.links.new(ms.outputs['Shader'], out.inputs['Surface'])
# anatomy shaders: realistic bone / wet tissue / vessel, visible only inside the porthole
def anat_mat(name, base, sss=0.0, rough=0.4, bump=0.3, emit=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; n, l = nt.nodes, nt.links
    bs = n["Principled BSDF"]; bs.inputs['Roughness'].default_value = rough
    nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 180; nz.inputs['Detail'].default_value = 12
    vor = n.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 400
    bp = n.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; l.new(nz.outputs['Fac'], bp.inputs['Height'])
    bp2 = n.new('ShaderNodeBump'); bp2.inputs['Strength'].default_value = bump * 0.6; l.new(vor.outputs['Distance'], bp2.inputs['Height']); l.new(bp.outputs['Normal'], bp2.inputs['Normal'])
    l.new(bp2.outputs['Normal'], bs.inputs['Normal'])
    cr = n.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = tuple(c * 0.7 for c in base) + (1,); cr.color_ramp.elements[1].color = tuple(min(1, c * 1.15) for c in base) + (1,)
    l.new(nz.outputs['Fac'], cr.inputs['Fac']); l.new(cr.outputs['Color'], bs.inputs['Base Color'])
    bs.inputs['Subsurface Weight'].default_value = sss; bs.inputs['Subsurface Radius'].default_value = (0.8, 0.3, 0.2)
    bs.inputs['Coat Weight'].default_value = 0.5 if sss > 0 else 0.0
    if emit:
        bs.inputs['Emission Color'].default_value = tuple(emit) + (1,)
        ev_ = n.new('ShaderNodeValue'); ev_.name = "Glow"
        for f, x in ((1, 0), (1430, 0), (1450, 1.2), (1510, 1.2), (1530, 0)):
            ev_.outputs[0].default_value = x; ev_.outputs[0].keyframe_insert("default_value", frame=f)
        l.new(ev_.outputs[0], bs.inputs['Emission Strength'])
    out = n["Material Output"]; src = bs.outputs['BSDF']
    mk = mask_nodes(nt)
    tr = n.new('ShaderNodeBsdfTransparent'); ms = n.new('ShaderNodeMixShader')
    l.new(mk.outputs[0], ms.inputs['Fac']); l.new(tr.outputs['BSDF'], ms.inputs[1]); l.new(src, ms.inputs[2]); l.new(ms.outputs['Shader'], out.inputs['Surface'])
    return m
BONE = anat_mat("XBone", (0.86, 0.8, 0.66), sss=0.05, rough=0.55, bump=0.4, emit=(0.2, 0.7, 1.0))
GUT = anat_mat("XGut", (0.75, 0.38, 0.33), sss=0.6, rough=0.25, bump=0.25)
VES = anat_mat("XVessel", (0.6, 0.06, 0.07), sss=0.5, rough=0.25, bump=0.15, emit=(1.0, 0.25, 0.2))
for o, m in ((skel, BONE), (hand, BONE), (guts, GUT), (aorta, VES)):
    o.data.materials.clear(); o.data.materials.append(m)
O["spine"].hide_render = True; O["spine"].hide_viewport = True
# x-ray dome: deep teal-to-navy gradient backdrop around the torso (camera-visible only)
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=2.0); dome = bpy.context.object; dome.name = "XRayDome"
for p in dome.data.polygons: p.use_smooth = True
dm = bpy.data.materials.new("XRayDomeMat"); dm.use_nodes = True; nt = dm.node_tree; n, l = nt.nodes, nt.links
for x in list(n): n.remove(x)
geo = n.new('ShaderNodeNewGeometry'); dot = n.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
l.new(geo.outputs['Incoming'], dot.inputs[0]); l.new(geo.outputs['Normal'], dot.inputs[1])
ab = n.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'; l.new(dot.outputs['Value'], ab.inputs[0])
pw = n.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 3.0; l.new(ab.outputs[0], pw.inputs[0])
tcd = n.new('ShaderNodeTexCoord'); sep = n.new('ShaderNodeSeparateXYZ'); l.new(tcd.outputs['Generated'], sep.inputs[0])
ad = n.new('ShaderNodeMath'); ad.operation = 'MULTIPLY_ADD'; ad.inputs[1].default_value = 0.25; l.new(sep.outputs['Z'], ad.inputs[0]); l.new(pw.outputs[0], ad.inputs[2])
cr = n.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0.002, 0.006, 0.025, 1); cr.color_ramp.elements[1].color = (0.02, 0.2, 0.27, 1)
cr.color_ramp.elements[0].position = 0.3
l.new(ad.outputs[0], cr.inputs['Fac'])
em = n.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.0; l.new(cr.outputs['Color'], em.inputs['Color'])
tr = n.new('ShaderNodeBsdfTransparent'); ms = n.new('ShaderNodeMixShader'); fv = n.new('ShaderNodeValue'); fv.name = "DomeFade"
for f, x in ((1, 0), (322, 0), (330, 1), (490, 1), (502, 0), (1395, 0), (1412, 1), (1512, 1), (1540, 0)):
    fv.outputs[0].default_value = x; fv.outputs[0].keyframe_insert("default_value", frame=f)
l.new(fv.outputs[0], ms.inputs['Fac']); l.new(tr.outputs['BSDF'], ms.inputs[1]); l.new(em.outputs[0], ms.inputs[2])
oo = n.new('ShaderNodeOutputMaterial'); l.new(ms.outputs[0], oo.inputs[0])
dome.data.materials.append(dm)
dome.visible_shadow = False; dome.visible_diffuse = False; dome.visible_glossy = False; dome.visible_transmission = False; dome.visible_volume_scatter = False
cl = dome.constraints.new('COPY_LOCATION'); cl.target = XC
for c in list(dome.users_collection): c.objects.unlink(dome)
bpy.data.collections["XRay"].objects.link(dome)
key_vis(dome, ((1, False), (320, True), (504, False), (1392, True), (1542, False)))
# x-ray key light that rides with the torso
xl = bpy.data.objects.new("XRayKey", bpy.data.lights.new("XRayKey", 'AREA')); xl.data.size = 0.6; xl.data.color = (0.8, 0.93, 1.0)
bpy.data.collections["XRay"].objects.link(xl); xl.parent = XC; xl.location = (0.0, -1.0, 0.6)
tq = xl.constraints.new('TRACK_TO'); tq.target = XC
for f, e in ((1, 0), (322, 0), (330, 60), (490, 60), (502, 0), (1395, 0), (1412, 60), (1512, 60), (1540, 0)):
    xl.data.energy = e; xl.data.keyframe_insert("energy", frame=f)
# bullet paths (glowing traces) built in spine04 space at frame 330
glowm, ge = emis("TraceGlow", (1.0, 0.55, 0.2), 0.0)
for f, x in ((1, 0), (330, 0), (336, 25), (488, 18), (500, 0), (1405, 0), (1420, 14), (1515, 14), (1535, 0)):
    ge.inputs['Strength'].default_value = x; ge.inputs['Strength'].keyframe_insert("default_value", frame=f)
def trace(name, pts_rest, bone, f0, f1, depth=0.005):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = depth; cu.bevel_resolution = 3
    sp = cu.splines.new('NURBS'); sp.points.add(len(pts_rest) - 1)
    for p, c in zip(sp.points, pts_rest): p.co = (c[0], c[1], c[2], 1)
    sp.use_endpoint_u = True; sp.order_u = 3
    o = bpy.data.objects.new(name, cu); bpy.data.collections["XRay"].objects.link(o); cu.materials.append(glowm)
    attach_rest(o, bone, Matrix.Identity(4))
    for f, v in ((1, 0.0), (f0, 0.0), (f1, 1.0)):
        cu.bevel_factor_end = v; cu.keyframe_insert("bevel_factor_end", frame=f)
    o.visible_shadow = False
    return o
cy = pope.data.bones["root"].head_local.y
trace("TraceGut", [(0.06, cy - 0.2, 1.02), (0.05, cy - 0.08, 1.0), (0.02, cy + 0.02, 0.99), (-0.02, cy + 0.14, 0.96), (-0.04, cy + 0.2, 0.95)], "spine04", 332, 372)
trace("TraceHand", [(c.x, c.y, c.z) for c in (wb.head_local + dirh * 0.12 + Vector((0, -0.08, 0)), wb.head_local + dirh * 0.11, wb.head_local + dirh * 0.1 + Vector((0, 0.08, 0)))], "wrist.L", 432, 452, depth=0.004)
trace("TraceCurve", [(0.06, cy - 0.22, 1.02), (0.06, cy - 0.08, 1.0), (0.05, cy + 0.0, 0.985), (0.025, cy + 0.08, 0.975), (0.0, cy + 0.2, 0.96)], "spine04", 1418, 1470, depth=0.006)
for nm in ("TraceGut", "TraceHand"):
    key_vis(O[nm], ((1, False), (330, True), (502, False)))
key_vis(O["TraceCurve"], ((1, False), (1405, True), (1540, False)))
# the bullet itself: slow-mo flight 255->330 from the muzzle to the robe
bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.0045); bul = bpy.context.object; bul.name = "Bullet"
bul.scale = (1, 1, 2.0); bpy.ops.object.transform_apply(scale=True)
for v in bul.data.vertices:
    if v.co.z < 0: v.co.z *= 0.35
bul.data.materials.append(bpy.data.materials["BulletLead"])
ev(330)
ENTRY = bone_w(pope, "spine04") + (pope.matrix_world.to_3x3() @ Vector((0.05, -0.2, 0.0)))
def bullet_pos(f):
    u = (f - 255) / 75.0; return MUZZLE.lerp(ENTRY, max(0, min(1, u)))
BD = (ENTRY - MUZZLE).normalized()
for f in range(254, 332, 2):
    key_obj(bul, f, loc=bullet_pos(f), rot=Vector((0, 0, 1)).rotation_difference(BD).to_euler())
key_vis(bul, ((1, False), (255, True), (331, False)))
# shimmer streak behind the bullet
smat, se = emis("Streak", (0.9, 0.95, 1.0), 0.6)
bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.004, radius2=0.0, depth=0.35); stk = bpy.context.object; stk.name = "BulletStreak"; stk.data.materials.append(smat)
stk.parent = bul; stk.location = (0, 0, -0.18); stk.rotation_euler = (math.pi, 0, 0); stk.visible_shadow = False
key_vis(stk, ((1, False), (256, True), (331, False)))

# ------------------------------------------------------------------ PIGEONS
pig = O["pigeon"]
PG = []
for i in range(26):
    o = pig.copy(); o.name = "Pigeon%d" % i; bpy.data.collections["Square"].objects.link(o)
    x = random.uniform(-2.3, 2.3) * (1 if i % 3 else 0.4); y = random.uniform(-1.0, 4.0)
    if abs(x) < 1.2: x = 1.2 * (1 if x >= 0 else -1) + x * 0.5
    yaw = random.uniform(0, 6.28)
    tk = 512 + random.randint(0, 25)
    tgt = Vector((-8 + random.uniform(-3, 3), 30 + random.uniform(-4, 4), 9 + random.uniform(-2, 3)))
    for f in range(1, 700, 4):
        if f < tk:
            peck = 0.35 * max(0, math.sin(f * 0.21 + i)) ** 8
            key_obj(o, f, loc=(x, y, 0), rot=(peck, 0, yaw + 0.3 * math.sin(f * 0.03 + i)))
        else:
            u = (f - tk) / 120.0
            p = Vector((x, y, 0)).lerp(tgt, smooth(u) * 0.6 + u * 0.4) + Vector((0, 0, 1.6 * math.sin(min(1, u) * 1.5)))
            d = (tgt - Vector((x, y, 0))).normalized()
            key_obj(o, f, loc=p, rot=(-0.5, 0.4 * math.sin(f * 1.3 + i), math.atan2(-d.x, d.y)))
    # wing-beat squash (no rig on the asset): fast scale flutter while flying
    for f in range(tk, 700, 2):
        o.scale = (1.0 + 0.35 * math.sin(f * 1.6 + i), 1.0, 1.0 - 0.15 * math.sin(f * 1.6 + i)); o.keyframe_insert("scale", frame=f)
    key_vis(o, ((1, True), (700, False)))
    PG.append(o)
# a few pigeons that cross the lens at 600-625 for the wipe toward the facade
for i in range(4):
    o = pig.copy(); o.name = "PigeonWipe%d" % i; bpy.data.collections["Square"].objects.link(o)
    key_vis(o, ((1, False), (590, True), (640, False)))

print("STAGE square done")

# ------------------------------------------------------------------ THEATRE 631..762 (floor z=7)
TABLE = O["optable"]
ev(640)
TABLE.location = (-10.6, 43.6, 7.0); TABLE.rotation_euler = (0, 0, R_(200))   # the asset is an anaesthesia/equipment stand: push it to the corner
tz = 7.95
def tbox(nm, size, loc, mat, bev=0.01):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); b_ = bpy.context.object; b_.name = nm; b_.scale = size
    b_.data.materials.append(bpy.data.materials[mat]); b_.modifiers.new("b", 'BEVEL').width = bev
    for c in list(b_.users_collection): c.objects.unlink(b_)
    bpy.data.collections["Theatre"].objects.link(b_); return b_
tbox("ORTableTop", (0.58, 2.05, 0.06), (-8.0, 40.5, tz - 0.08), "MetalPlate")
tbox("ORTablePad", (0.54, 2.0, 0.06), (-8.0, 40.5, tz - 0.03), "SurgDrape", 0.02)
tbox("ORTableColumn", (0.22, 0.4, 0.75), (-8.0, 40.5, 7.45), "MetalPlate")
tbox("ORTableBase", (0.6, 0.9, 0.08), (-8.0, 40.5, 7.04), "MetalPlate")
tbox("InstrumentTray", (0.5, 0.35, 0.03), (-7.05, 41.75, 8.0), "MetalPlate")
tbox("TrayStand", (0.03, 0.03, 0.95), (-7.05, 41.75, 7.5), "MetalPlate")
print("TABLE top", tz)
# Pope lies on his back, head toward +Y
key_obj(pope, 630, loc=pope.location.copy() if False else pope_root_obj(505), rot=(0, 0, POPE_YAW), interp='CONSTANT')
LIE = Vector((-8.0, 40.5 - 0.9, tz + 0.12))
key_obj(pope, 631, loc=LIE, rot=(R_(-90), 0, 0), interp='CONSTANT')
for f in range(631, 763, 6):
    stand(P, f, flex=0, head=(-8, 6 * math.sin(f * 0.02)))
    arms_down(P, f)
    face(pope, f, lids=1.0, jaw=2)
drape = bpy.data.meshes.new("Drape"); bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=30, y_segments=50, size=0.5); bm.to_mesh(drape)
for v in drape.vertices:
    v.co.x *= 2.4; v.co.y *= 3.8; v.co.z = -0.28 * max(0, abs(v.co.x) - 0.33) / 0.87
dro = bpy.data.objects.new("Drape", drape); bpy.data.collections["Theatre"].objects.link(dro)
dro.location = (-8.0, 40.5 - 0.35, tz + 0.55); drape.materials.append(bpy.data.materials["SurgDrape"])
sw = dro.modifiers.new("shrink", 'SHRINKWRAP'); sw.wrap_method = 'PROJECT'; sw.use_project_z = True; sw.use_negative_direction = True; sw.use_positive_direction = False
sw.target = body_of(pope); sw.offset = 0.06
sw2 = dro.modifiers.new("onTable", 'SHRINKWRAP'); sw2.wrap_method = 'PROJECT'; sw2.use_project_z = True; sw2.use_negative_direction = True; sw2.use_positive_direction = False
sw2.target = O["ORTablePad"]; sw2.offset = 0.01
dro.modifiers.new("smooth", 'CORRECTIVE_SMOOTH').iterations = 8
dro.modifiers.new("sol", 'SOLIDIFY').thickness = 0.006
dro.modifiers.new("sub", 'SUBSURF').levels = 1
key_vis(dro, ((1, False), (631, True), (763, False)))
TEAM = (("SurgA", Vector((-8.75, 40.4)), -90), ("SurgB", Vector((-7.25, 40.2)), 90), ("SurgC", Vector((-8.0, 41.45)), 180), ("Nurse", Vector((-7.0, 41.3)), 120))
for nm, xy, yw in TEAM:
    r = O[nm]; h = HUM[nm]
    key_obj(r, 1, loc=(xy.x, xy.y, 7.0), rot=(0, 0, R_(yw)), interp='CONSTANT')
    for f in range(600, 770, 4):
        ph = hash(nm) % 7
        stand(h, f, flex=22 if nm != "Nurse" else 8, head=(25, 8 * math.sin(f * 0.03 + ph)), crouch=0.02)
        if nm == "Nurse":
            hand_at(h, "R", f, (-0.2, -0.38 + 0.1 * math.sin(f * 0.04), 1.05), d=(0, -1, -0.3), n=(0, 0, -1)); hand_at(h, "L", f, (0.22, -0.2, 0.95), d=(0, -0.5, -1), n=(1, 0, 0))
        else:
            hand_at(h, "R", f, (-0.1 + 0.04 * math.sin(f * 0.11 + ph), -0.48, 0.98 + 0.02 * math.sin(f * 0.17)), d=(0.3, -1, -0.6), n=(0, 0, -1))
            hand_at(h, "L", f, (0.12 + 0.03 * math.sin(f * 0.09 + ph), -0.46, 0.97), d=(-0.3, -1, -0.6), n=(0, 0, -1))
        face(r, f, brow=-0.3 + 0.3 * math.sin(f * 0.05 + ph))
# monitor screen with a heartbeat trace (ragged -> steady), no digits
ev(700)
scr_m = bpy.data.materials.new("ScreenBlack"); scr_m.use_nodes = True; scr_m.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.01, 0.012, 0.012, 1)
scr_m.node_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = 0.15
MON = Vector((-6.6, 41.9, 8.55))
bpy.ops.mesh.primitive_cube_add(size=1, location=MON); mh = bpy.context.object; mh.name = "MonitorHousing"; mh.scale = (0.5, 0.09, 0.36)
mh.data.materials.append(bpy.data.materials["PaintedMetal"]); mh.modifiers.new("b", 'BEVEL').width = 0.015
mh.rotation_euler = (0, 0, R_(-35))
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); sp_ = bpy.context.object; sp_.name = "MonitorScreen"; sp_.scale = (0.44, 0.3, 1)
sp_.data.materials.append(scr_m); sp_.parent = mh; sp_.matrix_parent_inverse.identity(); sp_.location = (0, -0.505, 0); sp_.rotation_euler = (R_(90), 0, 0)
sp_.scale = (0.88, 0.83, 1)
lathe = None
ecg = bpy.data.curves.new("ECG", 'CURVE'); ecg.dimensions = '3D'; ecg.bevel_depth = 0.0025
spl = ecg.splines.new('POLY'); N = 220; spl.points.add(N - 1)
for i, p in enumerate(spl.points):
    x = -0.2 + 0.4 * i / (N - 1); ph = (i % 44) / 44.0; rag = i < N * 0.5
    y = 0.0
    if 0.40 < ph < 0.44: y = -0.02
    elif 0.44 < ph < 0.48: y = 0.11 if not rag else 0.06 + 0.06 * random.random()
    elif 0.48 < ph < 0.52: y = -0.05
    elif 0.65 < ph < 0.78: y = 0.025 * math.sin((ph - 0.65) / 0.13 * math.pi)
    if rag: y += random.uniform(-0.012, 0.012)
    p.co = (x, y * 0.9, 0, 1)
eo = bpy.data.objects.new("ECG", ecg); bpy.data.collections["Theatre"].objects.link(eo)
eo.parent = mh; eo.location = (0, -0.52, 0); eo.rotation_euler = (R_(90), 0, 0); eo.scale = (2.0, 2.0, 2.0)
em_, ee = emis("ECGGlow", (0.2, 1.0, 0.45), 12.0); ecg.materials.append(em_)
for f, v in ((1, 0.0), (632, 0.05), (760, 1.0)):
    ecg.bevel_factor_end = v; ecg.keyframe_insert("bevel_factor_end", frame=f)
for o in (mh, eo):
    for c in list(o.users_collection): c.objects.unlink(o)
    bpy.data.collections["Theatre"].objects.link(o)
# theatre lights
def light(name, kind, loc, energy, color=(1, 1, 1), size=0.5, rot=None, coll="Lights", spot=None):
    L = bpy.data.objects.new(name, bpy.data.lights.new(name, kind)); bpy.data.collections[coll].objects.link(L)
    L.location = loc; L.data.energy = energy; L.data.color = color
    if kind == 'AREA': L.data.size = size
    else: L.data.shadow_soft_size = size
    if kind == 'SPOT' and spot: L.data.spot_size = R_(spot)
    if rot: L.rotation_euler = rot
    return L
light("TheatreLamp", 'SPOT', (-8.0, 40.4, 10.6), 900, (1.0, 0.97, 0.92), 0.25, spot=55)
light("TheatreFill1", 'AREA', (-10.5, 39, 10.8), 250, (0.85, 0.95, 1.0), 1.5)
light("TheatreFill2", 'AREA', (-5.5, 43, 10.8), 250, (0.85, 0.95, 1.0), 1.5)
light("TheatreRim", 'AREA', (-8, 44.5, 9.0), 120, (0.7, 0.9, 1.0), 1.0, rot=(R_(90), 0, R_(180)))

# ------------------------------------------------------------------ BALCONY 763..1014 (balcony floor z=7.03)
BAL = Vector((0.0, 33.95, 7.03))
key_obj(pope, 763, loc=BAL, rot=(0, 0, 0), interp='CONSTANT')
aide = O["AideA"]
key_obj(aide, 700, loc=Vector((0.85, 34.7, 7.03)), rot=(0, 0, R_(-10)), interp='CONSTANT')
for f in range(763, 1020, 3):
    br = smooth((f - 800) / 40)
    stand(P, f, flex=3, twist=10 * math.sin(f * 0.02), head=(-5, 14 * math.sin(f * 0.018)))
    hand_at(P, "R", f, (-0.2 - 0.05 * br + 0.06 * math.sin(f * 0.05), -0.42, 1.25 + 0.45 * br + 0.04 * math.sin(f * 0.05)), d=(0, -0.3, 1), n=(0, -1, 0), pole=(-0.7, 0.2, 1.1))
    hand_at(P, "L", f, (0.2, -0.4, 1.0), d=(0, -1, -0.5), n=(0, 0, -1), pole=(0.6, 0.3, 1.0))   # rests on the rail
    face(pope, f, brow=0.35, smile=0.3, jaw=6 * max(0, math.sin(f * 0.25)) * (1 if (f // 40) % 3 else 0.2))
for f in range(700, 1020, 4):
    stand(HUM["AideA"], f, flex=2, head=(0, 10 * math.sin(f * 0.02))); arms_down(HUM["AideA"], f, 0.01); face(aide, f, smile=0.2)
# hide the square-only people during the later beats (they are teleported below)
for nm in ("AideB", "GuardA", "GuardB"):
    key_obj(O[nm], 700, loc=O[nm].location.copy() + Vector((0, 0, -60)), interp='CONSTANT') if O[nm].animation_data else None

# ------------------------------------------------------------------ CELL 1015..1152
pris = O["Prisoner"]; PR = HUM["Prisoner"]
SEAT = 0.47
key_obj(pope, 1015, loc=Vector((-0.55, 40.45, 7.0)), rot=(0, 0, R_(90 + 180) - R_(180) + R_(-90) + R_(180)), interp='CONSTANT')
key_obj(pope, 1015, loc=Vector((-0.55, 40.45, 7.0)), rot=(0, 0, R_(-90)), interp='CONSTANT')   # faces +X
key_obj(pris, 1, loc=Vector((0.55, 40.85, 7.0)), rot=(0, 0, R_(90)), interp='CONSTANT')          # faces -X
O["ChairPope"].location = (-0.55 - 0.12, 40.45, 7.0); O["ChairPrisoner"].location = (0.55 + 0.12, 40.85, 7.0)
def sit(h, f, flex=8.0, head=(0, 0), twist=0.0, knee_out=0.0):
    rh = h.root_head
    h.key_root(f, Vector((rh.x, rh.y + 0.12, SEAT + 0.12)), flex=-4)
    h.key_spine(f, flex=flex, twist=twist, head=head)
    for s in "LR":
        h.key_foot(s, f, Vector((h.ankle[s].x * (1.15 + knee_out), h.ankle[s].y - 0.42)), 0.0)
for f in range(1015, 1160, 3):
    sit(P, f, flex=16 + 3 * math.sin(f * 0.03), head=(10, 4 * math.sin(f * 0.04)), twist=-6)
    ev(f)
    # left hand on the prisoner's right shoulder (prisoner faces the Pope)
    W = pope.matrix_world.inverted() @ (bone_w(pris, "shoulder01.R") + Vector((0, 0, 0.06)))
    hand_at(P, "L", f, tuple(W), d=(0.3, -1, -0.4), n=(0, 0, -1), pole=(0.7, 0.0, 1.0))
    hand_at(P, "R", f, (-0.12, -0.38, 0.62), d=(0.3, -1, -0.2), n=(0, 0, -1))
    face(pope, f, brow=0.3 * math.sin(f * 0.05), jaw=7 * max(0, math.sin(f * 0.3)), smile=0.15)
    sit(PR, f, flex=24 + 4 * math.sin(f * 0.05), head=(28 + 10 * max(0, math.sin(f * 0.06)), 0))
    hand_at(PR, "R", f, (-0.14, -0.42, 0.62), d=(0.2, -1, -0.3), n=(0, 0, -1)); hand_at(PR, "L", f, (0.14, -0.42, 0.62), d=(-0.2, -1, -0.3), n=(0, 0, -1))
    face(pris, f, brow=-0.5, lids=0.35)
for f in range(1, 1015, 40):
    sit(PR, f); arms_down(PR, f)
cv = bpy.data.objects.new("CellVolume", None)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 40.6, 8.6)); vb = bpy.context.object; vb.name = "CellHaze"; vb.scale = (4.9, 4.7, 3.1)
vm = bpy.data.materials.new("Haze"); vm.use_nodes = True; nn = vm.node_tree.nodes
nn.remove(nn["Principled BSDF"]); pv = nn.new('ShaderNodeVolumePrincipled'); pv.inputs['Density'].default_value = 0.035
vm.node_tree.links.new(pv.outputs[0], nn["Material Output"].inputs['Volume']); vb.data.materials.append(vm)
for c in list(vb.users_collection): c.objects.unlink(vb)
bpy.data.collections["Cell"].objects.link(vb)
L = light("CellSun", 'SPOT', (0.0, 44.6, 10.4), 6000, (1.0, 0.78, 0.5), 0.1, spot=40)
L.rotation_euler = (Vector((0, 40.8, 7.4)) - L.location).to_track_quat('-Z', 'Y').to_euler()
light("CellBounce", 'AREA', (0, 39.0, 10.0), 160, (1.0, 0.85, 0.7), 2.0)
light("CorridorDim", 'POINT', (0, 37.4, 9.6), 8, (1.0, 0.8, 0.6), 0.2)

# ------------------------------------------------------------------ SHRINE 1153..1620
mary = O["mary"]; ev(1200)
top = mary.location.z + mary.dimensions.z
crown = O["crown"]
hz = max([z for z in (ray_down(mary, mary.location.x + dx, mary.location.y + dy, 11.5) for dx in (-0.03, 0, 0.03) for dy in (-0.03, 0, 0.03)) if z] or [top])
print("MARY head", hz, top)
tv = max((mary.matrix_world @ v.co for v in mary.data.vertices), key=lambda v: v.z)
crown.location = (tv.x, tv.y - 0.02, tv.z - 0.06)
KNEEL = Vector((0.0, 50.4, 7.0))
key_obj(pope, 1153, loc=KNEEL, rot=(0, 0, R_(180)), interp='CONSTANT')     # faces +Y toward the statue
for f in range(1153, 1621, 4):
    rh = P.root_head
    P.key_root(f, Vector((rh.x, rh.y + 0.15, 0.58 + 0.01 * math.sin(f * 0.03))), flex=4)
    P.key_spine(f, flex=8, head=(-8 + 3 * math.sin(f * 0.02), 0))
    for s in "LR":
        P.key_foot(s, f, Vector((P.ankle[s].x, P.ankle[s].y + 0.45)), 0.0, lift=-0.0, pitch=-70)
    hand_at(P, "L", f, (0.03, -0.3, 1.18), d=(0, -0.2, 1), n=(-1, 0, 0)); hand_at(P, "R", f, (-0.03, -0.3, 1.18), d=(0, -0.2, 1), n=(1, 0, 0))
    face(pope, f, lids=0.6, brow=0.2)
# kneeler under him
O["Pew"].location = O["Pew"].location
# cleric on a step stool places the bullet in the crown (AideB)
cl_ = O["AideB"]; CL = HUM["AideB"]
STOOL = Vector((0.75, 53.15, 7.0))
for i, (w_, h_) in enumerate(((0.55, 0.3), (0.55, 0.6))):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(STOOL.x, STOOL.y + 0.2 - i * 0.2, 7.0 + h_ - 0.03)); st = bpy.context.object; st.name = "StoolStep"
    st.scale = (w_, 0.22, 0.05); st.data.materials.append(bpy.data.materials["Wood"])
    for c in list(st.users_collection): c.objects.unlink(st)
    bpy.data.collections["Shrine"].objects.link(st)
    for dx in (-0.25, 0.25):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(STOOL.x + dx, STOOL.y + 0.2 - i * 0.2, 7.0 + h_ / 2)); lg = bpy.context.object; lg.name = "StoolLeg"; lg.scale = (0.04, 0.04, h_)
        lg.data.materials.append(bpy.data.materials["Wood"])
        for c in list(lg.users_collection): c.objects.unlink(lg)
        bpy.data.collections["Shrine"].objects.link(lg)
key_obj(cl_, 1100, loc=STOOL + Vector((0, 0.05, 0.6)), rot=(0, 0, R_(180 + 35)), interp='CONSTANT')
ev(1200)
CROWN_W = Vector(crown.location) + Vector((0.0, -0.06, 0.06))
for f in range(1100, 1621, 3):
    stand(CL, f, flex=4, head=(-18, 0))
    u = smooth((f - 1200) / 70); v2 = smooth((f - 1300) / 30); back = smooth((f - 1340) / 40)
    Wl = cl_.matrix_world.inverted() @ CROWN_W
    start = Vector((-0.2, -0.35, 1.05))
    Wt = start.lerp(Wl + Vector((0, 0.1, -0.04)), u) .lerp(start, back)
    hand_at(CL, "R", f, tuple(Wt), d=(0, -0.6, 0.8), n=(-1, 0, 0), pole=(-0.6, 0.3, 1.1))
    hand_at(CL, "L", f, (0.24, -0.1, 0.9), d=(0, 0, -1), n=(1, 0, 0))
    face(cl_, f, brow=0.3, lids=0.2)
# the relic bullet: held in the cleric's fingers, then seated in the crown at 1320
rb = bul.copy(); rb.data = bul.data; rb.name = "RelicBullet"; bpy.data.collections["Shrine"].objects.link(rb); rb.animation_data_clear()
rb.scale = (2.0, 2.0, 2.0)
ch = rb.constraints.new('CHILD_OF'); ch.target = cl_; ch.subtarget = "finger2-3.R"
ev(1250); ch.inverse_matrix = (cl_.matrix_world @ cl_.pose.bones["finger2-3.R"].matrix).inverted()
rb.location = cl_.matrix_world @ cl_.pose.bones["finger2-3.R"].tail
for f, v in ((1, 1.0), (1318, 1.0), (1320, 0.0)):
    ch.influence = v; ch.keyframe_insert("influence", frame=f)
ev(1320); seat = Vector(CROWN_W)
rb.keyframe_insert("location", frame=1318)
rb.location = seat; rb.keyframe_insert("location", frame=1320)
set_interp(rb, 1320, 'CONSTANT')
key_vis(rb, ((1, False), (1153, True)))
# candles: flickering point lights over the racks + incense haze
for side in (-1, 1):
    for r in range(2):
        Lc = light("Candle%d%d" % (side, r), 'POINT', (side * 1.9, 52.2 - r * 0.7, 8.3 + r * 0.15), 18, (1.0, 0.55, 0.2), 0.6)
        for f in range(1, 1621, 5):
            Lc.data.energy = 14 + 6 * random.random(); Lc.data.keyframe_insert("energy", frame=f)
light("ShrineKey", 'SPOT', (1.6, 50.2, 11.5), 700, (1.0, 0.82, 0.6), 0.3, spot=45).rotation_euler = (Vector((0, 53.6, 9.2)) - Vector((1.6, 50.2, 11.5))).to_track_quat('-Z', 'Y').to_euler()
light("ShrineFill", 'AREA', (-2.5, 46, 13), 120, (0.8, 0.85, 1.0), 3.0)
light("ShrineCrown", 'SPOT', (-0.6, 52.6, 10.8), 120, (1.0, 0.9, 0.75), 0.1, spot=20).rotation_euler = (Vector(crown.location) - Vector((-0.6, 52.6, 10.8))).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 49.6, 11.5)); vs_ = bpy.context.object; vs_.name = "ShrineHaze"; vs_.scale = (11.8, 12.4, 8.8)
vm2 = vm.copy(); vm2.node_tree.nodes["Principled Volume"].inputs['Density'].default_value = 0.012; vs_.data.materials.append(vm2)
for c in list(vs_.users_collection): c.objects.unlink(vs_)
bpy.data.collections["Shrine"].objects.link(vs_)

print("STAGE sets done")

# ------------------------------------------------------------------ ONE CAMERA
def popehead(f): return pope_root_obj(min(f, 505)) + Vector((0, 0, 1.62))
def popechest(f): return pope_root_obj(min(f, 505)) + Vector((0, 0, 1.25))
FD = Vector((math.sin(POPE_YAW) * -1, -math.cos(POPE_YAW), 0)) * -1   # his facing direction
FD = Matrix.Rotation(POPE_YAW, 3, 'Z') @ Vector((0, -1, 0))
PERP = Vector((-FD.y, FD.x, 0))
ev(340); XCW = XC.matrix_world.translation.copy(); ev(440); XHW = XH.matrix_world.translation.copy()
ev(1440); XCW8 = XC.matrix_world.translation.copy()
ev(960); HANDW = bone_w(pope, "wrist.R")
ev(1130); SHW = bone_w(pris, "shoulder01.R")
SHOT = (Vector((-3.92, 2.05, 1.78)))
K = [
 (1,    SHOT,                                  popehead(1), 55),
 (60,   Vector((-3.0, 0.4, 2.7)),               popehead(60), 45),
 (115,  popehead(115) + FD * 1.9 + Vector((0, 0, 0.2)), popehead(115) + Vector((0, 0, -0.1)), 35),
 (165,  popechest(165) + PERP * 2.4 + FD * 0.8 + Vector((0, 0, 0.9)), popechest(165), 24),
 (210,  Vector((2.8, -4.5, 4.6)),               Vector((-2.0, -1.5, 1.2)), 22),
 (245,  Vector((-3.3, 3.1, 2.3)),               Vector((-1.0, -2.0, 1.5)), 30),
]
for f in range(256, 327, 10):
    K.append((f, bullet_pos(f) - BD * 0.32 + Vector((0.04, 0, 0.05)), bullet_pos(f) + BD * 1.2, 35))
K += [
 (332,  ENTRY - BD * 0.36,                       XCW, 35),
 (375,  XCW + (Matrix.Rotation(R_(-55), 3, 'Z') @ (-BD)) * 0.62 + Vector((0, 0, 0.12)), XCW, 32),
 (418,  XHW + (Matrix.Rotation(R_(-20), 3, 'Z') @ (-BD)) * 0.45 + Vector((0, 0, -0.05)), XHW, 35),
 (465,  XHW + (Matrix.Rotation(R_(40), 3, 'Z') @ (-BD)) * 0.42 + Vector((0, 0, 0.08)), XHW, 35),
 (505,  popechest(505) + FD * 2.1 + PERP * 0.5 + Vector((0, 0, 0.3)), popechest(505) + Vector((0, 0, -0.1)), 30),
 (555,  popechest(505) + FD * 1.6 - PERP * 1.5 + Vector((0, 0, -0.5)), popechest(505) + Vector((0, 0, -0.35)), 24),
 (598,  popechest(505) + FD * 0.8 - PERP * 2.6 + Vector((0, 0, 0.3)), popechest(505) + Vector((0, 0, -0.3)), 22),
 (628,  Vector((-5.0, 22.0, 6.6)),              Vector((-8.0, 36.0, 9.3)), 22),
 (648,  Vector((-8.0, 35.2, 9.35)),             Vector((-8.0, 40.0, 8.6)), 22),
 (668,  Vector((-8.1, 38.0, 10.3)),             Vector((-8.0, 40.3, 8.1)), 24),
 (705,  Vector((-8.25, 40.0, 10.75)),           Vector((-8.0, 40.35, 8.0)), 24),
 (738,  Vector((-7.3, 40.7, 9.25)),             MON, 35),
 (760,  Vector((-7.0, 41.25, 8.85)),            MON, 40),
 (782,  Vector((-7.7, 37.6, 9.5)),              Vector((-6.0, 30.0, 8.5)), 24),
 (805,  Vector((-7.0, 32.5, 10.2)),             Vector((-1.0, 22.0, 3.0)), 22),
 (845,  Vector((-3.6, 23.5, 11.2)),             Vector((0.0, 34.0, 8.2)), 24),
 (900,  Vector((-1.4, 30.2, 8.7)),              Vector((0.0, 33.9, 8.5)), 32),
 (950,  HANDW + Vector((0.9, -1.5, -0.1)),       HANDW, 40),
 (990,  Vector((0.75, 34.2, 8.85)),             Vector((0.0, 37.0, 8.6)), 30),
 (1013, Vector((0.0, 36.3, 8.75)),              Vector((0.0, 39.5, 8.3)), 26),
 (1032, Vector((0.0, 38.65, 8.55)),             Vector((0.0, 40.65, 7.95)), 26),
 (1062, Vector((1.35, 39.55, 8.05)),            Vector((0.0, 40.65, 7.95)), 30),
 (1092, Vector((1.45, 41.7, 8.15)),             Vector((-0.1, 40.6, 7.95)), 32),
 (1118, Vector((1.25, 41.0, 8.25)),             Vector((-0.55, 40.45, 8.05)), 40),
 (1138, SHW + Vector((0.45, -0.75, 0.15)),       SHW, 45),
 (1155, Vector((0.0, 42.3, 8.95)),              Vector((0.0, 44.5, 9.0)), 26),
 (1172, Vector((0.0, 43.6, 9.0)),               Vector((0.0, 53.6, 9.2)), 24),
 (1205, Vector((0.6, 46.3, 8.5)),               Vector((0.0, 52.0, 8.8)), 24),
 (1245, Vector((-1.3, 50.6, 9.0)),              Vector((0.0, 53.6, 9.4)), 28),
 (1285, Vector((-0.95, 52.3, 10.1)),            CROWN_W, 35),
 (1325, CROWN_W + Vector((-0.42, -0.3, 0.02)), CROWN_W, 60),
 (1370, CROWN_W + Vector((-0.1, -0.46, 0.06)),  CROWN_W, 60),
 (1400, XCW8 + Vector((0.9, -0.9, 0.3)),         XCW8, 35),
 (1440, XCW8 + Vector((0.55, -0.35, 0.08)),      XCW8, 32),
 (1480, XCW8 + Vector((-0.5, -0.4, 0.12)),       XCW8, 32),
 (1520, XCW8 + Vector((-0.9, -1.1, 0.35)),       XCW8, 30),
 (1565, Vector((-0.6, 47.2, 8.6)),              Vector((0.0, 52.6, 8.9)), 26),
 (1620, Vector((0.2, 46.2, 8.75)),              Vector((0.0, 53.0, 9.1)), 26),
]
K.sort(key=lambda k: k[0])
cpos = catmull([(k[0], k[1]) for k in K]); ctgt = catmull([(k[0], k[2]) for k in K]); clen = pchip([(k[0], float(k[3])) for k in K])
cam = bpy.data.objects.new("CAM", bpy.data.cameras.new("CAM")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.sensor_width = 36; cam.data.clip_start = 0.01; cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 3.2
foc = bpy.data.objects.new("CamFocus", None); sc.collection.objects.link(foc); cam.data.dof.focus_object = foc
prev = None
for f in range(1, 1621):
    p = cpos(f); t = ctgt(f)
    q = (t - p).to_track_quat('-Z', 'Y'); e = q.to_euler('XYZ', prev) if prev else q.to_euler('XYZ'); prev = e
    cam.location = p; cam.rotation_euler = e; cam.data.lens = clen(f)
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f); cam.data.keyframe_insert("lens", frame=f)
    foc.location = t; foc.keyframe_insert("location", frame=f)
sc.frame_set(1)
import json
beats = [(1, "He fired straight at the Pope"), (265, "Two bullets tore through"), (505, "He collapsed, badly wounded"), (631, "but survived after emergency surgery"),
         (763, "And years later, the Pope publicly forgave"), (1015, "and even met him face to face"), (1153, "He later had one of the bullets placed"), (1375, "believing that God had guided it")]
json.dump([{"beat": i + 1, "frame": f, "first_words": w} for i, (f, w) in enumerate(beats)], open(os.path.join(os.path.dirname(OUT), "beats.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
