"""Post-production for the Iceman short: grade, interpolate, particles, typography, assembly.

Usage:  python post.py <frames_root> <work_dir> <out.mp4>
frames_root/shotN_*/fXXXX.png are the raw Cycles renders (12 fps, 960x408).
"""
import os, sys, json, glob, math, subprocess, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.ndimage import gaussian_filter

FR, WK, OUTMP4 = sys.argv[1], sys.argv[2], sys.argv[3]
W, H = 1280, 544
FPS = 24
FONT_DIR = "/usr/share/fonts/opentype/inter/"
F_LIGHT = FONT_DIR + "Inter-Light.otf"
F_THIN = FONT_DIR + "InterDisplay-Thin.otf"
F_REG = FONT_DIR + "Inter-Regular.otf"
F_MED = FONT_DIR + "Inter-Medium.otf"

SHOTS = [  # (render dir, grade preset, particles preset)
    ("shot1_peaks", "dawn", "none"),
    ("shot2_map", "map", "none"),
    ("shot3_trail", "storm", "blizzard"),
    ("shot4_axe", "night", "macro"),
    ("shot5_name", "deepnight", "topdown"),
]
XFADE = 12  # frames of dissolve between shots
ZOOM = {"shot2_map": 1.05}  # slight push-in crops the terrain tile's edge out of frame


# ----------------------------------------------------------------------------- helpers
def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def window(t, a, b, fade=0.5):
    """1 inside [a,b] with smooth fades of `fade` seconds at each end."""
    return smooth((t - a) / fade) * smooth((b - t) / fade)


def load(path):
    im = Image.open(path)
    a = np.asarray(im).astype(np.float32)
    return a[..., :3] / (65535.0 if a.max() > 255 else 255.0)


def save(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)


def lum(a):
    return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722


# ----------------------------------------------------------------------------- grading
GRADES = {
    #          lift (shadow tint)        gain (highlight tint)   sat   contrast  gamma
    "dawn":   ((0.010, 0.020, 0.040), (1.03, 1.00, 0.97), 0.95, 0.18, 1.00),
    "map":    ((0.012, 0.018, 0.030), (0.97, 1.00, 1.04), 0.65, 0.12, 0.98),
    "storm":  ((0.004, 0.012, 0.028), (0.97, 1.00, 1.05), 0.8, 0.32, 1.12),
    "night":  ((0.004, 0.014, 0.034), (1.04, 1.00, 0.96), 0.92, 0.20, 1.04),
    "deepnight": ((0.004, 0.012, 0.035), (0.96, 1.00, 1.05), 0.85, 0.22, 1.06),
}


def grade(a, preset):
    lift, gain, sat, con, gam = GRADES[preset]
    a = a ** gam
    y = lum(a)[..., None]
    a = y + (a - y) * sat
    # filmic S-curve around mid grey
    a = a + con * (a - a * a) * (a - 0.5) * 2.0
    lift = np.array(lift); gain = np.array(gain)
    a = lift + a * (gain - lift)
    return np.clip(a, 0, 1)


# ----------------------------------------------------------------------------- stage 1: grade + interpolate
def stage1(shot, preset):
    src = os.path.join(FR, shot)
    g12 = os.path.join(WK, shot, "g12"); g24 = os.path.join(WK, shot, "g24")
    if os.path.isdir(g24) and len(os.listdir(g24)) > 0:
        return sorted(glob.glob(g24 + "/*.png"))
    os.makedirs(g12, exist_ok=True); os.makedirs(g24, exist_ok=True)
    files = sorted(glob.glob(src + "/f*.png"))
    for k, f in enumerate(files):
        save(grade(load(f), preset), os.path.join(g12, f"{k:04d}.png"))
    # motion-compensated interpolation 12 -> 24 fps, then lanczos upscale to delivery size
    zoom = ZOOM.get(shot, 1.0)
    zw, zh = int(W * zoom) // 2 * 2, int(H * zoom) // 2 * 2
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "12", "-i", g12 + "/%04d.png",
                    "-vf", f"minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
                           f"scale={zw}:{zh}:flags=lanczos,crop={W}:{H},unsharp=5:5:0.35",
                    g24 + "/%04d.png"], check=True)
    return sorted(glob.glob(g24 + "/*.png"))


