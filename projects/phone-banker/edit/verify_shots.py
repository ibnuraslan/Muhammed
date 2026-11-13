"""Open every baked shot file: fonts packed, images packed or found, title shots carry their title. -> stdout"""
import os, sys, glob, bpy
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
bad = []
files = sorted(glob.glob(os.path.join(ROOT, "out", "blend", "*", "*.blend")))
files = [f for f in files if "/film/" not in f and "/_stale/" not in f]
for f in files:
    bpy.ops.wm.open_mainfile(filepath=f)
    fonts = [x.name for x in bpy.data.fonts if x.filepath and x.filepath != "<builtin>" and not x.packed_file]
    imgs = [x.name for x in bpy.data.images if x.source in ('FILE', 'SEQUENCE') and not x.packed_file and x.filepath
            and not os.path.exists(bpy.path.abspath(x.filepath).replace("f0001", "f0001"))]
    if fonts or imgs:
        bad.append((os.path.basename(f), fonts, imgs))
print(f"[shots] {len(files)} files checked; problems: {bad if bad else 'none'}")
