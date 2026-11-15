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
def mixed_coords(me):
    """vertex positions with the MPFB phenotype shape keys applied"""
    if not me.shape_keys: return [v.co.copy() for v in me.vertices]
    kbs = me.shape_keys.key_blocks; base = [d.co.copy() for d in kbs[0].data]; out = [c.copy() for c in base]
    for kb in kbs[1:]:
        if kb.mute or kb.value == 0: continue
        for i, d in enumerate(kb.data): out[i] += kb.value * (d.co - base[i])
    return out
def bake_keys(me):
    if not me.shape_keys: return
    mc = mixed_coords(me); tmp = bpy.data.objects.new("_tmp", me)
    tmp.shape_key_clear(); bpy.data.objects.remove(tmp)
    for v, c in zip(me.vertices, mc): v.co = c
def transfer_weights(dst, body, rig):
    for vg in body.vertex_groups: dst.vertex_groups.new(name=vg.name)
    dt = dst.modifiers.new("dt", 'DATA_TRANSFER'); dt.object = body; dt.use_vert_data = True
    dt.data_types_verts = {'VGROUP_WEIGHTS'}; dt.vert_mapping = 'POLYINTERP_NEAREST'
    bpy.context.view_layer.objects.active = dst
    bpy.ops.object.datalayout_transfer(modifier="dt"); bpy.ops.object.modifier_apply(modifier="dt")
    am = dst.modifiers.new("arm", 'ARMATURE'); am.object = rig
    dst.parent = rig
def cassock(rig, mat):
    body = body_of(rig); vs = mixed_coords(body.data)
    H = max(v.z for v in vs); seg = 72
    zs = [0.07 * H + (0.5 * H - 0.07 * H) * i / 22 for i in range(23)]   # top tucked under the jacket hem (no visible waist rim)
    prof = []
    cy = rig.data.bones["root"].head_local.y
    for z in zs:
        band = [v for v in vs if abs(v.z - z) < 0.02 and abs(v.x) < (0.2 if z > 0.45 * H else 0.32)]   # waist: torso only (not the hanging arms)
        rx = max((abs(v.x) for v in band), default=0.15); ry = max((abs(v.y - cy) for v in band), default=0.12)
        k_ = len(prof); tm = min(1.0, (22 - k_) / 3.0)      # top rings hug the waist (no open rim seen from above)
        prof.append([z, rx + 0.012 + 0.038 * tm, ry + 0.015 + 0.045 * tm])
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
    bm.faces.new(rings[-1])          # closed top (a waist band seen from above, never an open rim)
    bm.to_mesh(me); o = bpy.data.objects.new(rig.name + "_Cassock", me); me.materials.append(mat)
    for p in me.polygons: p.use_smooth = True
    for c in rig.users_collection: c.objects.link(o)
    transfer_weights(o, body, rig)
    # explicit skinning: hips carry the skirt, thighs pull the lower hem a little (no lift into the torso when he slumps)
    for g in list(o.vertex_groups): o.vertex_groups.remove(g)
    gR, gL_, gR_, gS = (o.vertex_groups.new(name=n_) for n_ in ("root", "upperleg01.L", "upperleg01.R", "spine05"))
    zt, zb = zs[-1], zs[0]
    for v in me.vertices:
        t = max(0.0, min(1.0, (zt - v.co.z) / (zt - zb))); sl = max(0.0, min(1.0, 0.5 + v.co.x / 0.3))
        wl, wr = 0.35 * t * sl, 0.35 * t * (1 - sl)
        ws = max(0.0, (v.co.z - (zt - 0.12)) / 0.12) * 0.7          # top 12 cm -> spine05
        gS.add([v.index], ws, 'REPLACE') if ws > 0.001 else None
        gR.add([v.index], max(0.0, 1 - wl - wr - ws), 'REPLACE')
        if wl > 0.001: gL_.add([v.index], wl, 'REPLACE')
        if wr > 0.001: gR_.add([v.index], wr, 'REPLACE')
    s = o.modifiers.new("sol", 'SOLIDIFY'); s.thickness = 0.012
    o.modifiers.new("sub", 'SUBSURF').levels = 1
    # sash at the waist
    return o
def shell(rig, name, pred, offset, mat, keep_groups=True):
    body = body_of(rig)
    me = body.data.copy(); bake_keys(me); o = bpy.data.objects.new(rig.name + "_" + name, me)
    for c in rig.users_collection: c.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(me)
    dl = bm.verts.layers.deform.active
    names = {vg.index: vg.name for vg in body.vertex_groups}
    keep = set()
    for f in bm.faces:
        if any(names[k] in ("HelperGeometry", "JointCubes") and v[dl][k] > 0.5 for v in f.verts for k in (v[dl].keys() if dl else [])): continue
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
lb = latex.node_tree.nodes["Principled BSDF"]; lb.inputs['Base Color'].default_value = (0.55, 0.66, 0.75, 1); lb.inputs['Roughness'].default_value = 0.3
lb.inputs['Subsurface Weight'].default_value = 0.3
maskm = bpy.data.materials["SurgDrape"]

def glove_paint(rig):
    """latex gloves = the MPFB hand itself with a glove colour (vertex-weight mask -> colour attribute -> body shader)"""
    body = body_of(rig); me = body.data
    gi = {g.index: g.name for g in body.vertex_groups}
    att = me.color_attributes.new("glove", 'FLOAT_COLOR', 'POINT')
    for v in me.vertices:
        w = sum(g.weight for g in v.groups if gi[g.group].startswith(("finger", "metacarpal", "wrist")))
        w = max(w, 0.0)
        att.data[v.index].color = (min(1, w * 1.6),) * 3 + (1,)
    for i, m in enumerate(me.materials):
        if not m or not m.node_tree: continue
        m2 = m.copy(); me.materials[i] = m2; nt = m2.node_tree
        bs = next((x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED'), None)
        if not bs: continue
        at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = "glove"
        src = bs.inputs['Base Color'].links[0].from_socket if bs.inputs['Base Color'].links else None
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['B'].default_value = (0.62, 0.68, 0.72, 1)
        if src: nt.links.new(src, mx.inputs['A'])
        else: mx.inputs['A'].default_value = bs.inputs['Base Color'].default_value
        nt.links.new(at.outputs['Fac'], mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], bs.inputs['Base Color'])
        for sock in ('Subsurface Weight',):
            if bs.inputs[sock].links: continue
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = bs.inputs['Roughness'].default_value; mr.inputs['To Max'].default_value = 0.3
        if not bs.inputs['Roughness'].links:
            nt.links.new(at.outputs['Fac'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], bs.inputs['Roughness'])
def setup_heroes():
    pope = O["Pope"]
    cm_ = bpy.data.materials.new("CassockWhite"); cm_.use_nodes = True; nt_ = cm_.node_tree; bs_ = nt_.nodes["Principled BSDF"]
    bs_.inputs['Base Color'].default_value = (0.93, 0.9, 0.84, 1); bs_.inputs['Roughness'].default_value = 0.75; bs_.inputs['Sheen Weight'].default_value = 0.4
    nz_ = nt_.nodes.new('ShaderNodeTexNoise'); nz_.inputs['Scale'].default_value = 400; bp_ = nt_.nodes.new('ShaderNodeBump'); bp_.inputs['Strength'].default_value = 0.08
    nt_.links.new(nz_.outputs['Fac'], bp_.inputs['Height']); nt_.links.new(bp_.outputs['Normal'], bs_.inputs['Normal'])
    cas = cassock(pope, cm_); cas.data.materials[0] = cm_
    hb = pope.data.bones["head"]; ht = hb.tail_local; top = max(c.z for c in mixed_coords(body_of(pope).data))
    shell(pope, "Zucchetto", lambda co, w: co.z > top - 0.05 and co.y > hb.head_local.y - 0.03, 0.03, skull_m)
    for nm in ("SurgA", "SurgB", "SurgC", "Nurse"):
        r = O[nm]; hb = r.data.bones["head"]; hh, ht = hb.head_local, hb.tail_local; top = max(c.z for c in mixed_coords(body_of(r).data))
        gl = shell(r, "Gloves", is_hand, 0.0012, latex)
        for md in list(gl.modifiers):
            if md.type in ('SOLIDIFY', 'SUBSURF'): gl.modifiers.remove(md)
        shell(r, "Cap", lambda co, w, top=top, hh=hh: co.z > top - 0.085 and co.y > hh.y - 0.075, 0.014, maskm)
        shell(r, "Mask", lambda co, w, hh=hh, top=top: top - 0.225 < co.z < top - 0.135 and co.y < hh.y - 0.045 and abs(co.x) < 0.07, 0.014, bpy.data.materials["WhiteWool"])
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
            pass
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
        hand_at(h, s, f, (sx * 0.36, -0.05 + sw * math.sin(f * 0.07 + sx), 0.96), d=(0.0, 0, -1), n=(sx, 0, 0))
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

CURL_SIGN = 1.0
def curl(rig, s, f, amt, thumb=None, spread=0.0):
    """finger flexion (deg per joint); thumb separately"""
    for fi in range(1, 6):
        a_ = (thumb if thumb is not None else amt * 0.6) if fi == 1 else amt
        for seg in (1, 2, 3):
            b = rig.pose.bones.get("finger%d-%d.%s" % (fi, seg, s))
            if not b: continue
            b.rotation_mode = 'QUATERNION'
            b.rotation_quaternion = Quaternion((1, 0, 0), R_(CURL_SIGN * a_ * (0.7 if seg == 1 else 1.0)))
            b.keyframe_insert("rotation_quaternion", frame=f)

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
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -12.0 - 0.85 + 0.1, FLOOR - 0.02)); bed = bpy.context.object; bed.name = "JeepBedFloor"
bed.scale = (1.3, 1.9, 0.04); bed.data.materials.append(bpy.data.materials["PaintedMetal"])
for c in list(bed.users_collection): c.objects.unlink(bed)
bpy.data.collections["Square"].objects.link(bed)
cb = bed.constraints.new('CHILD_OF'); cb.target = jeep; ev(1); cb.inverse_matrix = jeep.matrix_world.inverted()
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
    return f      # v007: real time (the Pope reacts to the hit on screen)