# ----------------------------------------------------------------------------- particles (falling snow)
class Snow:
    """Flakes live in camera space; projected with perspective, depth-of-field and motion blur."""

    def __init__(self, preset, seed=1):
        self.p = preset
        r = np.random.default_rng(seed)
        cfg = {
            "blizzard": dict(n=1100, wind=(0.9, 0.12), fall=0.35, turb=0.5, size=0.8, bright=0.6, tint=(0.85, 0.9, 1.0), focus=0.5),
            "macro":    dict(n=380, wind=(0.12, 0.0), fall=0.22, turb=0.15, size=1.5, bright=0.75, tint=(0.8, 0.88, 1.0), focus=0.55),
            "topdown":  dict(n=650, wind=(0.35, 0.1), fall=0.0, turb=0.25, size=1.1, bright=0.8, tint=(0.75, 0.85, 1.0), focus=0.9),
        }.get(preset)
        self.cfg = cfg
        if cfg is None:
            return
        n = cfg["n"]
        self.x = r.uniform(-1.6, 1.6, n); self.y = r.uniform(-1.0, 1.0, n); self.z = r.uniform(0.12, 1.6, n)
        self.ph = r.uniform(0, 6.28, n); self.sz = r.uniform(0.6, 1.4, n)

    def layer(self, t, dt=1 / FPS):
        if self.cfg is None:
            return None
        c = self.cfg
        f = 0.9  # focal length in normalised units
        imgs = [Image.new("L", (W, H), 0) for _ in range(3)]
        draws = [ImageDraw.Draw(im) for im in imgs]
        # screen-space position: wind/fall velocity divided by depth (parallax), wrapped
        def pos(tt):
            vx = c["wind"][0] * tt + c["turb"] * 0.15 * np.sin(tt * 1.3 + self.ph)
            vy = c["fall"] * tt + c["wind"][1] * tt + c["turb"] * 0.1 * np.cos(tt * 1.7 + self.ph * 2)
            sx = (self.x + vx * 0.25 / self.z + 1.6) % 3.2 - 1.6
            sy = (self.y + vy * 0.25 / self.z + 1.0) % 2.0 - 1.0
            return sx, sy
        X0, Y0 = pos(t - dt * 0.25); X1, Y1 = pos(t + dt * 0.25)  # 180-degree shutter
        for k in range(len(self.x)):
            x0, y0, x1, y1 = X0[k], Y0[k], X1[k], Y1[k]
            if abs(x1 - x0) > 1 or abs(y1 - y0) > 1:  # wrapped this frame
                continue
            z = self.z[k]
            sx0 = W / 2 + x0 * W / 2; sy0 = H / 2 + y0 * W / 2
            sx1 = W / 2 + x1 * W / 2; sy1 = H / 2 + y1 * W / 2
            rad = max(0.6, c["size"] * self.sz[k] * 1.6 / z)
            dof = abs(math.log(z / c["focus"]))
            b = 0 if dof < 0.35 else (1 if dof < 0.9 else 2)
            val = int(255 * min(1.0, 0.9 / (1 + dof * 0.8)))
            draws[b].line([(sx0, sy0), (sx1, sy1)], fill=val, width=max(1, int(rad * 2)))
            draws[b].ellipse([sx0 - rad, sy0 - rad, sx0 + rad, sy0 + rad], fill=val)
            draws[b].ellipse([sx1 - rad, sy1 - rad, sx1 + rad, sy1 + rad], fill=val)
        out = np.zeros((H, W), np.float32)
        for b, sig in enumerate((0.9, 2.5, 7.0)):
            a = np.asarray(imgs[b], np.float32) / 255
            if a.any():
                out += gaussian_filter(a, sig) * (1.0, 0.8, 0.55)[b]
        return out * c["bright"]


# ----------------------------------------------------------------------------- camera / film effects
_rng = np.random.default_rng(99)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
RR = np.sqrt(((XX - W / 2) / (W / 2)) ** 2 + ((YY - H / 2) / (H / 2)) ** 2 * 0.55)
VIGNETTE = (1 - 0.38 * np.clip(RR - 0.35, 0, None) ** 1.6)[..., None]


