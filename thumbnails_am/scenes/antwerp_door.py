"""Antwerp thumbnail (the user's concept): the massive round vault door swung wide open, seen 3/4 from above at the
front; through the doorway the vault with its rows of forced deposit boxes, softly lit; spilling out across the floor
toward the camera, jewels: sparkling brilliants, gold rings, necklaces and a few gold bars. Seldom yellow #E3FF00 is
the hero colour: the door's inner face and bolt-work, and the light pouring out of the vault. Everything else dark
blue-grey steel and concrete (never black), a soft volumetric beam and fine dust. Darker wall on the left for text.
    PREVIEW=0.4 SPP=32 blender -b --python antwerp_door.py"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tcommon as T
C = T.use("antwerp")
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix
import sets as S, props as PR, ship as SH
import vaultkit as V
E = os.environ.get
sc = T.res_setup(int(E("SPP", "256")), noise=0.012)
sc.cycles.max_bounces = 8; sc.cycles.glossy_bounces = 6; sc.cycles.transmission_bounces = 10
rng = random.Random(int(E("SEED", "5")))
col = sc.collection

# ---------------------------------------------------------------- materials
steel = V.brush(V.mono("door_steel", 0.5, rough=0.22, metal=0.85, var=0.05))
plate = V.mono("plates", 0.32, rough=0.3, metal=0.7)
black = V.mono("black", 0.02, rough=0.5)
box_m = V.brush(V.mono("box_steel", 0.42, rough=0.26, metal=0.7, var=0.06), scratch=1.0)
cav_m = V.mono("cavity", 0.012, rough=0.8)
frame_m = V.mono("frames", 0.2, rough=0.45, metal=0.3)
conc = V.mono("concrete", 0.2, rough=0.85, var=0.25, scale=1.5)
floor_m = V.mono("floor", 0.17, rough=0.4, var=0.2, scale=1.0)
floor_m.node_tree.nodes["Principled BSDF"].inputs['Coat Weight'].default_value = 0.4
YEL = V.yellow("door_inner_yellow", rough=0.3)
YEL_B = V.yellow("bolt_yellow", mult=0.85, rough=0.22)
for m_ in (YEL, YEL_B):
    p_ = m_.node_tree.nodes["Principled BSDF"]; p_.inputs['Metallic'].default_value = 0.35; p_.inputs['Coat Weight'].default_value = 0.6
gold = S.gold("gold", (1.0, 0.72, 0.28))
gold.node_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = 0.16
fire = PR.fire_glass("diamond_fire")
_N = fire.node_tree.nodes; _L = fire.node_tree.links; _out = _N["Material Output"]; _src = _out.inputs['Surface'].links[0].from_socket
_g2 = _N.new("ShaderNodeBsdfGlossy"); _g2.inputs['Roughness'].default_value = 0.01; _g2.inputs['Color'].default_value = (0.55, 0.55, 0.55, 1)
_ad = _N.new("ShaderNodeAddShader"); _L.new(_src, _ad.inputs[0]); _L.new(_g2.outputs[0], _ad.inputs[1]); _L.new(_ad.outputs[0], _out.inputs['Surface'])

# ---------------------------------------------------------------- the front wall with the round doorway, and the vault behind
R = float(E("R_OPEN", "1.2")); DZ = R + 0.12; WT = 0.9
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, WT / 2, 2.0)); fw = bpy.context.active_object; fw.name = "front_wall"
fw.scale = (14, WT, 4.0)
bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=R, depth=WT * 3, location=(0, WT / 2, DZ), rotation=(math.pi / 2, 0, 0))
hole = bpy.context.active_object; hole.hide_render = True; hole.hide_viewport = True
bo = fw.modifiers.new("hole", "BOOLEAN"); bo.object = hole; bo.operation = 'DIFFERENCE'; bo.solver = 'EXACT'
fw.data.materials.append(conc)
jamb = SH.cyl("jamb", (0, 0.0, DZ), (0, WT, DZ), R + 0.001, mat=steel, verts=128, caps=False)
jamb.modifiers.new("t", "SOLIDIFY").thickness = 0.05
for (rr, y_) in ((R + 0.14, -0.02), (R + 0.3, -0.01)):
    bpy.ops.mesh.primitive_torus_add(major_radius=rr, minor_radius=0.07, major_segments=128, minor_segments=12,
                                     location=(0, y_, DZ), rotation=(math.pi / 2, 0, 0))
    t_ = bpy.context.active_object; t_.scale = (1, 1, 0.45); t_.data.materials.append(steel)
S.box("floor", (0, 2, -0.05), (16, 20, 0.1), floor_m)
VD, VX, VZ = 7.0, float(E("VX", "1.55")), 3.2
S.box("vault_ceiling", (0, WT + VD / 2, VZ + 0.05), (2 * VX + 1, VD, 0.1), frame_m)
S.box("vault_back", (0, WT + VD + 0.05, VZ / 2), (2 * VX + 1, 0.1, VZ), frame_m)
# rows of forced boxes on the vault walls (small dense grid; every door bent open)
CW, RH, Z0 = 0.16, 0.13, 0.25
door_t = S._door_mesh(CW, RH, "boxdoor", (box_m, plate, black)); cav_t = S._cavity_mesh(CW, RH, 0.45, "cav", cav_m)
NR = int((VZ - Z0 - 0.3) / RH)
def wall(org, yaw, ncol):
    Rm = Matrix.Rotation(yaw, 4, 'Z')
    for c in range(ncol):
        for r in range(NR):
            M = Matrix.Translation(Vector(org) + Rm @ Vector((c * CW, 0, Z0 + (r + 0.5) * RH))) @ Rm
            cv = cav_t.copy(); col.objects.link(cv); cv.matrix_world = M
            d = door_t.copy(); col.objects.link(d)
            d.matrix_world = M @ Matrix.Rotation(math.radians(-rng.uniform(70, 160)), 4, 'Z') @ Matrix.Rotation(math.radians(rng.uniform(-6, 6)), 4, 'X')
    W = ncol * CW
    S.box("bank_back", Vector(org) + Rm @ Vector((W / 2, 0.47, (Z0 + NR * RH) / 2)), (W, 0.02, Z0 + NR * RH), cav_m).rotation_euler.z = yaw
wall((-VX, WT + 0.3, 0), math.pi / 2, int((VD - 0.6) / CW))          # left wall, faces +x
wall((VX, WT + VD - 0.3, 0), -math.pi / 2, int((VD - 0.6) / CW))     # right wall, faces -x
wall((-VX + 0.3, WT + VD, 0), 0.0, int((2 * VX - 0.6) / CW))         # back wall, faces -y

# ---------------------------------------------------------------- the door: swung wide open toward the camera, inner face yellow
Rd = R - 0.02
leaf = V.vault_door(Rd, steel, plate, black, face=YEL, bolt=YEL_B)
leaf.location = (R + 0.3, -0.32, DZ)
leaf.rotation_euler.z = math.radians(float(E("DOOR_ANG", "118")))
S.box("hinge_block", (R + 0.42, -0.32, DZ), (0.34, 0.34, 2.0), steel, bevel=0.03)

# ---------------------------------------------------------------- the spill: jewels across the floor toward the camera
gems = bpy.data.collections.new("gems"); col.children.link(gems)
def to_gems(o):
    for c_ in list(o.users_collection):
        c_.objects.unlink(o)
    gems.objects.link(o)
def spill_pt(spread=1.0):
    t = rng.random() ** 1.4
    y = -0.2 - 2.4 * t
    x = rng.gauss(-0.05 - 0.35 * t, 0.2 + 0.55 * t) * spread
    return Vector((x, y, 0))
for i in range(int(E("NGEM", "55"))):
    d = rng.uniform(0.04, 0.095) * float(E("GEMS", "1.0"))
    g = PR.brilliant(f"gem{i}", d, fire); p_ = spill_pt()
    if rng.random() < 0.7:
        g.location = p_ + Vector((0, 0, d * 0.43)); g.rotation_euler = (rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25), rng.uniform(0, 6.28))
    else:
        g.location = p_ + Vector((0, 0, d * 0.45)); g.rotation_euler = (math.radians(70), 0, rng.uniform(0, 6.28))
    to_gems(g)
# gold rings, each with a stone
for i in range(int(E("NRING", "9"))):
    p_ = spill_pt(0.8)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.011, minor_radius=0.0022, major_segments=48, minor_segments=12, location=p_ + Vector((0, 0, 0.0025)))
    rg = bpy.context.active_object; rg.data.materials.append(gold); rg.rotation_euler = (rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), 0)
    rg.scale = (5.0, 5.0, 5.0)
    st = PR.brilliant(f"ringstone{i}", 0.03, fire); st.location = rg.location + Vector((0.055, 0, 0.03)); st.rotation_euler = (0, math.radians(90), 0)
    to_gems(st)
# necklaces: gold chains of small links snaking over the floor, with a pendant stone
for i in range(int(E("NNECK", "4"))):
    p0 = spill_pt(0.9); a0 = rng.uniform(0, 6.28); pts = [p0]
    for k in range(60):
        a0 += rng.uniform(-0.35, 0.35); pts.append(pts[-1] + Vector((math.cos(a0) * 0.028, math.sin(a0) * 0.028, 0)))
    for k, q in enumerate(pts):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.011, minor_radius=0.003, major_segments=12, minor_segments=6,
                                         location=q + Vector((0, 0, 0.0014)), rotation=((math.pi / 2) * (k % 2), 0, a0 + k * 0.1))
        bpy.context.active_object.data.materials.append(gold)
    pd = PR.brilliant(f"pendant{i}", 0.07, fire); pd.location = pts[len(pts) // 2] + Vector((0, 0.02, 0.013)); to_gems(pd)
# a few gold bars
for i in range(int(E("NBAR", "10"))):
    gb = PR.gold_bar(f"bar{i}", big=True); p_ = spill_pt(0.7); gb.location = p_ * 0.85
    gb.rotation_euler = (0, 0, rng.uniform(0, 3.14))
    gb.data.materials.clear(); gb.data.materials.append(gold)

# ---------------------------------------------------------------- light: yellow light pours out of the vault; blue-grey ambience
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs['Color'].default_value = (0.09, 0.12, 0.16, 1)
bg.inputs['Strength'].default_value = float(E("WORLD", "1.0"))
YL = (0.85, 1.0, 0.25)
YL_SOFT = (1.0, 1.0, 0.7)                       # #E3FF00, a touch softened so it lights rather than burns
T.area("vault_glow", (0, WT + 3.5, VZ - 0.1), (0, WT + 3.5, 0), 1.2, float(E("GLOW_E", "220")), color=YL_SOFT, size_y=6)
spill = bpy.data.lights.new("spill", 'SPOT'); spill.energy = float(E("SPILL_E", "1400")); spill.spot_size = math.radians(55)
spill.spot_blend = 0.7; spill.shadow_soft_size = 0.6; spill.color = YL
so = bpy.data.objects.new("spill", spill); col.objects.link(so); so.location = (0.2, WT + 2.8, DZ + 0.6)
so.rotation_euler = (Vector((-0.4, -2.0, 0.0)) - so.location).to_track_quat('-Z', 'Y').to_euler()
T.area("cool_fill", (-3.5, -6.0, 3.5), (0, -0.5, 0.8), 4.0, float(E("COOL_E", "260")), color=(0.6, 0.75, 1.0))
T.area("door_key", (2.0, -4.5, 4.0), (R + 0.3 - Rd, -1.2, DZ), 2.0, float(E("DKEY_E", "220")), color=(1.0, 0.97, 0.9))
glt = bpy.data.lights.new("gem_glint", 'POINT'); glt.energy = float(E("GLINT_E", "600")); glt.shadow_soft_size = 0.02
glo = bpy.data.objects.new("gem_glint", glt); col.objects.link(glo); glo.location = (-1.5, -4.0, 2.5)
glo.light_linking.receiver_collection = gems; glo.visible_diffuse = False
# the beam: haze in front of the doorway lit only by the spill, with fine dust
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -2.5, 1.6)); hz = bpy.context.active_object; hz.name = "haze"; hz.scale = (8, 5, 3.2)
hm = bpy.data.materials.new("haze"); hm.use_nodes = True; HN = hm.node_tree.nodes; HN.remove(HN["Principled BSDF"])
vs = HN.new("ShaderNodeVolumeScatter"); vs.inputs['Anisotropy'].default_value = 0.6
htc = HN.new("ShaderNodeTexCoord"); hnz = HN.new("ShaderNodeTexNoise"); hnz.inputs['Scale'].default_value = 1.2
hm.node_tree.links.new(htc.outputs['Object'], hnz.inputs['Vector'])
hmr = HN.new("ShaderNodeMapRange"); hmr.inputs['To Min'].default_value = float(E("HAZE", "0.03")) * 0.4; hmr.inputs['To Max'].default_value = float(E("HAZE", "0.03")) * 1.5
hm.node_tree.links.new(hnz.outputs['Fac'], hmr.inputs['Value']); hm.node_tree.links.new(hmr.outputs[0], vs.inputs['Density'])
hm.node_tree.links.new(vs.outputs[0], HN["Material Output"].inputs['Volume']); hz.data.materials.append(hm); hz.visible_shadow = False
N_M = int(E("NMOTE", "220")); r_ = np.random.default_rng(3)
P = np.stack([r_.uniform(-1.6, 1.2, N_M), r_.uniform(-3.0, 0.0, N_M), r_.uniform(0.2, 2.6, N_M)], 1)
me = bpy.data.meshes.new("motes"); me.from_pydata(P.tolist(), [], []); me.update()
mo = bpy.data.objects.new("motes", me); col.objects.link(mo)
ng = bpy.data.node_groups.new("motes_pts", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
gi = ng.nodes.new("NodeGroupInput"); go = ng.nodes.new("NodeGroupOutput"); mp = ng.nodes.new("GeometryNodeMeshToPoints")
mp.inputs['Radius'].default_value = 0.0025; smn = ng.nodes.new("GeometryNodeSetMaterial")
mm = bpy.data.materials.new("mote"); mm.use_nodes = True; MN = mm.node_tree.nodes; MN.remove(MN["Principled BSDF"])
em = MN.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (0.95, 1.0, 0.7, 1); em.inputs['Strength'].default_value = float(E("MOTE_E", "1.5"))
mm.node_tree.links.new(em.outputs[0], MN["Material Output"].inputs['Surface']); smn.inputs['Material'].default_value = mm
ng.links.new(gi.outputs[0], mp.inputs['Mesh']); ng.links.new(mp.outputs['Points'], smn.inputs['Geometry']); ng.links.new(smn.outputs['Geometry'], go.inputs[0])
mo.modifiers.new("pts", "NODES").node_group = ng
for o in sc.objects:
    if o.type == 'LIGHT' and o.name not in ("spill",):
        o.visible_volume_scatter = False
try:
    sc.world.cycles_visibility.scatter = False
except Exception:
    pass

# ---------------------------------------------------------------- camera: 3/4 from the front-left, ~35 deg down
EL = math.radians(float(E("CAM_EL", "34"))); DIST = float(E("DIST", "7.0")); AZ = math.radians(float(E("CAM_AZ", "-112")))
tgt = Vector((float(E("TX", "0.2")), float(E("TY", "-0.6")), float(E("TZ", "0.9"))))
cam = tgt + Vector((math.cos(AZ) * math.cos(EL), math.sin(AZ) * math.cos(EL), math.sin(EL))) * DIST
C.camera(cam, tgt, lens=float(E("LENS", "32")), fstop=float(E("FSTOP", "5.6")), focus=(Vector((0.3, -0.8, 0.6)) - cam).length)

T.grade(sc, sat=float(E("SAT", "1.25")), con=float(E("CON", "1.15")), expo=float(E("EXPO", "0.0")), vig=float(E("VIG", "0.35")))
T.glints(sc, thr=float(E("GLT", "0.9")), strength=float(E("GLS", "0.7")))
T.render(sc, "antwerp_door")
