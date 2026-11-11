import bpy,sys,os
from mathutils import Vector
out=sys.argv[sys.argv.index('--')+1]; broken=len(sys.argv)>sys.argv.index('--')+2
sc=bpy.context.scene
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True
e=w.node_tree.nodes.new('ShaderNodeTexEnvironment'); e.image=bpy.data.images.load(os.path.abspath('assets/ph/hdri/forest_slope_1k.hdr'))
w.node_tree.links.new(e.outputs[0],w.node_tree.nodes['Background'].inputs[0])
sc.view_settings.view_transform='AgX'; sc.view_settings.look='AgX - Medium High Contrast'
if broken:
    bpy.data.objects['Toucan_beak_upper'].hide_render=True; bpy.data.objects['Toucan_beak_upper_broken'].hide_render=False
for o in bpy.data.objects:
    if o.name.startswith('Beak_'): o.hide_render=True
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
sc.render.engine='CYCLES'; sc.cycles.samples=12; sc.render.resolution_x=400; sc.render.resolution_y=400
for i,(loc,tg,lens) in enumerate([((1.0,0.05,0.15),(0,0,0.1),40),((0.5,0.7,0.35),(0,0.05,0.12),40),((0.25,0.3,0.3),(0,0.12,0.23),60)]):
    cam.location=loc; cam.rotation_euler=(Vector(tg)-Vector(loc)).to_track_quat('-Z','Y').to_euler(); cam.data.lens=lens
    sc.render.filepath=out+f'{i}.png'; bpy.ops.render.render(write_still=True)
