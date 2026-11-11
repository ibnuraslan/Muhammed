"""Cars (CC-BY touring car, roof removed and a folded roof added, no badges), and props: plumed helmet, wide hat, parasol,
pistol silhouette, plain dark ball (no construction detail), chauffeur/officer caps.
blender -b set.blend --python 03_props.py -- <out.blend>"""
import sys, os
import bpy, bmesh
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "00_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
CC = coll("Cars"); CP = coll("Props")
S_CAR = 0.0042; Z_CAR = 198.0

def build_car(name, paint, trim_mul=1.0):
    c = coll(name, CC)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, "car_touring.glb"))
    new = [o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    groups = {}
    for o in new:
        if o.type != 'MESH': continue
        if o.name.startswith("roof"):
            continue
        me = o.data.copy(); me.transform(o.matrix_world)
        me.transform(Matrix.Translation(V(0, 0, Z_CAR * S_CAR)) @ Matrix.Scale(S_CAR, 4))
        key = "Body"
        for w in ("wheel front.001", "wheel front", "wheel back.001", "wheel back"):
            if o.name.startswith(w + "_"): key = w; break
        groups.setdefault(key, []).append(me)
    for o in new: bpy.data.objects.remove(o)
    root = bpy.data.objects.new(name, None); c.objects.link(root)
    sway = bpy.data.objects.new(name + "_Sway", None); c.objects.link(sway); sway.parent = root
    parts = {}
    for key, mes in groups.items():
        bm = bmesh.new()
        mats = []
        for me in mes:
            off = len(mats)
            for m in me.materials: mats.append(m)
            tmp = bmesh.new(); tmp.from_mesh(me)
            for f in tmp.faces: f.material_index += off
            tm = bpy.data.meshes.new("tmp"); tmp.to_mesh(tm); tmp.free(); bm.from_mesh(tm); bpy.data.meshes.remove(tm)
        nm = name + "_" + key.replace(" ", "_").replace(".001", "R").replace("front", "F").replace("back", "B")
        o = mesh_obj(nm, bm, mats, c)
        if key != "Body":
            cen = sum((v.co for v in o.data.vertices), V(0, 0, 0)) / len(o.data.vertices)
            o.data.transform(Matrix.Translation(-cen)); o.location = cen; o.parent = root
            o.rotation_mode = 'XYZ'
        else:
            o.parent = sway
        shade_smooth(o); parts[key] = o
    # paint: unique materials per car
    body = parts["Body"]
    for i, m in enumerate(body.data.materials):
        if m is None: continue
        m2 = m.copy(); m2.name = name + "_" + m.name
        n, l = nodes_of(m2); bs = next((x for x in n if x.type == 'BSDF_PRINCIPLED'), None)
        if bs and m.name.startswith("body"):
            for lk in list(bs.inputs['Base Color'].links): m2.node_tree.links.remove(lk)
            bs.inputs['Base Color'].default_value = (*paint, 1); bs.inputs['Roughness'].default_value = 0.22 if m.name == "body" else 0.5
            bs.inputs['Metallic'].default_value = 0.0
            try: bs.inputs['Coat Weight'].default_value = 0.6
            except Exception: pass
        body.data.materials[i] = m2
    for k, o in parts.items():
        if k == "Body": continue
        for i, m in enumerate(o.data.materials):
            if m and m.name.startswith("body"):
                o.data.materials[i] = next(mm for mm in body.data.materials if mm and mm.name.endswith("_" + m.name))
    # folded roof bundle behind the rear seat (leather roll + two bows)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.13, radius2=0.13, depth=1.25,
                          matrix=Matrix.Translation(V(0, 1.18, 1.38)) @ Matrix.Rotation(R_(90), 4, 'Y'))
    for f in bm.faces: f.material_index = 0
    for dz in (0.0, 0.06):
        bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.015, radius2=0.015, depth=1.3,
                              matrix=Matrix.Translation(V(0, 1.24 + dz, 1.46 + dz)) @ Matrix.Rotation(R_(90), 4, 'Y'))
    roof = mesh_obj(name + "_FoldedRoof", bm, [flat(name + "_RoofLeather", (0.08, 0.06, 0.05), rough=0.55)], c)
    roof.parent = sway; shade_smooth(roof)
    root["wheel_r"] = (parts["wheel front"].dimensions.z) / 2
    return root, sway, parts

car1, sway1, P1 = build_car("Car1", (0.03, 0.05, 0.04))
car2, sway2, P2 = build_car("Car2", (0.12, 0.03, 0.03))
car2.location = (30, -2, 0)
bpy.context.view_layer.update()
bb = [P1["Body"].matrix_world @ Vector(c) for c in P1["Body"].bound_box]
print("CAR1 bbox", Vector(map(min, *bb)), Vector(map(max, *bb)), "wheel_r", car1["wheel_r"])

