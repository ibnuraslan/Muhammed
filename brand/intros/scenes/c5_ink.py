import sys, os, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
out = sys.argv[sys.argv.index("--")+1]; spp = int(sys.argv[sys.argv.index("--")+2])
reset(samples=spp)
world((0,0,0), 0)
lg = logo(width=4.0, depth=0.25, loc=(0, 0, 0), fill_mat=mat("F", YEL, 0.4), edge_mat=mat("E",(0.015,0.015,0.012,1),0.4))
# pigment cloud: a volume domain whose density is noise, densest around the letters and thinning upward (still settling)
def ink(name, dims, loc, dens, scale, col):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=loc); o = bpy.context.active_object; o.scale = dims
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
    v = nt.nodes.new("ShaderNodeVolumePrincipled"); v.inputs["Color"].default_value = col
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 1.2; wv.inputs["Distortion"].default_value = 9; wv.inputs["Detail"].default_value = 6; wv.wave_type='RINGS'
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = 8; n.inputs["Roughness"].default_value = 0.6
    mix = nt.nodes.new("ShaderNodeMath"); mix.operation='MULTIPLY'
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value=0.5; mr.inputs[2].default_value=0.72; mr.inputs[4].default_value=dens
    gz = nt.nodes.new("ShaderNodeSeparateXYZ"); fall = nt.nodes.new("ShaderNodeMapRange"); fall.inputs[1].default_value = -1.0; fall.inputs[2].default_value = 2.6; fall.inputs[3].default_value=1; fall.inputs[4].default_value=0
    f2 = nt.nodes.new("ShaderNodeMath"); f2.operation='MULTIPLY'
    nt.links.new(tc.outputs["Object"], mp.inputs[0]); nt.links.new(mp.outputs[0], wv.inputs[0]); nt.links.new(wv.outputs["Fac"], n.inputs["Vector"] if False else n.inputs["W"] if "W" in n.inputs else n.inputs[1])
    nt.links.new(tc.outputs["Generated"], n.inputs["Vector"])
    nt.links.new(n.outputs["Fac"], mr.inputs[0])
    nt.links.new(tc.outputs["Object"], gz.inputs[0]); nt.links.new(gz.outputs["Z"], fall.inputs[0])
    nt.links.new(mr.outputs[0], f2.inputs[0]); nt.links.new(fall.outputs[0], f2.inputs[1])
    nt.links.new(f2.outputs[0], v.inputs["Density"]); nt.links.new(v.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    o.data.materials.append(m); return o
ink("Plume", (13, 2.0, 10.0), (0, 0.4, 1.4), 4.0, 2.2, (0.75,0.95,0.05,1))
ink("Haze", (18, 5, 12), (0, 1.5, 1.0), 0.15, 1.1, (0.5,0.6,0.2,1))
# tiny suspended particles in the water
dm = mat("P", (1,1,0.8,1), 0.5, emit=(1,1,0.7,1), estr=1.5)
def p(i, rnd):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rnd.uniform(0.004,0.012), location=(rnd.uniform(-4,4), rnd.uniform(-2,1), rnd.uniform(-1.5,3.5)))
    bpy.context.active_object.data.materials.append(dm)
scatter(150, p, 5)
light('AREA', "Rim", (0, 4.5, 4), (0,0,0.5), energy=900, color=(1.0,0.95,0.8), size=3)
light('SPOT', "Side", (-6, -2, 3), (0,0,0.5), energy=4000, color=(0.85,0.9,1.0), spot=30, blend=0.5, size=0.5)
light('AREA', "Front", (0, -6, 1), (0,0,0), energy=150, color=(0.8,0.9,1), size=4)
camera((0, -8.5, 0.4), (0, 0, 0.6), lens=40)
render(out)
