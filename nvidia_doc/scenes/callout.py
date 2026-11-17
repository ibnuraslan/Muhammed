"""Shared real-photo callouts + caption style (all films). The user's chosen format (Nov 17):

  PEOPLE, first appearance only -> person_right(): lower-right third, right-aligned.
      B&W real photo, thick white border (10 px at 1080p), square-ish, ~15% of frame height;
      under it the NAME in a typewriter face (Special Elite), white, uppercase, large;
      under that the ROLE, smaller, bold typewriter (Courier Prime Bold), uppercase. Soft shadow. No arrow.
  PLACES, first appearance -> place_left(): the same card on the LEFT, left-aligned: PLACE / year or region.
  CAPTIONS -> caption(): burned-in "mystery" style: small Courier-like (Courier Prime), white, soft shadow,
      one line, centred, baseline ~6% above the bottom edge, ~2.2% of frame height. Exact script text, timed to the VO
      (see caption_burnin.py, which reads an SRT).
Calm: cards fade (0.4 s), never slide or bounce. Sizes scale with the frame height, so 1920x816, 1920x1080 and 4K
all match.

  python scenes/callout.py person <in.png> <photo.jpg> <out.png> --name "PHILIP PETERS" --role "RETIRED RAILROAD MAN" \
         [--caption "On October seventeenth, 1941, Philip Peters is seventy-three years old."] [--crop 0.75,0.42,0.64]
  python scenes/callout.py place  <in.png> <photo.jpg> <out.png> --name "DENVER, COLORADO" --role "1941" [--caption ...]
  python scenes/callout.py anim-person <frames_dir|video> <photo.jpg> <out.mp4> --name .. --role .. [--dur 4] [--fps 24]
      (card fades in over 0.4 s, holds, fades out over 0.4 s)
"""
import os, sys, glob, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fonts")
NAME_FONT = os.path.join(FONTS, "SpecialElite-Regular.ttf")      # Apache 2.0
ROLE_FONT = os.path.join(FONTS, "CourierPrime-Bold.ttf")         # OFL
CAP_FONT = os.path.join(FONTS, "CourierPrime-Regular.ttf")       # OFL

# style constants, as fractions of the frame height (Hf) / width (Wf)
PHOTO_H = 0.15          # photo height (inside the border)
PHOTO_AR = 0.92         # width / height: square-ish, a touch taller than wide (a portrait print)
BORDER = 10 / 1080      # white border
NAME_SIZE = 0.040       # name cap size
ROLE_SIZE = 0.024
GAP = 0.014             # photo -> name, name -> role
MARGIN_X = 0.055        # of frame width, from the side edge
BLOCK_BOTTOM = 0.80     # the card block ends here (fraction of Hf from the top): lower third, clear of captions
CAP_SIZE = 0.022
CAP_BASE = 0.06         # caption baseline above the bottom edge
WHITE = (255, 255, 255)


def _font(p, px):
    return ImageFont.truetype(p, max(8, int(round(px))))


def bw_photo(path, size, crop=None):
    """B&W print of the real photo, cropped to size. crop=(cx, cy, zoom) in 0..1 of the source (zoom = crop height)."""
    im = Image.open(path).convert("L")
    w, h = im.size; tw, th = size; ar = tw / th
    cx, cy, z = crop or (0.5, 0.5, 1.0)
    ch = min(h, int(h * z)); cw = int(ch * ar)
    if cw > w:
        cw = w; ch = int(cw / ar)
    x0 = int(min(max(0, cx * w - cw / 2), w - cw)); y0 = int(min(max(0, cy * h - ch / 2), h - ch))
    im = im.crop((x0, y0, x0 + cw, y0 + ch)).resize(size, Image.LANCZOS)
    im = ImageOps.autocontrast(im, cutoff=0.8)
    return im.convert("RGB")


def _soft_shadow(layer, radius, alpha, offset):
    a = layer.split()[-1].point(lambda v: v * alpha // 255)
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0)); sh.putalpha(a)
    sh = sh.filter(ImageFilter.GaussianBlur(radius))
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0)); out.alpha_composite(sh, (int(offset[0]), int(offset[1])))
    return out


