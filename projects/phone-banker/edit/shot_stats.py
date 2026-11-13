"""Profile one baked shot file: python edit/shot_stats.py <file.blend>  -> one JSON line on stdout (prefix [stats]).
Size, packed image bytes, vertex count, the heaviest meshes, keyframe count, and peak RAM (maxrss) after opening."""
import os, sys, json, resource
import bpy
f = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=f)
dg = bpy.context.evaluated_depsgraph_get()                       # what the renderer will build (modifiers evaluated)
ev = 0
for o in bpy.context.scene.objects:
    if o.type == 'MESH':
        try:
            ev += len(o.evaluated_get(dg).data.vertices)
        except Exception:
            pass
meshes = sorted(((m.name, len(m.vertices), m.users) for m in bpy.data.meshes), key=lambda x: -x[1])
keys = 0
for a in bpy.data.actions:
    for fc in getattr(a, "fcurves", []) or []:
        keys += len(fc.keyframe_points)
    for layer in getattr(a, "layers", []) or []:
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []) or []:
                for fc in cb.fcurves:
                    keys += len(fc.keyframe_points)
ims = [i for i in bpy.data.images if i.packed_file]
out = dict(file=os.path.basename(f), mb=round(os.path.getsize(f) / 2**20, 1), packed_mb=round(sum(i.packed_file.size for i in ims) / 2**20, 1),
           images=len(ims), big_images=sum(1 for i in ims if max(i.size) > 2048), verts=sum(x[1] for x in meshes), eval_verts=ev,
           top=meshes[:5], keys=keys, maxrss_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024))
print("[stats]", json.dumps(out), flush=True)