def belly_targets(f, push=0.06):
    """wrist targets (Pope-local) that put both palms on the front of his suit at the stomach (ray cast on the suit)"""
    ev(f)
    suit = O["Pope.male_elegantsuit01"]; es = suit.evaluated_get(bpy.context.evaluated_depsgraph_get())
    c3 = bone_w(pope, "spine03") + Vector((0, 0, 0.03)); fw = pope.matrix_world.to_3x3() @ Vector((0, -1, 0)); si = suit.matrix_world.inverted()
    out = []
    for dx in (0.0, -0.11):
        o_ = c3 + fw * 0.6 + (pope.matrix_world.to_3x3() @ Vector((dx, 0, 0))) + Vector((0, 0, -0.03 - 0.1 * (dx != 0)))
        ok, hl, hn, _ = es.ray_cast(si @ o_, (si.to_3x3() @ -fw).normalized())
        bw = (suit.matrix_world @ hl) if ok else c3 + fw * 0.2
        out.append(pope.matrix_world.inverted() @ (bw + fw * push + Vector((0, 0, 0.03))))
    return out
HIT = 258
for f in list(range(1, 505, 3)) + [505]:
    t = tw(f)
    wave = math.sin(t * 0.16)
    if f >= HIT:      # v007: the hit read on screen -- flinch, right hand clutches the stomach, the wounded left hand jerks back
        h_ = smooth((f - HIT) / 8.0); s2 = smooth((f - 300) / 200.0)
        stand(P, f, flex=4 + 10 * h_ + 6 * s2, twist=-6 * h_, head=(-6 - 8 * h_ + 4 * s2, 6 * h_))   # v008: head up, the pain shows on his face
        Wl_, Wr_ = belly_targets(f)
        w0 = math.sin(HIT * 0.16)
        r0 = Vector((-0.32 + 0.07 * w0, -0.12, 1.72 + 0.03 * math.cos(HIT * 0.16)))
        jr = smooth((f - HIT - 2) / 14.0)
        hand_at(P, "R", f, tuple(r0.lerp(Wr_, jr)), d=tuple(Vector((0, 0, 1)).lerp(Vector((0.9, -0.15, -0.1)), jr)),
                n=tuple(Vector((0, -1, 0.2)).lerp(Vector((0, 1, 0)), jr)), pole=(-0.75, -0.1, 0.95))
        kick = math.exp(-max(0, f - HIT) / 5.0) * h_
        lp = Vector((0.33, -0.28, 1.56)).lerp(Vector((0.15, -0.3, 1.24)), smooth((f - HIT - 4) / 26.0)) + Vector((0.06, 0.12, 0.1)) * kick
        hand_at(P, "L", f, tuple(lp), d=(0, -0.5, 0.6), n=(-0.3, -1, 0), pole=(0.7, 0.2, 1.0))
        face(pope, f, brow=-0.95 * h_, lids=0.85 * h_, jaw=16 * h_ * (1 - 0.3 * s2))   # eyes squeezed, mouth open
        continue
    stand(P, f, flex=4 + 2 * math.sin(t * 0.03), twist=8 * math.sin(t * 0.02), head=(-4 + 3 * math.sin(t * 0.05), 10 * math.sin(t * 0.025)))
    hand_at(P, "R", f, (-0.32 + 0.07 * wave, -0.12, 1.72 + 0.03 * math.cos(t * 0.16)), d=(0, 0, 1), n=(0, -1, 0.2), pole=(-0.6, 0.3, 1.2))
    if f < 200:
        hand_at(P, "L", f, (0.2, -0.36, 1.08), d=(0.1, -0.8, -0.6), n=(0.2, -0.3, -1), pole=(0.7, 0.1, 1.0))
    else:   # raises left hand too (greeting) -> hit in the hand
        u = smooth((t - 200) / 30)
        hand_at(P, "L", f, (0.13 + 0.2 * u, -0.33 + 0.05 * u, 1.06 + 0.5 * u), d=(0, -0.6 * (1 - u), -0.8 + 1.8 * u), n=(0, -1, 0), pole=(0.6, 0.2, 1.0))
    face(pope, f, brow=0.4, smile=0.6)
# hit + collapse 500..630: doubles over at the hit, knees give, the aides lower him back onto the rear bench (feet stay planted)
SEAT_Y, SEAT_TOP = 0.3, 0.42
ev(505)
bpy.ops.mesh.primitive_cube_add(size=1); bench = bpy.context.object; bench.name = "JeepBench"
bench.scale = (0.62, 0.36, SEAT_TOP); bpy.ops.object.transform_apply(scale=True)
bench.data.materials.append(bpy.data.materials["PaintedMetal"]); bench.modifiers.new("b", 'BEVEL').width = 0.02
for c in list(bench.users_collection): c.objects.unlink(bench)
bpy.data.collections["Square"].objects.link(bench)
bench.matrix_world = Matrix.Translation(pope_root_obj(505) + Mrot.to_3x3() @ Vector((0, SEAT_Y, SEAT_TOP / 2))) @ Mrot
cbn = bench.constraints.new('CHILD_OF'); cbn.target = jeep; cbn.inverse_matrix = jeep.matrix_world.inverted()
for f in range(505, 640, 3):
    u = smooth((f - 500) / 20); v = smooth((f - 522) / 62)
    rh = P.root_head
    p = Vector((rh.x, rh.y + (SEAT_Y + 0.02) * v, rh.z - (rh.z - SEAT_TOP - 0.12) * v - 0.05 * u * (1 - v)))
    P.key_root(f, p, flex=12 * u * (1 - v) - 6 * v, side=0.0)
    P.key_spine(f, flex=30 * u * (1 - v) + 6 * v, twist=0.0, side=0.0, head=(28 * u * (1 - v) + 12 * v, -14 * v))
    for s_ in "LR":
        P.key_foot(s_, f, Vector((P.ankle[s_].x, P.ankle[s_].y)), 0.0)
    ev(f)
    suit = O["Pope.male_elegantsuit01"]; es = suit.evaluated_get(bpy.context.evaluated_depsgraph_get())
    c3 = bone_w(pope, "spine03") + Vector((0, 0, 0.03)); fw = pope.matrix_world.to_3x3() @ Vector((0, -1, 0))
    si = suit.matrix_world.inverted()
    ok, hl, hn, _ = es.ray_cast(si @ (c3 + fw * 0.6 + Vector((0.0, 0, -0.03))), (si.to_3x3() @ -fw).normalized())
    belly = (suit.matrix_world @ hl) if ok else c3 + fw * 0.2
    Wl = pope.matrix_world.inverted() @ (belly + fw * (0.06 + 0.03 * u * (1 - v)) + Vector((0, 0, 0.03)))
    hand_at(P, "L", f, tuple(Wl), d=(-0.9, -0.15, -0.1), n=(0, 1, 0), pole=(0.75, -0.2, 0.9))
    ok2, hl2, hn2, _ = es.ray_cast(si @ (c3 + fw * 0.6 + (pope.matrix_world.to_3x3() @ Vector((-0.11, 0, 0))) + Vector((0, 0, -0.04))), (si.to_3x3() @ -fw).normalized())
    belly2 = (suit.matrix_world @ hl2) if ok2 else c3 + fw * 0.2 + Vector((0, 0, -0.1))
    Wr = pope.matrix_world.inverted() @ (belly2 + fw * (0.06 + 0.03 * u * (1 - v)) + Vector((0, 0, 0.03)))
    hand_at(P, "R", f, tuple(Wr), d=(0.9, -0.15, -0.1), n=(0, 1, 0), pole=(-0.75, -0.2, 0.9))
    face(pope, f, brow=-0.8 * u, lids=0.25 + 0.4 * v, jaw=12 * u * (1 - v) + 4 * v)
# aides stand behind him in the bed, catch under the arms
AIDES = (("AideA", Vector((0.68, 0.5))), ("AideB", Vector((-0.72, 0.6))))
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
            Aw = bone_w(pope, "upperarm01." + side); Cw = bone_w(pope, "spine02")
            W = r.matrix_world.inverted() @ (Aw + (Aw - Cw).normalized() * 0.13)
            # outer hand rests on top of his shoulder (surface from a ray onto the suit), fingertips forward over it
            Sw = bone_w(pope, "shoulder01." + side) * 0.5 + bone_w(pope, "upperarm01." + side) * 0.5
            suit_ = O["Pope.male_elegantsuit01"]; es_ = suit_.evaluated_get(bpy.context.evaluated_depsgraph_get()); si_ = suit_.matrix_world.inverted()
            okS, hS, nS, _ = es_.ray_cast(si_ @ (Sw + Vector((0, 0, 0.4))), (si_.to_3x3() @ Vector((0, 0, -1))).normalized())
            topS = (suit_.matrix_world @ hS) if okS else Sw + Vector((0, 0, 0.09))
            fwP = pope.matrix_world.to_3x3() @ Vector((0, -1, 0))
            ddS = (fwP + Vector((0, 0, -0.35))).normalized()
            W2 = r.matrix_world.inverted() @ (topS + Vector((0, 0, 0.02)) - ddS * 0.1 + Vector((0, 0, 0.015)))
            u = smooth((f - 505) / 18); v2 = smooth((f - 522) / 62)
            stand(h, f, flex=8 + 13 * u + 4 * v2, head=(4 * u, sx * 22 * u), crouch=0.1 * u + 0.12 * v2)   # head up, turned to him (not bowed onto the raised hand)
            base_o = Vector((sx * 0.24, -0.02, 0.86))
            inner, outer = ("L", "R") if sx < 0 else ("R", "L")
            Wi = Vector((-sx * 0.3, -0.03, 0.9)).lerp(W + Vector((0, -0.07, -0.08)), u)
            hand_at(h, inner, f, tuple(Wi), d=(-sx * 0.3, -0.5, 0.5), n=(-sx, 0, 0), pole=(sx * 0.15, 0.5, 0.85))
            crc = 0.1 * u + 0.12 * v2
            hand_at(h, outer, f, (sx * 0.37, -0.1, 0.98 - crc), d=(0, -0.2, -1), n=(sx, 0, 0))     # outer hand relaxed at his side
        face(r, f, brow=(-0.5 if f > 505 else 0.0), jaw=(8 if f > 510 else 0))