def _card_layer(Wf, Hf, photo_path, name, role, side, crop=None):
    """The whole callout (photo + border + name + role, with soft shadows) as a transparent full-frame layer."""
    ph = int(round(PHOTO_H * Hf)); pw = int(round(ph * PHOTO_AR)); b = max(5, int(round(BORDER * Hf)))
    fn = _font(NAME_FONT, NAME_SIZE * Hf * 1.25); fr = _font(ROLE_FONT, ROLE_SIZE * Hf * 1.25)
    name, role = name.upper(), (role or "").upper()
    lay = Image.new("RGBA", (Wf, Hf), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    nb = d.textbbox((0, 0), name, font=fn); rb = d.textbbox((0, 0), role, font=fr) if role else (0, 0, 0, 0)
    nh, rh = nb[3] - nb[1], rb[3] - rb[1]
    gap = GAP * Hf
    total = ph + 2 * b + gap + nh + (gap * 0.7 + rh if role else 0)
    y0 = BLOCK_BOTTOM * Hf - total
    mx = MARGIN_X * Wf
    # photo with its white border
    card = Image.new("RGB", (pw + 2 * b, ph + 2 * b), WHITE); card.paste(bw_photo(photo_path, (pw, ph), crop), (b, b))
    cx = int(Wf - mx - card.width) if side == "right" else int(mx)
    lay.paste(card, (cx, int(y0)))
    # text, right-aligned (people) / left-aligned (places) to the card edge
    ty = y0 + card.height + gap - nb[1]
    if side == "right":
        d.text((Wf - mx - (nb[2] - nb[0]) - nb[0], ty), name, font=fn, fill=WHITE + (255,))
    else:
        d.text((mx - nb[0], ty), name, font=fn, fill=WHITE + (255,))
    if role:
        ry = y0 + card.height + gap + nh + gap * 0.7 - rb[1]
        rx = (Wf - mx - (rb[2] - rb[0]) - rb[0]) if side == "right" else (mx - rb[0])
        d.text((rx, ry), role, font=fr, fill=(240, 238, 232, 255))
    sh = _soft_shadow(lay, radius=0.008 * Hf, alpha=170, offset=(0.002 * Hf, 0.003 * Hf))
    return Image.alpha_composite(sh, lay)


def _apply(img, layer, alpha):
    base = img.convert("RGBA")
    if alpha < 1.0:
        layer = layer.copy(); layer.putalpha(layer.split()[-1].point(lambda v: int(v * max(0.0, alpha))))
    return Image.alpha_composite(base, layer).convert("RGB")


def person_right(img, photo_path, name, role, alpha=1.0, crop=None, _cache={}):
    """A real person's first appearance: photo card lower-right, NAME / ROLE right-aligned."""
    k = ("p", img.size, photo_path, name, role, crop)
    if k not in _cache:
        _cache[k] = _card_layer(img.size[0], img.size[1], photo_path, name, role, "right", crop)
    return _apply(img, _cache[k], alpha)


def place_left(img, photo_path, place, line2, alpha=1.0, crop=None, _cache={}):
    """A place's first appearance: the same card lower-left, PLACE / year-or-region left-aligned."""
    k = ("l", img.size, photo_path, place, line2, crop)
    if k not in _cache:
        _cache[k] = _card_layer(img.size[0], img.size[1], photo_path, place, line2, "left", crop)
    return _apply(img, _cache[k], alpha)


def caption_layer(Wf, Hf, text):
    f = _font(CAP_FONT, CAP_SIZE * Hf * 1.3)
    lay = Image.new("RGBA", (Wf, Hf), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    bb = d.textbbox((0, 0), text, font=f, anchor="ls")
    x = (Wf - (bb[2] - bb[0])) / 2 - bb[0]; y = Hf * (1 - CAP_BASE)
    d.text((x, y), text, font=f, fill=WHITE + (255,), anchor="ls")
    sh = _soft_shadow(lay, radius=max(1.5, 0.0035 * Hf), alpha=230, offset=(0.0012 * Hf, 0.0018 * Hf))
    return Image.alpha_composite(sh, lay)


def caption(img, text, alpha=1.0, _cache={}):
    """Burned-in caption, one line, centred near the bottom (the user's 'mystery' style)."""
    if not text:
        return img
    k = (img.size, text)
    if k not in _cache:
        _cache[k] = caption_layer(img.size[0], img.size[1], text)
    return _apply(img, _cache[k], alpha)


def card_alpha(sec, dur, fade=0.4):
    """Fade in over 0.4 s, hold, fade out over 0.4 s (smoothstep, no slide or bounce)."""
    a = min(1.0, sec / fade, max(0.0, (dur - sec) / fade))
    a = max(0.0, a)
    return a * a * (3 - 2 * a)


def _frames_from(src, fps, dur):
    if os.path.isdir(src):
        return [Image.open(f).convert("RGB") for f in sorted(glob.glob(os.path.join(src, "*.png")))]
    out = os.path.join(os.path.dirname(os.path.abspath(src)), "_callout_src"); os.makedirs(out, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-t", str(dur), "-vf", f"fps={fps}", os.path.join(out, "f%04d.png")], check=True)
    return [Image.open(f).convert("RGB") for f in sorted(glob.glob(os.path.join(out, "f*.png")))]


if __name__ == "__main__":
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    mode = a[0]
    crop = tuple(float(v) for v in opt("--crop").split(",")) if opt("--crop") else None
    name, role, cap = opt("--name", ""), opt("--role", ""), opt("--caption", "")
    if mode in ("person", "place"):
        src, photo, out = a[1:4]
        im = Image.open(src).convert("RGB")
        if opt("--size"):
            im = im.resize(tuple(int(v) for v in opt("--size").split("x")), Image.LANCZOS)
        im = (person_right if mode == "person" else place_left)(im, photo, name, role, crop=crop)
        im = caption(im, cap)
        im.save(out); print("[callout]", out, im.size)
    elif mode in ("anim-person", "anim-place"):
        src, photo, out = a[1:4]
        fps = int(opt("--fps", 24)); dur = float(opt("--dur", 4.0))
        frames = _frames_from(src, fps, dur)
        size = tuple(int(v) for v in opt("--size").split("x")) if opt("--size") else frames[0].size
        fn = person_right if mode == "anim-person" else place_left
        tmp = out + "_frames"; os.makedirs(tmp, exist_ok=True)
        n = int(round(dur * fps))
        for i in range(n):
            im = frames[min(i, len(frames) - 1)].resize(size, Image.LANCZOS)
            im = fn(im, photo, name, role, alpha=card_alpha(i / fps, dur), crop=crop)
            im = caption(im, cap)
            im.save(os.path.join(tmp, f"c{i:04d}.png"))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-i", os.path.join(tmp, "c%04d.png"), "-c:v", "libx264",
                        "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], check=True)
        print("[callout] mp4", out, n, "frames")
