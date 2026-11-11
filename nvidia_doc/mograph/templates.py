"""Motion-graphics templates. Each template draws one frame: fn(fr, t, dur, beat, P) on a transparent Frame.
`t` is seconds into the beat, `dur` its length, `P` the beat's shot params. Registry: TEMPLATES[name]."""
import math
import numpy as np
from style import *
from canvas import Frame, font
import geo

TEMPLATES = {}


def template(name):
    def deco(fn):
        TEMPLATES[name] = fn
        return fn
    return deco


# ============================================================================ shared overlay layers
def draw_tag(fr, t, dur, tag):
    """ILLUSTRATION / RECONSTRUCTION marker, top-right: honest about recreated pictures."""
    if not tag:
        return
    a = window(t, 0.2, dur - 0.1, 0.4) * 0.85
    x = W - MARGIN; y = 86
    w_ = fr.text_width(tag, "mono_m", 15, 0.18) + 28
    fr.rect(x - w_, y - 22, w_, 32, STEEL, a * 0.6, stroke=1.2, r=3)
    fr.text(tag, x - 14, y, "mono_m", 15, STEEL, a, track=0.18, anchor="r")


def draw_src(fr, t, dur, src):
    if not src:
        return
    a = window(t, 0.5, dur - 0.1, 0.5) * 0.9
    fr.text("SOURCE", W - MARGIN, H - 92, "mono", 13, FAINT, a, track=0.2, anchor="r")
    fr.text(src, W - MARGIN, H - 66, "mono_m", 16, DIM, a, track=0.08, anchor="r")


def draw_date(fr, t, dur, g):
    a = window(t, 0.15, dur - 0.1, 0.35)
    if a <= 0:
        return
    x, y = MARGIN, 104
    fr.rect(x, y - 30, 6, 40, AMBER, a)
    fr.text(g["text"], x + 22, y, "mono_m", 30, TEXT, a, track=0.06, reveal=ease_out((t - 0.15) / 0.6))


def draw_label(fr, t, dur, g):
    pos = g.get("pos", "bl")
    a = window(t, 0.35, dur - 0.15, 0.45)
    if a <= 0:
        return
    slide = (1 - ease_out((t - 0.35) / 0.7)) * 24
    if pos == "name":        # big name super, lower-left, serif
        x, y = MARGIN, H - 210
        fr.rect(x, y - 64, 2.5, 120 if g.get("sub") else 76, TEXT, a * 0.9)
        fr.text(g["text"].title() if g["text"].isupper() and len(g["text"]) < 24 else g["text"], x + 26 - slide, y, "title", 74, TEXT, a)
        if g.get("sub"):
            fr.text(g["sub"], x + 28 - slide, y + 44, "sans", 24, DIM, a)
        return
    if pos == "spec":        # spec readout, right side
        x, y = W - MARGIN, H / 2 - 40
        fr.text(g["text"], x + slide, y, "mono_b", 92, TEXT, a, anchor="r", glow=6)
        fr.line((x - 260, y + 30), (x, y + 30), CYAN, 2, a)
        if g.get("sub"):
            fr.text(g["sub"].upper(), x + slide, y + 66, "sans_sb", 20, DIM, a, track=0.18, anchor="r")
        return
    x, y = MARGIN, H - 150     # standard lower-third
    fr.line((x, y - 44), (x + 54 * ease_out((t - 0.35) / 0.5), y - 44), TEXT, 2, a)
    fr.label(g["text"], x - slide, y, 30, TEXT, a)
    if g.get("sub"):
        fr.text(g["sub"], x - slide, y + 40, "sans", 26, DIM, a)


def draw_overlays(fr, t, dur, beat, skip=()):
    for g in beat["gfx"]:
        k = g["kind"]
        if k in skip:
            continue
        if k == "date":
            draw_date(fr, t, dur, g)
        elif k == "label":
            draw_label(fr, t, dur, g)
    draw_tag(fr, t, dur, beat.get("tag"))
    draw_src(fr, t, dur, beat.get("src"))


