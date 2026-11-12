"""Hands pass (STYLE_ANIMATED.md, client 23:00): Limit Rotation (local space) on every finger, thumb and wrist bone,
IK limits on the elbows. Fingers flex about local +X on this rig (checked in close-ups), so no backward bends.
blender -b film.blend --python 06_hands_pass.py -- <out.blend>"""
import sys, math, bpy
OUT = sys.argv[sys.argv.index("--") + 1]
R = math.radians
n = 0
for rn in ("Woman_rig", "Fiance_rig"):
    rig = bpy.data.objects[rn]
    for pb in rig.pose.bones:
        nm = pb.name
        side = nm[-1] if nm[-2:] in (".L", ".R") else None
        if side is None: continue
        zs = 1 if side == "R" else -1
        if nm.startswith("finger") and not nm.startswith("finger1"):
            c = pb.constraints.new("LIMIT_ROTATION"); c.owner_space = "LOCAL"; c.name = "HandLimit"
            c.use_limit_x = c.use_limit_y = c.use_limit_z = True
            c.min_x, c.max_x = R(0), R(100)          # +X = flex toward the palm; no backward bend
            c.min_y, c.max_y = R(-5), R(5)
            c.min_z, c.max_z = R(-10), R(10)         # spread
            n += 1
        elif nm.startswith("finger1"):
            c = pb.constraints.new("LIMIT_ROTATION"); c.owner_space = "LOCAL"; c.name = "HandLimit"
            c.use_limit_x = c.use_limit_y = c.use_limit_z = True
            c.min_x, c.max_x = R(-25), R(45); c.min_y, c.max_y = R(-30), R(30); c.min_z, c.max_z = R(-50), R(50)
            n += 1
        elif nm.startswith("wrist"):
            c = pb.constraints.new("LIMIT_ROTATION"); c.owner_space = "LOCAL"; c.name = "HandLimit"
            c.use_limit_x = c.use_limit_z = True; c.min_x, c.max_x = R(-60), R(60); c.min_z, c.max_z = R(-25), R(25)
            n += 1
        elif nm.startswith("lowerarm01"):
            pb.use_ik_limit_x = True; pb.ik_min_x = R(-150); pb.ik_max_x = R(150)   # elbow: no wrap-around; hinge axis locked elsewhere
# v007: delete MPFB helper geometry (never rendered: hidden by the "Hide helpers" mask) so contact scans only see real surfaces
import bmesh
for bn in ("Woman.body", "Fiance.body"):
    ob = bpy.data.objects[bn]; g = ob.vertex_groups.get("body")
    if g is None: continue
    keep = {v.index for v in ob.data.vertices if any(x.group == g.index and x.weight > 0.5 for x in v.groups)}
    bm = bmesh.new(); bm.from_mesh(ob.data)
    kill = [v for v in bm.verts if v.index not in keep]
    bmesh.ops.delete(bm, geom=kill, context="VERTS"); bm.to_mesh(ob.data); bm.free(); ob.data.update()
    for m in list(ob.modifiers):
        if m.type == "MASK" and m.name == "Hide helpers": ob.modifiers.remove(m)
    print("HELPERS_REMOVED", bn, len(kill), "kept", len(ob.data.vertices))
bpy.context.scene["hands_pass"] = "v007"
print("HAND_LIMITS", n)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
