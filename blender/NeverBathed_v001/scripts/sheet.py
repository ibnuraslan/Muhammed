"""python3 sheet.py OUTDIR out.jpg [cols]: montage all f*.jpg with frame labels"""
import sys, glob, os
from PIL import Image, ImageDraw
fs = sorted(glob.glob(os.path.join(sys.argv[1], "f*.jpg"))); cols = int(sys.argv[3]) if len(sys.argv) > 3 else 6
ims = [Image.open(f) for f in fs]; w, h = ims[0].size; rows = (len(ims) + cols - 1) // cols
c = Image.new("RGB", (w * cols, h * rows), "white"); d = ImageDraw.Draw(c)
for i, (f, im) in enumerate(zip(fs, ims)):
    x, y = (i % cols) * w, (i // cols) * h; c.paste(im, (x, y)); d.text((x + 4, y + 4), os.path.basename(f)[1:-4], fill=(255, 255, 0))
c.save(sys.argv[2], quality=88)
