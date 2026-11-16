"""dump EarInArm Patient/Surgeon local pose (FK basis incl. IK result) + chair state at given frames -> json"""
import bpy, sys, json
a = sys.argv[sys.argv.index("--") + 1:]; out = a[0]; frames = [int(x) for x in a[1].split(",")]
sc = bpy.context.scene; res = {}
for f in frames:
    sc.frame_set(f); d = {}
    for rn in ("Patient", "Surgeon"):
        rig = bpy.data.objects[rn]; P = {}
        for pb in rig.pose.bones:
            if pb.name.startswith(("IK_", "Pole_")): continue
            M = rig.convert_space(pose_bone=pb, matrix=pb.matrix, from_space='POSE', to_space='LOCAL')
            l, q, s = M.decompose(); P[pb.name] = [list(l), list(q)]
        d[rn] = dict(pose=P, mw=[list(r) for r in rig.matrix_world])
    objs = {}
    for o in bpy.data.objects:
        if o.type in ('MESH', 'EMPTY', 'LIGHT', 'CURVE') and not (o.parent and o.parent.type == 'ARMATURE'):
            objs[o.name] = [list(r) for r in o.matrix_world]
    d["objs"] = objs; res[f] = d
json.dump(res, open(out, "w"))
