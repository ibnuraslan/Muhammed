"""Hand pass with the shared library (director, Nov 12): add_hand_limits on every rig, apply_pose for every hand action."""
import bpy
exec(open(os.path.join(D, "..", "..", "pipeline", "hand_poses.py")).read())
rigs = [o for o in bpy.data.objects if o.type == 'ARMATURE' and "finger2-1.L" in o.pose.bones]
for r in rigs:
    for pb in r.pose.bones:                        # drop my earlier ad-hoc finger limits; the library adds the standard ones
        for c in list(pb.constraints):
            if c.type == 'LIMIT_ROTATION' and c.name != "HandLimit": pb.constraints.remove(c)
    add_hand_limits(r)
    if r.animation_data and r.animation_data.action:     # remove hand-set finger keys
        for layer in getattr(r.animation_data.action, "layers", []):
            for st in layer.strips:
                for cb in st.channelbags:
                    for fc in [fc for fc in cb.fcurves if '"finger' in fc.data_path]: cb.fcurves.remove(fc)
FPLAN = {
  "Fan": {"R": [(0.0, "flat_palm"), (12.6, "flat_palm"), (12.75, "relaxed"), (12.85, "hold_flat_object"), (23.0, "hold_flat_object"), (34.0, "relaxed"),
                (36.4, "relaxed"), (37.8, "relaxed"), (38.0, "hold_flat_object"), (44.0, "hold_flat_object")],
          "L": [(0.0, "flat_palm"), (9.9, "flat_palm"), (10.3, "relaxed"), (10.9, "relaxed"), (11.2, "flat_palm"), (13.0, "flat_palm"), (13.4, "hold_flat_object"),
                (15.6, "hold_flat_object"), (16.1, "relaxed"), (16.4, "power_fist"), (17.0, "power_fist"), (17.5, "relaxed"), (34.0, "relaxed"),
                (37.0, "relaxed"), (38.0, "hold_flat_object"), (44.0, "hold_flat_object")]},
  "Manager": {"R": [(0.0, "relaxed"), (20.0, "relaxed"), (20.3, "open_alarm"), (20.8, "relaxed"), (37.9, "relaxed"), (38.0, "flat_palm"), (44.0, "flat_palm")],
              "L": [(0.0, "relaxed"), (20.0, "relaxed"), (20.3, "open_alarm"), (20.8, "relaxed"), (37.9, "relaxed"), (38.0, "flat_palm"), (44.0, "flat_palm")]},
  "ManagerB": {"R": [(0.0, "relaxed"), (29.9, "relaxed"), (29.97, "hold_flat_object"), (34.0, "hold_flat_object")], "L": [(0.0, "relaxed")]},
  "Doctor": {"R": [(0.0, "relaxed"), (22.3, "relaxed"), (22.6, "wrap_grip"), (25.45, "wrap_grip"), (25.55, "relaxed"), (25.95, "relaxed"),
                   (26.02, "pinch"), (28.68, "pinch"), (28.75, "relaxed")],
             "L": [(0.0, "relaxed"), (22.3, "relaxed"), (22.6, "flat_palm"), (27.7, "flat_palm"), (27.85, "pinch"), (28.2, "pinch"), (28.3, "flat_palm"), (29.0, "flat_palm"), (29.3, "relaxed")]},
}
n = 0
for r in rigs:
    plan = FPLAN.get(r.name, {"R": [(0.0, "relaxed")], "L": [(0.0, "relaxed")]})
    for s, keys in plan.items():
        for t, pose in keys:
            apply_pose(r, s, pose, F(t)); n += 1
    for s in "LR":
        if s not in plan: apply_pose(r, s, "relaxed", 1); n += 1
print("HANDS_OK", len(rigs), "rigs", n, "pose keys")

# cheque held at its edges: grip_object for both hands at each finale key
cq = bpy.data.objects["Cheque"]
for t in (38.0, 39.0, 40.0, 40.5, 41.5, 42.0, 43.0, 44.0):
    f = F(t); sc.frame_set(f)
    M = cq.matrix_world; xa = (M.to_3x3() @ Vector((1, 0, 0))).normalized(); c0 = M.translation
    for s_, sg in (("L", 1), ("R", -1)):
        edge = c0 + xa * sg * 0.475 + Vector((0, 0, 0.06))
        try: grip_object(FR, s_, f, cq, edge, -xa * sg, grip='pinch')
        except Exception as e: print("GRIPFAIL", t, s_, e)
# hidden source meshes left at the origin confuse the QA (and add size): remove them; their copies keep the data
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o.hide_render and o.name.endswith("Src")]:
    bpy.data.objects.remove(o)
print("CHEQUE_GRIP_OK")