# guards: walk beside, then rush in
for i, nm in enumerate(("GuardA", "GuardB")):
    r = O[nm]; h = HUM[nm]; sx = 1 if i == 0 else -1
    r.location = (0, 0, 0); r.rotation_euler = (0, 0, 0)
    path = lambda f, sx=sx: Vector((sx * 1.4, (JY(tw(f)) if tw(f) < 380 else -2.0) + 0.4, 0)) if f < 505 else \
        Vector((sx * (1.4 - 0.2 * smooth((f - 505) / 60)), -2.0 + 0.4 - 0.9 * smooth((f - 505) / 60), 0))
    h.walk(path, lambda f: 180.0 if f < 505 else 180.0 + sx * 40, 1, 638, stride=0.7, step=3)
    yawf = lambda f, sx=sx: 180.0 if f < 505 else 180.0 + sx * 40
    for f in range(1, 640, 3):          # hands hang at his sides and swing with the walk (targets follow the walking root)
        pf = path(f); Rz = Matrix.Rotation(R_(yawf(f)), 3, 'Z'); sw_ = 0.07 * math.sin(f * 0.11)
        rx_ = smooth((f - 262) / 10.0) if 262 <= f < 505 else 0.0
        if rx_ > 0:
            h.key_spine(f, flex=6 * rx_, twist=-sx * 25 * rx_, side=0.0, head=(0, -sx * 35 * rx_))     # turn toward the shot / the Pope
        for s_, sg in (("L", 1), ("R", -1)):
            off = Rz @ Vector((sg * 0.25, -0.08 + sg * sw_ * 1.4, 0.0))
            W = Vector((pf.x + off.x, pf.y + off.y, 0.92))
            if rx_ > 0:
                inner = (sg == 1) == (sx > 0)      # the hand on the jeep side reaches for the Pope, the other comes up in alarm
                reach_ = (Vector((pf.x - sx * 0.5, pf.y + 0.2, 1.2)) if inner else Vector((pf.x, pf.y, 0)) + Rz @ Vector((sg * 0.22, -0.3, 1.05)))
                W = W.lerp(reach_, rx_)
            d = Rz @ Vector((0, -0.15, -1)); nrm = Rz @ Vector((sg, 0, 0))
            hand_at(h, s_, f, tuple(W), d=tuple(d), n=tuple(nrm), pole=tuple(W + Rz @ Vector((sg * 0.2, 0.45, 0.35))))

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
    for row in range(4):
        for k in range(10):
            y = -17.5 + k * 3.2 + random.uniform(-0.5, 0.5) + row * 1.1
            x = side * (3.4 + row * 0.75 + random.uniform(-0.15, 0.15))
            crowd.append((x, y))
SHOOTER = Vector((-3.45, 1.6))
crowd = [c for c in crowd if (Vector(c) - SHOOTER).length > 1.4]
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
        aL = ("Y", 48 - 8 * gasp); aR = ("Y", -48 + 8 * gasp)   # arms stay down at the sides, hands come up to the chest (no T-pose)
        R.key_rot("upperarm01.L", f, [aL, ("X", -55 * gasp)]); R.key_rot("upperarm01.R", f, [aR, ("X", -55 * gasp)])
        R.key_rot("lowerarm01.L", f, [("X", -120 * gasp), ("Z", 30 * gasp)]); R.key_rot("lowerarm01.R", f, [("X", -120 * gasp), ("Z", -30 * gasp)])
        return
    if kind == "wave":
        R.key_rot("upperarm01.R", f, [("Y", 92 + 6 * w), ("X", -22)]); R.key_rot("lowerarm01.R", f, [("X", -40), ("Y", 12 + 20 * w)])
        R.key_rot("upperarm01.L", f, [("Y", 50 + 3 * s), ("X", -8)]); R.key_rot("lowerarm01.L", f, [("X", -30)])
    elif kind == "cheer":
        R.key_rot("upperarm01.R", f, [("Y", 95 + 8 * w), ("X", -25)]); R.key_rot("upperarm01.L", f, [("Y", -95 - 8 * w), ("X", -25)])
        R.key_rot("lowerarm01.R", f, [("X", -38)]); R.key_rot("lowerarm01.L", f, [("X", -38)])
    elif kind == "clap":
        c = 0.5 + 0.5 * math.sin(t * 0.35 + ph)
        R.key_rot("upperarm01.L", f, [("Y", 38), ("X", -50)]); R.key_rot("upperarm01.R", f, [("Y", -38), ("X", -50)])
        R.key_rot("lowerarm01.L", f, [("X", -95 - 12 * c)]); R.key_rot("lowerarm01.R", f, [("X", -95 - 12 * c)])   # v008: hands meet in front (no T)
    else:
        R.key_rot("upperarm01.L", f, [("Y", 50 + 3 * s), ("X", -8)]); R.key_rot("upperarm01.R", f, [("Y", -50 - 3 * s), ("X", -8)])
        R.key_rot("lowerarm01.L", f, [("X", -32 - 4 * s)]); R.key_rot("lowerarm01.R", f, [("X", -32 + 4 * s)])
for pb in shooter.pose.bones: pb.rotation_mode = 'QUATERNION'
for (r, x, y, kind, ph) in CR:
    for pb in r.pose.bones: pb.rotation_mode = 'QUATERNION'
    R = Rig(r)
    # square: face the lane; years later (balcony beat) the same people stand below the balcony facing the facade
    yaw_sq = R_(yaw_to(-x, 0.6 * random.uniform(-1, 1)))
    bx, by = random.uniform(-9, 9), random.uniform(18, 31)
    key_obj(r, 1, loc=(x, y, 0), rot=(0, 0, yaw_sq), interp='CONSTANT')
    key_obj(r, 700, loc=(bx, by, 0), rot=(0, 0, R_(yaw_to(-bx * 0.2, 33 - by)) + random.uniform(-0.3, 0.3)), interp='CONSTANT')
    for f in list(range(1, 640, 8)) + list(range(700, 1020, 8)):
        t = tw(f) if f < 640 else f
        g = smooth((f - 512) / 18) if 505 < f < 640 else 0.0
        look = 0.0
        fk_pose(R, f, kind if f < 640 else random.choice(("wave", "cheer", "clap")) if f == 700 else kind, ph, t, gasp=g)
# shooter: in the second row on the left, gun hand rising from the crowd (seen from behind)
Rs = Rig(shooter)
key_obj(shooter, 1, loc=(SHOOTER.x, SHOOTER.y, 0), rot=(0, 0, R_(yaw_to(0.55, -0.83))), interp='CONSTANT')   # aims at the jeep
key_obj(shooter, 700, loc=(0, 0, -60), interp='CONSTANT')
for f in range(1, 640, 3):
    t = tw(f); u = smooth((t - 8) / 40)
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
for f, e in ((1, 0),):          # v008: no flash light (it washed out the shooter's hair)
    fl.data.energy = e; fl.data.keyframe_insert("energy", frame=f)
fm_, fe = emis("FlashMat", (1.0, 0.62, 0.15), 0.0)
bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.0, radius2=0.03, depth=0.08); flash = bpy.context.object; flash.name = "MuzzleFlash"
flash.data.materials.append(fm_); fe.inputs['Strength'].default_value = 12.0
flash.parent = pistol; flash.matrix_parent_inverse.identity(); flash.location = (0, 0.11 + 0.045, 0.04); flash.rotation_euler = (R_(-90), 0, 0)   # small orange cone pointing out of the muzzle
flash.visible_shadow = False; flash.visible_diffuse = False; flash.visible_glossy = False
key_vis(flash, ((1, False), (255, True), (258, False)))

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
H = max(c.z for c in mixed_coords(body_of(pope).data))
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
XR_H = ((1, 0.0), (392, 0.0), (404, 1.0), (488, 1.0), (500, 0.0))
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
    a_ = sph(XC, 0.2, 0.32, "XRT", XR_T); b_ = sph(XH, 0.07, 0.12, "XRH", XR_H)
    mx = n.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'; l.new(a_.outputs[0], mx.inputs[0]); l.new(b_.outputs[0], mx.inputs[1])
    return mx
done = set()
for ob in [c for c in O if c.parent == pope and c.type == 'MESH']:
    for m in ob.data.materials:
        if not m or m.name in done or not m.node_tree: continue
        if m.name.startswith("CassockWhite"): continue
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
O["bars"].hide_render = True; O["bars"].hide_viewport = True
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
l.new(sep.outputs['Z'], cr.inputs['Fac'])
cr.color_ramp.elements[0].color = (0.8, 0.93, 1.0, 1); cr.color_ramp.elements[1].color = (0.078, 0.55, 0.93, 1)
cr.color_ramp.elements[0].position = 0.25; cr.color_ramp.elements[1].position = 0.85
em = n.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.1; l.new(cr.outputs['Color'], em.inputs['Color'])
tr = n.new('ShaderNodeBsdfTransparent'); ms = n.new('ShaderNodeMixShader'); fv = n.new('ShaderNodeValue'); fv.name = "DomeFade"
for f, x in ((1, 0), (322, 0), (330, 1), (490, 1), (502, 0), (1395, 0), (1412, 1), (1512, 1), (1540, 0)):
    fv.outputs[0].default_value = x; fv.outputs[0].keyframe_insert("default_value", frame=f)
bfm = n.new('ShaderNodeMath'); bfm.operation = 'MULTIPLY'; l.new(fv.outputs[0], bfm.inputs[0]); l.new(geo.outputs['Backfacing'], bfm.inputs[1])   # seen only from inside: no wash when the camera leaves it
l.new(bfm.outputs[0], ms.inputs['Fac']); l.new(tr.outputs['BSDF'], ms.inputs[1]); l.new(em.outputs[0], ms.inputs[2])
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
key_vis(bul, ((1, False),))
# shimmer streak behind the bullet
smat, se = emis("Streak", (1.0, 0.9, 0.75), 3.0)
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
bmesh.ops.create_grid(bm, x_segments=40, y_segments=60, size=0.5); bm.to_mesh(drape)
for v in drape.vertices:      # 1.15 m x 1.45 m sheet: flat on the pad, hanging down past the table edges
    v.co.x *= 1.15; v.co.y *= 1.45
    ex = max(0.0, abs(v.co.x) - 0.28); v.co.z = -ex * 1.1 + 0.015 * math.sin(v.co.y * 40 + v.co.x * 7)
    if ex > 0: v.co.x = math.copysign(0.28 + ex * 0.25, v.co.x)
