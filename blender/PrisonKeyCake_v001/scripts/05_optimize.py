"""Pre-package size pass: drop unlinked image nodes, dedupe images, downscale big textures (hero skin stays 2K).
blender -b film.blend --python scripts/05_optimize.py --python ../pipeline/package_for_farm.py -- <out.blend>"""
import bpy, os
removed = 0
for m in bpy.data.materials:
    if not m.node_tree: continue
    while True:
        dead = [n for n in m.node_tree.nodes if n.type in ('TEX_IMAGE', 'DISPLACEMENT', 'MAPPING') and not any(o.is_linked for o in n.outputs)]
        if not dead: break
        for n in dead: m.node_tree.nodes.remove(n); removed += 1
by = {}
for im in bpy.data.images:
    if im.source == 'FILE':
        k = bpy.path.abspath(im.filepath)
        if k in by and im != by[k]: im.user_remap(by[k])
        else: by.setdefault(k, im)
for im in list(bpy.data.images):
    if im.users == 0: bpy.data.images.remove(im)
KEEP2K = ("young_lightskinned_male_diffuse", "old_lightskinned_male_diffuse", "male_casualsuit01_diffuse", "male_elegantsuit01_diffuse")
scaled = 0
for im in bpy.data.images:
    if im.source != 'FILE' or im.size[0] == 0: continue
    if im.filepath.lower().endswith(".hdr"): continue
    big = max(im.size)
    tgt = 2048 if any(k in im.name for k in KEEP2K) else 1024
    if big > tgt:
        im.scale(tgt, max(1, round(im.size[1] * tgt / im.size[0])))
        im.pack(); scaled += 1
print("OPT removed nodes", removed, "scaled", scaled, "images", len(bpy.data.images))
