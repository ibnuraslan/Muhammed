import sys, os, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
out = sys.argv[sys.argv.index("--")+1]; spp = int(sys.argv[sys.argv.index("--")+2])
reset(samples=spp)
world((0,0,0), 0)
plane("Table", 6, m=noise_bump(color_noise(mat("Steel", rough=0.35, metal=0.7), (0.05,0.05,0.055,1), (0.09,0.09,0.1,1), 30), 80, 0.03, (0.25,0.5)))
# latent print of the logo: fluorescing only where the UV pool lands (emission masked by distance to the pool centre)
fm = mat("Fluo", YEL, 0.6)
nt = fm.node_tree; p = nt.nodes["Principled BSDF"]
p.inputs["Emission Color"].default_value = (0.55,1.0,0.02,1)
tc = nt.nodes.new("ShaderNodeTexCoord"); obj_center = (0.1, 0.05, 0)
vm = nt.nodes.new("ShaderNodeVectorMath"); vm.operation='DISTANCE'; vm.inputs[1].default_value = obj_center
nt.links.new(tc.outputs["Object"] if False else tc.outputs["Generated"], vm.inputs[0])
# world-space distance via a Geometry node instead
geo = nt.nodes.new("ShaderNodeNewGeometry"); nt.links.new(geo.outputs["Position"], vm.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value=0.45; mr.inputs[2].default_value=0.85; mr.inputs[3].default_value=6; mr.inputs[4].default_value=0
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 90; nz.inputs["Detail"].default_value = 4
mul = nt.nodes.new("ShaderNodeMath"); mul.operation='MULTIPLY'
nt.links.new(vm.outputs["Value"], mr.inputs[0]); nt.links.new(mr.outputs[0], mul.inputs[0]); nt.links.new(nz.outputs["Fac"], mul.inputs[1])
nt.links.new(mul.outputs[0], p.inputs["Emission Strength"])
p.inputs["Base Color"].default_value = (0.03,0.03,0.03,1)
lg = logo(width=1.1, depth=0.0005, loc=(0.0, 0.05, 0.0004), rot=(0,0,math.radians(6)), fill_mat=fm, edge_mat=mat("E",(0.01,0.01,0.01,1),0.5), fill_raise=0.0002)
# a smeared glass, keys and an evidence marker on the table
glass = bpy.data.materials.new("Glass"); glass.use_nodes=True; g=glass.node_tree.nodes["Principled BSDF"]; g.inputs["Transmission Weight"].default_value=1; g.inputs["Roughness"].default_value=0.05
cyl("Glass", 0.09, 0.26, (-0.75, 0.45, 0.13), glass)
box("Marker", (0.12, 0.08, 0.1), (0.75, -0.35, 0.05), mat("Mk",(0.6,0.45,0.02,1),0.5), rot=(math.radians(-30),0,math.radians(20)))
text("3", 0.06, (0.75, -0.385, 0.06), (math.radians(60),0,math.radians(20)), mat("Mt",(0.01,0.01,0.01,1),0.5), "/usr/share/fonts/opentype/inter/Inter-Bold.otf")
# the UV torch in a gloved hand's grip, entering from the top right
tm = mat("Torch", (0.02,0.02,0.02,1), 0.3, 0.7)
t = cyl("Torch", 0.045, 0.38, (0.75, 0.55, 0.55), tm, rot=(math.radians(55),0,math.radians(140)))
light('SPOT', "UV", (0.62, 0.41, 0.42), (0.1, 0.05, 0), energy=3000, color=(0.45,0.15,1.0), spot=60, blend=0.5, size=0.02)
cyl("Bezel", 0.05, 0.02, (0.62, 0.41, 0.42), mat("Bz",(0.3,0.1,1,1),0.2, emit=(0.4,0.15,1,1), estr=4), rot=(math.radians(55),0,math.radians(140)))
light('AREA', 'TorchRim', (1.2, 1.0, 0.9), (0.75,0.55,0.55), energy=8, color=(0.6,0.6,1.0), size=0.5)
fog("Air", (4,4,2), (0,0,1), density=0.04, color=(0.8,0.8,1), aniso=0.3)
camera((-0.5, -1.75, 0.85), (0.25, 0.2, 0.2), lens=30, fstop=2.8, focus=1.9)
render(out)
