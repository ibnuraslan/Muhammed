"""Automatic quadruped rig for a standing, unrigged animal mesh (GLB).

blender -b --factory-startup --python rig_quadruped.py -- <in.glb> <name> <height_m> <out.blend>

Result: one mesh '<name>_body' parented to armature '<name>_rig' facing -Y, hooves on z=0.
Bones: root, torso (centre of mass), hips, spine1, spine2, chest, neck1, neck2, head, tail1, tail2,
legs <FL|FR|HL|HR>: upper, lower, cannon, hoof; IK controls IK_hoof.<leg> with poles.
"""
import sys, math
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, NAME, HEIGHT, OUT = argv[0], argv[1], float(argv[2]), argv[3]

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.import_scene.gltf(filepath=SRC)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in bpy.data.objects:
    o.select_set(False)
# bake world transforms into the meshes and join
for o in meshes:
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw
for o in [o for o in bpy.data.objects if o.type != 'MESH']:
    bpy.data.objects.remove(o, do_unlink=True)
bpy.context.view_layer.objects.active = meshes[0]
for o in meshes:
    o.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
if len(meshes) > 1:
    bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = NAME + "_body"
me = body.data
# weld split seams so extreme bends don't open cracks (UVs/normals live on loops, unaffected)
bm = bmesh.new(); bm.from_mesh(me)
nv = len(bm.verts)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5 * max(body.dimensions))
print("RIG welded", nv - len(bm.verts), "duplicate vertices")
bm.to_mesh(me); bm.free()

def verts():
    return [v.co.copy() for v in me.vertices]

# ---------------------------------------------------------------- normalise: long axis -> Y, scale, ground
V = verts()
ext = [max(p[i] for p in V) - min(p[i] for p in V) for i in range(3)]
if ext[0] > ext[1]:                      # long axis is X -> rotate to Y
    me.transform(Matrix.Rotation(math.radians(90), 4, 'Z'))
V = verts()
zmin = min(p.z for p in V); zmax = max(p.z for p in V)
s = HEIGHT / (zmax - zmin)
me.transform(Matrix.Scale(s, 4))
V = verts()
cx = (max(p.x for p in V) + min(p.x for p in V)) / 2
cy = (max(p.y for p in V) + min(p.y for p in V)) / 2
me.transform(Matrix.Translation((-cx, -cy, -min(p.z for p in V))))
V = verts()
H = max(p.z for p in V)
# head end: the end of the long axis whose top is highest (neck rises to the head)
yA, yB = min(p.y for p in V), max(p.y for p in V)
L = yB - yA
topA = max((p.z for p in V if p.y < yA + 0.25 * L), default=0)
topB = max((p.z for p in V if p.y > yB - 0.25 * L), default=0)
if topB > topA:                           # head at +Y -> turn to face -Y
    me.transform(Matrix.Rotation(math.radians(180), 4, 'Z'))
V = verts()
yF, yR = min(p.y for p in V), max(p.y for p in V)       # front (head) and rear
L = yR - yF
me.update()

# ---------------------------------------------------------------- legs: cluster low vertices
low = [p for p in V if p.z < 0.12 * H]
ymid = sum(p.y for p in low) / len(low)
legs = {}
for key, sx, front in (("FL", 1, True), ("FR", -1, True), ("HL", 1, False), ("HR", -1, False)):
    pts = [p for p in low if (p.x * sx > 0) and ((p.y < ymid) == front)]
    legs[key] = Vector((sum(p.x for p in pts) / len(pts), sum(p.y for p in pts) / len(pts)))

def column_centroid(xy, z, r):
    pts = [p for p in V if abs(p.z - z) < 0.025 * H and (Vector((p.x, p.y)) - xy).length < r]
    if len(pts) < 3:
        return None
    return Vector((sum(p.x for p in pts) / len(pts), sum(p.y for p in pts) / len(pts), z))

# belly height: lowest body vertex between the front and hind legs on the midline
ys = (legs["FL"].y + legs["FR"].y) / 2, (legs["HL"].y + legs["HR"].y) / 2
mid = [p for p in V if ys[0] + 0.25 * (ys[1] - ys[0]) < p.y < ys[1] - 0.25 * (ys[1] - ys[0]) and abs(p.x) < 0.1 * H]
# belly line: min z per y-slice across the middle of the trunk; udder/genitals pull a few slices
# down, so take the 75th percentile of the slice minima
y0, y1 = ys[0] + 0.25 * (ys[1] - ys[0]), ys[1] - 0.25 * (ys[1] - ys[0])
mins = []
for k in range(12):
    a0 = y0 + (y1 - y0) * k / 12; a1 = a0 + (y1 - y0) / 12
    sl = [p.z for p in mid if a0 <= p.y < a1]
    if sl:
        mins.append(min(sl))
