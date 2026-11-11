"""Shrink textures, then run the studio packer.
blender -b work/anim.blend --python 04_package.py -- ../NoPilotPlane_v002/NoPilotPlane_v002_60fps.blend
- duplicate MakeHuman images (same file loaded once per human) are merged
- every map -> 1K JPEG (YOU's skin and shirt 2K for the face reveal); teeth / tongue / sss / lash maps -> 256
- orphan data purged; the .blend must stay under 95 MB (no Git LFS from Connect chats)
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
SM = os.path.join(HERE, "..", "work", "tex_small"); os.makedirs(SM, exist_ok=True)
hero = ("young_lightskinned_male_diffuse.png", "male_casualsuit04_diffuse_nologo.png")   # YOU's face/shirt in the final reveal
for im in list(bpy.data.images):
    if im.source != 'FILE' or not im.size[0]: continue
    n = os.path.basename(im.filepath).lower()
    tgt = 256 if any(s in n for s in small) else (2048 if n in hero else 1024)
    if n.startswith("disp_") or n == "checklist.png": continue
    if im.size[0] > tgt: im.scale(tgt, tgt * im.size[1] // im.size[0])
    alpha = im.channels == 4 and any(k in n for k in ("eyelash", "eyebrow", "short0", "bob0", "afro", "ponytail", "long0", "braid"))
    dst = os.path.join(SM, os.path.splitext(n)[0] + (".png" if alpha else ".jpg"))
    im.filepath_raw = dst; im.file_format = 'PNG' if alpha else 'JPEG'
    im.save(filepath=dst, quality=88)
    im.filepath = dst; im.reload()
bpy.data.orphans_purge(do_recursive=True)
print("IMAGES merged", merged, "left", len([i for i in bpy.data.images if i.source == 'FILE']))
sys.argv = [sys.argv[0], "--", sys.argv[sys.argv.index("--") + 1]]
exec(open(os.path.join(HERE, "..", "..", "pipeline", "package_for_farm.py")).read())
