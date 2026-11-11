"""Cut the intro (cold open + title) at 2.35:1 from the rendered plates.

  python edit/intro_cut.py --still SHOT_ID T     one frame for look-dev
  python edit/intro_cut.py                       all frames + score -> out/intro_v2.mp4

Shot list (narration verbatim; timings are the 130 wpm estimate until the voiceover is aligned):
  a  bedroom     "I was unfaithful to my wife."  (email typed on the phone)
  b  bedroom     "That's what Nvidia CEO Jensen Huang tells his employees..." (Send)
  c  city        "...on November eighth."  (windows light up across the city)
  d  hq          "The same day, Nvidia opens an independent investigation..." (one floor switches on)
  e  watch       "...whether a foreign intelligence service targeted him."  (rain on glass)
  f  street walk "The woman at the center of the allegation is Alice Huang."
  g  puddle      "She comes from the other side of Nvidia's business."
  h  port        "The company she helps build buys the kinds of chips..."
  i  map         "...Washington is trying to keep out of China."
  j  title       THE SPY ALLEGATIONS ROCKING NVIDIA (over the street)
"""
import os, sys, json, math, glob, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "mograph"))
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates
import skia

W, H, FPS = 1920, 816, 24
PL = os.path.join(ROOT, "out", "plates")
OUT = os.path.join(ROOT, "out", "intro_v2")
FONTS = os.path.join(ROOT, "assets", "fonts")
SLAB = os.path.join(FONTS, "RobotoSlab-Bold.ttf")
SANS_L = "/usr/share/fonts/opentype/inter/Inter-Light.otf"
SANS = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"
SANS_SB = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
MONO = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Medium.ttf"

# ----------------------------------------------------------------------------- shot list
SHOTS = [  # id, plate scene/move, seconds, extra   (every shot is a true 3D animation, 12 fps -> 24 fps)
    ("a", ("bedroom", "over_shoulder"), 3.4, {"anim": (0.0, 0.58)}),     # "I was unfaithful to my wife."
    ("b", ("bedroom", "over_shoulder"), 2.4, {"send": True, "anim": (0.58, 1.0)}),   # "...tells his employees"
    ("c", ("office", "dolly"), 3.4, {}),                                # "...on November eighth." screens wake down the aisle
    ("d", ("boardroom", "board_slide"), 3.6, {}),                       # "...opens an independent investigation"
    ("e", ("surveil", "lens_push"), 3.6, {"rain": 0.25}),               # "...a foreign intelligence service targeted him."
    ("f", ("street", "slowmo_walk"), 3.6, {"rain": 1.0, "anim": (0.0, 0.6)}),   # "...Alice Huang."
    ("g", ("street", "puddle"), 3.4, {"rain": 0.8}),                    # "She comes from the other side..."
    ("h", ("port", "crane_rise"), 3.4, {}),                             # "...buys the kinds of chips"
    ("i", ("globe", "pacific_turn"), 3.6, {}),                          # "...keep out of China."
    ("j", ("cafe", "title_push"), 5.2, {"rain": 0.5, "title": True}),   # title over the two of them
]


def t0_of(sid):
    t = 0.0
    for s in SHOTS:
        if s[0] == sid:
            return t
        t += s[2]
    return t


TOTAL = sum(s[2] for s in SHOTS)
_YY, _XX = np.mgrid[0:H, 0:W].astype(np.float32)

# ----------------------------------------------------------------------------- io
_cache = {}


def load(path, mode="RGB"):
    key = (path, mode)
    if key not in _cache:
        im = Image.open(path).convert(mode)
        if im.size != (W, H):
            im = im.resize((W, H), Image.LANCZOS)
        _cache[key] = np.asarray(im).astype(np.float32) / 255.0
        if len(_cache) > 40:
            _cache.pop(next(iter(_cache)))
    return _cache[key]


def plate_dir(scene, move):
    for root in (PL, os.path.join(ROOT, "out", "plates_preview")):
        d = os.path.join(root, scene, move)
        if os.path.exists(os.path.join(d, "plate.png")) or glob.glob(os.path.join(d, "f*.png")):
            return d
    return None


