"""v012: dress the Man (T-shirt + jeans) and Mom (blouse + skirt) with the outfits fitted by build_clothes.py.
The new meshes are appended, parented to the film rigs with the same local transform, their Armature modifiers point at the film
rigs, and they show whenever the body shows. The old one-colour outfits are removed. Mom's blouse is shifted to a warm mustard so it
is not the boy's red stripes. blender -b film.blend --python import_clothes.py -- newclothes.blend out.blend"""
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]; SRC, OUT = a[0], a[1]
with bpy.data.libraries.load(SRC, link=False) as (fr, to):
    to.objects = [n for n in fr.objects if n.startswith("NEW_") and not n.endswith("_Body") and n not in ("NEW_Man", "NEW_Mom")]
OLD = {"Man": "Man_Man.male_casualsuit01", "Mom": "Mom_Mom.female_casualsuit01"}
def fcs(o): return [fc for l in o.animation_data.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves] if o.animation_data and o.animation_data.action else []
for o in to.objects:
    nm = "Man" if o.name.startswith("NEW_Man") else "Mom"; rig = bpy.data.objects[nm]; body = bpy.data.objects[nm + "_Body"]
    bpy.context.scene.collection.objects.link(o)
    loc = o.matrix_local.copy(); o.parent = rig; o.matrix_parent_inverse.identity(); o.matrix_basis = loc
    for m in o.modifiers:
        if m.type == "ARMATURE": m.object = rig
    o.name = nm + "_" + o.name.split("_", 2)[2]
    for fc in [c for c in fcs(body) if c.data_path == "hide_render"]:
        for k in fc.keyframe_points: o.hide_render = bool(k.co.y); o.keyframe_insert("hide_render", frame=k.co.x)
    o.hide_render = body.hide_render if not fcs(o) else o.hide_render
    old = bpy.data.objects.get(OLD[nm])
    if old: bpy.data.objects.remove(old, do_unlink=True)
    for b in [x for x in rig.children_recursive if x.type == "MESH" and x.name.endswith("_Body")]:
        for md in b.modifiers:                                   # MPFB "Delete" masks of the old outfit hid body skin under it
            if md.type == "MASK" and (md.vertex_group or "").lower().startswith("delete"): md.show_render = False; md.show_viewport = False
    if nm == "Mom":
        for mat in o.data.materials:
            nt = mat.node_tree; tex = next((n for n in nt.nodes if n.type == "TEX_IMAGE" and "diffuse" in n.name.lower()), None) or next((n for n in nt.nodes if n.type == "TEX_IMAGE"), None)
            if not tex: continue
            hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Hue"].default_value = 0.62; hs.inputs["Saturation"].default_value = 0.9
            for l in [l for l in nt.links if l.from_node == tex and l.from_socket.name == "Color"]:
                to_s = l.to_socket; nt.links.remove(l); nt.links.new(hs.outputs[0], to_s)
            nt.links.new(tex.outputs["Color"], hs.inputs["Color"])
    print("DRESSED", nm, o.name, len(o.data.vertices), [m.name for m in o.data.materials])
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
