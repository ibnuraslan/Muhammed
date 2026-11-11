import bpy, sys, math
from mathutils import Vector
out = sys.argv[sys.argv.index("--")+1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="assets/monkey.glb")
m = [o for o in bpy.data.objects if o.type == "MESH"][0]
M = m.matrix_world.copy(); m.parent = None; m.matrix_world = M
bpy.context.view_layer.objects.active = m; m.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
vs = [v.co for v in m.data.vertices]
mn = Vector([min(v[i] for v in vs) for i in range(3)]); mx = Vector([max(v[i] for v in vs) for i in range(3)])
print("BB", mn, mx)
# front-most point of the head (face direction?) : find which way the face looks: highest verts
top = [v for v in vs if v.z > mx.z - 0.12]
c = sum(top, Vector()) / len(top); print("HEADTOP centroid", c, "n", len(top))
print("head minY", min(v.y for v in top), "maxY", max(v.y for v in top), "minX", min(v.x for v in top), "maxX", max(v.x for v in top))
sc = bpy.context.scene
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = 0.2
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.8,0.8,0.8,1); w.node_tree.nodes["Background"].inputs[1].default_value = 1.5
sc.render.engine = "CYCLES"; sc.cycles.samples = 8; sc.render.resolution_x = 500; sc.render.resolution_y = 500
sc.render.image_settings.file_format = "PNG"
hc = Vector((c.x, c.y, mx.z - 0.08))
for nm, d in (("front", Vector((0, -1, 0))), ("side", Vector((1, 0, 0))), ("side2", Vector((-1,0,0))), ("back", Vector((0,1,0)))):
    cam.location = hc + d * 1.0
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = f"{out}_{nm}.png"; bpy.ops.render.render(write_still=True)
print("HC", hc)
