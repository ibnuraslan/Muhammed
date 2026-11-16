"""3-frame contact sheet: python3 sheet.py <stills_dir> <out.jpg> [shots per page]"""
import sys, glob, os
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]
fs = sorted(glob.glob(d + "/*.jpg"))
shots = sorted({os.path.basename(f).split("_")[0] for f in fs})
W, H = 540, 960; per = int(sys.argv[3]) if len(sys.argv) > 3 else 4
pages = [shots[i:i + per] for i in range(0, len(shots), per)]
for p, sh in enumerate(pages):
    S = Image.new("RGB", (W * 3, H * len(sh) + 0), "white"); dr = ImageDraw.Draw(S)
    for r, s in enumerate(sh):
        for k in range(3):
            g = glob.glob("%s/%s_%d_f*.jpg" % (d, s, k))
            if not g: continue
            S.paste(Image.open(g[0]).resize((W, H)), (k * W, r * H))
            dr.rectangle((k * W, r * H, k * W + 230, r * H + 26), fill="black")
            dr.text((k * W + 6, r * H + 6), os.path.basename(g[0])[:-4], fill="yellow")
    S.save(out.replace(".jpg", "_p%d.jpg" % (p + 1)), quality=85)
print("pages", len(pages))
