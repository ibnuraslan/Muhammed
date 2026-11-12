"""v004 (director): saturated, textured cutaway strata with relief at the band edges, bigger ridge jungle.
blender -b final3.blend --python 10_v004.py -- <out.blend>"""
import sys, bpy
OUT = sys.argv[sys.argv.index("--") + 1]
ms = bpy.data.materials["M_Strata"]; nt = ms.node_tree
p = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
rp = [n for n in nt.nodes if n.type == 'VALTORGB'][-1]
els = rp.color_ramp.elements
cols = [(0.72, 0.42, 0.1), (0.55, 0.2, 0.08), (0.22, 0.27, 0.33), (0.82, 0.66, 0.36), (0.42, 0.26, 0.14)]
for e, c in zip(els, cols): e.color = (*c, 1)
mx = next(n for n in nt.nodes if n.type == 'MIX' and n.blend_type == 'OVERLAY'); mx.inputs['Factor'].default_value = 0.6
for n in nt.nodes:
    if n.type == 'HUE_SAT': n.inputs['Saturation'].default_value = max(n.inputs['Saturation'].default_value, 1.4)
wv = next(n for n in nt.nodes if n.type == 'TEX_WAVE')
bmp = nt.nodes.new('ShaderNodeBump'); bmp.inputs['Strength'].default_value = 0.45; bmp.inputs['Distance'].default_value = 0.15
nmap = p.inputs['Normal'].links[0].from_socket if p.inputs['Normal'].links else None
nt.links.new(wv.outputs['Fac'], bmp.inputs['Height'])
if nmap: nt.links.new(nmap, bmp.inputs['Normal'])
nt.links.new(bmp.outputs['Normal'], p.inputs['Normal']); p.inputs['Roughness'].default_value = 0.55
for o in bpy.data.objects:
    if o.name.startswith("S3_MiniTree_"): o.scale = tuple(v * 2.0 for v in o.scale)
mj = bpy.data.materials["M_MiniJungle"]
for n in mj.node_tree.nodes:
    if n.type == 'HUE_SAT': n.inputs['Saturation'].default_value = 1.6; n.inputs['Value'].default_value = 0.8
import bmesh
# tunnel, passage and studio dome are seen from inside: point their normals into the space (QA INSIDE test; render unchanged)
for nm in ("S3_StudioDome",):
    o = bpy.data.objects.get(nm)
    if o is None: continue
    b_ = bmesh.new(); b_.from_mesh(o.data); bmesh.ops.reverse_faces(b_, faces=b_.faces); b_.to_mesh(o.data); b_.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("V004_OK")
