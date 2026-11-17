"""Format layers for the Nvidia film: chapter titles (clean plate + full-frame dim + clean title), photo cards, burned captions."""
import json, re, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from scipy.ndimage import gaussian_filter, grey_dilation
W, H, FPS = 1920, 816, 24
SP = '/tmp/claude-0/-home-user-Muhammed/8eef100b-02db-57dc-974f-d5b225739e26/scratchpad'
RF = '/home/user/Muhammed/nvidia_doc/assets/fonts'
FF = SP + '/fmt/fonts'
CREAM = np.array([1.0, 0.97, 0.92], np.float32) * 255
# ------------------------------------------------------------------ chapter titles
TITLES = [(922, 1022, 'CHAPTER 1', 'FOLLOW THE CHIPS'), (4770, 4870, 'CHAPTER 2', 'THE MEMO'), (7752, 7852, 'CHAPTER 3', 'BEHIND CLOSED DOORS')]
def text_alpha(small, big):
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    fb = ImageFont.truetype(f'{RF}/RobotoSlab-ExtraBold.ttf', 112); fs = ImageFont.truetype(f'{RF}/RobotoSlab-Bold.ttf', 34)
    ws = sum(fs.getlength(ch) for ch in small) + 9 * (len(small) - 1); x = W / 2 - ws / 2
    for ch in small: d.text((x, H / 2 - 70), ch, font=fs, fill=255, anchor='ls'); x += fs.getlength(ch) + 9
    d.text((W / 2 - fb.getlength(big) / 2, H / 2 + 50), big, font=fb, fill=255, anchor='ls')
    return np.asarray(im, np.float32) / 255
def title_layer(small, big):
    a = text_alpha(small, big)
    glow = np.clip(gaussian_filter(a, 18) * 0.55 + gaussian_filter(a, 5) * 0.35, 0, 1) * 0.6
    outline = np.clip(gaussian_filter(grey_dilation(a, size=(5, 5)), 1.6) * 1.15, 0, 1) * 0.75
    shadow = np.clip(np.roll(gaussian_filter(a, 3.0), (3, 2), (0, 1)) * 1.2, 0, 1) * 0.45
    # straight-alpha stack: glow (cream) -> dark rim/shadow -> text (cream); keep as premultiplied rgb + alpha
    rgb = np.zeros((H, W, 3), np.float32); al = np.zeros((H, W), np.float32)
    for col, aa in ((CREAM, glow), (np.zeros(3, np.float32), np.maximum(outline, shadow)), (CREAM, a * 0.97)):
        rgb = rgb * (1 - aa[..., None]) + col * aa[..., None]; al = al + aa * (1 - al)
    return rgb, al                                     # premultiplied
# baked-title extent (all three bakes use the same layout; Ch2's bake says BEHIND CLOSED DOORS, the widest)
_ba = text_alpha('CHAPTER 3', 'BEHIND CLOSED DOORS'); _g = gaussian_filter(_ba, 18) > 0.01
_ys, _xs = np.nonzero(_g | (_ba > 0)); BOX = (max(0, _xs.min() - 40), min(W - 1, _xs.max() + 40), _ys.min() - 30, _ys.max() + 30)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
def _boxmask(x0, x1, y0, y1, f=40):
    dx = np.maximum(np.maximum(x0 - xx, xx - x1), 0); dy = np.maximum(np.maximum(y0 - yy, yy - y1), 0)
    return np.clip(1 - np.sqrt(dx ** 2 + dy ** 2) / f, 0, 1)
BOX = (230, 1690, 330, 510)
PMASK = _boxmask(*BOX, f=60)[..., None]
def clean_plate(img):
    x0, x1, y0, y1 = BOX; f = img.astype(np.float32)
    top = f[y0 - 22:y0 - 6].mean(0); bot = f[y1 + 6:y1 + 22].mean(0)
    top = gaussian_filter(top, (25, 0)); bot = gaussian_filter(bot, (25, 0))
    t = np.clip((yy[:, :1] - (y0 - 14)) / ((y1 + 14) - (y0 - 14)), 0, 1)[..., None]
    plate = top[None] * (1 - t) + bot[None] * t
    return f * (1 - PMASK) + plate * PMASK
TL = {i: title_layer(s, b) for i, (_, _, s, b) in enumerate(TITLES)}
def title_state(n):
    for i, (w0, w1, s, b) in enumerate(TITLES):
        if w0 - 12 <= n <= w1 + 12:
            a = w0 - 18                                   # shot-local frame 1 (fade(f) = (f-18)/12 ... (120-f)/12)
            f = n - a + 1
            k = min(1, max(0, (f - 18) / 12)) * min(1, max(0, (120 - f) / 12))
            dim = 0.52 * min(1, max(0, (n - w0 + 1) / 10)) * min(1, max(0, (w1 + 1 - n) / 10))
            plate = 1.0 if (i == 1 and w0 <= n <= w1) else 0.0
            return i, k, dim, plate
    return None
def apply_title(f, n):
    st = title_state(n)
    if st is None: return f
    i, k, dim, plate = st
    if plate: f = clean_plate(f)
    f = f * (1 - dim)
    rgb, al = TL[i]
    return f * (1 - al[..., None] * k) + rgb * k
