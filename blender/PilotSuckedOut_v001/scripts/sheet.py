"""contact sheet: rows of shots, 3 frames each, labelled. python3 sheet.py frames_dir out.jpg [cols_of_shots]"""
import sys, os, re
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; per = int(sys.argv[3]) if len(sys.argv) > 3 else 4
fs = sorted(f for f in os.listdir(d) if f.endswith(".jpg"))
shots = {}
for f in fs:
    m = re.match(r"(\w+?)_(\d)_f(\d+)\.jpg", f)
    if m: shots.setdefault(m.group(1), []).append((int(m.group(2)), f, int(m.group(3))))
ids = sorted(shots); im0 = Image.open(os.path.join(d, fs[0])); w, h = im0.size; sc_ = 0.5 if w >= 540 else 1.0
tw, th = int(w * sc_), int(h * sc_); pad = 6
rows = (len(ids) + per - 1) // per
S = Image.new("RGB", (per * (3 * tw + 2 * 2 + pad * 2), rows * (th + 26)), (30, 30, 30)); dr = ImageDraw.Draw(S)
for k, sid in enumerate(ids):
    r_, c_ = divmod(k, per); x0 = c_ * (3 * tw + 4 + pad * 2); y0 = r_ * (th + 26)
    for j, f, fr in sorted(shots[sid]):
        im = Image.open(os.path.join(d, f)).resize((tw, th)); S.paste(im, (x0 + j * (tw + 2), y0 + 22))
        dr.text((x0 + j * (tw + 2) + 3, y0 + 4), f"S{sid} f{fr}", fill=(255, 255, 0))
S.save(out, quality=88); print(out, S.size)
