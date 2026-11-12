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

# ================================================================== x-ray beat (5): inside the real forearm, vessels grow over the ear, skin creeps across
for o in bpy.data.collections["Studio_Tissue"].objects: o.hide_render = True; o.hide_viewport = True
earB = OB["Ear_InArm"]
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
# vessels in the ear's local space, parented to it (it rides in the pocket)
Mw = Matrix.Identity(4)
verts = [Vector(v.co) for v in earB.data.vertices]; polys = [tuple(p.vertices) for p in earB.data.polygons]
bvh = BVHTree.FromPolygons(verts, polys)
ctr = sum(verts, Vector()) / len(verts)
M_VES = newmat("SB_Vessel", (0.3, 0.006, 0.014), 0.18, sss=0.3, emit=((0.9, 0.05, 0.05), 0.3), coat=1.0)
M_VES.node_tree.nodes["Principled BSDF"].inputs["Coat Roughness"].default_value = 0.05
ves_em = M_VES.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f in range(775, 1063, 30):
    ves_em.default_value = 0.9 if (f // 30) % 2 else 0.2; ves_em.keyframe_insert("default_value", frame=f)
def grow(pts, r0, f0, dur, name):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r0; cu.bevel_resolution = 3
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for k, q in enumerate(pts): sp.points[k].co = (*q, 1); sp.points[k].radius = 1.0 - 0.75 * k / max(1, len(pts) - 1)
    cu.materials.append(M_VES); o = bpy.data.objects.new(name, cu); bpy.data.collections["Props"].objects.link(o); o.parent = earB; o.matrix_parent_inverse = Matrix.Identity(4)
    o.hide_render = True; o.keyframe_insert("hide_render", frame=1); o.hide_render = False; o.keyframe_insert("hide_render", frame=800); o.hide_render = True; o.keyframe_insert("hide_render", frame=1150)
    cu.bevel_factor_mapping_end = 'SPLINE'
    cu.bevel_factor_end = 0.0; cu.keyframe_insert("bevel_factor_end", frame=f0); cu.bevel_factor_end = 1.0; cu.keyframe_insert("bevel_factor_end", frame=f0 + dur)
    return o
def walk_surf(start, d, n, step, wob):
    p, nrm, _, _ = bvh.find_nearest(start)
    if p is None: return []
    pts = [p + nrm * 0.0008]
    for k in range(n):
        q = pts[-1] + d * step; q, n2, _, _ = bvh.find_nearest(q)
        if q is None: break
        pts.append(q + n2 * 0.0008); d = (d + V(random.uniform(-wob, wob), 0, random.uniform(-wob, wob))).normalized()
    return pts
# trunks enter from the ear's rim (where the pocket's blood supply comes in) and branch twice
nv = 0
for i in range(9):
    a = i / 9 * 2 * math.pi
    start = ctr + V(0.024 * math.cos(a), -0.008, 0.034 * math.sin(a))
    d0 = (ctr - start); d0.y = 0; d0.normalize()
    trunk = walk_surf(start, d0, 16, 0.0028, 0.35)
    if len(trunk) < 4: continue
    f0 = 828 + i * 7; grow(trunk, 0.0013, f0, 80, "SB_Vessel%d" % nv); nv += 1
    for b in range(3):
        k = random.randint(3, len(trunk) - 2); dd = (trunk[k] - trunk[k - 1]).normalized()
        side = V(-dd.z, 0, dd.x) * random.choice((-1, 1))
        br = walk_surf(trunk[k], (dd + side).normalized(), 8, 0.0022, 0.5)
        if len(br) > 3:
            fb = f0 + int(80 * k / len(trunk)); grow(br, 0.0008, fb, 60, "SB_Vessel%d" % nv); nv += 1
            k2 = random.randint(2, len(br) - 2); d2 = (br[k2] - br[k2 - 1]).normalized()
            tw = walk_surf(br[k2], (d2 + V(-d2.z, 0, d2.x) * random.choice((-1, 1))).normalized(), 5, 0.0018, 0.6)
            if len(tw) > 2: grow(tw, 0.0005, fb + int(60 * k2 / len(br)), 40, "SB_Vessel%d" % nv); nv += 1
print("ARM_VESSELS", nv)


# the forearm skin itself goes glassy around the pocket (x-ray), keyed 790-815 on, 1040-1066 off
def xray(name, parent, r0, r1, keys, objs, static=None):
    xr = bpy.data.objects.new(name, None); bpy.data.collections["Props"].objects.link(xr); xr.parent = parent; xr.location = (0, 0, 0)
    bpy.context.view_layer.update(); ps_ = parent.matrix_world.to_scale().x; xr.scale = (1 / ps_,) * 3   # object coords in metres
    for ob_ in objs:
        for m in ob_.data.materials:
            nt_ = m.node_tree; outn = next(n for n in nt_.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
            src = outn.inputs["Surface"].links[0].from_socket
            ln = nt_.nodes.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'
            if static is None:
                tcx = nt_.nodes.new("ShaderNodeTexCoord"); tcx.object = xr; nt_.links.new(tcx.outputs["Object"], ln.inputs[0])
            else:   # world-space centre (the chest does not move while it is x-rayed)
                geo = nt_.nodes.new("ShaderNodeNewGeometry"); sub = nt_.nodes.new("ShaderNodeVectorMath"); sub.operation = 'SUBTRACT'
                sub.inputs[1].default_value = static; nt_.links.new(geo.outputs["Position"], sub.inputs[0]); nt_.links.new(sub.outputs[0], ln.inputs[0])
            mr_ = nt_.nodes.new("ShaderNodeMapRange"); mr_.inputs["From Min"].default_value = r0; mr_.inputs["From Max"].default_value = r1
            mr_.inputs["To Min"].default_value = 1.0; mr_.inputs["To Max"].default_value = 0.0; nt_.links.new(ln.outputs["Value"], mr_.inputs["Value"])
            amt = nt_.nodes.new("ShaderNodeMath"); amt.operation = 'MULTIPLY'; nt_.links.new(mr_.outputs["Result"], amt.inputs[0])
            for f, v in keys:
                amt.inputs[1].default_value = v; amt.inputs[1].keyframe_insert("default_value", frame=f)
            gl_ = nt_.nodes.new("ShaderNodeBsdfGlass"); gl_.inputs["Color"].default_value = (0.95, 0.8, 0.75, 1); gl_.inputs["Roughness"].default_value = 0.15
            em_ = nt_.nodes.new("ShaderNodeEmission"); em_.inputs["Color"].default_value = (0.4, 0.75, 1.0, 1); em_.inputs["Strength"].default_value = 0.4
            ad_ = nt_.nodes.new("ShaderNodeAddShader"); nt_.links.new(gl_.outputs[0], ad_.inputs[0]); nt_.links.new(em_.outputs[0], ad_.inputs[1])
            tr_ = nt_.nodes.new("ShaderNodeBsdfTransparent")
            mx2 = nt_.nodes.new("ShaderNodeMixShader"); mx2.inputs[0].default_value = 0.2; nt_.links.new(tr_.outputs[0], mx2.inputs[1]); nt_.links.new(ad_.outputs[0], mx2.inputs[2])
            mx_ = nt_.nodes.new("ShaderNodeMixShader"); nt_.links.new(amt.outputs[0], mx_.inputs[0]); nt_.links.new(src, mx_.inputs[1]); nt_.links.new(mx2.outputs[0], mx_.inputs[2])
            nt_.links.new(mx_.outputs[0], outn.inputs["Surface"])
xray("Xray_Center", OB["Arm_Pocket"], 0.03, 0.055, ((1, 0.0), (790, 0.0), (815, 0.95), (1040, 0.95), (1066, 0.0)), [OB["Patient.body"]])
# chest x-ray (beat 2): body and tee go glassy over the rib cage while the cartilage is harvested
xray("Xray_Chest", OB["Chest_Thorax"], 5.0, 6.0, ((1, 0.0), (140, 0.0), (165, 0.92), (322, 0.92), (346, 0.0)), [OB["Patient.male_casualsuit06"]])   # the whole tee turns x-ray glass
# heartbeat pulse of the glow on the patch
# ================================================================== world + OR lights + render settings
w = bpy.data.worlds.get("World") or bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
env = w.node_tree.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(HERE, "..", "assets", "hdri", "surgery_2k.hdr"))
bg = w.node_tree.nodes["Background"]; w.node_tree.links.new(env.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 0.3
for i, (loc, en, sz, col) in enumerate(((V(0.3, 0.2, 2.3), 260, 0.7, (1, 0.98, 0.95)), (V(1.6, -1.8, 2.4), 300, 1.5, (1, 0.96, 0.9)),
                                       (V(-1.5, 1.2, 2.2), 60, 1.2, (0.85, 0.92, 1.0)), (V(-0.8, 2.2, 1.9), 180, 0.5, (0.8, 0.9, 1.0)))):
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
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = -2.5
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
ev_at(200); PC = OB["Chest_Piece"].matrix_world.translation.copy(); BLK_SA = PC; ev_at(1)
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
  [  # OR, one continuous move: beat 1 shock -> x-ray of the chest (beat 2) -> follow the cartilage to the tray -> carving ...
    (1, V(1.55, -0.2, 1.45), FACE1 + V(0, 0, -0.1), 26), (30, V(1.25, -0.12, 1.5), FACE1, 32), (60, V(0.2, -0.95, 1.4), FACE1, 40),
    (90, V(0.75, -0.12, 1.45), EAR1, 45), (118, V(0.6, 0.05, 1.4), EAR1, 48), (145, V(0.15, -0.75, 1.25), PC + V(0, 0, 0.06), 38),
    (175, V(-0.05, -0.62, 1.12), PC + V(0, 0, 0.02), 42), (205, V(-0.22, -0.5, 1.08), PC, 45), (235, V(-0.18, -0.5, 1.2), PC, 50),
    (262, V(-0.12, -0.62, 1.28), PC + V(0.02, -0.03, 0.03), 44), (292, V(-0.05, -1.05, 1.5), PC.lerp(BLK, 0.4) + V(0, 0, 0.1), 34),
    (322, V(0.65, -1.4, 1.45), BLK + V(0, 0, 0.02), 38),
    (362, BLK + V(-0.08, -0.2, 0.16), BLK + V(0, 0, 0.01), 40),
    (400, BLK + V(-0.3, -0.28, 0.28), BLK + V(0, 0.03, 0.03), 34), (440, BLK + V(-0.34, -0.3, 0.3), BLK + V(0, 0.03, 0.03), 34),
    (480, BLK + V(0.02, -0.42, 0.36), BLK + V(0, 0.02, 0.0), 38), (525, BLK + V(0.12, -0.4, 0.32), BLK + V(0, 0.0, 0.0), 40),
    (565, BLK + V(0.2, -0.45, 0.42), BLK + V(-0.02, 0.02, 0.03), 36), (605, V(1.55, -0.35, 1.7), V(0.85, -0.1, 1.08), 30),
    (645, INC + V(0.3, -0.36, 0.26), INC, 34), (685, INC + V(0.17, -0.22, 0.37), INC, 40), (725, INC + V(0.07, -0.16, 0.33), INC, 48),
    (760, INC + V(0.05, -0.14, 0.32), INC, 50), (795, INC + V(0.02, -0.1, 0.24), INC, 58),
    # x-ray: the skin turns glassy and the camera orbits the ear growing inside the forearm
    (830, INC + V(0.07, -0.11, 0.1), INC + V(0, 0, -0.006), 70), (870, INC + V(0.16, -0.06, 0.09), INC + V(0, 0, -0.006), 70),
    (910, INC + V(0.13, 0.0, 0.16), INC + V(0, 0, -0.006), 65), (950, INC + V(0.0, -0.03, 0.19), INC + V(0, 0, -0.006), 65),
    (990, INC + V(-0.1, -0.07, 0.3), INC + V(0, 0, -0.006), 65), (1030, INC + V(-0.05, -0.12, 0.33), INC + V(0, 0, -0.006), 65),
    (1071, INC + V(0.04, -0.1, 0.36), INC, 48), (1130, INC + V(0.14, -0.24, 0.4), INC, 40),
    (1180, V(0.98, 0.12, 1.42), INC + V(0, 0, 0.06), 36), (1240, V(0.92, 0.3, 1.5), INC + V(0, 0, 0.18), 36), (1300, V(0.88, 0.22, 1.6), FT, 34),
    (1345, EO(0.6, -0.2, 0.3), EO(0.1, 0, 0.05), 32), (1385, EO(0.4, -0.15, 0.17), EAR_W, 38), (1425, EO(0.26, -0.09, 0.08), EAR_W, 45),
    (1465, EO(0.17, -0.03, 0.03), EAR_W + V(0, 0, -0.005), 75), (1505, EO(0.16, 0.03, 0.04), EAR_W, 75), (1545, EO(0.16, -0.04, 0.0), EAR_W, 75),
    (1585, EO(0.16, 0.0, -0.03), EAR_W, 75), (1625, EO(0.16, 0.04, 0.02), EAR_W, 70), (1650, EO(0.18, 0.02, 0.06), EAR_W, 45),
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
cuT = bpy.data.curves.new("Suture_Thread", 'CURVE'); cuT.dimensions = '3D'; cuT.bevel_depth = 0.00025; cuT.bevel_resolution = 2
spT = cuT.splines.new('POLY'); spT.points.add(3); cuT.materials.append(bpy.data.materials["Suture"])
thr_o = bpy.data.objects.new("Suture_Thread", cuT); bpy.data.collections["Props"].objects.link(thr_o)
thr_o.hide_render = True; thr_o.keyframe_insert("hide_render", frame=1); thr_o.hide_render = False; thr_o.keyframe_insert("hide_render", frame=1506)
thr_o.hide_render = True; thr_o.keyframe_insert("hide_render", frame=1650)
for f in range(1506, 1651, 2):
    ev_at(f); nd_ = OB["Needle"].matrix_world.translation.copy()
    i_ = max(0, min(8, (f - 1510) // 15)); st_ = OB["Stitch%d" % i_].matrix_world.translation.copy()
    tug = 1.0 - min(1.0, ((f - 1510) % 15) / 8.0)   # slack right after a stitch, then pulled taut
    mid = nd_.lerp(st_, 0.5) - V(0, 0, 0.006 * tug)
    for k_, q in enumerate((st_, st_.lerp(mid, 0.6), mid, nd_)):
        spT.points[k_].co = (*q, 1); spT.points[k_].keyframe_insert("co", frame=f)
beats = [(1, 1, "Lose an ear in an accident"), (2, 127, "A surgeon takes some cartilage"), (3, 343, "and carves it into the shape"),
         (4, 565, "Then it's slipped into a pocket"), (5, 775, "Inside your arm, it grows"), (6, 1063, "Once it's fully developed"),
         (7, 1309, "The blood vessels are connected"), (8, 1501, "and the skin is carefully stitched"), (9, 1645, "giving you a brand new ear")]
json.dump([dict(beat=b, frame=f, first_words=w_) for b, f, w_ in beats], open(os.path.join(HERE, "..", "beats.json"), "w"), indent=1)
sc.frame_set(1)
for c_ in ("Studio_Ribs", "Studio_Tissue"):
    for o in list(bpy.data.collections[c_].objects): bpy.data.objects.remove(o, do_unlink=True)
print("CAMERA_DONE")
bpy.ops.wm.save_as_mainfile(filepath=out)
