import bpy,sys,mathutils
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="assets/toucan_scan.glb")
sc=bpy.context.scene
for o in bpy.data.objects:
    if o.type=='MESH':
        bb=[o.matrix_world@mathutils.Vector(c) for c in o.bound_box]
        print(o.name,'min',[round(min(v[i] for v in bb),3) for i in range(3)],'max',[round(max(v[i] for v in bb),3) for i in range(3)], o.parent.name if o.parent else None)
o3=bpy.data.objects['Object_3']; o3.hide_render=True
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.location=(0.76,0.6,0.42)
t=mathutils.Vector((0.76,1.59,0.42)); cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.lens=40
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[1].default_value=1.0
sc.render.engine='CYCLES'; sc.cycles.samples=8; sc.render.resolution_x=800; sc.render.resolution_y=500
sc.render.filepath=sys.argv[-1]; bpy.ops.render.render(write_still=True)
