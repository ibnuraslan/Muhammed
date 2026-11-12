"""270x480 close-ups of every hand action. blender -b anim.blend --python 05c_hand_closeups.py -- <out_dir>"""
import sys, os, bpy
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1:][0]; os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.image_settings.file_format = 'JPEG'
cd = bpy.data.cameras.new("HandCam"); cam = bpy.data.objects.new("HandCam", cd); sc.collection.objects.link(cam); cd.lens = 40; cd.clip_start = 0.01
sc.camera = cam
SHOTS = [("Fan", 1.0, "hands_on_boards", "R"), ("Fan", 10.3, "hand_to_mouth", "L"), ("Fan", 14.0, "typing", "R"), ("Fan", 16.3, "slap", "R"),
         ("Fan", 16.8, "knock", "L"), ("Manager", 20.3, "shrug", "L"), ("Doctor", 23.5, "dermatoscope", "R"), ("Doctor", 24.6, "scope_at_neck", "L"), ("Doctor", 27.0, "forceps", "R"),
         ("Doctor", 28.1, "bandage", "L"), ("ManagerB", 31.0, "phone", "R"), ("Fan", 36.6, "home_mouth", "R"), ("Fan", 40.0, "cheque", "R"), ("Manager", 40.0, "clap", "R")]
for n, t, lab, hs in SHOTS:
    f = 1 + round(t * 60); sc.frame_set(f); r = bpy.data.objects[n]
    wl = r.matrix_world @ r.pose.bones["wrist.L"].head; wr = r.matrix_world @ r.pose.bones["wrist.R"].head
    head = r.matrix_world @ r.pose.bones["head"].head; root = r.matrix_world @ r.pose.bones["root"].head
    tgt = r.matrix_world @ r.pose.bones[f"finger3-1.{hs}"].head
    fwd = (head - root); fwd.z = 0
    spine = r.pose.bones["spine03"]; M = r.matrix_world @ spine.matrix
    fwd = (M.to_3x3() @ Vector((0, 0, 1))); fwd.z = 0; fwd.normalize()
    side = Vector((-fwd.y, fwd.x, 0))
    dg = bpy.context.evaluated_depsgraph_get(); best = None
    PREF = {"cheque": [side * 0.40 + fwd * 0.15 + Vector((0, 0, 0.05)), -side * 0.40 + fwd * 0.15 + Vector((0, 0, 0.05))], "shrug": [fwd * 0.55 + side * 0.25 + Vector((0, 0, 0.10)), -fwd * 0.45 + side * 0.30 + Vector((0, 0, 0.2))], "dermatoscope": [side * 0.45 + fwd * 0.25 + Vector((0, 0, 0.05)), side * 0.5 + Vector((0, 0, 0.15))], "scope_at_neck": [side * 0.30 + fwd * 0.10 + Vector((0, 0, -0.08)), side * 0.35 - fwd * 0.10 + Vector((0, 0, 0.0)), fwd * 0.35 + side * 0.15 + Vector((0, 0, -0.15))] + [side * 0.45 + fwd * 0.25 + Vector((0, 0, 0.05)), side * 0.5 + Vector((0, 0, 0.15))], "forceps": [side * 0.45 + fwd * 0.25 + Vector((0, 0, 0.05)), side * 0.5 + Vector((0, 0, 0.15))], "bandage": [side * 0.30 + fwd * 0.10 + Vector((0, 0, -0.08)), side * 0.35 - fwd * 0.10 + Vector((0, 0, 0.0)), fwd * 0.35 + side * 0.15 + Vector((0, 0, -0.15))] + [side * 0.45 + fwd * 0.25 + Vector((0, 0, 0.05)), side * 0.5 + Vector((0, 0, 0.15))]}
    for off in PREF.get(lab, []) + [fwd * 0.42 + Vector((0, 0, 0.12)), fwd * 0.3 + side * 0.3 + Vector((0, 0, 0.15)), fwd * 0.3 - side * 0.3 + Vector((0, 0, 0.15)),
                side * 0.42 + Vector((0, 0, 0.1)), -side * 0.42 + Vector((0, 0, 0.1)), fwd * 0.2 + Vector((0, 0, 0.45)), -fwd * 0.35 + Vector((0, 0, 0.3))]:
        p = tgt + off; d = (tgt - p)
        hit, loc, nrm, idx, ob, mx = sc.ray_cast(dg, p, d.normalized(), distance=d.length + 0.02)
        ok = (not hit) or (ob is not None and (ob.parent == r or (loc - tgt).length < 0.06))
        inside = sum(sc.ray_cast(dg, p, v_, distance=0.08)[0] for v_ in (Vector((0, 0, 1)), Vector((0, 0, -1)), Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, -1, 0)))) >= 2
        if ok and not inside: best = p; break
    cam.location = best if best is not None else tgt + fwd * 0.42 + Vector((0, 0, 0.12))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd.dof.use_dof = False
    sc.render.filepath = os.path.join(out, f"{t:05.1f}_{n}_{lab}.jpg"); bpy.ops.render.render(write_still=True)
print("CLOSEUPS_DONE")
