"""Proof sheet + checks for hand_poses.py on a plain MPFB character.
blender -b --python hand_poses_demo.py -- <out_dir>
Writes <out_dir>/hp_*.jpg stills, <out_dir>/hand_poses_report.txt; then run the sheet step at the bottom (PIL, outside Blender)."""
import sys, os, math
import bpy
from mathutils import Vector, Matrix, Quaternion
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[sys.argv.index("--") + 1]; os.makedirs(OUT, exist_ok=True)
from bl_ext.user_default.mpfb.services.humanservice import HumanService
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
info = HumanService._create_default_human_info_dict(); info["name"] = "Model"; info["rig"] = "default"
info["phenotype"] = {"gender": 0.6, "age": 0.5, "muscle": 0.5, "weight": 0.5, "proportions": 0.5, "height": 0.5, "cupsize": 0.5, "firmness": 0.5,
                     "race": {"asian": 0.33, "caucasian": 0.34, "african": 0.33}}
info["eyes"] = "high-poly/high-poly.mhclo"; info["clothes"] = ["male_casualsuit02/male_casualsuit02.mhclo"]
info["skin_mhmat"] = "young_caucasian_male/young_caucasian_male.mhmat"; info["skin_material_type"] = "ENHANCED_SSS"
st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1
HumanService.deserialize_from_dict(info, st)
exec(open(os.path.join(HERE, "anim_lib.py")).read())
exec(open(os.path.join(HERE, "hand_poses.py")).read())
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
make_human_ctrl(rig); add_hand_limits(rig)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = 8; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.render.image_settings.file_format = 'JPEG'
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.75, 0.95, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.8
for nm, loc, e in (("Key", (1.0, -2.0, 2.2), 300), ("Fill", (-1.5, -1.2, 1.5), 120)):
    ld = bpy.data.lights.new(nm, 'AREA'); ld.energy = e; ld.size = 1.5; L = bpy.data.objects.new(nm, ld); sc.collection.objects.link(L)
    L.location = loc; L.rotation_euler = (Vector((0, 0, 1.2)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
cd = bpy.data.cameras.new("Cam"); cd.lens = 50; cam = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(cam); sc.camera = cam; cd.clip_start = 0.01
HP = {"L": Vector((0.24, -0.32, 1.22)), "R": Vector((-0.24, -0.32, 1.22))}   # MPFB faces -Y; his left is +X
POSE_NAMES = list(POSES)
REPORT = []
def shoot(tag, s, hand, thumbside=False):
    out = []
    views = [("front", Vector((0.0, -0.40, 0.10))), ("side", Vector((0.38 if s == "L" else -0.38, -0.08, 0.02)))]
    if thumbside: views.append(("thumbside", Vector((-0.30 if s == "L" else 0.30, -0.2, 0.12))))
    for view, off in views:
        cam.location = hand + off; cam.rotation_euler = (hand - cam.location).to_track_quat('-Z', 'Y').to_euler()
        fn = os.path.join(OUT, "hp_%s_%s_%s.jpg" % (tag, s, view)); sc.render.filepath = fn; bpy.ops.render.render(write_still=True); out.append(fn)
    return out
def local_e(pb):
    b = pb.bone; rr = b.parent.matrix_local.inverted() @ b.matrix_local
    return ((pb.parent.matrix @ rr).inverted() @ pb.matrix).to_euler('XYZ')
def check(tag, s):
    bad = []; PB = rig.pose.bones
    for k in (2, 3, 4, 5):
        for j in (1, 2, 3):
            e = local_e(PB["finger%d-%d.%s" % (k, j, s)])
            if math.degrees(e.x) < -1.0 or math.degrees(e.x) > 91 or abs(math.degrees(e.z)) > 10.5: bad.append(("f%d-%d" % (k, j), round(math.degrees(e.x)), round(math.degrees(e.z))))
    tips = [rig.matrix_world @ PB["finger%d-3.%s" % (k, s)].tail for k in (2, 3, 4, 5)]
    gaps = [round((tips[i] - tips[i + 1]).length * 1000) for i in range(3)]
    th = rig.matrix_world @ PB["finger1-3.%s" % s].tail; it = rig.matrix_world @ PB["finger2-3.%s" % s].tail
    REPORT.append("%-17s %s  joint violations: %-3d  adjacent fingertip gaps mm: %s  thumb-to-index-tip mm: %d" % (tag, s, len(bad), gaps, round((th - it).length * 1000)))
    if bad: REPORT.append("     " + str(bad))
# ---- every pose, both hands
for i, name in enumerate(POSE_NAMES):
    f = 1 + i * 10
    for s in "LR":
        place_hand(rig, s, f, HP[s], Vector((0, 0, -1)), Vector((0, -1, 0)))   # palm down, fingers forward (natural, inside wrist limits)
    sc.frame_set(f)
    for s in "LR": apply_pose(rig, s, name, f)
    sc.frame_set(f)
    for s in "LR":
        check(name, s); shoot("%02d_%s" % (i, name), s, HP[s] + Vector((0, -0.06, -0.01)))
# ---- grip_object demos (right hand): cylinder, box edge, sheet of paper
def obj_mat(o, col):
    m = bpy.data.materials.new(o.name + "_m"); m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (*col, 1); o.data.materials.append(m)
demos = []
# horizontal bar (wrap from above), box top-front edge (fingers over the edge), sheet lying flat (pinch its near edge)
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.018, depth=0.3, location=(-0.24, -0.40, 1.20), rotation=(0, math.radians(90), 0))
cyl = bpy.context.active_object; cyl.name = "Demo_Cylinder"; obj_mat(cyl, (0.8, 0.3, 0.1)); demos.append((cyl, Vector((-0.24, -0.40, 1.218)), Vector((0, 0, -1))))
bpy.ops.mesh.primitive_cube_add(size=0.14, location=(-0.24, -0.47, 1.13)); box = bpy.context.active_object; box.name = "Demo_Box"; obj_mat(box, (0.2, 0.5, 0.8))
demos.append((box, Vector((-0.24, -0.505, 1.20)), Vector((0, 0, -1))))
bpy.ops.mesh.primitive_plane_add(size=1, location=(-0.24, -0.55, 1.20)); pap = bpy.context.active_object; pap.name = "Demo_Paper"
pap.scale = (0.21, 0.297, 1); bpy.ops.object.transform_apply(scale=True)
pap.modifiers.new("t", 'SOLIDIFY').thickness = 0.0006; obj_mat(pap, (0.95, 0.93, 0.85))
demos.append((pap, Vector((-0.24, -0.55 + 0.1485, 1.20)), Vector((0, -1, 0))))
for o, *_ in demos: o.hide_render = True; o.hide_viewport = True
for gi, (o, cp, ad) in enumerate(demos):
    f = 200 + gi * 10
    for x in demos: x[0].hide_render = x[0].hide_viewport = (x[0] is not o)
    bpy.context.view_layer.update()
    place_hand(rig, "L", f, HP["L"], Vector((0, 1, 0)), Vector((0, 0, 1))); apply_pose(rig, "L", "relaxed", f)
    rep = grip_object(rig, "R", f, o, cp, ad)
    sc.frame_set(f); check("grip_" + o.name[5:], "R")
    REPORT.append("     grip contacts (closing fraction at first touch, per finger tip bone): %s" % rep)
    pts = []
    dg = bpy.context.evaluated_depsgraph_get()
    for k in (1, 2, 3, 4, 5):
        t = rig.matrix_world @ rig.pose.bones["finger%d-3.R" % k].tail; pts.append(round(_dist_to(o, t) * 1000))
    REPORT.append("     fingertip-bone end distance to surface mm (thumb..little): %s" % pts)
    shoot("g%d_%s" % (gi, o.name[5:]), "R", cp + Vector((0, 0.02, 0.01)), thumbside=True)
open(os.path.join(OUT, "hand_poses_report.txt"), "w").write("\n".join(REPORT) + "\n"); print("\n".join(REPORT))
import subprocess
SHEET = r'''
import sys, glob, os
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; W, H = 270, 480
rows = []
for f in sorted(glob.glob(os.path.join(d, "hp_[0-9][0-9]_*_L_front.jpg"))):
    stem = f[:-len("_L_front.jpg")]; name = os.path.basename(stem)[6:]
    rows.append((name, [stem + "_L_front.jpg", stem + "_L_side.jpg", stem + "_R_front.jpg", stem + "_R_side.jpg"], ["L front", "L side", "R front", "R side"]))
for f in sorted(glob.glob(os.path.join(d, "hp_g*_R_front.jpg"))):
    stem = f[:-len("_R_front.jpg")]; name = "grip_object: " + os.path.basename(stem)[6:]
    rows.append((name, [stem + "_R_front.jpg", stem + "_R_side.jpg", stem + "_R_thumbside.jpg"], ["R front", "R outside", "R thumb side"]))
S = Image.new("RGB", (W * 4, (H + 22) * len(rows)), (30, 30, 30)); dr = ImageDraw.Draw(S)
for r, (name, fs, labs) in enumerate(rows):
    y = r * (H + 22); dr.text((6, y + 5), name, fill=(255, 230, 80))
    for c, (fn, lab) in enumerate(zip(fs, labs)):
        S.paste(Image.open(fn), (c * W, y + 22)); dr.rectangle((c * W, y + 22, c * W + 70, y + 36), fill=(0, 0, 0)); dr.text((c * W + 3, y + 23), lab, fill=(255, 255, 255))
S.save(out, quality=86); print("SHEET", out, S.size)
'''
subprocess.run(["python3", "-I", "-c", SHEET, OUT, os.path.join(HERE, "hand_poses_sheet.jpg")])
print("DEMO_DONE")
