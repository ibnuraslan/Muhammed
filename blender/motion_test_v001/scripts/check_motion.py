"""Numerical motion checks (not a substitute for watching the preview).
blender -b anim.blend --python check_motion.py -- <report.json> [step]
Reports per-frame IK reach error, planted-foot drift, hand/bottle relation,
bottle-face clearance and speed profiles of key points.
"""
import sys, json, math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]
STEP = int(argv[1]) if len(argv) > 1 else 1
sc = bpy.context.scene
arm = bpy.data.objects["Farmer"]
PB = arm.pose.bones
bottle = bpy.data.objects.get("Bottle")
rep = {"frames": [], "ik": {}, "pts": {}}
pts = {"pelvis": lambda: PB["root"].head.copy(),
       "head": lambda: PB["head"].tail.copy(),
       "handR": lambda: PB["wrist.R"].head.copy(),
       "handL": lambda: PB["wrist.L"].head.copy(),
       "footL": lambda: PB["foot.L"].head.copy(),
       "footR": lambda: PB["foot.R"].head.copy()}
for k in pts:
    rep["pts"][k] = []
for k in ("legL", "legR", "armL", "armR"):
    rep["ik"][k] = []
rep["bottle"] = []
rep["wrist_in_bottle"] = []
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f)
    rep["frames"].append(f)
    for s in "LR":
        rep["ik"]["leg" + s].append((PB["lowerleg02." + s].tail - PB["IK_foot." + s].head).length)
        rep["ik"]["arm" + s].append((PB["lowerarm02." + s].tail - PB["IK_hand." + s].head).length)
    for k, fn in pts.items():
        rep["pts"][k].append(tuple(fn()))
    if bottle:
        rep["bottle"].append(tuple(bottle.matrix_world.translation))
        rel = bottle.matrix_world.inverted() @ PB["wrist.R"].matrix
        rep["wrist_in_bottle"].append(tuple(rel.translation))
json.dump(rep, open(OUT, "w"))
for k, v in rep["ik"].items():
    worst = max(range(len(v)), key=lambda i: v[i])
    print("IKERR", k, "max %.4f at frame %d" % (v[worst], rep["frames"][worst]),
          "frames>3mm:", [rep["frames"][i] for i in range(len(v)) if v[i] > 0.003][::4])
