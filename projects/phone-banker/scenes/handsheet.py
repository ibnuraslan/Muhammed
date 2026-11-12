"""Grade the hand crops (EXR from handcrops.py) and lay them out as a labelled grid.
  python handsheet.py <crop_dir> <out.jpg>
"""
import os, sys, json, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "nvidia_doc", "scenes"))
from PIL import Image, ImageDraw, ImageFont
import grade

src, out = sys.argv[1], sys.argv[2]
tmp = os.path.join(src, "_graded"); os.makedirs(tmp, exist_ok=True)
cells = []
for exr in sorted(glob.glob(os.path.join(src, "*.exr"))):
    base = os.path.splitext(exr)[0]
    meta = json.load(open(base + ".json"))
    dst = os.path.join(tmp, os.path.basename(base) + ".png")
    grade.grade_file(exr, dst, look="cinematic", exposure=meta["exposure"])
    parts = os.path.basename(base).split("_")
    t_i = next(i for i, p_ in enumerate(parts) if p_.replace(".", "").isdigit())
    label = f"{parts[0]} {' '.join(parts[1:t_i])} t{parts[t_i]} - {parts[t_i + 1]} {'left' if parts[-1] == 'L' else 'right'} hand"
    cells.append((label, dst))

TW, TH, pad, lab, cols = 420, 420, 12, 30, 4
font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Medium.otf", 17)
head = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 24)
rows = (len(cells) + cols - 1) // cols
S = Image.new("RGB", (pad + cols * (TW + pad), 60 + rows * (TH + lab + pad)), (14, 14, 16))
d = ImageDraw.Draw(S)
d.text((pad, 16), "Hand close-ups (full resolution crops, cinematic grade): wrists straight, thumbs on the natural side", font=head, fill=(235, 235, 235))
for i, (label, p) in enumerate(cells):
    im = Image.open(p).convert("RGB")
    k = min(TW / im.width, TH / im.height)                                        # small (distant) hands are scaled up
    im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
    x = pad + (i % cols) * (TW + pad); y = 60 + (i // cols) * (TH + lab + pad)
    d.text((x, y + 4), label, font=font, fill=(200, 200, 200))
    S.paste(im, (x + (TW - im.width) // 2, y + lab + (TH - im.height) // 2))
S.save(out, quality=90)
print("[hands]", out)
