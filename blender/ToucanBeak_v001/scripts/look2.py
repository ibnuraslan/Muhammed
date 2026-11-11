import bpy,sys,mathutils
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="assets/toucan_b.glb")
sc=bpy.context.scene
o=[o for o in bpy.data.objects if o.type=='MESH'][0]
bb=[o.matrix_world@mathutils.Vector(c) for c in o.bound_box]
mn=[min(v[i] for v in bb) for i in range(3)]; mx=[max(v[i] for v in bb) for i in range(3)]
print('BB',mn,mx)
c=mathutils.Vector([(a+b)/2 for a,b in zip(mn,mx)]); r=max(b-a for a,b in zip(mn,mx))
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
for i,d in enumerate([(1,0,0),(0,-1,0),(-0.7,-0.7,0.3)]):
    cam.location=c+mathutils.Vector(d)*r*1.8
    cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler()
    w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[1].default_value=1.5
    sc.render.engine='CYCLES'; sc.cycles.samples=8; sc.render.resolution_x=500; sc.render.resolution_y=500
    sc.render.filepath=sys.argv[-1]+f"{i}.png"; bpy.ops.render.render(write_still=True)