def zoom_pan(img, z, px=0.0, py=0.0, shake=(0.0, 0.0)):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u = (xx - W / 2) / z + W / 2 - px * W + shake[0]
    v = (yy - H / 2) / z + H / 2 - py * H + shake[1]
    if img.ndim == 2:
        return map_coordinates(img, [v, u], order=1, mode="nearest")
    return np.stack([map_coordinates(img[..., c], [v, u], order=1, mode="nearest") for c in range(img.shape[2])], -1)


def handheld(T, amp=2.2):
    return (amp * (math.sin(T * 1.7) * 0.6 + math.sin(T * 3.1 + 1) * 0.3), amp * 0.7 * (math.sin(T * 1.3 + 2) * 0.6 + math.sin(T * 2.7) * 0.3))


# ----------------------------------------------------------------------------- phone UI (pinned to the screen corners)
def phone_ui(t, typed, sent=0.0):
    """A generic mail app (no brand). typed in [0,1] types the line; sent in [0,1] plays the send animation."""
    w_, h_ = 540, 1170
    s = skia.Surface(w_, h_); c = s.getCanvas()
    c.clear(skia.Color4f(0.06, 0.065, 0.075, 1))
    p = skia.Paint(AntiAlias=True)
    def txt(st, x, y, f, size, col, a=1.0):
        p.setColor4f(skia.Color4f(col[0], col[1], col[2], a)); c.drawString(st, x, y, skia.Font(skia.Typeface.MakeFromFile(f), size), p)
    txt("9:41", 36, 54, SANS_SB, 28, (0.9, 0.9, 0.92))
    txt("Cancel", 36, 140, SANS, 30, (0.45, 0.65, 1.0))
    txt("New Message", 190, 140, SANS_SB, 30, (0.95, 0.95, 0.96))
    p.setColor4f(skia.Color4f(0.2, 0.22, 0.25, 1))
    for y in (190, 262, 334):
        c.drawRect(skia.Rect.MakeXYWH(36, y, w_ - 72, 2), p)
    txt("To:", 36, 240, SANS, 28, (0.55, 0.57, 0.6)); txt("All employees", 100, 240, SANS, 28, (0.92, 0.92, 0.94))
    txt("Subject:", 36, 312, SANS, 28, (0.55, 0.57, 0.6)); txt("A message to our company", 150, 312, SANS, 28, (0.92, 0.92, 0.94))
    line = "I was unfaithful to my wife."
    n = int(len(line) * max(0.0, min(1.0, typed)))
    txt(line[:n], 36, 420, SANS, 34, (0.96, 0.96, 0.97))
    if typed < 1.0 or (int(t * 2) % 2 == 0 and sent == 0):     # cursor
        f = skia.Font(skia.Typeface.MakeFromFile(SANS), 34); xw = f.measureText(line[:n])
        p.setColor4f(skia.Color4f(0.45, 0.65, 1.0, 1)); c.drawRect(skia.Rect.MakeXYWH(38 + xw, 390, 3, 40), p)
    # send button (pressed when sent > 0)
    bc = (0.45, 0.65, 1.0) if sent == 0 else (0.7, 0.82, 1.0)
    p.setColor4f(skia.Color4f(*bc, 1)); c.drawCircle(w_ - 70, 132, 26 * (1 - 0.15 * math.sin(math.pi * min(sent * 4, 1))), p)
    p.setColor4f(skia.Color4f(0.06, 0.065, 0.075, 1)); c.drawPath(skia.Path.Polygon([skia.Point(w_ - 80, 144), skia.Point(w_ - 58, 132), skia.Point(w_ - 80, 120)], True), p)
    img = s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3].astype(np.float32) / 255
    if sent > 0:     # the message slides up and away, then a 'Sent' toast appears
        k = ease(min(1.0, sent * 1.6)); dy = int(k * 520)
        bg = np.array([0.06, 0.065, 0.075], np.float32)
        new = img.copy(); new[300:] = bg
        n_ = h_ - 300 - dy
        if n_ > 0:
            new[300:300 + n_] = img[300 + dy:300 + dy + n_] * (1 - k) + bg * k
        img = new
        if sent > 0.4:
            s2 = skia.Surface(w_, h_); c2 = s2.getCanvas(); c2.clear(skia.Color4f(0, 0, 0, 0))
            p2 = skia.Paint(AntiAlias=True); p2.setColor4f(skia.Color4f(0.18, 0.2, 0.24, 1))
            c2.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(150, 560, 240, 70), 35, 35), p2)
            p2.setColor4f(skia.Color4f(0.95, 0.95, 0.96, 1)); c2.drawString("Sent", 232, 606, skia.Font(skia.Typeface.MakeFromFile(SANS_SB), 30), p2)
            a = s2.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).astype(np.float32) / 255
            al = a[..., 3:4] * min(1.0, (sent - 0.4) * 4)
            img = img * (1 - al) + a[..., :3] * al
    return img


