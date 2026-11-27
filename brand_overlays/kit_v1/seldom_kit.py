"""Seldom on-screen graphics kit v1: animated overlay templates rendered with Python/PIL.

Every template is a function  f(t, **params) -> Frame  where t is seconds since the element starts. A Frame holds
  .rgba   the 1920x1080 RGBA overlay (straight alpha), ready to composite over any shot
  .bg     background treatment for that moment: dict(blur=px, dim=0..1) (0/0 = leave the shot alone)
Templates also expose DUR (default length, s) and, for the typewriter, cue times (see cues()).

CLI:
  python3 seldom_kit.py render quote --params '{"text": "...", "who": "..."}' --out frames_dir [--dur 4.5]
      -> frames_dir/f_0001.png ... (RGBA), frames_dir/meta.json (fps, bg treatment per frame, SFX cues)
  python3 seldom_kit.py list
"""
import os, sys, json, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
W, H, FPS = 1920, 1080, 24

# ---------------------------------------------------------------- design tokens
YEL = (227, 255, 0)          # Seldom yellow #E3FF00
WHITE = (243, 241, 234)      # warm paper white #F3F1EA
INK = (11, 10, 8)            # near-black #0B0A08
GREY = (150, 146, 136)       # secondary text #969288
FONT = dict(
    label=os.path.join(FONTS, "Oswald-Medium.ttf"),        # condensed caps for labels, names, tags
    label_bold=os.path.join(FONTS, "Oswald-Bold.ttf"),
    label_light=os.path.join(FONTS, "Oswald-Light.ttf"),
    serif=os.path.join(FONTS, "CormorantGaramond-SemiBold.ttf"),      # refined serif for quotes and titles
    serif_it=os.path.join(FONTS, "CormorantGaramond-MediumItalic.ttf"),
    type=os.path.join(FONTS, "SpecialElite-Regular.ttf"),          # typewriter for short phrases
    mono=os.path.join(FONTS, "CourierPrime-Regular.ttf"),           # case-file mono (documents, data)
    mono_bold=os.path.join(FONTS, "CourierPrime-Bold.ttf"),
    plex=os.path.join(FONTS, "IBMPlexMono-Regular.ttf"),            # small technical mono (coordinates, indices)
)
_fc = {}


def font(key, size):
    k = (key, int(size))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FONT.get(key, key), int(size))
    return _fc[k]


# ---------------------------------------------------------------- easing and timing helpers
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def seg(t, t0, t1):
    """0 before t0, 1 after t1, linear between."""
    return clamp((t - t0) / max(1e-6, t1 - t0))


def out_cubic(x):
    return 1 - (1 - x) ** 3


def out_expo(x):
    return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)


def in_out(x):
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def out_back(x, s=1.6):
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def fade(t, tin0, tin1, tout0=None, tout1=None):
    a = out_cubic(seg(t, tin0, tin1))
    if tout0 is not None:
        a *= 1 - in_out(seg(t, tout0, tout1))
    return a


class Frame:
    def __init__(self):
        self.rgba = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.bg = dict(blur=0.0, dim=0.0)
        self.d = ImageDraw.Draw(self.rgba)


# ---------------------------------------------------------------- drawing primitives
def layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def text_w(txt, f, tracking=0):
    return sum(f.getlength(c) for c in txt) + tracking * max(0, len(txt) - 1)


def draw_text(im, xy, txt, f, fill, tracking=0, anchor="ls"):
    """Text with letter-spacing. anchor: l/m/r + s (baseline) like PIL."""
    d = ImageDraw.Draw(im)
    x, y = xy
    tw = text_w(txt, f, tracking)
    if anchor[0] == "m":
        x -= tw / 2
    elif anchor[0] == "r":
        x -= tw
    for c in txt:
        d.text((x, y), c, font=f, fill=fill, anchor="l" + anchor[1])
        x += f.getlength(c) + tracking
    return tw


def with_alpha(im, a):
    if a >= 0.999:
        return im
    r, g, b, al = im.split()
    al = al.point(lambda v: int(v * a))
    return Image.merge("RGBA", (r, g, b, al))


