"""AimFix (director, v006): for every QA range with no character in view, blend a Damped Track on the camera
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
    c = cons.get(tgt.name)
    if c is None:
        c = cam.constraints.new("DAMPED_TRACK"); c.name = "AimFix_" + tgt.name; c.target = tgt; c.subtarget = "head"; c.track_axis = "TRACK_NEGATIVE_Z"
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
