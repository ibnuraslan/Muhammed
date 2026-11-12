"""Labelled preview sheet, two columns, graded exactly like a real render (EXR stills from b_run.py), plus an
optional hand-crop strip (every visible wrist, close crops) for the hands QA rule.
  python b_sheet.py out.jpg "DIR|label" "DIR|label" ... [--hands out_hands.jpg]
DIR holds plate.exr + plate.json (+ hands.json). A plain .png path is pasted as is.
"""
import os, sys, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "nvidia_doc", "scenes"))
from PIL import Image, ImageDraw, ImageFont

argv = sys.argv[1:]
hands_out = None
if "--hands" in argv:
    i = argv.index("--hands"); hands_out = argv[i + 1]; argv = argv[:i] + argv[i + 2:]
out = argv[0]
items = [a.split("|", 1) for a in argv[1:]]
tmp = tempfile.mkdtemp()
import grade
done = []
for k, (p, lab) in enumerate(items):
    if os.path.isdir(p):
        meta = json.load(open(os.path.join(p, "plate.json")))
        dst = os.path.join(tmp, f"g{k}.png")
        grade.grade_file(os.path.join(p, "plate.exr"), dst, look="cinematic", exposure=meta["exposure"], cine=meta.get("cine") or None)
        hj = os.path.join(p, "hands.json")
        done.append((dst, lab, json.load(open(hj)) if os.path.exists(hj) else []))
    else:
        done.append((p, lab, []))
W, H, BAR = 960, 408, 44
font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 26)
small = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Medium.otf", 16)
rows = (len(done) + 1) // 2
sheet = Image.new("RGB", (W * 2, (H + BAR) * rows), (14, 16, 20)); d = ImageDraw.Draw(sheet)
crops = []
for k, (p, lab, hands) in enumerate(done):
    im = Image.open(p).convert("RGB")
    x, y = (k % 2) * W, (k // 2) * (H + BAR)
    sheet.paste(im.resize((W, H), Image.LANCZOS), (x, y + BAR)); d.text((x + 14, y + 8), lab, font=font, fill=(235, 235, 235))
    for h in hands:
        r = max(0.07, min(0.2, 0.22 / max(h["dist"], 0.4))) * im.height
        cx, cy = h["x"] * im.width, h["y"] * im.height
        c = im.crop((int(cx - r), int(cy - r), int(cx + r), int(cy + r))).resize((240, 240), Image.LANCZOS)
        crops.append((c, lab.split(" ")[0] + f" {h['side']}"))
sheet.save(out, quality=88); print("[sheet]", out)
if hands_out and crops:
    n = 8; rows = (len(crops) + n - 1) // n
    strip = Image.new("RGB", (n * 244, rows * 268), (14, 16, 20)); d = ImageDraw.Draw(strip)
    for k, (c, lab) in enumerate(crops):
        x, y = (k % n) * 244, (k // n) * 268
        strip.paste(c, (x, y + 24)); d.text((x + 4, y + 3), lab, font=small, fill=(220, 220, 220))
    strip.save(hands_out, quality=88); print("[hands]", hands_out, len(crops))
