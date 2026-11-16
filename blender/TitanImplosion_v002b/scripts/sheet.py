"""3-frame sheet: one row per shot (first | middle | last), labelled.  python3 -I sheet.py <dir> <out.jpg> [cell_w=270]"""
import sys, os, glob
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; cw = int(sys.argv[3]) if len(sys.argv) > 3 else 270
fs = sorted(glob.glob(os.path.join(d, "S*_*.jpg")))
shots = sorted({os.path.basename(f).split("_")[0] for f in fs})
ch = round(cw * 16 / 9); per = 3
cols = 2  # two shots per row -> 6 cells
rows = (len(shots) + cols - 1) // cols
S = Image.new("RGB", (cols * (per * cw + 12), rows * (ch + 18)), "white"); D = ImageDraw.Draw(S)
for i, sid in enumerate(shots):
    x0 = (i % cols) * (per * cw + 12); y0 = (i // cols) * (ch + 18)
    for j, tag in enumerate("abc"):
        f = [x for x in fs if os.path.basename(x).startswith(sid + "_" + tag)]
        if not f: continue
        im = Image.open(f[0]).convert("RGB").resize((cw, ch)); S.paste(im, (x0 + j * cw, y0 + 16))
        D.text((x0 + j * cw + 3, y0 + 2), "%s %s f%s" % (sid, ["first", "mid", "last"][j], os.path.basename(f[0]).split("_")[2][:5]), fill=(0, 0, 0))
S.save(out, quality=85); print("SHEET", out, S.size)
