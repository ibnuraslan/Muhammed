"""Transparent title overlay for the farm-rendered Nvidia film (no re-render).

The farm render baked the chapter titles in, but over bright shots (Ch1: the white Capitol dome at dawn) the
cream text and its glow wash out. This writes ONE film-length clip with alpha that goes on the top video track
at 0:00. It is fully transparent except while each chapter title is on screen, where it adds a soft elliptical
dark scrim plus crisp, opaque cream title text (dark outline + the original glow) at exactly the baked
position, size and font, following the baked fade curve frame for frame.

Layout is copied from the title card the farm render used (git a5e97a4~1:nvidia_doc/scenes/title_card.py):
RobotoSlab ExtraBold 112 at baseline H/2+50, RobotoSlab Bold 34 letter-spaced +9 px at baseline H/2-70.
Fade is the same driver: min(1, max(0, (f - f_in) / 12)) * min(1, max(0, (f_out - f) / 12)), f = shot-local
frame (shot frame 1 = first frame of the shot in the film), f_in/f_out from the shot specs (sc_capitol.py,
sc_computex.py). Shot starts come from edit/film_edl.json (1-based film frames, end-exclusive).

  python edit/title_overlay.py                 # writes out/title_overlay/nvidia_title_overlay.mov/.webm + sheet
  python edit/title_overlay.py --sheet-only
"""
import os, sys, json, subprocess
import numpy as np
import skia
from scipy.ndimage import gaussian_filter, grey_dilation
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
FONTS = os.path.join(ROOT, "assets", "fonts")
OUT = os.path.join(ROOT, "out", "title_overlay")
W, H, FPS = 1920, 816, 24
FADE = 12
CREAM = np.array([1.0, 0.97, 0.92], np.float32)

# (EDL shot name, small, big, f_in, f_out) -- values from the shot specs' title=(...) tuples
TITLES = [("c1_01_capitol_dawn_push", "CHAPTER 1", "FOLLOW THE CHIPS", 18, 120),   # sc_capitol.py dawn_push
          ("c2_01_computex_crowd", "CHAPTER 2", "THE MEMO", 18, 120),              # sc_computex.py crowd
          ("c3_01_capitol_ch3_push", "CHAPTER 3", "BEHIND CLOSED DOORS", 18, 120)]  # sc_capitol.py ch3_push


def text_alpha(small, big):
    """Coverage of the baked title text, drawn exactly as title_card.title_image drew it."""
    s = skia.Surface(W, H); c = s.getCanvas(); c.clear(skia.Color4f(0, 0, 0, 0))
    p = skia.Paint(AntiAlias=True); p.setColor4f(skia.Color4f(1, 1, 1, 1))
    f_big = skia.Font(skia.Typeface.MakeFromFile(os.path.join(FONTS, "RobotoSlab-ExtraBold.ttf")), 112)
    f_small = skia.Font(skia.Typeface.MakeFromFile(os.path.join(FONTS, "RobotoSlab-Bold.ttf")), 34)
    big = big.upper(); small = small.upper()
    wb = f_big.measureText(big); ws = sum(f_small.measureText(ch) for ch in small) + 9 * (len(small) - 1)
    x = W / 2 - ws / 2
    for ch in small:
        c.drawString(ch, x, H / 2 - 70, f_small, p); x += f_small.measureText(ch) + 9
    c.drawString(big, W / 2 - wb / 2, H / 2 + 50, f_big, p)
    return s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).astype(np.float32)[..., 3] / 255


def baked_title(alpha):
    """The title RGBA exactly as baked (cream, alpha = text + glow) -- used only to simulate the farm frame."""
    glow = gaussian_filter(alpha, 18) * 0.55 + gaussian_filter(alpha, 5) * 0.35
    out = np.zeros((H, W, 4), np.float32); out[..., :3] = CREAM
    out[..., 3] = np.clip(alpha + glow * (1 - alpha), 0, 1)
    return out


def over(dst, rgb, a):
    """Straight-alpha 'over': layer (rgb, a) on top of dst (straight RGBA)."""
    a = a[..., None]; da = dst[..., 3:4]
    oa = a + da * (1 - a)
    orgb = (np.asarray(rgb) * a + dst[..., :3] * da * (1 - a)) / np.maximum(oa, 1e-6)
    return np.concatenate([orgb, oa], -1)


