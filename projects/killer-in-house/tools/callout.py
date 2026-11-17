"""Real-photo callouts (STYLE SAMPLE, Nov 17): the first time a real person or city appears, a real public-domain photo
sits beside the 3D shot, joined to the character/place by an arrow or line, with a small name label.
Three styles:  A "evidence print"  ·  B "clean editorial"  ·  C "case file".
Calm and premium: no fake software windows, no sci-fi backgrounds, no glow; at most ~20% of the frame.

  python tools/callout.py still <plate.png> <photo.jpg> <out.png> --style A --target 0.62,0.48 --corner tl \
         --name "PHILIP PETERS, 73" --role "retired railroad man" [--kind person|city]
  python tools/callout.py anim  <frames_dir> <photo.jpg> <out.mp4> --style A --track track.json --corner tl ...
Animation (4 s at 24 fps): photo eases in (no bounce) 0-0.5 s · line/arrow draws on 0.4-1.0 s · label fades in
0.8-1.1 s · holds ~2.5 s · everything fades out 3.6-4.0 s."""
import os, sys, math, json, glob, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "..", "..", "nvidia_doc", "assets", "fonts")
SLAB_B = os.path.join(FONTS, "RobotoSlab-ExtraBold.ttf"); SLAB = os.path.join(FONTS, "RobotoSlab-Bold.ttf")
SERIF = os.path.join(FONTS, "SourceSerif4Regular.ttf"); SERIF_I = os.path.join(FONTS, "SourceSerif4Italic.ttf")
MONO = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"
LIME = (212, 255, 0); WARM = (244, 238, 224)
W, H = 1920, 816


def ease_out(x):
    x = min(1.0, max(0.0, x)); return 1 - (1 - x) ** 3


