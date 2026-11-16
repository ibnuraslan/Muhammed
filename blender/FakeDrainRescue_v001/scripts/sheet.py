"""python3 sheet.py dir out.jpg cols [cell_w] -> labelled contact sheet of the jpgs in dir (sorted)"""
import sys, glob, os
from PIL import Image, ImageDraw
d, out, cols = sys.argv[1], sys.argv[2], int(sys.argv[3]); cw = int(sys.argv[4]) if len(sys.argv) > 4 else 270
fs = sorted(glob.glob(d + "/*.jpg")); ims = [Image.open(f) for f in fs]
ch = int(cw * ims[0].height / ims[0].width); rows = (len(ims) + cols - 1) // cols
S = Image.new("RGB", (cols * cw, rows * (ch + 18)), (20, 20, 20)); dr = ImageDraw.Draw(S)
for i, (f, im) in enumerate(zip(fs, ims)):
    x, y = (i % cols) * cw, (i // cols) * (ch + 18); S.paste(im.resize((cw, ch)), (x, y + 18)); dr.text((x + 4, y + 3), os.path.basename(f)[:-4], fill=(255, 255, 0))
S.save(out, quality=88); print(out, len(ims))