dro = bpy.data.objects.new("Drape", drape); bpy.data.collections["Theatre"].objects.link(dro)
dro.location = (-8.0, 40.5 - 0.25, tz + 0.012); drape.materials.append(bpy.data.materials["SurgDrape"])
# drape over the patient: a body-shaped rise (feet low, chest high) over the pad, edges hanging off the table
ev(700); dgd = bpy.context.evaluated_depsgraph_get(); pts = []
for ch_ in [c for c in pope.children if c.type == 'MESH' and not c.hide_render and not c.name.endswith(("_Cassock",))]:
    me_ = ch_.evaluated_get(dgd).to_mesh(); pts += [ch_.matrix_world @ v.co for v in me_.vertices]; ch_.evaluated_get(dgd).to_mesh_clear()
BAND = {}
for p_ in pts:
    if p_.y < 40.98 and abs(p_.x - dro.location.x) < 0.34:
        k_ = int(round(p_.y / 0.05)); BAND[k_] = max(BAND.get(k_, -9), p_.z)
def band_h(y):
    ks = [BAND.get(int(round(y / 0.05)) + d_, None) for d_ in (-2, -1, 0, 1, 2)]
    ks = [k for k in ks if k is not None]
    return (sum(ks) / len(ks)) if ks else None
for v in drape.vertices:
    w = dro.location + v.co
    hb = band_h(w.y)
    if hb is not None:
        dx = abs(w.x - dro.location.x); prof = max(0.0, 1 - (dx / 0.36) ** 4) ** 0.5
        v.co.z = max(v.co.z, (hb - dro.location.z + 0.07) * prof)
def drape_z(x, y):
    best = None
    for v in drape.vertices:
        w = dro.location + v.co
        if abs(w.x - x) < 0.03 and abs(w.y - y) < 0.03: best = max(best or -9, w.z)
    return best if best is not None else tz
sw = dro.modifiers.new("smooth0", 'SMOOTH'); sw.factor = 0.9; sw.iterations = 14   # soft cloth over the patient, no blocky ridges
dro.modifiers.new("sol", 'SOLIDIFY').thickness = 0.006
dro.modifiers.new("sub", 'SUBSURF').levels = 2; dro.modifiers["sub"].render_levels = 2
key_vis(dro, ((1, False), (631, True), (763, False)))
key_vis(O["Pope_Cassock"], ((1, True), (631, False), (763, True)))
# camera leaves the theatre through its wall and the facade: hide them from camera rays for that pass (no blank wall frames)
for nm_, f0_, f1_ in (("Theatre", 765, 777), ("Facade", 765, 777)):
    o_ = O[nm_]
    for f_, v_ in ((1, True), (f0_, False), (f1_, True)):
        o_.visible_camera = v_; o_.keyframe_insert("visible_camera", frame=f_)
    for fc in fcurves(o_.animation_data.action):
        if fc.data_path == "visible_camera":
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
# the cell gate slides open on the 'face to face' beat, before the camera passes through the doorway
cd_ = O["celldoor"]
for f_, x_ in ((1, 0.0), (1000, 0.0), (1024, 2.9)):
    cd_.location.x = x_; cd_.keyframe_insert("location", index=0, frame=f_)
TEAM = (("SurgA", Vector((-8.72, 40.62)), 90), ("SurgB", Vector((-7.28, 40.58)), -90),   # level with the abdomen they work on
         ("SurgC", Vector((-8.0, 41.55)), 0), ("Nurse", Vector((-7.0, 41.3)), -51))
O["InstrumentTray"].location = (-7.32, 40.98, 8.0); O["TrayStand"].location = (-7.32, 40.98, 7.5)
HANDS_ON = {"SurgA": ((-8.13, 40.5), (-8.13, 40.74)), "SurgB": ((-7.87, 40.46), (-7.87, 40.7)), "SurgC": ((-7.88, 40.7), (-8.12, 40.7))}   # abdomen (spine03-05 at y 40.54-40.69)
for nm, xy, yw in TEAM:
    r = O[nm]; h = HUM[nm]
    key_obj(r, 1, loc=(xy.x, xy.y, 7.0), rot=(0, 0, R_(yw)), interp='CONSTANT')
    for f in range(600, 770, 4):
        ph = hash(nm) % 7
        stand(h, f, flex=22 if nm != "Nurse" else 8, head=(25, 8 * math.sin(f * 0.03 + ph)), crouch=0.02)
        Minv = r.matrix_world.inverted() if f > 600 else None
        if Minv is None: ev(601); Minv = r.matrix_world.inverted()
        if nm == "SurgC":    # at the head end: sterile pose, gloved hands raised in front of the chest, touching nothing
            for s_, dx in (("R", -0.11), ("L", 0.11)):
                tw_ = Vector((xy.x + dx, xy.y - 0.24, 8.22 + 0.01 * math.sin(f * 0.07)))   # at his own chest, well clear of the patient's head
                hand_at(h, s_, f, tuple(Minv @ tw_), d=tuple(Minv.to_3x3() @ Vector((0, -0.2, 1))), n=tuple(Minv.to_3x3() @ Vector((0, -1, 0))))
        elif nm == "Nurse":
            for s_, dx in (("R", -0.13), ("L", 0.13)):
                tw_ = Vector((-7.32 + dx * 0.6, 40.98 + dx * 0.8, 8.03 + 0.012))
                hand_at(h, s_, f, tuple(Minv @ tw_), d=tuple(Minv.to_3x3() @ Vector((-0.6, -0.5, -0.4))), n=tuple(Minv.to_3x3() @ Vector((0, 0, -1))))
        else:
            for s_, (hx, hy) in zip(("R", "L"), HANDS_ON[nm] if nm == "SurgA" else HANDS_ON[nm][::-1]):
                wob = 0.015 * math.sin(f * 0.11 + ph + (0 if s_ == "R" else 1.7))
                fwd_ = (Vector((hx, hy, 0)) - Vector((xy.x, xy.y, 0))).normalized()
                tip = Vector((hx + wob, hy + wob * 0.6, 0)); tip.z = drape_z(tip.x, tip.y) + 0.06
                dd = (fwd_ + Vector((0, 0, -0.2))).normalized()
                tw_ = tip - dd * 0.1 + Vector((0, 0, 0.02))
                hand_at(h, s_, f, tuple(Minv @ tw_), d=tuple(Minv.to_3x3() @ dd), n=tuple(Minv.to_3x3() @ Vector((0, 0, -1))))
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
light("TheatreFill1", 'AREA', (-10.5, 39, 10.8), 600, (0.85, 0.95, 1.0), 1.5)
light("TheatreFill2", 'AREA', (-5.5, 43, 10.8), 600, (0.85, 0.95, 1.0), 1.5)
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
for nm in ("GuardA", "GuardB"):       # guards are in the square only (they had no object keys, so a lone 700 key hid them for the whole film)
    key_obj(O[nm], 1, loc=Vector((0, 0, 0)), interp='CONSTANT'); key_obj(O[nm], 700, loc=Vector((0, 0, -60)), interp='CONSTANT')
key_obj(O["AideB"], 700, loc=O["AideB"].location.copy() + Vector((0, 0, -60)), interp='CONSTANT')

# ------------------------------------------------------------------ CELL 1015..1152
pris = O["Prisoner"]; PR = HUM["Prisoner"]
SEAT = 0.47
key_obj(pope, 1015, loc=Vector((-0.55, 40.45, 7.0)), rot=(0, 0, R_(90 + 180) - R_(180) + R_(-90) + R_(180)), interp='CONSTANT')
key_obj(pope, 1015, loc=Vector((-0.4, 40.66, 7.0)), rot=(0, 0, R_(135)), interp='CONSTANT')   # faces +X; v007: prisoner sits to his right -> right hand to the near shoulder, nothing crosses a body
key_obj(pris, 1, loc=Vector((0.4, 40.66, 7.0)), rot=(0, 0, R_(-135)), interp='CONSTANT')          # faces -X
O["ChairPope"].location = (-0.4 - 0.085, 40.66 - 0.085, 7.0); O["ChairPrisoner"].location = (0.4 + 0.085, 40.66 - 0.085, 7.0)
O["ChairPope"].rotation_euler.z += R_(45); O["ChairPrisoner"].rotation_euler.z -= R_(45)
def sit(h, f, flex=8.0, head=(0, 0), twist=0.0, knee_out=0.0):
    rh = h.root_head
    h.key_root(f, Vector((rh.x, rh.y + 0.12, SEAT + 0.12)), flex=-4)
    h.key_spine(f, flex=flex, twist=twist, head=head)
    for s in "LR":
        h.key_foot(s, f, Vector((h.ankle[s].x * (0.95 + knee_out), h.ankle[s].y - 0.42)), 0.0)
