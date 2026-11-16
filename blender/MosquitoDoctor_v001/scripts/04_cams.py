"""B22 cameras: one camera per shot, bound by timeline markers (hard cuts). Each camera tracks a keyed aim empty
(Track To, world up = level horizon) and moves on a smooth 2-key path (slow push/orbit). Macros f/8 focused on the aim.
Also: ward logo crate decal, catchlight per camera, a few staging fixes. blender -b anim.blend --python 04_cams.py -- out.blend"""
import bpy, sys, os, math
from mathutils import Vector, Matrix
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; D = bpy.data.objects; V = Vector
def bw(n, b, f):
    sc.frame_set(f); return D[n].matrix_world @ D[n].pose.bones[b].head
def headc(n, f):
    sc.frame_set(f); pb = D[n].pose.bones["head"]; return D[n].matrix_world @ (pb.head * 0.45 + pb.tail * 0.55)
def eyes(n, f):
    sc.frame_set(f); return D[n].matrix_world @ ((D[n].pose.bones["eye.L"].head + D[n].pose.bones["eye.R"].head) / 2)
def obj(n, f): sc.frame_set(f); return D[n].matrix_world.translation.copy()
def mq(f): return obj("Mosquito", f)
def vialmid(f): sc.frame_set(f); return D["Vial"].matrix_world @ V((0, 0, 0.0375))
def fixed(p): return lambda f: V(p)
def mix(a, b, t): return lambda f: a(f).lerp(b(f), t)
def add(a, o): return lambda f: a(f) + V(o)
# (name, f0, f1, aim_fn, cam_start, cam_end, lens, macro, relative)  relative: cam = aim + offset
SH = [
 ("S01", 1, 100, mq, (0.065, -0.05, 0.03), (0.045, -0.035, 0.022), 50, True, True),
 ("S02", 101, 240, lambda f: headc("Boy", f), (0.48, 0.42, 0.42), (0.40, 0.35, 0.36), 40, False, True),
 ("S03", 241, 340, add(mq, (0, 0, 0.002)), (0.075, -0.012, 0.012), (0.065, 0.006, 0.012), 70, True, True),
 ("S04", 341, 440, add(mq, (0, 0, 0.002)), (0.035, 0.055, 0.03), (0.050, 0.035, 0.026), 60, True, True),
 ("S05", 441, 560, mix(lambda f: headc("Doctor", f), vialmid, 0.35), (-0.55, -0.32, -0.08), (-0.47, -0.26, -0.07), 35, False, True),
 ("S06", 561, 710, add(lambda f: obj("Mosquito", 600), (0, 0, 0.035)), (0.03, 0.24, 0.03), (0.03, 0.20, 0.028), 70, True, True),
 ("S07", 711, 830, fixed((1.47, 1.82, 0.98)), (1.02, 1.0, 1.38), (1.08, 1.12, 1.33), 30, False, False),
 ("S08", 831, 950, add(mq, (0, 0, 0.004)), (-0.025, -0.11, 0.05), (-0.015, -0.09, 0.044), 50, True, True),
 ("S09", 951, 1110, fixed((-1.4, 0.8, 0.78)), (0.0, 0.25, 1.55), (-0.05, 0.40, 1.50), 30, False, False),
 ("S10", 1111, 1280, fixed((1.42, 1.85, 0.98)), (1.28, 0.95, 1.36), (1.34, 1.07, 1.31), 32, False, False),
 ("S11", 1281, 1490, mix(vialmid, lambda f: eyes("Doctor", f), 0.45), (0.05, -0.42, -0.02), (0.04, -0.35, -0.02), 40, False, True),
 ("S12", 1491, 1610, lambda f: obj("BiteBump", f), (0.06, -0.24, 0.13), (0.05, -0.20, 0.11), 40, True, True),
 ("S13", 1611, 1730, fixed((1.42, 1.85, 0.98)), (0.52, 1.50, 1.24), (0.60, 1.58, 1.21), 30, False, False),
 ("S14", 1731, 1850, fixed((1.40, 2.0, 1.02)), (1.40, 0.92, 1.26), (1.40, 1.05, 1.22), 30, False, False),
 ("S15", 1851, 1940, lambda f: headc("Doctor", f), (0.06, -0.58, 0.0), (0.05, -0.47, 0.0), 50, False, True),
 ("S16", 1941, 2030, lambda f: eyes("Doctor", f), (0.02, -0.32, 0.02), (0.0, -0.25, 0.015), 50, True, True),
 ("S17", 2031, 2150, fixed((1.05, 2.20, 0.92)), (0.45, 1.90, 0.60), (0.50, 1.95, 0.58), 24, False, False),
 ("S18", 2151, 2270, fixed((0.75, 2.28, 0.08)), (0.0, 1.72, 0.58), (0.08, 1.80, 0.50), 30, False, False),
 ("S19", 2271, 2390, fixed((0.1, 2.15, 1.22)), (0.1, 0.75, 1.36), (0.1, 1.00, 1.31), 30, False, False),
 ("S20", 2391, 2510, fixed((0.1, 2.15, 1.17)), (0.1, 1.50, 1.24), (0.1, 1.64, 1.20), 35, False, False),
 ("S21", 2511, 2620, lambda f: headc("Doctor", f), (0.50, 0.40, 0.42), (0.42, 0.34, 0.36), 40, False, True),
 ("S22", 2621, 2710, fixed((1.45, 1.70, 0.82)), (0.98, 0.68, 1.30), (1.08, 0.84, 1.25), 26, False, False),
 ("S23", 2711, 2830, fixed((1.65, 2.0, 1.22)), (1.50, 0.70, 1.50), (1.56, 0.88, 1.45), 26, False, False),
 ("S24", 2831, 2950, fixed((1.18, 1.95, 1.12)), (1.02, 1.08, 0.96), (1.04, 1.16, 0.94), 30, False, False),
 ("S25", 2951, 3070, fixed((40.0, 6.0, 0.9)), (40.0, -7.6, 1.5), (40.0, -5.6, 1.45), 24, False, False),
 ("S26", 3071, 3190, lambda f: headc("Boy", f), (-0.60, -0.30, 0.45), (-0.50, -0.25, 0.38), 40, False, True),
]
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
for c in [o for o in D if o.name.startswith(("CAM_", "AIM_", "CATCH_"))]: bpy.data.objects.remove(c, do_unlink=True)
def smooth(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)
for name, f0, f1, aim, c0, c1, lens, macro, rel in SH:
    a = bpy.data.objects.new("AIM_" + name, None); sc.collection.objects.link(a); a.empty_display_size = 0.02
    cam = bpy.data.objects.new("CAM_" + name, bpy.data.cameras.new("CAM_" + name)); sc.collection.objects.link(cam)
    cam.data.lens = lens; cam.data.clip_start = 0.005 if macro else 0.05; cam.data.sensor_width = 36
    steps = list(range(f0, f1 + 1, 10)) + ([f1] if (f1 - f0) % 10 else [])
    A0 = aim(f0)
    for f in steps:
        p = aim(f)
        a.location = p; a.keyframe_insert("location", frame=f)
        t = smooth((f - f0) / (f1 - f0))
        off = V(c0).lerp(V(c1), t)
        cam.location = ((p if rel else V((0, 0, 0))) + off) if rel else off
        if rel: cam.location = A0.lerp(p, 0.85) + off      # follow the subject, damped
        cam.keyframe_insert("location", frame=f)
    tt = cam.constraints.new('TRACK_TO'); tt.target = a; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'; tt.use_target_z = True
    cam.data.dof.use_dof = macro
    if macro: cam.data.dof.focus_object = a; cam.data.dof.aperture_fstop = 8.0
    # catchlight: tiny point light near the lens, seen only in glossy reflections (eyes)
    L = bpy.data.objects.new("CATCH_" + name, bpy.data.lights.new("CATCH_" + name, 'POINT')); sc.collection.objects.link(L)
    L.data.energy = 1.5 if not macro else 0.3; L.data.shadow_soft_size = 0.02; L.parent = cam; L.location = (0.08, 0.10, 0)
    L.visible_diffuse = False; L.visible_transmission = False; L.visible_volume_scatter = False; L.visible_camera = False
    mk = sc.timeline_markers.new(name, frame=f0); mk.camera = cam
