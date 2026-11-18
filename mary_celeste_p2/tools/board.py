"""Build review/ from rendered frames: one annotated JPG per shot + a contact sheet + STORYBOARD.md."""
import os, sys, textwrap
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); P2 = os.path.dirname(HERE)
sys.path.insert(0, P2)
from shots import SHOTS
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(P2, "out", "frames")
OUT = os.path.join(P2, "review"); os.makedirs(OUT, exist_ok=True)
F = os.path.join(P2, "assets", "fonts")
fb = ImageFont.truetype(os.path.join(F, "CourierPrime-Bold.ttf"), 26)
fr = ImageFont.truetype(os.path.join(F, "CourierPrime-Regular.ttf"), 22)
W, H = 1280, 720
tiles = []
md = ["# Part 2 storyboard — real 3D frames (Cycles, low samples)", "",
      "| # | VO (word for word) | Shot | Action | SFX | Card / tag | Frame |", "|---|---|---|---|---|---|---|"]
for sid, scene, vo, shot, action, sfx, card in SHOTS:
    p = os.path.join(SRC, f"{sid}.png")
    if not os.path.exists(p):
        continue
    im = Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS)
    pan = Image.new("RGB", (W, H + 210), (14, 12, 11)); pan.paste(im, (0, 0))
    d = ImageDraw.Draw(pan)
    d.text((24, H + 14), f"{sid}  {shot}", font=fb, fill=(240, 200, 140))
    y = H + 50
    for line in textwrap.wrap(f'VO: "{vo}"', 100)[:2] + textwrap.wrap(f"{action}", 100)[:2] + \
            textwrap.wrap(f"SFX: {sfx}" + (f"   |   {card}" if card else ""), 100)[:2]:
        d.text((24, y), line, font=fr, fill=(225, 220, 210)); y += 26
    fn = f"sb_{sid}.jpg"; pan.save(os.path.join(OUT, fn), quality=88)
    tiles.append(pan)
    md.append(f"| {sid} | {vo} | {shot} | {action} | {sfx} | {card} | review/{fn} |")
cols = 4; tw, th = 480, int(480 * (H + 210) / W)
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, rows * th), (0, 0, 0))
for i, t in enumerate(tiles):
    sheet.paste(t.resize((tw, th), Image.LANCZOS), ((i % cols) * tw, (i // cols) * th))
sheet.save(os.path.join(OUT, "contact_sheet.jpg"), quality=85)
open(os.path.join(P2, "STORYBOARD.md"), "w").write("\n".join(md) + "\n")
print(len(tiles), "panels")
