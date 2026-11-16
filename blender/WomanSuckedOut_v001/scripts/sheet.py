"""python3 sheet.py dir out.jpg [cols]: labelled contact sheet of shotstills output"""
import sys, os, glob
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; cols = int(sys.argv[3]) if len(sys.argv) > 3 else 9
fs = sorted(glob.glob(d + "/*.jpg")); ims = [Image.open(f) for f in fs]
w, h = ims[0].size; rows = (len(ims) + cols - 1) // cols
S = Image.new("RGB", (cols * w, rows * (h + 22)), "white"); dr = ImageDraw.Draw(S)
for i, (f, im) in enumerate(zip(fs, ims)):
    x, y = (i % cols) * w, (i // cols) * (h + 22); S.paste(im, (x, y + 22)); dr.text((x + 4, y + 4), os.path.basename(f)[:-4], fill="black")
S.save(out, quality=88); print(out, S.size)
