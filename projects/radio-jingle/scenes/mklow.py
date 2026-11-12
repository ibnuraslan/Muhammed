"""One-time cache of light single trees from the heavy Poly Haven scans (each scan holds three trees and millions of
polygons). python mklow.py <aid> <pick> <target_polys>  -> nvidia_doc/assets/polyhaven/_low/<aid>_<pick>.blend
The cache is git-ignored with the rest of assets/polyhaven; rj.low_model() creates it on demand."""
import os, sys
import bpy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "nvidia_doc", "scenes"))
import ph
from common import reset

aid, pick, target = sys.argv[1], sys.argv[2], int(sys.argv[3])
out = os.path.join(ph.ROOT, "_low", f"{aid}_{pick}.blend")
os.makedirs(os.path.dirname(out), exist_ok=True)
reset()
r, ms = ph.model(aid)
keep = [o for o in ms if pick in o.name] or ms[:1]
for o in ms:
    if o not in keep:
        bpy.data.objects.remove(o, do_unlink=True)
objs = []
for o in keep:
    n = len(o.data.polygons)
    mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    bpy.context.view_layer.objects.active = o
    for ob in bpy.context.selected_objects:
        ob.select_set(False)
    o.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    if n > target:
        d = o.modifiers.new("dec", 'DECIMATE'); d.ratio = target / n
        bpy.ops.object.modifier_apply(modifier="dec")
    objs.append(o)
from mathutils import Vector
lo = [min((o.matrix_world @ Vector(c))[i] for o in objs for c in o.bound_box) for i in range(3)]
hi = [max((o.matrix_world @ Vector(c))[i] for o in objs for c in o.bound_box) for i in range(3)]
for o in objs:                                   # centre on the trunk base: origin at the bottom centre
    o.location.x -= (lo[0] + hi[0]) / 2; o.location.y -= (lo[1] + hi[1]) / 2; o.location.z -= lo[2]
    o.name = f"LOW_{aid}_{pick}"
bpy.data.libraries.write(out, set(objs), path_remap='ABSOLUTE', fake_user=True)
print("[low]", out, [len(o.data.polygons) for o in objs])
