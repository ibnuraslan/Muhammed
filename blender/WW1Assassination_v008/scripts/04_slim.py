"""WW1Assassination v008: texture slimming before packing (target < 95 MB). Packed images keep alpha (pack(), not save_render).
blender -b film.blend --python 04_slim.py -- <out.blend>
Hero faces (Archduke, Duchess, gunman skins) stay 2K; the map rasters keep their exact resolution; other textures 1K;
normal/bump maps 512."""
import bpy, sys
out = sys.argv[sys.argv.index("--") + 1]
KEEP = ("map_state", "map_height", "DaKrasFilms")
HERO = ("middleage_lightskinned_male_diffuse.png", "middleage_lightskinned_female_diffuse.png", "young_lightskinned_male_diffuse.png")
for im in bpy.data.images:
    if im.source != 'FILE' or any(k in im.name for k in KEEP): continue
    w, h = im.size
    if w == 0: continue
    lim = 2048 if im.name in HERO else (512 if any(k in im.name.lower() for k in ("norm", "bump", "spec", "_ao")) else 1024)
    if max(w, h) > lim:
        k = lim / max(w, h); im.scale(max(1, int(w * k)), max(1, int(h * k)))
        im.pack()
        print("SLIM", im.name, (w, h), "->", tuple(im.size))
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=out)
print("SLIM_DONE")
