"""270x480 close-ups of every hand action (client hands rule). blender -b film.blend --python hand_closeups.py -- outdir"""
import bpy, sys, os
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]; os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
cd = bpy.data.cameras.new("HandCam"); cd.lens = 50; hc = bpy.data.objects.new("HandCam", cd); sc.collection.objects.link(hc); sc.camera = hc
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = "JPEG"
SHOTS = [(60, "Man", "L"), (60, "Man", "R"), (276, "Man", "R"), (268, "OfficerA", "R"), (255, "OfficerA", "L"), (312, "Man", "L"),
         (360, "ManW", "R"), (560, "ManW", "L"), (940, "ManW", "R"), (1060, "Man", "R"), (1300, "OfficerB", "R"), (1306, "OfficerD", "R"),
         (1330, "OfficerC", "R"), (1340, "OfficerE", "L"), (1530, "ManW", "R"), (230, "Vendor", "R")]
lt = bpy.data.objects.new("HandLight", bpy.data.lights.new("HandLight", "POINT")); lt.data.energy = 6; lt.data.shadow_soft_size = 0.25
sc.collection.objects.link(lt); lt.parent = hc; lt.location = (0.08, 0.1, 0)      # review-only fill so dark-set hands read
film = bpy.data.objects["CAM_Film"]
def owner_ok(o, arm):
    return o is not None and ((o.parent is arm and (".body" in o.name or "glove" in o.name.lower())) or o.name.startswith(("TicketSlip", "TicketPad", "St_Phone", "KeyRing", "TapFile", "FanPaper")) or "glove" in o.name.lower())
for i, (f, n, s) in enumerate(SHOTS):
    sc.frame_set(f); arm = bpy.data.objects[n]; dg = bpy.context.evaluated_depsgraph_get()
    w = arm.matrix_world @ arm.pose.bones["wrist." + s].head
    k = arm.matrix_world @ arm.pose.bones["finger3-2." + s].head
    c = (w + k) * 0.5
    r = arm.matrix_world @ arm.pose.bones["root"].head
    side = (w - Vector((r.x, r.y, w.z))); side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
    fc = film.matrix_world.translation; tof = (fc - c); tof.z = max(tof.z, 0); tof = tof.normalized()
    cands = [tof, (tof + side).normalized(), side, (side + Vector((0, 0, 0.8))).normalized(), (tof + Vector((0, 0, 0.9))).normalized(), -side, (-tof + Vector((0,0,0.5))).normalized()]
    best = None
    for d in cands:
        p_ = c + d * 0.45 + Vector((0, 0, 0.05)); v = c - p_
        h = sc.ray_cast(dg, p_, v.normalized(), distance=v.length + 0.05)
        if not h[0] or (owner_ok(h[4], arm) and (h[1] - c).length < 0.14): best = p_; break
    hc.location = best if best is not None else c + cands[0] * 0.45
    hc.rotation_euler = (c - hc.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(out, "h%02d_f%04d_%s_%s.jpg" % (i, f, n, s)); bpy.ops.render.render(write_still=True)
    print("SHOT", i, f, n, s, "clear" if best is not None else "OCCLUDED")