def overlay_layer(alpha):
    """Full-strength overlay for one title (straight RGBA, float): scrim, glow, dark outline, opaque text."""
    ys, xs = np.nonzero(alpha > 0.02)
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    hw, hh = (xs.max() - xs.min()) / 2, (ys.max() - ys.min()) / 2
    # scrim: a filled ellipse well past the text, Gaussian-feathered -> no hard edges anywhere; ~50% at centre band
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = ((xx - cx) / (hw + 170)) ** 2 + ((yy - cy) / (hh + 95)) ** 2
    scrim = gaussian_filter((r <= 1).astype(np.float32), 55)
    scrim = scrim / scrim.max() * 0.52
    glow = gaussian_filter(alpha, 18) * 0.55 + gaussian_filter(alpha, 5) * 0.35
    outline = np.clip(gaussian_filter(grey_dilation(alpha, size=(5, 5)), 1.6) * 1.15, 0, 1) * 0.75   # ~2-3 px dark rim
    shadow = np.clip(np.roll(gaussian_filter(alpha, 3.0), (3, 2), (0, 1)) * 1.2, 0, 1) * 0.45        # soft drop shadow
    L = np.zeros((H, W, 4), np.float32)
    L = over(L, (0, 0, 0), scrim)
    L = over(L, CREAM, np.clip(glow, 0, 1) * 0.6)          # the original glow (a bit lower: the scrim already lifts contrast)
    L = over(L, (0, 0, 0), np.maximum(outline, shadow))
    L = over(L, CREAM, alpha * 0.97)
    return L


def fade(f, f_in, f_out):
    return min(1.0, max(0.0, (f - f_in) / FADE)) * min(1.0, max(0.0, (f_out - f) / FADE))


def plan():
    edl = json.load(open(os.path.join(HERE, "film_edl.json")))
    starts = {n: (a, b) for a, b, n in edl["shots"]}
    total = edl["end"]                                     # last film frame (1-based); shots end-exclusive at end+1
    assert edl["shots"][0][0] == 1 and edl["shots"][-1][1] == total + 1
    titles = []
    for name, small, big, f_in, f_out in TITLES:
        a, b = starts[name]
        fr = {}                                            # film frame (1-based) -> fade
        for F in range(a, b):
            v = fade(F - a + 1, f_in, f_out)
            if v > 0:
                fr[F] = v
        win = sorted(fr)
        full = [F for F in win if fr[F] >= 1]
        titles.append(dict(name=name, small=small, big=big, shot=(a, b - 1), f_in=f_in, f_out=f_out, fades=fr,
                           window=(win[0], win[-1]), fade_in=(win[0], full[0] - 1), hold=(full[0], full[-1]),
                           fade_out=(full[-1] + 1, win[-1])))
    return total, titles


def tc(F):
    """Editor timecode of 1-based film frame F (film frame 1 = 00:00:00:00)."""
    i = F - 1
    return f"{i // (FPS * 3600):02d}:{i // (FPS * 60) % 60:02d}:{i // FPS % 60:02d}:{i % FPS:02d}"


def to8(L, k):
    """Straight RGBA float layer with alpha scaled by fade k -> uint8 RGBA."""
    o = L.copy(); o[..., 3] *= k
    return (np.clip(o, 0, 1) * 255 + 0.5).astype(np.uint8)


def comp(bg, rgba8):
    a = rgba8[..., 3:4].astype(np.float32) / 255
    return bg * (1 - a) + rgba8[..., :3].astype(np.float32) / 255 * a


