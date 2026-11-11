"""Contact audit for StanleyCup. blender -b anim.blend --python audit.py -- [step]
Checks: shoe soles vs floor (hover/sink), seat contact, fingers through the table top, the cup leaving the table, the bullet vs floor,
and the camera inside solid geometry (ray parity test)."""
import sys, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STEP = int(a[0]) if a else 10
sc = bpy.context.scene; TOP = sc["table_top"]; SEAT = sc["seat_top"]
dg = bpy.context.evaluated_depsgraph_get()
def wverts(name):
    o = bpy.data.objects[name]; e = o.evaluated_get(dg); me = e.to_mesh(); M = o.matrix_world
    vs = [M @ v.co for v in me.vertices]; e.to_mesh_clear(); return vs
def inside(p):
    """ray parity along +Z and -X; counts hits per object"""
    hits = {}
    for d in (Vector((0, 0, 1)), Vector((0.31, 0.17, 0.93)).normalized()):
        o = p.copy(); n = {}
        for _ in range(40):
            ok, loc, nr, idx, ob, M = sc.ray_cast(dg, o, d)
            if not ok: break
            n[ob.name] = n.get(ob.name, 0) + 1; o = loc + d * 1e-4
        for k, v in n.items():
            if v % 2: hits[k] = hits.get(k, 0) + 1
    return [k for k, v in hits.items() if v == 2 and not k.startswith(("Drop", "Spark", "DustPuff", "DustMote", "FlyDrop", "Tumbler_Water", "Lawn", "BulletWake"))]
rep = {"feet": [], "seat": [], "fingers": [], "camera": [], "bullet": []}
cam = sc.camera
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    for who, shoe, body in (("Woman", "Woman.shoes02", "Woman.body"), ("Fiance", "Fiance.shoes03", "Fiance.body")):
        sv = wverts(shoe)
        for side, sel in (("L", lambda v: v.x > 0), ("R", lambda v: v.x <= 0)):
            pass
        zmin = min(v.z for v in sv)
        if zmin > 0.02 or zmin < -0.015: rep["feet"].append((f, who, round(zmin, 3)))
        bv = wverts(body)
        # fingertips under the table top inside the table footprint
        tb = [v for v in bv if 2.3 < v.x < 4.5 and -0.42 < v.y < 0.42 and TOP - 0.06 < v.z < TOP - 0.004]
        if tb: rep["fingers"].append((f, who, len(tb), round(min(v.z for v in tb) - TOP, 3)))
        # seat contact: lowest body vertex over the seat footprint
        seat_xy = bpy.data.objects["Chair_Woman" if who == "Woman" else "Chair_Fiance"].location
        sv2 = [v for v in bv if (Vector((v.x, v.y)) - seat_xy.to_2d()).length < 0.17 and v.z < SEAT + 0.25]
        if sv2:
            zb = min(v.z for v in sv2)
            if zb < SEAT - 0.03 or zb > SEAT + 0.03: rep["seat"].append((f, who, round(zb - SEAT, 3)))
    b = bpy.data.objects["Bullet"]; bz = min((b.matrix_world @ Vector(c)).z for c in b.bound_box)
    if f > 1300 and (bz < -0.003): rep["bullet"].append((f, round(bz, 4)))
    ins = inside(cam.matrix_world.translation)
    if ins: rep["camera"].append((f, ins[:3]))
for k, v in rep.items():
    print("AUDIT", k, len(v), v[:40])
