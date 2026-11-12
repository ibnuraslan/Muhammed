"""AimFix (director, v006b: Track To with world up, horizon level): for every QA range with no character in view, blend a Damped Track on the camera
toward the acting character's head (influence 0->1 over 10 frames in, 1->0 over 10 frames out). Camera path unchanged.
blender -b film.blend --python 05_aimfix.py -- <qa.json> <out.blend>"""
import sys, json, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; QA, OUT = a[0], a[1]
sc = bpy.context.scene; cam = sc.camera
fr = json.load(open(QA))["frames"]
bad = sorted(int(f) for f, fl in fr.items() if any(k == "EMPTY" and (w.startswith("no character") or w.startswith("only ")) for k, w in fl))
ranges = []
for f in bad:
    if ranges and f - ranges[-1][1] <= 18: ranges[-1][1] = f
    else: ranges.append([f, f])
RIGS = [o for o in bpy.data.objects if o.type == "ARMATURE" and "head" in o.pose.bones]
def body(r):
    m = [c for c in r.children if c.type == "MESH" and c.name.endswith(".body")]
    return m[0] if m else None
cons = {}
for r0, r1 in ranges:
    r0 -= 3; r1 += 3
    mid = (r0 + r1) // 2; sc.frame_set(mid); cp = cam.matrix_world.translation
    live = [r for r in RIGS if body(r) and not body(r).hide_render]
    if not live: print("AIMFIX no live char", r0, r1); continue
    tgt = min(live, key=lambda r: (r.matrix_world @ r.pose.bones["head"].head - cp).length)
    if r0 >= 3505 and "Protester1" in bpy.data.objects: tgt = bpy.data.objects["Protester1"]     # outside: the protesters, not the old man behind the wall
    if 2840 <= r0 <= 2900: tgt = bpy.data.objects["Prisoner"]                                     # the runner in the corridor, not the inmate behind cell walls
    c = cons.get(tgt.name)
    if c is None:
        c = cam.constraints.new("TRACK_TO"); c.name = "AimFix_" + tgt.name; c.target = tgt; c.subtarget = "head"; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"; c.use_target_z = False
        c.influence = 0.0; c.keyframe_insert("influence", frame=0); cons[tgt.name] = c
    for f, v in ((r0 - 10, 0.0), (r0, 1.0), (r1, 1.0), (r1 + 10, 0.0)):
        c.influence = v; c.keyframe_insert("influence", frame=f)
    print("AIMFIX", r0, r1, "->", tgt.name)
sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("AIMFIX_SAVED", OUT, len(ranges))
# the young->old swap at 3166 needs a few frames off him: aim at the young man to 3160, the old man from 3172
c = cam.constraints.get("AimFix_Prisoner")
if c and c.id_data.animation_data:
    _act = c.id_data.animation_data.action
    _fcs = list(_act.fcurves) if hasattr(_act, "fcurves") else [fc for l in _act.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
    for fc in [x for x in _fcs if 'AimFix_Prisoner"' in x.data_path]:
        for k in [k for k in fc.keyframe_points if 3100 <= k.co.x <= 3215][::-1]: fc.keyframe_points.remove(k)
    for f, v in ((3116, 0.0), (3126, 1.0), (3150, 1.0), (3160, 0.0)):
        c.influence = v; c.keyframe_insert("influence", frame=f)
    co = cam.constraints.get("AimFix_PrisonerOld")
    if co is None:
        co = cam.constraints.new("TRACK_TO"); co.name = "AimFix_PrisonerOld"; co.target = bpy.data.objects["PrisonerOld"]; co.subtarget = "head"; co.up_axis = "UP_Y"; co.use_target_z = False
        co.track_axis = "TRACK_NEGATIVE_Z"; co.influence = 0.0; co.keyframe_insert("influence", frame=0)
    for f, v in ((3172, 0.0), (3182, 1.0), (3204, 1.0), (3214, 0.0)):
        co.influence = v; co.keyframe_insert("influence", frame=f)
    bpy.ops.wm.save_as_mainfile(filepath=OUT); print("AIMFIX_SWAP_SPLIT")
# drop aims that make the camera jump (CAMJUMP): the guard at the gate whip, the field->cell cut-over, the protester at 3621
def _drop(name, f0, f1):
    co = cam.constraints.get(name)
    if not co: return
    act = cam.animation_data.action
    fcs = list(act.fcurves) if hasattr(act, "fcurves") else [fc for l in act.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
    for fc in [x for x in fcs if ('"%s"' % name) in x.data_path]:
        for k in [k for k in fc.keyframe_points if f0 <= k.co.x <= f1][::-1]: fc.keyframe_points.remove(k)
        fc.keyframe_points.insert(f0, 0.0); fc.keyframe_points.insert(f1, 0.0)
_drop("AimFix_Guard", 1485, 1545); _drop("AimFix_Prisoner", 1840, 1885); _drop("AimFix_Guard2", 3605, 3645)
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("AIMFIX_DROPPED")
# the corridor-run aim must be off before the beat-12 cut-over at 2898 (the target moves sets there)
_drop("AimFix_Prisoner", 2815, 2915)
_c = cam.constraints.get("AimFix_Prisoner")
for f, v in ((2826, 0.0), (2836, 1.0), (2884, 1.0), (2893, 0.0)):
    _c.influence = v; _c.keyframe_insert("influence", frame=f)
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("AIMFIX_2898")

# runner in the field (30 s): aim on him until just before he is moved into the cell at 1860
_c = cam.constraints.get("AimFix_Prisoner")
for f, v in ((1778, 0.0), (1788, 1.0), (1848, 1.0), (1857, 0.0)):
    _c.influence = v; _c.keyframe_insert("influence", frame=f)
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("AIMFIX_FIELD")
# roll check: camera world X axis must stay level (|z| < 0.1)
bad = []
for f in range(sc.frame_start, sc.frame_end + 1):
    sc.frame_set(f); x = cam.matrix_world.to_3x3().col[0]
    if abs(x.z) >= 0.1: bad.append(f)
print("ROLL_BAD", len(bad), bad[:20])
