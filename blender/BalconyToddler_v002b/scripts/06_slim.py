"""Before packaging: merge duplicate images that load the same file (MPFB teeth/tongue/sss copies per character), purge orphans.
blender -b in.blend --python 06_slim.py -- out.blend"""
import bpy, sys
out = sys.argv[sys.argv.index("--") + 1]
first = {}; n = 0
for im in list(bpy.data.images):
    if im.source != 'FILE': continue
    key = (bpy.path.abspath(im.filepath), tuple(im.size), im.colorspace_settings.name, im.alpha_mode)
    if key in first and first[key] != im:
        im.user_remap(first[key]); bpy.data.images.remove(im); n += 1
    else:
        first[key] = im
# drop EXR detail maps (normal / roughness / metal from Poly Haven): flat values instead; keeps the package under 95 MB and the
# surfaces smooth (STYLE_ANIMATED: low bump)
ne = 0
for m in bpy.data.materials:
    if not m.node_tree: continue
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type == 'TEX_IMAGE' and n.image and (n.image.filepath.lower().endswith(".exr") or
                any(k in n.image.name.lower() for k in ("nor_gl", "_rough", "_metal", "_arm"))):
            for l in list(n.outputs[0].links) + list(n.outputs[1].links if len(n.outputs) > 1 else []):
                to = l.to_node; sock = l.to_socket; nt.links.remove(l)
                if to.type == 'NORMAL_MAP':
                    for l2 in list(to.outputs[0].links): nt.links.remove(l2)
                elif to.type == 'BSDF_PRINCIPLED' and sock.name == 'Roughness': sock.default_value = 0.55
                elif to.type == 'BSDF_PRINCIPLED' and sock.name == 'Metallic': sock.default_value = 0.0
            nt.nodes.remove(n); ne += 1
print("SLIM detail-map nodes removed", ne)
# unused library copies (aged / rusted variants etc.): objects in PROPS whose mesh nothing else uses
used = {o.data for o in bpy.data.objects if o.data and not any(c.name == "PROPS" for c in o.users_collection)}
for o in list(bpy.data.collections["PROPS"].objects):
    if o.data not in used: bpy.data.objects.remove(o, do_unlink=True)
for im in bpy.data.images: im.use_fake_user = False
bpy.data.orphans_purge(do_recursive=True)
print("SLIM merged", n, "images left", len(bpy.data.images))
bpy.ops.wm.save_as_mainfile(filepath=out)
