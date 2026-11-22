import sys, os, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
out = sys.argv[sys.argv.index("--")+1]; spp = int(sys.argv[sys.argv.index("--")+2])
reset(samples=spp)
world((0.012,0.02,0.035), 1.0)
bpy.ops.mesh.primitive_plane_add(size=400, location=(0,0,-1)); sea = bpy.context.active_object
om = sea.modifiers.new("o", 'OCEAN'); om.geometry_mode='DISPLACE'; om.resolution=12; om.wave_scale=1.2; om.spatial_size=60; om.choppiness=1.2
sea.data.materials.append(mat("Sea", (0.005,0.012,0.02,1), 0.08)); bpy.ops.object.shade_smooth()
rock = noise_bump(color_noise(mat("Rock", rough=0.85), (0.02,0.02,0.02,1), (0.07,0.065,0.06,1), 2), 6, 0.6)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=6, location=(0,0,-4.8)); r=bpy.context.active_object; r.scale=(2.2,1.3,1)
d=r.modifiers.new("d",'DISPLACE'); t=bpy.data.textures.new("n",'CLOUDS'); t.noise_scale=1.5; d.texture=t; d.strength=1.6
r.data.materials.append(rock); bpy.ops.object.shade_smooth()
# the logo stands on the headland like an old cast-iron sign
lg = logo(width=7.0, depth=0.5, loc=(0, 0, 2.6), rot=(math.radians(90),0,math.radians(-4)),
          fill_mat=noise_bump(mat("F", YEL, 0.5), 20, 0.2), edge_mat=mat("E",(0.015,0.015,0.012,1),0.6))
# lighthouse far right on its own rock
white = mat("LH", (0.55,0.55,0.52,1), 0.6); red = mat("LHr", (0.25,0.02,0.02,1), 0.6)
bpy.ops.mesh.primitive_cone_add(radius1=1.6, radius2=1.0, depth=14, location=(44, 40, 7)); lh=bpy.context.active_object; lh.data.materials.append(white)
cyl("Gal", 1.6, 0.4, (44,40,14.2), red); cyl("Lant", 0.9, 1.6, (44,40,15.2), mat("Glass",(1,0.9,0.7,1),0.1, emit=(1,0.85,0.6,1), estr=40))
bpy.ops.mesh.primitive_cone_add(radius1=1.1, radius2=0.1, depth=1.0, location=(44,40,16.5)); bpy.context.active_object.data.materials.append(red)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=7, location=(44,40,-5)); bpy.context.active_object.data.materials.append(rock)
fog("Fog", (200, 200, 40), (0, 20, 19), density=0.004, color=(0.7,0.8,0.95), aniso=0.6, noise=0.04)
# the beam: from the lantern, crossing the bay and landing on the sign
light('SPOT', "Beam", (43.2, 39.3, 15.2), (0, 0, 3.2), energy=1.5e6, color=(1.0,0.88,0.65), spot=4.5, blend=0.3, size=0.6)
light('SPOT', "Beam2", (44.5, 41.0, 15.2), (30, 100, 20), energy=4.0e6, color=(1.0,0.88,0.65), spot=4.5, blend=0.3, size=0.6)
light('SUN', "Moon", (0,0,10), (5,30,-2), energy=0.4, color=(0.6,0.7,1.0))
light('SPOT', 'KeyL', (30, 30, 14), (0, 0, 2.6), energy=2.5e5, color=(1.0,0.88,0.65), spot=6, blend=0.3, size=0.4)
camera((-6, -15, 1.2), (6, 14, 5.5), lens=26)
render(out)