# ============================================================================ icons
def chip_icon(fr, x, y, s, rgb=CYAN, a=1.0, glow=0):
    """Generic processor: package, die, pins (no brand features)."""
    fr.rect(x - s, y - s, 2 * s, 2 * s, BG2, a, r=s * 0.12)
    fr.rect(x - s, y - s, 2 * s, 2 * s, rgb, a, stroke=max(1.5, s * 0.06), r=s * 0.12)
    fr.rect(x - s * 0.5, y - s * 0.5, s, s, rgb, a * 0.85, r=s * 0.06, blur=0)
    if glow:
        fr.rect(x - s * 0.5, y - s * 0.5, s, s, rgb, a * 0.5, r=s * 0.06, blur=glow)
    for k in range(5):
        o = -s * 0.7 + k * s * 0.35
        for (ax, ay, bx, by) in ((x + o, y - s, x + o, y - s * 1.3), (x + o, y + s, x + o, y + s * 1.3),
                                 (x - s, y + o, x - s * 1.3, y + o), (x + s, y + o, x + s * 1.3, y + o)):
            fr.line((ax, ay), (bx, by), rgb, max(1.2, s * 0.05), a)


def server_icon(fr, x, y, w_, h_, rgb=STEEL, a=1.0, lights=0.0, t=0.0):
    fr.rect(x, y, w_, h_, BG2, a, r=6); fr.rect(x, y, w_, h_, rgb, a, stroke=2, r=6)
    n = 6
    for k in range(n):
        yy = y + 12 + k * (h_ - 24) / n
        fr.rect(x + 12, yy, w_ - 24, (h_ - 24) / n - 8, rgb, a * 0.18, r=3)
        for j in range(3):
            on = (math.sin(t * 7 + k * 1.7 + j * 2.3) > 0.2) * lights
            fr.circle(x + w_ - 26 - j * 14, yy + ((h_ - 24) / n - 8) / 2, 3, CYAN, a * (0.25 + 0.75 * on), glow=4 if on else 0)


def cloud_icon(fr, x, y, s, rgb=CYAN, a=1.0, stroke=2.5):
    import skia
    P = skia.Path()
    P.addCircle(x - s * 0.55, y + s * 0.1, s * 0.42); P.addCircle(x, y - s * 0.18, s * 0.58); P.addCircle(x + s * 0.6, y + s * 0.12, s * 0.4)
    P.addRect(skia.Rect.MakeLTRB(x - s * 0.55, y + s * 0.1, x + s * 0.6, y + s * 0.52))
    P2 = skia.Op(P, skia.Path(), skia.PathOp.kUnion_PathOp) or P
    fr.c.drawPath(P2, fr.paint(BG2, a)); fr.c.drawPath(P2, fr.paint(rgb, a, stroke=stroke))


def doc_icon(fr, x, y, w_, h_, rgb=PAPER, a=1.0, lines=6, ink=INK):
    fr.rect(x, y, w_, h_, rgb, a, r=4)
    for k in range(lines):
        ww = w_ * (0.75 if k % 3 == 2 else 0.86)
        fr.rect(x + w_ * 0.08, y + h_ * 0.18 + k * h_ * 0.11, ww * 0.95, h_ * 0.035, ink, a * 0.55, r=2)


def bg_grid(fr, a=0.35, step=60, t=0.0):
    for x in range(0, W + step, step):
        fr.line((x, 0), (x, H), GRID, 1, a * 0.6)
    for y in range(0, H + step, step):
        fr.line((0, y), (W, y), GRID, 1, a * 0.6)


# ============================================================================ cards
@template("quote_card")
def t_quote(fr, t, dur, beat, P):
    q = next(g for g in beat["gfx"] if g["kind"] == "quote")
    hb = P.get("hold_black", 0.0)
    rv = ease_in_out((t - hb) / max(0.8, dur * 0.45))
    a = window(t, hb, dur, 0.4)
    size = 88
    lines = fr.wrap("“" + q["text"] + "”", "quote", size, W - 2 * MARGIN - 200)
    y0 = H / 2 - (len(lines) - 1) * size * 0.62
    total = sum(len(l) for l in lines); done = rv * total
    for k, l in enumerate(lines):
        frac = max(0.0, min(1.0, (done - sum(len(x) for x in lines[:k])) / max(len(l), 1)))
        fr.text(l, W / 2, y0 + k * size * 1.2, "quote", size, TEXT, a, anchor="c", reveal=frac)
    ya = y0 + len(lines) * size * 1.2 + 30
    aa = window(t, hb + dur * 0.45, dur, 0.5)
    fr.line((W / 2 - 40, ya - 10), (W / 2 + 40, ya - 10), AMBER, 2, aa)
    fr.label(q["who"], W / 2, ya + 36, 20, DIM, aa, anchor="c")
    if q.get("when"):
        fr.text(q["when"], W / 2, ya + 72, "mono_m", 20, FAINT, aa, track=0.12, anchor="c")


