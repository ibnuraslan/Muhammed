"""v012b (client F, list 35): the man sat INTO the bench and sank UNDER the mattress. For each frame of the bench (1291-1476) and
bed (1478-1586) ranges the lowest body/clothes vertex inside the surface footprint is compared with the surface height (bench seat
from a ray cast under his hips; mattress top), and his root is raised by the shortfall (smoothed over 9 frames), so he sits ON
the seat and lies ON the mattress. blender -b in.blend --python plant_man.py -- out.blend"""
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; vl = bpy.context.view_layer
M = bpy.data.objects["Man"]; parts = [bpy.data.objects["Man_Body"], bpy.data.objects["Man_male_casualsuit06"]]
saved = [(m, m.show_viewport) for b in parts for m in b.modifiers if m.type == "SUBSURF" or (m.type == "MASK" and (m.vertex_group or "").startswith("Delete"))]   # helpers stay hidden
for m, _ in saved: m.show_viewport = False
def W(n): return M.matrix_world @ M.pose.bones[n].head
def footprint(o):
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]; return min(v.x for v in bb), max(v.x for v in bb), min(v.y for v in bb), max(v.y for v in bb), max(v.z for v in bb)
def need(f, surf, kind):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    x0, x1, y0, y1, ztop = footprint(surf)
    if kind == "bench":
        hip = (W("pelvis.L") + W("pelvis.R")) / 2
        hit, loc, n, i, ob, _ = sc.ray_cast(dg, hip + Vector((0, 0, 0.6)), Vector((0, 0, -1)))
        # first hit may be his own body: walk down through hits until the bench
        o_ = hip + Vector((0, 0, 0.6)); z = None
        for _ in range(8):
            hit, loc, n, i, ob, _ = sc.ray_cast(dg, o_, Vector((0, 0, -1)))
            if not hit: break
            if ob.name == surf.name and n.z > 0.7: z = loc.z; break   # the seat top (his hips may already be inside it)
            o_ = loc + Vector((0, 0, -0.002))
        if z is None: return 0.0
        ztop = z; rad = 0.12; cx, cy = hip.x, hip.y
    back = [W(n) for n in ("spine05", "spine04", "spine03", "spine02", "spine01", "neck01", "head")] if kind == "bed" else []
    lo = 9.0
    for b in parts:
        e = b.evaluated_get(dg); me = e.to_mesh(); mw = e.matrix_world
        for v in me.vertices:
            p = mw @ v.co
            if kind == "bench":
                if (p.x - cx) ** 2 + (p.y - cy) ** 2 > rad * rad or not (ztop - 0.28 < p.z < ztop + 0.12): continue
            elif not (x0 < p.x < x1 and y0 < p.y < y1) or min((p - c).length for c in back) > 0.16: continue   # back/shoulders/hips only, not the blanketed legs
            lo = min(lo, p.z)
        e.to_mesh_clear()
    return min(0.25, max(0.0, ztop + 0.006 - lo)) if lo < 9 else 0.0   # sanity clamp
root = M.pose.bones["root"]
TO_LOC = (M.matrix_world.to_3x3() @ root.bone.matrix_local.to_3x3()).inverted()   # world delta -> root.location delta (root has no parent)
def fcs():
    out = {}
    for l in M.animation_data.action.layers:
        for st in l.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    if fc.data_path == 'pose.bones["root"].location': out[fc.array_index] = fc
    return out
def chans(ob):
    ad = ob.animation_data
    if not ad or not ad.action: return []
    return [fc for l in ad.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
def shift(fcl, f0, f1, sm, vec_of):
    """raise the keyed world position of a channel group over [f0, f1] by sm (world z); keys pinned at the range ends first"""
    fr = sorted(sm)
    def dz(f): return sm[min(fr, key=lambda g: abs(g - f))]
    by = {fc.array_index: fc for fc in fcl}
    if len(by) < 3: return 0
    for f in (f0, f1):
        vals = [by[i].evaluate(f) for i in range(3)]
        for i in range(3): by[i].keyframe_points.insert(f, vals[i], options={"FAST"})
    n = 0
    for i in range(3):
        for k in by[i].keyframe_points:
            if f0 <= k.co.x <= f1:
                d = vec_of(dz(k.co.x))[i]; k.co.y += d; k.handle_left.y += d; k.handle_right.y += d; n += 1
        by[i].update()
    return n
def carry(f0, f1, sm):
    """his hands, the props in them and the camera were keyed in world space: they rise with him"""
    tot = 0
    for b in ("IK_hand.L", "IK_hand.R", "Pole_elbow.L", "Pole_elbow.R"):
        pb = M.pose.bones[b]; T = (M.matrix_world.to_3x3() @ pb.bone.matrix_local.to_3x3()).inverted()
        tot += shift([fc for fc in chans(M) if fc.data_path == 'pose.bones["%s"].location' % b], f0, f1, sm, lambda z, T=T: T @ Vector((0, 0, z)))
    for on in ("Prop_Tissue", "Prop_Inhaler", "CAM_Film", "CAM_Film_Aim"):
        ob = bpy.data.objects.get(on)
        if ob and not ob.parent:
            tot += shift([fc for fc in chans(ob) if fc.data_path == "location"], f0, f1, sm, lambda z: Vector((0, 0, z)))
    print("CARRY", f0, f1, "keys moved", tot)
for name, kind, f0, f1 in (("painted_wooden_bench", "bench", 1292, 1476), ("BR_Mattress", "bed", 1478, 1586)):
    surf = bpy.data.objects[name]
    raw = {}
    for f in range(f0, f1 + 1, 2):
        sc.frame_set(f); p = W("pelvis.L"); x0, x1, y0, y1, _ = footprint(surf)
        if x0 - 0.3 < p.x < x1 + 0.3 and y0 - 0.3 < p.y < y1 + 0.3: raw[f] = need(f, surf, kind)   # only frames where he is at this prop
    fr = sorted(raw)
    sm = {f: max(raw[g] for g in fr if abs(g - f) <= 8) for f in fr}         # hold the max over +-8 frames: no bobbing
    F = fcs(); new = {}
    for f in fr:
        d = TO_LOC @ Vector((0, 0, sm[f])); new[f] = [F[i].evaluate(f) + d[i] for i in range(3)]
    for f in fr:
        for i in range(3): F[i].keyframe_points.insert(f, new[f][i], options={"FAST"})
    for i in range(3): F[i].update()
    carry(f0, f1, sm)
    print("PLANT", name, "frames", fr[0], fr[-1], "max raise %.1f cm" % (max(sm.values()) * 100), "mean %.1f cm" % (sum(sm.values()) / len(sm) * 100))
for m, v in saved: m.show_viewport = v
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
