import bpy, sys, os, glob
from mathutils import Vector
A = sys.argv[sys.argv.index("--")+1]
for f in sorted(glob.glob(A+"/*.glb")):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=f)
    obs = bpy.data.objects
    ms = [o for o in obs if o.type=='MESH']
    pts = [o.matrix_world @ Vector(c) for o in ms for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    arm = [o for o in obs if o.type=='ARMATURE']
    print("ASSET", os.path.basename(f), "meshes", len(ms), "faces", sum(len(o.data.polygons) for o in ms), "size", tuple(round(x,3) for x in hi-lo), "min", tuple(round(x,2) for x in lo),
          "arm", [(a.name, len(a.data.bones)) for a in arm], "actions", [(a.name, tuple(a.frame_range)) for a in bpy.data.actions][:6],
          "mats", [m.name for m in bpy.data.materials][:8], "shapekeys", [o.name for o in ms if o.data.shape_keys][:3])