@template("quote_card_small")
def t_quote_small(fr, t, dur, beat, P):
    q = next(g for g in beat["gfx"] if g["kind"] == "quote")
    a = window(t, 0.6, dur - 0.1, 0.5)
    x = MARGIN; y = H - 300
    fr.rect(x, y - 70, 4, 150, AMBER, a)
    fr.text("“" + q["text"] + "”", x + 34, y, "quote", 64, TEXT, a, reveal=ease_out((t - 0.6) / 1.6))
    fr.label(q["who"], x + 36, y + 64, 19, DIM, window(t, 1.6, dur - 0.1, 0.5))


@template("title_card")
def t_title(fr, t, dur, beat, P):
    ttl = next(g for g in beat["gfx"] if g["kind"] == "title")["text"]
    words = ttl.split()
    a = window(t, 0.2, dur - 0.1, 0.8)
    # two lines: THE SPY ALLEGATIONS / ROCKING NVIDIA
    l1 = title_case(" ".join(words[:3])); l2 = title_case(" ".join(words[3:]))
    s1, s2 = 150, 150
    fr.label("A DOCUMENTARY", W / 2, H / 2 - 190, 20, DIM, window(t, 0.6, dur - 0.1, 0.6), anchor="c", track=0.5)
    fr.text(l1, W / 2, H / 2 - 20, "title", s1, TEXT, a, anchor="c", glow=0)
    fr.text(l2, W / 2, H / 2 + 130, "title_i", s2, TEXT, a, anchor="c")
    # light sweep across the type
    sx = -400 + (W + 800) * ease_in_out((t - 0.6) / 2.4)
    import skia
    sh = skia.GradientShader.MakeLinear([skia.Point(sx - 220, 0), skia.Point(sx + 220, 0)],
                                        [skia.Color(255, 255, 255, 0), skia.Color(255, 255, 255, int(140 * a)), skia.Color(255, 255, 255, 0)],
                                        [0.0, 0.5, 1.0])
    p = skia.Paint(AntiAlias=True); p.setShader(sh); p.setBlendMode(skia.BlendMode.kSrcATop)
    fr.c.drawRect(skia.Rect.MakeXYWH(0, H / 2 - 160, W, 340), p)
    fr.line((W / 2 - 160 * ease_out((t - 1.0) / 1.2), H / 2 + 200), (W / 2 + 160 * ease_out((t - 1.0) / 1.2), H / 2 + 200), RED, 2, a)


@template("chapter_card")
def t_chapter(fr, t, dur, beat, P):
    a = window(t, 0.2, dur - 0.05, 0.6)
    fr.label("CHAPTER " + P["number"], W / 2, H / 2 - 70, 24, DIM, a, anchor="c", track=0.6)
    w_ = 120 * ease_out((t - 0.3) / 0.9)
    fr.line((W / 2 - w_, H / 2 - 36), (W / 2 + w_, H / 2 - 36), AMBER, 2, a)
    fr.text(title_case(P["name"]), W / 2, H / 2 + 80, "title", 132, TEXT, a, anchor="c", reveal=ease_out((t - 0.4) / 1.2))


@template("final_question")
def t_final(fr, t, dur, beat, P):
    q = next(g for g in beat["gfx"] if g["kind"] == "title")["text"]
    a = window(t, 0.3, dur, 0.8)
    l1, l2 = "What, if anything,", "reached Beijing?"
    fr.text(l1, W / 2, H / 2 - 20, "title", 120, TEXT, a, anchor="c", reveal=ease_out((t - 0.3) / 1.0))
    fr.text(l2, W / 2, H / 2 + 110, "title_i", 120, TEXT, a, anchor="c", reveal=ease_out((t - 1.0) / 1.0))


