import sys, glob, os
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; per = int(sys.argv[3]) if len(sys.argv) > 3 else 99
fs = sorted(glob.glob(d + "/S*_?_f*.jpg"))
shots = sorted(set(os.path.basename(f)[:3] for f in fs))
im0 = Image.open(fs[0]); w, h = im0.size
for k in range(0, len(shots), per):
    grp = shots[k:k + per]; cols = 3 * min(len(grp), 4); rows = (len(grp) + 3) // 4
    S = Image.new("RGB", (w * cols + (min(len(grp),4) - 1) * 6, h * rows), "white")
    for i, sh in enumerate(grp):
        for j, tag in enumerate("abc"):
            f = [x for x in fs if os.path.basename(x).startswith(sh + "_" + tag)]
            if not f: continue
            x = (i % 4) * (3 * w + 6) + j * w; y = (i // 4) * h
            S.paste(Image.open(f[0]), (x, y)); ImageDraw.Draw(S).text((x + 4, y + 4), os.path.basename(f[0])[:-4], fill=(255, 255, 0))
    S.save(out.replace(".jpg", "_%d.jpg" % (k // per)), quality=85)
    print(out.replace(".jpg", "_%d.jpg" % (k // per)))