def glow(im, radius=10, strength=0.55, color=None):
    """A soft halo under the layer (computed at half resolution for speed)."""
    small = im.resize((W // 2, H // 2), Image.BILINEAR).filter(ImageFilter.GaussianBlur(radius / 2))
    g = small.resize((W, H), Image.BILINEAR)
    if color is not None:
        a = g.split()[3]
        g = Image.merge("RGBA", (*[Image.new("L", (W, H), c) for c in color], a))
    g = with_alpha(g, strength)
    out = layer(); out.alpha_composite(g); out.alpha_composite(im)
    return out


def shadow(im, offset=(0, 6), radius=12, strength=0.7):
    a = im.split()[3].resize((W // 2, H // 2), Image.BILINEAR).filter(ImageFilter.GaussianBlur(radius / 2)).resize((W, H), Image.BILINEAR)
    a = a.point(lambda v: int(v * strength))
    sh = Image.merge("RGBA", (Image.new("L", (W, H), 0),) * 3 + (a,))
    out = layer(); out.alpha_composite(sh, dest=offset); out.alpha_composite(im)
    return out


_grain = {}


def grain(im, t, amount=0.10):
    """Film grain on the overlay itself (modulates alpha and luminance slightly), changes every frame."""
    k = int(t * FPS) % 12
    if k not in _grain:
        rnd = random.Random(k)
        g = Image.effect_noise((W // 2, H // 2), 64).resize((W, H), Image.BILINEAR)
        _grain[k] = g
    g = _grain[k]
    r, gg, b, a = im.split()
    m = g.point(lambda v: int(255 - amount * 255 + amount * v))
    a = ImageChops.multiply(a, m)
    return Image.merge("RGBA", (r, gg, b, a))


def line(im, p0, p1, prog, fill, width=2):
    if prog <= 0:
        return
    d = ImageDraw.Draw(im)
    x = p0[0] + (p1[0] - p0[0]) * prog; y = p0[1] + (p1[1] - p0[1]) * prog
    d.line([p0, (x, y)], fill=fill, width=width)


def poly_draw(im, pts, prog, fill, width=2, dash=None):
    """Draw a polyline up to fraction prog of its length (optionally dashed: (on, off) px)."""
    if prog <= 0 or len(pts) < 2:
        return
    d = ImageDraw.Draw(im)
    L = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    tot = sum(L); left = tot * prog; s = 0.0
    for i, l in enumerate(L):
        if left <= 0:
            break
        u = min(1.0, left / l) if l else 1.0
        a = pts[i]; b = (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * u, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * u)
        if dash:
            seglen = math.dist(a, b); n = 0.0
            while n < seglen:
                q0 = n / max(seglen, 1e-6); q1 = min(1.0, (n + dash[0]) / max(seglen, 1e-6))
                if ((s + n) % (dash[0] + dash[1])) < dash[0]:
                    d.line([(a[0] + (b[0] - a[0]) * q0, a[1] + (b[1] - a[1]) * q0), (a[0] + (b[0] - a[0]) * q1, a[1] + (b[1] - a[1]) * q1)], fill=fill, width=width)
                n += dash[0] + dash[1]
        else:
            d.line([a, b], fill=fill, width=width)
        s += l; left -= l


def rounded_rect_path(x0, y0, x1, y1, r, steps=8):
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for k in range(steps + 1):
            a = math.radians(a0 + 90 * k / steps)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pts.append(pts[0])
    return pts


def duotone(img, size, dark=(14, 11, 6), light=(250, 236, 170), contrast=1.15):
    """Photos sit in the world: gold duotone, slight crunch."""
    from PIL import ImageOps
    im = ImageOps.autocontrast(img.convert("L"), cutoff=1)
    w, h = im.size; tw, th = size
    s = max(tw / w, th / h); im = im.resize((int(w * s + 1), int(h * s + 1)), Image.LANCZOS)
    l = (im.width - tw) // 2; tp = (im.height - th) // 2
    im = im.crop((l, tp, l + tw, tp + th))
    im = im.point(lambda v: clamp((v / 255 - 0.5) * contrast + 0.5) * 255)
    lut = [tuple(int(dark[c] + (light[c] - dark[c]) * (v / 255) ** 1.1) for c in range(3)) for v in range(256)]
    rgb = Image.merge("RGB", [im.point([lut[v][c] for v in range(256)]) for c in range(3)])
    return rgb


# ---------------------------------------------------------------- templates
TEMPLATES = {}


def template(name, dur):
    def deco(fn):
        fn.DUR = dur; TEMPLATES[name] = fn
        return fn
    return deco


@template("datestamp", 3.5)
def datestamp(t, top="16 FEBRUARY", big="2003", x=0.43, y=0.80, dur=3.5):
    """Date stamp (user layout: lower-left of centre). Rules slide out from the centre, the small line tracks in,
    the year sharpens up; a fast fade at the end."""
    fr = Frame(); L = layer()
    cx, cy = W * x, H * y
    a = fade(t, 0.0, 0.7, dur - 0.35, dur)
    fb = font("label_bold", 108); fs = font("label_light", 34)
    trk = 14 + 10 * (1 - out_cubic(seg(t, 0.0, 0.9)))
    draw_text(L, (cx, cy - 92), top, fs, WHITE + (255,), tracking=trk, anchor="ms")
    yw = text_w(big, fb, 4)
    yl = layer(); draw_text(yl, (cx, cy + 12), big, fb, WHITE + (255,), tracking=4, anchor="ms")
    bl = 6 * (1 - out_cubic(seg(t, 0.05, 0.8)))
    if bl > 0.2:
        yl = yl.filter(ImageFilter.GaussianBlur(bl))
    L.alpha_composite(yl)
    p = out_expo(seg(t, 0.0, 0.9)); gap = yw / 2 + 28
    for sg in (-1, 1):
        x0 = cx + sg * gap; x1 = cx + sg * (gap + 170)
        line(L, (x0, cy - 34), (x1, cy - 34), p, WHITE + (220,), 2)
    ImageDraw.Draw(L).rectangle([cx - 3, cy + 26, cx + 3, cy + 32], fill=YEL + (255,))      # yellow tick under the year
    L = glow(L, 14, 0.45)
    fr.rgba = grain(with_alpha(shadow(L, (0, 4), 10, 0.6), a), t, 0.06)
    return fr


def wrap(txt, f, maxw, tracking=0):
    words = txt.split(); lines = []; cur = ""
    for w_ in words:
        nx = (cur + " " + w_).strip()
        if text_w(nx, f, tracking) <= maxw:
            cur = nx
        else:
            lines.append(cur); cur = w_
    if cur:
        lines.append(cur)
    return lines


@template("quote", 5.0)
def quote(t, text="It holds for about a second and a half, then leaves on the cut with no exit animation.", who="MARTHA SLOAN, WITNESS",
          x=0.54, y=0.10, w=0.30, dur=5.0):
    """Quote card (user layout: upper right-of-centre). The big quote mark drops in, the dashed rounded box draws
    round, the quote types on word by word in serif, then the attribution slides in."""
    fr = Frame(); L = layer()
    x0, y0 = W * x, H * y; bw = W * w
    f = font("serif", 44); lines = wrap(text, f, bw - 70)
    lh = 52; bh = 50 + lh * len(lines) + 46
    a = fade(t, 0.0, 0.3, dur - 0.3, dur)
    # quote mark
    qp = seg(t, 0.0, 0.45); qa = out_cubic(qp); qs = 0.6 + 0.4 * out_back(qp)
    qm = layer(); qf = font("serif", int(170 * qs))
    ImageDraw.Draw(qm).text((x0 - 26, y0 + 70), "“", font=qf, fill=YEL + (int(255 * qa),), anchor="ls")
    # dashed rounded box
    path = rounded_rect_path(x0, y0 + 26, x0 + bw, y0 + 26 + bh, 18)
    poly_draw(L, path, in_out(seg(t, 0.2, 1.1)), WHITE + (200,), 2, dash=(10, 7))
    # text: words appear in order (fade per word)
    words = [wd for ln in lines for wd in ln.split()]; nW = len(words)
    t0, t1 = 0.7, 0.7 + 0.075 * nW; k = 0
    for i, ln in enumerate(lines):
        xx = x0 + 40; yy = y0 + 26 + 58 + i * lh
        for wd in ln.split():
            wa = out_cubic(seg(t, t0 + (t1 - t0) * k / nW, t0 + (t1 - t0) * k / nW + 0.25))
            if wa > 0:
                dy = 6 * (1 - wa)
                ImageDraw.Draw(L).text((xx, yy + dy), wd, font=f, fill=WHITE + (int(255 * wa),), anchor="ls")
            xx += f.getlength(wd + " "); k += 1
    # attribution: yellow dash + small caps
    ap = out_cubic(seg(t, t1 + 0.05, t1 + 0.5))
    if ap > 0:
        fa = font("label", 22); ay = y0 + 26 + bh - 22
        ax = x0 + bw - 30 - text_w(who, fa, 3)
        line(L, (ax - 46, ay - 8), (ax - 14, ay - 8), ap, YEL + (255,), 3)
        draw_text(L, (ax + 18 * (1 - ap), ay), who, fa, GREY + (int(255 * ap),), tracking=3)
    L.alpha_composite(glow(qm, 18, 0.6, YEL))
    L = glow(L, 10, 0.35)
    fr.rgba = grain(with_alpha(shadow(L, (0, 5), 12, 0.65), a), t, 0.06)
    return fr


def _phrase_layout(text):
    f = font("type", 76)
    return f, text_w(text, f, 2)


def phrase_cues(text, t0=0.55, cps=16.0):
    """Typing SFX cue times (s) for each visible character of the phrase."""
    out = []; tt = t0
    for c in text:
        out.append(round(tt, 3)); tt += (1 / cps) * (1.9 if c in " ,.;:!?’" else 1.0)
    return out


@template("phrase", 4.0)
def phrase(t, text="“short quoted phrases”", y=0.42, dur=4.0, cps=16.0):
    """Short quoted phrase (user layout: centred, the shot blurred and dimmed). Typewriter: characters type on with
    a blinking block cursor, a tiny ink-hit jitter on each key; typing SFX cues from phrase_cues()."""
    fr = Frame(); L = layer()
    bgp = in_out(seg(t, 0.0, 0.5)) * (1 - in_out(seg(t, dur - 0.4, dur)))
    fr.bg = dict(blur=14 * bgp, dim=0.55 * bgp)
    f, tw = _phrase_layout(text); cx = W / 2; base = H * y
    cues = phrase_cues(text, 0.55, cps); n = sum(1 for c in cues if c <= t)
    x = cx - tw / 2; d = ImageDraw.Draw(L)
    for i, c in enumerate(text[:n]):
        age = t - cues[i]; jit = (random.Random(i).uniform(-1, 1) * 2.5) if age < 0.05 else 0
        d.text((x, base + jit), c, font=f, fill=YEL + (255,), anchor="ls")
        x += f.getlength(c) + 2
    # cursor: solid while typing, blinking after
    done = n >= len(text)
    on = (not done) or (int((t - cues[-1]) * 2.2) % 2 == 0)
    if on and t > 0.25 and t < dur - 0.3:
        d.rectangle([x + 4, base - 60, x + 30, base + 10], fill=YEL + (230,))
    L = glow(L, 16, 0.55, YEL)
    a = 1 - in_out(seg(t, dur - 0.35, dur))
    fr.rgba = grain(with_alpha(L, a), t, 0.08)
    return fr


@template("section", 3.8)
def section(t, text="THE VAULT", index="02", x=0.045, y=0.90, dur=3.8):
    """Section tag (user layout: bottom-left). A yellow bar rises, the frame draws, the label wipes in behind a
    mask; a small mono index sits on the left. Wipes out to the left."""
    fr = Frame(); L = layer()
    f = font("label", 46); fi = font("plex", 22)
    tw = text_w(text, f, 5); x0 = W * x; yb = H * y; bh = 74; bw = tw + 120
    p_in = seg(t, 0.0, 0.9); p_out = seg(t, dur - 0.45, dur)
    bar = out_expo(seg(t, 0.0, 0.35))
    d = ImageDraw.Draw(L)
    d.rectangle([x0, yb - bh * bar, x0 + 5, yb], fill=YEL + (255,))
    box = [(x0 + 5, yb - bh), (x0 + bw, yb - bh), (x0 + bw, yb), (x0 + 5, yb)]
    poly_draw(L, box, out_cubic(seg(t, 0.15, 0.75)), WHITE + (170,), 2)
    # fill: very dark, translucent
    fill = layer(); ImageDraw.Draw(fill).rectangle([x0 + 6, yb - bh + 1, x0 + bw - 1, yb - 1], fill=INK + (int(150 * out_cubic(seg(t, 0.2, 0.7))),))
    tx = layer(); draw_text(tx, (x0 + 80, yb - 21), text, f, WHITE + (255,), tracking=5)
    draw_text(tx, (x0 + 26, yb - 26), index, fi, YEL + (255,), tracking=1)
    reveal = out_cubic(seg(t, 0.35, 0.95))
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rectangle([x0, yb - bh - 4, x0 + 10 + (bw + 10) * reveal, yb + 4], fill=255)
    tx.putalpha(ImageChops.multiply(tx.split()[3], m))
    out = layer(); out.alpha_composite(fill); out.alpha_composite(L); out.alpha_composite(tx)
    # out: wipe right-to-left
    if p_out > 0:
        m2 = Image.new("L", (W, H), 0); ImageDraw.Draw(m2).rectangle([x0 - 4, yb - bh - 6, x0 + (bw + 10) * (1 - in_out(p_out)), yb + 6], fill=255)
        out.putalpha(ImageChops.multiply(out.split()[3], m2))
    out = glow(out, 10, 0.3)
    fr.rgba = grain(shadow(out, (0, 4), 10, 0.6), t, 0.06)
    return fr


@template("title", 5.5)
def title(t, text="THEY STOLE $100 MILLION", sub="THE ANTWERP DIAMOND HEIST", dur=5.5):
    """Episode title, creepy: the serif caps bleed up out of the dark like wet ink (threshold on a growing blur),
    flicker like a failing tube, carry a faint VHS jitter with a red/cyan split, and a low amber flare crawls across
    them. The subtitle types on in mono. Ends on a hard flicker-out."""
    fr = Frame()
    fr.bg = dict(blur=6 * in_out(seg(t, 0.0, 1.0)), dim=0.45 * in_out(seg(t, 0.0, 1.0)))
    f = font("serif", 112); tr = 18
    base = layer(); draw_text(base, (W / 2, H * 0.47), text, f, WHITE + (255,), tracking=tr, anchor="ms")
    # ink bleed: blur then threshold with a level that sweeps from high (only cores) to normal
    ink = seg(t, 0.2, 2.4)
    a = base.split()[3]
    bl = a.filter(ImageFilter.GaussianBlur(3 + 9 * (1 - ink)))
    rnd = random.Random(int(t * FPS) // 2)
    noise = Image.effect_noise((W // 4, H // 4), 90).resize((W, H), Image.BILINEAR)
    lvl = int(235 - 140 * out_cubic(ink))
    m = ImageChops.add(bl, noise.point(lambda v: int(v * 0.35)), 1.0, -40).point(lambda v: 255 if v > lvl else int(v * 0.25))
    a2 = ImageChops.multiply(m, a.filter(ImageFilter.MaxFilter(3)))
    col = Image.merge("RGBA", (Image.new("L", (W, H), WHITE[0]), Image.new("L", (W, H), WHITE[1]), Image.new("L", (W, H), WHITE[2]), a2))
    # flicker: random drops early, steady later, flicker-out at the end
    fl = 1.0
    if t < 2.6:
        fl = 0.25 + 0.75 * (rnd.random() > 0.22) * rnd.uniform(0.7, 1.0)
    if t > dur - 0.5:
        fl *= 0.0 if rnd.random() < 0.6 else 0.6
    # VHS jitter + chroma split
    jx = int(rnd.choice([0, 0, 0, 0, 2, -3, 5]) if t < 3.2 else (rnd.choice([0, 0, 0, 0, 0, 1])))
    r_ = with_alpha(Image.merge("RGBA", (Image.new("L", (W, H), 255), Image.new("L", (W, H), 40), Image.new("L", (W, H), 30), a2)), 0.35)
    c_ = with_alpha(Image.merge("RGBA", (Image.new("L", (W, H), 40), Image.new("L", (W, H), 220), Image.new("L", (W, H), 230), a2)), 0.25)
    L = layer(); L.alpha_composite(r_, dest=(jx - 4, 0)); L.alpha_composite(c_, dest=(jx + 4, 0)); L.alpha_composite(col, dest=(jx, 0))
    # scanlines, very faint
    sl = Image.new("L", (W, H), 255); ds = ImageDraw.Draw(sl)
    for yy in range(0, H, 3):
        ds.line([(0, yy), (W, yy)], fill=205)
    L.putalpha(ImageChops.multiply(L.split()[3], sl))
    # flare: a thin horizontal amber streak passing behind the words
    fp = seg(t, 1.2, 4.6)
    if 0 < fp < 1:
        fx = W * (0.15 + 0.7 * in_out(fp))
        fl_l = layer(); dfl = ImageDraw.Draw(fl_l)
        for k, (hw, al) in enumerate(((520, 40), (300, 70), (140, 120), (50, 200))):
            dfl.ellipse([fx - hw, H * 0.47 - 40 - 2 - k, fx + hw, H * 0.47 - 40 + 2 + k], fill=(255, 210, 120, al))
        fl_l = fl_l.filter(ImageFilter.GaussianBlur(6))
        L.alpha_composite(with_alpha(fl_l, math.sin(math.pi * fp) * 0.9))
    # subtitle: mono, typed
    fs = font("mono", 30); st = sub[: int(len(sub) * seg(t, 2.6, 3.8))]
    if st:
        draw_text(L, (W / 2 - text_w(sub, fs, 8) / 2, H * 0.47 + 70), st, fs, YEL + (230,), tracking=8)
    L = glow(L, 22, 0.55, (255, 220, 150))
    fr.rgba = grain(with_alpha(L, fl), t, 0.14)
    return fr


def photo_card(L, img, x0, y0, pw, ph, p, name, role, align="l", mono_line=None):
    """A framed photo card: white hairline frame + inner yellow keyline, duotone photo, name and role below."""
    d = ImageDraw.Draw(L)
    a = out_cubic(p); dy = 30 * (1 - a)
    y0 += dy
    pad = 10
    d.rectangle([x0 - pad, y0 - pad, x0 + pw + pad, y0 + ph + pad], fill=INK + (int(210 * a),))
    ph_img = duotone(img, (int(pw), int(ph))).convert("RGBA")
    blur = 8 * (1 - out_cubic(seg(p, 0.0, 0.8)))
    if blur > 0.2:
        ph_img = ph_img.filter(ImageFilter.GaussianBlur(blur))
    L.alpha_composite(with_alpha(ph_img, a), dest=(int(x0), int(y0)))
    d.rectangle([x0 - pad, y0 - pad, x0 + pw + pad, y0 + ph + pad], outline=WHITE + (int(235 * a),), width=2)
    d.rectangle([x0 + 6, y0 + 6, x0 + pw - 6, y0 + ph - 6], outline=YEL + (int(140 * a),), width=1)
    # corner ticks
    for (cx, cy, sx, sy) in ((x0 - pad, y0 - pad, 1, 1), (x0 + pw + pad, y0 - pad, -1, 1), (x0 - pad, y0 + ph + pad, 1, -1), (x0 + pw + pad, y0 + ph + pad, -1, -1)):
        d.line([(cx - sx * 8, cy), (cx + sx * 22, cy)], fill=YEL + (int(255 * a),), width=3)
        d.line([(cx, cy - sy * 8), (cx, cy + sy * 22)], fill=YEL + (int(255 * a),), width=3)
    fn = font("label_bold", 40); fr_ = font("plex", 20)
    tp = out_cubic(seg(p, 0.35, 1.0))
    ax = {"l": x0 - pad, "m": x0 + pw / 2, "r": x0 + pw + pad}[align]; anc = {"l": "ls", "m": "ms", "r": "rs"}[align]
    draw_text(L, (ax, y0 + ph + pad + 52), name, fn, WHITE + (int(255 * tp),), tracking=3, anchor=anc)
    rp = out_cubic(seg(p, 0.55, 1.0))
    draw_text(L, (ax, y0 + ph + pad + 84), role, fr_, YEL + (int(255 * rp),), tracking=4, anchor=anc)
    if mono_line:
        draw_text(L, (ax, y0 + ph + pad + 110), mono_line, font("plex", 16), GREY + (int(220 * rp),), tracking=2, anchor=anc)


def _img(path_or_img):
    if isinstance(path_or_img, Image.Image):
        return path_or_img
    return Image.open(path_or_img)


@template("person", 4.5)
def person(t, photo=None, name="PERSON NAMED", role="VICTIM", x=0.035, y=0.55, pw=250, ph=310, dur=4.5):
    """Person card (user layout: bottom-left). Card rises and the photo comes into focus; name and role follow."""
    fr = Frame(); L = layer()
    p = seg(t, 0.0, 1.2)
    photo_card(L, _img(photo), W * x, H * y, pw, ph, p, name, role, "l")
    a = 1 - in_out(seg(t, dur - 0.35, dur))
    fr.rgba = grain(with_alpha(shadow(glow(L, 10, 0.25), (0, 8), 16, 0.75), a), t, 0.06)
    return fr


@template("person_pair", 5.0)
def person_pair(t, photos=(None, None), names=("PERSON NAMED", "PERSON NAMED"), roles=("SUSPECT", "SUSPECT"), y=0.40, pw=250, ph=310, dur=5.0):
    """Two person cards side by side (user layout: centred low), the shot blurred and dimmed behind them; the second
    card follows the first by 0.25 s, and a thin yellow link draws between them."""
    fr = Frame(); L = layer()
    bgp = in_out(seg(t, 0.0, 0.6)) * (1 - in_out(seg(t, dur - 0.4, dur)))
    fr.bg = dict(blur=12 * bgp, dim=0.5 * bgp)
    gap = 120; tot = 2 * pw + gap; x0 = W / 2 - tot / 2
    for i in range(2):
        photo_card(L, _img(photos[i]), x0 + i * (pw + gap), H * y, pw, ph, seg(t, 0.15 + 0.25 * i, 1.35 + 0.25 * i), names[i], roles[i], "m")
    lp = in_out(seg(t, 1.2, 1.8)); ly = H * y + ph / 2
    line(L, (x0 + pw + 12, ly), (x0 + pw + gap - 12, ly), lp, YEL + (220,), 2)
    if lp >= 1:
        dd = ImageDraw.Draw(L)
        for xx in (x0 + pw + 12, x0 + pw + gap - 12):
            dd.ellipse([xx - 5, ly - 5, xx + 5, ly + 5], fill=YEL + (255,))
    a = 1 - in_out(seg(t, dur - 0.35, dur))
    fr.rgba = grain(with_alpha(shadow(glow(L, 10, 0.25), (0, 8), 16, 0.75), a), t, 0.06)
    return fr


@template("place", 4.5)
def place(t, photo=None, name="ANTWERP DIAMOND CENTRE", country="BELGIUM", coords="51.2194° N  4.4025° E", x=0.70, y=0.62, pw=420, ph=236, dur=4.5):
    """Place card (user layout: bottom-right, landscape photo). A pin drops onto the frame corner, coordinates tick in."""
    fr = Frame(); L = layer()
    p = seg(t, 0.0, 1.2)
    x0 = W * x
    photo_card(L, _img(photo), x0, H * y, pw, ph, p, name, country, "r",
               mono_line=coords[: int(len(coords) * seg(t, 0.9, 1.8))])
    # pin on the top-left corner
    pp = out_back(seg(t, 0.5, 0.9)); d = ImageDraw.Draw(L)
    if pp > 0:
        px, py = x0 - 10, H * y - 10 - 40 * (1 - pp)
        d.ellipse([px - 12, py - 12, px + 12, py + 12], fill=YEL + (255,)); d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=INK + (255,))
    a = 1 - in_out(seg(t, dur - 0.35, dur))
    fr.rgba = grain(with_alpha(shadow(glow(L, 10, 0.25), (0, 8), 16, 0.75), a), t, 0.06)
    return fr


DISCRETION_TEXT = "This film contains descriptions of violence and death that some viewers may find distressing."
RECORDS_TEXT = ("This story is told from public records, court documents and news reports.",
                "Some scenes are recreated to show what may have happened.")


@template("disclaimer", 8.0)
def disclaimer(t, discretion=True, discretion_head="VIEWER DISCRETION ADVISED", discretion_text=DISCRETION_TEXT,
               text=RECORDS_TEXT, title="THINGS TO KNOW BEFORE YOU WATCH", dur=8.0):
    """Standalone two-part card, "THINGS TO KNOW BEFORE YOU WATCH". The shot sinks to near-black, the title tracks in
    between two hairlines that draw out from the centre. Paragraph 1 (optional, discretion=True) is the yellow
    "VIEWER DISCRETION ADVISED" head and its warning line; paragraph 2 is the records note. With discretion=False
    only paragraph 2 shows and the whole block re-centres. Lines rise in one after the other."""
    fr = Frame(); L = layer()
    bgp = in_out(seg(t, 0.0, 0.8)) * (1 - in_out(seg(t, dur - 0.6, dur)))
    fr.bg = dict(blur=10 * bgp, dim=0.9 * bgp)
    fs = font("serif_it", 44); fh = font("plex", 19); ft = font("label", 34)
    maxw = 1500; LH = 60
    p1 = wrap(discretion_text, fs, maxw) if discretion else []
    p2 = [w for ln in text for w in wrap(ln, fs, maxw)]
    # vertical layout (heights in px), then centre the block
    items = [("title", 34), ("gap", 34), ("rule", 0), ("gap", 62)]
    if discretion:
        items += [("head", 19), ("gap", 46)] + [("p1", LH)] * len(p1) + [("gap", 22), ("div", 0), ("gap", 66)]
    items += [("p2", LH)] * len(p2) + [("gap", 34), ("rule2", 0)]
    tot = sum(h for _, h in items); y = H / 2 - tot / 2
    hp = in_out(seg(t, 0.35, 1.35)); half = 420
    # timing: title, then paragraph 1 head and lines, then paragraph 2
    tl = 1.05
    seq = {}
    if discretion:
        seq["head"] = tl; tl += 0.45
        for i in range(len(p1)):
            seq[("p1", i)] = tl; tl += 0.55
        seq["div"] = tl; tl += 0.75
    for i in range(len(p2)):
        seq[("p2", i)] = tl; tl += 0.7
    n1 = n2 = 0
    for kind, h in items:
        if kind == "title":
            a_ = fade(t, 0.35, 1.0); tr = 8 + 6 * (1 - out_cubic(seg(t, 0.35, 1.3)))
            draw_text(L, (W / 2, y + h), title, ft, WHITE + (int(250 * a_),), tracking=tr, anchor="ms")
        elif kind in ("rule", "rule2"):
            line(L, (W / 2, y), (W / 2 - half, y), hp, WHITE + (120,), 1); line(L, (W / 2, y), (W / 2 + half, y), hp, WHITE + (120,), 1)
            if kind == "rule":
                d = ImageDraw.Draw(L); q = int(255 * hp)
                d.rectangle([W / 2 - 3, y - 3, W / 2 + 3, y + 3], fill=YEL + (q,))
        elif kind == "head":
            a_ = fade(t, seq["head"], seq["head"] + 0.6)
            draw_text(L, (W / 2, y + h + 6 * (1 - a_)), discretion_head, fh, YEL + (int(255 * a_),), tracking=7, anchor="ms")
        elif kind == "div":
            dp = in_out(seg(t, seq["div"], seq["div"] + 0.6))
            line(L, (W / 2 - 40, y), (W / 2 + 40, y), dp, YEL + (200,), 2)
        elif kind in ("p1", "p2"):
            i = n1 if kind == "p1" else n2
            t0 = seq[(kind, i)]; a_ = fade(t, t0, t0 + 0.9); dy = 10 * (1 - a_)
            txt = (p1 if kind == "p1" else p2)[i]
            draw_text(L, (W / 2, y + h - 14 + dy), txt, fs, WHITE + (int(255 * a_),), tracking=1, anchor="ms")
            if kind == "p1":
                n1 += 1
            else:
                n2 += 1
        y += h
    a = 1 - in_out(seg(t, dur - 0.5, dur))
    fr.rgba = grain(with_alpha(glow(L, 12, 0.3), a), t, 0.07)
    return fr


def _paper(w, h, seed=3):
    """An off-white sheet with fibre noise, a darker edge and a faint fold."""
    rnd = random.Random(seed)
    im = Image.new("RGB", (w, h), (226, 219, 200))
    n = Image.effect_noise((w, h), 18).point(lambda v: int(v * 0.5 + 128))
    im = ImageChops.multiply(im, Image.merge("RGB", (n, n, n)).point(lambda v: int(min(255, v + 120))))
    vg = Image.new("L", (w, h), 0); ImageDraw.Draw(vg).rectangle([18, 18, w - 18, h - 18], fill=255)
    vg = vg.filter(ImageFilter.GaussianBlur(26))
    dark = Image.new("RGB", (w, h), (160, 150, 128))
    im = Image.composite(im, dark, vg)
    ImageDraw.Draw(im).line([(0, h * 0.34), (w, h * 0.34)], fill=(205, 197, 176), width=2)
    return im


@template("document", 6.5)
def document(t, title="POLICE REPORT  —  ANTWERP", ref="PV 12.845/03", lines=None, highlight=(3, 6), dur=6.5):
    """Evidence document: a typed sheet slides in tilted over the dimmed shot, settles, then yellow highlighter bars
    sweep across the key lines one after the other."""
    lines = lines or ["DATE OF REPORT: 17.02.2003  08:40", "LOCATION: DIAMOND CENTRE, SCHUPSTRAAT 1", "VAULT LEVEL -2",
                      "123 OF 160 SAFE DEPOSIT BOXES FORCED OPEN.", "NO SIGN OF FORCED ENTRY AT STREET LEVEL.", "ALARM NOT TRIGGERED.",
                      "CAMERA TAPES REMOVED FROM THE RECORDER.", "ESTIMATED LOSS: UNKNOWN (OVER $100M).", "INVESTIGATING OFFICER: A. PEYS"]
    fr = Frame()
    bgp = in_out(seg(t, 0.0, 0.6)) * (1 - in_out(seg(t, dur - 0.5, dur)))
    fr.bg = dict(blur=8 * bgp, dim=0.6 * bgp)
    pw, ph = 760, 900
    sheet = _paper(pw, ph).convert("RGBA"); d = ImageDraw.Draw(sheet)
    fm = font("mono_bold", 26); fs = font("mono", 24)
    d.text((60, 90), title, font=fm, fill=(30, 26, 20, 255)); d.text((60, 128), ref, font=font("mono", 20), fill=(90, 80, 66, 255))
    d.line([(60, 150), (pw - 60, 150)], fill=(60, 52, 40, 255), width=2)
    for i, ln in enumerate(lines):
        yy = 210 + i * 62
        hp = 0.0
        if highlight[0] <= i <= highlight[1]:
            k = i - highlight[0]; hp = in_out(seg(t, 1.6 + 0.45 * k, 2.1 + 0.45 * k))
        if hp > 0:
            hl = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
            ImageDraw.Draw(hl).rectangle([54, yy - 26, 54 + (pw - 108) * hp, yy + 12], fill=YEL + (150,))
            sheet = Image.alpha_composite(sheet, hl); d = ImageDraw.Draw(sheet)
        d.text((60, yy), ln, font=fs, fill=(28, 24, 18, 255), anchor="ls")
    d.text((pw - 230, ph - 90), "[ SEALED ]", font=font("mono_bold", 24), fill=(120, 30, 20, 200))
    # slide in: from below-right, rotating to -3 deg
    p = out_cubic(seg(t, 0.0, 1.1)); ang = -3 - 9 * (1 - p)
    sh = sheet.rotate(ang, resample=Image.BICUBIC, expand=True)
    L = layer(); cx = W * 0.5 + 300 * (1 - p); cy = H * 0.52 + 500 * (1 - p)
    L.alpha_composite(sh, dest=(int(cx - sh.width / 2), int(cy - sh.height / 2)))
    a = 1 - in_out(seg(t, dur - 0.45, dur))
    fr.rgba = grain(with_alpha(shadow(L, (14, 22), 28, 0.85), a), t, 0.05)
    return fr


@template("timeline", 6.0)
def timeline(t, events=(("FRI 14 FEB", "18:00", "LAST TRADERS LEAVE"), ("SAT 15 FEB", "23:30", "CREW ENTERS THE VAULT"),
                       ("SUN 16 FEB", "05:30", "CREW LEAVES WITH THE LOOT"), ("MON 17 FEB", "08:30", "THE VAULT IS FOUND OPEN")),
             now=2, y=0.80, dur=6.0):
    """Timeline strip: the line draws from the left, ticks drop in one by one with mono dates and condensed labels;
    the current event gets a pulsing yellow node."""
    fr = Frame(); L = layer(); d = ImageDraw.Draw(L)
    x0, x1 = W * 0.08, W * 0.92; yy = H * y
    lp = in_out(seg(t, 0.0, 1.2)); line(L, (x0, yy), (x1, yy), lp, WHITE + (170,), 2)
    n = len(events)
    for i, (dte, tm, lab) in enumerate(events):
        xi = x0 + (x1 - x0) * (i + 0.5) / n
        p = out_cubic(seg(t, 0.6 + 0.45 * i, 1.1 + 0.45 * i))
        if p <= 0:
            continue
        cur = (i == now)
        col = YEL if cur else WHITE
        d.line([(xi, yy - 16 * p), (xi, yy + 16 * p)], fill=col + (255,), width=2)
        r = 7 if cur else 5
        d.ellipse([xi - r, yy - r, xi + r, yy + r], fill=col + (int(255 * p),))
        if cur and t > 1.1 + 0.45 * i:
            pr = (t * 1.3) % 1.0
            rr = 8 + 26 * pr
            d.ellipse([xi - rr, yy - rr, xi + rr, yy + rr], outline=YEL + (int(200 * (1 - pr)),), width=2)
        draw_text(L, (xi, yy - 40 - 8 * (1 - p)), f"{dte}  {tm}", font("plex", 20), (YEL if cur else GREY) + (int(255 * p),), tracking=2, anchor="ms")
        draw_text(L, (xi, yy + 52 + 8 * (1 - p)), lab, font("label", 26), WHITE + (int(255 * p),), tracking=3, anchor="ms")
    a = 1 - in_out(seg(t, dur - 0.4, dur))
    band = layer(); ImageDraw.Draw(band).rectangle([0, yy - 90, W, yy + 90], fill=INK + (int(120 * lp),))
    band = band.filter(ImageFilter.GaussianBlur(30))
    out = layer(); out.alpha_composite(band); out.alpha_composite(glow(L, 10, 0.3))
    fr.rgba = grain(with_alpha(out, a), t, 0.06)
    return fr


def grid_floor(alpha=40):
    """Faint perspective grid on black for 2D boards."""
    g = layer(); d = ImageDraw.Draw(g); hz = H * 0.42; cx = W / 2
    for k in range(-24, 25):
        x = cx + k * 140
        d.line([(cx + k * 18, hz), (x, H)], fill=WHITE + (alpha,), width=1)
    for k in range(1, 18):
        y = hz + (H - hz) * (k / 17) ** 2.2
        d.line([(0, y), (W, y)], fill=WHITE + (alpha,), width=1)
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rectangle([0, hz, W, H], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(60))
    g.putalpha(ImageChops.multiply(g.split()[3], m))
    return g


def poly_point(pts, prog):
    """The point at fraction prog along a polyline (for draw-on heads and labels)."""
    L_ = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]; tot = sum(L_) or 1.0
    left = tot * clamp(prog)
    for i, l in enumerate(L_):
        if left <= l or i == len(L_) - 1:
            u = left / l if l else 1.0
            return (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * u, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * u)
        left -= l
    return pts[-1]


def _tag(L, xy, txt, a):
    """A small mono tag sitting on a line: near-black pill, yellow hairline, yellow caps."""
    if a <= 0 or not txt:
        return
    f = font("plex", 16); w = text_w(txt, f, 3) + 26; h = 30; x, y = xy
    d = ImageDraw.Draw(L)
    d.rounded_rectangle([x - w / 2, y - h / 2, x + w / 2, y + h / 2], radius=4, fill=INK + (int(240 * a),), outline=YEL + (int(200 * a),), width=1)
    draw_text(L, (x, y + 6), txt, f, YEL + (int(255 * a),), tracking=3, anchor="ms")


LB_PW, LB_PH = 200, 188          # card photo size on the link board


def _lb_box(c):
    """Card c's anchor box: photo frame (with pad) and the bottom of its name/role text."""
    x0, y0 = W * c["pos"][0] - LB_PW / 2, H * c["pos"][1]
    return dict(l=x0 - 10, r=x0 + LB_PW + 10, t=y0 - 10, b=y0 + LB_PH + 10, tb=y0 + LB_PH + 10 + 100,
                cx=x0 + LB_PW / 2, cy=y0 + LB_PH / 2)


def _lb_path(ca, cb):
    """Elbow connector from card ca to card cb: below-to-top when cb sits on another row, side-to-side on one row."""
    A, B = _lb_box(ca), _lb_box(cb)
    if B["t"] > A["tb"] - 4:          # cb is below
        a, b = (A["cx"], A["tb"]), (B["cx"], B["t"] - 4); m = (a[1] + b[1]) / 2
        return [a, (a[0], m), (b[0], m), b]
    if A["t"] > B["tb"] - 4:          # cb is above
        a, b = (A["cx"], A["t"] - 4), (B["cx"], B["tb"]); m = (a[1] + b[1]) / 2
        return [a, (a[0], m), (b[0], m), b]
    if B["l"] > A["r"]:               # same row, to the right
        a, b = (A["r"] + 4, A["cy"]), (B["l"] - 4, B["cy"])
    else:
        a, b = (A["l"] - 4, A["cy"]), (B["r"] + 4, B["cy"])
    m = (a[0] + b[0]) / 2
    return [a, (m, a[1]), (m, b[1]), b]


def linkboard_schedule(cards, links, line_dur=0.9):
    """Resolve the board's timeline. cards: list of dicts {photo, name, role, pos=(fx, fy), t=appear time or None};
    links: list of (from, to, start_time, label) or (from, to, start_time, label, duration). A card with t=None
    appears the moment the first line drawn to it arrives. A link with start_time=None starts when its source card
    has finished appearing (0.6 s after it appears). Returns (card_times, [(i, j, t0, t1, label)])."""
    ct = [c.get("t") for c in cards]; out = []
    for lk in links:
        i, j, t0, lab = lk[:4]; du = lk[4] if len(lk) > 4 else line_dur
        if ct[i] is None:
            ct[i] = 0.4
        if t0 is None:
            t0 = ct[i] + 0.6
        out.append((i, j, t0, t0 + du, lab))
        if ct[j] is None or ct[j] > t0 + du:
            ct[j] = t0 + du
    ct = [0.4 if v is None else v for v in ct]
    return ct, out


LB_DEMO_CARDS = [dict(photo=None, name="PERSON A", role="ROLE", pos=(0.5, 0.05), t=0.4),
                 dict(photo=None, name="PERSON B", role="ROLE", pos=(0.25, 0.37)),
                 dict(photo=None, name="PERSON C", role="ROLE", pos=(0.75, 0.37)),
                 dict(photo=None, name="PERSON D", role="ROLE", pos=(0.5, 0.69))]
LB_DEMO_LINKS = [(0, 1, 1.4, "PARTNER"), (1, 2, 2.9, "FRIEND"), (2, 3, 4.4, "BROTHER")]


@template("linkboard", 8.0)
def linkboard(t, cards=None, links=None, people=None, line_dur=0.9, dur=8.0):
    """Link board on black with a faint grid, built SEQUENTIALLY and driven by data: the first card appears; a yellow
    line draws out of it (bright head on the tip); the moment the line reaches the next position that card appears
    (a node pops on the arrival point); the next line draws from that card; and so on. Optional small tag on each
    line ("BROTHER", "PARTNER") fades in as the head passes the middle. Time every link to the narration with
    links=[(from, to, start_time, label), ...]; cards=[{photo, name, role, pos, t}] (t=None: on the line's arrival).
    `people` (list of (photo, name, role)) is still accepted and fills the default positions."""
    cards = [dict(c) for c in (cards or LB_DEMO_CARDS)]
    if people:
        for c, p in zip(cards, people):
            c["photo"], c["name"], c["role"] = p
    ct, sched = linkboard_schedule(cards, links if links is not None else LB_DEMO_LINKS, line_dur)
    fr = Frame()
    fr.bg = dict(blur=0, dim=0.92 * in_out(seg(t, 0.0, 0.5)) * (1 - in_out(seg(t, dur - 0.4, dur))))
    L = layer(); L.alpha_composite(with_alpha(grid_floor(36), fade(t, 0.1, 0.8)))
    d = ImageDraw.Draw(L)
    tags = []
    for (i, j, t0, t1, lab) in sched:
        p = in_out(seg(t, t0, t1))
        if p <= 0:
            continue
        pts = _lb_path(cards[i], cards[j])
        poly_draw(L, pts, p, YEL + (230,), 3)
        s = pts[0]; d.ellipse([s[0] - 5, s[1] - 5, s[0] + 5, s[1] + 5], fill=YEL + (255,))
        if p < 1:
            h = poly_point(pts, p)
            d.ellipse([h[0] - 7, h[1] - 7, h[0] + 7, h[1] + 7], fill=WHITE + (255,))
        else:                                     # arrival node pops and settles
            k = out_back(seg(t, t1, t1 + 0.3)); e = pts[-1]; r = 6 * k
            d.ellipse([e[0] - r, e[1] - r, e[0] + r, e[1] + r], fill=YEL + (255,))
            ring = seg(t, t1, t1 + 0.6)
            if 0 < ring < 1:
                rr = 6 + 26 * out_cubic(ring)
                d.ellipse([e[0] - rr, e[1] - rr, e[0] + rr, e[1] + rr], outline=YEL + (int(220 * (1 - ring)),), width=2)
        if lab:
            tags.append((poly_point(pts, 0.5), lab, out_cubic(clamp((p - 0.5) / 0.3))))
    for (xy, lab, a_) in tags:
        _tag(L, xy, lab, a_)
    for c, t0 in zip(cards, ct):
        x0, y0 = W * c["pos"][0] - LB_PW / 2, H * c["pos"][1]
        p = seg(t, t0, t0 + 1.0)
        if p > 0:
            photo_card(L, _img(c["photo"]), x0, y0, LB_PW, LB_PH, p, c["name"], c["role"], "m")
    a = 1 - in_out(seg(t, dur - 0.35, dur))
    fr.rgba = grain(with_alpha(glow(L, 10, 0.3), a), t, 0.06)
    return fr


def _load_map():
    return json.load(open(os.path.join(HERE, "data", "benelux_10m.json")))


@template("map", 6.5)
def map_card(t, route=((4.4025, 51.2194, "ANTWERP"), (4.52, 50.98, ""), (4.3517, 50.8503, "BRUSSELS", "l")),
             pin=0, bbox=(2.4, 49.4, 6.6, 51.9), label="ANTWERP, BELGIUM", route_t=(1.6, 3.6), legs=None, dur=6.5):
    """Map card: a dark stylised map (country outlines in thin warm grey, the target country filled near-black with a
    yellow hairline) scales in; the pin drops and pulses; the route draws on as a dashed yellow path with a moving
    head; place labels in condensed caps, coordinates in mono."""
    fr = Frame()
    fr.bg = dict(blur=6 * in_out(seg(t, 0.0, 0.6)), dim=0.7 * in_out(seg(t, 0.0, 0.6)) * (1 - in_out(seg(t, dur - 0.4, dur))))
    geo = _load_map()
    mw, mh = 1160, 760; mx0, my0 = (W - mw) / 2, (H - mh) / 2 + 10
    lon0, lat0, lon1, lat1 = bbox
    k = math.cos(math.radians((lat0 + lat1) / 2))
    sx = mw / ((lon1 - lon0) * k); sy = mh / (lat1 - lat0); s = min(sx, sy)
    def P(lon, lat):
        return (mx0 + (lon - lon0) * k * s, my0 + (lat1 - lat) * s)
    M = layer(); dm = ImageDraw.Draw(M)
    dm.rectangle([mx0 - 20, my0 - 20, mx0 + mw + 20, my0 + mh + 20], fill=(16, 14, 10, 235))
    for name, rings in geo.items():
        for r in rings:
            pts = [P(x, y) for x, y in r]
            if name == "Belgium":
                dm.polygon(pts, fill=(30, 27, 18, 255))
            dm.line(pts, fill=(YEL + (200,)) if name == "Belgium" else (120, 112, 96, 160), width=2 if name == "Belgium" else 1)
    # mask to the card
    mk = Image.new("L", (W, H), 0); ImageDraw.Draw(mk).rectangle([mx0 - 20, my0 - 20, mx0 + mw + 20, my0 + mh + 20], fill=255)
    M.putalpha(ImageChops.multiply(M.split()[3], mk))
    ImageDraw.Draw(M).rectangle([mx0 - 20, my0 - 20, mx0 + mw + 20, my0 + mh + 20], outline=WHITE + (170,), width=2)
    for (lo, la, nm) in ((3.7174, 51.0543, "GHENT"), (3.2247, 51.2093, "BRUGES"), (5.5797, 50.6326, "LIÈGE"), (4.8719, 50.4674, "NAMUR"),
                         (5.3378, 50.9307, "HASSELT"), (4.4777, 51.9244, "ROTTERDAM"), (6.1296, 49.6116, "LUXEMBOURG")):
        q = P(lo, la); ca = int(170 * fade(t, 0.5, 1.2))
        dm.ellipse([q[0] - 3, q[1] - 3, q[0] + 3, q[1] + 3], fill=GREY + (ca,))
        draw_text(M, (q[0] + 10, q[1] + 6), nm, font("label_light", 20), GREY + (ca,), tracking=3)
    # route: drawn leg by leg (data-driven: legs=[(t0, t1), ...], default = route_t split by length); each stop's
    # label and node land the moment the head reaches it; waypoints with an empty name stay unlabelled
    pts = [P(st[0], st[1]) for st in route]
    ll = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    if legs is None:
        T0, T1 = route_t; acc = 0.0; legs = []
        for l in ll:
            legs.append((T0 + (T1 - T0) * acc / sum(ll), T0 + (T1 - T0) * (acc + l) / sum(ll))); acc += l
    dmm = ImageDraw.Draw(M); arrive = [legs[0][0]] + [e for _, e in legs]
    for i, (a0, a1) in enumerate(legs):
        lp = clamp((t - a0) / max(a1 - a0, 1e-6))
        poly_draw(M, [pts[i], pts[i + 1]], lp, YEL + (255,), 4, dash=(16, 10))
        if 0 < lp < 1:
            hx, hy = poly_point([pts[i], pts[i + 1]], lp)
            dmm.ellipse([hx - 7, hy - 7, hx + 7, hy + 7], fill=WHITE + (255,))
    for i, st in enumerate(route):
        lo, la, nm = st[:3]; side = st[3] if len(st) > 3 else "r"
        q = P(lo, la); ta = arrive[i] if i else 1.0
        tx, anc = (q[0] + 22, "ls") if side == "r" else (q[0] - 22, "rs")
        lpv = out_cubic(seg(t, ta, ta + 0.5))
        if i and nm and lpv > 0:
            kk = out_back(seg(t, ta, ta + 0.3)); r = 7 * kk
            dmm.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=YEL + (255,))
        if lpv > 0 and nm:
            draw_text(M, (tx, q[1] - 14), nm, font("label", 30), WHITE + (int(255 * lpv),), tracking=3, anchor=anc)
            draw_text(M, (tx, q[1] + 14), f"{la:.4f}°N  {lo:.4f}°E", font("plex", 16), GREY + (int(230 * lpv),), tracking=1, anchor=anc)
    # pin
    q = P(route[pin][0], route[pin][1]); pp = out_back(seg(t, 0.8, 1.2))
    if pp > 0:
        py = q[1] - 50 * (1 - pp)
        dmm.ellipse([q[0] - 11, py - 11, q[0] + 11, py + 11], fill=YEL + (255,)); dmm.ellipse([q[0] - 4, py - 4, q[0] + 4, py + 4], fill=INK + (255,))
        if t > 1.2:
            pr = ((t - 1.2) * 1.1) % 1.0; rr = 12 + 40 * pr
            dmm.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], outline=YEL + (int(220 * (1 - pr)),), width=2)
    draw_text(M, (mx0, my0 - 34), label, font("label", 28), WHITE + (230,), tracking=5)
    draw_text(M, (mx0 + mw, my0 - 34), "FIG. 03", font("plex", 18), YEL + (220,), tracking=3, anchor="rs")
    # scale in
    p = out_cubic(seg(t, 0.0, 0.9)); sc = 0.94 + 0.06 * p
    Mi = M.resize((int(W * sc), int(H * sc)), Image.BICUBIC)
    L = layer(); L.alpha_composite(Mi, dest=(int((W - Mi.width) / 2), int((H - Mi.height) / 2)))
    a = p * (1 - in_out(seg(t, dur - 0.35, dur)))
    fr.rgba = grain(with_alpha(shadow(glow(L, 10, 0.25), (0, 10), 20, 0.8), a), t, 0.06)
    return fr


def lineart_from(img, accent_box=None):
    """Turn a render or photo into white line art: edges, thinned and boosted; the accent box region is redrawn
    in yellow."""
    g = img.convert("L").resize((W, H), Image.LANCZOS)
    g = g.point(lambda v: min(255, int(v * 2.2)))
    e = g.filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 26 else 0)
    e = e.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.6))
    wl = Image.merge("RGBA", (Image.new("L", (W, H), WHITE[0]), Image.new("L", (W, H), WHITE[1]), Image.new("L", (W, H), WHITE[2]), e))
    if accent_box:
        m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rectangle(accent_box, fill=255)
        ya = Image.merge("RGBA", (*[Image.new("L", (W, H), c) for c in YEL], ImageChops.multiply(e, m)))
        wl.alpha_composite(ya)
    return wl


@template("lineart", 7.0)
def lineart(t, source=None, accent_box=None, dur=7.0):
    """2D line-art sample: white ink lines on black with a faint grid floor; the drawing reveals left to right with
    a soft edge, then drifts slowly (2D camera move); one yellow accent detail."""
    fr = Frame()
    fr.bg = dict(blur=0, dim=0.97 * in_out(seg(t, 0.0, 0.5)) * (1 - in_out(seg(t, dur - 0.5, dur))))
    art = lineart_from(_img(source), accent_box)
    rv = in_out(seg(t, 0.3, 3.2))
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rectangle([0, 0, W * rv * 1.15, H], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(60))
    art.putalpha(ImageChops.multiply(art.split()[3], m))
    s = 1.0 + 0.05 * seg(t, 0, dur); art = art.resize((int(W * s), int(H * s)), Image.BICUBIC)
    L = layer(); L.alpha_composite(with_alpha(grid_floor(28), fade(t, 0.1, 1.0)))
    L.alpha_composite(art, dest=(int(-(art.width - W) / 2 - 30 * seg(t, 0, dur)), int(-(art.height - H) / 2)))
    a = 1 - in_out(seg(t, dur - 0.5, dur))
    fr.rgba = grain(with_alpha(glow(L, 8, 0.35), a), t, 0.1)
    return fr


# ---------------------------------------------------------------- compositing and CLI
# YouTube end-screen safe layout at 1920x1080: two video slots and the subscribe circle (YouTube draws these itself;
# the card only leaves the space and frames it). Slots are 16:9.
OUTRO_SLOTS = ((150, 470, 660, 371), (1110, 470, 660, 371))
OUTRO_SUB = (960, 655, 112)                       # subscribe circle: centre x, centre y, radius


@template("outro", 10.0)
def outro(t, thanks="THANKS FOR WATCHING", subscribe="SUBSCRIBE", tuned="STAY TUNED FOR MORE", logo=None,
          guides=True, dur=10.0):
    """Outro end card (8–10 s). The shot sinks to near-black over a faint grid; the official Seldom logo (logo art,
    never 3D text) rises out of a soft bloom at the top; "THANKS FOR WATCHING" tracks in between hairlines. Below, the
    space for YouTube's end-screen elements: two 16:9 video slots framed only by corner ticks, and the subscribe circle
    between them, drawn as a yellow ring that pulses, with "SUBSCRIBE" and an arrow. "STAY TUNED FOR MORE" types on at
    the bottom. guides=False drops the slot frames and ring (if YouTube's own elements should sit on a clean field)."""
    fr = Frame(); L = layer()
    bgp = in_out(seg(t, 0.0, 0.9)) * (1 - in_out(seg(t, dur - 0.5, dur)))
    fr.bg = dict(blur=14 * bgp, dim=0.93 * bgp)
    L.alpha_composite(with_alpha(grid_floor(26), 0.8 * fade(t, 0.2, 1.2)))
    d = ImageDraw.Draw(L)
    # logo
    lg = Image.open(logo or os.path.join(HERE, "assets", "seldom_logo.png")).convert("RGBA")
    lw = 560; lh = int(lg.height * lw / lg.width)
    lp = out_cubic(seg(t, 0.4, 1.5)); sc_ = 0.94 + 0.06 * lp
    g = lg.resize((int(lw * sc_), int(lh * sc_)), Image.LANCZOS)
    blur = 14 * (1 - out_cubic(seg(t, 0.4, 1.3)))
    if blur > 0.3:
        g = g.filter(ImageFilter.GaussianBlur(blur))
    gx, gy = int(W / 2 - g.width / 2), int(150 - g.height / 2 + 18 * (1 - lp))
    bloom = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bloom.alpha_composite(g, (gx, gy))
    bloom = bloom.filter(ImageFilter.GaussianBlur(45)); bloom = with_alpha(bloom, 0.45 * lp)
    L.alpha_composite(bloom); L.alpha_composite(with_alpha(g, lp), (gx, gy))
    # thanks
    ty = 330; tp = fade(t, 1.2, 2.0); tr = 10 + 8 * (1 - out_cubic(seg(t, 1.2, 2.2)))
    draw_text(L, (W / 2, ty), thanks, font("label", 44), WHITE + (int(250 * tp),), tracking=tr, anchor="ms")
    hp = in_out(seg(t, 1.0, 2.0))
    for yy in (ty - 62, ty + 34):
        line(L, (W / 2, yy), (W / 2 - 330, yy), hp, WHITE + (90,), 1); line(L, (W / 2, yy), (W / 2 + 330, yy), hp, WHITE + (90,), 1)
    d.rectangle([W / 2 - 3, ty + 31, W / 2 + 3, ty + 37], fill=YEL + (int(255 * hp),))
    if guides:
        # video slots: faint plate + corner ticks, drawing in one after the other
        for k, (x, y, w, h) in enumerate(OUTRO_SLOTS):
            p = out_cubic(seg(t, 1.8 + 0.25 * k, 2.6 + 0.25 * k))
            if p <= 0:
                continue
            d.rectangle([x, y, x + w, y + h], fill=INK + (int(150 * p),), outline=WHITE + (int(40 * p),), width=1)
            c = 34 * p
            for (cx, cy, sx, sy) in ((x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
                d.line([(cx, cy), (cx + sx * c, cy)], fill=WHITE + (int(220 * p),), width=3)
                d.line([(cx, cy), (cx, cy + sy * c)], fill=WHITE + (int(220 * p),), width=3)
            draw_text(L, (x, y - 16), ("WATCH NEXT", "MORE FROM SELDOM")[k], font("plex", 18), GREY + (int(230 * p),), tracking=4)
        # subscribe ring: draws round, then pulses
        cx, cy, r = OUTRO_SUB; rp = in_out(seg(t, 2.3, 3.2))
        if rp > 0:
            pts = [(cx + r * math.cos(math.radians(-90 + 360 * u / 180)), cy + r * math.sin(math.radians(-90 + 360 * u / 180))) for u in range(181)]
            poly_draw(L, pts, rp, YEL + (240,), 4)
            if t > 3.2:
                pr = ((t - 3.2) / 1.6) % 1.0; rr = r + 6 + 34 * out_cubic(pr)
                d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=YEL + (int(150 * (1 - pr)),), width=2)
        sp = fade(t, 2.9, 3.6)
        draw_text(L, (cx, cy + r + 84), subscribe, font("label_bold", 34), YEL + (int(255 * sp),), tracking=8, anchor="ms")
        ay = cy + r + 40 - 5 * math.sin(max(0, t - 3.6) * 3.2) * sp
        d.polygon([(cx - 9, ay), (cx + 9, ay), (cx, ay - 11)], fill=YEL + (int(255 * sp),))
    else:
        cx, cy, r = OUTRO_SUB; sp = fade(t, 2.9, 3.6)
        draw_text(L, (cx, cy + r + 84), subscribe, font("label_bold", 34), YEL + (int(255 * sp),), tracking=8, anchor="ms")
    # stay tuned: types on at the bottom
    n = int(len(tuned) * seg(t, 3.6, 3.6 + len(tuned) / 18.0)); ft = font("plex", 24)
    draw_text(L, (W / 2, 975), tuned[:n], ft, WHITE + (220,), tracking=8, anchor="ms")
    if 3.6 <= t and (n < len(tuned) or int(t * 2.2) % 2 == 0):
        x_end = W / 2 + text_w(tuned, ft, 8) / 2 - text_w(tuned[n:], ft, 8) + 8
        d.rectangle([x_end, 955, x_end + 12, 979], fill=YEL + (230,))
    a = 1 - in_out(seg(t, dur - 0.5, dur))
    fr.rgba = grain(with_alpha(glow(L, 10, 0.25), a), t, 0.06)
    return fr


def composite(bg, fr):
    """Apply the frame's background treatment to an RGB shot and lay the overlay on top."""
    out = bg.convert("RGB")
    b = fr.bg.get("blur", 0); dm = fr.bg.get("dim", 0)
    if b > 0.3:
        out = out.resize((W // 2, H // 2), Image.BILINEAR).filter(ImageFilter.GaussianBlur(b / 2)).resize((W, H), Image.BILINEAR)
    if dm > 0.005:
        out = Image.blend(out, Image.new("RGB", (W, H), (0, 0, 0)), dm)
    o = out.convert("RGBA"); o.alpha_composite(fr.rgba)
    return o.convert("RGB")


def render(name, params, out_dir, dur=None):
    fn = TEMPLATES[name]; dur = dur or params.pop("dur", None) or fn.DUR
    os.makedirs(out_dir, exist_ok=True); meta = dict(fps=FPS, frames=[], template=name, params={k: str(v) for k, v in params.items()})
    n = int(round(dur * FPS))
    for i in range(n):
        fr = fn(i / FPS, dur=dur, **params)
        fr.rgba.save(os.path.join(out_dir, f"f_{i + 1:04d}.png"), compress_level=1)
        meta["frames"].append(fr.bg)
    if name == "phrase":
        meta["typing_sfx_cues_s"] = phrase_cues(params.get("text", "“short quoted phrases”"), 0.55, params.get("cps", 16.0))
    json.dump(meta, open(os.path.join(out_dir, "meta.json"), "w"), indent=1)
    return n


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("name", nargs="?")
    ap.add_argument("--params", default="{}"); ap.add_argument("--out", default="out"); ap.add_argument("--dur", type=float)
    a = ap.parse_args()
    if a.cmd == "list":
        for k, f in TEMPLATES.items():
            print(f"{k:12s} {f.DUR:4.1f}s  {f.__doc__.strip().splitlines()[0]}")
    elif a.cmd == "render":
        print(render(a.name, json.loads(a.params), a.out, a.dur), "frames")