def homography(src, dst):
    A = []
    for (x, y), (u, v) in zip(src, dst):
        A += [[x, y, 1, 0, 0, 0, -u * x, -u * y, -u], [0, 0, 0, x, y, 1, -v * x, -v * y, -v]]
    _, _, Vt = np.linalg.svd(np.array(A))
    return Vt[-1].reshape(3, 3) / Vt[-1][-1]


def pin(base, ui, corners_px, glow=0.9):
    """Warp `ui` onto the quad `corners_px` (TL,TR,BR,BL in output pixels) and add it as emitted light."""
    h_, w_ = ui.shape[:2]
    Hm = homography(corners_px, [(0, 0), (w_, 0), (w_, h_), (0, h_)])        # output -> ui
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    den = Hm[2, 0] * xx + Hm[2, 1] * yy + Hm[2, 2]
    u = (Hm[0, 0] * xx + Hm[0, 1] * yy + Hm[0, 2]) / den; v = (Hm[1, 0] * xx + Hm[1, 1] * yy + Hm[1, 2]) / den
    inside = ((u >= 0) & (u < w_) & (v >= 0) & (v < h_)).astype(np.float32)
    inside = gaussian_filter(inside, 0.7)
    col = np.stack([map_coordinates(ui[..., c], [v, u], order=1, mode="constant") for c in range(3)], -1)
    return base * (1 - inside[..., None]) + col * inside[..., None] * glow + base * inside[..., None] * 0.0


# ----------------------------------------------------------------------------- rain (streaks in screen space, depth-faded)
_rng = np.random.default_rng(3)
RAIN = dict(x=_rng.uniform(0, W, 1100), y=_rng.uniform(0, H, 1100), z=_rng.uniform(0.2, 1.0, 1100), ph=_rng.uniform(0, 1, 1100))


def rain_layer(T, amount):
    if amount <= 0:
        return None
    s = skia.Surface(W, H); c = s.getCanvas(); c.clear(skia.Color4f(0, 0, 0, 0))
    p = skia.Paint(AntiAlias=True); p.setStyle(skia.Paint.kStroke_Style); p.setStrokeCap(skia.Paint.kRound_Cap)
    n = int(len(RAIN["x"]) * amount)
    for k in range(n):
        z = RAIN["z"][k]
        speed = 900 / z * 0.35                     # slow motion
        y = (RAIN["y"][k] + T * speed) % (H + 120) - 60
        x = RAIN["x"][k] + 0.12 * (y - RAIN["y"][k])
        L_ = 34 / z * 0.6
        p.setStrokeWidth(max(0.6, 1.8 / z * 0.5)); p.setColor4f(skia.Color4f(0.85, 0.9, 1.0, 0.09 * (1.1 - z)))
        c.drawLine(x, y, x + 0.12 * L_, y + L_, p)
    a = s.makeImageSnapshot().toarray().astype(np.float32) / 255
    return gaussian_filter(a[..., 3], 0.6)


# ----------------------------------------------------------------------------- text
def surface_text(draw):
    s = skia.Surface(W, H); c = s.getCanvas(); c.clear(skia.Color4f(0, 0, 0, 0))
    draw(c)
    a = s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType).astype(np.float32) / 255
    return a


def font(path, size):
    f = skia.Font(skia.Typeface.MakeFromFile(path), size); f.setSubpixel(True); return f


def tracked(c, s_, x, y, f, alpha, track=0.0, anchor="l", col=(1, 1, 1)):
    p = skia.Paint(AntiAlias=True); p.setColor4f(skia.Color4f(*col, alpha))
    ws = [f.measureText(ch) for ch in s_]; tot = sum(ws) + track * f.getSize() * (len(s_) - 1)
    xx = x - (tot / 2 if anchor == "c" else tot if anchor == "r" else 0)
    for ch, w_ in zip(s_, ws):
        c.drawString(ch, xx, y, f, p); xx += w_ + track * f.getSize()


