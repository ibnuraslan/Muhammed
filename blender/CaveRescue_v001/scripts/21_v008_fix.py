"""v008 fixes from the spot check (new timeline frames):
- 6. The "giant white ball" in the chamber pool (and the white disc at the far end of the tunnel) was the sky-blue world
  background seen through the open end of the passage tube. Camera rays now see black while the camera is in the caves
  (713-1908); the sky stays for the outdoor and tunnel-mouth shots.
- 3. Death beat (994-1105): medium shot from in front of the lone diver as he slows and goes still, face down, his lamp
  fading (his face is never shown); the camera glides slowly in.
- 7. Ending (2062-2268): the camera rises over the stretcher and the people (never through them) and settles on a medium
  push-in on the coach and the boys outside in daylight, faces to camera.
blender -b in.blend --python 21_v008_fix.py -- out.blend"""
import bpy, sys
from mathutils import Vector as V
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; cam = sc.camera; aim = cam.constraints[0].target
bg = sc.world.node_tree.nodes["Background"].inputs["Strength"]
s0 = bg.default_value
for f, v in ((1, s0), (712, s0), (713, 0.0), (1908, 0.0), (1909, s0)):
    bg.default_value = v; bg.keyframe_insert("default_value", frame=f)
fcb = sc.world.node_tree.animation_data.action
for lay in fcb.layers:
    for st in lay.strips:
        for cb in st.channelbags:
            for fc in cb.fcurves:
                if "Strength" in fc.data_path and "Background" in fc.data_path:
                    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
def fcs(o, path):
    ad = o.animation_data
    return sorted([fc for lay in ad.action.layers for st in lay.strips for cb in st.channelbags for fc in cb.fcurves if fc.data_path == path], key=lambda f: f.array_index)
CL, AL = fcs(cam, "location"), fcs(aim, "location"); LF = fcs(cam.data, "lens")
def setk(F, f, vals):
    for i, fc in enumerate(F):
        ks = [k for k in fc.keyframe_points if int(round(k.co.x)) == f]
        v = vals[i] if hasattr(vals, "__len__") else vals
        if ks: ks[0].co.y = v; ks[0].handle_left.y = v; ks[0].handle_right.y = v; ks[0].interpolation = 'LINEAR'
        else: fc.keyframe_points.insert(f, v).interpolation = 'LINEAR'
def catmull(pts):
    def at(f):
        fs = [p[0] for p in pts]
        i = max(0, min(len(pts) - 2, max(k for k in range(len(fs)) if fs[k] <= f) if f >= fs[0] else 0))
        p0 = pts[max(0, i - 1)][1]; p1 = pts[i][1]; p2 = pts[i + 1][1]; p3 = pts[min(len(pts) - 1, i + 2)][1]
        t = (f - fs[i]) / (fs[i + 1] - fs[i]); t = max(0.0, min(1.0, t))
        return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
    return at
def override(f0, f1, cpts, apts, lpts):
    fc_, fa_, fl_ = catmull(cpts), catmull(apts), catmull(lpts)
    for f in range(f0, f1 + 1):
        setk(CL, f, fc_(f)); setk(AL, f, fa_(f)); setk(LF, f, fl_(f)[0] if hasattr(fl_(f), "__len__") else fl_(f))
    for F in (CL, AL, LF):
        for fc in F: fc.update()
# death beat
override(994, 1105,
         [(994, V((400.85, -22.2, -3.25))), (1050, V((400.82, -22.1, -3.28))), (1105, V((400.8, -22.0, -3.3)))],
         [(994, V((400.5, -20.3, -3.4))), (1050, V((400.5, -20.3, -3.45))), (1105, V((400.5, -20.3, -3.5)))],
         [(994, V((30, 0, 0))), (1050, V((31, 0, 0))), (1105, V((32, 0, 0)))])
# ending: from the current camera at 2061 up over the group, then onto the coach and the boys
c61 = V([fc.evaluate(2061) for fc in CL]); a61 = V([fc.evaluate(2061) for fc in AL]); l61 = LF[0].evaluate(2061)
override(2062, 2268,
         [(2040, V([fc.evaluate(2040) for fc in CL])), (2061, c61), (2095, V((0.0, -13.0, 3.0))), (2145, V((2.4, -18.0, 2.2))), (2200, V((1.6, -18.3, 1.5))), (2268, V((1.4, -18.6, 1.45)))],
         [(2040, V([fc.evaluate(2040) for fc in AL])), (2061, a61), (2095, V((0.6, -14.0, 1.0))), (2145, V((1.4, -15.2, 1.1))), (2200, V((1.5, -15.3, 1.15))), (2268, V((1.2, -15.3, 1.15)))],
         [(2040, V((l61, 0, 0))), (2061, V((l61, 0, 0))), (2145, V((27, 0, 0))), (2268, V((26, 0, 0)))])
print("V008_FIX_OK")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
