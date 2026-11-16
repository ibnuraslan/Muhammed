import bpy, math, sys
from mathutils import Vector, Quaternion, Euler
out=sys.argv[-1]; sc=bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.samples=8; sc.render.resolution_x=900; sc.render.resolution_y=500
w=bpy.data.worlds.new("w"); sc.world=w; w.use_nodes=True; w.node_tree.nodes["Background"].inputs[0].default_value=(0.7,0.8,0.9,1)
bpy.ops.mesh.primitive_plane_add(size=20)
L=bpy.data.objects.new("l",bpy.data.lights.new("l","SUN")); sc.collection.objects.link(L); L.rotation_euler=(0.6,0.3,0.5); L.data.energy=3
cam=bpy.data.objects.new("c",bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera=cam
rig=bpy.data.objects["Croc"]
def shot(loc,tgt,fn):
    cam.location=loc; cam.rotation_euler=(Vector(tgt)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=fn; bpy.ops.render.render(write_still=True)
shot((3.2,-2.6,1.6),(0,0.2,0.2),out+"_a.png")
shot((0,0.3,6),(0,0.3,0),out+"_top.png")
pb=rig.pose.bones
for i in range(1,9): pb["tail%d"%i].rotation_quaternion=Quaternion((0,0,1),math.radians(12*math.sin(i*0.8)))
pb["neck"].rotation_quaternion=Quaternion((1,0,0),math.radians(15))
pb["FL_up"].rotation_quaternion=Quaternion((0,0,1),math.radians(30))
shot((3.2,-2.6,1.6),(0,0.2,0.2),out+"_b.png")
