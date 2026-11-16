"""python3 sheet.py dir out.jpg [cols]: grid of stills with labels"""
import sys, glob, os
from PIL import Image, ImageDraw
fs = sorted(glob.glob(sys.argv[1] + "/S*_*.jpg")); cols = int(sys.argv[3]) if len(sys.argv) > 3 else 9
im0 = Image.open(fs[0]); w, h = im0.size; rows = (len(fs) + cols - 1) // cols
S = Image.new("RGB", (cols * w, rows * (h + 18)), "white")
for i, f in enumerate(fs):
    S.paste(Image.open(f), ((i % cols) * w, (i // cols) * (h + 18) + 18))
    ImageDraw.Draw(S).text(((i % cols) * w + 3, (i // cols) * (h + 18) + 3), os.path.basename(f)[:-4], fill=(0, 0, 0))
S.save(sys.argv[2], quality=85); print(sys.argv[2], S.size)
