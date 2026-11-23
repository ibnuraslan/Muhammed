"""Build one shot: set + cast + camera move -> clip check -> shots/<PART>/<ID>.blend -> storyboard frame.

    blender -b --python tools/shot.py -- P1 S04            # build, check, save, render the middle frame
    env: PREVIEW=0.25 (board) | SPP | HAIR (strand density) | NORENDER=1 | FRAME=mid|first|last
"""
import os, sys, json, math, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "lib")); sys.path.insert(0, os.path.join(ROOT, "scenes"))
import common as C
argv = sys.argv[sys.argv.index("--") + 1:]
PART, SID = argv[0], argv[1]
C.reset()
import bpy
from mathutils import Vector
import importlib
mod = importlib.import_module(PART.lower())
spec = mod.SHOTS[SID]
FPS = 24
sc = C.render_setup(samples=int(os.environ.get("SPP", "128")), noise=0.03, bounces=8)
sc.render.fps = FPS
sc.name = SID
t0 = time.time()
cam_spec = spec["fn"]()
N = int(round(spec["dur"] * FPS))
sc.frame_start = 1; sc.frame_end = N


def camera_move(cs, N):
    a_loc, a_tgt = Vector(cs["a"][0]), Vector(cs["a"][1])
    b_loc, b_tgt = (Vector(cs["b"][0]), Vector(cs["b"][1])) if cs.get("b") else (a_loc, a_tgt)
    cam = bpy.data.objects.new("CAM_" + SID, bpy.data.cameras.new("CAM_" + SID)); sc.collection.objects.link(cam)
    tgt = bpy.data.objects.new("CAMTGT_" + SID, None); sc.collection.objects.link(tgt)
    cam.data.lens = cs.get("lens", 35); cam.data.sensor_width = 36; cam.data.clip_start = 0.02; cam.data.clip_end = 2000
    con = cam.constraints.new('TRACK_TO'); con.target = tgt; con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'
    for f, l, t in ((1, a_loc, a_tgt), (N, b_loc, b_tgt)):
        cam.location = l; tgt.location = t
        cam.keyframe_insert("location", frame=f); tgt.keyframe_insert("location", frame=f)
    if cs.get("lens_b"):
        cam.data.lens = cs["lens"]; cam.data.keyframe_insert("lens", frame=1)
        cam.data.lens = cs["lens_b"]; cam.data.keyframe_insert("lens", frame=N)
    if cs.get("fstop"):
        cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = cs["fstop"]
        if cs.get("focus_obj") is not None:
            cam.data.dof.focus_object = cs["focus_obj"]
        else:
            fo = bpy.data.objects.new("FOCUS_" + SID, None); sc.collection.objects.link(fo)
            fo.location = Vector(cs.get("focus", a_tgt)); cam.data.dof.focus_object = fo
    sc.camera = cam
    return cam


cam = camera_move(cam_spec, N)
# clip QA (people vs everything else); FLOATING hands too
import clipcheck
bad = clipcheck.check(f"{PART}_{SID}", limit=cam_spec.get("clip_limit", 60),
                      hand_ok=tuple(clipcheck.check.__defaults__[1]) + tuple(cam_spec.get("hand_ok", ())) + ("_floor", "stair"))
cine = dict(sat=1.18, exposure=0.15); cine.update(cam_spec.get("cine") or {})
cam_spec["cine"] = cine
import grade as G
G.add_grade(sc, bloom=cam_spec.get("bloom", 0.3), look="cinematic", cine=cam_spec.get("cine"))
sc.render.image_settings.file_format = 'PNG'
shots_dir = os.path.join(ROOT, "shots", PART); os.makedirs(shots_dir, exist_ok=True)
info = dict(shot=SID, part=PART, dur=spec["dur"], frames=N, vo=spec.get("vo", ""), desc=spec.get("desc", ""),
            clips=len(bad), build_s=round(time.time() - t0, 1))
sc["shot_info"] = json.dumps(info)
blend = os.path.join(shots_dir, SID + ".blend")
bpy.ops.file.make_paths_relative() if bpy.data.filepath else None
bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
print("SAVED", blend)
if not os.environ.get("NORENDER"):
    which = os.environ.get("FRAME", "mid")
    f = {"first": 1, "last": N}.get(which, max(1, N // 2))
    sc.frame_set(f)
    out = os.path.join(ROOT, "out", PART.lower(), "board", SID + ".png"); os.makedirs(os.path.dirname(out), exist_ok=True)
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("RENDERED", out)
for ex in cam_spec.get("extra", []):          # extra stills (e.g. a CCTV view used on a monitor in another shot)
    c2 = bpy.data.objects.new("EXCAM", bpy.data.cameras.new("EXCAM")); sc.collection.objects.link(c2)
    c2.location = Vector(ex["loc"]); c2.rotation_euler = (Vector(ex["tgt"]) - Vector(ex["loc"])).to_track_quat('-Z', 'Y').to_euler()
    c2.data.lens = ex.get("lens", 24); sc.camera = c2; sc.render.use_compositing = False
    sc.render.filepath = os.path.join(ROOT, "out", PART.lower(), "extra", ex["name"] + ".png")
    bpy.ops.render.render(write_still=True); sc.camera = cam; sc.render.use_compositing = True
    bpy.data.objects.remove(c2)
info["render_s"] = round(time.time() - t0, 1)
json.dump(info, open(os.path.join(shots_dir, SID + ".json"), "w"), indent=1)
print("SHOTINFO", json.dumps(info))
