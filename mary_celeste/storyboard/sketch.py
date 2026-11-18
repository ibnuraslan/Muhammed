"""Blockout frame sketches for the Mary Celeste storyboard.

Pure-PIL pinhole 'blockout' renderer: grey boxes, hulls, figures and props
projected through a simple camera, then toned per lighting mood.
These are planning frames only, not final renders.
"""
import math, random
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageFont

W, H = 1920, 1080
OUT_W = 960
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

MOODS = {
    # black, mid, white  (tritone grade = lighting / time of day)
    "noon":   ((16, 22, 27), (96, 110, 117), (222, 229, 231)),
    "dawn":   ((28, 18, 16), (152, 104, 68), (255, 222, 172)),
    "storm":  ((6, 10, 16), (52, 63, 76), (168, 183, 194)),
    "cold":   ((12, 16, 20), (78, 90, 97), (204, 214, 217)),
    "warm":   ((20, 12, 7), (130, 86, 48), (252, 226, 180)),
    "nyday":  ((24, 21, 19), (122, 113, 100), (236, 229, 212)),
    "court":  ((19, 13, 9), (116, 84, 58), (242, 221, 190)),
    "under":  ((2, 13, 19), (28, 78, 88), (150, 210, 208)),
    "lab":    ((19, 19, 17), (110, 108, 96), (236, 233, 216)),
    "modern": ((13, 15, 19), (88, 94, 104), (226, 226, 231)),
    "home":   ((22, 15, 10), (126, 94, 68), (242, 226, 205)),
    "legend": ((40, 26, 12), (152, 110, 60), (246, 226, 180)),
    "spec":   ((28, 28, 30), (108, 108, 110), (198, 198, 198)),
    "gib":    ((22, 20, 22), (126, 118, 112), (238, 230, 220)),
    "genoa":  ((28, 22, 18), (142, 118, 94), (246, 232, 210)),
    "maq":    ((40, 38, 36), (160, 156, 150), (250, 248, 244)),
    "dusk":   ((14, 12, 22), (98, 80, 92), (226, 180, 150)),
    "black":  ((0, 0, 0), (20, 20, 20), (60, 60, 60)),
}


def P(x, y):
    return (int(x * W), int(y * H))


class Cam:
    """Pinhole camera. World metres: X right, Y up, Z forward."""

    def __init__(self, hz=0.42, camH=1.6, camX=0.0, f=0.35, cx=0.5):
        self.hz, self.camH, self.camX, self.f, self.cx = hz, camH, camX, f, cx

    def p(self, X, Y, Z):
        Z = max(Z, 0.05)
        fy = self.f * 16 / 9
        return (int((self.cx + (X - self.camX) * self.f / Z) * W),
                int((self.hz + (self.camH - Y) * fy / Z) * H))

    def scale(self, Z):  # pixels per metre (vertical) at depth Z
        return self.f * 16 / 9 / max(Z, 0.05) * H