# ------------------------------------------------------------------ props
def cone(bm, r1, r2, d, M, seg=16, mat=0):
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=d, matrix=M)
    for v in res['verts']:
        for f in v.link_faces: f.material_index = mat

M_DKBLUE = flat("HelmetBlack", (0.015, 0.03, 0.02), rough=0.25, metal=0.2)
M_GOLD = flat("Gold", (0.8, 0.55, 0.2), rough=0.3, metal=1.0)
M_PLUME = flat("PlumeGreen", (0.02, 0.12, 0.04), rough=0.55)
M_WHITE = flat("HatWhite", (0.88, 0.87, 0.84), rough=0.7)
M_LACE = flat("ParasolLace", (0.9, 0.89, 0.86), rough=0.8, trans=0.15)
M_GUN = flat("GunMetal", (0.02, 0.02, 0.02), rough=0.35, metal=0.9)
M_GRIP = flat("GripWood", (0.15, 0.08, 0.04), rough=0.6)
M_BOMB = flat("DarkObject", (0.03, 0.03, 0.028), rough=0.5, metal=0.6)
M_CAP = flat("CapDark", (0.05, 0.05, 0.06), rough=0.6)

# general's helmet: dark shell fitted to the skull, thin gold band, finial, and a crest of thin dark-green plume strands
# streaming back (head faces -Y, so back is +Y). Origin = skull top.
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.104, matrix=Matrix.Translation(V(0, 0.008, -0.075)) @ Matrix.Diagonal((0.98, 1.12, 0.92, 1)))
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.083], context='VERTS')
cone(bm, 0.104, 0.104, 0.012, Matrix.Translation(V(0, 0.008, -0.078)) @ Matrix.Diagonal((0.98, 1.12, 1, 1)), seg=24, mat=1)
cone(bm, 0.016, 0.006, 0.045, Matrix.Translation(V(0, 0.0, 0.035)), seg=8, mat=1)
random.seed(7)
for i in range(70):
    a0 = random.uniform(-0.6, 0.6); L = random.uniform(0.18, 0.3); w = 0.006
    p = [V(0, 0, 0.05)]
    d = V(math.sin(a0) * 0.35, random.uniform(0.4, 0.8), random.uniform(0.5, 0.9)).normalized()
    for k in range(1, 5):
        u = k / 4
        p.append(V(0, 0, 0.05) + d * L * u + V(0, 0.06 * u * u, -0.18 * u * u))
    side = V(math.cos(a0), 0, 0) * w
    vl = [bm.verts.new(q - side * (1 - j / 5)) for j, q in enumerate(p)]; vr = [bm.verts.new(q + side * (1 - j / 5)) for j, q in enumerate(p)]
    for j in range(len(p) - 1):
        f = bm.faces.new((vl[j], vr[j], vr[j + 1], vl[j + 1])); f.material_index = 2
helmet = mesh_obj("Helmet", bm, [M_DKBLUE, M_GOLD, M_PLUME], CP)
# wide white hat
bm = bmesh.new()
cone(bm, 0.26, 0.26, 0.012, Matrix.Translation(V(0, 0, -0.025)), seg=32)
cone(bm, 0.105, 0.095, 0.09, Matrix.Translation(V(0, 0, 0.02)), seg=24)
for i in range(8):
    a = R_(i * 24 - 60); d = V(math.cos(a), math.sin(a), 0.4).normalized()
    p0 = V(0.06 * math.cos(a), 0.06 * math.sin(a), 0.06); side = d.cross(V(0, 0, 1)).normalized() * 0.025
    vs = [bm.verts.new(p) for p in (p0, p0 + d * 0.12 + side, p0 + d * 0.2, p0 + d * 0.12 - side)]
    bm.faces.new(vs)
hat = mesh_obj("WideHat", bm, [M_WHITE], CP)
# parasol: origin at grip, shaft along +Z
bm = bmesh.new()
cone(bm, 0.008, 0.008, 0.95, Matrix.Translation(V(0, 0, 0.42)), seg=8, mat=1)
res = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.065, radius2=0.01, depth=0.55, matrix=Matrix.Translation(V(0, 0, 0.62)))   # furled
for f in bm.faces:
    if f.material_index == 0 and all(v.co.z > 0.65 for v in f.verts): f.material_index = 0
