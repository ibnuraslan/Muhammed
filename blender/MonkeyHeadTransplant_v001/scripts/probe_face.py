import bpy, sys
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="assets/monkey.glb")
m = [o for o in bpy.data.objects if o.type == "MESH"][0]
M = m.matrix_world.copy(); m.parent = None; m.matrix_world = M
bpy.context.view_layer.objects.active = m; m.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
dg = bpy.context.evaluated_depsgraph_get()
hc = Vector((-0.0662, -0.4204, 0.2510)); s = 0.0004
def ray(px, py, view):
    if view == "front": o = Vector((hc.x + (px-250)*s, -2, hc.z + (250-py)*s)); d = Vector((0,1,0))
    if view == "side":  o = Vector((2, hc.y + (px-250)*s, hc.z + (250-py)*s)); d = Vector((-1,0,0))
    if view == "side2": o = Vector((-2, hc.y - (px-250)*s, hc.z + (250-py)*s)); d = Vector((1,0,0))
    r = bpy.context.scene.ray_cast(dg, o, d)
    return r[1] if r[0] else None
for nm, px, py, v in (("eyeL_front", 160, 220, "front"), ("eyeR_front", 245, 218, "front"), ("eye_side2", 340, 220, "side2"),
                      ("nose", 178, 320, "front"), ("chin", 200, 440, "front"), ("earL", 128, 100, "front"), ("earR", 420, 90, "front"), ("mouth", 190,370,"front")):
    print("P", nm, ray(px, py, v))
# inner corners: scan the front eye row for local depth minima
for px in range(140, 270, 5):
    p = ray(px, 220, "front"); print("ROW", px, None if p is None else tuple(round(x,4) for x in p))