mins.sort()
belly = mins[int(0.75 * (len(mins) - 1))]
back = max(p.z for p in mid)
print("RIG belly %.3f back %.3f H %.3f L %.3f" % (belly, back, H, L))

joints = {}
leg_r = 0.07 * H
for key, xy in legs.items():
    front = key.startswith("F")
    fr = [0.015, 0.10, 0.30 if front else 0.33, 0.52 * belly / 0.55 if belly < 0.6 * H else 0.5 * H]
    pts, cur = [], xy
    for zf in (0.03, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60):
        z = zf * H
        if z > belly * 0.95:
            break
        c = column_centroid(cur, z, leg_r)
        if c:
            pts.append(c)
            cur = Vector((c.x, c.y))
    def at(z):
        best = min(pts, key=lambda c: abs(c.z - z))
        return Vector((best.x, best.y, z))
    hoof = at(0.03 * H)
    fetlock = at(0.10 * H)
    knee = at((0.28 if front else 0.31) * H)
    elbow = at(min(0.95 * belly, (0.47 if front else 0.50) * H))
    top_z = belly + 0.55 * (back - belly)
    sx = 1 if key.endswith("L") else -1
    top = Vector((elbow.x * 0.75, elbow.y + (0.05 if front else -0.06) * H, top_z))
    # hind stifle sits forward of the hock line, front elbow behind the knee
    if not front:
        elbow.y -= 0.04 * H
        knee.y += 0.035 * H
    else:
        elbow.y += 0.02 * H
        knee.y -= 0.01 * H
    toe = hoof + Vector((0, -0.06 * H, -hoof.z + 0.005))
    joints[key] = [top, elbow, knee, fetlock, toe]

# spine / neck / head
hipC = (joints["HL"][0] + joints["HR"][0]) / 2
shC = (joints["FL"][0] + joints["FR"][0]) / 2
hipC.x = shC.x = 0
spine_z = belly + 0.6 * (back - belly)
hip = Vector((0, hipC.y + 0.02 * H, spine_z))
withers = Vector((0, shC.y - 0.01 * H, spine_z + 0.03 * H))
front_pts = [p for p in V if p.y < shC.y - 0.05 * L]
snout = min(front_pts, key=lambda p: p.y)
snout = Vector((0, snout.y, snout.z))
head_pts = [p for p in V if p.y < snout.y + 0.13 * L]
headC = Vector((0, sum(p.y for p in head_pts) / len(head_pts), sum(p.z for p in head_pts) / len(head_pts)))
# head bone: from the poll (top-back of skull) to the snout
poll = Vector((0, headC.y + 0.06 * L, headC.z + 0.03 * H))
neck_mid = withers.lerp(poll, 0.5) + Vector((0, 0, 0.04 * H))
rear_pts = [p for p in V if p.y > yR - 0.04 * L]
tail_root = Vector((0, yR - 0.03 * L, max(p.z for p in rear_pts) - 0.03 * H))
tail_tip = Vector((0, yR + 0.01 * L, tail_root.z - 0.18 * H))

# ---------------------------------------------------------------- armature
arm_d = bpy.data.armatures.new(NAME + "_rig")
arm = bpy.data.objects.new(NAME + "_rig", arm_d)
bpy.context.scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects:
    o.select_set(False)
arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_d.edit_bones

def bone(name, h, t, parent=None, deform=True, connect=False):
    b = eb.new(name)
    b.head, b.tail = h, t
    if (b.tail - b.head).length < 1e-4:
        b.tail = b.head + Vector((0, 0, 0.02))
    b.parent = eb[parent] if parent else None
    b.use_connect = connect and parent is not None
    b.use_deform = deform
    b.roll = 0
    return b

