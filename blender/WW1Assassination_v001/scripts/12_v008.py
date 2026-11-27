# WW1Assassination v008: rebuild of the approved-then-rejected v007 to the batch-2 standard (hard cuts, director's 25-item list).
# blender -b WW1Assassination_v007_60fps.blend --python 12_v008.py -- out.blend
# Same VO, timing and frame range as v007 (1-1826). Every fix is applied to the packed v007 scene; then per-shot cameras.
import bpy, sys, os, math
from mathutils import Vector, Matrix, Quaternion
OUT = sys.argv[sys.argv.index("--") + 1]
HERE = os.path.dirname(os.path.abspath(__file__))
sc = bpy.context.scene; O = bpy.data.objects

def fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    return [f for l in ad.action.layers for s in l.strips for cb in s.channelbags for f in cb.fcurves]
def channelbag(idb):
    ad = idb.animation_data
    return [cb for l in ad.action.layers for s in l.strips for cb in s.channelbags][0]
def drop_curves(idb, pred):
    ad = idb.animation_data
    if not ad or not ad.action: return
    for l in ad.action.layers:
        for s in l.strips:
            for cb in s.channelbags:
                for f in list(cb.fcurves):
                    if pred(f): cb.fcurves.remove(f)
def hide_always(o):
    drop_curves(o, lambda f: f.data_path in ("hide_render", "hide_viewport"))
    o.hide_render = True; o.hide_viewport = True

# ---------------------------------------------------------------- 1. grade: one constant look (no rewind tint, no exposure blips)
drop_curves(sc, lambda f: f.data_path in ("view_settings.exposure", "view_settings.white_balance_temperature"))
sc.view_settings.exposure = -0.35; sc.view_settings.white_balance_temperature = 6500
print("GRADE constant")

exec(open(os.path.join(HERE, "12_v008_fix.py")).read())
exec(open(os.path.join(HERE, "12_v008_fix2.py")).read())
exec(open(os.path.join(HERE, "12_v008_cams.py")).read())

sc.frame_start, sc.frame_end = 1, 1826
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("V008_SAVED", OUT)
