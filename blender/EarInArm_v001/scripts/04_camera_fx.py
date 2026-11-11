"""Studio B growth FX, lights, render settings and the single continuous camera.
blender -b work/anim.blend --python 04_camera_fx.py -- work/film.blend"""
import sys, os, math, random, json
import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[sys.argv.index("--") + 1]
R_ = math.radians
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
sc = bpy.context.scene; OB = bpy.data.objects
random.seed(5)
V = lambda *a: Vector(a)

def newmat(name, col, rough=0.5, sss=0.0, emit=None, alpha=1.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    if sss: b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Scale"].default_value = 0.01
    if emit: b.inputs["Emission Color"].default_value = (*emit[0], 1); b.inputs["Emission Strength"].default_value = emit[1]
    if alpha < 1: b.inputs["Alpha"].default_value = alpha
    if coat: b.inputs["Coat Weight"].default_value = coat
    return m

# ================================================================== studio B: ear in the tissue, vessels grow, skin creeps
SB = V(60, 0, 1.2)
OB["SB_SkinXray"].location.z += 0.03
earB = OB["Ear_Src"].copy(); earB.data = OB["Ear_Src"].data.copy(); earB.name = "SB_Ear"; bpy.data.collections["Studio_Tissue"].objects.link(earB)
earB.matrix_world = Matrix.Translation(SB + V(0, 0, 0.034)) @ Matrix.Rotation(R_(-90), 4, 'X') @ Matrix.Scale(4.0, 4)
# material: cartilage -> pink skin, a wipe across the ear (object Z) keyed 860..1040
m = bpy.data.materials.new("SB_EarGrow"); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
cart = nt.nodes.new("ShaderNodeBsdfPrincipled"); cart.inputs["Base Color"].default_value = (0.86, 0.88, 0.9, 1); cart.inputs["Roughness"].default_value = 0.3
cart.inputs["Subsurface Weight"].default_value = 0.35; cart.inputs["Subsurface Scale"].default_value = 0.01; cart.inputs["Coat Weight"].default_value = 0.4
skin = nt.nodes.new("ShaderNodeBsdfPrincipled"); skin.inputs["Base Color"].default_value = (0.78, 0.45, 0.4, 1); skin.inputs["Roughness"].default_value = 0.45
skin.inputs["Subsurface Weight"].default_value = 0.35; skin.inputs["Subsurface Scale"].default_value = 0.01
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
noi = nt.nodes.new("ShaderNodeTexNoise"); noi.inputs["Scale"].default_value = 80.0; nt.links.new(tc.outputs["Object"], noi.inputs["Vector"])
add = nt.nodes.new("ShaderNodeMath"); add.operation = 'MULTIPLY_ADD'; add.inputs[1].default_value = 0.012
nt.links.new(noi.outputs["Fac"], add.inputs[0]); nt.links.new(sep.outputs["Z"], add.inputs[2])
thr = nt.nodes.new("ShaderNodeMath"); thr.operation = 'GREATER_THAN'; nt.links.new(add.outputs[0], thr.inputs[0])
for f, v in ((1, 0.05), (860, 0.05), (1040, -0.05)):
    thr.inputs[1].default_value = v; thr.inputs[1].keyframe_insert("default_value", frame=f)
mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(thr.outputs[0], mx.inputs[0]); nt.links.new(cart.outputs[0], mx.inputs[1]); nt.links.new(skin.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
earB.data.materials.clear(); earB.data.materials.append(m)
# gentle pulse on the heartbeat
for f in range(775, 1063, 30):
    earB.scale = (4.0,) * 3 if (f // 30) % 2 else (4.08,) * 3; earB.keyframe_insert("scale", frame=f)
# vessels: surface random walks on the ear (bvh), drawn on with bevel_factor_end
dg = bpy.context.evaluated_depsgraph_get(); bpy.context.view_layer.update()
Mw = earB.matrix_world
verts = [Mw @ v.co for v in earB.data.vertices]; polys = [tuple(p.vertices) for p in earB.data.polygons]
bvh = BVHTree.FromPolygons(verts, polys)
ctr = sum(verts, Vector()) / len(verts)
M_VES = newmat("SB_Vessel", (0.6, 0.03, 0.04), 0.3, sss=0.3, emit=((1.0, 0.08, 0.08), 0.6))
ves_em = M_VES.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f in range(775, 1063, 30):
    ves_em.default_value = 1.5 if (f // 30) % 2 else 0.4; ves_em.keyframe_insert("default_value", frame=f)
for i in range(22):
    start = ctr + V(random.uniform(-0.09, 0.09), random.uniform(-0.12, 0.12), 0.03)
    p, n, _, _ = bvh.find_nearest(start)
    if p is None: continue
    pts = [p]; d = V(random.uniform(-1, 1), random.uniform(-1, 1), 0).normalized()
    for k in range(14):
        q = pts[-1] + d * 0.012; q, n2, _, _ = bvh.find_nearest(q)
        if q is None: break
        pts.append(q + n2 * 0.003); d = (d + V(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5), 0)).normalized()
    cu = bpy.data.curves.new("SB_Vessel%d" % i, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = random.uniform(0.0015, 0.003); cu.bevel_resolution = 2
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for k, q in enumerate(pts): sp.points[k].co = (*q, 1)
    cu.materials.append(M_VES); o = bpy.data.objects.new(cu.name, cu); bpy.data.collections["Studio_Tissue"].objects.link(o)
    f0 = 830 + i * 6
    cu.bevel_factor_end = 0.0; cu.keyframe_insert("bevel_factor_end", frame=f0); cu.bevel_factor_end = 1.0; cu.keyframe_insert("bevel_factor_end", frame=f0 + 90)

# ================================================================== world + OR lights + render settings
w = bpy.data.worlds.get("World") or bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
env = w.node_tree.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(HERE, "..", "assets", "hdri", "surgery_2k.hdr"))
bg = w.node_tree.nodes["Background"]; w.node_tree.links.new(env.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 0.6
for i, (loc, en, sz, col) in enumerate(((V(0.3, 0.2, 2.3), 260, 0.7, (1, 0.98, 0.95)), (V(1.6, -1.8, 2.4), 300, 1.5, (1, 0.96, 0.9)),
                                       (V(-1.5, 1.2, 2.2), 150, 1.2, (0.85, 0.92, 1.0)))):
    ld = bpy.data.lights.new("OR_Key%d" % i, 'AREA'); ld.energy = en; ld.size = sz; ld.color = col
    lo = bpy.data.objects.new(ld.name, ld); bpy.data.collections["OR_Set"].objects.link(lo); lo.location = loc
    lo.rotation_euler = (V(0.3, 0, 1.0) - loc).to_track_quat('-Z', 'Y').to_euler()
# surgical light spot onto the working area, follows the action (arm then head)
sd = bpy.data.lights.new("OR_SurgSpot", 'SPOT'); sd.energy = 120; sd.spot_size = R_(35); sd.spot_blend = 0.6; sd.shadow_soft_size = 0.25
spot = bpy.data.objects.new("OR_SurgSpot", sd); bpy.data.collections["OR_Set"].objects.link(spot); spot.location = (0.5, 0.0, 2.0)
r = sc.render; r.engine = 'CYCLES'; r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100; r.fps = 60; r.fps_base = 1.0
sc.cycles.samples = 48; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.cycles.denoiser = 'OPENIMAGEDENOISE'; sc.cycles.device = 'CPU'
sc.cycles.max_bounces = 8; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3; sc.cycles.transmission_bounces = 8; sc.cycles.transparent_max_bounces = 8
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False; r.use_persistent_data = True
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - High Contrast'; sc.view_settings.exposure = -1.9
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'; r.image_settings.color_depth = '8'; r.image_settings.compression = 15
r.filepath = "//render/EarInArm_"

# ================================================================== camera: one camera, continuous spline per space, jumps hidden in full-frame surfaces
def ev_at(f): sc.frame_set(f); bpy.context.view_layer.update()
P = OB["Patient"]
def pbone(name, f):
    ev_at(f); return P.matrix_world @ P.pose.bones[name].head
EAR1 = pbone("head", 60) + (P.matrix_world.to_3x3() @ V(0.08, 0.0, 0.02))
FACE1 = pbone("head", 60) + V(0, -0.1, 0.04)
CHEST = V(0.08, -0.16, 1.02)
P0 = OB["SA_CartBlock"].location.copy()
ev_at(340); BLK_SA = OB["SA_CartBlock"].matrix_world.translation.copy(); ev_at(1)
TRAY = OB["Tray"].matrix_world.translation.copy(); BLK = TRAY + V(-0.02, -0.02, 0.035)
ev_at(700); INC = OB["Arm_Pocket"].matrix_world.translation.copy()
ev_at(1480); EAR_W = OB["Ear_New"].matrix_world.translation.copy()
Hm = P.matrix_world @ P.pose.bones["head"].matrix
EAR_OUT = (Hm.to_3x3() @ V(1, 0, 0)).normalized()
ev_at(1300); FT = OB["Forceps"].matrix_world @ V(0, 0.13, 0)
ev_at(1760); FACE9 = P.matrix_world @ P.pose.bones["head"].head + V(0, -0.1, 0.05); EAR9 = OB["Ear_New"].matrix_world.translation.copy()
print("CAMPTS", EAR1, FACE1, BLK_SA, BLK, INC, EAR_W, EAR_OUT, FACE9, EAR9)
up = V(0, 0, 1); fwd = up.cross(EAR_OUT).normalized()
def EO(o, s, u): return EAR_W + EAR_OUT * o + fwd * s + up * u

SEGS = [
  [  # OR: beat 1 -> into the chest
    (1, V(1.9, -1.7, 1.2), FACE1 + V(0, 0, -0.1), 26), (30, V(1.35, -1.1, 1.35), FACE1, 32), (60, V(0.8, -0.72, 1.42), FACE1, 42),
    (90, V(0.8, -0.18, 1.45), EAR1, 45), (118, V(0.5, 0.02, 1.42), EAR1, 52), (140, V(0.45, -0.5, 1.2), CHEST + V(0, 0, 0.02), 40),
    (157, V(0.24, -0.48, 1.08), CHEST + V(0.06, 0, 0.03), 40), (166, V(0.17, -0.33, 1.06), CHEST + V(0.07, 0.05, 0.03), 40), (171, V(0.155, -0.275, 1.06), CHEST + V(0.07, 0.1, 0.03), 40)],
  [  # studio A: out of the membrane, orbit the rib cage, push to the block being lifted
    (172, V(40.03, -0.6, 1.17), P0 + V(-0.04, 0.2, 0.05), 32), (186, V(40.07, -0.52, 1.2), V(40.02, 0, 1.15), 30), (212, V(40.33, -0.47, 1.32), V(40.02, 0, 1.18), 28),
    (240, V(40.12, -0.44, 1.2), P0 + V(0, 0, 0.03), 34), (265, V(39.93, -0.33, 1.06), P0, 45), (300, V(40.0, -0.31, 1.15), P0 + V(0, -0.03, 0.01), 52),
    (328, BLK_SA + V(0.012, -0.1, 0.025), BLK_SA + V(0, 0.01, 0), 55), (342, BLK_SA + V(-0.002, -0.045, 0.01), BLK_SA, 70)],
  [  # OR: out of the block on the tray, orbit the carving hands, follow the ear to the arm, macro on the bump, into the skin
    (343, BLK + V(0.0, -0.012, 0.1), BLK, 70), (362, BLK + V(-0.08, -0.2, 0.16), BLK + V(0, 0, 0.01), 40),
    (400, BLK + V(-0.3, -0.28, 0.28), BLK + V(0, 0.03, 0.03), 34), (440, BLK + V(-0.06, -0.42, 0.34), BLK + V(0, 0.04, 0.04), 34),
    (480, BLK + V(0.28, -0.32, 0.3), BLK + V(0, 0.03, 0.03), 36), (525, BLK + V(0.1, -0.22, 0.26), BLK + V(0, 0.0, 0.0), 42),
    (565, BLK + V(0.25, 0.12, 0.36), BLK + V(-0.08, 0.2, 0.1), 30), (605, V(1.15, -0.25, 1.38), V(0.85, -0.1, 1.08), 32),
    (645, INC + V(0.3, -0.36, 0.26), INC, 34), (685, INC + V(0.17, -0.22, 0.07), INC, 42), (725, INC + V(0.07, -0.14, 0.05), INC, 52),
    (760, INC + V(0.05, -0.12, 0.08), INC, 50), (788, INC + V(0.01, -0.05, 0.065), INC, 58), (803, INC + V(0.0, -0.012, 0.022), INC + V(0, 0, -0.01), 60)],
  [  # studio B: under the skin, orbit the growing ear, back up through the membrane
    (804, SB + V(0.0, -0.01, 0.445), SB + V(0, 0.01, 0.0), 40), (830, SB + V(0.03, -0.08, 0.3), SB + V(0, 0, 0.03), 36),
    (875, SB + V(0.22, -0.24, 0.24), SB + V(0, 0, 0.035), 34), (925, SB + V(0.3, 0.12, 0.2), SB + V(0, 0, 0.035), 36),
    (975, SB + V(0.0, 0.32, 0.22), SB + V(0, 0, 0.035), 36), (1015, SB + V(-0.24, 0.08, 0.16), SB + V(0, 0, 0.035), 40),
    (1050, SB + V(-0.05, -0.05, 0.33), SB + V(0, 0, 0.03), 38), (1062, SB + V(0.0, -0.01, 0.445), SB, 40)],
  [  # OR: out of the arm, over the surgeon's shoulder as the ear is lifted out, fly to the head, macro join, stitches, pull out and orbit to the front
    (1063, INC + V(0.0, -0.012, 0.024), INC + V(0, 0, -0.01), 60), (1078, INC + V(0.04, -0.1, 0.09), INC, 50), (1130, INC + V(0.14, -0.24, 0.13), INC, 40),
    (1180, V(0.98, 0.12, 1.42), INC + V(0, 0, 0.06), 36), (1240, V(0.92, 0.3, 1.5), INC + V(0, 0, 0.18), 36), (1300, V(0.88, 0.22, 1.6), FT, 34),
    (1345, EO(0.6, -0.2, 0.3), EO(0.1, 0, 0.05), 32), (1385, EO(0.4, -0.15, 0.17), EAR_W, 38), (1425, EO(0.26, -0.09, 0.08), EAR_W, 45),
    (1465, EO(0.12, -0.03, 0.03), EAR_W + V(0, 0, -0.005), 55), (1505, EO(0.11, 0.03, 0.04), EAR_W, 55), (1545, EO(0.1, -0.035, 0.0), EAR_W, 55),
    (1585, EO(0.1, 0.0, -0.03), EAR_W, 55), (1625, EO(0.11, 0.04, 0.02), EAR_W, 52), (1650, EO(0.18, 0.02, 0.06), EAR_W, 45),
    (1685, V(0.75, 0.15, 1.5), V(0.05, 0.1, 1.3), 34), (1715, V(0.85, -0.45, 1.46), FACE9, 36), (1745, V(0.5, -0.88, 1.43), FACE9 + V(0.02, 0, -0.02), 40),
    (1770, V(0.4, -0.95, 1.42), FACE9 + V(0.02, 0, -0.02), 41)],
]
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.lens = 30; cam_d.sensor_fit = 'AUTO'; cam_d.clip_start = 0.004; cam_d.clip_end = 60
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 4.0
cam = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(cam); sc.camera = cam
aim = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(aim)
tt = cam.constraints.new('TRACK_TO'); tt.target = aim; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
cam_d.dof.focus_object = aim
JUMPS = []
for seg in SEGS:
    fc = catmull([(f, c) for f, c, a, l in seg]); fa = catmull([(f, a) for f, c, a, l in seg]); fl = catmull([(f, float(l)) for f, c, a, l in seg])
    f0, f1 = seg[0][0], seg[-1][0]
    for f in list(range(f0, f1 + 1, 2)) + [f1]:
        cam.location = fc(f); cam.keyframe_insert("location", frame=f)
        aim.location = fa(f); aim.keyframe_insert("location", frame=f)
        cam_d.lens = fl(f); cam_d.keyframe_insert("lens", frame=f)
    JUMPS.append(f1)
JUMPS = JUMPS[:-1]
def stepped(idb, frames):
    ad = idb.animation_data
    for layer in ad.action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fcv in cb.fcurves:
                    for kp in fcv.keyframe_points:
                        if int(round(kp.co.x)) in frames: kp.interpolation = 'CONSTANT'
for f in range(1, sc.frame_end + 1, 4):
    ev_at(f); dist = (cam.matrix_world.translation - aim.matrix_world.translation).length
    cam_d.dof.aperture_fstop = max(2.8, min(22.0, 2.8 * 0.9 / max(dist, 0.02))); cam_d.dof.keyframe_insert("aperture_fstop", frame=f)
for idb in (cam, aim, cam_d): stepped(idb, set(JUMPS))
# surgical spot follows the working area
for f, tgt in ((1, V(0.05, -0.1, 1.3)), (330, BLK), (600, INC), (1300, INC), (1400, EAR_W), (1640, EAR_W), (1720, FACE9)):
    spot.location = tgt + V(0.25, 0.1, 1.0); spot.rotation_euler = (tgt - spot.location).to_track_quat('-Z', 'Y').to_euler()
    spot.keyframe_insert("location", frame=f); spot.keyframe_insert("rotation_euler", frame=f)
print("JUMPS", JUMPS)
beats = [(1, 1, "Lose an ear in an accident"), (2, 127, "A surgeon takes some cartilage"), (3, 343, "and carves it into the shape"),
         (4, 565, "Then it's slipped into a pocket"), (5, 775, "Inside your arm, it grows"), (6, 1063, "Once it's fully developed"),
         (7, 1309, "The blood vessels are connected"), (8, 1501, "and the skin is carefully stitched"), (9, 1645, "giving you a brand new ear")]
json.dump([dict(beat=b, frame=f, first_words=w_) for b, f, w_ in beats], open(os.path.join(HERE, "..", "beats.json"), "w"), indent=1)
sc.frame_set(1)
print("CAMERA_DONE")
bpy.ops.wm.save_as_mainfile(filepath=out)
