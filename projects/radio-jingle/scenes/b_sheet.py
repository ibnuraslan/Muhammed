"""Labelled preview sheet (graded with the cinematic look), two columns.
  python b_sheet.py out.jpg "img1.png|1A label" "img2.png|1B label" ...  [--nograde]
"""
import os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "nvidia_doc", "scenes"))
from PIL import Image, ImageDraw, ImageFont

out = sys.argv[1]
items = [a.split("|", 1) for a in sys.argv[2:] if not a.startswith("--")]
grade_it = "--nograde" not in sys.argv
tmp = tempfile.mkdtemp()
if grade_it:
    import grade
    graded = []
    for k, (p, lab) in enumerate(items):
        dst = os.path.join(tmp, f"g{k}.png")
        grade.grade_file(os.path.abspath(p), dst, look="cinematic")
        graded.append((dst, lab))
    items = graded
W, H, BAR = 960, 408, 44
cols = 2; rows = (len(items) + 1) // 2
sheet = Image.new("RGB", (W * cols, (H + BAR) * rows), (14, 16, 20))
d = ImageDraw.Draw(sheet)
font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 26)
for k, (p, lab) in enumerate(items):
    im = Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS)
    x, y = (k % cols) * W, (k // cols) * (H + BAR)
    sheet.paste(im, (x, y + BAR)); d.text((x + 14, y + 8), lab, font=font, fill=(235, 235, 235))
sheet.save(out, quality=88)
print("[sheet]", out)
