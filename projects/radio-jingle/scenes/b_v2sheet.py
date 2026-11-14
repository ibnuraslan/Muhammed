"""STORYBOARD_v2 before/after sheets: one row per changed shot, left = v1 frame (cropped from the approved v3 chapter
sheet), right = the v2 render (graded like every sheet). New shots show "new shot" on the left.
  python b_v2sheet.py V1_DIR ST_DIR OUT_DIR [t]
"""
import os, sys, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "nvidia_doc", "scenes"))
from PIL import Image, ImageDraw, ImageFont
import grade
import b_shots

v1dir, st, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
T = sys.argv[4] if len(sys.argv) > 4 else "0.5"
W, H, BAR = 960, 408, 44
font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 24)
small = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Medium.otf", 20)
tmp = tempfile.mkdtemp()
for ch in ("ch3", "ch4", "ch5"):
    n = ch[2]
    old = Image.open(os.path.join(v1dir, f"b_ch{n}_sheet.jpg")).convert("RGB")
    v1_labels = [l.split(" ")[0] for (_, _, l) in b_shots.CHAPTERS_V1[ch]]
    rows = []
    for (s, m, lab, v1id) in b_shots.CHAPTERS[ch]:
        sid = lab.split(" ")[0]
        if sid not in b_shots.CHANGED:
            continue
        if v1id and v1id in v1_labels:
            k = v1_labels.index(v1id)
            x, y = (k % 2) * W, (k // 2) * (H + BAR) + BAR
            left = old.crop((x, y, x + W, y + H))
        else:
            left = Image.new("RGB", (W, H), (24, 26, 30)); ImageDraw.Draw(left).text((W // 2 - 60, H // 2 - 14), "new shot", font=font, fill=(150, 150, 150))
        d = os.path.join(st, f"{s}_{m}_{T}")
        if os.path.exists(os.path.join(d, "plate.exr")):
            meta = json.load(open(os.path.join(d, "plate.json"))); png = os.path.join(tmp, f"{s}_{m}.png")
            grade.grade_file(os.path.join(d, "plate.exr"), png, look="cinematic", exposure=meta["exposure"], cine=meta.get("cine") or None)
            right = Image.open(png).convert("RGB").resize((W, H), Image.LANCZOS)
        else:
            right = Image.new("RGB", (W, H), (40, 20, 20)); ImageDraw.Draw(right).text((40, H // 2), "missing render", font=font, fill=(220, 120, 120))
        rows.append((lab, v1id, left, right))
    sheet = Image.new("RGB", (W * 2, (H + BAR) * len(rows)), (14, 16, 20)); dr = ImageDraw.Draw(sheet)
    for r, (lab, v1id, left, right) in enumerate(rows):
        y = r * (H + BAR)
        dr.text((14, y + 9), f"v1  {v1id or '-'}", font=small, fill=(170, 170, 170))
        dr.text((W + 14, y + 8), f"v2  {lab}", font=font, fill=(240, 240, 240))
        sheet.paste(left, (0, y + BAR)); sheet.paste(right, (W, y + BAR))
    out = os.path.join(outdir, f"b_v2_{ch}.jpg"); sheet.save(out, quality=86); print("[v2sheet]", out, len(rows), "rows")