ctr = (hip + withers) / 2
bone("root", Vector((0, ctr.y, 0)), Vector((0, ctr.y - 0.2 * H, 0)), deform=False)
bone("torso", ctr, ctr + Vector((0, 0, 0.15 * H)), "root", deform=False)
sp = [hip.lerp(withers, t) for t in (0.0, 0.33, 0.66, 1.0)]
bone("hips", sp[1], sp[0], "torso")
bone("spine1", sp[1], sp[2], "torso")
bone("spine2", sp[2], sp[3] + Vector((0, 0.03 * H, 0)), "spine1", connect=True)
bone("chest", eb["spine2"].tail, withers, "spine2", connect=True)
bone("neck1", withers, neck_mid, "chest", connect=True)
bone("neck2", neck_mid, poll, "neck1", connect=True)
bone("head", poll, snout + Vector((0, 0.02 * L, 0)), "neck2", connect=True)
bone("tail1", tail_root, tail_root.lerp(tail_tip, 0.5), "hips")
bone("tail2", tail_root.lerp(tail_tip, 0.5), tail_tip, "tail1", connect=True)
for key, (top, elbow, knee, fetlock, toe) in joints.items():
    par = "chest" if key.startswith("F") else "hips"
    bone("upper." + key, top, elbow, par)
    bone("lower." + key, elbow, knee, "upper." + key, connect=True)
    bone("cannon." + key, knee, fetlock, "lower." + key, connect=True)
    bone("hoof." + key, fetlock, toe, "cannon." + key, connect=True)
    c = bone("IK_hoof." + key, fetlock, toe, "root", deform=False)
    pole_dir = -1 if key.startswith("F") else 1          # front knees point forward? no: elbows back, hind stifle forward
    pz = knee.z
    bone("pole." + key, Vector((knee.x, knee.y + (0.8 if key.startswith("F") else -0.8) * H, pz)),
         Vector((knee.x, knee.y + (0.8 if key.startswith("F") else -0.8) * H, pz + 0.05)), "root", deform=False)
bpy.ops.object.mode_set(mode='POSE')
for pb in arm.pose.bones:
    pb.rotation_mode = 'QUATERNION'
for key in joints:
    c = arm.pose.bones["cannon." + key].constraints.new('IK')
    c.target, c.subtarget = arm, "IK_hoof." + key
    c.pole_target, c.pole_subtarget = arm, "pole." + key
    c.chain_count = 3
    cr = arm.pose.bones["hoof." + key].constraints.new('COPY_ROTATION')
    cr.target, cr.subtarget = arm, "IK_hoof." + key
bpy.ops.object.mode_set(mode='OBJECT')

# pole angles: reproduce rest pose
def calib(key):
    c = arm.pose.bones["cannon." + key].constraints["IK"]
    ref = arm_d.bones["lower." + key].tail_local.copy()
    best = (0, 9)
    for d in range(-180, 180, 3):
        c.pole_angle = math.radians(d)
        bpy.context.view_layer.update()
        e = (arm.pose.bones["lower." + key].tail - ref).length
        if e < best[1]:
            best = (d, e)
    for d10 in range((best[0] - 3) * 10, (best[0] + 3) * 10):
        c.pole_angle = math.radians(d10 / 10)
        bpy.context.view_layer.update()
        e = (arm.pose.bones["lower." + key].tail - ref).length
        if e < best[1]:
            best = (d10 / 10, e)
    c.pole_angle = math.radians(best[0])
    print("RIG pole", key, best)
for key in joints:
    calib(key)

# ---------------------------------------------------------------- weights (distance to bone segments, region-gated)
def seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
    return (p - (a + ab * t)).length, t

deform = [b for b in arm_d.bones if b.use_deform]
groups = {b.name: body.vertex_groups.new(name=b.name) for b in deform}
for v in me.vertices:
    p = v.co
    cands = []
    for b in deform:
        n = b.name
        if "." in n:                     # leg bone: same side, same end, below the back line
            key = n.split(".")[1]
            sx = 1 if key.endswith("L") else -1
            if p.x * sx < -0.01 * H:
                continue
            front = key.startswith("F")
            yl = joints[key][0].y
            if abs(p.y - yl) > 0.22 * L:
                continue
            if n.startswith("upper") and p.z > joints[key][0].z + 0.05 * H:
                continue
        if n.startswith("tail") and p.y < tail_root.y - 0.04 * L:
            continue
        if n in ("head", "neck2") and p.y > withers.y + 0.02 * L:
            continue
        d, t = seg_dist(p, b.head_local, b.tail_local)
        cands.append((d, n))
    cands.sort()
    top = cands[:3]
    ws = [1.0 / max(d, 0.004 * H) ** 4 for d, n in top]
    tot = sum(ws)
    for (d, n), w in zip(top, ws):
        if w / tot > 0.02:
            groups[n].add([v.index], w / tot, 'REPLACE')
# smooth the weights a little
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects:
    o.select_set(False)
body.select_set(True)
bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
bpy.ops.object.vertex_group_smooth(group_select_mode='ALL', factor=0.5, repeat=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
bpy.ops.object.mode_set(mode='OBJECT')
body.parent = arm
mod = body.modifiers.new("Armature", 'ARMATURE')
mod.object = arm
arm.data.display_type = 'STICK'
print("RIG bones", len(arm_d.bones), "joints", {k: [tuple(round(c, 3) for c in j) for j in v] for k, v in joints.items()})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("RIG_OK", OUT)
