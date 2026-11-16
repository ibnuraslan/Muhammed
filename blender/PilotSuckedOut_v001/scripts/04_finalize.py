"""B17 Phase 2: VO sound strip, bake the per-shot cameras (markers) into ONE camera with hard cuts, farm settings.
blender -b p2.blend --python 04_finalize.py -- VO.mp3 out.blend"""
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; VO, OUT = a
D = bpy.data; sc = bpy.context.scene
END = 1887
sc.frame_start = 1; sc.frame_end = END
# VO
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor
strips = getattr(se, "strips", None) or se.sequences
for st in list(strips): strips.remove(st)
snd = strips.new_sound("VO", VO, channel=1, frame_start=1)
# one camera
mk = sorted(sc.timeline_markers, key=lambda m: m.frame)
cd = D.cameras.new("CAM_FILM"); cam = D.objects.new("CAM_FILM", cd); sc.collection.objects.link(cam)
cam.rotation_mode = 'QUATERNION'; cd.clip_start = 0.03; cd.clip_end = 100000; cd.dof.use_dof = False
cd.sensor_fit = 'AUTO'
lt = D.lights.new("CATCH_FILM", 'POINT'); lt.energy = 1.5; lt.shadow_soft_size = 0.02
lo = D.objects.new("CATCH_FILM", lt); sc.collection.objects.link(lo); lo.parent = cam; lo.location = (0, 0.06, 0)
def src_cam(f):
    c = None
    for m in mk:
        if m.frame <= f: c = m.camera
    return c
prev = None
for f in range(1, END + 1):
    sc.frame_set(f); c = src_cam(f)
    M = c.matrix_world.copy(); loc, q, s = M.decompose()
    cam.location = loc
    if prev is not None and prev.dot(q) < 0: q = -q
    cam.rotation_quaternion = q; prev = q
    cd.lens = c.data.lens
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_quaternion", frame=f); cd.keyframe_insert("lens", frame=f)
for fc in (list(cam.animation_data.action.fcurves) if hasattr(cam.animation_data.action, "fcurves") else []) :
    for k in fc.keyframe_points: k.interpolation = 'LINEAR'
# remove per-shot cameras and their catchlights, unbind markers (keep names for review)
for m in mk: m.camera = None
for o in [o for o in D.objects if (o.type == 'CAMERA' and o is not cam) or (o.name.startswith("CATCH_") and o is not lo)]:
    D.objects.remove(o, do_unlink=True)
sc.camera = cam
# farm settings
r = sc.render; r.engine = 'CYCLES'; r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps = 60; r.fps_base = 1.0; r.use_motion_blur = False
cy = sc.cycles; cy.samples = 48; cy.adaptive_threshold = 0.05; cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'; cy.device = 'CPU'
r.use_simplify = False
r.image_settings.file_format = 'PNG'
r.filepath = "//render/PilotSuckedOut_v002_"
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("FINAL_OK", END, len(mk))
