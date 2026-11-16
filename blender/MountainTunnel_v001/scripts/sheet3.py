"""python3 sheet3.py FRAMEDIR shots.json OUTPREFIX: 3 frames per shot (first, middle, last), 5 shots per page, labelled"""
import sys, os, json
from PIL import Image, ImageDraw
d, shots, out = sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3]
W, H = 270, 480
per = 5
for p in range(0, len(shots), per):
    grp = shots[p:p + per]
    c = Image.new("RGB", (W * 3 * 2, H * ((len(grp) + 1) // 2)), "white"); dr = ImageDraw.Draw(c)
    for i, s in enumerate(grp):
        fr = (s["f0"], s["f0"] + s["len"] // 2, s["f0"] + s["len"] - 1)
        for j, (f, lab) in enumerate(zip(fr, ("first", "mid", "last"))):
            im = Image.open(os.path.join(d, "f%05d.jpg" % f)).resize((W, H))
            x, y = ((i % 2) * 3 + j) * W, (i // 2) * H
            c.paste(im, (x, y)); dr.rectangle((x, y, x + 120, y + 16), fill=(0, 0, 0)); dr.text((x + 4, y + 3), "%s %s f%d" % (s["id"], lab, f), fill=(255, 255, 0))
    c.save("%s_%d.jpg" % (out, p // per + 1), quality=88)