# ------------------------------------------------------------------ cards
PH = int(round(0.30 * H)); BORDER = 8; MARGIN = 64; CARD_BOTTOM = 668
f_name = ImageFont.truetype(f'{FF}/SpecialElite-Regular.ttf', 48)
f_role = ImageFont.truetype(f'{FF}/CourierPrime-Bold.ttf', 24)
def make_card(photo, name, role, side, crop_y=0.5, crop_x=0.5):
    im = Image.open(photo).convert('L'); im = ImageOps.autocontrast(im, cutoff=1)
    w, h = im.size; s = min(w, h)
    x0 = int((w - s) * crop_x); y0 = int((h - s) * crop_y)
    im = im.crop((x0, y0, x0 + s, y0 + s)).resize((PH, PH), Image.LANCZOS)
    pw = PH + 2 * BORDER
    d0 = ImageDraw.Draw(Image.new('L', (1, 1)))
    tw = max(d0.textlength(name, font=f_name), d0.textlength(role, font=f_role)) if role else d0.textlength(name, font=f_name)
    cw = int(max(pw, tw)) + 40; chh = pw + 140
    rgba = Image.new('RGBA', (cw, chh), (0, 0, 0, 0))
    px = cw - 20 - pw if side == 'right' else 20
    photo_rgba = Image.new('RGBA', (pw, pw), (255, 255, 255, 255)); photo_rgba.paste(Image.merge('RGBA', [im, im, im, Image.new('L', im.size, 255)]), (BORDER, BORDER))
    # shadow
    sh = Image.new('L', (cw, chh), 0); sd = ImageDraw.Draw(sh)
    sd.rectangle([px + 4, 14 + 6, px + pw + 4, 14 + pw + 6], fill=150)
    td = ImageDraw.Draw(rgba)
    ny = 14 + pw + 14 + 42; ry = ny + 32
    anchor = 'rs' if side == 'right' else 'ls'; tx = px + pw if side == 'right' else px
    for txt, fnt, yy_ in ((name, f_name, ny), (role, f_role, ry)):
        if txt: sd.text((tx + 2, yy_ + 2), txt, font=fnt, fill=230, anchor=anchor)
    sh = sh.filter(ImageFilter.GaussianBlur(7))
    out = Image.new('RGBA', (cw, chh), (0, 0, 0, 0)); out.putalpha(sh)
    out.alpha_composite(photo_rgba, (px, 14))
    td = ImageDraw.Draw(out)
    for txt, fnt, yy_ in ((name, f_name, ny), (role, f_role, ry)):
        if txt: td.text((tx, yy_), txt, font=fnt, fill=(255, 255, 255, 255), anchor=anchor)
    a = np.asarray(out, np.float32); al = a[..., 3] / 255
    return a[..., :3] * al[..., None], al          # premultiplied
def ease_out(t): return 1 - (1 - t) ** 3
def ease_in(t): return t ** 3
IN, HOLD, OUT = 0.35, 3.0, 0.30
def card_offset(t, t0, t_end, width):
    """x offset (px toward the card's own edge) at time t; None if not visible."""
    t1 = t0 + IN; t3 = min(t0 + IN + HOLD + OUT, t_end); t2 = t3 - OUT
    if t < t0 or t >= t3: return None
    if t < t1: return (1 - ease_out((t - t0) / IN)) * (width + MARGIN + 10)
    if t < t2: return 0.0
    return ease_in((t - t2) / OUT) * (width + MARGIN + 10)
def place_card(f, card, side, off):
    rgb, al = card; ch, cw = al.shape
    y0 = CARD_BOTTOM - ch + 30
    x0 = (W - MARGIN - cw + 20 + int(round(off))) if side == 'right' else (MARGIN - 20 - int(round(off)))
    xa, xb = max(0, x0), min(W, x0 + cw)
    if xb <= xa: return f
    sl = slice(xa - x0, xb - x0)
    f[y0:y0 + ch, xa:xb] = f[y0:y0 + ch, xa:xb] * (1 - al[:, sl, None]) + rgb[:, sl]
    return f
# ------------------------------------------------------------------ captions
f_cap = ImageFont.truetype(f'{FF}/CourierPrime-Bold.ttf', 27)
CAP_BASE = int(round(H * 0.94)); CAP_LINE = 34; ONE_LINE_MAX = 66
def load_srt(path):
    caps = []
    for blk in open(path, encoding='utf-8').read().strip().split('\n\n'):
        L = blk.split('\n'); a, b = L[1].split(' --> ')
        ts = lambda s: int(s[:2]) * 3600 + int(s[3:5]) * 60 + int(s[6:8]) + int(s[9:12]) / 1000
        lines = L[2:]; j = ' '.join(lines)
        caps.append((ts(a), ts(b), [j] if len(j) <= ONE_LINE_MAX else lines))
    return caps
_cap_cache = {}
def caption_layer(lines):
    key = tuple(lines)
    if key in _cap_cache: return _cap_cache[key]
    hh = CAP_LINE * len(lines) + 40; img = Image.new('L', (W, hh), 0); sh = Image.new('L', (W, hh), 0)
    d = ImageDraw.Draw(img); sd = ImageDraw.Draw(sh)
    for i, l in enumerate(lines):
        y = hh - 20 - (len(lines) - 1 - i) * CAP_LINE
        d.text((W / 2, y), l, font=f_cap, fill=255, anchor='ms'); sd.text((W / 2 + 1, y + 2), l, font=f_cap, fill=255, anchor='ms', stroke_width=3, stroke_fill=255)
    sh = np.clip(np.asarray(sh.filter(ImageFilter.GaussianBlur(3)), np.float32) / 255 * 1.3, 0, 0.92)
    tx = np.asarray(img, np.float32) / 255
    al = tx + sh * (1 - tx); rgb = (tx * 255)[..., None].repeat(3, 2)
    y0 = CAP_BASE + 20 - hh
    _cap_cache[key] = (y0, rgb, al); return _cap_cache[key]
def apply_caption(f, lines):
    y0, rgb, al = caption_layer(lines); hh = al.shape[0]
    f[y0:y0 + hh] = f[y0:y0 + hh] * (1 - al[..., None]) + rgb
    return f
