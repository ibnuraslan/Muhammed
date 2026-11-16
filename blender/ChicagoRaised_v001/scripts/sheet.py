"""Contact sheet: python3 sheet.py <dir> <out.jpg> [cols]  (files named Sxx_ffff.jpg; 3 per shot -> one row per shot group)"""
import sys, os, glob
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; cols = int(sys.argv[3]) if len(sys.argv) > 3 else 9
fs = sorted(glob.glob(os.path.join(d, "*.jpg")), key=lambda p: (int(os.path.basename(p)[1:3]), int(os.path.basename(p)[4:8])))
w, h = Image.open(fs[0]).size
rows = (len(fs) + cols - 1) // cols
im = Image.new("RGB", (w * cols, (h + 18) * rows), (255, 255, 255)); dr = ImageDraw.Draw(im)
for i, f in enumerate(fs):
    x, y = (i % cols) * w, (i // cols) * (h + 18)
    im.paste(Image.open(f), (x, y + 18)); dr.text((x + 4, y + 3), os.path.basename(f)[:-4], fill=(0, 0, 0))
im.save(out, quality=88); print(out, im.size)
