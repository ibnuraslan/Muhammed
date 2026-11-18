"""Build the review package from the rendered storyboard frames (system python3 + PIL).

    python3 tools/storyboard.py            -> review/frames/<id>.jpg (1280x720, card + caption burned in as they will play),
                                              review/contact_<n>.jpg sheets, review/STORYBOARD.md, review/sfx_cues.csv
Shot data (VO words, duration, description, SFX, card) is read from shots.py with ast (no Blender needed)."""
import ast, os, sys, csv
from PIL import Image, ImageDraw, ImageFont

P1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(P1, "comp"))
import callout as CO

FONT = os.path.join(P1, "assets", "fonts", "CourierPrime-Regular.ttf")
FONTB = os.path.join(P1, "assets", "fonts", "CourierPrime-Bold.ttf")
PHOTOS = os.path.join(P1, "assets", "photos")


def shots():
    tree = ast.parse(open(os.path.join(P1, "shots.py")).read())
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for d in node.decorator_list:
                if isinstance(d, ast.Call) and getattr(d.func, "id", "") == "shot":
                    a = [ast.literal_eval(x) for x in d.args]
                    kw = {k.arg: ast.literal_eval(k.value) for k in d.keywords}
                    out.append(dict(id=a[0], vo=a[1], dur=a[2], desc=a[3], sfx=a[4], card=kw.get("card"), label=kw.get("label"),
                                    line=node.lineno))
    out.sort(key=lambda s: s["line"])
    return out


def photo_for(label):
    """A real free-license photo for the card if we have one (assets/photos/<slug>.jpg + CREDITS.txt), else None."""
    slug = label.lower().replace(" ", "_").replace(",", "")
    for ext in (".jpg", ".png"):
        p = os.path.join(PHOTOS, slug + ext)
        if os.path.exists(p):
            return p
    return None


def burn_label(im, text, fx, fy):
    """A small burned-in callout (Courier Prime Bold, white, soft shadow) at (fx, fy) of the frame, like '3½ FT'."""
    from PIL import ImageFilter
    W, H = im.size
    f = ImageFont.truetype(FONTB, int(0.03 * H))
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.text((fx * W, fy * H), text, font=f, fill=(255, 255, 255, 255))
    sh = lay.split()[-1].filter(ImageFilter.GaussianBlur(0.004 * H)).point(lambda v: v * 180 // 255)
    shadow = Image.new("RGBA", im.size, (0, 0, 0, 0)); shadow.putalpha(sh)
    out = Image.alpha_composite(im.convert("RGBA"), shadow); out = Image.alpha_composite(out, lay)
    return out.convert("RGB")


def placeholder(size=(400, 440)):
    im = Image.new("RGB", size, (70, 70, 70)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONTB, 34)
    for k, t in enumerate(("PHOTO", "PENDING")):
        bb = d.textbbox((0, 0), t, font=f); d.text(((size[0] - bb[2]) / 2, size[1] / 2 - 40 + k * 46), t, font=f, fill=(200, 200, 200))
    p = os.path.join(P1, "out", "tex", "photo_pending.png"); os.makedirs(os.path.dirname(p), exist_ok=True); im.save(p)
    return p


def main():
    S = shots()
    rv = os.path.join(P1, "review"); fr = os.path.join(rv, "frames"); os.makedirs(fr, exist_ok=True)
    t = 0.0; rows = []; thumbs = []
    for s in S:
        src = os.path.join(P1, "out", "board", s["id"] + ".png")
        if not os.path.exists(src):
            print("missing", s["id"]); t += s["dur"]; continue
        im = Image.open(src).convert("RGB").resize((1280, 720), Image.LANCZOS)
        note = ""
        if s["card"]:
            kind, rest = s["card"].split(":", 1); name, role = rest.split("|")
            ph = photo_for(name)
            if ph is None:
                ph = placeholder(); note = " (photo pending)"
            im = (CO.person_right if kind == "person" else CO.place_left)(im, ph, name, role)
        if s.get("label"):
            im = burn_label(im, *s["label"])
        im = CO.caption(im, s["vo"])
        im.save(os.path.join(fr, s["id"] + ".jpg"), quality=88)
        thumbs.append((s, im))
        rows.append((s, t, note)); t += s["dur"]
    # contact sheets: 12 frames per sheet (3 x 4), with id + timecode under each
    f = ImageFont.truetype(FONTB, 20)
    for k in range(0, len(thumbs), 12):
        grp = thumbs[k:k + 12]
        sheet = Image.new("RGB", (3 * 640 + 40, 4 * (360 + 34) + 20), (18, 18, 18)); d = ImageDraw.Draw(sheet)
        for j, (s, im) in enumerate(grp):
            x = 10 + (j % 3) * 650; y = 10 + (j // 3) * 394
            sheet.paste(im.resize((640, 360), Image.LANCZOS), (x, y))
            tc = next(tt for ss, tt, _ in rows if ss is s)
            d.text((x, y + 364), f"{s['id']}  {int(tc // 60)}:{tc % 60:04.1f}  ({s['dur']:.1f}s)", font=f, fill=(235, 225, 210))
        sheet.save(os.path.join(rv, f"contact_{k // 12 + 1}.jpg"), quality=85)
    # storyboard table and SFX cue list
    with open(os.path.join(rv, "STORYBOARD.md"), "w") as md:
        md.write("# Part 1 storyboard — \"The Ship That Came Back Without Its Crew\"\n\n")
        md.write(f"{len(rows)} shots · {t:.1f} s · 16:9 2560x1440 24 fps (frames here: real Cycles renders at half res, low samples, "
                 "card + caption burned in)\n\n")
        md.write("| # | TC | Dur | VO (verbatim) | Shot | SFX | Card |\n|---|---|---|---|---|---|---|\n")
        for s, tc, note in rows:
            md.write(f"| {s['id']} | {int(tc // 60)}:{tc % 60:04.1f} | {s['dur']:.1f} | {s['vo']} | {s['desc']} | {'; '.join(s['sfx'])} | "
                     f"{(s['card'] or '').replace('|', ' / ')}{note} |\n")
    with open(os.path.join(rv, "sfx_cues.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["shot", "start_s", "end_s", "sfx"])
        for s, tc, _ in rows:
            for x in s["sfx"]:
                w.writerow([s["id"], f"{tc:.2f}", f"{tc + s['dur']:.2f}", x])
    print("shots", len(rows), "total", round(t, 1), "s")


if __name__ == "__main__":
    main()