for f in range(1015, 1160, 3):
    reach = smooth((f - 1035) / 30)
    sit(P, f, flex=12 + 10 * reach + 2 * math.sin(f * 0.03), head=(4, 6 * math.sin(f * 0.04)), twist=8 * reach, knee_out=-0.25)
    # the prisoner first (his pose drives the shoulder the Pope's hand rests on)
    look = 0.5 + 0.5 * math.sin((f - 1015) * 0.045)
    nod = 4 * max(0, math.sin(f * 0.35)) * (1 if (f // 50) % 2 else 0)
    sit(PR, f, flex=8 + 3 * math.sin(f * 0.05), head=(16 - 14 * look + nod, -6 * look), knee_out=-0.25)
    hand_at(PR, "R", f, (-0.12, -0.32, 0.73), d=(0.1, -1, -0.25), n=(0, 0, -1)); hand_at(PR, "L", f, (0.12, -0.32, 0.73), d=(-0.1, -1, -0.25), n=(0, 0, -1))
    ev(f)
    Sh = bone_w(pris, "shoulder01.L") * 0.6 + bone_w(pris, "upperarm01.L") * 0.4
    shirt = O["Prisoner.male_casualsuit03"]; esh = shirt.evaluated_get(bpy.context.evaluated_depsgraph_get()); si = shirt.matrix_world.inverted()
    ok, hl, hn, _ = esh.ray_cast(si @ (Sh + Vector((0, 0, 0.4))), (si.to_3x3() @ Vector((0, 0, -1))).normalized())
    top = (shirt.matrix_world @ hl) if ok else Sh + Vector((0, 0, 0.09))
    dd = Vector((0.8, -0.55, -0.3)).normalized()                  # fingers lie over the shoulder toward his back
    tipW = top + Vector((0, 0, 0.018)); wristW = tipW - dd * 0.1 + Vector((0, 0, 0.015))
    rest = Vector((-0.14, -0.36, 0.73)); Minv_ = pope.matrix_world.inverted()
    W = rest.lerp(Minv_ @ wristW, reach) + Vector((0, -0.04, 0.08)) * math.sin(math.pi * reach)   # gentle arc to the shoulder
    hand_at(P, "R", f, tuple(W), d=tuple((Minv_.to_3x3() @ dd).lerp(Vector((-0.2, -1, -0.25)).normalized(), 1 - reach)), n=tuple(Minv_.to_3x3() @ Vector((0, 0, -1))), pole=(-0.8, 0.2, 0.9))
    hand_at(P, "L", f, (0.14, -0.34, 0.73), d=(-0.2, -1, -0.25), n=(0, 0, -1))
    face(pope, f, brow=0.3 * math.sin(f * 0.05), jaw=7 * max(0, math.sin(f * 0.3)), smile=0.15)
    face(pris, f, brow=-0.8 + 0.25 * look, lids=0.45 - 0.15 * look, jaw=3 * max(0.0, math.sin(f * 0.4)))   # moved: sorrow, trembling lip
for f in range(1, 1015, 40):
    sit(PR, f, flex=8, head=(15, 0))
    hand_at(PR, "R", f, (-0.12, -0.32, 0.73), d=(0.1, -1, -0.25), n=(0, 0, -1)); hand_at(PR, "L", f, (0.12, -0.32, 0.73), d=(-0.1, -1, -0.25), n=(0, 0, -1))
cv = bpy.data.objects.new("CellVolume", None)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 40.6, 8.6)); vb = bpy.context.object; vb.name = "CellHaze"; vb.scale = (4.9, 4.7, 3.1)
vm = bpy.data.materials.new("Haze"); vm.use_nodes = True; nn = vm.node_tree.nodes
nn.remove(nn["Principled BSDF"]); pv = nn.new('ShaderNodeVolumePrincipled'); pv.inputs['Density'].default_value = 0.008
vm.node_tree.links.new(pv.outputs[0], nn["Material Output"].inputs['Volume']); vb.data.materials.append(vm)
for c in list(vb.users_collection): c.objects.unlink(vb)
bpy.data.collections["Cell"].objects.link(vb)
L = light("CellSun", 'SPOT', (0.0, 44.6, 10.4), 6000, (1.0, 0.78, 0.5), 0.1, spot=40)
L.rotation_euler = (Vector((0, 40.8, 7.4)) - L.location).to_track_quat('-Z', 'Y').to_euler()
light("CellBounce", 'AREA', (0, 39.0, 10.0), 500, (1.0, 0.85, 0.7), 2.0)
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
key_obj(pope, 1358, loc=KNEEL, rot=(0, 0, R_(180)), interp='CONSTANT')     # faces +Y toward the statue (after he has set the bullet)
for f in range(1358, 1621, 4):
    # standing in prayer before the statue: head bowed, hands folded, slow breathing sway
    stand(P, f, flex=9 + 2 * math.sin(f * 0.03), head=(18 + 4 * math.sin(f * 0.02), 3 * math.sin(f * 0.013)), sway=0.01)
    hand_at(P, "L", f, (0.06, -0.28, 1.27 + 0.01 * math.sin(f * 0.03)), d=(0, -0.25, 1), n=(-1, 0, 0), pole=(0.5, 0.2, 0.9))
    hand_at(P, "R", f, (-0.06, -0.28, 1.27 + 0.01 * math.sin(f * 0.03)), d=(0, -0.25, 1), n=(1, 0, 0), pole=(-0.5, 0.2, 0.9))
    face(pope, f, lids=0.6, brow=0.2)
# kneeler under him
O["Pew"].location = O["Pew"].location
# cleric on a step stool places the bullet in the crown (AideB)
cl_ = O["AideB"]; CL = HUM["AideB"]
STOOL = Vector((0.75, 53.15, 7.0))
for i, (w_, h_) in enumerate(((0.62, 0.3), (0.62, 0.6))):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(STOOL.x, STOOL.y + 0.2 - i * 0.2, 7.0 + h_ - 0.03)); st = bpy.context.object; st.name = "StoolStep"
    st.scale = (w_, 0.3 if i else 0.22, 0.05); st.data.materials.append(bpy.data.materials["Wood"])
    for c in list(st.users_collection): c.objects.unlink(st)
    bpy.data.collections["Shrine"].objects.link(st)
    for dx in (-0.25, 0.25):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(STOOL.x + dx, STOOL.y + 0.2 - i * 0.2, 7.0 + h_ / 2)); lg = bpy.context.object; lg.name = "StoolLeg"; lg.scale = (0.04, 0.04, h_)
        lg.data.materials.append(bpy.data.materials["Wood"])
        for c in list(lg.users_collection): c.objects.unlink(lg)
        bpy.data.collections["Shrine"].objects.link(lg)
key_obj(cl_, 1100, loc=STOOL + Vector((0, 0.05, 0.6)), rot=(0, 0, R_(180 + 35)), interp='CONSTANT')   # the cleric on the step-stool
POPE_HO = Vector((1.3, 53.0, 7.0))
key_obj(pope, 1153, loc=POPE_HO, rot=(0, 0, R_(0)), interp='CONSTANT')      # v008: first he holds the bullet up to the camera
key_obj(pope, 1200, loc=POPE_HO, rot=(0, 0, R_(-105)), interp='CONSTANT')   # (cut at 1200) then turns to hand it up
ev(1200)
CROWN_W = Vector(crown.location) + Vector((0.0, -0.095, 0.035))
HP = Vector((1.06, 53.24, 8.74))          # handover point: both hands meet here at 1236
HO = 1236
for f in range(1100, 1621, 3):
    stand(CL, f, flex=4 + 10 * smooth((f - 1195) / 30) * (1 - smooth((f - 1240) / 25)), head=(-18 + 30 * smooth((f - 1195) / 30) * (1 - smooth((f - 1240) / 25)), 0))
    Mi = cl_.matrix_world.inverted()
    side_ = Vector((0.3, -0.12, 0.98)); hp_l = Mi @ HP; cr_l = Mi @ CROWN_W
    a_ = smooth((f - 1200) / 30); b_ = smooth((f - 1244) / 60); back = smooth((f - 1332) / 30)
    Wt = side_.lerp(hp_l + Vector((0, 0.02, 0.02)), a_).lerp(cr_l + Vector((0, 0.1, -0.04)), b_).lerp(side_, back)
    hand_at(CL, "R", f, tuple(Wt), d=(0, -0.6, 0.8 if b_ > 0.5 else -0.2), n=(-1, 0, 0), pole=(-0.6, 0.3, 1.1))
    hand_at(CL, "L", f, (0.36, -0.06, 0.97), d=(0, 0, -1), n=(1, 0, 0))
    face(cl_, f, brow=0.3, lids=0.2)
for f in range(1153, 1358, 3):
    up = smooth((f - 1196) / 34) * (1 - smooth((f - 1242) / 28)); pray = smooth((f - 1262) / 25)
    stand(P, f, flex=4 + 6 * pray, head=(-22 * up + 10 * pray, 0))
    Mi = pope.matrix_world.inverted()
    chest = Vector((-0.12, -0.3, 1.16))
    Wr = chest.lerp(Mi @ HP + Vector((0, 0.02, -0.03)), up).lerp(Vector((-0.06, -0.28, 1.27)), pray)
    if f < 1200: Wr = chest.lerp(Vector((-0.17, -0.38, 1.36)), smooth((f - 1155) / 12.0))  # held up beside his face (face stays clear)
    hand_at(P, "R", f, tuple(Wr), d=tuple(Vector((0, -0.4, 1)).lerp(Vector((0, -0.25, 1)), pray)), n=tuple(Vector((-1, 0, 0.3)).lerp(Vector((1, 0, 0)), pray)), pole=(-0.6, 0.3, 1.0))
    hand_at(P, "L", f, tuple(Vector((0.12, -0.3, 1.1)).lerp(Vector((0.06, -0.28, 1.27)), pray)), d=(0, -0.25, 1), n=(-1, 0, 0), pole=(0.5, 0.2, 0.9))
    face(pope, f, brow=0.35, lids=0.2 + 0.4 * pray, smile=0.2 * (1 - pray))
# the relic bullet: in the Pope's fingers, handed to the cleric at 1236, seated in the crown at 1320
rb = bul.copy(); rb.data = bul.data; rb.name = "RelicBullet"; bpy.data.collections["Shrine"].objects.link(rb); rb.animation_data_clear()
rb.scale = (4.5, 4.5, 4.5)
bm_ = bpy.data.materials.new("RelicLead"); bm_.use_nodes = True; bb_ = bm_.node_tree.nodes["Principled BSDF"]
bb_.inputs['Base Color'].default_value = (0.82, 0.82, 0.86, 1); bb_.inputs['Metallic'].default_value = 1.0; bb_.inputs['Roughness'].default_value = 0.12
rb.data = rb.data.copy(); rb.data.materials.clear(); rb.data.materials.append(bm_)
ev(HO); rb.location = pope.matrix_world @ pope.pose.bones["finger2-3.R"].tail   # at his fingertip (pinched)
c1 = rb.constraints.new('CHILD_OF'); c1.target = pope; c1.subtarget = "finger2-3.R"; c1.inverse_matrix = (pope.matrix_world @ pope.pose.bones["finger2-3.R"].matrix).inverted()
c2 = rb.constraints.new('CHILD_OF'); c2.target = cl_; c2.subtarget = "finger2-3.R"; c2.inverse_matrix = (cl_.matrix_world @ cl_.pose.bones["finger2-3.R"].matrix).inverted()
for f, v1, v2_ in ((1, 1.0, 0.0), (HO - 1, 1.0, 0.0), (HO, 0.0, 1.0), (1318, 0.0, 1.0), (1320, 0.0, 0.0)):
    c1.influence = v1; c1.keyframe_insert("influence", frame=f); c2.influence = v2_; c2.keyframe_insert("influence", frame=f)