def film(a, i, bloom=0.22):
    # bloom / halation: highlights glow with a warm-red fringe like film
    hi = np.clip(a - 0.72, 0, None)
    if hi.any():
        bl = np.stack([gaussian_filter(hi[..., c], 14) for c in range(3)], -1)
        a = a + bl * np.array([1.15, 0.95, 0.85]) * bloom * 2
    # lens: subtle chromatic aberration at the edges
    a2 = a.copy()
    sw, sh = int(W * 1.0016), int(H * 1.0016)
    ox, oy = (sw - W) // 2, (sh - H) // 2
    a2[..., 0] = np.asarray(Image.fromarray(a[..., 0].astype(np.float32)).resize((sw, sh), Image.BILINEAR))[oy:oy + H, ox:ox + W]
    a = a2 * VIGNETTE
    # grain: luminance-dependent, slightly clumped
    g = _rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    g = np.asarray(Image.fromarray(g).resize((W, H), Image.BICUBIC))
    y = lum(np.clip(a, 0, 1))[..., None]
    a = a + g[..., None] * 0.017 * (0.35 + 0.65 * (1 - np.abs(y - 0.45) * 1.6).clip(0.2, 1))
    return np.clip(a, 0, 1)


# ----------------------------------------------------------------------------- typography
_font_cache = {}


def font(path, size):
    k = (path, size)
    if k not in _font_cache:
        _font_cache[k] = ImageFont.truetype(path, size)
    return _font_cache[k]


def tracked(draw, xy, text, fnt, fill, tracking=0.18, anchor="l"):
    """Draw text with letter-spacing. anchor l/c/r horizontally."""
    sp = fnt.size * tracking
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + sp * (len(text) - 1)
    x, y = xy
    if anchor == "c":
        x -= total / 2
    elif anchor == "r":
        x -= total
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += w + sp
    return total


def overlay(a, items):
    """items: list of (callable(draw), alpha). Rendered on an RGBA layer, softened, composited."""
    if not items:
        return a
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for fn, alpha in items:
        if alpha <= 0.002:
            continue
        sub = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fn(ImageDraw.Draw(sub))
        if alpha < 1:
            arr = np.asarray(sub).copy(); arr[..., 3] = (arr[..., 3] * alpha).astype(np.uint8)
            sub = Image.fromarray(arr)
        lay = Image.alpha_composite(lay, sub)
    # tiny glow so text sits in the image rather than on top of it
    L = np.asarray(lay).astype(np.float32) / 255
    glow = gaussian_filter(L[..., 3], 3) * 0.25
    al = L[..., 3:4]
    rgb = L[..., :3]
    a = a * (1 - al) + rgb * al
    return np.clip(a + glow[..., None] * 0.15, 0, 1)


WHITE = (236, 240, 245, 255)
DIM = (200, 210, 222, 255)
RED = (214, 38, 30, 255)