@template("sources")
def t_sources(fr, t, dur, beat, P):
    a = window(t, 0.3, dur - 0.2, 0.8)
    fr.label("SOURCES", MARGIN, 170, 22, DIM, a, track=0.5)
    rows = [
        ("NVIDIA", "Employee email · board statements · appointment of outside counsel · SEC filing on the H20"),
        ("REUTERS", "Corporate filings · shipping records · Taipei footage · profile of Alice Huang"),
        ("FINANCIAL TIMES", "Investor account of the 2025 data-center pitch"),
        ("THE NEW YORK TIMES", "Reporting on the memo and on U.S. inquiries into Megaspeed"),
        ("THE STRAITS TIMES", "Visit to Megaspeed’s Singapore office"),
        ("U.S. COMMERCE DEPARTMENT", "October 2022 export controls"),
        ("U.S. HOUSE COMMITTEES", "Request for a private briefing"),
        ("CHINA’S FOREIGN MINISTRY", "Response to the allegation"),
        ("ASSOCIATED PRESS", "Shareholder complaint · FBI update"),
    ]
    for k, (who, what) in enumerate(rows):
        y = 250 + k * 62
        ak = a * ease_out((t - 0.5 - k * 0.12) / 0.6)
        fr.text(who, MARGIN, y, "mono_m", 22, TEXT, ak, track=0.06)
        fr.text(what, MARGIN + 470, y, "sans", 24, DIM, ak)
    note = "All pictures in this film are illustrations and reconstructions generated in software. No real footage or photographs are shown."
    fr.text(note, MARGIN, H - 120, "sans", 22, FAINT, a * ease_out((t - 2.0) / 1.0))
    fr.text("REPORTING CUTOFF · NOVEMBER 11, 2026", MARGIN, H - 80, "mono", 18, FAINT, a * ease_out((t - 2.2) / 1.0), track=0.12)


# ============================================================================ map
def _draw_map(fr, proj, a=1.0, highlight=()):
    for rec, rings in geo.countries():
        name = rec.get("ADMIN", "")
        hl = name in highlight
        for r in rings:
            for piece in proj.ring(r):
                pts = [tuple(p) for p in piece]
                if max(p[0] for p in pts) < -50 or min(p[0] for p in pts) > W + 50:
                    continue
                fr.poly_fill(pts, (30, 37, 46) if hl else LAND, a)
                fr.path(pts + [pts[0]], BORDER if not hl else (78, 92, 108), 1.0, a * 0.9)


def _city(fr, x, y, name, a, rgb=TEXT, t=0.0, side="r", sub=None):
    ring = (t * 0.8) % 1.0
    fr.circle(x, y, 6 + ring * 26, rgb, a * (1 - ring) * 0.6, stroke=1.5)
    fr.circle(x, y, 5.5, rgb, a, glow=6)
    dx = 18 if side == "r" else -18
    fr.label(name, x + dx, y - 12, 20, rgb, a, anchor="l" if side == "r" else "r")
    if sub:
        fr.text(sub, x + dx, y + 16, "sans", 19, DIM, a, anchor="l" if side == "r" else "r")