def encode(total, titles, layers):
    os.makedirs(OUT, exist_ok=True)
    mov = os.path.join(OUT, "nvidia_title_overlay.mov")
    webm = os.path.join(OUT, "nvidia_title_overlay.webm")
    raw = ["-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    cmds = [["ffmpeg", "-y", "-loglevel", "error"] + raw + ["-c:v", "qtrle", "-pix_fmt", "argb", "-g", "240", mov],
            ["ffmpeg", "-y", "-loglevel", "error"] + raw + ["-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p",
             "-b:v", "0", "-crf", "18", "-row-mt", "1", "-deadline", "good", "-cpu-used", "4", "-auto-alt-ref", "0", webm]]
    procs = [subprocess.Popen(c, stdin=subprocess.PIPE) for c in cmds]
    empty = bytes(W * H * 4)
    lookup = {F: (i, t["fades"][F]) for i, t in enumerate(titles) for F in t["fades"]}
    for F in range(1, total + 1):
        if F in lookup:
            i, k = lookup[F]; buf = to8(layers[i], k).tobytes()
        else:
            buf = empty
        for p in procs:
            p.stdin.write(buf)
        if F % 500 == 0:
            print(f"[overlay] {F}/{total}", flush=True)
    for p in procs:
        p.stdin.close(); assert p.wait() == 0
    return mov, webm


def sheet(titles, layers, bakes):
    """Per chapter: fade-in middle / hold / fade-out middle, over white, mid-grey and a simulated farm frame
    (white + the faint baked title at the same fade), then the overlay on top."""
    sw, sh = 640, 272
    white = np.ones((H, W, 3), np.float32); grey = np.full((H, W, 3), 0.5, np.float32)
    try:
        lab = ImageFont.truetype(os.path.join(FONTS, "RobotoSlab-Bold.ttf"), 22)
    except Exception:
        lab = ImageFont.load_default()
    cols = ["over white", "over mid-grey", "simulated farm frame: white + baked title, then overlay"]
    rows = []
    for i, t in enumerate(titles):
        picks = [("fade-in mid", (t["fade_in"][0] + t["fade_in"][1]) // 2), ("hold", (t["hold"][0] + t["hold"][1]) // 2),
                 ("fade-out mid", (t["fade_out"][0] + t["fade_out"][1]) // 2)]
        for lbl, F in picks:
            k = t["fades"][F]; o8 = to8(layers[i], k)
            b8 = to8(bakes[i], k)
            farm = comp(white, b8)                                    # what the farm render roughly shows
            tiles = [comp(white, o8), comp(grey, o8), comp(farm, o8)]
            rows.append((f"{t['small']} {t['big']}  |  {lbl}  film frame {F}  ({tc(F)})  fade {k:.2f}", tiles))
    pad, head = 12, 34
    img = Image.new("RGB", (pad + 3 * (sw + pad), 40 + len(rows) * (sh + head + pad)), (24, 24, 28))
    d = ImageDraw.Draw(img)
    for j, c in enumerate(cols):
        d.text((pad + j * (sw + pad), 10), c, fill=(220, 220, 220), font=lab if j < 2 else ImageFont.truetype(os.path.join(FONTS, "RobotoSlab-Bold.ttf"), 15))
    y = 40
    for text, tiles in rows:
        d.text((pad, y + 6), text, fill=(240, 200, 120), font=lab)
        for j, tl in enumerate(tiles):
            im = Image.fromarray((np.clip(tl, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((sw, sh), Image.LANCZOS)
            img.paste(im, (pad + j * (sw + pad), y + head))
        y += sh + head + pad
    path = os.path.join(OUT, "title_overlay_check.png")
    img.save(path)
    # one full-size hold frame of Ch1 over white + baked title, to judge sharpness
    t = titles[0]; F = (t["hold"][0] + t["hold"][1]) // 2
    Image.fromarray((np.clip(comp(comp(white, to8(bakes[0], 1)), to8(layers[0], 1)), 0, 1) * 255 + .5).astype(np.uint8)).save(
        os.path.join(OUT, "title_overlay_ch1_hold_fullres.png"))
    return path


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    total, titles = plan()
    alphas = [text_alpha(t["small"], t["big"]) for t in titles]
    layers = [overlay_layer(a) for a in alphas]
    bakes = [baked_title(a) for a in alphas]
    for t in titles:
        print(f"[overlay] {t['small']} {t['big']}: shot {t['shot']}  visible {t['window']} ({tc(t['window'][0])}-{tc(t['window'][1])})"
              f"  fade-in {t['fade_in']}  hold {t['hold']}  fade-out {t['fade_out']}")
    print("[overlay] sheet", sheet(titles, layers, bakes))
    if "--sheet-only" not in sys.argv:
        print("[overlay] wrote", *encode(total, titles, layers))
