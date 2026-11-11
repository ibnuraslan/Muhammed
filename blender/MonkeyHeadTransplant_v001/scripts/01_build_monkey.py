"""Monkey parts from the CC-BY 'Realistic Monkey' (TdoubleU8).
blender -b --python scripts/01_build_monkey.py -- build/monkey.blend
Makes: MK_Head (pale donor head, capped clean underside), MK_BodyA (pale donor body), MK_BodyB (ginger body),
eyeballs + blink lids + ear-twitch shape keys on the head. All in the model's own sitting frame (feet z=0)."""
import bpy, bmesh, sys, math
from mathutils import Vector, Matrix
out = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="assets/monkey.glb")
src = [o for o in bpy.data.objects if o.type == "MESH"][0]
M = src.matrix_world.copy(); src.parent = None; src.matrix_world = M
for o in list(bpy.data.objects):
    if o != src: bpy.data.objects.remove(o)
bpy.context.view_layer.objects.active = src; src.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
zmin = min(v.co.z for v in src.data.vertices)
for v in src.data.vertices: v.co.z -= zmin
DZ = -zmin
src.name = "MK_src"
F = Vector((-0.385, -0.923, 0)).normalized()          # face direction (head is turned ~23 deg to its right)
Z = Vector((0, 0, 1)); RT = F.cross(Z).normalized()     # head's right (+X-ish)
EYE_SURF = {"L": Vector((-0.1012, -0.4595, 0.2632 + DZ)), "R": Vector((-0.0676, -0.4742, 0.2638 + DZ))}
EAR_TIP = {"L": Vector((-0.1150, -0.3769, 0.3110 + DZ)), "R": Vector((0.0018, -0.4235, 0.3150 + DZ))}
P0 = Vector((-0.080, -0.440, 0.188 + DZ)); N = (Z + F * 0.5).normalized()   # neck cut plane, rises toward the back
print("DZ", DZ)

skin = src.data.materials[0]
stump = bpy.data.materials.new("M_NeckCap"); stump.use_nodes = True
b = stump.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.78, 0.55, 0.5, 1)
b.inputs["Roughness"].default_value = 0.55
b.inputs["Subsurface Weight"].default_value = 0.3; b.inputs["Subsurface Radius"].default_value = (0.02, 0.008, 0.006)

