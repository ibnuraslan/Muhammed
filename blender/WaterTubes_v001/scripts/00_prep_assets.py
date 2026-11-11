"""Import the CC-BY GLBs, join each into one object, scale to real size, origin at bottom centre, save asset library.
blender -b --factory-startup --python 00_prep_assets.py -- <models_dir> <out.blend> [preview_dir]"""
import bpy, sys, os, math
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]
MD, OUT = a[0], a[1]; PV = a[2] if len(a) > 2 else None
# name: (size metres, measured along 'h' height / 'w' max horizontal)
T = {"hero_house": (12.5, "w"), "house_a": (12.0, "w"), "house_b": (13.0, "w"), "house_c": (15.0, "w"),
     "house_d": (12.0, "w"), "house_e": (12.0, "w"), "car": (5.0, "w"), "bin": (1.05, "h"), "fence": (1.5, "h"),
     "sofa": (2.0, "w"), "hose": (0.75, "h")}
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob)
lib = []
DROP = ("edge_color", "Snow", "M_Dome", "Grass_Dark_Green", "M_Badge")
for name, (size, mode) in T.items():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(MD, name + ".glb"))
    new = [o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    ms = [o for o in new if o.type == "MESH"]
    for o in ms:
        M = o.matrix_world.copy(); o.parent = None; o.matrix_world = M
    for o in new:
        if o.type != "MESH": bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in ms: o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]
    for o in ms:
        if o.data.users > 1: o.data = o.data.copy()
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(ms) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active; ob.name = ob.data.name = name
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bad = {i for i, m in enumerate(ob.data.materials) if m and any(k in m.name for k in DROP)}
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in bad], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(ob.data); bm.free()
    for m in ob.data.materials:
        if m and "Glass" not in m.name and "Translucent" not in m.name and hasattr(m, "blend_method"): m.blend_method = "OPAQUE"
        if m and m.node_tree:
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED" and "Glass" not in m.name and "Translucent" not in m.name:
                    for l in list(n.inputs["Alpha"].links): m.node_tree.links.remove(l)
                    n.inputs["Alpha"].default_value = 1.0
    vs = [v.co for v in ob.data.vertices]
    mn = Vector([min(v[i] for v in vs) for i in range(3)]); mx = Vector([max(v[i] for v in vs) for i in range(3)])
    d = mx - mn; s = size / (d.z if mode == "h" else max(d.x, d.y))
    c = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    ob.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation(-c)); ob.data.update()
    ob.location = (0, 0, 0)
    print("ASSET", name, "dims", tuple(round(x * s, 2) for x in d), "faces", len(ob.data.polygons))
    lib.append(ob)
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
if PV:
    os.makedirs(PV, exist_ok=True)
    sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.samples = 8
    sc.render.resolution_x = sc.render.resolution_y = 300
    w = bpy.data.worlds.new("w"); sc.world = w; w.color = (0.8, 0.8, 0.8)
    cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
    sun = bpy.data.objects.new("s", bpy.data.lights.new("s", "SUN")); sc.collection.objects.link(sun); sun.rotation_euler = (0.7, 0.2, 0.5)
    for ob in lib: ob.hide_render = True
    for ob in lib:
        ob.hide_render = False
        dm = max(ob.dimensions); cam.location = Vector((dm * 0.6, -dm * 1.6, dm * 0.7))
        cam.rotation_euler = (Vector((0, 0, ob.dimensions.z * 0.4)) - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(PV, ob.name + ".jpg"); sc.render.image_settings.file_format = "JPEG"
        bpy.ops.render.render(write_still=True); ob.hide_render = True
