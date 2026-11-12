"""270x480 close-ups of every hand action. blender -b anim.blend --python 05c_hand_closeups.py -- <out_dir>"""
import sys, os, bpy
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1:][0]; os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.image_settings.file_format = 'JPEG'
cd = bpy.data.cameras.new("HandCam"); cam = bpy.data.objects.new("HandCam", cd); sc.collection.objects.link(cam); cd.lens = 40; cd.clip_start = 0.01
sc.camera = cam
SHOTS = [("Fan", 1.0, "hands_on_boards", "R"), ("Fan", 10.3, "hand_to_mouth", "L"), ("Fan", 14.0, "typing", "R"), ("Fan", 16.3, "slap", "R"),
         ("Fan", 16.8, "knock", "L"), ("Manager", 20.3, "shrug", "R"), ("Doctor", 23.5, "dermatoscope", "R"), ("Doctor", 27.0, "forceps", "R"),
         ("Doctor", 28.1, "bandage", "L"), ("ManagerB", 31.0, "phone", "R"), ("Fan", 36.6, "home_mouth", "R"), ("Fan", 40.0, "cheque", "R"), ("Manager", 40.0, "clap", "R")]
for n, t, lab, hs in SHOTS:
    f = 1 + round(t * 60); sc.frame_set(f); r = bpy.data.objects[n]
    wl = r.matrix_world @ r.pose.bones["wrist.L"].head; wr = r.matrix_world @ r.pose.bones["wrist.R"].head
    head = r.matrix_world @ r.pose.bones["head"].head; root = r.matrix_world @ r.pose.bones["root"].head
    tgt = r.matrix_world @ r.pose.bones[f"finger3-1.{hs}"].head
    fwd = (head - root); fwd.z = 0
    spine = r.pose.bones["spine03"]; M = r.matrix_world @ spine.matrix
    face_dir = (M.to_3x3() @ Vector((0, 0, 1)))
    face_dir.z = 0
    if face_dir.length < 1e-3: face_dir = Vector((0, -1, 0))
    face_dir.normalize()
    cam.location = tgt + face_dir * 0.42 + Vector((0.0, 0, 0.14))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd.dof.use_dof = False
    sc.render.filepath = os.path.join(out, f"{t:05.1f}_{n}_{lab}.jpg"); bpy.ops.render.render(write_still=True)
print("CLOSEUPS_DONE")
