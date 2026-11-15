"""Quick stills of sc_binder_ots for layout and hand QA (not the delivery render).
  python scenes/preview_ots.py OUTDIR [--t 0,0.5,1] [--samples 16] [--pct 50] [--hand]
--hand also renders a close-up of the right hand from three angles (camera only; the scene is unchanged)."""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
import kit
from common import reset, camera, point_at
import sc_binder_ots as S

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
out = os.path.abspath(sys.argv[1]); os.makedirs(out, exist_ok=True)
ts = [float(x) for x in arg("--t", "0,0.5,1").split(",")]
s = reset(res=kit.RES, samples=arg("--samples", 16), exposure=S.EXPOSURE)
s.render.resolution_percentage = arg("--pct", 50)
s.cycles.use_denoising = True
ctx = S.build("ots"); spec = S.MOVES["ots"]
cam = camera((0, 0, 0), (0, 1, 0), lens=35, dof_dist=3.0, fstop=spec["dof"]); cam.data.dof.use_dof = True
ctx["cam"] = cam
rest = {(a.name, pb.name): pb.matrix_basis.copy() for a in bpy.data.objects if a.type == 'ARMATURE' for pb in a.pose.bones}
for t in ts:
    for a in bpy.data.objects:
        if a.type == 'ARMATURE':
            for pb in a.pose.bones:
                pb.matrix_basis = rest[(a.name, pb.name)]
    bpy.context.view_layer.update()
    kit.apply_cam(cam, ctx, spec, t); bpy.context.view_layer.update()
    s.render.filepath = os.path.join(out, f"t{t:.2f}.png"); bpy.ops.render.render(write_still=True)
    if "--hand" in sys.argv:
        h = ctx["h"]; pen = ctx["pen"]; c0 = pen.location + (pen.rotation_quaternion @ Vector((0, 0, 0.035)))
        print("[preview] t", t, "tip err", ctx.get("tip_err"), "clear", ctx.get("clear"), "axis", tuple(round(v, 2) for v in (pen.rotation_quaternion @ Vector((0, 0, 1)))), "wrist", tuple(round(v, 3) for v in h.bone_head("wrist.R")), "elbow", tuple(round(v, 3) for v in h.bone_head("lowerarm01.R")), flush=True)
        L0, lens0, dof0 = cam.location.copy(), cam.data.lens, cam.data.dof.use_dof
        cam.data.dof.use_dof = False
        for k, off in enumerate((Vector((0.16, -0.24, 0.2)), Vector((-0.3, -0.02, 0.12)), Vector((0.02, 0.32, 0.1)))):
            cam.location = c0 + off; point_at(cam, tuple(c0)); cam.data.lens = 50
            s.render.filepath = os.path.join(out, f"t{t:.2f}_hand{k}.png"); bpy.ops.render.render(write_still=True)
        cam.location, cam.data.lens = L0, lens0; cam.data.dof.use_dof = dof0
print("[preview] done", out, flush=True)
