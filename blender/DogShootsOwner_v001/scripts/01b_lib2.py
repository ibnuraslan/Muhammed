"""Second library pass (director P1 notes): steering wheel, stethoscope, clipboard, shelf, storage and glass cabinets; medics' gloves.
blender -b lib.blend --python 01b_lib2.py -- <glb2_dir> <out_lib.blend>"""
import bpy, sys, math
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]
GLB, OUT = a

def move_to(o, c):
    for uc in list(o.users_collection): uc.objects.unlink(o)
    c.objects.link(o)

def imp(name, path, target_size):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH' and len(o.data.polygons) > 0]
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o not in meshes: bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(meshes) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active; ob.name = name; ob.rotation_mode = 'XYZ'
    if ob.animation_data: ob.animation_data_clear()
    pts = [v.co for v in ob.data.vertices]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    ax, val = target_size; s = val / (mx - mn)["xyz".index(ax)]
    cen = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    ob.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation(-cen)); ob.data.update()
    move_to(ob, bpy.data.collections["PROPS"])
    pts = [v.co for v in ob.data.vertices]
    print("LIB2 prop", name, tuple(round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3)))
    return ob

imp("SteeringWheel", GLB + "/wheel.glb", ("x", 0.40))
imp("Stethoscope", GLB + "/steth.glb", ("y", 0.55))
imp("Clipboard", GLB + "/clip.glb", ("y", 0.32))
imp("Shelf", GLB + "/shelf.glb", ("z", 1.80))
imp("StorageCab", GLB + "/mcab.glb", ("z", 1.85))
imp("GlassCab", GLB + "/medcab.glb", ("z", 1.85))

# blue nitrile gloves on both medics: hand faces of the body mesh get a glove material
glove = bpy.data.materials.new("GloveBlue"); glove.use_nodes = True
p = glove.node_tree.nodes["Principled BSDF"]; p.inputs["Base Color"].default_value = (0.20, 0.42, 0.85, 1); p.inputs["Roughness"].default_value = 0.45
HAND = ("wrist", "finger", "metacarpal")
for rn in ("MedA", "MedB"):
    body = bpy.data.objects[rn + ".body"]
    me = body.data
    gi = {g.index: g.name for g in body.vertex_groups}
    hand_v = set()
    for v in me.vertices:
        tot = 0.0; hw = 0.0
        for g in v.groups:
            n = gi.get(g.group, "")
            if "." not in n or not any(n.startswith(k) for k in ("upperarm", "lowerarm", "wrist", "finger", "metacarpal", "hand", "clavicle", "shoulder", "spine", "neck", "head", "pelvis", "upperleg", "lowerleg", "foot", "toe", "root", "breast")):
                continue
            tot += g.weight
            if any(n.startswith(k) for k in HAND): hw += g.weight
        if tot > 0 and hw / tot > 0.5: hand_v.add(v.index)
    # extend a little up the forearm so the cuff covers the wrist
    me.materials.append(glove); gidx = len(me.materials) - 1
    n = 0
    for poly in me.polygons:
        if sum(1 for vi in poly.vertices if vi in hand_v) >= len(poly.vertices) - 1:
            poly.material_index = gidx; n += 1
    print("LIB2 gloves", rn, "faces", n)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("LIB2_OK")