def ease_io(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def F(p, s):
    return ImageFont.truetype(p, s)


def prep_photo(path, kind, size):
    """Crop to the inset's aspect (person: 4:5 head-and-shoulders, city: 4:3), keep the period B&W, gentle contrast."""
    im = Image.open(path).convert("L")
    w, h = im.size
    tw, th = size; ar = tw / th
    if kind == "person":                     # the stand-in's head is upper right of the frame
        cw = int(h * 0.64 * ar); ch = int(h * 0.64); cx = int(w * 0.75); cy = int(h * 0.44)
    else:
        cw = min(int(w * 0.9), int(h * 0.9 * ar)); ch = int(cw / ar); cx = w // 2; cy = int(h * 0.5)      # trims the negative's edge numbers
    box = (max(0, cx - cw // 2), max(0, cy - ch // 2)); box = (min(box[0], w - cw), min(box[1], h - ch))
    im = im.crop((box[0], box[1], box[0] + cw, box[1] + ch)).resize(size, Image.LANCZOS)
    im = ImageOps.autocontrast(im, cutoff=1)
    tone = ImageOps.colorize(im, (18, 16, 14), (238, 232, 220))     # a faint warm silver print, not sepia
    return tone.convert("RGB")


def paper(size, tone, seed=1, amt=10):
    rng = np.random.default_rng(seed)
    a = np.ones((size[1], size[0], 3)) * np.array(tone, float)
    a += rng.normal(0, amt * 0.35, (size[1], size[0], 1))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def shadow_of(card, blur=14, alpha=120, offset=(10, 14)):
    a = card.split()[-1]
    sh = Image.new("RGBA", (card.width + 80, card.height + 80), (0, 0, 0, 0))
    m = Image.new("L", sh.size, 0); m.paste(a, (40 + offset[0], 40 + offset[1]))
    m = m.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: v * alpha // 255)
    sh.putalpha(m); return sh


# ---------------------------------------------------------------------------------------------------- the 3 cards
def card_A(photo, name, role):
    """Evidence print: white border, paper tooth, slight tilt; the name in the title font under the photo."""
    pw, ph = photo.size; b = 14; bb = 16
    c = paper((pw + 2 * b, ph + b + bb), (241, 238, 230), seed=3, amt=12).convert("RGBA")
    c.paste(photo, (b, b))
    edge = ImageDraw.Draw(c); edge.rectangle([0, 0, c.width - 1, c.height - 1], outline=(214, 210, 200, 255), width=1)
    return c, (name, role)


def card_B(photo, name, role):
    """Clean editorial: crisp photo, thin white keyline; label set beside it (drawn by the layout)."""
    pw, ph = photo.size; k = 2
    c = Image.new("RGBA", (pw + 2 * k, ph + 2 * k), (255, 255, 255, 235)); c.paste(photo, (k, k))
    return c, (name, role)


def card_C(photo, name, role, extra=""):
    """Case file: manila card, the photo held by a paper clip, a typed name strip."""
    pw, ph = photo.size; m = 18
    cw, chh = pw + 2 * m, ph + m + 96
    c = paper((cw, chh), (205, 178, 128), seed=7, amt=14).convert("RGBA")
    d = ImageDraw.Draw(c)
    d.rectangle([0, 0, cw - 1, chh - 1], outline=(168, 140, 92, 255), width=2)
    # photo with a thin white border, a little offset like it was clipped on by hand
    pb = Image.new("RGBA", (pw + 10, ph + 10), (240, 236, 226, 255)); pb.paste(photo, (5, 5))
    pb = pb.rotate(1.2, expand=True, resample=Image.BICUBIC)
    c.alpha_composite(pb, (m - 4, m - 6))
    # typed strip (typewriter on a white label)
    lab = paper((cw - 2 * m, 62), (238, 234, 222), seed=9, amt=8)
    ld = ImageDraw.Draw(lab); ld.text((12, 6), name, font=F(MONO, 18), fill=(30, 28, 26)); ld.text((12, 34), role, font=F(MONO, 15), fill=(60, 56, 50))
    c.paste(lab, (m, ph + m + 20))
    # paper clip (steel wire, drawn as two nested rounded loops, over the photo's top edge)
    clip = Image.new("RGBA", (40, 92), (0, 0, 0, 0)); cd = ImageDraw.Draw(clip)
    for (x0, y0, x1, y1) in ((4, 2, 34, 88), (11, 14, 27, 70)):
        cd.rounded_rectangle([x0, y0, x1, y1], radius=(x1 - x0) // 2, outline=(150, 152, 156, 255), width=4)
        cd.rounded_rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], radius=(x1 - x0) // 2, outline=(210, 212, 216, 255), width=1)
    c.alpha_composite(clip, (cw - 70, -2) if False else (cw - 72, 0))
    return c, None


# ---------------------------------------------------------------------------------------------------- lines
def bezier(p0, p1, p2, n=80):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in np.linspace(0, 1, n)]


def hand_arrow(d, p0, p2, prog, col, width=5, seed=2, bend=0.22):
    """A hand-drawn-feel arrow: a curved stroke of slightly varying width with a two-stroke head; prog 0..1 draws it on."""
    if prog <= 0:
        return
    rng = np.random.default_rng(seed)
    mx, my = (p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2; dx, dy = p2[0] - p0[0], p2[1] - p0[1]
    p1 = (mx - dy * bend, my + dx * bend)
    pts = bezier(p0, p1, p2)
    k = max(2, int(len(pts) * prog))
    for i in range(k - 1):
        wv = width * (0.75 + 0.35 * math.sin(i * 0.21 + 1.3)) * (0.85 + 0.15 * rng.random())
        d.line([pts[i], pts[i + 1]], fill=col, width=max(2, int(round(wv))))
    if prog >= 0.98:                         # the head: two quick strokes back from the tip
        ex, ey = pts[-1]; px, py = pts[-6]; a = math.atan2(ey - py, ex - px)
        for s_ in (-1, 1):
            b = a + math.pi - s_ * math.radians(28)
            d.line([(ex, ey), (ex + 24 * math.cos(b), ey + 24 * math.sin(b))], fill=col, width=width)


def thin_line(d, p0, p2, prog, col, width=2, dot=7):
    if prog <= 0:
        return
    e = (p0[0] + (p2[0] - p0[0]) * prog, p0[1] + (p2[1] - p0[1]) * prog)
    d.line([p0, e], fill=col, width=width)
    if prog >= 0.98:
        d.ellipse([p2[0] - dot, p2[1] - dot, p2[0] + dot, p2[1] + dot], fill=col)
        d.ellipse([p2[0] - dot - 5, p2[1] - dot - 5, p2[0] + dot + 5, p2[1] + dot + 5], outline=col, width=2)


# ---------------------------------------------------------------------------------------------------- compose
def compose(plate, photo_path, style, target, corner, name, role, kind, p_in=1.0, p_line=1.0, p_lab=1.0, fade=1.0):
    """plate: RGB image (any size, scaled to 1920x816). target: (u, v) in 0..1, origin top-left.
    Returns the composited RGB frame. p_* are the animation phases (0..1)."""
    base = plate.convert("RGB").resize((W, H), Image.LANCZOS).convert("RGBA")
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    size = (230, 288) if kind == "person" else (300, 225)
    photo = prep_photo(photo_path, kind, size)
    if style == "A":
        card, lab = card_A(photo, name, role); tilt = -4.0 if corner.endswith("l") else 4.0
    elif style == "B":
        card, lab = card_B(photo, name, role); tilt = 0.0
    else:
        card, lab = card_C(photo, name, role); tilt = -2.0 if corner.endswith("l") else 2.0
    card = card.rotate(tilt, expand=True, resample=Image.BICUBIC)
    mx, my = 64, 54
    x = mx if corner.endswith("l") else W - mx - card.width
    y = my if corner.startswith("t") else H - my - card.height - (70 if style == "B" else 0)
    # ease in: a short slide (24 px) toward its place + opacity; no overshoot
    e = ease_out(p_in); slide = (1 - e) * 24 * (1 if corner.endswith("l") else -1)
    x0 = int(x - slide)
    if style != "B":
        sh = shadow_of(card, blur=12 if style == "A" else 10, alpha=150, offset=(8, 12))
        over.alpha_composite(sh, (x0 - 40, y - 40))
    over.alpha_composite(card, (x0, y))
    d = ImageDraw.Draw(over)
    # where the line leaves the card: the card edge nearest the target
    tx, ty = target[0] * W, target[1] * H
    cx = x0 + card.width if tx > x0 + card.width / 2 else x0
    cy = y + card.height * (0.45 if kind == "person" else 0.55)
    start = (cx + (14 if cx > x0 else -14), cy)
    end = (tx - (40 if tx > start[0] else -40) * (1 if style == "A" else 0.0), ty)
    if style == "A":
        hand_arrow(d, start, (tx + (-36 if tx > start[0] else 36), ty + 6), ease_io(p_line), LIME + (235,), width=5)
    else:
        thin_line(d, start, (tx, ty), ease_io(p_line), (255, 255, 255, 230) if style == "B" else WARM + (235,), width=2)
    # labels
    a = int(255 * ease_io(p_lab))
    if a > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        if style == "A":
            f = F(SLAB_B, 30); fr = F(SERIF_I, 22)
            ly = y + card.height + 14
            ld.text((x0 + 6, ly), name, font=f, fill=WARM + (a,))
            if role:
                ld.text((x0 + 8, ly + 38), role, font=fr, fill=(226, 220, 206, int(a * 0.85)))
        elif style == "B":
            f = F(SLAB_B, 26); fr = F(SERIF, 20)
            ly = y + card.height + 16
            ld.text((x0, ly), name, font=f, fill=(255, 255, 255, a))
            ld.line([(x0, ly + 36), (x0 + 36, ly + 36)], fill=LIME + (a,), width=3)
            if role:
                ld.text((x0, ly + 44), role, font=fr, fill=(225, 225, 225, int(a * 0.9)))
        over = Image.alpha_composite(over, lay) if style != "C" else over
        if style == "C":       # the typed strip is on the card; a small slab caption only for the city
            pass
    if fade < 1.0:
        over.putalpha(over.split()[-1].point(lambda v: int(v * fade)))
    return Image.alpha_composite(base, over).convert("RGB")


def phases(sec):
    return dict(p_in=sec / 0.5, p_line=(sec - 0.4) / 0.6, p_lab=(sec - 0.8) / 0.3, fade=1.0 - ease_io((sec - 3.6) / 0.4))


if __name__ == "__main__":
    a = sys.argv[1:]
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    mode = a[0]
    style, corner = opt("--style", "A"), opt("--corner", "tl")
    name, role, kind = opt("--name", ""), opt("--role", ""), opt("--kind", "person")
    if mode == "still":
        plate, photo, out = a[1:4]
        tgt = tuple(float(v) for v in opt("--target", "0.6,0.5").split(","))
        compose(Image.open(plate), photo, style, tgt, corner, name, role, kind).save(out)
        print("[callout]", out)
    else:
        fdir, photo, out = a[1:4]
        trk = json.load(open(opt("--track", "")))
        key = opt("--key", "spine03")
        frames = sorted(glob.glob(os.path.join(fdir, "f*.png")))
        n = min(len(frames), 96)
        tmp = out + "_frames"; os.makedirs(tmp, exist_ok=True)
        for i in range(n):
            sec = i / 24.0
            u = i / max(len(frames) - 1, 1)                               # plate frames span the tracked move
            j = u * (len(trk) - 1); j0 = int(j); j1 = min(j0 + 1, len(trk) - 1); f_ = j - j0
            p = [trk[j0][key][k] * (1 - f_) + trk[j1][key][k] * f_ for k in (0, 1)]
            tgt = (p[0], 1 - p[1])
            ph = phases(sec)
            compose(Image.open(frames[i]), photo, style, tgt, corner, name, role, kind, **ph).save(os.path.join(tmp, f"c{i:04d}.png"))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "24", "-i", os.path.join(tmp, "c%04d.png"), "-c:v", "libx264", "-crf", "18",
                        "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], check=True)
        print("[callout] mp4", out, n, "frames")
