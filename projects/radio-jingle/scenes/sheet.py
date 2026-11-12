"""Labelled preview sheet, graded with the house cinematic look:
  python sheet.py out.jpg "1A label" img1 "1B label" img2 ...   (two columns: A left, B right)
Set NOGRADE=1 to skip the grade (raw renders)."""
import os, sys, tempfile
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "nvidia_doc", "scenes"))
out = sys.argv[1]; pairs = list(zip(sys.argv[2::2], sys.argv[3::2]))
graded = []
tmp = tempfile.mkdtemp()
for k, (label, path) in enumerate(pairs):
    if os.environ.get("NOGRADE"):
        graded.append(path); continue
    import grade
    dst = os.path.join(tmp, f"g{k}.png")
    grade.grade_file(os.path.abspath(path), dst, look="cinematic")
    graded.append(dst)
W, H, BAR = 960, 408, 44
font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 24)
rows = (len(pairs) + 1) // 2
S = Image.new("RGB", (W * 2 + 12, rows * (H + BAR) + 6), (14, 16, 20))
d = ImageDraw.Draw(S)
for i, ((label, _), path) in enumerate(zip(pairs, graded)):
    x, y = (i % 2) * (W + 12), (i // 2) * (H + BAR)
    S.paste(Image.open(path).convert("RGB").resize((W, H), Image.LANCZOS), (x, y + BAR))
    d.text((x + 14, y + 9), label, font=font, fill=(235, 236, 240))
S.save(out, quality=86)
print("[sheet]", out)
