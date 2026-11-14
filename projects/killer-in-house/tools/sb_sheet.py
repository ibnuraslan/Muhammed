"""STORYBOARD v2 before/after sheet: one row per changed shot -> shot + new idea | BEFORE still | AFTER still.
  python tools/sb_sheet.py out.jpg "title" "shot|before_dir|after_dir|new idea" ...   (dirs hold plate.png; after_dir may be a.b list with commas)"""
import sys, os, textwrap
from PIL import Image, ImageDraw, ImageFont
out, title, rows = sys.argv[1], sys.argv[2], sys.argv[3:]
W = 560; H = int(W * 816 / 1920); TXT = 360; PAD = 10; HEAD = 70
F = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 19)
FS = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 15)
FT = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 28)
sheet = Image.new("RGB", (TXT + 2 * W + 4 * PAD, HEAD + len(rows) * (H + PAD) + PAD), (18, 18, 20))
d = ImageDraw.Draw(sheet); d.text((PAD, 12), title, font=FT, fill=(235, 235, 235))
d.text((TXT + 2 * PAD, HEAD - 24), "BEFORE (approved v1)", font=FS, fill=(170, 170, 170))
d.text((TXT + W + 3 * PAD, HEAD - 24), "AFTER (storyboard v2)", font=FS, fill=(235, 200, 120))
for i, r in enumerate(rows):
    shot, bdir, adir, idea = r.split("|", 3)
    y = HEAD + i * (H + PAD)
    d.text((PAD, y + 4), shot, font=F, fill=(240, 225, 190))
    for k, line in enumerate(textwrap.wrap(idea, 40)[:8]):
        d.text((PAD, y + 34 + k * 19), line, font=FS, fill=(200, 200, 200))
    for j, dd in enumerate((bdir, adir)):
        x = TXT + 2 * PAD + j * (W + PAD); p = os.path.join(dd, "plate.png")
        if dd and os.path.exists(p):
            sheet.paste(Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS), (x, y))
        else:
            d.rectangle([x, y, x + W, y + H], fill=(40, 30, 30)); d.text((x + 16, y + 16), "(new shot, no v1)" if j == 0 else "missing", font=FS, fill=(220, 190, 190))
sheet.save(out, quality=86); print(out, sheet.size)
