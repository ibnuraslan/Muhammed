"""Contact sheet of hand crops: python tools/hand_sheet.py out.jpg out/hands [filter]  (skips *_hidden crops)"""
import sys, os, glob
from PIL import Image, ImageDraw, ImageFont
out, root = sys.argv[1], sys.argv[2]; flt = sys.argv[3] if len(sys.argv) > 3 else ""
F = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 13)
items = sorted(p for p in glob.glob(os.path.join(root, "*", "hand_*.png")) if "_hidden" not in p and flt in p)
C = 8; S = 200; rows = (len(items) + C - 1) // C
sheet = Image.new("RGB", (C * (S + 6) + 6, rows * (S + 22) + 6), (18, 18, 20)); d = ImageDraw.Draw(sheet)
for i, p in enumerate(items):
    x = 6 + (i % C) * (S + 6); y = 6 + (i // C) * (S + 22)
    sheet.paste(Image.open(p).convert("RGB").resize((S, S)), (x, y + 18))
    lab = os.path.basename(os.path.dirname(p)) + " " + os.path.basename(p)[5:-4].split("_rig")[0][-10:]
    d.text((x, y + 2), lab[:30], font=F, fill=(230, 220, 200))
sheet.save(out, quality=85); print(out, len(items))