def glow_text(img, layer, strength=0.5, radius=14):
    a = layer[..., 3]
    g = gaussian_filter(a, radius) * 0.9 + gaussian_filter(a, 4) * 0.5
    img = img + g[..., None] * strength
    return img * (1 - a[..., None]) + a[..., None] * 0.96


def ease(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)


def win(t, a, b, f=0.4):
    return ease((t - a) / f) * ease((b - t) / f)


_SCRIM = np.clip((_YY - H * 0.58) / (H * 0.42), 0, 1)[..., None] ** 1.3 * np.clip(1.15 - _XX / W, 0, 1)[..., None]


def lower_third(img, t, dur, head, sub, date=None):
    a = win(t, 0.5, dur - 0.15, 0.5)
    if a <= 0:
        return img
    img = img * (1 - 0.6 * a * _SCRIM)          # soft dark gradient behind the type
    def d(c):
        tracked(c, head, 110, H - 128, font(SANS_SB, 30), a, 0.22)
        if sub:
            tracked(c, sub, 110, H - 86, font(SANS, 24), a * 0.8)
        p = skia.Paint(AntiAlias=True); p.setColor4f(skia.Color4f(1, 1, 1, a * 0.9))
        c.drawRect(skia.Rect.MakeXYWH(110, H - 172, 46 * ease((t - 0.5) / 0.6), 2), p)
        if date:
            tracked(c, date, W - 110, 92, font(MONO, 26), a, 0.08, "r")
    return glow_text(img, surface_text(d), 0.12, 6)


def tag(img, t, dur, text):
    a = win(t, 0.2, dur - 0.1, 0.4) * 0.75
    def d(c):
        tracked(c, text, W - 110, H - 60, font(MONO, 15), a, 0.2, "r", (0.75, 0.78, 0.82))
    l = surface_text(d); al = l[..., 3:4]
    return img * (1 - al) + l[..., :3] * al


# ----------------------------------------------------------------------------- finish
_YY, _XX = np.mgrid[0:H, 0:W].astype(np.float32)
_VIG = (1 - 0.35 * np.clip(np.sqrt(((_XX - W / 2) / (W / 2)) ** 2 + ((_YY - H / 2) / (H / 2)) ** 2 * 0.5) - 0.45, 0, None) ** 1.6)[..., None]
_grng = np.random.default_rng(9)


