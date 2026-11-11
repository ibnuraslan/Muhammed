# Real models replace procedural stand-ins (exec'd at the end of 02_build_scene.py):
# key (Old Key, Meerschaum Digital), lock (Pocket Door Lock scan, IU Indianapolis University Library),
# cake (Christmas Panettone scan, alban), government building (Prefettura di Trieste, Karpulya). All CC-BY via Objaverse.
from mathutils.bvhtree import BVHTree
MD = os.path.join(ROOT, "assets", "models")
def import_glb(name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(MD, name + ".glb"))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    bpy.context.view_layer.update()
    for o in meshes:
        o.data = o.data.copy() if o.data.users > 1 else o.data
        o.data.transform(o.matrix_world); o.parent = None; o.matrix_world = Matrix.Identity(4)
    for o in new:
        if o.type != 'MESH': bpy.data.objects.remove(o)
    if len(meshes) > 1:
        bpy.ops.object.select_all(action='DESELECT')
        for o in meshes: o.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]; bpy.ops.object.join()
    o = meshes[0]
    for c in o.users_collection: c.objects.unlink(o)
    return o
# ---------------- key: map Old Key axes onto our key convention (x bow->bit, y bit side, z thickness)
k = import_glb("key2")
S_K = 0.145 / 762.1
k.data.transform(Matrix(((-S_K, 0, 0, 0), (0, 0, S_K, 0), (0, S_K, 0, 0), (0, 0, 0, 1))))
for p in k.data.polygons: p.use_smooth = True
for nm in ("Key_Master", "Key_Copy1", "Key_Copy2", "Key_Casting"):
    o = bpy.data.objects[nm]; old = o.data; mats = list(old.materials)
    o.data = k.data.copy()
    if nm == "Key_Casting": o.data.materials[0] = mats[0]
    bpy.data.meshes.remove(old)
bpy.data.objects.remove(k)
# wax imprint re-cast from the real key's silhouette (ray cast down onto the key, key-local)
kb = BVHTree.FromPolygons([v.co for v in bpy.data.objects["Key_Master"].data.vertices], [p.vertices for p in bpy.data.objects["Key_Master"].data.polygons])
for wn in ("WaxPool", "WaxMold_Pocket"):
    w = bpy.data.objects[wn]; base = w.data.shape_keys.key_blocks["Basis"]; imp = w.data.shape_keys.key_blocks["Imprint"]
    for i, v in enumerate(base.data):
        x, y = v.co.x, v.co.y
        dmin = 9.0
        for dx, dy in ((0, 0), (0.0012, 0), (-0.0012, 0), (0, 0.0012), (0, -0.0012)):
            h = kb.ray_cast(Vector((x + dx, y + dy, 1.0)), Vector((0, 0, -1)))
            if h[0] is not None: dmin = 0.0 if (dx, dy) == (0, 0) else min(dmin, 0.5)
        s_ = 1.0 if dmin == 0.0 else (0.45 if dmin == 0.5 else 0.0)
        imp.data[i].co = Vector((v.co.x, v.co.y, v.co.z - 0.0042 * s_))
