import sys; sys.path.insert(0, "/home/user/Muhammed/thumbnails/drain")
from make import ANTON, W, H, YEL, WHITE
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S = sys.argv[1]
base = Image.open(S + "/dd/v3e/dd_velvet.png").convert("RGB").resize((W, H), Image.LANCZOS).convert("RGBA")
RED = (230, 30, 30)
def shadow(img, T, r=16, k=1.0):
    sh = T.split()[-1].filter(ImageFilter.GaussianBlur(r)).point(lambda v: int(min(255, v * k)))
    b = Image.new("RGBA", (W, H), (0, 0, 0, 0)); b.putalpha(sh); img.alpha_composite(b); img.alpha_composite(b)
def runs(d, x, y, parts, f, anchor="l"):
    sp = d.textlength(" ", font=f) * 0.85; tot = sum(d.textlength(t, font=f) for t, _ in parts) + sp * (len(parts) - 1)
    if anchor == "c": x = x - tot / 2
    for t, c in parts:
        d.text((x, y), t, font=f, fill=c + (255,), stroke_width=4, stroke_fill=(0, 0, 0, 255)); x += d.textlength(t, font=f) + sp
def A():
    img = base.copy(); T = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(T)
    runs(d, W / 2, 10, [("$25M…", YEL)], ImageFont.truetype(ANTON, 240), "c")
    runs(d, W / 2, 290, [("SEALED", RED), ("UNDER", WHITE), ("A", WHITE), ("DRAIN", WHITE)], ImageFont.truetype(ANTON, 130), "c")
    shadow(img, T); img.alpha_composite(T); return img
def B():
    img = base.copy(); T = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(T)
    runs(d, 60, 40, [("$25M…", YEL)], ImageFont.truetype(ANTON, 230))
    runs(d, 60, 330, [("SEALED", RED)], ImageFont.truetype(ANTON, 190))
    runs(d, 60, 560, [("UNDER A", WHITE)], ImageFont.truetype(ANTON, 120))
    runs(d, 60, 720, [("DRAIN", WHITE)], ImageFont.truetype(ANTON, 190))
    shadow(img, T); img.alpha_composite(T); return img
def C():
    img = base.copy(); T = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(T)
    f = ImageFont.truetype(ANTON, 150)
    runs(d, W / 2, 30, [("$25M", YEL), ("DIAMOND…", WHITE)], f, "c")
    # red banner
    f2 = ImageFont.truetype(ANTON, 110); txt = "SEALED UNDER A DRAIN"; w = d.textlength(txt, font=f2)
    d.rectangle([W / 2 - w / 2 - 30, 228, W / 2 + w / 2 + 30, 370], fill=(200, 20, 20, 255))
    d.text((W / 2 - w / 2, 232), txt, font=f2, fill=WHITE + (255,))
    shadow(img, T, 14, 0.8); img.alpha_composite(T); return img
ims = [A(), B(), C()]
for k, im in zip("ABC", ims): im.convert("RGB").save(f"{S}/dd/var_{k}.jpg", quality=92)
sheet = Image.new("RGB", (1920, 1660), (20, 20, 20)); dd = ImageDraw.Draw(sheet); lf = ImageFont.truetype(ANTON, 60)
for i, im in enumerate(ims):
    x, y = (i % 2) * 960, (i // 2) * 600
    sheet.paste(im.convert("RGB").resize((940, 529)), (x + 10, y + 60)); dd.text((x + 20, y), "ABC"[i], font=lf, fill=(255, 255, 255))
sheet.crop((0, 0, 1920, 1200)).save(f"{S}/dd/var_sheet.jpg", quality=90)
