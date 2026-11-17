"""Part 2 chapter titles, new style: whole frame dimmed uniformly + clean two-line title (no oval scrim).
The redo clips c4_01 / c5_01 carry the old baked title (title_card.title_image, scrim 0.36, driver fade 18..120 local).
Clean plate: the baked title layer is rebuilt exactly (same code/fonts), its contribution is subtracted and the scrim
divided out; where the lettering is too opaque to invert, the hole is inpainted. Then dim + new title on top."""
import os, numpy as np, skia, cv2
from scipy.ndimage import gaussian_filter, grey_dilation
FONTS = os.environ.get("FONTS", "/home/user/Muhammed/nvidia_doc/assets/fonts")
W, H = 1920, 816
CREAM = np.array([1.0, 0.97, 0.92], np.float32)
TITLES = {"4": ("CHAPTER 4", "THE SECOND EMPLOYEE", 1), "5": ("CHAPTER 5", "THE PASSPORT AND THE PAPER TRAIL", 4103)}
DIM = 0.52
HA = np.array([0, .005, .02, .045, .08, .125, .175, .25, .35, .45, .55, .65, .75, .85, .935, 1.0])
HV = np.array([0, 0, 0, 2.5, 9.5, 19, 33, 52.5, 80, 107, 140, 151, 162, 170, 179, 192.5]); NEW_FADE = 10

def split_title(big, limit=18):
    words = big.split()
    if len(big) <= limit or len(words) < 2: return [big]
    best = min(range(1, len(words)), key=lambda k: max(len(" ".join(words[:k])), len(" ".join(words[k:]))))
    return [" ".join(words[:best]), " ".join(words[best:])]

def text_alpha(small, big, bold_small=False):
    tf_big = skia.Typeface.MakeFromFile(os.path.join(FONTS, "RobotoSlab-ExtraBold.ttf"))
    f_small = skia.Font(skia.Typeface.MakeFromFile(os.path.join(FONTS, "RobotoSlab-Bold.ttf")), 34)
    lines = split_title(big.upper()); size = 112 if len(lines) == 1 else 92
    f_big = skia.Font(tf_big, size); widest = max(f_big.measureText(l) for l in lines)
    if widest > 0.70 * W: size = size * 0.70 * W / widest; f_big = skia.Font(tf_big, size)
    lh = size * 1.12; block = 34 + 0.75 * size + lh * (len(lines) - 1) + size * 0.75; top = H / 2 - block / 2 + 10
    s = skia.Surface(W, H); c = s.getCanvas(); c.clear(skia.Color4f(0, 0, 0, 0))
    p = skia.Paint(AntiAlias=True); p.setColor4f(skia.Color4f(1, 1, 1, 1))
    ps = skia.Paint(AntiAlias=True); ps.setColor4f(skia.Color4f(1, 1, 1, 1))
    if bold_small: ps.setStyle(skia.Paint.kStrokeAndFill_Style); ps.setStrokeWidth(1.6)
    ws = sum(f_small.measureText(ch) for ch in small) + 9 * (len(small) - 1); x = W / 2 - ws / 2
    for ch in small: c.drawString(ch, x, top + 25, f_small, ps); x += f_small.measureText(ch) + 9
    for i, ln in enumerate(lines):
        c.drawString(ln, W / 2 - f_big.measureText(ln) / 2, top + 34 + 0.75 * size + size * 0.72 + i * lh, f_big, p)
    return s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).astype(np.float32)[..., 3] / 255, top + block / 2

def baked_layers(small, big, scrim=0.36):
    """= title_card.title_image: a_t (lettering + glow) and a_o (total, incl. scrim)."""
    alpha, _ = text_alpha(small, big)
    glow = gaussian_filter(alpha, 18) * 0.55 + gaussian_filter(alpha, 5) * 0.35
    a_t = np.clip(alpha + glow * (1 - alpha), 0, 1)
    # title_image's block centre: recompute exactly as title_card does
    lines = split_title(big.upper()); size = 112 if len(lines) == 1 else 92
    tf_big = skia.Typeface.MakeFromFile(os.path.join(FONTS, "RobotoSlab-ExtraBold.ttf")); f_big = skia.Font(tf_big, size)
    widest = max(f_big.measureText(l) for l in lines)
    if widest > 0.70 * W: size = size * 0.70 * W / widest
    lh = size * 1.12; block = 34 + 0.75 * size + lh * (len(lines) - 1) + size * 0.75; top = H / 2 - block / 2 + 10; cy = top + block / 2
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a_s = scrim * np.exp(-0.5 * ((yy - cy) / (0.19 * H)) ** 2) * np.exp(-0.5 * ((xx - W / 2) / (0.36 * W)) ** 2)
    a_o = a_t + a_s * (1 - a_t)
    return a_t, a_o, alpha

