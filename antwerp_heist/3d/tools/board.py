"""Storyboard for a part: contact sheet (JPG) + PDF (cover, then 4 shots per page with VO, action, duration, QA).
    python3 tools/board.py P1   -> review/<part>/<PART>_storyboard.pdf, <PART>_contact_sheet.jpg"""
import os, sys, json, textwrap, glob
from PIL import Image, ImageDraw, ImageFont
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PART = sys.argv[1]; p = PART.lower()
SHOTS = sorted(glob.glob(os.path.join(D, "shots", PART, "[A-Z][0-9]*.json")))
info = [json.load(open(f)) for f in SHOTS]
F = lambda s, b=False: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if b else ""), s)
OUT = os.path.join(D, "review", p); os.makedirs(OUT, exist_ok=True)
img = lambda sid: Image.open(os.path.join(D, "out", p, "board", sid + ".png")).convert("RGB")
total = sum(i["dur"] for i in info)

# contact sheet: 6 across
cols = 6; tw, th = 420, 236; pad = 8; cap = 44
rows = (len(info) + cols - 1) // cols
sheet = Image.new("RGB", (cols * (tw + pad) + pad, 90 + rows * (th + cap + pad)), (14, 13, 12))
d = ImageDraw.Draw(sheet)
d.text((pad + 4, 22), f"They Stole $100 Million. Then Threw Away the Evidence.  ·  Part {PART[1:]}  ·  {len(info)} shots  ·  {total:.0f} s, timed to the VO", font=F(30, True), fill=(235, 205, 150))
for k, i in enumerate(info):
    x = pad + (k % cols) * (tw + pad); y = 90 + (k // cols) * (th + cap + pad)
    sheet.paste(img(i["shot"]).resize((tw, th)), (x, y))
    d.text((x + 4, y + th + 4), f"{i['shot']}  {i['dur']:.1f}s", font=F(17, True), fill=(240, 200, 120))
    d.text((x + 4, y + th + 24), textwrap.shorten(i["desc"], 52), font=F(14), fill=(200, 195, 185))
sheet.save(os.path.join(OUT, f"{PART}_contact_sheet.jpg"), quality=90)

# PDF pages (A4 landscape-ish 3508x2480 @300dpi -> use 2480x1754 @212)
W, Hh = 2480, 1754
pages = []
cov = Image.new("RGB", (W, Hh), (14, 13, 12)); d = ImageDraw.Draw(cov)
d.text((120, 120), "They Stole $100 Million.", font=F(96, True), fill=(240, 210, 150))
d.text((120, 240), "Then Threw Away the Evidence.", font=F(96, True), fill=(240, 210, 150))
d.text((120, 400), f"Part {PART[1:]}  —  storyboard (real 3D frames, low samples)", font=F(48), fill=(220, 215, 205))
lines = [f"{len(info)} shots · {total:.0f} s timed to the narration · 2560x1440 · 24 fps · Cycles · Atrium look",
         "All shots built in Blender (sets, cast, props); clipcheck 0 clips on every shot.",
         "Faces: no close-ups (backs, over-the-shoulder, profiles in half shadow, silhouettes).",
         "Camera carries the motion; nothing moves by itself. No burned-in text (cards added in CapCut).",
         "Cast: Leonardo (stocky, grey swept-back hair, navy blazer) · D'Onorio (tall, lean, suede jacket)",
         "Finotto (broad, cropped hair, olive knit sweater) · detectives Peys & De Bruycker · Van Camp · lab technicians · judges."]
for k, t in enumerate(lines):
    d.text((120, 540 + k * 70), t, font=F(36), fill=(200, 195, 185))
cov.paste(sheet.resize((W - 240, int((W - 240) * sheet.height / sheet.width))).crop((0, 0, W - 240, Hh - 1000)), (120, 980))
pages.append(cov)
per = 4; iw, ih = 1100, 619
for s in range(0, len(info), per):
    pg = Image.new("RGB", (W, Hh), (14, 13, 12)); d = ImageDraw.Draw(pg)
    d.text((80, 40), f"Part {PART[1:]} storyboard  ·  page {s // per + 1}", font=F(34, True), fill=(235, 205, 150))
    for k, i in enumerate(info[s:s + per]):
        x = 80 + (k % 2) * (iw + 120); y = 120 + (k // 2) * (ih + 200)
        pg.paste(img(i["shot"]).resize((iw, ih)), (x, y))
        d.text((x, y + ih + 10), f"{i['shot']}   {i['dur']:.1f} s   ·   clips {i['clips']}", font=F(30, True), fill=(240, 200, 120))
        d.text((x, y + ih + 52), textwrap.shorten(i["desc"], 70), font=F(26), fill=(220, 215, 205))
        vo = textwrap.wrap("VO: " + i["vo"], 78)[:3]
        for j, t in enumerate(vo):
            d.text((x, y + ih + 92 + j * 32), t, font=F(23), fill=(160, 158, 150))
    pages.append(pg)
pdf = os.path.join(OUT, f"{PART}_storyboard.pdf")
pages[0].save(pdf, save_all=True, append_images=pages[1:], resolution=212, quality=88)
print(pdf, os.path.getsize(pdf) // 1024, "KB")
