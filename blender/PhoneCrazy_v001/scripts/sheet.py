"""python3 -I sheet.py <dir> <out.jpg> <cols>: labelled contact sheet of every jpg in dir (sorted by shot, frame)"""
import sys, os, re
from PIL import Image, ImageDraw
d, out, cols = sys.argv[1], sys.argv[2], int(sys.argv[3])
fs = sorted([f for f in os.listdir(d) if f.endswith(".jpg")], key=lambda f: (int(re.findall(r"S(\d+)", f)[0]), f))
im0 = Image.open(os.path.join(d, fs[0])); w, h = im0.size
rows = (len(fs) + cols - 1) // cols; S = Image.new("RGB", (cols * w, rows * (h + 18)), "white"); D = ImageDraw.Draw(S)
for i, f in enumerate(fs):
    x, y = (i % cols) * w, (i // cols) * (h + 18); S.paste(Image.open(os.path.join(d, f)), (x, y + 18)); D.text((x + 3, y + 3), f[:-4], fill=(0, 0, 0))
S.save(out, quality=85); print(out, S.size)
