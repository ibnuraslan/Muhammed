"""Storyboard boards for Part 3: each real 3D frame with its burned-in caption (Courier Prime, the shared
callout.py style), its person/place card where the shot has one, and a notes strip (VO, size, action, SFX).
    python3 tools/board.py            -> review/boards/p3_XX.jpg + review/P3_STORYBOARD.pdf + review/contact.jpg"""
import os, sys, re, ast
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "shared"))
import callout as CO
F = os.path.join(ROOT, "assets", "fonts")
REV = os.path.join(ROOT, "review"); BO = os.path.join(REV, "boards"); os.makedirs(BO, exist_ok=True)
PH = os.path.join(ROOT, "assets", "photos")


def shots_meta():
    """Read the @shot(...) decorators from shots.py without importing Blender."""
    src = open(os.path.join(ROOT, "shots.py")).read()
    out = []
    for m in re.finditer(r'@shot\((.*?)\)\ndef ', src, re.S):
        node = ast.parse("f(" + m.group(1) + ")").body[0].value
        args = [ast.literal_eval(a) for a in node.args]
        kw = {k.arg: ast.literal_eval(k.value) for k in node.keywords}
        sid, vo, size, dur, action, sfx = args[:6]
        out.append(dict(sid=sid, vo=vo, size=size, dur=dur, action=action, sfx=sfx, card=kw.get("card"), tag=kw.get("tag")))
    return out


def placeholder(path, label):
    if os.path.exists(path):
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im = Image.new("L", (600, 650), 120); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(os.path.join(F, "CourierPrime-Bold.ttf"), 34)
    for i, line in enumerate(["PHOTO", "PENDING", label]):
        d.text((300, 250 + i * 50), line, font=f, fill=230, anchor="mm")
    im.save(path)
    return path


def date_tag(im, text):
    d = ImageDraw.Draw(im); W, H = im.size
    f = ImageFont.truetype(os.path.join(F, "CourierPrime-Bold.ttf"), int(H * 0.034))
    d.text((W / 2 + 2, H * 0.085 + 2), text, font=f, fill=(0, 0, 0), anchor="mm")
    d.text((W / 2, H * 0.085), text, font=f, fill=(255, 255, 255), anchor="mm")
    return im


def frame_with_graphics(s, im):
    if s["card"]:
        side, name, role = s["card"]
        photo = os.path.join(PH, re.sub(r"[^a-z]+", "_", name.lower()).strip("_") + ".jpg")
        if not os.path.exists(photo):
            photo = placeholder(os.path.join(PH, "_pending_" + re.sub(r"[^a-z]+", "_", name.lower()).strip("_") + ".png"), name.split()[-1])
        im = (CO.person_right if side == "r" else CO.place_left)(im, photo, name, role)
    if s["tag"]:
        im = date_tag(im, s["tag"])
    return CO.caption(im, s["vo"])


def board(s, t0):
    src = os.path.join(REV, s["sid"] + ".png")
    if not os.path.exists(src):
        return None
    im = Image.open(src).convert("RGB").resize((1280, 720), Image.LANCZOS)
    im = frame_with_graphics(s, im)
    W = 1280; H = 720 + 200
    B = Image.new("RGB", (W, H), (18, 16, 15)); B.paste(im, (0, 0)); d = ImageDraw.Draw(B)
    fb = ImageFont.truetype(os.path.join(F, "CourierPrime-Bold.ttf"), 26); fr = ImageFont.truetype(os.path.join(F, "CourierPrime-Regular.ttf"), 20)
    d.text((24, 736), f"{s['sid'].upper()}   {s['size']}   {s['dur']:.1f}s   @{t0 // 60:.0f}:{t0 % 60:04.1f}", font=fb, fill=(240, 200, 120))
    y = 776
    for lab, txt in (("VO", s["vo"]), ("ACTION", s["action"]), ("SFX", s["sfx"])):
        d.text((24, y), f"{lab:<7}", font=fb, fill=(200, 200, 200))
        words = txt.split(); line = ""
        for w in words:
            if d.textlength(line + " " + w, font=fr) > W - 170:
                d.text((150, y + 4), line.strip(), font=fr, fill=(235, 235, 235)); y += 26; line = ""
            line += " " + w
        d.text((150, y + 4), line.strip(), font=fr, fill=(235, 235, 235)); y += 34
    out = os.path.join(BO, s["sid"] + ".jpg"); B.save(out, quality=88)
    return out


if __name__ == "__main__":
    S = shots_meta(); t = 0.0; outs = []
    for s in S:
        o = board(s, t); t += s["dur"]
        if o:
            outs.append(o)
    print("shots", len(S), "total", round(t, 1), "s; boards", len(outs))
    if outs:
        ims = [Image.open(o).convert("RGB") for o in outs]
        ims[0].save(os.path.join(REV, "P3_STORYBOARD.pdf"), save_all=True, append_images=ims[1:], resolution=100)
        # contact sheet: 4 across
        cw, ch = 480, 345; cols = 4; rows = (len(ims) + cols - 1) // cols
        C = Image.new("RGB", (cw * cols, ch * rows), (10, 10, 10))
        for i, b in enumerate(ims):
            C.paste(b.resize((cw, ch)), ((i % cols) * cw, (i // cols) * ch))
        C.save(os.path.join(REV, "contact.jpg"), quality=85)
