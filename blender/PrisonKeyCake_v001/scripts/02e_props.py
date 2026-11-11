# More real props (exec'd after 02d): crucible scan (City of Ballarat), Poly Haven Barrel_01 and Wooden Bucket 01.
MD2 = os.path.join(ROOT, "assets", "models2")
def import_glb2(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]; meshes = [o for o in new if o.type == 'MESH' and len(o.data.vertices) > 100]
    bpy.context.view_layer.update()
    for o in meshes:
        for m in [m for m in o.modifiers if m.type == 'ARMATURE']: o.modifiers.remove(m)
        o.data = o.data.copy(); o.data.transform(o.matrix_world); o.parent = None; o.matrix_world = Matrix.Identity(4)
    for o in new:
        if o not in meshes: bpy.data.objects.remove(o)
    if len(meshes) > 1:
        bpy.ops.object.select_all(action='DESELECT')
        for o in meshes: o.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]; bpy.ops.object.join()
    o = meshes[0]
    for c in o.users_collection: c.objects.unlink(o)
    return o
def fit(me, height, base_center=True):
    vs = [v.co for v in me.vertices]; mn = Vector([min(v[i] for v in vs) for i in range(3)]); mx = Vector([max(v[i] for v in vs) for i in range(3)])
    me.transform(Matrix.Translation(Vector((-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z if base_center else -(mn.z + mx.z) / 2))))
    me.transform(Matrix.Scale(height / (mx.z - mn.z), 4))
# crucible: scanned body replaces the cylinder (centred like the old one), round iron shank
cr = import_glb2(os.path.join(MD2, "crucible.glb")); fit(cr.data, 0.17, base_center=False)
CRo = bpy.data.objects["Crucible"]; old = CRo.data; CRo.data = cr.data; bpy.data.meshes.remove(old); bpy.data.objects.remove(cr)
sh = bpy.data.objects["Crucible_Shank"]; me = bpy.data.meshes.new("Crucible_Shank"); bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.012, radius2=0.012, depth=0.68)
bmesh.ops.rotate(bm, verts=bm.verts, matrix=Matrix.Rotation(R_(90), 3, 'Y')); bmesh.ops.translate(bm, verts=bm.verts, vec=Vector((-0.43, 0, 0)))
bm.to_mesh(me); bm.free(); old = sh.data; sh.data = me; me.materials.append(M_KEY); bpy.data.meshes.remove(old)
for p in me.polygons: p.use_smooth = True
bpy.data.objects["Crucible_Ring"].data.materials[0] = M_KEY
mol = bpy.data.objects["Crucible_Molten"]; mol.scale = (0.72, 0.72, 1.0)
M_MOLTEN.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 14
# barrels (Poly Haven Barrel_01) replace the cylinders; wooden bucket in the cell
_parts = append_obj("wine_barrel_01", c="Props")
bpy.ops.object.select_all(action='DESELECT')
for o in _parts: o.select_set(True)
brl = next(o for o in _parts if o.name == "wine_barrel_01"); bpy.context.view_layer.objects.active = brl; bpy.ops.object.join()
bh = brl.dimensions.z
for o in [o for o in bpy.data.objects if o.name.startswith(("Yard_Barrel", "Shop_Barrel"))]:
    loc = o.location.copy(); col = o.users_collection[0]; nm = o.name
    bpy.data.objects.remove(o)
    n = brl.copy(); n.name = nm; col.objects.link(n); n.location = (loc.x, loc.y, 0); n.rotation_euler = (0, 0, random.uniform(0, 6.28)); n.scale = (0.9 / bh,) * 3
coll("Props").objects.unlink(brl)
bkt = append_obj("wooden_bucket_01", c="Cell")[0]
ob_ = bpy.data.objects["Cell_Bucket"]; bkt.location = (ob_.location.x, ob_.location.y, 0); bpy.data.objects.remove(ob_); bkt.name = "Cell_Bucket"
print("PROPS real: crucible, barrels, bucket")
