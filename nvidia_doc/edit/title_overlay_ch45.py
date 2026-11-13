"""Transparent title overlay for the farm master nvidia_ch45.blend (no re-render, no new upload).

The two chapter cards baked into the master (two-line style with a light scrim) wash out over bright shots: the
dusk tower (Ch4) and the pale interview room (Ch5). This writes ONE clip with alpha, exactly the master's length
(10155 frames, 24 fps, 1920x816), that goes on the top video track at 0:00. It is fully transparent except while
each card is on screen, where it adds, following the baked fade frame for frame:
  - a -1 stop darkening of the whole frame (50% black),
  - a wide feathered scrim (~65%) behind the text block, no hard edges,
  - the title text drawn opaque in cream at exactly the baked layout, with a dark outline and a soft drop shadow,
    and the CHAPTER line a touch bolder (stroked) on the same letter positions.

Layout = scenes/title_card.py title_image() as baked (RobotoSlab ExtraBold big lines 92 px wrapped by split_title,
RobotoSlab Bold 34 px letter-spaced +9 CHAPTER line). Fade = add_title driver:
  min(1, max(0, (f - 18) / 12)) * min(1, max(0, (120 - f) / 12)),  f = shot-local frame.
Shot starts come from vo/ch45_timing.json (Ch4 shot 1 at master frame 1, Ch5 shot 1 at 4103). The master also
fades up from black over frames 1-25 (a black colour strip above the picture), so the Ch4 overlay is scaled by
the same fade-up.

  python edit/title_overlay_ch45.py          -> out/title_overlay_ch45/nvidia_ch45_title_overlay.mov + .webm + sheet
  python edit/title_overlay_ch45.py --sheet-only
"""
import os, sys, json, subprocess, re
import numpy as np
import skia
from scipy.ndimage import gaussian_filter, grey_dilation, binary_erosion, binary_dilation
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
FONTS = os.path.join(ROOT, "assets", "fonts")
OUT = os.path.join(ROOT, "out", "title_overlay_ch45")
W, H, FPS = 1920, 816, 24
FADE, F_IN, F_OUT = 12, 18, 120
CREAM = np.array([1.0, 0.97, 0.92], np.float32)
DIM, SCRIM = 0.5, 0.65
TITLES = [("4", "CHAPTER 4", "THE SECOND EMPLOYEE"), ("5", "CHAPTER 5", "THE PASSPORT AND THE PAPER TRAIL")]


def split_title(big, limit=18):            # = title_card.split_title
    words = big.split()
    if len(big) <= limit or len(words) < 2:
        return [big]
    best = min(range(1, len(words)), key=lambda k: max(len(" ".join(words[:k])), len(" ".join(words[k:]))))
    return [" ".join(words[:best]), " ".join(words[best:])]


def text_layers(small, big):
    """(alpha of the baked lettering, alpha of the overlay lettering with a bolder CHAPTER line, block centre y)."""
    tf_big = skia.Typeface.MakeFromFile(os.path.join(FONTS, "RobotoSlab-ExtraBold.ttf"))
    f_small = skia.Font(skia.Typeface.MakeFromFile(os.path.join(FONTS, "RobotoSlab-Bold.ttf")), 34)
    big = big.upper(); small = small.upper()
    lines = split_title(big)
    size = 112 if len(lines) == 1 else 92
    f_big = skia.Font(tf_big, size)
    widest = max(f_big.measureText(ln) for ln in lines)
    if widest > 0.70 * W:
        size = size * 0.70 * W / widest; f_big = skia.Font(tf_big, size)
    lh = size * 1.12
    block = 34 + 0.75 * size + lh * (len(lines) - 1) + size * 0.75
    top = H / 2 - block / 2 + 10
    out = []
    for bold_small in (False, True):
        s = skia.Surface(W, H); c = s.getCanvas(); c.clear(skia.Color4f(0, 0, 0, 0))
        p = skia.Paint(AntiAlias=True); p.setColor4f(skia.Color4f(1, 1, 1, 1))
        ps = skia.Paint(AntiAlias=True); ps.setColor4f(skia.Color4f(1, 1, 1, 1))
        if bold_small:                                   # same glyph positions, stroked a little heavier
            ps.setStyle(skia.Paint.kStrokeAndFill_Style); ps.setStrokeWidth(1.6)
        ws = sum(f_small.measureText(ch) for ch in small) + 9 * (len(small) - 1)
        x = W / 2 - ws / 2
        for ch in small:
            c.drawString(ch, x, top + 25, f_small, ps); x += f_small.measureText(ch) + 9
        for i, ln in enumerate(lines):
            c.drawString(ln, W / 2 - f_big.measureText(ln) / 2, top + 34 + 0.75 * size + size * 0.72 + i * lh, f_big, p)
        out.append(s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).astype(np.float32)[..., 3] / 255)
    return out[0], out[1], top + block / 2


