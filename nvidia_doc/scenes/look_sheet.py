"""Before/after sheet for the house look: for each shot, plain (old light + plain grade) | cinematic grade only |
cinematic (look.py light + cinematic grade). Inputs are scene-linear EXR stills from run.py --exr (--plain for the
'before'), so the grade is exactly what a real render gets.
  python look_sheet.py out.jpg "Label" plain_dir cine_dir ["Label" plain_dir cine_dir ...]
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFont
import grade

out, rest = sys.argv[1], sys.argv[2:]
rows = [rest[i:i + 3] for i in range(0, len(rest), 3)]
tmp = os.path.join(os.path.dirname(os.path.abspath(out)), "_sheet_tmp"); os.makedirs(tmp, exist_ok=True)
cells = []
for k, (label, pd, cd) in enumerate(rows):
    row = []
    for tag, d, lk in (("plain", pd, "plain"), ("grade only", pd, "cinematic"), ("cinematic", cd, "cinematic")):
        meta = json.load(open(os.path.join(d, "plate.json")))
        dst = os.path.join(tmp, f"{k}_{lk}_{os.path.basename(d.rstrip('/'))}.png")
        grade.grade_file(os.path.join(d, "plate.exr"), dst, look=lk, exposure=meta["exposure"],
                         cine=meta.get("cine") if d == cd else None)
        row.append((tag, dst))
    cells.append((label, row))

W = 760
font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 22)
small = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Medium.otf", 18)
ims = [[Image.open(p).convert("RGB") for _, p in r] for _, r in cells]
h = int(W * ims[0][0].height / ims[0][0].width)
pad, head, lab = 14, 46, 34
sheet = Image.new("RGB", (pad + 3 * (W + pad), head + len(cells) * (h + lab + pad)), (14, 14, 16))
d = ImageDraw.Draw(sheet)
for j, t in enumerate(("BEFORE: plain light + plain grade", "cinematic grade only", "AFTER: cinematic light + grade")):
    d.text((pad + j * (W + pad), 12), t, font=font, fill=(235, 235, 235))
for i, (label, row) in enumerate(cells):
    y = head + i * (h + lab + pad)
    d.text((pad, y + 4), label, font=small, fill=(200, 200, 200))
    for j, im in enumerate(ims[i]):
        sheet.paste(im.resize((W, h), Image.LANCZOS), (pad + j * (W + pad), y + lab))
sheet.save(out, quality=88)
print("[sheet]", out)
