import bpy,sys
for n in sys.argv[sys.argv.index('--')+1:]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=f"assets/{n}.glb")
    for o in bpy.data.objects:
        if o.type in('MESH','ARMATURE'):
            print(n,o.name,o.type,len(o.data.polygons) if o.type=='MESH' else len(o.data.bones),[round(x,3) for x in o.dimensions],[m.name for m in o.data.materials] if o.type=='MESH' else '')
    print(n,'imgs',[(i.name,i.size[:]) for i in bpy.data.images],'anims',[a.name for a in bpy.data.actions])