def cut(name, keep_above):
    me = src.data.copy(); me.name = name
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=2e-5)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    r = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=P0, plane_no=N, clear_inner=keep_above, clear_outer=not keep_above, dist=1e-5)
    cut_edges = [e for e in r["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    # drop small floating islands on the wrong side (e.g. fingertips if any)
    nf = len(bm.faces)
    res = bmesh.ops.holes_fill(bm, edges=[e for e in cut_edges if e.is_boundary], sides=0)
    me.materials.append(stump)
    for f in res["faces"]:
        f.material_index = 1
    bmesh.ops.triangulate(bm, faces=res["faces"])
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    print("CUT", name, "faces", len(me.polygons), "cap faces", len(res["faces"]))
    return ob

head = cut("MK_Head", True)
bodyA = cut("MK_BodyA", False)
# keep only the largest connected part of the head (removes stray bits of shoulder fur)
for ob in (head, bodyA):
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
    seen = set(); parts = []
    for v in bm.verts:
        if v.index in seen: continue
        st = [v]; comp = []; seen.add(v.index)
        while st:
            x = st.pop(); comp.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen: seen.add(y.index); st.append(y)
        parts.append(comp)
    parts.sort(key=len, reverse=True)
    small = [v for p in parts[1:] for v in p if len(p) < 0.004 * len(bm.verts)]
    bmesh.ops.delete(bm, geom=small, context="VERTS"); bm.to_mesh(ob.data); bm.free()
    print("PARTS", ob.name, [len(p) for p in parts[:6]], "removed", len(small))
bpy.data.objects.remove(src)

# ---------- ginger body B: hue-shifted copy of the skin material
bodyB = bpy.data.objects.new("MK_BodyB", bodyA.data.copy()); bpy.context.scene.collection.objects.link(bodyB)
gm = skin.copy(); gm.name = "M_MonkeyGinger"
nt = gm.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
lk = bsdf.inputs["Base Color"].links[0]; fs = lk.from_socket
hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Hue"].default_value = 0.47; hs.inputs["Saturation"].default_value = 1.35; hs.inputs["Value"].default_value = 0.9
mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 0.35
mx.inputs["B"].default_value = (0.95, 0.62, 0.38, 1)
nt.links.new(fs, hs.inputs["Color"]); nt.links.new(hs.outputs["Color"], mx.inputs["A"]); nt.links.new(mx.outputs["Result"], bsdf.inputs["Base Color"])
bodyB.data.materials[0] = gm
skin.name = "M_MonkeyPale"

# ---------- eyes: keep the painted eyes (realistic); gaze = UV shift of the iris inside each eye disc,
# blink = two lid shells that use the head's own skin texture (UVs pinned to the brow skin next to each eye)
hm = skin.copy(); hm.name = "M_MonkeyHead"; head.data.materials[0] = hm
me = head.data; uvl = me.uv_layers.active.data
vco = [v.co.copy() for v in me.vertices]
loop_of = {}
for l in me.loops: loop_of.setdefault(l.vertex_index, l.index)
def nearest(p):
    return min(range(len(vco)), key=lambda i: (vco[i] - p).length)
def uv_at(i): return Vector(uvl[loop_of[i]].uv)
EYE = {}
for s in "LR":
    i0 = nearest(EYE_SURF[s])
    near = [i for i in range(len(vco)) if (vco[i] - EYE_SURF[s]).length < 0.006]
    nrm = sum((me.vertices[i].normal for i in near), Vector()).normalized()
    # least-squares UV jacobian against head-right and up
    A = []; Bu = []
    c_uv = uv_at(i0)
    for i in near:
        d = vco[i] - vco[i0]; du = uv_at(i) - c_uv
        if du.length > 0.05: continue      # across a UV seam
        A.append((d.dot(RT), d.dot(Z))); Bu.append(du)
    import numpy as np
    A_ = np.array(A); B_ = np.array([[u.x, u.y] for u in Bu])
    J, *_ = np.linalg.lstsq(A_, B_, rcond=None)     # rows: d/dRT, d/dZ  -> (du, dv)
    EYE[s] = dict(c=c_uv, n=nrm, Jr=Vector(J[0]), Jz=Vector(J[1]), i0=i0)
    print("EYE", s, "uv", c_uv, "n", nrm, "Jr", J[0], "Jz", J[1], "pts", len(A))
nt = hm.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
texs = [n for n in nt.nodes if n.type == "TEX_IMAGE"]
uvn = nt.nodes.new("ShaderNodeUVMap")
gx = nt.nodes.new("ShaderNodeValue"); gx.name = gx.label = "GazeX"; gz = nt.nodes.new("ShaderNodeValue"); gz.name = gz.label = "GazeZ"
cur = uvn.outputs["UV"]
R_UV = {}
for s in "LR":
    e = EYE[s]
    r_uv = 0.0062 * (e["Jr"].length + e["Jz"].length) / 2
    R_UV[s] = r_uv
    # offset = -(gx*Jr + gz*Jz)  (texture moves opposite to the uv shift)
    def vec(v):
        n = nt.nodes.new("ShaderNodeCombineXYZ"); n.inputs[0].default_value = v.x; n.inputs[1].default_value = v.y; return n.outputs[0]
    m1 = nt.nodes.new("ShaderNodeVectorMath"); m1.operation = "SCALE"; nt.links.new(vec(-e["Jr"]), m1.inputs[0]); nt.links.new(gx.outputs[0], m1.inputs["Scale"])
    m2 = nt.nodes.new("ShaderNodeVectorMath"); m2.operation = "SCALE"; nt.links.new(vec(-e["Jz"]), m2.inputs[0]); nt.links.new(gz.outputs[0], m2.inputs["Scale"])
    ad = nt.nodes.new("ShaderNodeVectorMath"); ad.operation = "ADD"; nt.links.new(m1.outputs[0], ad.inputs[0]); nt.links.new(m2.outputs[0], ad.inputs[1])
    dist = nt.nodes.new("ShaderNodeVectorMath"); dist.operation = "DISTANCE"; nt.links.new(uvn.outputs["UV"], dist.inputs[0]); nt.links.new(vec(e["c"]), dist.inputs[1])
    fo = nt.nodes.new("ShaderNodeMapRange"); fo.interpolation_type = "SMOOTHSTEP"
    fo.inputs["From Min"].default_value = r_uv; fo.inputs["From Max"].default_value = r_uv * 0.35
    fo.inputs["To Min"].default_value = 0.0; fo.inputs["To Max"].default_value = 1.0
    nt.links.new(dist.outputs["Value"], fo.inputs["Value"])
    sc_ = nt.nodes.new("ShaderNodeVectorMath"); sc_.operation = "SCALE"; nt.links.new(ad.outputs[0], sc_.inputs[0]); nt.links.new(fo.outputs["Result"], sc_.inputs["Scale"])
    tot = nt.nodes.new("ShaderNodeVectorMath"); tot.operation = "ADD"; nt.links.new(cur, tot.inputs[0]); nt.links.new(sc_.outputs[0], tot.inputs[1])
    cur = tot.outputs[0]
for t in texs:
    nt.links.new(cur, t.inputs["Vector"])
R_EYE = 0.0098
for s in "LR":
    e = EYE[s]; Fe = e["n"]; Fe = (Fe - Z * Fe.dot(Z) * 0.6).normalized()
    Re = Fe.cross(Z).normalized(); Ue = Re.cross(Fe).normalized()
    c = EYE_SURF[s] - Fe * (R_EYE - 0.0016)
    piv = bpy.data.objects.new("EyePivot_" + s, None); bpy.context.scene.collection.objects.link(piv)
    piv.matrix_world = Matrix.Translation(c) @ Matrix((Re, -Fe, Ue)).transposed().to_4x4()
    piv.empty_display_size = 0.01
    # brow skin uv: a vertex 7 mm above the eye on the surface
    ib = nearest(EYE_SURF[s] + Ue * 0.0085 + Fe * 0.002); buv = uv_at(ib)
    for nm, up in (("LidUp_" + s, 1), ("LidLo_" + s, -1)):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=R_EYE)
        kill = [v for v in bm.verts if v.co.z * up < -0.00005]
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
        mel = bpy.data.meshes.new(nm); bm.to_mesh(mel); bm.free()
        lu = mel.uv_layers.new(name="UVMap")
        for l in lu.data: l.uv = buv
        lo = bpy.data.objects.new(nm, mel); bpy.context.scene.collection.objects.link(lo)
        lo.data.materials.append(skin); lo.parent = piv
        for p in mel.polygons: p.use_smooth = True
        lo.rotation_mode = "XYZ"
        lo.rotation_euler = (math.radians(-75 if up > 0 else 70), 0, 0)
        so = lo.modifiers.new("solid", "SOLIDIFY"); so.thickness = 0.0008; so.offset = 1.0
    piv.parent = head; piv.matrix_parent_inverse = head.matrix_world.inverted()

# ---------- ear twitch shape keys (rotate the ear about its base toward the face/sound)
head.shape_key_add(name="Basis")
for s in "LR":
    k = head.shape_key_add(name="Ear_" + s)
    tip = EAR_TIP[s]
    base = tip + (Vector((tip.x - (-0.085), tip.y - (-0.42), 0)).normalized() * -0.022) - Z * 0.028
    axis = (tip - base).cross(F).normalized()
    Rm = Matrix.Rotation(math.radians(-24 if s == "R" else 24), 3, axis)
    for i, v in enumerate(head.data.vertices):
        d = (v.co - tip).length
        w = max(0.0, 1.0 - d / 0.032) ** 1.5
        if w > 0 and v.co.z > base.z - 0.004:
            k.data[i].co = base + (Rm @ (v.co - base) - (v.co - base)) * w + (v.co - base)
kr = head.shape_key_add(name="Ears_Round")
for s_ in "LR":
    tip = EAR_TIP[s_]
    base = tip + (Vector((tip.x - (-0.085), tip.y - (-0.42), 0)).normalized() * -0.018) - Z * 0.024
    for i, v in enumerate(head.data.vertices):
        d = (v.co - tip).length
        w = max(0.0, 1.0 - d / 0.03) ** 1.2
        if w > 0 and v.co.z > base.z - 0.004:
            kr.data[i].co = v.co + (base - v.co) * 0.42 * w
for o in (head, bodyA, bodyB):
    for p in o.data.polygons: p.use_smooth = True
# neck reference for later scripts
nk = bpy.data.objects.new("NeckRef", None); bpy.context.scene.collection.objects.link(nk)
nk.matrix_world = Matrix.Translation(P0) @ N.to_track_quat("Z", "Y").to_matrix().to_4x4()
print("HEAD bb z", min(v.co.z for v in head.data.vertices), max(v.co.z for v in head.data.vertices))
print("BODY bb", [round(min(v.co[i] for v in bodyA.data.vertices), 3) for i in range(3)], [round(max(v.co[i] for v in bodyA.data.vertices), 3) for i in range(3)])
bpy.ops.wm.save_as_mainfile(filepath=bpy.path.abspath(out) if not out.startswith("/") else out)
print("SAVED", out)
