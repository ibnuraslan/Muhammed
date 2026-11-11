"""Pre-package texture budget: everything to 1K except the woman's hero skin/hair (2K). Repacks the scaled pixels."""
import bpy
HERO = {"middleage_lightskinned_female_diffuse.png", "bob02_diffuse.png", "sss.png"}
for im in list(bpy.data.images):
    if im.source != 'FILE' or im.size[0] == 0: continue
    lim = 2048 if im.name in HERO else 1024
    if max(im.size) > lim:
        w, h = im.size; s = lim / max(w, h)
        im.scale(int(w * s), int(h * s))
        im.file_format = 'PNG'
        im.pack()
        print("SCALED", im.name, im.size[:])
bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
