"""v008 fixes from the spot check (new timeline frames):
- 6. The "giant white ball" in the chamber pool (and the white disc at the far end of the tunnel) was the sky-blue world
  background seen through the open end of the passage tube. Camera rays now see black while the camera is in the caves
  (713-1908); the sky stays for the outdoor and tunnel-mouth shots.
- 6b. The ball itself was DiverA's rim point light seen through the water; rim lights are now invisible to camera, glossy and transmission rays.
- 3. Death beat (994-1105): medium shot from behind and above the lone diver as he slows and goes still, face down, his lamp
  fading (his face is never shown); the camera glides slowly in.
- 7. Ending (2062-2268): the camera rises over the stretcher and the people (never through them) and settles on a medium
  push-in on the coach and the boys outside in daylight, faces to camera.
blender -b in.blend --python 21_v008_fix.py -- out.blend"""
import bpy, sys
from mathutils import Vector as V
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; cam = sc.camera; aim = cam.constraints[0].target
bg = sc.world.node_tree.nodes["Background"].inputs["Strength"]
s0 = 1.0      # the sky's own strength (v007); never read it back from an animated socket
wad = sc.world.node_tree.animation_data
if wad and wad.action:
    for lay in wad.action.layers:
        for st in lay.strips:
            for cb in st.channelbags:
                for fc in list(cb.fcurves):
                    if fc.data_path == 'nodes["Background"].inputs[1].default_value': cb.fcurves.remove(fc)
for f, v in ((1, s0), (712, s0), (713, 0.0), (2119, 0.0), (2120, s0)):   # v009 timeline (v008 + longer death beat and tow)
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
# death beat: from behind and above the lone diver (tanks, back and fins read; a front view read as a face)
dc = bpy.data.objects["DiverC"]
def spine(f):
    sc.frame_set(f); return dc.matrix_world @ dc.pose.bones["spine03"].head
P = {f: spine(f) for f in (1014, 1094, 1175)}
override(1014, 1175,
         [(1014, P[1014] + V((0.5, 1.75, 0.6))), (1094, P[1094] + V((0.5, 1.6, 0.55))), (1175, P[1175] + V((0.45, 1.45, 0.5)))],
         [(1014, P[1014]), (1094, P[1094]), (1175, P[1175])],
         [(1014, V((28, 0, 0))), (1094, V((28, 0, 0))), (1175, V((29, 0, 0)))])
# ending: from the stretcher shot round the outside of the group (never over bare ground, never through people) onto the coach and the boys
c61 = V([fc.evaluate(2272) for fc in CL]); a61 = V([fc.evaluate(2272) for fc in AL]); l61 = LF[0].evaluate(2272)
c40 = V([fc.evaluate(2251) for fc in CL]); a40 = V([fc.evaluate(2251) for fc in AL])
override(2273, 2479,
         [(2251, c40), (2272, c61), (2311, V((3.4, -12.0, 1.9))), (2351, V((4.3, -16.0, 1.7))), (2401, V((2.4, -18.6, 1.55))), (2479, V((1.0, -19.0, 1.5)))],
         [(2251, a40), (2272, a61), (2311, V((1.0, -14.6, 1.3))), (2351, V((0.9, -15.2, 1.25))), (2401, V((0.9, -15.3, 1.2))), (2479, V((0.8, -15.3, 1.2)))],
         [(2251, V((l61, 0, 0))), (2272, V((l61, 0, 0))), (2351, V((26, 0, 0))), (2479, V((25, 0, 0)))])
# 6. the "white ball": the divers' rim lights (point lights, 15 cm radius) seen through the water. Light only, never seen.
for o in bpy.data.objects:
    if o.type == 'LIGHT' and o.name.endswith("_Rim"):
        o.visible_camera = False; o.visible_glossy = False; o.visible_transmission = False; o.visible_diffuse = True
print("V008_FIX_OK")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
