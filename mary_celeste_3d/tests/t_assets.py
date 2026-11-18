"""Contact sheet of downloaded Sketchfab assets: each normalised, lit, rendered from 3/4."""
import sys, os, glob, math; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import common as C
C.reset()
import bpy
from mathutils import Vector
sc = C.render_setup(samples=32, noise=0.05); sc.render.resolution_x = 640; sc.render.resolution_y = 640; sc.render.resolution_percentage = 100
import sea; sea.sky(strength=0.8, rot_deg=240)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 2.5; sun.rotation_euler = (0.9, 0, -0.6)
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "sketchfab")
out = os.environ["OUT"]
for f in sorted(glob.glob(D + "/*.glb")):
    for o in list(bpy.data.objects):
        if o.type not in ('LIGHT',):
            bpy.data.objects.remove(o)
    bpy.ops.import_scene.gltf(filepath=f)
    ms = [o for o in bpy.data.objects if o.type == 'MESH']
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in ms for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    c = (lo + hi) / 2; r = (hi - lo).length / 2
    print("ASSET", os.path.basename(f), "dims", tuple(round(v, 3) for v in (hi - lo)), "meshes", len(ms),
          "arm", [o.name for o in bpy.data.objects if o.type == 'ARMATURE'][:2])
    C.camera(c + Vector((r * 1.6, -r * 2.2, r * 0.6)), c, lens=50)
    sc.render.filepath = out + "_" + os.path.basename(f)[:8] + ".png"; bpy.ops.render.render(write_still=True)