for fc in fcurves(rb.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
rb.keyframe_insert("location", frame=1318)
rb.location = Vector(CROWN_W); rb.keyframe_insert("location", frame=1320)
for nm_, pos_, en_, fr_ in (("BulletGlint", Vector((1.05, 52.35, 8.75)), 12, ((1, False), (1153, True), (1200, False))),
                           ("CrownGlint", CROWN_W + Vector((-0.12, -0.28, 0.08)), 5, ((1, False), (1300, True)))):
    gl_ = bpy.data.objects.new(nm_, bpy.data.lights.new(nm_, 'POINT')); bpy.data.collections["Shrine"].objects.link(gl_)
    gl_.location = pos_; gl_.data.energy = en_; gl_.data.shadow_soft_size = 0.02; gl_.data.color = (1.0, 0.97, 0.92)
    key_vis(gl_, fr_)
set_interp(rb, 1320, 'CONSTANT')
key_vis(rb, ((1, False), (1153, True)))
# candles: flickering point lights over the racks + incense haze
for side in (-1, 1):
    for r in range(2):
        Lc = light("Candle%d%d" % (side, r), 'POINT', (side * 1.9, 52.2 - r * 0.7, 8.3 + r * 0.15), 18, (1.0, 0.55, 0.2), 0.6)
        for f in range(1, 1621, 5):
            Lc.data.energy = 14 + 6 * random.random(); Lc.data.keyframe_insert("energy", frame=f)
light("ShrineKey", 'SPOT', (1.6, 50.2, 11.5), 700, (1.0, 0.82, 0.6), 0.3, spot=45).rotation_euler = (Vector((0, 53.6, 9.2)) - Vector((1.6, 50.2, 11.5))).to_track_quat('-Z', 'Y').to_euler()
light("ShrineFill", 'AREA', (-2.5, 46, 13), 900, (1.0, 0.95, 0.88), 4.0)
light("ShrineFill2", 'AREA', (2.5, 49, 12.5), 600, (1.0, 0.93, 0.85), 4.0)
light("CellFill", 'AREA', (1.5, 41.5, 9.8), 250, (1.0, 0.95, 0.9), 1.5)
light("ShrineCrown", 'SPOT', (-0.6, 52.6, 10.8), 120, (1.0, 0.9, 0.75), 0.1, spot=20).rotation_euler = (Vector(crown.location) - Vector((-0.6, 52.6, 10.8))).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 49.6, 11.5)); vs_ = bpy.context.object; vs_.name = "ShrineHaze"; vs_.scale = (11.8, 12.4, 8.8)
vm2 = vm.copy(); vm2.node_tree.nodes["Principled Volume"].inputs['Density'].default_value = 0.004; vs_.data.materials.append(vm2)
for c in list(vs_.users_collection): c.objects.unlink(vs_)
bpy.data.collections["Shrine"].objects.link(vs_)

for hz in ("CellHaze", "ShrineHaze"):   # haze boxes off: the camera flies through them (QA INSIDE) and the look wants no haze
    O[hz].hide_render = True; O[hz].hide_viewport = True
print("STAGE sets done")

# ------------------------------------------------------------------ HANDS: finger curls for every grasp / gesture
def curl_keys(rig, s, keys):
    for f, a_, th in keys: curl(rig, s, f, a_, th)
curl_keys(pope, "R", [(1, 8, 5), (258, 8, 5), (272, 35, 25), (505, 35, 25), (520, 35, 25), (640, 20, 15), (763, 6, 4), (1015, 25, 20), (1153, 12, 10), (1240, 10, 8), (1262, 5, 5)])
curl_keys(pope, "L", [(1, 15, 10), (258, 15, 10), (268, 45, 30), (505, 40, 25), (520, 40, 25), (640, 20, 15), (763, 45, 30), (1015, 32, 20), (1153, 20, 12), (1262, 5, 5)])
for f in range(780, 1015, 30):          # blessing: two fingers up, ring + little curled
    for fi, a_ in ((4, 75), (5, 80), (1, 30), (2, 2), (3, 2)):
        for seg in (1, 2, 3):
            b = pope.pose.bones["finger%d-%d.R" % (fi, seg)]; b.rotation_quaternion = Quaternion((1, 0, 0), R_(CURL_SIGN * a_)); b.keyframe_insert("rotation_quaternion", frame=f)
for nm in ("AideA", "AideB"):
    for s_ in "LR": curl_keys(O[nm], s_, [(1, 20, 10), (512, 20, 10), (528, 60, 40), (700, 25, 15)])
curl_keys(O["AideB"], "R", [(1328, 10, 8)])
for rig_, f in ((pope, 1160), (pope, 1234), (O["AideB"], 1238), (O["AideB"], 1318)):      # pinch: index meets thumb
    for fi, a_ in ((1, 38), (2, 42), (3, 18), (4, 14), (5, 12)):
        for seg in (1, 2, 3):
            b = rig_.pose.bones["finger%d-%d.R" % (fi, seg)]; b.rotation_quaternion = Quaternion((1, 0, 0), R_(CURL_SIGN * a_ * (0.7 if seg == 1 else 1.0))); b.keyframe_insert("rotation_quaternion", frame=f)
curl_keys(shooter, "R", [(1, 75, 50)]); curl_keys(shooter, "L", [(1, 25, 15)])
for nm in ("SurgA", "SurgB", "SurgC", "Nurse"):
    for s_ in "LR": curl_keys(O[nm], s_, [(600, 25, 15), (680, 35, 25), (740, 22, 15)])
for s_ in "LR": curl_keys(pris, s_, [(1, 40, 30), (1100, 50, 35)])

# ------------------------------------------------------------------ HAND LIMITS (no backward bends) on every rigged character
def limit(pb, x, y, z):
    c = pb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'
    c.use_limit_x = c.use_limit_y = c.use_limit_z = True
    c.min_x, c.max_x = R_(x[0]), R_(x[1]); c.min_y, c.max_y = R_(y[0]), R_(y[1]); c.min_z, c.max_z = R_(z[0]), R_(z[1])
NL = 0
for r in [o for o in O if o.type == 'ARMATURE']:
    for pb in r.pose.bones:
        n_ = pb.name
        if n_.startswith("finger1-"): limit(pb, (-20, 70), (-30, 30), (-30, 30)); NL += 1
        elif n_.startswith("finger"): limit(pb, (0, 95), (-10, 10), (-10, 10)); NL += 1
        elif n_.startswith("wrist."): limit(pb, (-60, 60), (-30, 30), (-25, 25)); NL += 1
print("LIMITS", NL)
# pectoral cross on a chain (gold, plain, no text), riding on the chest bone
ev(1)
bvs = [c for c in mixed_coords(body_of(pope).data) if abs(c.x) < 0.03 and 1.30 < c.z < 1.36]
chest_y = min(v.y for v in bvs) if bvs else -0.12
CR0 = Vector((0, chest_y - 0.035, 1.33))
def gbox(nm, size, loc):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); b_ = bpy.context.object; b_.name = nm; b_.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    b_.data.materials.append(bpy.data.materials["Gold"]); b_.modifiers.new("b", 'BEVEL').width = 0.003
    for c in list(b_.users_collection): c.objects.unlink(b_)
    pope.users_collection[0].objects.link(b_); return b_
