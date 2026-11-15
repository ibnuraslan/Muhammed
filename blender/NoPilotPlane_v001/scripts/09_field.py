"""v009c (director): the flat lime-green patch in the window view must read as the landing field.
Grass material with mowing bands on LONG_FIELD, and a runway strip (asphalt, white centreline dashes, edge lines)
along its long axis. Run on the packaged film after 08_camera.py:
blender -b film.blend --python 09_field.py -- out.blend"""
import sys, bpy, bmesh
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]
bpy.context.scene.frame_set(1)
F = bpy.data.objects["LONG_FIELD"]
ws = [F.matrix_world @ v.co for v in F.data.vertices]
lo = Vector((min(v.x for v in ws), min(v.y for v in ws), min(v.z for v in ws)))
hi = Vector((max(v.x for v in ws), max(v.y for v in ws), max(v.z for v in ws)))
ctr = (lo + hi) / 2; size = hi - lo
along_x = size.x >= size.y
print("FIELD", tuple(round(c, 1) for c in lo), tuple(round(c, 1) for c in hi), "long axis", "x" if along_x else "y")

def node_mat(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], o.inputs[0]); b.inputs["Roughness"].default_value = 0.9
    return m, nt, b

# grass: two greens mixed by noise, darker/lighter mowing bands across the long axis
m, nt, b = node_mat("M_long_field")
tc = nt.nodes.new("ShaderNodeTexCoord")
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.02; nz.inputs["Detail"].default_value = 6
nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'X' if along_x else 'Y'
wv.inputs["Scale"].default_value = 0.012; wv.inputs["Distortion"].default_value = 0.0
nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (0.055, 0.12, 0.03, 1); ramp.color_ramp.elements[1].color = (0.11, 0.20, 0.05, 1)
nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
band = nt.nodes.new("ShaderNodeMix"); band.data_type = 'RGBA'; band.blend_type = 'MULTIPLY'
band.inputs["Factor"].default_value = 0.25
nt.links.new(ramp.outputs["Color"], band.inputs["A"]); nt.links.new(wv.outputs["Color"], band.inputs["B"])
nt.links.new(band.outputs["Result"], b.inputs["Base Color"])
F.data.materials.clear(); F.data.materials.append(m)

# runway: 60 % of the field length, 45 m wide, just above the field
L = (size.x if along_x else size.y) * 0.7; W = 160.0          # wide enough to read from the cockpit at this distance
me = bpy.data.meshes.new("RUNWAY_STRIP"); bm = bmesh.new()
hx, hy = (L / 2, W / 2) if along_x else (W / 2, L / 2)
z = hi.z + 0.3
vs = [bm.verts.new((ctr.x + sx * hx, ctr.y + sy * hy, z)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
f = bm.faces.new(vs); bm.to_mesh(me); bm.free()
uv = me.uv_layers.new(name="UVMap")
for li, l in enumerate(me.loops):
    v = me.vertices[l.vertex_index].co
    u_ = (v.x - (ctr.x - hx)) / (2 * hx); v_ = (v.y - (ctr.y - hy)) / (2 * hy)
    uv.data[li].uv = (u_, v_) if along_x else (v_, u_)          # u along the runway, v across
rw = bpy.data.objects.new("RUNWAY_STRIP", me); F.users_collection[0].objects.link(rw)
rw.parent = F; rw.matrix_parent_inverse = F.matrix_world.inverted()      # the terrain moves under the aircraft: ride with the field
m2, nt2, b2 = node_mat("M_runway")
uvn = nt2.nodes.new("ShaderNodeUVMap"); sep = nt2.nodes.new("ShaderNodeSeparateXYZ"); nt2.links.new(uvn.outputs[0], sep.inputs[0])
def math(op, a, bb=None):
    n = nt2.nodes.new("ShaderNodeMath"); n.operation = op
    for i, x in enumerate((a, bb)):
        if x is None: continue
        if isinstance(x, (int, float)): n.inputs[i].default_value = x
        else: nt2.links.new(x, n.inputs[i])
    return n.outputs[0]
dv = math('ABSOLUTE', math('SUBTRACT', sep.outputs["Y"], 0.5))              # distance from the centreline, 0..0.5
centre = math("LESS_THAN", dv, 0.03)
dash = math('LESS_THAN', math('FRACT', math('MULTIPLY', sep.outputs["X"], 60.0)), 0.5)
cl = math('MULTIPLY', centre, dash)
edge = math("GREATER_THAN", dv, 0.44)
paint = math('MAXIMUM', cl, edge)
mx = nt2.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'
mx.inputs["A"].default_value = (0.07, 0.07, 0.075, 1); mx.inputs["B"].default_value = (0.85, 0.85, 0.82, 1)
nt2.links.new(paint, mx.inputs["Factor"]); nt2.links.new(mx.outputs["Result"], b2.inputs["Base Color"])
me.materials.append(m2)
print("RUNWAY", round(L), "x", W, "at z", round(z, 2))
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("FIELD09 saved", out)
