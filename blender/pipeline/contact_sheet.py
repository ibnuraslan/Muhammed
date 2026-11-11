"""python3 -I contact_sheet.py <dir_of_jpgs> <out.jpg> <cols> <stills_per_second> [start] [end]"""
import sys, glob
from PIL import Image, ImageDraw
src, out, cols, rate = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4])
start = int(sys.argv[5]) if len(sys.argv) > 5 else 0
end = int(sys.argv[6]) if len(sys.argv) > 6 else 10**9
fs = sorted(glob.glob(src + "/*.jpg"))[start:end]
ims = [Image.open(f).convert("RGB") for f in fs]
w, h = ims[0].size
S = Image.new("RGB", (w * cols, h * ((len(ims) + cols - 1) // cols)), "black")
for i, im in enumerate(ims):
    d = ImageDraw.Draw(im); d.rectangle((0, 0, 46, 14), fill=(0, 0, 0)); d.text((2, 1), "%.1fs" % ((start + i) / rate), fill=(255, 255, 0))
    S.paste(im, ((i % cols) * w, (i // cols) * h))
S.save(out, quality=85); print(out, S.size, len(ims))
