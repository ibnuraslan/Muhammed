import sys, glob
from PIL import Image, ImageDraw
out = sys.argv[1]; cols = int(sys.argv[2]); fs = sys.argv[3:]
if len(fs) == 1: fs = sorted(glob.glob(fs[0]))
ims = [Image.open(f) for f in fs]; w, h = ims[0].size; rows = (len(ims) + cols - 1) // cols
S = Image.new("RGB", (w * cols, h * rows), "white")
for i, (f, im) in enumerate(zip(fs, ims)):
    S.paste(im.resize((w, h)), (w * (i % cols), h * (i // cols))); ImageDraw.Draw(S).text((w * (i % cols) + 6, h * (i // cols) + 6), f.split("/")[-1].rsplit(".", 1)[0], fill=(255, 255, 0))
S.save(out, quality=85)
