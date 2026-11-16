import sys, glob
from PIL import Image, ImageDraw
fs = sorted(glob.glob(sys.argv[1] + "_*.png")); cols = int(sys.argv[3]) if len(sys.argv) > 3 else 6
ims = [Image.open(f).convert("RGB") for f in fs]; w, h = ims[0].size
S = Image.new("RGB", (w * min(cols, len(ims)), h * ((len(ims) + cols - 1) // cols)))
for i, im in enumerate(ims):
    ImageDraw.Draw(im).text((3, 3), fs[i].split("_")[-1][:-4], fill=(255, 255, 0)); S.paste(im, ((i % cols) * w, (i // cols) * h))
S.save(sys.argv[2], quality=85)
