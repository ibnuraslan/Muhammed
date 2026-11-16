import sys, glob
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; fs = sorted(glob.glob(d + "/f*.jpg")); im0 = Image.open(fs[0]); w, h = im0.size
n = len(fs); cols = min(n, int(sys.argv[3]) if len(sys.argv) > 3 else 6); rows = (n + cols - 1) // cols
S = Image.new("RGB", (w * cols, h * rows), "white")
for i, f in enumerate(fs):
    S.paste(Image.open(f), (w * (i % cols), h * (i // cols))); ImageDraw.Draw(S).text((w * (i % cols) + 4, h * (i // cols) + 4), f.split("/")[-1][1:5], fill=(255, 255, 0))
S.save(out, quality=85)
