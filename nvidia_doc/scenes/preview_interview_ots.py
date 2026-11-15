"""Quick stills of sc_interview_ots for layout and hand QA (not the delivery render).
  python scenes/preview_interview_ots.py OUTDIR [--t 0.2,0.55,0.95] [--samples 16] [--pct 50] [--hand] [--wide]
--hand also renders close-ups of the right hand from three angles (camera only; the scene is unchanged).
--wide adds a wide view of the whole set from the side (layout check)."""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
import kit
from common import reset, camera, point_at
import sc_interview_ots as S

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
out = os.path.abspath(sys.argv[1]); os.makedirs(out, exist_ok=True)
ts = [float(x) for x in arg("--t", "0.2,0.55,0.95").split(",")]
s = reset(res=kit.RES, samples=arg("--samples", 16), exposure=S.EXPOSURE)
s.render.resolution_percentage = arg("--pct", 50)
s.cycles.use_denoising = True
ctx = S.build(S.VARIANT_FOR["slide"]); spec = S.MOVES["slide"]
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
    h = ctx["h"]
    print(f"[preview] t {t:.2f} gap {ctx.get('rh_gap')} rh_min {ctx.get('rh_min'):.4f} passport {tuple(round(v, 3) for v in ctx['passport'].location)} "
          f"wrist {tuple(round(v, 3) for v in h.bone_head('wrist.R'))} shoulder {tuple(round(v, 3) for v in h.bone_head('upperarm01.R'))} "
          f"lh_dz {ctx.get('lh_dz'):.4f}", flush=True)
    s.render.filepath = os.path.join(out, f"t{t:.2f}.png"); bpy.ops.render.render(write_still=True)
    L0, lens0, dof0 = cam.location.copy(), cam.data.lens, cam.data.dof.use_dof
    if "--hand" in sys.argv:
        c0 = h.bone_head("finger3-1.R").lerp(h.bone_head("wrist.R"), 0.3)
        cam.data.dof.use_dof = False
        for k, off in enumerate((Vector((-0.28, 0.10, 0.16)), Vector((0.05, -0.32, 0.10)), Vector((-0.30, -0.06, 0.02)))):
            cam.location = c0 + off; point_at(cam, tuple(c0)); cam.data.lens = 50
            s.render.filepath = os.path.join(out, f"t{t:.2f}_hand{k}.png"); bpy.ops.render.render(write_still=True)
    if "--wide" in sys.argv:
        cam.data.dof.use_dof = False
        cam.location = Vector((-2.1, 0.2, 1.5)); point_at(cam, (0, 0.3, 0.9)); cam.data.lens = 24
        s.render.filepath = os.path.join(out, f"t{t:.2f}_wide.png"); bpy.ops.render.render(write_still=True)
    cam.location, cam.data.lens = L0, lens0; cam.data.dof.use_dof = dof0
print("[preview] done", out, flush=True)