def captions(shot, t, dur, i, labels=None):
    items = []
    if shot == "shot1_peaks":
        al = window(t, 0.9, dur - 0.6, 0.8)
        def f(d):
            tracked(d, (64, H - 128), "ÖTZTAL ALPS", font(F_LIGHT, 34), WHITE, 0.32)
            d.line([(66, H - 80), (66 + 46, H - 80)], fill=(236, 240, 245, 200), width=1)
            tracked(d, (64, H - 68), "AUSTRIAN – ITALIAN BORDER", font(F_REG, 14), DIM, 0.35)
        items.append((f, al))
    elif shot == "shot2_map" and labels is not None:
        # labels.json is indexed by 12 fps render frame; interpolate for 24 fps
        k = i / 2.0; k0 = int(math.floor(k)); k1 = min(k0 + 1, len(labels) - 1); fr = k - k0
        def P(name):
            a_, b_ = labels[str(min(k0, len(labels) - 1))][name], labels[str(k1)][name]
            z = ZOOM.get(shot, 1.0)
            u = (a_[0] * (1 - fr) + b_[0] * fr - 0.5) * z + 0.5
            v = (a_[1] * (1 - fr) + b_[1] * fr - 0.5) * z + 0.5
            return (u * W, v * H)
        def countries(d):
            for nm, txt in (("austria", "AUSTRIA"), ("italy", "ITALY")):
                x, y = P(nm)
                if -200 < x < W + 200 and -50 < y < H + 50:
                    tracked(d, (x, y - 14), txt, font(F_LIGHT, 26), (30, 36, 48, 190), 0.6, "c")
        items.append((countries, window(t, 0.4, dur - 0.2, 0.8)))
        def start(d):
            x, y = P("start")
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(30, 34, 44, 255))
            tracked(d, (x + 12, y - 9), "SIMILAUN HUT", font(F_MED, 13), (30, 34, 44, 255), 0.25)
        items.append((start, window(t, 0.5, dur - 0.2, 0.6)))
        def peak(d):
            x, y = P("peak")
            d.polygon([(x, y - 6), (x - 5, y + 3), (x + 5, y + 3)], fill=(30, 34, 44, 230))
            tracked(d, (x + 10, y - 8), "FINAILSPITZE  3,514 M", font(F_MED, 12), (30, 34, 44, 230), 0.2)
        items.append((peak, window(t, 1.2, dur - 0.2, 0.6)))
        reveal = smooth((t - dur * 0.72) / 0.5)
        def disc(d):
            x, y = P("discovery")
            r = 9 + 26 * (1 - reveal)
            d.ellipse([x - r, y - r, x + r, y + r], outline=RED, width=2)
            s_ = 6
            d.line([(x - s_, y - s_), (x + s_, y + s_)], fill=RED, width=3)
            d.line([(x - s_, y + s_), (x + s_, y - s_)], fill=RED, width=3)
            lx, ly = x + 40, y - 70
            d.line([(x + 9, y - 9), (lx, ly), (lx + 150, ly)], fill=(214, 38, 30, 230), width=1)
            tracked(d, (lx + 4, ly - 24), "PLACE OF DISCOVERY", font(F_MED, 15), RED, 0.22)
            tracked(d, (lx + 4, ly + 7), "3,210 M  ·  19 SEPT 1991", font(F_MED, 13), (25, 22, 26, 255), 0.22)
        items.append((disc, reveal * window(t, 0, dur - 0.1, 0.3)))
    elif shot == "shot3_trail":
        al = window(t, 0.7, dur - 0.5, 0.9)
        def f(d):
            tracked(d, (W / 2, H / 2 - 46), "5,300 YEARS EARLIER", font(F_THIN, 46), WHITE, 0.28, "c")
            tracked(d, (W / 2, H / 2 + 20), "c. 3230 BC", font(F_REG, 15), DIM, 0.4, "c")
        items.append((f, al))
    elif shot == "shot4_axe":
        al = window(t, 0.9, dur - 0.4, 0.7)
        def f(d):
            x0 = W - 330; y0 = 150
            tracked(d, (x0, y0), "COPPER AXE", font(F_LIGHT, 30), WHITE, 0.3)
            d.line([(x0 + 2, y0 + 48), (x0 + 40, y0 + 48)], fill=(236, 240, 245, 200), width=1)
            rows = [("BLADE", "9.5 CM  ·  99.7 % COPPER"), ("HAFT", "60 CM  ·  YEW WOOD"), ("BOUND", "LEATHER & BIRCH TAR")]
            for k_, (a_, b_) in enumerate(rows):
                yy = y0 + 64 + k_ * 26
                tracked(d, (x0, yy), a_, font(F_MED, 12), (170, 182, 198, 255), 0.3)
                tracked(d, (x0 + 74, yy), b_, font(F_REG, 13), WHITE, 0.18)
        items.append((f, al))
    elif shot == "shot5_name":
        al = window(t, 2.2, dur + 1, 0.9)
        def f(d):
            tracked(d, (W / 2, H - 92), "THE MAN FROM THE ICE", font(F_LIGHT, 18), WHITE, 0.55, "c")
        items.append((f, al))
    return items


# ----------------------------------------------------------------------------- caption scrim
def scrim(a, cx, cy, rx, ry, strength):
    """Soft elliptical darkening behind captions so thin type stays legible over bright snow."""
    if strength <= 0.002:
        return a
    m = np.exp(-(((XX - cx) / rx) ** 2 + ((YY - cy) / ry) ** 2) * 1.5)[..., None]
    return a * (1 - m * strength)


SCRIMS = {  # shot -> (cx, cy, rx, ry, strength, caption window start, end)
    "shot1_peaks": (200, H - 95, 420, 120, 0.55, 0.9, -0.6),
    "shot4_axe": (W - 200, 220, 360, 150, 0.35, 0.9, -0.4),
}


# ----------------------------------------------------------------------------- horizon haze (shot 3)
def horizon_haze(a, t):
    band = np.exp(-((YY - H * 0.33) / (H * 0.07)) ** 2)[..., None]
    drift = 0.75 + 0.25 * np.sin(XX / W * 6.0 + t * 0.6)[..., None]
    col = np.array([0.42, 0.48, 0.58])
    k = band * drift * 0.3
    return a * (1 - k) + col * k


