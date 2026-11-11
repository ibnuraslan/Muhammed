"""Shrink textures, then run the studio packer.
blender -b work/anim.blend --python 04_package.py -- ../NoPilotPlane_v002/NoPilotPlane_v002_60fps.blend
- duplicate MakeHuman images (same file loaded once per human) are merged
- 4K maps -> 2K (normals 1K); teeth / tongue / sss / eyelash maps -> 512
then pipeline/package_for_farm.py packs everything and saves compressed."""
import sys, os, bpy
HERE = os.path.dirname(os.path.abspath(__file__))
by_path = {}
merged = 0
for im in list(bpy.data.images):
    if im.source != 'FILE': continue
    k = os.path.realpath(bpy.path.abspath(im.filepath))
    if k in by_path:
        im.user_remap(by_path[k]); bpy.data.images.remove(im); merged += 1
    else:
        by_path[k] = im
small = ("teeth", "tongue", "sss", "eyelash", "eyebrow")
for im in bpy.data.images:
    if im.source != 'FILE' or not im.size[0]: continue
    n = os.path.basename(im.filepath).lower()
    tgt = 512 if any(s in n for s in small) else (1024 if "normal" in n else 2048)
    if "nologo" in n or "skinned" in n: tgt = 2048
    if im.size[0] > tgt:
        im.scale(tgt, tgt * im.size[1] // im.size[0]); im.pack()
print("IMAGES merged", merged, "left", len([i for i in bpy.data.images if i.source == 'FILE']))
sys.argv = [sys.argv[0], "--", sys.argv[sys.argv.index("--") + 1]]
exec(open(os.path.join(HERE, "..", "..", "pipeline", "package_for_farm.py")).read())
