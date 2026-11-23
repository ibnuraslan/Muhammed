"""v014: the core beat, legible (director, v013 note 4). Runs after 22, before 23.
blender -b in.blend --python 24_v014_brand.py -- <out.blend>
- The initials are crisp charred letters "SB" lying on the liver's surface (shrink-wrapped to it), revealed by the
  burn front that follows the pen tip, with a thin glowing edge while burning. They stay on the liver for the reveal.
- The old burn mask / hot curves (white glare at preview size) are off.
- The argon jet is a bright blue emissive cone from the pen tip to the liver with its own light, on while burning.
- The surgical lamps are dimmed (they blew out the top of frame)."""
import sys, os, math, json
import bpy, bmesh
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import v12lib as VL
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; V = lambda *a: Vector(a); OB = bpy.data.objects
LV = OB["Liver"]; E = OB["LiverRig"]; pen = OB["ArgonPen_Studio"]
# ---- old burn off
for n in ("Brand_S_Hot", "Brand_S_Sear", "Brand_B_Hot", "Brand_B_Sear", "TipFlare"):
    if OB.get(n): VL.key_hide(OB[n], [])
for m in LV.data.materials:
    if m and m.node_tree and "BurnProgress" in m.node_tree.nodes:
        bp = m.node_tree.nodes["BurnProgress"]; VL.clear_keys(m.node_tree, ('nodes["BurnProgress"]',)); bp.outputs[0].default_value = -1.0
# ---- letter placement: on the liver top, reading +y (left to right from the foot end), letter tops toward the head (-x)
sc.frame_set(250); bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
lv_ev = LV.evaluated_get(dg)
def liver_top(x, y):
    Mi = LV.matrix_world.inverted(); ok, loc, nrm, i = lv_ev.ray_cast(Mi @ V(x, y, 2.0), Mi.to_3x3() @ V(0, 0, -1))
    return (LV.matrix_world @ loc) if ok else None
tips = []
for f in range(141, 279, 2):
    sc.frame_set(f); tips.append((f, pen.matrix_world.translation.copy()))
