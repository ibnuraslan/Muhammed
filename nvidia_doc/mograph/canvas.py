"""Thin Skia wrapper: antialiased vector drawing, tracked type, glows, draw-on paths, compositing to numpy."""
import math
import numpy as np
import skia
from style import W, H, F, TEXT, TRACK_LABEL

_tf = {}


def typeface(key):
    if key not in _tf:
        _tf[key] = skia.Typeface.MakeFromFile(F.get(key, key))
    return _tf[key]


def font(key, size):
    f = skia.Font(typeface(key), size)
    f.setSubpixel(True); f.setEdging(skia.Font.Edging.kSubpixelAntiAlias)
    return f


def col(rgb, a=1.0):
    return skia.Color4f(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, max(0.0, min(1.0, a)))


class Frame:
    def __init__(self, w=W, h=H, bg=None):
        self.w, self.h = w, h
        self.surf = skia.Surface(w, h)
        self.c = self.surf.getCanvas()
        if bg is None:
            self.c.clear(skia.Color4f(0, 0, 0, 0))
        else:
            self.c.clear(col(bg))

    # ------------------------------------------------------------ paints
    @staticmethod
    def paint(rgb, a=1.0, stroke=None, blur=0.0, cap="round", dash=None, join="round"):
        p = skia.Paint(AntiAlias=True)
        p.setColor4f(col(rgb, a))
        if stroke is not None:
            p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
            p.setStrokeCap({"round": skia.Paint.kRound_Cap, "butt": skia.Paint.kButt_Cap, "square": skia.Paint.kSquare_Cap}[cap])
            p.setStrokeJoin({"round": skia.Paint.kRound_Join, "miter": skia.Paint.kMiter_Join}[join])
        if dash:
            p.setPathEffect(skia.DashPathEffect.Make(list(dash), 0))
        if blur > 0:
            p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
        return p

    # ------------------------------------------------------------ primitives (each optionally glowing)
    def line(self, a, b, rgb, w=2, a_=1.0, glow=0, dash=None, cap="round"):
        if glow:
            self.c.drawLine(*a, *b, self.paint(rgb, a_ * 0.55, stroke=w * 3, blur=glow, cap=cap))
        self.c.drawLine(*a, *b, self.paint(rgb, a_, stroke=w, dash=dash, cap=cap))

    def rect(self, x, y, w, h, rgb, a=1.0, stroke=None, r=0, blur=0):
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)
        self.c.drawRRect(rr, self.paint(rgb, a, stroke=stroke, blur=blur))

    def circle(self, x, y, r, rgb, a=1.0, stroke=None, glow=0):
        if glow:
            self.c.drawCircle(x, y, r * 1.6, self.paint(rgb, a * 0.5, blur=glow))
        self.c.drawCircle(x, y, r, self.paint(rgb, a, stroke=stroke))

    def path(self, pts, rgb, w=2, a=1.0, glow=0, dash=None, closed=False, fill=False, progress=1.0):
        """Polyline; `progress` (0..1) draws it on from the start (for animated trails)."""
        if len(pts) < 2 or progress <= 0:
            return None
        P = skia.Path(); P.moveTo(*pts[0])
        for q in pts[1:]:
            P.lineTo(*q)
        if closed:
            P.close()
        if progress < 1.0:
            meas = skia.PathMeasure(P, False); L = meas.getLength()
            seg = skia.Path(); meas.getSegment(0, L * progress, seg, True); P = seg
        if fill:
            self.c.drawPath(P, self.paint(rgb, a))
            return P
        if glow:
            self.c.drawPath(P, self.paint(rgb, a * 0.5, stroke=w * 3.5, blur=glow))
        self.c.drawPath(P, self.paint(rgb, a, stroke=w, dash=dash))
        return P

    def poly_fill(self, pts, rgb, a=1.0):
        self.path(pts, rgb, a=a, closed=True, fill=True)

    # ------------------------------------------------------------ type
    def text_width(self, s, fkey, size, track=0.0):
        f = font(fkey, size)
        if not track:
            return f.measureText(s)
        return sum(f.measureText(ch) for ch in s) + track * size * max(len(s) - 1, 0)

    def text(self, s, x, y, fkey, size, rgb=TEXT, a=1.0, track=0.0, anchor="l", glow=0, reveal=1.0):
        """Baseline at y. anchor l/c/r. `reveal` types the string on (0..1, character count)."""
        if a <= 0.003 or not s:
            return 0
        f = font(fkey, size)
        total = self.text_width(s, fkey, size, track)
        x0 = x - (total / 2 if anchor == "c" else total if anchor == "r" else 0)
        n = int(math.ceil(len(s) * max(0.0, min(1.0, reveal))))
        s_vis = s[:n]
        p = self.paint(rgb, a)
        if glow:
            g = self.paint(rgb, a * 0.6, blur=glow)
        if not track:
            if glow:
                self.c.drawString(s_vis, x0, y, f, g)
            self.c.drawString(s_vis, x0, y, f, p)
        else:
            xx = x0
            for ch in s_vis:
                if glow:
                    self.c.drawString(ch, xx, y, f, g)
                self.c.drawString(ch, xx, y, f, p)
                xx += f.measureText(ch) + track * size
        return total

    def label(self, s, x, y, size=22, rgb=TEXT, a=1.0, anchor="l", fkey="sans_sb", track=TRACK_LABEL, reveal=1.0):
        return self.text(s.upper(), x, y, fkey, size, rgb, a, track=track, anchor=anchor, reveal=reveal)

    def wrap(self, s, fkey, size, max_w):
        words, lines, cur = s.split(), [], ""
        for w_ in words:
            t = (cur + " " + w_).strip()
            if self.text_width(t, fkey, size) > max_w and cur:
                lines.append(cur); cur = w_
            else:
                cur = t
        if cur:
            lines.append(cur)
        return lines

    # ------------------------------------------------------------ output
    def rgba(self):
        """Premultiplied RGBA float32 (0..1)."""
        a = self.surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
        return a.astype(np.float32) / 255.0


def over(base_rgb, layer_rgba, opacity=1.0):
    """Composite a premultiplied RGBA layer over an RGB float image."""
    a = layer_rgba[..., 3:4] * opacity
    return base_rgb * (1 - a) + layer_rgba[..., :3] * opacity


def solid(rgb):
    return np.ones((H, W, 3), np.float32) * (np.array(rgb, np.float32) / 255.0)


_noise_cache = {}


def paper_texture(seed=0, scale=1.0):
    """Subtle fibrous paper luminance field for documents."""
    key = (seed, scale)
    if key not in _noise_cache:
        r = np.random.default_rng(seed)
        n = r.normal(0, 1, (H // 4, W // 4)).astype(np.float32)
        from scipy.ndimage import gaussian_filter, zoom
        n = gaussian_filter(n, 1.2) * 0.6 + gaussian_filter(n, 6) * 1.4
        n = zoom(n, 4, order=1)[:H, :W]
        _noise_cache[key] = (n - n.mean()) / (n.std() + 1e-6)
    return _noise_cache[key]
