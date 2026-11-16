"""Fingertip pinch helpers measured on the deformed skin (not the bones): the prop sits in the gap between the pads."""
_PADV = {}

def _pad_verts(rig, s):
    key = (rig.name, s)
    if key in _PADV: return _PADV[key]
    body = next(o for o in rig.children if o.type == 'MESH' and o.name.lower().endswith("body"))
    out = {}
    for gname, tag in (("finger2-3." + s, "index"), ("finger1-3." + s, "thumb")):
        g = body.vertex_groups.get(gname); idx = []
        for v in body.data.vertices:
            for ge in v.groups:
                if ge.group == g.index and ge.weight > 0.6: idx.append(v.index)
        out[tag] = idx
    _PADV[key] = (body, out); return _PADV[key]

def skin_coords(body):
    saved = []
    for m in body.modifiers:
        if m.type in ('MASK', 'SUBSURF') and m.show_viewport: saved.append(m); m.show_viewport = False
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    be = body.evaluated_get(dg); me = be.to_mesh(); Mw = be.matrix_world
    co = [Mw @ v.co for v in me.vertices]; be.to_mesh_clear()
    for m in saved: m.show_viewport = True
    return co

def pads(rig, s, f):
    """returns (P = midpoint of the closest index/thumb pad vertices, gap (m), axis index->thumb unit)"""
    sc.frame_set(int(f)); bpy.context.view_layer.update()
    body, ids = _pad_verts(rig, s); co = skin_coords(body)
    I = [co[i] for i in ids["index"]]; T = [co[i] for i in ids["thumb"]]
    best = None
    for a in I:
        for b in T:
            d = (a - b).length
            if best is None or d < best[0]: best = (d, a, b)
    d, a, b = best
    return (a + b) / 2, d, (b - a).normalized() if d > 1e-6 else Vector((0, 0, 1))

def pinch_at(rig, s, f, P, finger_dir, palm_normal, gap=0.003, pose="pinch"):
    """key IK_hand + a pinch so the pad gap is about `gap` and its midpoint sits on world point P. Returns the pad axis."""
    place_hand(rig, s, f, Vector(P) - Vector(finger_dir).normalized() * 0.07, palm_normal, finger_dir)
    apply_pose(rig, s, "relaxed", f)
    lo, hi = 0.3, 1.0; u = 1.0
    for it in range(7):     # bisection on the pinch amount for the wanted pad gap
        apply_pose(rig, s, "relaxed", f); apply_pose(rig, s, pose, f, amount=u)
        Q, g, ax = pads(rig, s, f)
        if abs(g - gap) < 0.0006: break
        if g < gap: hi = u
        else: lo = u
        u = (lo + hi) / 2
    for it in range(8):     # move the hand so the pinch midpoint lands on P
        Q, g, ax = pads(rig, s, f)
        if (Q - Vector(P)).length < 0.0004: break
        pb = rig.pose.bones["IK_hand." + s]
        delta = rig.matrix_world.inverted().to_3x3() @ (Vector(P) - Q)
        pb.location = pb.location + rig.data.bones["IK_hand." + s].matrix_local.to_3x3().inverted() @ delta
        pb.keyframe_insert("location", frame=f, group=pb.name)
    Q, g, ax = pads(rig, s, f)
    print("PINCH", rig.name, s, f, "gap %.1fmm err %.1fmm" % (g * 1000, (Q - Vector(P)).length * 1000))
    global LAST_Q
    LAST_Q = Q.copy()
    return ax, g

def parent_to_bone(obj, rig, bone, f):
    """rigid bone parent, keeping the object's current world matrix at frame f"""
    sc.frame_set(int(f)); bpy.context.view_layer.update()
    mw = obj.matrix_world.copy()
    obj.parent = rig; obj.parent_type = 'BONE'; obj.parent_bone = bone
    bpy.context.view_layer.update()
    obj.matrix_world = mw
    bpy.context.view_layer.update()

def frame_from(x, z_hint):
    """rotation matrix with local X = x, local Y ~ perpendicular, local Z close to z_hint"""
    x = Vector(x).normalized(); z = Vector(z_hint); z = (z - x * z.dot(x)).normalized(); y = z.cross(x)
    return Matrix((x, y, z)).transposed()