ys = [p.y for f, p in tips]; xs = [p.x for f, p in tips]
cy = (min(ys) + max(ys)) / 2; cx = sum(xs) / len(xs)
sc.frame_set(250)
top = liver_top(cx, cy) or V(cx, cy, 1.08)
cu = bpy.data.curves.new("BrandSB", 'FONT'); cu.body = "SB"; cu.size = 0.052; cu.space_character = 1.15
cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.extrude = 0.0004
tmp = OB.new("BrandSB_tmp", cu); bpy.data.collections["OR_Set"].objects.link(tmp)
bpy.context.view_layer.update()
me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
bpy.data.objects.remove(tmp, do_unlink=True)
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.triangulate(bm, faces=bm.faces[:])
bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=3, use_grid_fill=True)
bm.to_mesh(me); bm.free()
br = OB.new("BrandSB", me); bpy.data.collections["OR_Set"].objects.link(br)
# text local: x = reading, y = letter up, z = normal  ->  world: x->+y, y->-x, z->+z
Rm = Matrix(((0, -1, 0), (1, 0, 0), (0, 0, 1)))
br.matrix_world = Matrix.Translation(top + V(0, 0, 0.004)) @ Rm.to_4x4()
sw = br.modifiers.new("OnLiver", 'SHRINKWRAP'); sw.target = LV; sw.wrap_method = 'PROJECT'; sw.use_project_z = True
sw.use_negative_direction = True; sw.use_positive_direction = True; sw.offset = 0.0009
# charred letters, revealed by the burn front (world y), glowing at the front
mat = bpy.data.materials.new("BrandChar"); mat.use_nodes = True; nt = mat.node_tree; N, L = nt.nodes, nt.links
for n in list(N): N.remove(n)
out = N.new("ShaderNodeOutputMaterial"); bsdf = N.new("ShaderNodeBsdfPrincipled")
bsdf.inputs["Base Color"].default_value = (0.035, 0.012, 0.006, 1); bsdf.inputs["Roughness"].default_value = 0.85
front = OB.new("BurnFront", None); bpy.data.collections["OR_Set"].objects.link(front)
tc = N.new("ShaderNodeTexCoord"); tc.object = front
sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp.inputs[0])
rev = N.new("ShaderNodeMath"); rev.operation = 'LESS_THAN'; L.new(sp.outputs["Y"], rev.inputs[0]); rev.inputs[1].default_value = 0.0
edge = N.new("ShaderNodeMapRange"); L.new(sp.outputs["Y"], edge.inputs[0])
edge.inputs[1].default_value = -0.012; edge.inputs[2].default_value = 0.0; edge.inputs[3].default_value = 0.0; edge.inputs[4].default_value = 1.0
em = N.new("ShaderNodeEmission"); em.inputs[0].default_value = (1.0, 0.45, 0.1, 1)
ems = N.new("ShaderNodeMath"); ems.operation = 'MULTIPLY'; L.new(edge.outputs[0], ems.inputs[0]); ems.inputs[1].default_value = 18.0
L.new(ems.outputs[0], em.inputs[1])
add = N.new("ShaderNodeAddShader"); L.new(bsdf.outputs[0], add.inputs[0]); L.new(em.outputs[0], add.inputs[1])
tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
L.new(rev.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(add.outputs[0], mx.inputs[2])
L.new(mx.outputs[0], out.inputs[0])
me.materials.append(mat)
# burn front = running max of the pen tip's y while burning; after the burn it is far ahead (all letters shown)
ylo = br.matrix_world.translation.y - 0.06; run = ylo
front.keyframe_insert("location", frame=1)
front.location = V(0, ylo - 0.02, 0); front.keyframe_insert("location", frame=1)
front.location = V(0, ylo - 0.02, 0); front.keyframe_insert("location", frame=140)
span = max(ys) - min(ys)
for f, p in tips:
    u = (f - 141) / (278 - 141.0)
    run = max(run, ylo + (0.12) * u)          # sweeps S then B, left to right, in time with the writing
    front.location = V(0, run, 0); front.keyframe_insert("location", frame=f)
front.location = V(0, ylo + 1.0, 0); front.keyframe_insert("location", frame=282)
for fc in VL.fcurves(front):
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
# the letters ride the liver (lift in the reveal)
mw = br.matrix_world.copy(); br.parent = E; br.matrix_parent_inverse = E.matrix_world.inverted(); br.matrix_world = mw
VL.key_hide(br, [(0, 362), (1000, 1262)])
# ---- argon jet: bright blue cone + light, on while burning
beam = OB.get("ArgonBeam")
if beam:
    beam.scale = (2.4, 2.4, 1.6)
    for m in beam.data.materials:
        for n in m.node_tree.nodes:
            if n.type == 'EMISSION': n.inputs[1].default_value = 90.0; n.inputs[0].default_value = (0.35, 0.55, 1.0, 1)
            if n.type == 'MIX_SHADER':
                for l in list(n.inputs[0].links): m.node_tree.links.remove(l)
                n.inputs[0].default_value = 0.85
    ld = bpy.data.lights.new("ArgonGlow", 'POINT'); ld.energy = 2.5; ld.color = (0.45, 0.6, 1.0); ld.shadow_soft_size = 0.004
    gl = OB.new("ArgonGlow", ld); bpy.data.collections["OR_Set"].objects.link(gl)
    gl.parent = pen; gl.matrix_parent_inverse = Matrix.Identity(4); gl.location = (0, 0, -0.006)
    VL.key_hide(gl, [(141, 278)]); VL.key_hide(beam, [(141, 278)])
print("BRAND letters at", tuple(round(x, 3) for x in br.matrix_world.translation), "pen y span", round(span, 3))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("BRAND_DONE", OUT)