def finish(img, bloom=0.4):
    hi = np.clip(img - 0.7, 0, None)
    small = hi[::4, ::4]
    bl = np.stack([gaussian_filter(small[..., c], 7) for c in range(3)], -1)
    bl = np.asarray(Image.fromarray((np.clip(bl, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
    img = img + bl * np.array([1.15, 0.95, 0.85]) * bloom
    img = img * _VIG
    g = _grng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    g = np.asarray(Image.fromarray(g).resize((W, H), Image.BICUBIC))
    y = img.mean(-1, keepdims=True)
    img = img + g[..., None] * 0.022 * (0.4 + 0.6 * (1 - np.abs(y - 0.4)))
    return np.clip(img, 0, 1)


def grade(img, lift=(0.006, 0.010, 0.018), gain=(1.0, 0.98, 0.96), sat=0.92, con=0.18):
    y = (img * np.array([0.2126, 0.7152, 0.0722])).sum(-1, keepdims=True)
    img = y + (img - y) * sat
    img = img + con * (img - img * img) * (img - 0.5) * 2
    return np.clip(np.array(lift) + img * (np.array(gain) - np.array(lift)), 0, 1)


# ----------------------------------------------------------------------------- per-shot compose
def shot_frame(sid, t):
    sh = next(s for s in SHOTS if s[0] == sid); _, src, dur, ex = sh
    u = t / dur
    T = t0_of(sid) + t
    if ex.get("map"):
        return map_frame(t, dur)
    d = plate_dir(*src)
    if d is None:
        return np.full((H, W, 3), 0.05, np.float32)
    frames = sorted(glob.glob(os.path.join(d, "f*.png")))
    if frames:
        a0, a1 = ex.get("anim", (0.0, 1.0))
        f = (a0 + (a1 - a0) * u) * (len(frames) - 1); i0 = int(f); fr = f - i0
        img = load(frames[i0]) * (1 - fr) + load(frames[min(i0 + 1, len(frames) - 1)]) * fr
        if sid in ("a", "b"):
            img = phone_comp(img, sid, t, dur, frame_pos=(a0 + (a1 - a0) * u) * (len(frames) - 1))
        img = zoom_pan(img, 1.0 + 0.02 * u, shake=handheld(T, 1.4 if sid in ("a", "b") else 0.8))
    else:
        img = load(os.path.join(d, "plate.png"))
        z = {"a": 1.0 + 0.05 * u, "b": 1.05 + 0.03 * u, "c": 1.0 + 0.06 * u, "d": 1.02 + 0.05 * u, "e": 1.0 + 0.04 * u,
             "g": 1.03 + 0.05 * u, "h": 1.0 + 0.06 * u}.get(sid, 1.0 + 0.04 * u)
        if ex.get("reveal"):
            d2 = plate_dir(*ex["reveal"])
            lit = load(os.path.join(d2, "plate.png")) if d2 else img
            img = reveal(img, lit, u, sid)
        if sid in ("a", "b"):
            img = phone_comp(img, sid, t, dur)
        img = zoom_pan(img, z, shake=handheld(T, 1.6 if sid in ("a", "b") else 0.6))
    img = grade(img, con=0.32 if sid in ("f", "g") else 0.2, sat=0.95)
    r = rain_layer(T, ex.get("rain", 0.0))
    if r is not None:
        img = img + r[..., None] * np.array([0.85, 0.9, 1.0])
    return img


def phone_comp(img, sid, t, dur, frame_pos=None):
    d = plate_dir("bedroom", "over_shoulder")
    sj = os.path.join(d, "screen.json")
    if not os.path.exists(sj):
        return img
    data = json.load(open(sj))
    if frame_pos is not None and "frames" in data:          # animated plate: interpolate this frame's corners
        fr_ = data["frames"]; i0 = int(frame_pos); f = frame_pos - i0
        A = np.array(fr_[min(i0, len(fr_) - 1)]); B = np.array(fr_[min(i0 + 1, len(fr_) - 1)])
        cn = (A * (1 - f) + B * f).tolist()
    else:
        cn = data["corners"]
    px = [(x * W, y * H) for x, y in cn]
    if sid == "a":
        ui = phone_ui(t, typed=ease((t - 0.4) / 2.0))
    else:
        ui = phone_ui(t, typed=1.0, sent=max(0.0, (t - 0.5) / 1.2))
    return pin(img, ui, px, glow=1.0)


def reveal(dark, lit, u, sid):
    """Lights come on progressively: per-pixel thresholds from a smooth noise field, sweeping from one side."""
    key = ("revealmask", sid)
    if key not in _cache:
        r = np.random.default_rng(5).random((H // 6, W // 6)).astype(np.float32)
        r = np.asarray(Image.fromarray(r).resize((W, H), Image.NEAREST))      # blocky cells ~ windows
        sweep = (_XX / W) * 0.6 + (1 - _YY / H) * 0.15
        _cache[key] = np.clip(r * 0.5 + sweep * 0.7, 0, 1)
    m = _cache[key]
    k = ease((u - 0.15) / 0.7)
    on = np.clip((k * 1.25 - m) / 0.05, 0, 1)[..., None]
    if sid == "d":    # the boardroom floor comes on at once, as a single wipe along the floor
        on = np.clip((k * 1.4 - _XX[..., None] / W * 0.3) / 0.08, 0, 1)
    return dark * (1 - on) + np.maximum(dark, lit) * on


def map_frame(t, dur):
    import style, canvas, templates
    from canvas import Frame, over, solid
    from templates import TEMPLATES
    fr = Frame()
    beat = dict(gfx=[], tag=None, src=None)
    TEMPLATES["map"](fr, t + 0.6, dur + 0.6, beat, dict(view="us_china", routes=[("WASHINGTON", "BEIJING", "blocked")], chips=True))
    base = solid(style.BG)
    return over(base, fr.rgba())


def frame(T):
    t = 0.0
    for sid, src, dur, ex in SHOTS:
        if T < t + dur or sid == SHOTS[-1][0]:
            lt = T - t
            img = shot_frame(sid, lt)
            # dissolve into the next shot over the last 6 frames when the scenes differ
            nxt = SHOTS[[s[0] for s in SHOTS].index(sid) + 1] if sid != SHOTS[-1][0] else None
            if nxt and dur - lt < 0.25 and nxt[1] != src:
                f = 1 - (dur - lt) / 0.25
                img = img * (1 - f) + shot_frame(nxt[0], 0.0) * f
            img = overlays(img, sid, lt, dur)
            fade = ease(T / 0.8) * ease((TOTAL - T) / 1.2)
            return finish(img * fade, 0.25 if sid in ("f", "g", "j") else 0.4)
        t += dur


def overlays(img, sid, t, dur):
    if sid in ("a", "b", "c", "d", "e", "f", "g", "j"):
        img = tag(img, t, dur, "DRAMATIZATION")
    if sid == "b":
        img = lower_third(img, t, dur, "JENSEN HUANG", "Chief executive, Nvidia")
    if sid == "c":
        img = lower_third(img, t, dur, "NOVEMBER 8, 2026", "An email to Nvidia employees")
    if sid == "d":
        img = lower_third(img, t, dur, "INDEPENDENT INVESTIGATION", "Opened by Nvidia’s board the same day")
    if sid == "f":
        a = win(t, 0.9, dur - 0.1, 0.6)
        img = img * (1 - 0.55 * a * _SCRIM)
        def d(c):
            tracked(c, "ALICE HUANG", 110, H - 118, font(SLAB, 58), a, 0.04)
            tracked(c, "AT THE CENTER OF THE ALLEGATION", 112, H - 76, font(SANS_L, 22), a * 0.85, 0.3)
        img = glow_text(img, surface_text(d), 0.35, 10)
    if sid == "i":
        img = lower_third(img, t, dur, "EXPORT CONTROLS", "Advanced AI chips restricted from China")
        a = win(t, 2.7, dur + 1, 0.3)
        def d_(c):
            tracked(c, "RESTRICTED", W * 0.505, H * 0.17, font(SANS_SB, 26), a, 0.3, "c", (1.0, 0.32, 0.28))
        img = glow_text(img, surface_text(d_), 0.3, 8)
    if sid == "j":
        a = win(t, 0.6, dur + 2, 0.9)
        def d(c):
            tracked(c, "THE SPY ALLEGATIONS", W / 2, H / 2 - 6, font(SLAB, 104), a, 0.02, "c")
            tracked(c, "ROCKING NVIDIA", W / 2, H / 2 + 104, font(SLAB, 104), a, 0.02, "c")
        dim = 1 - 0.35 * a
        img = glow_text(img * dim, surface_text(d), 0.55, 14)
    return img


def save(img, path):
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)


def main():
    if "--still" in sys.argv:
        sid = sys.argv[sys.argv.index("--still") + 1]; t = float(sys.argv[sys.argv.index("--still") + 2])
        out = sys.argv[sys.argv.index("--still") + 3] if len(sys.argv) > sys.argv.index("--still") + 3 else f"/tmp/intro_{sid}.png"
        save(frame(t0_of(sid) + t), out); print(out); return
    os.makedirs(OUT, exist_ok=True)
    n = int(TOTAL * FPS)
    for k in range(n):
        p = os.path.join(OUT, f"{k:05d}.png")
        if not os.path.exists(p) or "--force" in sys.argv:
            save(frame(k / FPS), p)
        if k % 24 == 0:
            print(f"[intro] {k / FPS:.1f}/{TOTAL:.1f}s", flush=True)
    wav = os.path.join(ROOT, "out", "intro_v2.wav")
    subprocess.run([sys.executable, os.path.join(HERE, "intro_score.py"), wav, f"{TOTAL:.3f}",
                    ",".join(f"{s[0]}:{t0_of(s[0]):.3f}" for s in SHOTS)], check=True)
    mp4 = os.path.join(ROOT, "out", "intro_v2.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(OUT, "%05d.png"), "-i", wav,
                    "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k",
                    "-shortest", "-movflags", "+faststart", mp4], check=True)
    print("[done]", mp4)


if __name__ == "__main__":
    main()