def over(dst, rgb, a):
    a = a[..., None]; da = dst[..., 3:4]
    oa = a + da * (1 - a)
    orgb = (np.asarray(rgb, np.float32) * a + dst[..., :3] * da * (1 - a)) / np.maximum(oa, 1e-6)
    return np.concatenate([orgb, oa], -1)


def overlay_layer(alpha, cy):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    scrim = SCRIM * np.exp(-0.5 * ((yy - cy) / (0.26 * H)) ** 2) * np.exp(-0.5 * ((xx - W / 2) / (0.44 * W)) ** 2)
    dark = 1 - (1 - DIM) * (1 - scrim)                                # -1 stop everywhere, ~83% at the block centre
    rim = np.clip(gaussian_filter(grey_dilation(alpha, size=(7, 7)), 1.5) * 1.1, 0, 1) * 0.9
    shadow = np.clip(np.roll(gaussian_filter(alpha, 3.0), (4, 3), (0, 1)) * 1.2, 0, 1) * 0.7
    glow = np.clip(gaussian_filter(alpha, 14) * 0.35 + gaussian_filter(alpha, 4) * 0.2, 0, 1)
    L = np.zeros((H, W, 4), np.float32)
    L = over(L, (0, 0, 0), dark)
    L = over(L, CREAM, glow * 0.5)
    L = over(L, (0, 0, 0), np.maximum(rim, shadow))
    L = over(L, CREAM, alpha * 0.97)
    return L


def fade(f):
    return min(1.0, max(0.0, (f - F_IN) / FADE)) * min(1.0, max(0.0, (F_OUT - f) / FADE))


def fade_up(F):
    """The master's black colour strip, opacity keyed 1 at frame 1 -> 0 at frame 25 (Bezier ~ smoothstep)."""
    if F >= 25: return 1.0
    u = (F - 1) / 24.0
    return u * u * (3 - 2 * u)


def plan():
    tim = json.load(open(os.path.join(ROOT, "vo", "ch45_timing.json")))
    start = {"4": 1, "5": 1 + sum(s["frames"] for s in tim["4"])}
    total = start["5"] - 1 + sum(s["frames"] for s in tim["5"])
    titles = []
    for c, small, big in TITLES:
        a0 = start[c]
        fr = {}
        for f in range(1, 200):
            v = fade(f) * (fade_up(a0 + f - 1) if c == "4" else 1.0)
            if v > 0:
                fr[a0 + f - 1] = v
        win = sorted(fr); full = [F for F in win if fade(F - a0 + 1) >= 1]
        titles.append(dict(c=c, small=small, big=big, start=a0, fades=fr, window=(win[0], win[-1]),
                           fade_in=(win[0], full[0] - 1), hold=(full[0], full[-1]), fade_out=(full[-1] + 1, win[-1])))
    return total, titles


def tc(F):
    i = F - 1
    return f"{i // (FPS * 3600):02d}:{i // (FPS * 60) % 60:02d}:{i // FPS % 60:02d}:{i % FPS:02d}"


def to8(L, k):
    o = L.copy(); o[..., 3] *= k
    return (np.clip(o, 0, 1) * 255 + 0.5).astype(np.uint8)


def comp(bg, rgba8):
    a = rgba8[..., 3:4].astype(np.float32) / 255
    return bg * (1 - a) + rgba8[..., :3].astype(np.float32) / 255 * a


def lum(img):
    return 0.2126 * img[..., 0] + 0.7152 * img[..., 1] + 0.0722 * img[..., 2]


def encode(total, titles, layers):
    mov = os.path.join(OUT, "nvidia_ch45_title_overlay.mov"); webm = os.path.join(OUT, "nvidia_ch45_title_overlay.webm")
    raw = ["-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    cmds = [["ffmpeg", "-y", "-loglevel", "error"] + raw + ["-c:v", "qtrle", "-pix_fmt", "argb", "-g", "240", mov],
            ["ffmpeg", "-y", "-loglevel", "error"] + raw + ["-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "18",
             "-row-mt", "1", "-deadline", "good", "-cpu-used", "4", "-auto-alt-ref", "0", webm]]
    procs = [subprocess.Popen(c, stdin=subprocess.PIPE) for c in cmds]
    empty = bytes(W * H * 4)
    lookup = {F: (i, k) for i, t in enumerate(titles) for F, k in t["fades"].items()}
    for F in range(1, total + 1):
        if F in lookup:
            i, k = lookup[F]; buf = to8(layers[i], k).tobytes()
        else:
            buf = empty
        for p in procs:
            p.stdin.write(buf)
        if F % 1000 == 0:
            print(f"[overlay45] {F}/{total}", flush=True)
    for p in procs:
        p.stdin.close(); assert p.wait() == 0
    return mov, webm