parasol = mesh_obj("Parasol", bm, [M_LACE, M_GOLD], CP)
# pistol silhouette (no mechanism detail): origin at grip, barrel along local -Y (hand forward)
bm = bmesh.new()
add_box(bm, V(-0.013, -0.17, 0.02), V(0.013, 0.02, 0.055), 0)
add_box(bm, V(-0.014, -0.01, -0.08), V(0.014, 0.04, 0.03), 1)
pistol = mesh_obj("Pistol", bm, [M_GUN, M_GRIP], CP)
# the thrown object: a plain dark ball
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.055)
cone(bm, 0.018, 0.018, 0.03, Matrix.Translation(V(0, 0, 0.06)), seg=8)
bomb = mesh_obj("Bomb", bm, [M_BOMB], CP); shade_smooth(bomb)
# caps
def cap(name, mat):
    bm = bmesh.new()
    cone(bm, 0.105, 0.12, 0.07, Matrix.Translation(V(0, 0, 0.0)), seg=20)
    cone(bm, 0.11, 0.11, 0.008, Matrix.Translation(V(0, -0.09, -0.03)) @ Matrix.Diagonal((0.8, 0.55, 1, 1)), seg=16)
    return mesh_obj(name, bm, [mat], CP)
cap("DriverCap", M_CAP); cap("OfficerCap", flat("OfficerCapMat", (0.1, 0.12, 0.18), rough=0.5))
for o in (helmet, hat, parasol, bomb): shade_smooth(o)

def attach_to_bone(obj, arm, bone, M_world):
    bpy.context.view_layer.update()
    obj.parent = arm; obj.parent_type = 'BONE'; obj.parent_bone = bone
    bpy.context.view_layer.update()
    obj.matrix_world = M_world

def head_top(arm):
    b = arm.data.bones["head"]
    return arm.matrix_world @ b.tail_local, b
# handlebar moustache: placed under the nose tip found on the body mesh
def body_verts(arm):
    body = bpy.data.objects[arm.name + ".body"]; dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); me = ev.to_mesh()
    vs = [body.matrix_world @ v.co for v in me.vertices]; ev.to_mesh_clear(); return vs
def nose_tip(arm):
    vs = [v for v in body_verts(arm) if abs(v.x) < 0.012 and v.z > 1.2]
    zt = max(v.z for v in vs)
    return min((v for v in vs if zt - 0.32 < v.z < zt - 0.12), key=lambda v: v.y)
def skull_top(arm):
    vs = [v for v in body_verts(arm) if abs(v.x) < 0.03 and v.z > 1.0]
    t = max(vs, key=lambda v: v.z); return t
arch = bpy.data.objects["Archduke"]
nt = nose_tip(arch)
bm = bmesh.new()
for sx in (1, -1):
    pts = [V(0.004 * sx, -0.004, -0.03), V(0.02 * sx, 0.0, -0.035), V(0.038 * sx, 0.008, -0.03), V(0.05 * sx, 0.016, -0.017), V(0.056 * sx, 0.02, -0.005)]
    ws = [0.009, 0.008, 0.006, 0.004, 0.002]
    vu = [bm.verts.new(p + V(0, 0, w)) for p, w in zip(pts, ws)]; vd = [bm.verts.new(p - V(0, 0, w)) for p, w in zip(pts, ws)]
    vb = [bm.verts.new(p + V(0, 0.006, 0)) for p in pts]
    for j in range(len(pts) - 1):
        bm.faces.new((vu[j], vu[j + 1], vd[j + 1], vd[j])); bm.faces.new((vu[j], vb[j], vb[j + 1], vu[j + 1])); bm.faces.new((vd[j], vd[j + 1], vb[j + 1], vb[j]))
mous = mesh_obj("Moustache", bm, [flat("MoustacheHair", (0.05, 0.035, 0.025), rough=0.6)], CP); shade_smooth(mous)
attach_to_bone(mous, arch, "head", Matrix.Translation(nt))
print("NOSE", nt)
cap("FlatCapA", flat("FlatCapTweed", (0.2, 0.17, 0.13), rough=0.9))
for nm, obj, dz, dy in (("Archduke", helmet, 0.0, 0.012), ("NerveA", bpy.data.objects["FlatCapA"], -0.055, 0.0), ("Duchess", hat, -0.085, 0.01), ("Driver", bpy.data.objects["DriverCap"], -0.075, 0.0),
                        ("Officer", bpy.data.objects["OfficerCap"], -0.075, 0.0)):
    arm = bpy.data.objects[nm]
    top = (skull_top(arm) + V(0, 0, 0.012)) if nm in ('Archduke', 'NerveA') else head_top(arm)[0]   # skull top + hair for the new pieces
    attach_to_bone(obj, arm, "head", Matrix.Translation(top + V(0, dy, dz)))
print("PROPS_DONE")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