cv_ = gbox("PectoralCross", (0.012, 0.008, 0.075), CR0); ch_ = gbox("PectoralCrossBar", (0.05, 0.008, 0.012), CR0 + Vector((0, 0, 0.015)))
cu = bpy.data.curves.new("CrossChain", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0025
spn = cu.splines.new('NURBS'); pts = []
neck = pope.data.bones["neck01"].head_local
for i in range(9):
    t = math.pi * (0.1 + 0.8 * i / 8)
    pts.append(Vector((0.085 * math.cos(t), neck.y - 0.01 - (0.04 + chest_y - neck.y) * math.sin(t) ** 3 * 0.9, neck.z + 0.02 - (neck.z - CR0.z - 0.035) * math.sin(t) ** 2)))
spn.points.add(len(pts) - 1)
for pp, c in zip(spn.points, pts): pp.co = (c.x, c.y, c.z, 1)
spn.use_endpoint_u = True; cu.materials.append(bpy.data.materials["Gold"])
chn = bpy.data.objects.new("CrossChain", cu); pope.users_collection[0].objects.link(chn)
for o_ in (cv_, ch_, chn):
    attach_rest(o_, "spine01", Matrix.Translation(o_.location) if o_ != chn else Matrix.Identity(4))

# ------------------------------------------------------------------ ONE CAMERA
def popehead(f): return pope_root_obj(min(f, 505)) + Vector((0, 0, 1.62))
def popechest(f): return pope_root_obj(min(f, 505)) + Vector((0, 0, 1.25))
FD = Vector((math.sin(POPE_YAW) * -1, -math.cos(POPE_YAW), 0)) * -1   # his facing direction
FD = Matrix.Rotation(POPE_YAW, 3, 'Z') @ Vector((0, -1, 0))
PERP = Vector((-FD.y, FD.x, 0))
ev(340); XCW = XC.matrix_world.translation.copy(); ev(440); XHW = XH.matrix_world.translation.copy()
ev(1440); XCW8 = XC.matrix_world.translation.copy(); POPEHEAD8 = bone_w(pope, "head", "tail") + Vector((0, 0, -0.08))
ev(960); HANDW = bone_w(pope, "wrist.R")
ev(1130); SHW = bone_w(pris, "shoulder01.L")
SDIR = Vector((0.55, -0.83, 0)).normalized(); SRIGHT = Vector((SDIR.y, -SDIR.x, 0))
SHOT = Vector((SHOOTER.x, SHOOTER.y, 1.75)) - SDIR * 0.95 + SRIGHT * 0.38     # over his right shoulder, gun hand in frame
ev(60); SHEAD = bone_w(shooter, "head")
SPROF = SHEAD + SRIGHT * 1.25 + SDIR * 0.45 + Vector((0, 0, -0.05))       # the shooter's face in profile, gun arm toward frame right
# v007 (director): clean cuts between shots; each shot is its own smooth spline. (start, end, [(frame, pos, target, lens)])
SHOTS = [
 (1, 74,    [(1, SPROF + Vector((0, 0, -0.12)), SHEAD + SDIR * 0.15 + Vector((0, 0, -0.3)), 28),
             (74, SPROF + SRIGHT * 0.1, SHEAD + SDIR * 0.22 + Vector((0, 0, -0.02)), 30)]),                     # A: he raises the gun
 (75, 237,  [(75, popehead(75) + FD * 2.8 + PERP * 0.7 + Vector((0, 0, 0.1)), popehead(75) + Vector((0, 0, -0.25)), 30),
             (115, popehead(115) + FD * 1.9 + Vector((0, 0, 0.2)), popehead(115) + Vector((0, 0, -0.1)), 35),
             (165, popechest(165) + PERP * 2.4 + FD * 0.8 + Vector((0, 0, 0.9)), popechest(165), 24),
             (237, popechest(237) + FD * 2.6 + PERP * 1.0 + Vector((0, 0, 0.5)), popechest(237), 28)]),        # B: the Pope waves from the jeep
 (238, 261, [(238, SPROF + SRIGHT * 0.45 + Vector((0, 0, 0.02)), SHEAD + SDIR * 0.3, 30),
             (261, SPROF + SRIGHT * 0.35 + Vector((0, 0, 0.02)), SHEAD + SDIR * 0.3, 32)]),                   # C: he fires (flash at 255)
 (262, 467, [(262, popechest(262) + FD * 1.9 + PERP * 1.1 + Vector((0, 0, 0.35)), popechest(262) + Vector((0, 0, 0.22)), 32),
             (360, popechest(360) + FD * 1.8 + PERP * 1.05 + Vector((0, 0, 0.32)), popechest(360) + Vector((0, 0, 0.2)), 33),
             (467, popechest(467) + FD * 1.75 + PERP * 1.0 + Vector((0, 0, 0.3)), popechest(467) + Vector((0, 0, 0.15)), 34)]),   # 3/4 front on his face  # D: hit, clutch
 (468, 630, [(468, popechest(505) + FD * 3.4 + PERP * 1.0 + Vector((0, 0, 1.4)), popechest(505) + Vector((0, 0, -0.4)), 30),
             (630, popechest(505) + FD * 3.1 + PERP * 0.9 + Vector((0, 0, 1.3)), popechest(505) + Vector((0, 0, -0.5)), 30)]),   # E: caught, lowered
 (631, 762, [(631, Vector((-9.05, 41.3, 8.8)), Vector((-8.0, 40.95, 8.2)), 28),
             (762, Vector((-8.95, 41.2, 8.7)), Vector((-8.0, 40.95, 8.18)), 30)]),                            # F: surgery from the foot end
 (763, 1014, [(763, Vector((-7.4, 33.9, 9.75)), Vector((-3.0, 22.0, 3.0)), 24),
             (805, Vector((-7.0, 32.5, 10.2)), Vector((-1.0, 22.0, 3.0)), 22),
             (845, Vector((-3.6, 23.5, 11.2)), Vector((0.0, 34.0, 8.2)), 24),
             (900, Vector((-1.4, 30.2, 8.7)), Vector((0.0, 33.9, 8.5)), 32),
             (950, Vector((-0.9, 31.3, 8.75)), Vector((0.0, 33.95, 8.6)), 34),
             (1014, Vector((-0.6, 31.7, 8.7)), Vector((0.0, 33.95, 8.55)), 36)]),                               # G: balcony (held front view)
 (1015, 1152, [(1015, Vector((0.0, 42.25, 9.05)), Vector((0.0, 40.62, 8.35)), 28),
              (1152, Vector((0.0, 42.1, 9.0)), Vector((0.0, 40.62, 8.38)), 30)]),                         # H: side two-shot in the cell
 (1153, 1199, [(1153, Vector((1.15, 51.95, 8.62)), Vector((1.27, 52.7, 8.5)), 40),
              (1199, Vector((1.17, 52.02, 8.6)), Vector((1.27, 52.7, 8.52)), 44)]),                            # I1: the bullet held up to us
 (1200, 1321, [(1200, Vector((0.35, 52.3, 9.0)), HP + Vector((0, 0, -0.1)), 26),
              (1321, Vector((0.3, 52.25, 9.1)), HP + Vector((-0.1, 0.1, 0.05)), 26)]),                       # I2: handed up to the cleric                          # I: he hands the bullet up to the cleric
 (1322, 1360, [(1322, CROWN_W + Vector((-0.18, -0.52, 0.03)), CROWN_W, 40),
              (1360, CROWN_W + Vector((-0.15, -0.48, 0.03)), CROWN_W, 42)]),                                  # J: crown close-up, bullet set
 (1361, 1545, [(1361, POPEHEAD8 + Vector((-0.75, 0.62, 0.0)), POPEHEAD8 + Vector((0, 0, -0.08)), 38),
              (1545, POPEHEAD8 + Vector((-0.6, 0.55, 0.02)), POPEHEAD8 + Vector((0, 0, -0.06)), 42)]),         # K: 3/4 front, praying
 (1546, 1620, [(1546, POPEHEAD8 + Vector((-0.9, -1.6, 0.45)), CROWN_W + Vector((0, 0, -0.3)), 30),
              (1585, POPEHEAD8 + Vector((-0.45, -0.55, 0.3)), CROWN_W + Vector((0, 0, -0.1)), 34),
              (1604, CROWN_W + Vector((-0.3, -0.9, 0.0)), CROWN_W, 40),
              (1620, CROWN_W + Vector((-0.1, -0.42, 0.01)), CROWN_W, 50)]),                                    # ends on the bullet          # L: push-in to the crown
]
cam = bpy.data.objects.new("CAM", bpy.data.cameras.new("CAM")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.sensor_width = 36; cam.data.clip_start = 0.01; cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 8.0
foc = bpy.data.objects.new("CamFocus", None); sc.collection.objects.link(foc); cam.data.dof.focus_object = foc
def ang(a_, b_): return math.degrees(2 * math.acos(min(1.0, abs(a_.dot(b_)))))
CPOS, CTGT, CLEN, QS = {}, {}, {}, {}
CUTF = [s0 for s0, _, _ in SHOTS[1:]]
for s0, s1, ks in SHOTS:
    cp_ = catmull([(k[0], k[1]) for k in ks]); ct_ = catmull([(k[0], k[2]) for k in ks]); cl_ = pchip([(k[0], float(k[3])) for k in ks])
    for f in range(s0, s1 + 1):
        CPOS[f], CTGT[f], CLEN[f] = cp_(f), ct_(f), cl_(f)
        QS[f] = (CTGT[f] - CPOS[f]).to_track_quat('-Z', 'Y')
        if f > s0 and QS[f].dot(QS[f - 1]) < 0: QS[f] = -QS[f]
    for it in range(40):                      # ease any snap inside the shot
        jumps = [f for f in range(s0 + 1, s1 + 1) if ang(QS[f - 1], QS[f]) > 18.0]
        if not jumps: break
        for j in jumps:
            tot = ang(QS[j - 1], QS[j]); half = max(4, int(math.ceil(tot / 16.0)) + 2)
            a0, b0 = max(s0, j - half), min(s1, j + half)
            qa, qb = QS[a0].copy(), QS[b0].copy()
            for f in range(a0 + 1, b0):
                QS[f] = qa.slerp(qb, smooth((f - a0) / (b0 - a0)))
print("CAMJUMP max deg/frame (cuts excluded)", round(max(ang(QS[f - 1], QS[f]) for f in range(2, 1621) if f not in CUTF), 1))
print("CUTS at", CUTF)
def src(f): return f
prev = None
for f in range(1, 1621):
    q = QS[f]; e = q.to_euler('XYZ', prev) if prev else q.to_euler('XYZ'); prev = e
    cam.location = CPOS[f]; cam.rotation_euler = e; cam.data.lens = CLEN[f]
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f); cam.data.keyframe_insert("lens", frame=f)
    foc.location = CTGT[f]; foc.keyframe_insert("location", frame=f)
for fc in fcurves(cam.animation_data.action) + fcurves(foc.animation_data.action) + fcurves(cam.data.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'    # baked per frame: no blending across cuts
for f_, n_ in ((1, 8.0), (1153, 11.0), (1200, 8.0), (1322, 11.0), (1361, 8.0), (1600, 11.0), (1612, 16.0)):      # crown close-ups: f/11 so the whole crown and the bullet are sharp
    cam.data.dof.aperture_fstop = n_; cam.data.dof.keyframe_insert("aperture_fstop", frame=f_)
cpos = lambda f: CPOS[int(round(f))]; ctgt = lambda f: CTGT[int(round(f))]; clen = lambda f: CLEN[int(round(f))]
# ------------------------------------------------------------------ INSET DIAGRAM (replaces the x-ray; director v005 review)
# The robe stays solid. A small round side-view cut-away sits in the upper-right corner: torso outline, spine, aorta, stomach,
# intestines, and the bullet path drawing itself between them (missing the aorta and spine). Camera-only, no text.
XRAY_OFF = [o_ for o_ in bpy.data.collections["XRay"].all_objects] + [skel, aorta, guts, hand]
for o_ in XRAY_OFF:
    if o_.animation_data: o_.animation_data_clear()
    o_.hide_render = True; o_.hide_viewport = True
for m_ in bpy.data.materials:                       # robe masks: x-ray porthole values to 0 (solid robe everywhere)
    if m_.node_tree:
        for nd in m_.node_tree.nodes:
            if nd.type == 'VALUE' and nd.name in ("XRT", "XRH"):
                if m_.node_tree.animation_data: m_.node_tree.animation_data_clear()
                nd.outputs[0].default_value = 0.0
def flat(name, col, strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; n = nt.nodes
    for x in list(n): n.remove(x)
    em = n.new('ShaderNodeEmission'); em.inputs['Color'].default_value = tuple(col) + (1,); em.inputs['Strength'].default_value = strength
    out = n.new('ShaderNodeOutputMaterial'); nt.links.new(em.outputs[0], out.inputs[0]); return m
INSET = bpy.data.objects.new("Inset", None); sc.collection.objects.link(INSET); INSET.parent = cam
INS_PARTS = []
def ell(name, cx, cy, rx, ry, z, mat, segs=64, rot=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [bm.verts.new((cx + rx * math.cos(2 * math.pi * i / segs) * math.cos(rot) - ry * math.sin(2 * math.pi * i / segs) * math.sin(rot),
                        cy + rx * math.cos(2 * math.pi * i / segs) * math.sin(rot) + ry * math.sin(2 * math.pi * i / segs) * math.cos(rot), z)) for i in range(segs)]
    bm.faces.new(vs); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.parent = INSET; INS_PARTS.append(o); return o
ell("InsetRing", 0, 0, 1.12, 1.12, -0.004, flat("InsetNavy", (0.95, 0.95, 0.95), 1.6))   # thick white border
ell("InsetDisc", 0, 0, 1.0, 1.0, 0.0, flat("InsetPaper", (0.03, 0.06, 0.12), 1.0))   # plain dark disc
TS, TX, TY = 0.74, 0.2, 0.08                     # torso group: right part of the circle
def ellT(name, cx, cy, rx, ry, z, mat, segs=64, rot=0.0): return ell(name, TX + TS * cx, TY + TS * cy, TS * rx, TS * ry, z, mat, segs, rot)
ellT("InsetTorso", 0.0, 0.0, 0.44, 0.8, 0.004, flat("InsetBody", (0.55, 0.74, 0.9), 0.9))
ellT("InsetGut", -0.06, -0.33, 0.27, 0.2, 0.008, flat("InsetGutM", (0.92, 0.66, 0.58), 1.0), rot=0.2)
ellT("InsetStomach", -0.12, 0.2, 0.2, 0.14, 0.009, flat("InsetStomachM", (0.93, 0.4, 0.48), 1.1), rot=-0.35)
ellT("InsetAorta", 0.14, 0.0, 0.035, 0.62, 0.01, flat("InsetAortaM", (0.82, 0.07, 0.08), 1.0), segs=24)
spm = flat("InsetSpineM", (0.98, 0.95, 0.86), 1.1)
for i in range(9):
    ellT("InsetVert%d" % i, 0.28, -0.64 + i * 0.16, 0.06, 0.06, 0.01, spm, segs=6)
# the wounded hand (left index finger), lower left of the circle
skin = flat("InsetSkin", (0.95, 0.76, 0.62), 1.0); HX, HY = -0.55, -0.32
ell("InsetPalm", HX, HY, 0.13, 0.15, 0.006, skin)
for k_, dx_ in enumerate((-0.09, -0.03, 0.03, 0.09)):
    ell("InsetFinger%d" % k_, HX + dx_, HY + 0.22 - 0.02 * abs(k_ - 1.5), 0.03, 0.1, 0.006, skin, segs=24)
ell("InsetThumb", HX - 0.16, HY + 0.02, 0.03, 0.09, 0.006, skin, segs=24, rot=0.7)
ell("InsetWound", HX - 0.09, HY + 0.24, 0.07, 0.018, 0.012, flat("InsetWoundM", (1.0, 0.5, 0.08), 3.0), segs=24, rot=0.35)
cu = bpy.data.curves.new("InsetPath", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.022; cu.bevel_resolution = 2
sp_ = cu.splines.new('NURBS'); PTS = tuple((TX + TS * x_, TY + TS * y_) for x_, y_ in ((-0.7, 0.03), (-0.3, 0.0), (0.0, -0.03), (0.2, -0.09), (0.45, -0.14), (0.72, -0.18)))
sp_.points.add(len(PTS) - 1)
for pt, (x_, y_) in zip(sp_.points, PTS): pt.co = (x_, y_, 0.014, 1)
sp_.use_endpoint_u = True; sp_.order_u = 3; cu.materials.append(flat("InsetPathM", (1.0, 0.5, 0.08), 3.0))
pth = bpy.data.objects.new("InsetPath", cu); sc.collection.objects.link(pth); pth.parent = INSET; INS_PARTS.append(pth)
for o_ in INS_PARTS:
    for k_ in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter"): setattr(o_, k_, False)
INSET_W = ((300, 392),)
cu.bevel_factor_end = 0.0; cu.keyframe_insert("bevel_factor_end", frame=1)
for a_, b_ in INSET_W:
    for f_, v_ in ((a_ + 6, 0.0), (a_ + 36, 1.0), (b_, 1.0), (b_ + 1, 0.0)):
        cu.bevel_factor_end = v_; cu.keyframe_insert("bevel_factor_end", frame=f_)
for f in range(1, 1621):
    w_ = [(a_, b_) for a_, b_ in INSET_W if a_ - 1 <= f <= b_ + 1]
    if not w_ and f not in (1,): continue
    if w_:
        a_, b_ = w_[0]; g_ = smooth((f - a_) / 8.0) * (1 - smooth((f - (b_ - 8)) / 8.0))
    else:
        g_ = 0.0
    D = max(0.4, (ctgt(src(f)) - cpos(src(f))).length * 0.7)      # in front of the subject, near the focus plane (sharp at f/8)
    hh = D * 18.0 / clen(src(f)); hw = hh * 1080 / 1920
    r_ = 0.6 * hw
    INSET.location = (-hw * 0.95 + r_ * 1.12, -hh * 0.9 + r_ * 1.12, -D); INSET.scale = (r_ * max(g_, 0.001),) * 3
    INSET.keyframe_insert("location", frame=f); INSET.keyframe_insert("scale", frame=f)
for o_ in INS_PARTS:
    key_vis(o_, ((1, False), (INSET_W[0][0], True), (INSET_W[0][1] + 1, False)))
# ------------------------------------------------------------------ v007: oxygen mask on the patient (surgery 631..762)
ev(700)
hh_ = bone_w(pope, "head"); ht_ = bone_w(pope, "head", "tail"); ax_ = (ht_ - hh_).normalized()
MOUTH = hh_ + ax_ * 0.05 + Vector((0, 0, 0.1))
mm = bpy.data.materials.new("OxyMask"); mm.use_nodes = True; bsm = mm.node_tree.nodes["Principled BSDF"]
bsm.inputs['Base Color'].default_value = (0.75, 0.92, 0.85, 1); bsm.inputs['Roughness'].default_value = 0.25
bsm.inputs['Transmission Weight'].default_value = 0.55; bsm.inputs['Alpha'].default_value = 0.9
bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0, location=MOUTH); om = bpy.context.object; om.name = "OxygenMask"
om.scale = (0.045, 0.055, 0.03); om.data.materials.append(mm)
for p_ in om.data.polygons: p_.use_smooth = True
tc_ = bpy.data.curves.new("OxyTube", 'CURVE'); tc_.dimensions = '3D'; tc_.bevel_depth = 0.008; tc_.bevel_resolution = 2
spt = tc_.splines.new('NURBS'); TP = (MOUTH + Vector((0, 0, 0.02)), MOUTH + Vector((0.12, 0.04, 0.05)), MOUTH + Vector((0.3, 0.08, -0.02)), MOUTH + Vector((0.42, 0.1, -0.3)))
spt.points.add(len(TP) - 1)
for pt, c_ in zip(spt.points, TP): pt.co = (c_.x, c_.y, c_.z, 1)
spt.use_endpoint_u = True; spt.order_u = 3
tm = bpy.data.materials.new("OxyTubeM"); tm.use_nodes = True; tm.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.7, 0.85, 0.9, 1)
tc_.materials.append(tm); otb = bpy.data.objects.new("OxyTube", tc_); sc.collection.objects.link(otb)
for o_ in (om, otb):
    key_vis(o_, ((1, False), (631, True), (763, False)))
# ------------------------------------------------------------------ v007: cloth shader on the robe, paint shader on the jeep (no flat clay white)
def cloth(mname, tint):
    m = bpy.data.materials.get(mname)
    if not m or not m.node_tree: return
    nt = m.node_tree; n, l = nt.nodes, nt.links
    bs = next((x for x in n if x.type == 'BSDF_PRINCIPLED'), None)
    if not bs: return
    if bs.inputs['Base Color'].links:
        src_ = bs.inputs['Base Color'].links[0].from_socket
        mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        mx.inputs[7].default_value = tint + (1,); l.new(src_, mx.inputs[6]); l.new(mx.outputs[2], bs.inputs['Base Color'])
    else:
        bs.inputs['Base Color'].default_value = tint + (1,)
    wv = n.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 420; wv.inputs['Distortion'].default_value = 1.5
    nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 60
    mxh = n.new('ShaderNodeMath'); mxh.operation = 'ADD'; l.new(wv.outputs['Fac'], mxh.inputs[0]); l.new(nz.outputs['Fac'], mxh.inputs[1])
    bp = n.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.12; l.new(mxh.outputs[0], bp.inputs['Height'])
    if bs.inputs['Normal'].links: l.new(bs.inputs['Normal'].links[0].from_socket, bp.inputs['Normal'])
    l.new(bp.outputs['Normal'], bs.inputs['Normal'])
    bs.inputs['Roughness'].default_value = 0.78
    bs.inputs['Sheen Weight'].default_value = 0.5; bs.inputs['Sheen Roughness'].default_value = 0.4
for mn_ in ("CassockWhite", "Pope_male_elegantsuit01", "PopeWool"):
    cloth(mn_, (0.93, 0.9, 0.84))
jm = bpy.data.materials.get("jeep.001")
if jm and jm.node_tree:
    bs = next((x for x in jm.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'), None)
    if bs:
        if not bs.inputs['Base Color'].links: bs.inputs['Base Color'].default_value = (0.8, 0.82, 0.84, 1)
        bs.inputs['Roughness'].default_value = 0.35; bs.inputs['Metallic'].default_value = 0.15
        bs.inputs['Coat Weight'].default_value = 0.9; bs.inputs['Coat Roughness'].default_value = 0.04
print("V007 shaders + mask done")
sc.frame_set(1)
import json
beats = [(1, "He fired straight at the Pope"), (265, "Two bullets tore through"), (505, "He collapsed, badly wounded"), (631, "but survived after emergency surgery"),
         (763, "And years later, the Pope publicly forgave"), (1015, "and even met him face to face"), (1153, "He later had one of the bullets placed"), (1375, "believing that God had guided it")]
json.dump([{"beat": i + 1, "frame": f, "first_words": w} for i, (f, w) in enumerate(beats)], open(os.path.join(os.path.dirname(OUT), "beats.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