@template("map")
def t_map(fr, t, dur, beat, P):
    v = geo.VIEWS[P.get("view", "asia")]
    z = 1 + (v["push"] - 1) * ease_in_out(t / dur)
    proj = geo.Projection(v["lon"], v["lat"], v["ppd"], z)
    fade = window(t, 0, dur + 1, 0.4)
    bg_grid(fr, 0.25)
    hl = {"us_china": ("United States of America", "China"), "pacific": ("United States of America", "China"),
          "asia": ("China", "Singapore", "Indonesia", "Taiwan"), "sea": ("Indonesia", "Singapore", "Malaysia")}[P.get("view", "asia")]
    _draw_map(fr, proj, fade, hl)
    for (A, B, kind) in P.get("routes", []):
        ca = geo.CITIES.get(A); cb = geo.CITIES.get(B)
        prog = ease_in_out((t - 0.4) / max(1.2, dur * 0.5))
        if kind == "blocked":
            xa, ya = proj(*ca); xb, yb = proj(*cb)
            pts = geo.pacific_arc(proj, ca, cb, 0.10)
            stop = 0.62
            fr.path(pts, AMBER, 3, fade, glow=6, progress=min(prog, 1.0) * stop)
            fr.path(pts, FAINT, 2, fade * 0.6, dash=(6, 10))
            _city(fr, xa, ya, A, fade, t=t, side="r" if xa < xb else "l")
            _city(fr, xb, yb, B, fade, t=t, side="l" if xa < xb else "r")
            if prog > 0.9:
                k = int(stop * (len(pts) - 1)); bx, by = pts[k]
                ab = ease_out((prog - 0.9) / 0.1) * fade
                fr.line((bx - 0, by - 70), (bx, by + 70), RED, 5, ab, glow=10)
                fr.label("RESTRICTED", bx, by - 92, 22, RED, ab, anchor="c")
            if P.get("chips"):
                for j in range(4):
                    s = ((t * 0.25 + j * 0.25) % 1.0) * stop * min(prog * 1.2, 1)
                    k = int(s * (len(pts) - 1)); x, y = pts[k]
                    chip_icon(fr, x, y, 9, CYAN, fade * 0.95)
        elif kind == "data":
            xa, ya = proj(*ca); xb, yb = proj(*cb)
            pts = geo.arc_screen(proj, ca, cb, 0.25)
            fr.path(pts, CYAN, 2.5, fade * 0.8, glow=5, progress=prog)
            for j in range(6):
                s = (t * 0.45 + j / 6) % 1.0
                if s < prog:
                    x, y = pts[int(s * (len(pts) - 1))]
                    fr.circle(x, y, 4.5, CYAN, fade, glow=8)
            _city(fr, xa, ya, "WHO SENDS THE WORK", fade, CYAN, t, side="r", sub="One country")
            _city(fr, xb, yb, "WHERE THE MACHINES ARE", fade, TEXT, t, side="r", sub="Another country")
        elif kind == "shipping":
            xb, yb = proj(*cb)
            lanes = [(118, 16), (128, 5), (96, 8), (112, 22)]
            for j, lane in enumerate(lanes):
                pts = geo.arc_screen(proj, lane, cb, 0.14, 60)
                pr = ease_in_out((t - 0.3 - j * 0.25) / 1.6)
                fr.path(pts, AMBER, 2.5, fade * 0.9, dash=(10, 8), progress=pr)
                if 0 < pr < 0.97:
                    x, y = pts[int(min(pr, 0.999) * (len(pts) - 1))]
                    fr.rect(x - 9, y - 6, 18, 12, AMBER, fade, r=2)
            _city(fr, xb, yb, "INDONESIA", fade, AMBER, t, side="r", sub="Megaspeed’s subsidiary")
            if P.get("manifest"):
                am = window(t, 1.2, dur, 0.5)
                x0, y0 = W - MARGIN - 520, 250
                fr.rect(x0, y0, 520, 300, BG2, am * 0.92, r=8); fr.rect(x0, y0, 520, 300, AMBER, am * 0.7, stroke=1.5, r=8)
                fr.label("SHIPPING RECORDS · REVIEWED BY REUTERS", x0 + 26, y0 + 44, 16, AMBER, am)
                rows = [("CONSIGNEE", "MEGASPEED · INDONESIA"), ("GOODS", "NVIDIA HARDWARE"), ("INCLUDES", "H100"), ("PERIOD", "2024 — 2026")]
                for k, (kk, vv) in enumerate(rows):
                    yy = y0 + 100 + k * 46
                    ar = am * ease_out((t - 1.5 - k * 0.25) / 0.5)
                    fr.text(kk, x0 + 26, yy, "mono", 18, DIM, ar, track=0.1)
                    fr.text(vv, x0 + 200, yy, "mono_m", 20, TEXT, ar, track=0.04)
        elif kind == "unknown":
            xa, ya = proj(*geo.CITIES["INDONESIA"])
            _city(fr, xa, ya, "INDONESIA", fade, AMBER, t, side="l")
            targets = [(140, 40), (75, 30), (150, 0), (100, 45), (60, 10)]
            for j, tg in enumerate(targets):
                pts = geo.arc_screen(proj, geo.CITIES["INDONESIA"], tg, 0.18, 60)
                pr = ease_in_out((t - 0.5 - j * 0.2) / 1.4)
                fr.path(pts, CYAN, 1.8, fade * 0.7, dash=(3, 9), progress=pr)
                if pr >= 0.98:
                    x, y = pts[-1]
                    fr.text("?", x, y + 14, "title", 48, CYAN, fade * ease_out((t - 2.0 - j * 0.2) / 0.5), anchor="c")
    if P.get("view") in ("us_china", "pacific"):
        pass


# ============================================================================ simple text/statement helpers
def headline_card(fr, x, y, w_, head, body, who, a, accent=STEEL):
    h_ = 210
    fr.rect(x, y, w_, h_, BG2, a * 0.95, r=10)
    fr.rect(x, y, 6, h_, accent, a, r=2)
    fr.text(who, x + 36, y + 48, "mono_m", 17, accent, a, track=0.16)
    lines = fr.wrap(head, "serif", 40, w_ - 80)
    for k, l in enumerate(lines[:3]):
        fr.text(l, x + 36, y + 104 + k * 48, "serif", 40, TEXT, a)
    return h_
