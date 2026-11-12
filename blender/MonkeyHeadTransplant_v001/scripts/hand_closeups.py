"""270x480 close-up of every hand contact. blender -b film.blend --python hand_closeups.py -- <out_dir> x ; then python3 hand_closeups_sheet.py <out_dir> <sheet.jpg>"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, SHEET = a[0], a[1]; os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene; film = sc.camera
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = "JPEG"
cd = bpy.data.cameras.new("HC"); cd.lens = 35; cd.dof.use_dof = False; cam = bpy.data.objects.new("HC", cd); sc.collection.objects.link(cam)
ld = bpy.data.lights.new("HCL", "AREA"); ld.energy = 25; ld.size = 0.3; lo = bpy.data.objects.new("HCL", ld); sc.collection.objects.link(lo)
CONTACTS = [(120, "Surgeon", "R", "pen pinch (marker line)"), (200, "Surgeon", "L", "palm on monkey shoulder"),
            (262, "Surgeon", "L", "cradle back of skull"), (262, "Surgeon", "R", "palm on temple"), (330, "Surgeon", "L", "carry, cradle"),
            (330, "Surgeon", "R", "carry, temple"), (470, "Surgeon", "R", "needle holder pinch"), (470, "Surgeon", "L", "forceps pinch"),
            (600, "Nurse", "L", "bowl rim pinch"), (480, "Nurse", "R", "gas knob"), (300, "Anaes", "R", "breathing bag"),
            (1270, "Surgeon", "R", "wave in front of face (no contact)")]
dg = None; done = []
sc.camera = cam
for i, (f, rig, s, label) in enumerate(CONTACTS):
    sc.frame_set(f); r = bpy.data.objects[rig]
    p = (r.matrix_world @ r.pose.bones["finger3-1." + s].head)
    dg = bpy.context.evaluated_depsgraph_get()
    root = r.matrix_world @ r.pose.bones["root"].head
    out = p - root; out.z = 0; out.normalize()
    cands = [(film.matrix_world.translation - p), out + Vector((0, 0, 0.6)), out + Vector((0, 0, -0.2)), Vector((0, 0, 1)) + out * 0.3,
             out.cross(Vector((0, 0, 1))) + Vector((0, 0, 0.4)), -out.cross(Vector((0, 0, 1))) + Vector((0, 0, 0.4))]
    best = None
    for d in cands:
        d = d.normalized(); hit = sc.ray_cast(dg, p + d * 0.06, d, distance=0.34)
        free = (hit[1] - p).length if hit[0] else 0.4
        if best is None or free > best[0]: best = (free, d)
    dist = min(0.3, best[0] - 0.04); d = best[1]
    cam.location = p + d * dist; cam.rotation_euler = (p - cam.location).to_track_quat("-Z", "Y").to_euler()
    lo.location = cam.location + Vector((0, 0, 0.15)); lo.rotation_euler = cam.rotation_euler
    sc.render.filepath = os.path.join(OUT, "c%02d.jpg" % i); bpy.ops.render.render(write_still=True); done.append((i, f, rig, s, label))
import json
json.dump([dict(i=i, frame=f, rig=rig, side=s, label=label) for i, f, rig, s, label in done], open(os.path.join(OUT, "labels.json"), "w"))
print("CLOSEUPS", OUT, len(done))
