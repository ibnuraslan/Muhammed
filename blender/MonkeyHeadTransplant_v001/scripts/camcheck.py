import bpy
from mathutils import Vector
sc = bpy.context.scene; cam = sc.camera
for f in list(range(1, 1771, 15)):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    M = cam.matrix_world; p = M.translation; fwd = -(M.to_3x3().col[2])
    h = sc.ray_cast(dg, p, fwd)
    nm = h[4].name if h[0] else None; d = (h[1] - p).length if h[0] else 99
    bad = [nm] if d < 0.06 else []
    # inside test: cast up/down/sides, count backface-ish (normal facing away)
    for dv in (Vector((0,0,1)), Vector((0,0,-1)), Vector((1,0,0)), Vector((-1,0,0)), Vector((0,1,0)), Vector((0,-1,0))):
        hh = sc.ray_cast(dg, p, dv)
        if hh[0] and hh[2].dot(dv) > 0 and (hh[1]-p).length < 0.5 and hh[4].name not in ("XR_Void",): bad.append("in:" + hh[4].name)
    if bad: print("CAM", f, round(f/60,2), "front", nm, round(d,3), bad)