# ----------------------------------------------------------------------------- main
def main():
    os.makedirs(WK, exist_ok=True)
    clips = []
    for shot, gpreset, ppreset in SHOTS:
        files = stage1(shot, gpreset)
        labels = None
        lj = os.path.join(FR, shot, "labels.json")
        if os.path.exists(lj):
            labels = json.load(open(lj))
        snow = Snow(ppreset, seed=len(clips) + 3)
        dur = len(files) / FPS
        outd = os.path.join(WK, shot, "fx"); os.makedirs(outd, exist_ok=True)
        done = sorted(glob.glob(outd + "/*.png"))
        if len(done) != len(files):
            for i, f in enumerate(files):
                t = i / FPS
                a = load(f)
                if shot == "shot3_trail":
                    a = horizon_haze(a, t)
                sl = snow.layer(t + 3.0)
                if sl is not None:
                    tint = np.array(snow.cfg["tint"])
                    a = 1 - (1 - a) * (1 - np.clip(sl, 0, 1)[..., None] * tint)
                a = film(a, i, bloom=0.3 if shot in ("shot1_peaks", "shot4_axe") else 0.15)
                if shot in SCRIMS:
                    cx, cy, rx, ry, st, ta, tb = SCRIMS[shot]
                    a = scrim(a, cx, cy, rx, ry, st * window(t, ta, dur + tb, 0.8))
                a = overlay(a, captions(shot, t, dur, i, labels))
                save(a, os.path.join(outd, f"{i:04d}.png"))
                if i % 24 == 0:
                    print(f"[fx] {shot} {i}/{len(files)}", flush=True)
        clips.append(sorted(glob.glob(outd + "/*.png")))

    # ---- assemble with dissolves, fade in from black, end card
    final = os.path.join(WK, "final"); shutil.rmtree(final, ignore_errors=True); os.makedirs(final)
    seq = []  # list of (fileA, fileB or None, mix)
    for ci, c in enumerate(clips):
        if ci == 0:
            seq += [(f, None, 0) for f in c]
        else:
            n = min(XFADE, len(c))
            for k in range(n):
                prev = seq[-n + k]
                seq[-n + k] = (prev[0], c[k], (k + 1) / (n + 1))
            seq += [(f, None, 0) for f in c[n:]]
    idx = 0
    total = len(seq)
    for k, (fa, fb, m) in enumerate(seq):
        a = load(fa)
        if fb is not None:
            a = a * (1 - smooth(m)) + load(fb) * smooth(m)
        fade_in = smooth(k / 18.0)
        fade_out = smooth((total - 1 - k) / 30.0)
        save(a * fade_in * fade_out, os.path.join(final, f"{idx:05d}.png")); idx += 1
    # end card
    for k in range(int(FPS * 4.0)):
        t = k / FPS
        a = np.zeros((H, W, 3), np.float32) + 0.008
        def f1(d):
            tracked(d, (W / 2, H / 2 - 34), "5,300 YEARS IN THE ICE", font(F_THIN, 40), WHITE, 0.3, "c")
        def f2(d):
            tracked(d, (W / 2, H / 2 + 34), "RENDERED ENTIRELY FROM CODE  ·  PYTHON + BLENDER CYCLES", font(F_REG, 11), (150, 160, 175, 255), 0.35, "c")
        a = overlay(a, [(f1, window(t, 0.3, 3.6, 0.7)), (f2, window(t, 1.0, 3.6, 0.7))])
        a = film(a, k, bloom=0)
        save(a, os.path.join(final, f"{idx:05d}.png")); idx += 1
    n_frames = idx
    print(f"[assemble] {n_frames} frames = {n_frames / FPS:.1f}s", flush=True)

    # ---- soundtrack
    wav = os.path.join(WK, "score.wav")
    starts = []
    acc = 0
    for ci, c in enumerate(clips):
        starts.append(acc / FPS)
        acc += len(c) - (XFADE if ci < len(clips) - 1 else 0)
    subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "sound.py"), wav,
                    f"{n_frames / FPS:.3f}", ",".join(f"{s:.3f}" for s in starts)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", final + "/%05d.png", "-i", wav,
                    "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-tune", "film",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUTMP4], check=True)
    print("[done]", OUTMP4)


if __name__ == "__main__":
    main()