def over(dst, rgb, a):
    a = a[..., None]; da = dst[..., 3:4]; oa = a + da * (1 - a)
    orgb = (np.asarray(rgb, np.float32) * a + dst[..., :3] * da * (1 - a)) / np.maximum(oa, 1e-6)
    return np.concatenate([orgb, oa], -1)

def new_text_layer(small, big):
    """The new title lettering (no scrim, no dim): cream text, soft glow, dark rim + drop shadow (title_overlay_ch45 look)."""
    alpha, _ = text_alpha(small, big, bold_small=True)
    rim = np.clip(gaussian_filter(grey_dilation(alpha, size=(7, 7)), 1.5) * 1.1, 0, 1) * 0.9
    shadow = np.clip(np.roll(gaussian_filter(alpha, 3.0), (4, 3), (0, 1)) * 1.2, 0, 1) * 0.7
    glow = np.clip(gaussian_filter(alpha, 14) * 0.35 + gaussian_filter(alpha, 4) * 0.2, 0, 1)
    L = np.zeros((H, W, 4), np.float32)
    L = over(L, CREAM, glow * 0.5); L = over(L, (0, 0, 0), np.maximum(rim, shadow)); L = over(L, CREAM, alpha * 0.97)
    return L

def baked_fade(local):
    return min(1.0, max(0.0, (local - 18) / 12)) * min(1.0, max(0.0, (120 - local) / 12))

def new_fade(local):
    """Visible local frames 19..119 (master Ch4 19-119, Ch5 4121-4221), ~0.4 s ease in/out."""
    u = min(1.0, max(0.0, (local - 18) / NEW_FADE)) * min(1.0, max(0.0, (120 - local) / NEW_FADE))
    return u * u * (3 - 2 * u)

class Title:
    def __init__(s, ch, cream_rendered=None):
        s.small, s.big, s.start = TITLES[ch]
        s.a_t, s.a_o, s.alpha = baked_layers(s.small, s.big)
        s.L = new_text_layer(s.small, s.big)
        s.Cr = cream_rendered
        s.hole_core = s.alpha
    def calibrate(s, frame_rgb_float):
        m = s.alpha > 0.99
        s.Cr = np.median(frame_rgb_float[m], 0); return s.Cr
    def clean(s, img, local):
        """img float 0..255 -> clean plate (baked title removed)."""
        k = baked_fade(local)
        if k <= 0: return img
        ao = s.a_o * k; at = s.a_t * k
        # measured response of the baked lettering+glow (median over flat background, both clips; the render's view
        # transform makes it non-linear in a_t): additive light vs a_t, scaled to the calibrated cream
        add = np.interp(at, HA, HV)[..., None] * (s.Cr / 192.5)[None, None]
        bg = (img - add) / np.maximum(1 - ao, 0.05)[..., None]
        # where the lettering is too opaque the inversion is unreliable: inpaint (weights blend smoothly)
        bad = at > 0.40
        if bad.any():
            m = cv2.dilate(bad.astype(np.uint8), np.ones((5, 5), np.uint8))
            src = np.clip(bg, 0, 255).astype(np.uint8)
            inp = cv2.inpaint(src, m, 9, cv2.INPAINT_TELEA).astype(np.float32)
            w = np.clip((at - 0.30) / 0.10, 0, 1); w = np.maximum(w, cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.5))[..., None]
            bg = bg * (1 - w) + inp * w
        return np.clip(bg, 0, 255)
    def apply(s, img, local):
        """img float 0..255 (with baked title) -> clean plate, dimmed, new title on top."""
        f = s.clean(img, local)
        k = new_fade(local)
        if k <= 0: return f
        f = f * (1 - DIM * k)
        a = (s.L[..., 3] * k)[..., None]
        return f * (1 - a) + s.L[..., :3] * 255 * a