sc.camera = D["CAM_S01"]
# ward net of the recovered boy's bed is tied up (hidden) so S26 sees him clearly; logo crate near the ward entrance
n = D.get("Net_-1_1")
if n: n.hide_render = True; n.hide_viewport = True
cp = D["CrateWard_pivot"]; cp.location = V((40.95, -6.2, 0)); cp.rotation_euler = (0, 0, math.radians(-15))
bpy.context.view_layer.update()
img = bpy.data.images.load("/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_dark.png"); img.pack()
ml = bpy.data.materials.new("LogoDecal"); ml.use_nodes = True; nt = ml.node_tree; P = nt.nodes["Principled BSDF"]
tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img; nt.links.new(tx.outputs["Color"], P.inputs["Base Color"]); nt.links.new(tx.outputs["Alpha"], P.inputs["Alpha"])
P.inputs["Roughness"].default_value = 0.7
cm = [o for o in cp.children_recursive if o.type == 'MESH']
pts = [o.matrix_world @ V(c) for o in cm for c in o.bound_box]
lo = V([min(p[i] for p in pts) for i in range(3)]); hi = V([max(p[i] for p in pts) for i in range(3)])
bpy.ops.mesh.primitive_plane_add(size=1); dec = bpy.context.object; dec.name = "LogoWard"
w = 0.42; dec.scale = (w, w * 414 / 967, 1); dec.data.materials.append(ml)
# front face of the crate (toward -y in the crate's frame)
dec.parent = cp; dec.matrix_parent_inverse = Matrix.Identity(4)
loc_local = cp.matrix_world.inverted() @ V(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, (lo.z + hi.z) / 2))
# put it on the crate's local -y face
ext = [cp.matrix_world.inverted() @ p for p in pts]; ymin = min(p.y for p in ext); zc = (min(p.z for p in ext) + max(p.z for p in ext)) / 2
xc = (min(p.x for p in ext) + max(p.x for p in ext)) / 2
dec.location = V((xc, ymin - 0.004, zc)); dec.rotation_euler = (math.radians(90), 0, 0)
print("LOGO crate size", [round(x, 2) for x in hi - lo])
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("CAMS", len(SH))