def sheet(titles, layers, masks):
    """Real farm frames (rendered from nvidia_ch45.blend at 100%/32 samples) before / after the overlay, plus white
    and mid-grey; text and background-under-block luminance measured on every composite."""
    rt = os.path.join(ROOT, "out", "ch45_rendertest")
    F = lambda z: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", z)
    f1, f2, fh = F(18), F(15), F(26)
    tw, th = 620, 264; pad = 12
    rows = []; report = []
    for i, t in enumerate(titles):
        picks = [("fade-in", (t["fade_in"][0] + t["fade_in"][1]) // 2), ("hold", t["start"] + 65),
                 ("fade-out", (t["fade_out"][0] + t["fade_out"][1]) // 2)]
        m = masks[i]; text = binary_erosion(m > 0.9, iterations=2)
        ys, xs = np.nonzero(m > 0.1)
        box = np.zeros_like(text); box[ys.min() - 30:ys.max() + 30, xs.min() - 40:xs.max() + 40] = True
        bgm = box & ~binary_dilation(m > 0.05, iterations=12)
        for lbl, Fr in picks:
            k = t["fades"].get(Fr, 0.0); o8 = to8(layers[i], k)
            p = os.path.join(rt, f"f:{Fr}_f{Fr:05d}.png")
            real = np.asarray(Image.open(p).convert("RGB")).astype(np.float32) / 255 if os.path.exists(p) else None
            tiles = []
            if real is not None:
                after = comp(real, o8)
                tiles += [(real, "farm frame (baked title)"), (after, "farm frame + overlay")]
                Lb, La = lum(real), lum(after)
                report.append(dict(chapter=t["c"], pick=lbl, frame=Fr, fade=round(k, 2),
                                   before=dict(text=round(float(Lb[text].mean()), 3), bg=round(float(Lb[bgm].mean()), 3)),
                                   after=dict(text=round(float(La[text].mean()), 3), bg=round(float(La[bgm].mean()), 3))))
            tiles += [(comp(np.ones((H, W, 3), np.float32), o8), "over white"), (comp(np.full((H, W, 3), 0.5, np.float32), o8), "over mid-grey")]
            rows.append((f"{t['small']} · {t['big']}  |  {lbl}  frame {Fr} ({tc(Fr)})  fade {k:.2f}", tiles))
    ncol = 4
    img = Image.new("RGB", (pad + ncol * (tw + pad), 44 + len(rows) * (th + 60)), (18, 18, 22)); d = ImageDraw.Draw(img)
    d.text((pad, 10), "NVIDIA CH4-5 TITLE OVERLAY · check over the real farm frames (nvidia_ch45.blend, 100%, 32 samples)", fill=(240, 240, 245), font=fh)
    y = 44
    for text_, tiles in rows:
        d.text((pad, y + 4), text_, fill=(240, 200, 120), font=f1)
        for j, (tl, cap) in enumerate(tiles):
            im = Image.fromarray((np.clip(tl, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((tw, th), Image.LANCZOS)
            img.paste(im, (pad + j * (tw + pad), y + 28)); d.text((pad + j * (tw + pad), y + 30 + th), cap, fill=(170, 180, 190), font=f2)
        y += th + 60
    path = os.path.join(OUT, "title_overlay_ch45_check.png"); img.save(path)
    for i, t in enumerate(titles):                                     # the two hold frames at full size, after
        Fr = t["start"] + 65; p = os.path.join(rt, f"f:{Fr}_f{Fr:05d}.png")
        if os.path.exists(p):
            real = np.asarray(Image.open(p).convert("RGB")).astype(np.float32) / 255
            Image.fromarray((np.clip(comp(real, to8(layers[i], t["fades"][Fr])), 0, 1) * 255 + .5).astype(np.uint8)).save(
                os.path.join(OUT, f"ch{t['c']}_title_hold_with_overlay_fullres.png"))
    json.dump(report, open(os.path.join(OUT, "title_overlay_ch45_measure.json"), "w"), indent=1)
    return path, report


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    total, titles = plan()
    baked, layers, masks = [], [], []
    for t in titles:
        a_baked, a_bold, cy = text_layers(t["small"], t["big"])
        layers.append(overlay_layer(a_bold, cy)); masks.append(a_baked)
    for t in titles:
        print(f"[overlay45] {t['small']}: visible {t['window']} ({tc(t['window'][0])}-{tc(t['window'][1])}) "
              f"fade-in {t['fade_in']} hold {t['hold']} fade-out {t['fade_out']}")
    p, rep = sheet(titles, layers, masks)
    print("[overlay45] sheet", p)
    for r in rep:
        print("[overlay45] measure", r)
    if "--sheet-only" not in sys.argv:
        print("[overlay45] wrote", *encode(total, titles, layers))
