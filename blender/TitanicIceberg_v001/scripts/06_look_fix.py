"""After pipeline/anim_look.py (--no-sky): restore the few things the generic pass should not touch.
blender -b look.blend --python 06_look_fix.py -- <out.blend>"""
import sys, bpy
out = sys.argv[sys.argv.index("--") + 1]
sea = bpy.data.materials["M_Sea"].node_tree.nodes["Principled BSDF"]
for n in bpy.data.materials["M_Sea"].node_tree.nodes:
    if n.type == 'BSDF_PRINCIPLED' and n.name == "Principled BSDF":
        for l in list(n.inputs['Roughness'].links): bpy.data.materials["M_Sea"].node_tree.links.remove(l)
        n.inputs['Roughness'].default_value = 0.12   # v008 (sun glossy off below)
        for _f, _v in ((0, 0.12), (605, 0.12), (606, 0.85), (905, 0.85), (906, 0.12)):   # v008: matte water in the high ship shot (HDRI sun glints off the near wave facets)
            n.inputs['Roughness'].default_value = _v; n.inputs['Roughness'].keyframe_insert("default_value", frame=_f)
        for _fc in bpy.data.materials["M_Sea"].node_tree.animation_data.action.fcurves if hasattr(bpy.data.materials["M_Sea"].node_tree.animation_data.action, "fcurves") else []:
            for _k in _fc.keyframe_points: _k.interpolation = 'CONSTANT'
for m in ("M_Developer", "M_PortGlow"):
    if m in bpy.data.materials:
        for n in bpy.data.materials[m].node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                for l in list(n.inputs['Roughness'].links): bpy.data.materials[m].node_tree.links.remove(l)
                n.inputs['Roughness'].default_value = 0.05
# no prints/logos on clothes: MakeHuman casual shirts carry a chest print -> solid colour
for ob in bpy.data.objects:
    if ob.type == 'MESH' and "casualsuit" in ob.name:
        for m in ob.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED':
                    for l in list(n.inputs['Base Color'].links): m.node_tree.links.remove(l)
                    n.inputs['Base Color'].default_value = (0.09, 0.16, 0.36, 1); n.inputs['Roughness'].default_value = 0.85
            print("PATCHED print-free", ob.name, m.name)
# black-hole eyes: MPFB EnhancedEye cornea -> transparent mix (director recipe, eye_fix.py from connect03 a44130b)
import os
_NO_SAVE = True
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else ".", "eye_fix.py")).read(), {"bpy": bpy, "sys": sys, "_NO_SAVE": True, "__name__": "eye_fix"})
# v008: wet catch-light on the cornea (the transparent-only cornea read flat and glassy)
_g = bpy.data.node_groups["EnhancedEye"]; _mx = _g.nodes["CorneaTransparentMix"]
_tr = _mx.inputs[2].links[0].from_node
_gl = _g.nodes.new("ShaderNodeBsdfGlossy"); _gl.inputs["Roughness"].default_value = 0.04
_fr = _g.nodes.new("ShaderNodeFresnel"); _fr.inputs["IOR"].default_value = 1.9
_m2 = _g.nodes.new("ShaderNodeMixShader"); _g.links.new(_fr.outputs[0], _m2.inputs[0])
_g.links.new(_tr.outputs[0], _m2.inputs[1]); _g.links.new(_gl.outputs[0], _m2.inputs[2]); _g.links.new(_m2.outputs[0], _mx.inputs[2])
print("EYE catch-light added")
bpy.data.objects['Key_Sun'].visible_glossy = False   # v008: no sun-glint discs/sheen on the water
# v010: the developing print reads under the safelight (its own image glows faintly as it comes up)
_pd = bpy.data.materials["M_Print_Dev"].node_tree; _pb = _pd.nodes["Principled BSDF"]
_src = _pb.inputs['Base Color'].links[0].from_socket
_pd.links.new(_src, _pb.inputs['Emission Color']); _pb.inputs['Emission Strength'].default_value = 0.9
# v011: the tech's shirt is real cloth (dark charcoal with a weave), not lilac clay
for ob in bpy.data.objects:
    if ob.type == 'MESH' and ob.name.startswith("Tech.") and "casualsuit" in ob.name:
        for m in ob.data.materials:
            if not m or not m.use_nodes: continue
            nt = m.node_tree; pb = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if not pb: continue
            for l in list(pb.inputs['Base Color'].links): nt.links.remove(l)
            pb.inputs["Base Color"].default_value = (0.012, 0.014, 0.018, 1); pb.inputs["Roughness"].default_value = 0.8
            if 'Sheen Weight' in pb.inputs: pb.inputs["Sheen Weight"].default_value = 0.15
            wv = nt.nodes.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 180; bm = nt.nodes.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = 0.25
            nt.links.new(wv.outputs['Fac'], bm.inputs['Height']); nt.links.new(bm.outputs['Normal'], pb.inputs['Normal'])
            print("TECH SHIRT", m.name)
bpy.context.scene.render.use_motion_blur = False
bpy.ops.wm.save_as_mainfile(filepath=out)
print("LOOKFIX done")
