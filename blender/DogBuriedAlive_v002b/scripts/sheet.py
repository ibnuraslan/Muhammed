"""3-frames-per-shot sheet: python3 sheet.py <frames_dir> <out.jpg> [cols_shots=3]"""
import sys, os, re
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; per_row = int(sys.argv[3]) if len(sys.argv) > 3 else 3
fs = sorted(f for f in os.listdir(d) if f.endswith(".jpg"))
shots = {}
for f in fs:
    m = re.match(r"(\d+)_(\w+?)_(\d)_f(\d+)\.jpg", f)
    if m: shots.setdefault((int(m.group(1)), m.group(2)), []).append((int(m.group(3)), int(m.group(4)), f))
keys = sorted(shots)
W, H = Image.open(os.path.join(d, fs[0])).size; s = 0.5; w, h = int(W * s), int(H * s)
rows = (len(keys) + per_row - 1) // per_row
S = Image.new("RGB", (per_row * 3 * w + (per_row - 1) * 12, rows * (h + 22)), "white"); D = ImageDraw.Draw(S)
for i, k in enumerate(keys):
    r, c = divmod(i, per_row); x0 = c * (3 * w + 12); y0 = r * (h + 22)
    for j, fr, f in sorted(shots[k]):
        S.paste(Image.open(os.path.join(d, f)).convert("RGB").resize((w, h)), (x0 + j * w, y0 + 20))
        D.text((x0 + j * w + 4, y0 + 4), f"{k[1]}  f{fr}", fill=(0, 0, 0))
S.save(out, quality=85); print("SHEET", out, S.size)
