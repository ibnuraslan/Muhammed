# from ScaldingCoffee_v001 (Connect B09)
"""blender -b f --python bpc_run.py -- out.json step f0 f1 Prop/Empty,... Rig,...  (empties expand to their mesh descendants)"""
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]
out, step, f0, f1, props, rigs = a[0], a[1], int(a[2]), int(a[3]), a[4].split(","), a[5].split(",")
names = []
for n in props:
    o = bpy.data.objects.get(n)
    if o is None: print("BPC_MISSING", n); continue
    if o.type == 'MESH': names.append(o.name)
    names += [c.name for c in o.children_recursive if c.type == 'MESH']
rn = [r.name for r in bpy.data.objects if r.type == 'ARMATURE' and any(r.name == x or r.name.startswith(x) for x in rigs)]
sc = bpy.context.scene; sc.frame_start, sc.frame_end = f0, f1; sc.frame_set(f0)
print("BPC_PROPS", len(names), "RIGS", rn)
sys.argv = [sys.argv[0], "--", out, step, ",".join(sorted(set(names))), ",".join(rn)]
exec(open("/home/user/Muhammed/blender/pipeline/body_prop_cross.py").read())