# ---------------- lock: real mortise lock on the inside face of the cell door, keyhole on LOCK_C
lk_old = [bpy.data.objects[n] for n in ("CellLock", "CellLock_Keyhole")]
lkm = import_glb("lock")
S_L = 0.2 / 408.7
KH = Vector((-6.0, -678.4, -38.0))                     # keyhole on the model's -Y face (model units)
lkm.data.transform(Matrix.Translation(-KH)); lkm.data.transform(Matrix.Scale(S_L, 4)); lkm.data.transform(Matrix.Rotation(R_(-90), 4, 'Z'))
coll("Cell").objects.link(lkm); lkm.name = "CellLock"
for o in lk_old: bpy.data.objects.remove(o)
bpy.context.view_layer.update()
lkm.location = Vector((LOCK_C.x - 0.026, LOCK_C.y, LOCK_C.z - 0.004))
lkm.parent = door_piv; lkm.matrix_parent_inverse = door_piv.matrix_world.inverted()
bolt.data.materials[0] = M_KEY; bolt.modifiers.new("bev", 'BEVEL').width = 0.003
# ---------------- cake: panettone scan, whole (Cake1) and cut (Cake2_Main + Cake2_Slice)
cm_ = import_glb("cake")
vs = [v.co for v in cm_.data.vertices]; mn = Vector([min(v[i] for v in vs) for i in range(3)]); mx = Vector([max(v[i] for v in vs) for i in range(3)])
cm_.data.transform(Matrix.Translation(Vector((-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z))))
cm_.data.transform(Matrix.Scale(0.24 / max(mx.x - mn.x, mx.y - mn.y), 4))
cm_.data.materials.append(M_FC); CRUMB_I = len(cm_.data.materials) - 1
def cut(me_src, planes, name, coll_name, loc):
    me = me_src.copy(); bm = bmesh.new(); bm.from_mesh(me)
    for (co, no) in planes:
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        r = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no, clear_outer=True)
        edges = [e for e in r['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
        if edges:
            nf = bmesh.ops.holes_fill(bm, edges=edges, sides=0)
            for f in nf['faces']: f.material_index = CRUMB_I
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); coll(coll_name).objects.link(o); o.location = loc; return o
for n in ("Cake1", "Cake2_Main", "Cake2_Slice"):
    if bpy.data.objects.get(n): bpy.data.objects.remove(bpy.data.objects[n])
o1 = bpy.data.objects.new("Cake1", cm_.data.copy()); coll("Foundry").objects.link(o1); o1.location = loc1
def nrm(a): return Vector((math.cos(R_(a)), math.sin(R_(a)), 0))
a0, a1 = SL
n0 = Vector((math.sin(R_(a0)), -math.cos(R_(a0)), 0)); n1 = Vector((-math.sin(R_(a1)), math.cos(R_(a1)), 0))   # outward normals of the wedge sides
C0 = Vector((0, 0, 0))
cut(cm_.data, [(C0, n0), (C0, n1)], "Cake2_Slice", "Cell", CAKE2_P)          # inside both planes = the wedge
pa = cut(cm_.data, [(C0, -n0)], "Cake2_MainA", "Cell", CAKE2_P)
pb = cut(cm_.data, [(C0, -n1), (C0, n0)], "Cake2_MainB", "Cell", CAKE2_P)
bpy.ops.object.select_all(action='DESELECT'); pa.select_set(True); pb.select_set(True); bpy.context.view_layer.objects.active = pa
bpy.ops.object.join(); pa.name = "Cake2_Main"
bpy.data.objects.remove(cm_)
# ---------------- government building: Prefettura di Trieste behind the steps, entrance portal on the axis
for o in [o for o in bpy.data.objects if o.name.startswith(("Gov_Column", "Gov_ColBase", "Gov_Entablature", "Gov_Pediment", "Gov_Facade", "Gov_Door", "Gov_Win", "Gov_Wing", "Town"))]:
    bpy.data.objects.remove(o)
bd = import_glb("building"); coll("Gov").objects.link(bd); bd.name = "Gov_Building"
S_B = 0.75
bd.data.transform(Matrix.Scale(S_B, 4)); bd.data.transform(Matrix.Rotation(R_(90), 4, 'Z'))
portal = Matrix.Rotation(R_(90), 4, 'Z') @ (Vector((-49.72, 38.4, 0)) * S_B)
bd.location = Vector((0, GY + 5.9, TOPZ)) - portal
bpy.context.view_layer.update()
vs = [bd.matrix_world @ v.co for v in bd.data.vertices]
bmn = Vector([min(v[i] for v in vs) for i in range(3)]); bmx = Vector([max(v[i] for v in vs) for i in range(3)])
box("Gov_Plinth", (bmn.x - 0.3, GY + 5.6, 0), (bmx.x + 0.3, bmx.y + 0.3, TOPZ + 0.02), M_SANDST, c="Gov", bevel=0.03)
print("REAL models in: key, lock, cake, building", tuple(round(x, 1) for x in bmn), tuple(round(x, 1) for x in bmx))