class Canvas:
    def __init__(self, mood="noon", seed=1):
        self.img = Image.new("L", (W, H), 128)
        self.d = ImageDraw.Draw(self.img)
        self.mood = mood
        self.rng = random.Random(seed)
        self.overlays = []  # functions drawn after toning (RGB)

    # ---------- primitives ----------
    def grad(self, box, top, bot):
        x0, y0, x1, y1 = [int(v) for v in box]
        y0, y1 = max(y0, 0), min(y1, H)
        for y in range(y0, y1):
            t = (y - y0) / max(1, (y1 - y0))
            self.d.line([(x0, y), (x1, y)], fill=int(top + (bot - top) * t))

    def poly(self, pts, fill, outline=None, w=1):
        self.d.polygon([tuple(map(int, p)) for p in pts], fill=fill, outline=outline)
        if outline is not None and w > 1:
            self.d.line([tuple(map(int, p)) for p in pts] + [tuple(map(int, pts[0]))], fill=outline, width=w)

    def line(self, pts, fill, w=3):
        self.d.line([tuple(map(int, p)) for p in pts], fill=fill, width=int(w))

    def ell(self, cx, cy, rx, ry, fill, outline=None, w=1):
        self.d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill, outline=outline, width=w)

    def blur_layer(self, draw_fn, radius=12):
        """Draw something on its own layer (with mask) and blur it: soft foreground / DOF."""
        layer = Image.new("L", (W, H), 0)
        mask = Image.new("L", (W, H), 0)
        draw_fn(ImageDraw.Draw(layer), ImageDraw.Draw(mask))
        layer = layer.filter(ImageFilter.GaussianBlur(radius))
        mask = mask.filter(ImageFilter.GaussianBlur(radius))
        self.img.paste(layer, (0, 0), mask)
        self.d = ImageDraw.Draw(self.img)

    def blur_all(self, radius):
        self.img = self.img.filter(ImageFilter.GaussianBlur(radius))
        self.d = ImageDraw.Draw(self.img)

    def light_shaft(self, top_pts, bot_pts, strength=60):
        layer = Image.new("L", (W, H), 0)
        ImageDraw.Draw(layer).polygon([tuple(map(int, p)) for p in top_pts + bot_pts[::-1]], fill=strength)
        layer = layer.filter(ImageFilter.GaussianBlur(40))
        self.img = Image.composite(Image.new("L", (W, H), 255), self.img, layer)
        self.d = ImageDraw.Draw(self.img)

    def vignette(self, k=0.55):
        v = Image.new("L", (W, H), 0)
        ImageDraw.Draw(v).ellipse([-W * 0.15, -H * 0.2, W * 1.15, H * 1.2], fill=255)
        v = v.filter(ImageFilter.GaussianBlur(160))
        dark = self.img.point(lambda p: int(p * (1 - k)))
        self.img = Image.composite(self.img, dark, v)
        self.d = ImageDraw.Draw(self.img)

    # ---------- 3D box ----------
    def box(self, cam, x0, x1, y0, y1, z0, z1, front=110, side=80, top=150, outline=None):
        c = {}
        for X in (x0, x1):
            for Y in (y0, y1):
                for Z in (z0, z1):
                    c[(X, Y, Z)] = cam.p(X, Y, Z)
        faces = []
        if cam.camH > y1:
            faces.append(([c[(x0, y1, z0)], c[(x1, y1, z0)], c[(x1, y1, z1)], c[(x0, y1, z1)]], top))
        if cam.camH < y0:
            faces.append(([c[(x0, y0, z0)], c[(x1, y0, z0)], c[(x1, y0, z1)], c[(x0, y0, z1)]], int(side * 0.8)))
        if cam.camX < x0:
            faces.append(([c[(x0, y0, z0)], c[(x0, y1, z0)], c[(x0, y1, z1)], c[(x0, y0, z1)]], side))
        if cam.camX > x1:
            faces.append(([c[(x1, y0, z0)], c[(x1, y1, z0)], c[(x1, y1, z1)], c[(x1, y0, z1)]], side))
        for pts, t in faces:
            self.poly(pts, t, outline)
        self.poly([c[(x0, y0, z0)], c[(x1, y0, z0)], c[(x1, y1, z0)], c[(x0, y1, z0)]], front, outline)

    def plane_floor(self, cam, x0, x1, z0, z1, y, near, far):
        steps = 30
        for i in range(steps):
            za = z0 + (z1 - z0) * i / steps
            zb = z0 + (z1 - z0) * (i + 1) / steps
            t = i / steps
            self.poly([cam.p(x0, y, za), cam.p(x1, y, za), cam.p(x1, y, zb), cam.p(x0, y, zb)],
                      int(near + (far - near) * t))

    # ---------- people ----------
    def fig(self, x, yf, h, view="front", pose="stand", tone=34, hat=None, arms=None,
            female=False, child=False, face_tone=None, beard=False):
        """Full figure, normalized x/yfeet (0..1), h = height as fraction of frame height."""
        X, Yf, Hh = x * W, yf * H, h * H
        r = Hh * (0.075 if child else 0.062)
        if pose == "sit":
            hip_y = Yf - Hh * 0.30
            sh_y = hip_y - Hh * 0.36
        elif pose == "kneel":
            hip_y = Yf - Hh * 0.30
            sh_y = hip_y - Hh * 0.36
        elif pose == "bend":
            hip_y = Yf - Hh * 0.50
            sh_y = hip_y - Hh * 0.22
        else:
            hip_y = Yf - Hh * 0.50
            sh_y = Yf - Hh * 0.82
        sw = Hh * (0.13 if not child else 0.11)
        hw = Hh * 0.09
        lean = Hh * 0.12 if pose == "bend" else 0
        dirx = -1 if view in ("left", "3q_l") else 1
        hx = X + lean * dirx
        head_y = sh_y - r * 1.55
        lw = max(4, Hh * 0.055)
        # legs
        if pose == "stand" or pose == "bend":
            if female:
                self.poly([(X - hw * 0.9, hip_y - Hh * 0.05), (X + hw * 0.9, hip_y - Hh * 0.05),
                           (X + hw * 1.9, Yf), (X - hw * 1.9, Yf)], tone)
            else:
                self.line([(X - hw * 0.5, hip_y), (X - hw * 0.6, Yf)], tone, lw * 1.1)
                self.line([(X + hw * 0.5, hip_y), (X + hw * 0.6, Yf)], tone, lw * 1.1)
        elif pose == "sit":
            self.line([(X, hip_y), (X + dirx * Hh * 0.22, hip_y), (X + dirx * Hh * 0.24, Yf)], tone, lw * 1.1)
            if female:
                self.poly([(X - hw, hip_y - Hh * 0.08), (X + hw, hip_y - Hh * 0.08),
                           (X + dirx * Hh * 0.3, Yf), (X - hw * 1.4, Yf)], tone)
        elif pose == "kneel":
            self.line([(X, hip_y), (X + dirx * Hh * 0.05, Yf - Hh * 0.02), (X - dirx * Hh * 0.18, Yf)], tone, lw * 1.1)
            self.line([(X, hip_y), (X + dirx * Hh * 0.2, hip_y + Hh * 0.04), (X + dirx * Hh * 0.2, Yf)], tone, lw * 1.1)
        # torso
        self.poly([(hx - sw, sh_y), (hx + sw, sh_y), (X + hw, hip_y), (X - hw, hip_y)], tone)
        self.ell(hx - sw * 0.9, sh_y + lw * 0.3, lw * 0.6, lw * 0.6, tone)
        self.ell(hx + sw * 0.9, sh_y + lw * 0.3, lw * 0.6, lw * 0.6, tone)
        # arms: list of (side, hand_dx, hand_dy) in units of h relative to shoulder
        arms = arms if arms is not None else [(-1, -0.03, 0.34), (1, 0.03, 0.34)]
        for side, dx, dy in arms:
            sx = hx + side * sw * 0.95
            ex, ey = sx + dx * Hh * 0.5 + side * Hh * 0.02, sh_y + dy * Hh * 0.5
            hxp, hyp = sx + dx * Hh, sh_y + dy * Hh
            self.line([(sx, sh_y + lw * 0.3), (ex, ey), (hxp, hyp)], tone, lw * 0.85)
            self.ell(hxp, hyp, lw * 0.55, lw * 0.55, tone)
        # neck + head
        self.line([(hx, sh_y), (hx, head_y)], tone, lw * 0.9)
        self.ell(hx, head_y, r * 0.85, r, tone)
        if view in ("front", "3q_l", "3q_r", "left", "right"):
            ft = face_tone if face_tone is not None else min(255, tone + 60)
            off = {"front": 0, "3q_l": -0.3, "3q_r": 0.3, "left": -0.55, "right": 0.55}[view]
            self.ell(hx + off * r, head_y + r * 0.1, r * 0.55, r * 0.75, ft)
        if female:
            self.ell(hx - dirx * r * 0.7, head_y - r * 0.2, r * 0.45, r * 0.45, tone)
        if hat == "cap":
            self.poly([(hx - r * 0.95, head_y - r * 0.45), (hx + r * 0.95, head_y - r * 0.45),
                       (hx + r * 0.8, head_y - r * 1.05), (hx - r * 0.8, head_y - r * 1.05)], max(0, tone - 12))
            self.line([(hx - r * 1.1, head_y - r * 0.45), (hx + r * 1.25 * dirx, head_y - r * 0.4)], max(0, tone - 12), r * 0.2)
        elif hat == "top":
            self.poly([(hx - r * 0.75, head_y - r * 0.6), (hx + r * 0.75, head_y - r * 0.6),
                       (hx + r * 0.7, head_y - r * 2.1), (hx - r * 0.7, head_y - r * 2.1)], max(0, tone - 15))
            self.line([(hx - r * 1.2, head_y - r * 0.6), (hx + r * 1.2, head_y - r * 0.6)], max(0, tone - 15), r * 0.18)
        elif hat == "bonnet":
            self.d.chord([hx - r * 1.4, head_y - r * 1.5, hx + r * 1.4, head_y + r * 0.9], 180, 360, fill=min(255, tone + 25))
        elif hat == "helmet":
            self.ell(hx, head_y, r * 1.7, r * 1.7, min(255, tone + 40))
            self.ell(hx + r * 0.3, head_y, r * 0.75, r * 0.75, max(0, tone - 20))
        elif hat == "wig":
            self.ell(hx, head_y - r * 0.2, r * 1.15, r * 1.0, 200)
            self.ell(hx + r * 0.2, head_y + r * 0.15, r * 0.55, r * 0.7, min(255, tone + 60))

    def bust(self, cx, cy, s, view="3q_l", tone=40, light="l", hat=None, female=False,
             child=False, look=0.0, expr="neutral", blur=0, beard=False):
        """Chest-up portrait. s = head height (fraction of H). cx,cy = head centre."""
        def draw(d, m=None):
            X, Y, S = cx * W, cy * H, s * H
            rx, ry = S * 0.40, S * 0.5
            shw = S * (1.25 if not child else 0.9)
            shy = Y + S * 0.95
            for dd, fillv in ((d, tone), (m, 255)):
                if dd is None:
                    continue
                dd.polygon([(X - shw, shy + S * 0.25), (X - shw * 0.55, shy - S * 0.05), (X + shw * 0.55, shy - S * 0.05),
                            (X + shw, shy + S * 0.25), (X + shw * 1.2, H + 50), (X - shw * 1.2, H + 50)], fill=fillv)
                dd.rectangle([X - S * 0.17, Y + S * 0.3, X + S * 0.17, shy + 5], fill=fillv)
                dd.ellipse([X - rx, Y - ry, X + rx, Y + ry], fill=fillv)
                if hat == "cap":
                    dd.polygon([(X - rx * 1.05, Y - ry * 0.45), (X + rx * 1.05, Y - ry * 0.45),
                                (X + rx * 0.9, Y - ry * 1.15), (X - rx * 0.9, Y - ry * 1.15)], fill=max(0, fillv - 12) if dd is d else 255)
                elif hat == "top":
                    dd.polygon([(X - rx * 0.85, Y - ry * 0.6), (X + rx * 0.85, Y - ry * 0.6),
                                (X + rx * 0.8, Y - ry * 2.1), (X - rx * 0.8, Y - ry * 2.1)], fill=max(0, fillv - 12) if dd is d else 255)
                    dd.rectangle([X - rx * 1.35, Y - ry * 0.68, X + rx * 1.35, Y - ry * 0.55], fill=max(0, fillv - 12) if dd is d else 255)
                elif hat == "bonnet":
                    dd.chord([X - rx * 1.6, Y - ry * 1.5, X + rx * 1.6, Y + ry * 0.9], 180, 360, fill=min(255, fillv + 30) if dd is d else 255)
                elif hat == "wig":
                    dd.ellipse([X - rx * 1.3, Y - ry * 1.2, X + rx * 1.3, Y + ry * 0.9], fill=200 if dd is d else 255)
                if female and hat != "bonnet":
                    bx = X + (rx * 0.9 if view in ("3q_l", "left") else -rx * 0.9)
                    dd.ellipse([bx - rx * 0.45, Y - ry * 0.75, bx + rx * 0.45, Y - ry * 0.05], fill=fillv)
            # face plane lit side
            off = {"front": 0, "3q_l": -0.28, "3q_r": 0.28, "left": -0.5, "right": 0.5, "back": None}[view]
            if off is None:
                return
            fx = X + off * rx + look * rx * 0.3
            lt = min(255, tone + 95)
            d.ellipse([fx - rx * 0.7, Y - ry * 0.75, fx + rx * 0.7, Y + ry * 0.92], fill=min(255, tone + 45))
            if light == "l":
                d.chord([fx - rx * 0.7, Y - ry * 0.75, fx + rx * 0.7, Y + ry * 0.92], 90, 270, fill=lt)
            elif light == "r":
                d.chord([fx - rx * 0.7, Y - ry * 0.75, fx + rx * 0.7, Y + ry * 0.92], 270, 90, fill=lt)
            else:
                d.ellipse([fx - rx * 0.6, Y - ry * 0.65, fx + rx * 0.6, Y + ry * 0.85], fill=lt)
            ey = Y - ry * 0.08
            brow = {"neutral": 0, "worry": -0.06, "frown": 0.05, "wide": -0.12, "tired": 0.03}[expr]
            for ex in (fx - rx * 0.3, fx + rx * 0.3):
                d.ellipse([ex - rx * 0.11, ey - ry * 0.05, ex + rx * 0.11, ey + ry * 0.05], fill=tone - 20 if tone > 20 else 0)
                d.line([(ex - rx * 0.16, ey - ry * (0.15 - brow)), (ex + rx * 0.16, ey - ry * (0.15 + brow * (1 if ex > fx else -1)))],
                       fill=max(0, tone - 10), width=max(2, int(S * 0.025)))
            d.line([(fx, ey + ry * 0.05), (fx + rx * 0.05, Y + ry * 0.35)], fill=max(0, tone + 10), width=max(2, int(S * 0.02)))
            mw = rx * (0.22 if expr != "wide" else 0.15)
            d.line([(fx - mw, Y + ry * 0.55), (fx + mw, Y + ry * 0.55)], fill=max(0, tone), width=max(2, int(S * 0.02)))
            if beard:
                d.chord([fx - rx * 0.72, Y + ry * 0.2, fx + rx * 0.72, Y + ry * 1.05], 0, 180, fill=max(0, tone - 5))
        if blur:
            self.blur_layer(lambda l, m: draw(l, m), blur)
        else:
            draw(self.d)

    def ots(self, side="l", tone=22, s=0.62, blur=18, hat=None, female=False, arm_to=None, hand_tone=None):
        """Over-the-shoulder foreground head+shoulder, soft focus; optional arm reaching to arm_to (x,y)."""
        cx = 0.12 if side == "l" else 0.88
        def draw(l, m):
            X, Y, S = cx * W, 0.42 * H, s * H
            for dd, f in ((l, tone), (m, 255)):
                dd.ellipse([X - S * 0.38, Y - S * 0.5, X + S * 0.38, Y + S * 0.5], fill=f)
                dd.polygon([(X - S * 1.3, H + 40), (X - S * 0.9, Y + S * 0.85), (X + S * 0.9, Y + S * 0.85), (X + S * 1.3, H + 40)], fill=f)
                dd.rectangle([X - S * 0.18, Y + S * 0.3, X + S * 0.18, Y + S * 0.95], fill=f)
                if hat == "cap":
                    dd.polygon([(X - S * 0.42, Y - S * 0.2), (X + S * 0.42, Y - S * 0.2), (X + S * 0.36, Y - S * 0.58), (X - S * 0.36, Y - S * 0.58)], fill=f)
                if female:
                    dd.ellipse([X - S * 0.2, Y - S * 0.62, X + S * 0.2, Y - S * 0.25], fill=f)
        self.blur_layer(draw, blur)
        if arm_to:
            sx = (cx + (0.16 if side == "l" else -0.16)) * W
            sy = 0.86 * H
            tx, ty = arm_to[0] * W, arm_to[1] * H
            ht = hand_tone if hand_tone is not None else tone + 40
            def arm(l, m):
                for dd, f in ((l, tone + 10), (m, 255)):
                    dd.line([(sx, sy), ((sx + tx) / 2, (sy + ty) / 2 + 40), (tx, ty)], fill=f, width=int(H * 0.075))
                for dd, f in ((l, ht), (m, 255)):
                    dd.ellipse([tx - H * 0.045, ty - H * 0.035, tx + H * 0.045, ty + H * 0.035], fill=f)
            self.blur_layer(arm, 3)

    # ---------- ships ----------
    def ship(self, cx, wy, L, face=1, sails="full", tone=38, sail_tone=205, boat_on_deck=False):
        X, Y, Lp = cx * W, wy * H, L * W
        h = Lp * 0.10
        sx, bx = X - face * Lp / 2, X + face * Lp / 2
        self.poly([(sx, Y - h * 1.05), (X, Y - h * 0.9), (bx, Y - h * 1.35), (bx - face * Lp * 0.07, Y + h * 0.2),
                   (sx + face * Lp * 0.03, Y + h * 0.18)], tone)
        self.line([(sx, Y - h * 0.95), (X, Y - h * 0.8), (bx, Y - h * 1.25)], min(255, tone + 40), max(2, h * 0.06))
        bs_tip = (bx + face * Lp * 0.24, Y - h * 1.9)
        self.line([(bx, Y - h * 1.3), bs_tip], tone, max(2, h * 0.12))
        fm, mm = X + face * Lp * 0.26, X - face * Lp * 0.10
        fh, mh = Lp * 0.95, Lp * 0.9
        mw = max(3, h * 0.12)
        self.line([(fm, Y - h), (fm, Y - fh)], tone, mw)
        self.line([(mm, Y - h), (mm, Y - mh)], tone, mw)
        # rigging
        for p in [(bs_tip, (fm, Y - fh)), ((bx, Y - h * 1.3), (fm, Y - fh * 0.62)), ((fm, Y - fh), (mm, Y - mh * 0.95)),
                  ((sx, Y - h), (mm, Y - mh))]:
            self.line(list(p), tone, max(1, h * 0.03))
        # fore square sails
        levels = [(0.18, 0.40, 0.36), (0.42, 0.60, 0.30), (0.62, 0.76, 0.24), (0.78, 0.88, 0.17)]
        for i, (a, b, wd) in enumerate(levels):
            ya, yb = Y - fh * b, Y - fh * a
            w = Lp * wd / 2
            if sails == "bare":
                self.line([(fm - w, ya), (fm + w, ya)], tone, max(2, h * 0.06))
                continue
            if sails == "torn" and i in (0, 3):
                self.line([(fm - w, ya), (fm + w, ya)], tone, max(2, h * 0.06))
                for k in range(3):
                    rx = fm - w + w * 0.6 * k + self.rng.random() * w * 0.3
                    self.poly([(rx, ya), (rx + w * 0.25, ya), (rx + w * 0.1, ya + (yb - ya) * (0.6 + self.rng.random() * 0.5))], sail_tone - 30)
                continue
            belly = (w * 0.10) * face
            self.poly([(fm - w, ya), (fm + w, ya), (fm + w * 1.05 + belly, yb), (fm - w * 1.05 + belly, yb)], sail_tone)
            self.line([(fm - w, ya), (fm + w, ya)], tone, max(2, h * 0.05))
        # main gaff sail
        if sails != "bare":
            gaff_end = (mm - face * Lp * 0.40, Y - mh * 0.70)
            boom_end = (mm - face * Lp * 0.46, Y - h * 1.9)
            if sails == "torn":
                self.poly([(mm, Y - h * 2.0), (mm, Y - mh * 0.8), (gaff_end[0] * 0.5 + mm * 0.5, Y - mh * 0.75),
                           (mm - face * Lp * 0.15, Y - h * 2.4)], sail_tone - 15)
                self.line([(mm, Y - mh * 0.8), gaff_end], tone, mw * 0.7)
                self.line([gaff_end, (gaff_end[0] + face * 10, Y - mh * 0.35)], sail_tone - 40, max(2, h * 0.04))
            else:
                self.poly([(mm, Y - h * 2.0), (mm, Y - mh * 0.8), gaff_end, boom_end], sail_tone - 10)
            self.line([(mm, Y - h * 2.0), boom_end], tone, mw * 0.7)
            # jibs
            if sails == "full" or sails == "spare":
                self.poly([bs_tip, (fm, Y - fh * 0.62), (fm + face * Lp * 0.05, Y - h * 1.6)], sail_tone - 5)
                self.poly([(bs_tip[0] - face * Lp * 0.08, bs_tip[1] + h * 0.1), (fm, Y - fh * 0.92), (fm + face * Lp * 0.04, Y - fh * 0.3)], sail_tone - 18)
            else:
                self.poly([bs_tip, (fm, Y - fh * 0.62), (fm + face * Lp * 0.12, Y - fh * 0.3)], sail_tone - 25)
        if boat_on_deck:
            self.ell(X + face * Lp * 0.05, Y - h * 1.15, Lp * 0.07, h * 0.22, min(255, tone + 50))

    def small_boat(self, cx, wy, L, people=2, tone=35, oars=True, face=1):
        X, Y, Lp = cx * W, wy * H, L * W
        h = Lp * 0.16
        self.poly([(X - Lp / 2, Y - h), (X + Lp / 2, Y - h * 1.2), (X + Lp * 0.4, Y + h * 0.3), (X - Lp * 0.42, Y + h * 0.3)], tone)
        for i in range(people):
            px = X - Lp * 0.35 + Lp * 0.7 * (i + 0.5) / people
            self.fig(px / W, (Y - h * 0.6) / H, h * 2.0 / H, view="back", pose="sit", tone=tone - 8 if tone > 8 else 0)
        if oars:
            self.line([(X - Lp * 0.1, Y - h * 1.2), (X - Lp * 0.55, Y + h * 0.9)], tone, max(2, h * 0.12))
            self.line([(X + Lp * 0.1, Y - h * 1.2), (X + Lp * 0.55, Y + h * 0.9)], tone, max(2, h * 0.12))

    # ---------- environments ----------
    def sky_sea(self, hy=0.48, sky=(215, 165), sea=(130, 55), waves=True, fog=0):
        self.grad((0, 0, W, hy * H), sky[1] if False else sky[0], sky[1])
        self.grad((0, hy * H, W, H), sea[0], sea[1])
        if waves:
            for i in range(420):
                t = self.rng.random() ** 1.8
                y = hy * H + t * (1 - hy) * H
                x = self.rng.random() * W
                l = 8 + t * 140
                v = sea[0] + 30 if self.rng.random() < 0.5 else sea[1] - 20
                self.line([(x, y), (x + l, y - l * 0.05)], max(0, min(255, int(v))), max(1, t * 7))
        if fog:
            self.grad((0, (hy - 0.08) * H, W, (hy + 0.05) * H), sky[1], sky[1])

    def clouds(self, n=8, tone=225, y0=0.05, y1=0.35):
        def draw(l, m):
            for i in range(n):
                x = self.rng.random() * W
                y = (y0 + self.rng.random() * (y1 - y0)) * H
                rx = 150 + self.rng.random() * 300
                ry = 30 + self.rng.random() * 60
                l.ellipse([x - rx, y - ry, x + rx, y + ry], fill=tone)
                m.ellipse([x - rx, y - ry, x + rx, y + ry], fill=130)
        self.blur_layer(draw, 40)

    def island(self, cx, hy, wdt=0.25, ht=0.05, tone=95):
        X, Y = cx * W, hy * H
        pts = [(X - wdt * W / 2, Y)]
        n = 12
        for i in range(n + 1):
            t = i / n
            pts.append((X - wdt * W / 2 + t * wdt * W, Y - ht * H * math.sin(math.pi * t) ** 0.7 * (0.7 + 0.3 * self.rng.random())))
        pts.append((X + wdt * W / 2, Y))
        self.poly(pts, tone)

    def rock_gib(self, cx, hy, s=0.5, tone=100):
        X, Y = cx * W, hy * H
        self.poly([(X - s * W * 0.5, Y), (X - s * W * 0.35, Y - s * H * 0.12), (X - s * W * 0.05, Y - s * H * 0.55),
                   (X + s * W * 0.12, Y - s * H * 0.48), (X + s * W * 0.45, Y - s * H * 0.08), (X + s * W * 0.55, Y)], tone)

    def rain(self, n=700, tone=200):
        for i in range(n):
            x, y = self.rng.random() * W, self.rng.random() * H
            self.line([(x, y), (x - 18, y + 60)], tone, 2)

    def deck(self, cam, length=24, half=3.4, bulwark=1.0, gap=None, hatches=(), masts=(8, 16), helm=None,
             boat_chocks=None, sea=True, sails_up=True, plank_tone=(150, 95), wet=False, rail_flat=None):
        hz = cam.hz
        if sea:
            self.sky_sea(hy=hz, sky=(220, 185), sea=(150, 90), waves=False)
        self.plane_floor(cam, -half, half, 0.6, length, 0, plank_tone[0], plank_tone[1])
        for k in range(-6, 7):
            X = k * half / 6.5
            self.line([cam.p(X, 0, 0.6), cam.p(X, 0, length)], plank_tone[1] - 25, 2)
        for side in (-1, 1):
            X = side * half
            segs = [(0.6, length)]
            if gap and gap[0] == side:
                segs = [(0.6, gap[1]), (gap[2], length)]
            for z0, z1 in segs:
                self.poly([cam.p(X, 0, z0), cam.p(X, bulwark, z0), cam.p(X, bulwark, z1), cam.p(X, 0, z1)], 70 if side < 0 else 85)
                self.line([cam.p(X, bulwark, z0), cam.p(X, bulwark, z1)], 175, 6)
                for z in range(int(z0) + 1, int(z1), 2):
                    self.line([cam.p(X, 0, z), cam.p(X, bulwark, z)], 55, 3)
        if rail_flat:
            side, z0, z1 = rail_flat
            X = side * (half - 0.6)
            self.poly([cam.p(X - 0.15, 0.05, z0), cam.p(X + 0.15, 0.05, z0), cam.p(X + 0.15, 0.05, z1), cam.p(X - 0.15, 0.05, z1)], 185)
        for (hx, hz0, hz1, open_) in hatches:
            self.poly([cam.p(hx - 0.8, 0.25, hz0), cam.p(hx + 0.8, 0.25, hz0), cam.p(hx + 0.8, 0.25, hz1), cam.p(hx - 0.8, 0.25, hz1)],
                      12 if open_ else 120)
            self.box(cam, hx - 0.9, hx + 0.9, 0, 0.25, hz0, hz0 + 0.12, front=100, side=80, top=130)
            if open_:
                self.poly([cam.p(hx + 1.0, 0.02, hz0), cam.p(hx + 2.4, 0.02, hz0), cam.p(hx + 2.4, 0.1, hz1), cam.p(hx + 1.0, 0.1, hz1)], 135)
        if boat_chocks:
            bx, bz = boat_chocks
            for dz in (0, 2.5):
                self.box(cam, bx - 0.8, bx + 0.8, 0.25, 0.55, bz + dz, bz + dz + 0.25, front=170, side=120, top=190)
            self.line([cam.p(bx - 0.8, 0.5, bz + 0.1), cam.p(bx - 1.5, 0.02, bz - 0.4)], 200, 4)
            self.line([cam.p(bx + 0.8, 0.5, bz + 2.6), cam.p(bx + 1.6, 0.02, bz + 2.9)], 200, 4)
        for mz in sorted(masts, reverse=True):
            base, top = cam.p(0, 0, mz), cam.p(0, 30, mz)
            wpx = cam.scale(mz) * 0.35
            self.line([base, top], 60, wpx)
            if sails_up:
                pass
        if helm:
            hx, hzz = helm
            c = cam.p(hx, 1.2, hzz)
            r = cam.scale(hzz) * 0.6
            self.ell(c[0], c[1], r, r, None, 50, max(3, int(r * 0.1)))
            for a in range(0, 360, 45):
                self.line([c, (c[0] + r * 1.25 * math.cos(math.radians(a)), c[1] + r * 1.25 * math.sin(math.radians(a)))], 50, max(2, r * 0.06))
            self.box(cam, hx - 0.15, hx + 0.15, 0, 1.2, hzz + 0.2, hzz + 0.4, front=60, side=45, top=80)
        if wet:
            for i in range(25):
                X = (self.rng.random() * 2 - 1) * half * 0.9
                Z = 1 + self.rng.random() * length * 0.5
                p = cam.p(X, 0, Z)
                s = cam.scale(Z) * (0.06 + self.rng.random() * 0.12)
                self.ell(p[0], p[1], s, s * 0.22, 175)

    def room(self, cam, w=3.0, h=2.1, d=4.0, wall=(95, 75), floor=(85, 60), ceil=60, beams=True, back=None):
        x0, x1 = -w / 2, w / 2
        self.poly([cam.p(x0, h, 0.3), cam.p(x1, h, 0.3), cam.p(x1, h, d), cam.p(x0, h, d)], ceil)
        self.poly([cam.p(x0, 0, 0.3), cam.p(x0, h, 0.3), cam.p(x0, h, d), cam.p(x0, 0, d)], wall[1])
        self.poly([cam.p(x1, 0, 0.3), cam.p(x1, h, 0.3), cam.p(x1, h, d), cam.p(x1, 0, d)], wall[1] + 10)
        self.plane_floor(cam, x0, x1, 0.3, d, 0, floor[0], floor[1])
        self.poly([cam.p(x0, 0, d), cam.p(x1, 0, d), cam.p(x1, h, d), cam.p(x0, h, d)], back if back is not None else wall[0])
        if beams:
            for z in [0.8 + i * 0.7 for i in range(int(d / 0.7))]:
                self.box(cam, x0, x1, h - 0.12, h, z, z + 0.12, front=45, side=40, top=40)
        for z in [0.5 + i * 0.25 for i in range(int(d / 0.25))]:
            self.line([cam.p(x0, 0, z), cam.p(x1, 0, z)], floor[1] - 15, 1)

    def water_floor(self, cam, w, d, y, tone=150):
        self.poly([cam.p(-w / 2, y, 0.3), cam.p(w / 2, y, 0.3), cam.p(w / 2, y, d), cam.p(-w / 2, y, d)], tone)
        for i in range(40):
            X = (self.rng.random() - 0.5) * w
            Z = 0.4 + self.rng.random() * (d - 0.4)
            p = cam.p(X, y, Z)
            s = cam.scale(Z) * 0.25
            self.line([(p[0] - s, p[1]), (p[0] + s, p[1])], tone + 50, 2)

    def barrel(self, x, y, r, tone=105, lying=False):
        X, Y, R = x * W, y * H, r * H
        if lying:
            self.ell(X, Y, R, R, tone)
            self.ell(X, Y, R * 0.88, R * 0.88, None, tone - 35, max(2, int(R * 0.05)))
            self.ell(X, Y, R * 0.7, R * 0.7, None, tone - 25, max(2, int(R * 0.03)))
            self.ell(X, Y, R * 0.08, R * 0.08, tone - 50)
        else:
            self.d.rounded_rectangle([X - R, Y - R * 1.35, X + R, Y + R * 1.35], radius=int(R * 0.5), fill=tone)
            for k in (-0.9, -0.3, 0.3, 0.9):
                self.line([(X - R * (1 - abs(k) * 0.1), Y + k * R * 1.2), (X + R * (1 - abs(k) * 0.1), Y + k * R * 1.2)], tone - 40, max(2, R * 0.06))
            self.ell(X, Y - R * 1.3, R * 0.95, R * 0.25, tone + 25)

    def barrel_stack(self, x0, y0, x1, y1, r, tone=105):
        y = y1
        row = 0
        while y > y0:
            x = x0 + (r * H / W) * (row % 2)
            while x < x1:
                self.barrel(x, y, r, tone + self.rng.randint(-15, 15), lying=True)
                x += 2 * r * H / W
            y -= r * 1.75
            row += 1

    def table(self, cam, x0, x1, z0, z1, y=0.75, tone=120):
        self.box(cam, x0, x1, y - 0.05, y, z0, z1, front=tone - 30, side=tone - 40, top=tone)
        for X, Z in ((x0 + 0.05, z0 + 0.05), (x1 - 0.05, z0 + 0.05)):
            self.box(cam, X - 0.04, X + 0.04, 0, y - 0.05, Z, Z + 0.08, front=tone - 50, side=tone - 60, top=tone - 40)

    def bunk(self, cam, x0, x1, z0, z1, y=0.55, tone=120, wet=False, hollow=False):
        self.box(cam, x0, x1, 0, y, z0, z1, front=60, side=50, top=70)
        self.box(cam, x0 + 0.05, x1 - 0.05, y, y + 0.15, z0 + 0.05, z1 - 0.05, front=tone, side=tone - 20, top=tone + 30)
        if wet:
            for i in range(10):
                X = x0 + (x1 - x0) * self.rng.random()
                Z = z0 + (z1 - z0) * self.rng.random()
                p = cam.p(X, y + 0.16, Z)
                self.ell(p[0], p[1], cam.scale(Z) * 0.12, cam.scale(Z) * 0.04, tone - 45)
        if hollow:
            p = cam.p((x0 + x1) / 2, y + 0.16, (z0 + z1) / 2)
            s = cam.scale((z0 + z1) / 2)
            self.ell(p[0], p[1], s * 0.42, s * 0.12, tone - 30)
            self.ell(p[0] - s * 0.38, p[1] - s * 0.01, s * 0.1, s * 0.06, tone - 40)

    # ---------- props (drawn flat, near camera) ----------
    def prop(self, kind, x=0.55, y=0.62, s=0.3, tone=150):
        X, Y, S = x * W, y * H, s * H
        d = self.d
        if kind == "compass":
            self.ell(X, Y, S, S * 0.55, 90)
            self.ell(X, Y, S * 0.85, S * 0.45, 200)
            for a in range(0, 360, 30):
                self.line([(X, Y), (X + S * 0.8 * math.cos(math.radians(a)), Y + S * 0.42 * math.sin(math.radians(a)))], 120, 2)
            self.line([(X - S * 0.6, Y + S * 0.2), (X + S * 0.5, Y - S * 0.25)], 30, 6)
            for i in range(9):
                a = self.rng.random() * 6.28
                self.line([(X, Y - S * 0.05), (X + S * 0.8 * math.cos(a), Y + S * 0.4 * math.sin(a))], 250, 3)
        elif kind == "rod":
            self.poly([(X - S * 2.2, Y - S * 0.06), (X + S * 2.2, Y - S * 0.14), (X + S * 2.2, Y + S * 0.0), (X - S * 2.2, Y + S * 0.08)], 170)
            self.poly([(X - S * 2.2, Y - S * 0.06), (X - S * 0.6, Y - S * 0.09), (X - S * 0.6, Y + S * 0.05), (X - S * 2.2, Y + S * 0.08)], 60)
            for k in range(12):
                xx = X - S * 2.0 + k * S * 0.36
                self.line([(xx, Y - S * 0.1), (xx, Y + S * 0.04)], 30, 3)
        elif kind == "logbook":
            self.poly([(X - S * 1.4, Y - S * 0.7), (X, Y - S * 0.6), (X + S * 1.4, Y - S * 0.7), (X + S * 1.5, Y + S * 0.6),
                       (X, Y + S * 0.7), (X - S * 1.5, Y + S * 0.6)], 215)
            self.line([(X, Y - S * 0.6), (X, Y + S * 0.7)], 120, 4)
            for k in range(9):
                yy = Y - S * 0.5 + k * S * 0.12
                self.line([(X - S * 1.3, yy), (X - S * 0.15, yy + 4)], 90, 3)
                if k < 3:
                    self.line([(X + S * 0.15, yy + 4), (X + S * 1.25, yy)], 90, 3)
        elif kind == "slate":
            self.poly([(X - S * 1.3, Y - S * 0.85), (X + S * 1.3, Y - S * 0.8), (X + S * 1.35, Y + S * 0.85), (X - S * 1.35, Y + S * 0.8)], 150)
            self.poly([(X - S * 1.15, Y - S * 0.7), (X + S * 1.15, Y - S * 0.66), (X + S * 1.2, Y + S * 0.7), (X - S * 1.2, Y + S * 0.66)], 35)
            for k in range(6):
                yy = Y - S * 0.5 + k * S * 0.2
                self.line([(X - S * 1.0, yy), (X + S * (0.2 + 0.7 * self.rng.random()), yy + 3)], 175, 4)
        elif kind == "letter":
            self.poly([(X - S * 1.0, Y - S * 0.75), (X + S * 1.0, Y - S * 0.8), (X + S * 1.05, Y + S * 0.75), (X - S * 0.95, Y + S * 0.8)], 225)
            for k in range(10):
                yy = Y - S * 0.6 + k * S * 0.13
                self.line([(X - S * 0.8, yy), (X + S * (0.3 + 0.5 * self.rng.random()), yy - 2)], 100, 3)
        elif kind == "sword":
            self.line([(X - S * 2.2, Y + S * 0.3), (X + S * 1.6, Y - S * 0.2)], 190, S * 0.09)
            for i in range(14):
                t = self.rng.random()
                p = (X - S * 2.2 + t * S * 3.8, Y + S * 0.3 - t * S * 0.5)
                self.ell(p[0], p[1], S * 0.05, S * 0.03, 95)
            self.line([(X + S * 1.6, Y - S * 0.5), (X + S * 1.7, Y + S * 0.1)], 80, S * 0.08)
            self.line([(X + S * 1.65, Y - S * 0.2), (X + S * 2.3, Y - S * 0.3)], 60, S * 0.12)
        elif kind == "chrono_box":
            self.poly([(X - S * 1.1, Y - S * 0.6), (X + S * 1.1, Y - S * 0.6), (X + S * 1.25, Y + S * 0.7), (X - S * 1.25, Y + S * 0.7)], 90)
            self.ell(X, Y + S * 0.05, S * 0.7, S * 0.45, 40)
            self.ell(X, Y + S * 0.05, S * 0.55, S * 0.33, 25)
        elif kind == "sextant_case":
            self.poly([(X - S * 1.0, Y - S * 0.8), (X + S * 1.0, Y - S * 0.8), (X + S * 1.1, Y + S * 0.8), (X - S * 1.1, Y + S * 0.8)], 95)
            self.d.pieslice([X - S * 0.8, Y - S * 0.9, X + S * 0.8, Y + S * 0.7], 40, 140, fill=35)
        elif kind == "drawer":
            self.poly([(X - S * 1.5, Y - S * 0.4), (X + S * 1.5, Y - S * 0.4), (X + S * 1.8, Y + S * 0.6), (X - S * 1.8, Y + S * 0.6)], 110)
            self.poly([(X - S * 1.35, Y - S * 0.3), (X + S * 1.35, Y - S * 0.3), (X + S * 1.6, Y + S * 0.45), (X - S * 1.6, Y + S * 0.45)], 45)
        elif kind == "pump_parts":
            self.line([(X - S * 1.8, Y + S * 0.3), (X - S * 0.2, Y + S * 0.1)], 70, S * 0.18)
            self.ell(X + S * 0.4, Y + S * 0.2, S * 0.25, S * 0.12, 120)
            self.line([(X + S * 0.9, Y + S * 0.4), (X + S * 2.0, Y - S * 0.1)], 150, S * 0.06)
            self.ell(X + S * 1.2, Y - S * 0.25, S * 0.18, S * 0.1, 60)
            for i in range(30):
                self.ell(X - S * 1.5 + self.rng.random() * S * 3, Y + S * 0.45 + self.rng.random() * S * 0.2, 4, 3, 25)
        elif kind == "organ":
            self.box(Cam(hz=y - 0.2, camH=1.6), -0.6, 0.6, 0, 0.9, 2.2, 2.7, front=95, side=70, top=130)
            for k in range(16):
                p = Cam(hz=y - 0.2, camH=1.6).p(-0.55 + k * 0.07, 0.9, 2.22)
                self.line([p, (p[0], p[1] + 18)], 230, 8)
        elif kind == "dolls":
            for dx, broken in ((-0.6, False), (0.6, True)):
                cx = X + dx * S
                self.ell(cx, Y - S * 0.55, S * 0.22, S * 0.25, 215)
                self.poly([(cx - S * 0.3, Y - S * 0.3), (cx + S * 0.3, Y - S * 0.3), (cx + S * 0.45, Y + S * 0.6), (cx - S * 0.45, Y + S * 0.6)], 175)
                self.line([(cx - S * 0.3, Y - S * 0.25), (cx - S * 0.55, Y + S * 0.15)], 200, S * 0.09)
                if broken:
                    self.line([(cx + S * 0.3, Y - S * 0.25), (cx + S * 0.4, Y - S * 0.1)], 200, S * 0.09)
                    self.line([(cx + S * 0.75, Y + S * 0.5), (cx + S * 0.95, Y + S * 0.65)], 200, S * 0.09)
                else:
                    self.line([(cx + S * 0.3, Y - S * 0.25), (cx + S * 0.55, Y + S * 0.15)], 200, S * 0.09)
        elif kind == "seal":
            self.poly([(X - S * 1.6, Y - S * 0.6), (X + S * 1.6, Y - S * 0.7), (X + S * 1.8, Y + S * 0.7), (X - S * 1.7, Y + S * 0.8)], 165)
            self.line([(X - S * 1.7, Y), (X + S * 1.8, Y - S * 0.05)], 220, 5)
            self.line([(X, Y - S * 0.7), (X + S * 0.05, Y + S * 0.75)], 220, 5)
            self.ell(X, Y, S * 0.3, S * 0.25, 55)
            self.ell(X, Y, S * 0.18, S * 0.15, 80)
        elif kind == "staves":
            for dx, t, pores in ((-0.9, 150, 40), (0.9, 175, 6)):
                cx = X + dx * S
                self.poly([(cx - S * 0.6, Y - S * 0.5), (cx + S * 0.6, Y - S * 0.5), (cx + S * 0.65, Y + S * 0.5), (cx - S * 0.65, Y + S * 0.5)], t)
                for k in range(pores):
                    self.ell(cx - S * 0.55 + self.rng.random() * S * 1.1, Y - S * 0.45 + self.rng.random() * S * 0.9, 5, 4, 50)
                for k in range(6):
                    yy = Y - S * 0.4 + k * S * 0.16
                    self.line([(cx - S * 0.6, yy), (cx + S * 0.6, yy + 6)], t - 40, 2)
        elif kind == "tube":
            self.d.rounded_rectangle([X - S * 0.12, Y - S * 1.0, X + S * 0.12, Y + S * 0.8], radius=int(S * 0.12), fill=200)
            self.d.rounded_rectangle([X - S * 0.1, Y + S * 0.1, X + S * 0.1, Y + S * 0.78], radius=int(S * 0.1), fill=235)
        elif kind == "stain":
            for k in range(-4, 5):
                yy = Y + k * S * 0.22
                self.line([(0, yy), (W, yy - 20)], 85, 3)
            def draw(l, m):
                for i in range(6):
                    cx, cy = X + (self.rng.random() - 0.5) * S, Y + (self.rng.random() - 0.5) * S * 0.4
                    r = S * (0.1 + self.rng.random() * 0.25)
                    l.ellipse([cx - r, cy - r * 0.4, cx + r, cy + r * 0.4], fill=40)
                    m.ellipse([cx - r, cy - r * 0.4, cx + r, cy + r * 0.4], fill=200)
            self.blur_layer(draw, 8)
        elif kind == "notice":
            self.poly([(X - S * 0.25, 0), (X + S * 0.25, 0), (X + S * 0.25, H), (X - S * 0.25, H)], 80)
            self.poly([(X - S * 0.7, Y - S * 0.9), (X + S * 0.7, Y - S * 0.85), (X + S * 0.65, Y + S * 0.9), (X - S * 0.72, Y + S * 0.85)], 225)
            for k in range(8):
                yy = Y - S * 0.6 + k * S * 0.17
                self.line([(X - S * 0.5, yy), (X + S * 0.45, yy)], 110, 3)
            self.ell(X, Y - S * 0.78, 8, 8, 40)
        elif kind == "blanket":
            for k in range(7):
                yy = Y - S * 0.6 + k * S * 0.2
                self.d.chord([X - S * 2.5, yy - S * 0.15, X + S * 2.5, yy + S * 0.25], 0, 180, fill=120 + (k % 2) * 20)
            for i in range(20):
                self.ell(X + (self.rng.random() - 0.5) * S * 3, Y + (self.rng.random() - 0.3) * S, 10, 6, 230)
        elif kind == "rail":
            self.poly([(0, Y + S * 0.2), (W, Y - S * 0.4), (W, Y - S * 0.1), (0, Y + S * 0.5)], 175)
            for k in range(4):
                xx = W * (0.15 + 0.22 * k)
                yy = Y + S * 0.35 - (xx / W) * S * 0.6
                self.ell(xx, yy, 10, 6, 30)
        elif kind == "chocks":
            for dx in (-0.8, 0.8):
                self.poly([(X + dx * S - S * 0.5, Y), (X + dx * S + S * 0.5, Y), (X + dx * S + S * 0.45, Y + S * 0.4), (X + dx * S - S * 0.45, Y + S * 0.4)], 175)
                self.d.chord([X + dx * S - S * 0.4, Y - S * 0.3, X + dx * S + S * 0.4, Y + S * 0.3], 0, 180, fill=60)
            self.line([(X - S * 1.5, Y + S * 0.2), (X - S * 2.2, Y + S * 0.7)], 215, 6)
            self.line([(X + S * 1.5, Y + S * 0.2), (X + S * 2.3, Y + S * 0.6)], 215, 6)
        elif kind == "coats":
            for k in range(3):
                cx = X + (k - 1) * S * 0.7
                self.poly([(cx - S * 0.3, Y - S * 0.8), (cx + S * 0.3, Y - S * 0.8), (cx + S * 0.38, Y + S * 0.8), (cx - S * 0.38, Y + S * 0.8)], 50 + k * 15)
                self.line([(cx, Y - S * 0.95), (cx, Y - S * 0.8)], 160, 4)
        elif kind == "pen":
            self.prop("letter", x, y, s)
            self.line([(X + S * 0.2, Y + S * 0.1), (X + S * 1.3, Y - S * 0.9)], 30, S * 0.06)
        elif kind == "chart":
            self.poly([(X - S * 2.6, Y - S * 0.9), (X + S * 2.6, Y - S * 1.0), (X + S * 2.9, Y + S * 1.0), (X - S * 2.9, Y + S * 1.05)], 210)
            for k in range(8):
                self.line([(X - S * 2.6 + k * S * 0.75, Y - S * 0.95), (X - S * 2.9 + k * S * 0.83, Y + S * 1.0)], 180, 2)
            self.poly([(X - S * 2.0, Y - S * 0.2), (X - S * 1.6, Y - S * 0.35), (X - S * 1.4, Y - S * 0.1), (X - S * 1.8, Y + S * 0.05)], 150)

    def ripple(self, x, y, r=0.06, k=3):
        """Accent: soft FILLED orange bands (never line rings). Drawn after toning."""
        def f(rgb):
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            dd = ImageDraw.Draw(layer)
            for i in range(k, 0, -1):
                rr = r * H * i / k
                a = int(110 * (1 - (i - 1) / k))
                dd.ellipse([x * W - rr * 1.6, y * H - rr * 0.6, x * W + rr * 1.6, y * H + rr * 0.6], fill=(240, 140, 50, a))
            layer = layer.filter(ImageFilter.GaussianBlur(18))
            return Image.alpha_composite(rgb.convert("RGBA"), layer).convert("RGB")
        self.overlays.append(f)

    def pin(self, x, y, tone=230):
        X, Y = x * W, y * H
        self.line([(X, Y), (X + 8, Y - 70)], 60, 6)
        self.ell(X + 8, Y - 78, 16, 16, tone)

    def pencil_line(self, pts, tone=40, w=5):
        self.line([(p[0] * W, p[1] * H) for p in pts], tone, w)

    # ---------- finish ----------
    def finish(self, path, label=None, move=None, card=None, tag=None, silence=False, spec=False):
        self.vignette(0.45)
        black, mid, white = MOODS[self.mood]
        rgb = ImageOps.colorize(self.img, black=black, mid=mid, white=white)
        if spec:
            rgb = Image.blend(rgb, ImageOps.grayscale(rgb).convert("RGB"), 0.5)
        for f in self.overlays:
            rgb = f(rgb)
        d = ImageDraw.Draw(rgb)
        if move:
            draw_move(d, move)
        if card:
            draw_card(d, card)
        if tag:
            ft = ImageFont.truetype("/home/user/Muhammed/mary_celeste/assets/fonts/CourierPrime-Bold.ttf", 34)
            tw = d.textlength(tag, font=ft)
            d.rectangle([(W - tw) / 2 - 20, 30, (W + tw) / 2 + 20, 86], fill=(10, 10, 10))
            d.text(((W - tw) / 2, 40), tag, font=ft, fill=(240, 240, 235))
        if label:
            ft = ImageFont.truetype(FONT, 34)
            d.rectangle([0, 0, d.textlength(label, font=ft) + 40, 60], fill=(0, 0, 0))
            d.text((20, 10), label, font=ft, fill=(255, 255, 255))
        if silence:
            ft = ImageFont.truetype(FONT, 34)
            s = "SILENCE"
            tw = d.textlength(s, font=ft)
            d.rectangle([W - tw - 40, 0, W, 60], fill=(150, 20, 20))
            d.text((W - tw - 20, 10), s, font=ft, fill=(255, 255, 255))
        if spec:
            ft = ImageFont.truetype(FONT, 30)
            s = "RECONSTRUCTION (desaturated)"
            d.rectangle([0, H - 56, d.textlength(s, font=ft) + 40, H], fill=(0, 0, 0))
            d.text((20, H - 48), s, font=ft, fill=(220, 220, 220))
        rgb.resize((OUT_W, OUT_W * 9 // 16), Image.LANCZOS).save(path, quality=84)


def arrow(d, a, b, col=(255, 255, 255), w=10):
    d.line([a, b], fill=(0, 0, 0), width=w + 8)
    d.line([a, b], fill=col, width=w)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    L = 42
    pts = [b, (b[0] - L * math.cos(ang - 0.45), b[1] - L * math.sin(ang - 0.45)),
           (b[0] - L * math.cos(ang + 0.45), b[1] - L * math.sin(ang + 0.45))]
    d.polygon(pts, fill=col, outline=(0, 0, 0))


def draw_move(d, move):
    Y = (255, 214, 60)
    if move in ("push", "pull", "push_slow"):
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            o = (W / 2 + sx * W * 0.40, H / 2 + sy * H * 0.38)
            i = (W / 2 + sx * W * 0.30, H / 2 + sy * H * 0.28)
            arrow(d, o, i, Y) if move != "pull" else arrow(d, i, o, Y)
        if move == "push" or move == "push_slow":
            d.rectangle([W * 0.3, H * 0.28, W * 0.7, H * 0.72], outline=Y, width=5)
    elif move in ("pan_l", "pan_r", "track_l", "track_r"):
        y = H * 0.9
        a, b = (W * 0.3, y), (W * 0.7, y)
        if move.endswith("_l"):
            a, b = b, a
        arrow(d, a, b, Y)
        ft = ImageFont.truetype(FONT, 30)
        d.text((W * 0.46, y - 60), "PAN" if move.startswith("pan") else "TRACK", font=ft, fill=Y, stroke_width=3, stroke_fill=(0, 0, 0))
    elif move in ("tilt_u", "tilt_d", "crane_u", "crane_d"):
        x = W * 0.93
        a, b = (x, H * 0.75), (x, H * 0.25)
        if move.endswith("_d"):
            a, b = b, a
        arrow(d, a, b, Y)
        ft = ImageFont.truetype(FONT, 30)
        d.text((x - 130, H * 0.5), "TILT" if move.startswith("tilt") else "CRANE", font=ft, fill=Y, stroke_width=3, stroke_fill=(0, 0, 0))
    elif move == "orbit":
        d.arc([W * 0.25, H * 0.75, W * 0.75, H * 0.98], 200, 340, fill=Y, width=10)
        arrow(d, (W * 0.70, H * 0.80), (W * 0.74, H * 0.84), Y)
    elif move == "handheld":
        pts = [(W * 0.35 + i * 30, H * 0.92 + 14 * math.sin(i)) for i in range(18)]
        d.line(pts, fill=Y, width=8)
    elif move == "rack":
        ft = ImageFont.truetype(FONT, 32)
        d.text((W * 0.40, H * 0.88), "RACK FOCUS", font=ft, fill=Y, stroke_width=3, stroke_fill=(0, 0, 0))
    elif move == "static":
        ft = ImageFont.truetype(FONT, 32)
        d.text((W * 0.42, H * 0.88), "LOCKED OFF", font=ft, fill=Y, stroke_width=3, stroke_fill=(0, 0, 0))


def draw_card(d, card):
    side, name, role = card
    ft = ImageFont.truetype("/home/user/Muhammed/mary_celeste/assets/fonts/CourierPrime-Bold.ttf", 40)
    fr = ImageFont.truetype("/home/user/Muhammed/mary_celeste/assets/fonts/CourierPrime-Regular.ttf", 32)
    cw, ch = 640, 220
    x = W - cw - 60 if side == "r" else 60
    y = H * 0.56
    d.rectangle([x, y, x + cw, y + ch], fill=(18, 18, 18), outline=(255, 255, 255), width=4)
    d.rectangle([x + 18, y + 18, x + 168, y + ch - 18], fill=(150, 150, 150), outline=(255, 255, 255), width=6)
    d.text((x + 186, y + 50), name, font=ft, fill=(255, 255, 255))
    d.text((x + 186, y + 104), role, font=fr, fill=(210, 210, 210))
    a = (x + cw + 40, y - 30) if side == "r" else (x - 40, y - 30)
    b = (x + cw - 120, y - 30) if side == "r" else (x + 120, y - 30)
    arrow(d, a, b, (120, 220, 255), 7)
