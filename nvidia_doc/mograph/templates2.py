"""Second batch of templates: diagrams, documents, data, statements."""
import math
import numpy as np
from style import *
from templates import template, chip_icon, server_icon, cloud_icon, doc_icon, bg_grid, headline_card


def _node(fr, x, y, w_, h_, head, sub, a, rgb=TEXT, accent=STEEL, dashed=False):
    fr.rect(x, y, w_, h_, BG2, a * 0.95, r=10)
    fr.rect(x, y, w_, h_, accent, a, stroke=2, r=10)
    if dashed:
        fr.rect(x, y, w_, h_, BG2, a, r=10); fr.path([(x, y), (x + w_, y), (x + w_, y + h_), (x, y + h_), (x, y)], accent, 2, a, dash=(8, 7))
    fr.label(head, x + 26, y + 46, 24, rgb, a)
    if sub:
        for k, l in enumerate(fr.wrap(sub, "sans", 21, w_ - 52)[:2]):
            fr.text(l, x + 26, y + 82 + k * 28, "sans", 21, DIM, a)


def _arrow(fr, a, b, rgb, w, alpha, prog=1.0, dash=None, head=True):
    pts = [a, b]
    if prog <= 0:
        return
    bx = a[0] + (b[0] - a[0]) * prog; by = a[1] + (b[1] - a[1]) * prog
    fr.line(a, (bx, by), rgb, w, alpha, dash=dash)
    if head and prog > 0.95:
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        for s in (-0.45, 0.45):
            fr.line((bx, by), (bx - 16 * math.cos(ang + s), by - 16 * math.sin(ang + s)), rgb, w, alpha)


def _redaction_lines(fr, x, y, w_, n, a, rng_seed=0, ink=INK, lh=34, bar=(18, 20, 24), redact_p=0.35, t=0.0):
    r = np.random.default_rng(rng_seed)
    for k in range(n):
        lw = w_ * r.uniform(0.62, 1.0)
        if r.random() < 0.12:
            continue
        xx = x
        while xx < x + lw:
            seg = r.uniform(40, 160)
            seg = min(seg, x + lw - xx)
            if r.random() < redact_p:
                fr.rect(xx, y + k * lh - 15, seg, 20, bar, a, r=1)
            else:
                fr.rect(xx, y + k * lh - 6, seg, 6, ink, a * 0.35, r=2)
            xx += seg + 12


def _paper(fr, x, y, w_, h_, a, angle=0.0):
    fr.c.save(); fr.c.translate(x + w_ / 2, y + h_ / 2); fr.c.rotate(angle); fr.c.translate(-(x + w_ / 2), -(y + h_ / 2))
    fr.rect(x + 10, y + 16, w_, h_, (0, 0, 0), a * 0.5, r=2, blur=18)
    fr.rect(x, y, w_, h_, PAPER, a, r=2)


@template("document_stamp")
def t_doc_stamp(fr, t, dur, beat, P):
    a = window(t, 0.1, dur, 0.4)
    slide = (1 - ease_out(t / 1.0)) * 120
    x, y, w_, h_ = (MARGIN + 60 if P.get("doc") == "license" else W / 2 + 140), 150 + slide, 620, 800
    _paper(fr, x, y, w_, h_, a, angle=-3 if P.get("doc") != "license" else 3)
    if P.get("doc") == "license":
        fr.text("LICENSE REQUIREMENT", x + 50, y + 90, "mono_b", 26, INK, a, track=0.1)
        fr.text("Export of the H20 to China", x + 50, y + 130, "serif", 26, INK, a)
        stamp = "LICENSE REQUIRED"
    else:
        fr.text("U.S. DEPARTMENT OF COMMERCE", x + 50, y + 90, "mono_b", 24, INK, a, track=0.1)
        fr.text("Export controls · advanced computing", x + 50, y + 128, "serif", 26, INK, a)
        stamp = "RESTRICTED"
    fr.line((x + 50, y + 160), (x + w_ - 50, y + 160), INK, 1.5, a * 0.6)
    _redaction_lines(fr, x + 50, y + 220, w_ - 100, 15, a, rng_seed=3, redact_p=0.0)
    sa = ease_out((t - 1.2) / 0.25)
    if sa > 0:
        sc = 1.6 - 0.6 * sa
        cx, cy = x + w_ / 2, y + h_ * 0.6
        fr.c.save(); fr.c.translate(cx, cy); fr.c.rotate(-12); fr.c.scale(sc, sc)
        tw = fr.text_width(stamp, "mono_b", 54, 0.12)
        fr.rect(-tw / 2 - 30, -60, tw + 60, 84, RED, a * sa * 0.9, stroke=5, r=6)
        fr.text(stamp, 0, 0, "mono_b", 54, RED, a * sa * 0.9, track=0.12, anchor="c")
        fr.c.restore()
    fr.c.restore()


@template("dual_use")
def t_dual(fr, t, dur, beat, P):
    a = window(t, 0, dur, 0.4)
    bg_grid(fr, 0.2)
    cx, cy = W / 2, H / 2 - 30
    chip_icon(fr, cx, cy, 60, CYAN, a, glow=14)
    fr.label("THE SAME COMPUTING POWER", cx, cy + 130, 20, DIM, a, anchor="c")
    # left: commercial research (network graph)
    al = a * ease_out((t - 0.5) / 0.8)
    r = np.random.default_rng(4)
    nodes = [(cx - 620 + r.uniform(-180, 180), cy + r.uniform(-200, 200)) for _ in range(14)]
    for i, p in enumerate(nodes):
        for q in nodes[i + 1:i + 3]:
            fr.line(p, q, CYAN, 1.2, al * 0.4)
    for i, p in enumerate(nodes):
        fr.circle(*p, 6, CYAN, al * (0.5 + 0.5 * math.sin(t * 4 + i)), glow=6)
    fr.label("COMMERCIAL RESEARCH", cx - 620, cy + 300, 24, TEXT, al, anchor="c")
    _arrow(fr, (cx - 90, cy), (cx - 360, cy), CYAN, 2, al, ease_out((t - 0.5) / 0.6))
    # right: military systems (radar sweep)
    ar = a * ease_out((t - 1.3) / 0.8)
    rx = cx + 620
    for k in (70, 140, 210):
        fr.circle(rx, cy, k, RED, ar * 0.5, stroke=1.5)
    ang = t * 2.0
    fr.line((rx, cy), (rx + 210 * math.cos(ang), cy + 210 * math.sin(ang)), RED, 3, ar, glow=8)
    for j, (bx, by) in enumerate([(rx + 90, cy - 60), (rx - 120, cy + 40), (rx + 40, cy + 150)]):
        fr.circle(bx, by, 5, RED, ar * (0.4 + 0.6 * ((math.sin(t * 3 + j)) > 0)), glow=6)
    fr.label("MILITARY SYSTEMS", rx, cy + 300, 24, TEXT, ar, anchor="c")
    _arrow(fr, (cx + 90, cy), (cx + 360, cy), RED, 2, ar, ease_out((t - 1.3) / 0.6))


@template("split_choice")
def t_split(fr, t, dur, beat, P):
    a = window(t, 0, dur, 0.35)
    foc = P.get("focus")
    for side, x0 in (("left", W * 0.25), ("right", W * 0.75)):
        dim = 1.0 if foc in (None, side) else 0.28
        aa = a * dim
        if side == "left":
            server_icon(fr, x0 - 110, H / 2 - 190, 220, 300, TEXT, aa, lights=1, t=t)
            fr.label("BUY", x0, H / 2 + 190, 56, TEXT, aa, anchor="c", track=0.3)
            fr.text("Own the hardware · install it yourself", x0, H / 2 + 245, "sans", 26, DIM, aa, anchor="c")
        else:
            cloud_icon(fr, x0, H / 2 - 80, 150, CYAN, aa, 3)
            server_icon(fr, x0 - 60, H / 2 - 50, 120, 120, CYAN, aa * 0.8, lights=1, t=t + 1)
            fr.label("RENT", x0, H / 2 + 190, 56, CYAN if foc == "right" else TEXT, aa, anchor="c", track=0.3)
            fr.text("Pay to use someone else’s machines", x0, H / 2 + 245, "sans", 26, DIM, aa, anchor="c")
    fr.line((W / 2, 220), (W / 2, H - 220), GRID, 2, a)
    fr.text("or", W / 2, H / 2 + 10, "title_i", 60, DIM, a, anchor="c")


@template("data_moves")
def t_data_moves(fr, t, dur, beat, P):
    a = window(t, 0, dur, 0.4)
    rx, ry, rw, rh = W * 0.56, 170, 300, 660
    fr.rect(rx, ry, rw, rh, CYAN, a * 0.9, stroke=2.5, r=8)
    for k in range(10):
        fr.line((rx + 20, ry + 40 + k * 66), (rx + rw - 20, ry + 40 + k * 66), CYAN, 1, a * 0.4)
    # lock
    la = a * ease_out((t - 1.6) / 0.5)
    lx, ly = rx + rw / 2, ry + rh + 70
    fr.rect(lx - 28, ly - 16, 56, 44, TEXT, la, r=6)
    fr.path([(lx - 18, ly - 16), (lx - 18, ly - 36), (lx - 10, ly - 46), (lx + 10, ly - 46), (lx + 18, ly - 36), (lx + 18, ly - 16)], TEXT, 5, la)
    fr.label("THE CHIPS STAY", rx + rw + 70, ry + rh / 2 - 10, 34, TEXT, la)
    fr.label("IN THE RACK", rx + rw + 70, ry + rh / 2 + 40, 34, TEXT, la)
    # data packets streaming in from the left edge, and results streaming back out
    ad = a * ease_out((t - 0.2) / 0.5)
    for j in range(26):
        s = (t * 0.55 + j / 26) % 1.0
        x = -40 + s * (rx - (-40)); y = ry + 120 + (j * 97) % (rh - 240)
        fr.rect(x, y, 26, 8, CYAN, ad * (0.3 + 0.7 * s), r=3)
        fr.rect(x - 70 * s, y + 2, 70 * s, 4, CYAN, ad * 0.25 * s, r=2)
    fr.label("THE DATA MOVES", MARGIN + 40, ry + 60, 30, CYAN, ad)


@template("records")
def t_records(fr, t, dur, beat, P):
    a = window(t, 0, dur, 0.35)
    foc = P.get("focus")
    panels = [("shipping", "SHIPPING RECORD", AMBER, MARGIN, [("CONSIGNEE", "▇▇▇▇▇▇▇▇▇"), ("DESTINATION", "▇▇▇▇▇▇▇"), ("GOODS", "SERVER HARDWARE"),
                                                             ("DELIVERED", "▇▇▇▇-▇▇-▇▇")], "WHERE THE MACHINE WENT"),
              ("access", "ACCESS RECORDS", CYAN, W / 2 + 40, None, "WHO USED IT · FROM WHERE")]
    for key, head, rgb, x0, rows, cap in panels:
        dimv = 1.0 if foc in (None, key) else 0.3
        aa = a * dimv
        w_, h_ = W / 2 - MARGIN - 40, 600
        y0 = 210
        fr.rect(x0, y0, w_, h_, BG2, aa * 0.95, r=10); fr.rect(x0, y0, w_, h_, rgb, aa * 0.8, stroke=2, r=10)
        fr.label(head, x0 + 36, y0 + 60, 26, rgb, aa)
        if rows:
            for k, (kk, vv) in enumerate(rows):
                yy = y0 + 150 + k * 90
                ar = aa * ease_out((t - 0.3 - k * 0.2) / 0.5)
                fr.text(kk, x0 + 36, yy, "mono", 22, DIM, ar, track=0.1)
                fr.text(vv, x0 + 290, yy, "mono_m", 26, TEXT, ar)
                fr.line((x0 + 36, yy + 26), (x0 + w_ - 36, yy + 26), GRID, 1, ar)
        else:
            n = 12
            for k in range(n):
                yy = y0 + 130 + k * 36
                s = (t * 1.4 - k * 0.12)
                ar = aa * max(0.0, min(1.0, s))
                hh = (k * 37 + 11) % 24; mm = (k * 53 + 7) % 60
                fr.text(f"{hh:02d}:{mm:02d}:{(k * 17) % 60:02d}", x0 + 36, yy, "mono", 20, DIM, ar)
                fr.text("USER ▇▇▇▇▇", x0 + 200, yy, "mono", 20, TEXT, ar)
                fr.text("CONNECTED FROM  ???", x0 + 400, yy, "mono", 20, CYAN, ar)
        fr.text(cap, x0 + 36, y0 + h_ - 40, "sans_sb", 22, DIM, aa, track=0.1)


@template("structure")
def t_structure(fr, t, dur, beat, P):
    step = P.get("step", 1)
    a = window(t, 0, dur, 0.3)
    e = lambda k, d=0.0: a * (1.0 if step > k else ease_out((t - d) / 0.7))
    # layout
    alice = (MARGIN, 420, 400, 150); mega = (760, 420, 440, 150)
    origin = (760, 760, 440, 140); swift = (760, 120, 440, 140); client = (1400, 420, 400, 150)
    _node(fr, *alice, "ALICE HUANG", "From Shanghai’s investment world", e(0), TEXT, STEEL)
    _node(fr, *mega, "MEGASPEED", "Singapore", e(0, 0.3), TEXT, CYAN)
    _arrow(fr, (alice[0] + alice[2], 495), (mega[0], 495), TEXT, 2.5, e(0, 0.6), ease_out((t - 0.6) / 0.6) if step == 1 else 1)
    fr.text("TAKES CONTROL · 2023", (alice[0] + alice[2] + mega[0]) / 2, 470, "mono_m", 17, DIM, e(0, 0.9), anchor="c", track=0.08)
    if step >= 2:
        _node(fr, *origin, "ORIGINS", "Began as a subsidiary of a video game developer", e(1), TEXT, FAINT)
        _arrow(fr, (980, origin[1]), (980, mega[1] + mega[3]), FAINT, 2, e(1, 0.3))
        ab = e(1, 1.0)
        fr.rect(mega[0] + mega[2] - 236, mega[1] - 22, 220, 40, CYAN, ab, r=20)
        fr.text("NVIDIA CLOUD PARTNER", mega[0] + mega[2] - 126, mega[1] + 5, "sans_b", 15, BG, ab, anchor="c", track=0.06)
    if step >= 3:
        _node(fr, *swift, "SWIFTDATA", "Singapore · owner by the end of 2023", e(2), TEXT, AMBER)
        _arrow(fr, (980, swift[1] + swift[3]), (980, mega[1]), AMBER, 2.5, e(2, 0.4))
        fr.text("OWNS", 1000, 360, "mono_m", 17, AMBER, e(2, 0.6), track=0.1)
    if step >= 4:
        _node(fr, *client, "ALIBABA", "Named as a client for the project, according to the investor", e(3), TEXT, RED, dashed=True)
        _arrow(fr, (mega[0] + mega[2], 495), (client[0], 495), RED, 2, e(3, 0.3), dash=(8, 7))


@template("filings")
def t_filings(fr, t, dur, beat, P):
    step = P.get("step", 0)
    a = window(t, 0, dur, 0.3)
    x0, base = 620, 900
    fr.line((x0 - 60, base), (W - MARGIN, base), STEEL, 2, a)
    fr.label("TOTAL ASSETS · COMPANY FILINGS", x0 - 60, 170, 22, DIM, a)
    if step == 0:
        doc_icon(fr, W / 2 - 160, 300, 320, 420, PAPER, a * ease_out(t / 0.8), 10)
        return
    v1, v2 = 33e6, 3e9
    hmax = 640
    g1 = ease_out((t - 0.2) / 1.0); g2 = ease_out((t - 1.6) / 1.8)
    h1 = max(3, hmax * v1 / v2) * g1; h2 = hmax * g2
    bw = 260
    fr.rect(x0, base - h1, bw, h1, STEEL, a, r=2)
    fr.text("2023", x0 + bw / 2, base + 50, "mono_m", 30, DIM, a, anchor="c")
    fr.text(f"${33 * g1:.0f} MILLION", x0 + bw / 2, base - h1 - 26, "mono_b", 34, TEXT, a * g1, anchor="c")
    x2 = x0 + 520
    fr.rect(x2, base - h2, bw, h2, CYAN, a, r=2)
    fr.rect(x2, base - h2, bw, h2, CYAN, a * 0.4, r=2, blur=24)
    fr.text("2024", x2 + bw / 2, base + 50, "mono_m", 30, DIM, a, anchor="c")
    val = 33e6 + (v2 - 33e6) * g2
    txt = f"${val / 1e9:.1f} BILLION" if val >= 1e9 else f"${val / 1e6:.0f} MILLION"
    fr.text(txt, x2 + bw / 2, base - h2 - 26, "mono_b", 44, TEXT, a * min(1, g2 * 3), anchor="c", glow=6 if g2 > 0.95 else 0)
    am = a * ease_out((t - 3.4) / 0.6)
    fr.text("~90×", x2 + bw + 90, base - hmax / 2, "title", 120, CYAN, am)
    fr.text("in one year", x2 + bw + 96, base - hmax / 2 + 50, "sans", 26, DIM, am)


@template("headlines")
def t_headlines(fr, t, dur, beat, P):
    step = P.get("step", 1)
    a = window(t, 0, dur, 0.3)
    items = {
        1: ("U.S. authorities look into whether Megaspeed helped Chinese companies get access to controlled chips", "REPORTED BY THE NEW YORK TIMES · OCT 2025", STEEL),
        2: ("Singapore police confirm their own investigation into possible breaches of Singapore law", "SINGAPORE POLICE", STEEL),
        3: ("Megaspeed denies illicit activity involving chips", "MEGASPEED", TEXT),
        4: ("The suspected operation is made public", "THE NEW YORK TIMES · OCT 29", RED),
    }
    keys = [k for k in (1, 2, 3) if k <= step] if step <= 3 else [4]
    w_ = 1240; x = (W - w_) / 2
    y = 230
    for k in keys:
        newest = (k == keys[-1])
        ak = a * (ease_out(t / 0.7) if newest else 1.0) * (1.0 if newest else 0.45)
        dy = (1 - ease_out(t / 0.7)) * 40 if newest else 0
        h_ = headline_card(fr, x, y + dy, w_, items[k][0], None, items[k][1], ak, items[k][2])
        y += h_ + 30


@template("broadcast_frame")
def t_broadcast(fr, t, dur, beat, P):
    """Generic broadcast treatment drawn over the plate (no real channel branding)."""
    a = window(t, 0, dur, 0.25)
    if P.get("state") == "noise":
        r = np.random.default_rng(int(t * 24))
        for k in range(1400):
            x = r.uniform(0, W); y = r.uniform(0, H); g = r.uniform(80, 230)
            fr.rect(x, y, r.uniform(2, 8), 2, (g, g, g), a * 0.8)
        fr.label("TELEVISION FOOTAGE", W / 2, H / 2, 30, TEXT, a * (0.5 + 0.5 * math.sin(t * 9)), anchor="c", track=0.5)
        return
    for y in range(0, H, 4):
        fr.rect(0, y, W, 1.5, (0, 0, 0), a * 0.22)
    fr.rect(70, 70, W - 140, H - 140, TEXT, a * 0.5, stroke=1.5, r=4)
    fr.circle(140, 128, 9, RED, a * (0.5 + 0.5 * (math.sin(t * 6) > 0)))
    fr.label("TV FOOTAGE · TAIPEI", 164, 136, 20, TEXT, a)
    fr.text("2025-05-22", W - 140, H - 110, "mono_m", 26, TEXT, a * 0.9, anchor="r")


@template("compare_frames")
def t_compare(fr, t, dur, beat, P):
    a = window(t, 0, dur, 0.35)
    for k, (lab, x0) in enumerate((("TELEVISION FOOTAGE", 180), ("SEPARATE PHOTOGRAPH", 1000))):
        ak = a * ease_out((t - k * 0.4) / 0.6)
        fr.rect(x0, 250, 740, 420, BG2, ak, r=6); fr.rect(x0, 250, 740, 420, STEEL, ak, stroke=2, r=6)
        # abstract table scene: round table and empty chairs (no people)
        cx, cy = x0 + 370, 470
        fr.c.save(); fr.c.translate(cx, cy); fr.c.scale(1, 0.45)
        fr.circle(0, 0, 200, (60, 46, 36), ak); fr.circle(0, 0, 200, AMBER, ak * 0.5, stroke=2); fr.circle(0, 0, 70, (90, 70, 52), ak)
        fr.c.restore()
        for j in range(7):
            an = j / 7 * 2 * math.pi + 0.3
            fr.rect(cx + 250 * math.cos(an) - 22, cy + 112 * math.sin(an) - 44, 44, 60, (40, 44, 50), ak, r=8)
        fr.label(lab, x0, 715, 20, DIM, ak)
    am = a * ease_out((t - 1.4) / 0.6)
    for (p, q) in (((1000 + 370 + 240, 430), (180 + 370 + 240, 430)),):
        fr.circle(*p, 34, RED, am, stroke=3, glow=6); fr.circle(*q, 34, RED, am, stroke=3, glow=6)
        fr.path([q, ((p[0] + q[0]) / 2, 200), p], RED, 2, am, dash=(8, 8), progress=ease_out((t - 1.6) / 0.8))
    fr.label("MATCH", W / 2, 190, 24, RED, am, anchor="c")


@template("connection")
def t_connection(fr, t, dur, beat, P):
    a = window(t, 0, dur, 0.35)
    _node(fr, 260, 420, 420, 150, "NVIDIA", "Sells the chips", a, TEXT, CYAN)
    _node(fr, 1240, 420, 420, 150, "MEGASPEED", "Nvidia cloud partner", a, TEXT, CYAN)
    pr = ease_out((t - 0.4) / 1.0)
    fr.line((680, 495), (680 + (1240 - 680) * pr, 495), CYAN, 3, a, glow=6)
    fr.label("BUSINESS CONNECTION", W / 2, 470, 20, CYAN, a * pr, anchor="c")


@template("memo_redact")
def t_memo(fr, t, dur, beat, P):
    """The reported claim, set as an attributed pull-quote (never presented as the memo's own text)."""
    a = window(t, 0.2, dur, 0.4)
    x, y = MARGIN, H - 330
    fr.rect(0, y - 120, W, 360, (0, 0, 0), a * 0.55, blur=40)
    fr.label("REPORTED · ACCORDING TO PEOPLE BRIEFED ON THE INTELLIGENCE", x, y - 50, 18, RED, a)
    line = P.get("line", "")
    fr.text("“…" + line + "…”", x, y + 30, "quote", 58, TEXT, a, reveal=ease_out((t - 0.4) / 2.2))


@template("trace_vs_talk")
def t_trace(fr, t, dur, beat, P):
    a = window(t, 0, dur, 0.35)
    foc = P.get("focus")
    al = a * (1.0 if foc == "chip" else 0.3)
    pts = [(220, 760), (420, 620), (620, 700), (820, 520)]
    for k, (x, y) in enumerate(pts):
        fr.circle(x, y, 8, AMBER, al, glow=6)
        fr.text(["FACTORY", "PORT", "WAREHOUSE", "RACK"][k], x, y + 46, "mono_m", 18, DIM, al, anchor="c", track=0.1)
    fr.path(pts, AMBER, 2.5, al, dash=(10, 8), progress=ease_in_out(t / 2.0) if foc == "chip" else 1)
    s = ease_in_out(t / 2.0) if foc == "chip" else 1
    seg = min(int(s * 3), 2); f = s * 3 - seg
    cx = pts[seg][0] + (pts[seg + 1][0] - pts[seg][0]) * f; cy = pts[seg][1] + (pts[seg + 1][1] - pts[seg][1]) * f
    chip_icon(fr, cx, cy - 60, 30, CYAN, al, glow=8)
    fr.label("TRACEABLE", 520, 330, 40, AMBER, al, anchor="c", track=0.3)
    fr.text("A chip leaves a paper trail", 520, 380, "sans", 26, DIM, al, anchor="c")
    ar = a * (1.0 if foc == "talk" else 0.3)
    bx = 1400
    for side in (-1, 1):
        x = bx + side * 200
        fr.rect(x - 90, 560, 180, 120, BG2, ar, r=24); fr.rect(x - 90, 560, 180, 120, TEXT, ar, stroke=2, r=24)
        for k in range(14):
            hh = 10 + 30 * abs(math.sin(t * 6 + k * 0.7 + side))
            fr.rect(x - 70 + k * 10, 620 - hh / 2, 5, hh, TEXT, ar * 0.8, r=2)
    for j in range(16):
        s = (t * 0.6 + j / 16) % 1.0
        fr.circle(bx - 110 + 220 * s, 520 - math.sin(s * math.pi) * 90, 3, CYAN, ar * math.sin(s * math.pi))
    fr.label("A CONVERSATION", bx, 330, 40, CYAN, ar, anchor="c", track=0.3)
    fr.text("Plans, requests, timing — no shipping record", bx, 380, "sans", 26, DIM, ar, anchor="c")


@template("big_number")
def t_big(fr, t, dur, beat, P):
    a = window(t, 0, dur, 0.35)
    g = ease_out((t - 0.2) / 1.6)
    v = P["value"] * g
    fr.text(f"{P.get('prefix', '')}{v:.1f}", W / 2 - 30, H / 2 + 60, "title", 300, TEXT, a, anchor="r", glow=0)
    fr.text(P["unit"], W / 2 + 10, H / 2 + 50, "sans_l", 110, TEXT, a, track=0.06)
    fr.line((W / 2 - 420, H / 2 + 110), (W / 2 - 420 + 840 * g, H / 2 + 110), RED, 3, a)
    fr.text("Charge reported by Nvidia · H20", W / 2, H / 2 + 170, "sans", 28, DIM, a * g, anchor="c")


@template("timeline_bets")
def t_bets(fr, t, dur, beat, P):
    a = window(t, 0, dur, 0.35)
    gx, gy = 640, H / 2
    _node(fr, gx - 440, gy - 75, 380, 150, "WASHINGTON", "Clears a chip for sale — or doesn’t", a, TEXT, STEEL)
    flip = (math.sin(t * 1.3) > 0)
    for k, (lab, yy, rgb) in enumerate((("CLEARED", gy - 200, CYAN), ("BLOCKED", gy + 200, RED))):
        on = (k == 0) == flip
        fr.path([(gx - 60, gy), (gx + 200, gy), (gx + 360, yy)], rgb, 3 if on else 1.5, a * (1 if on else 0.3), glow=6 if on else 0)
        fr.label(lab, gx + 400, yy + 10, 30, rgb, a * (1 if on else 0.35))
        fr.text("Where billions get spent", gx + 400, yy + 50, "sans", 24, DIM, a * (1 if on else 0.35))
        if on:
            for j in range(10):
                s = (t * 0.7 + j / 10) % 1.0
                px = gx - 60 + s * 420; py = gy + (yy - gy) * max(0, (s - 0.62) / 0.38)
                fr.text("$", px, py + 10, "mono_b", 26, rgb, a * 0.9, anchor="c")


@template("statements")
def t_statements(fr, t, dur, beat, P):
    who = P.get("who")
    a = window(t, 0, dur, 0.35)
    content = {
        "NVIDIA": ("NVIDIA SAYS", ["Its CEO routinely meets with customers.", "Its regional cloud customers receive ordinary business information."], CYAN),
        "CHINA’S FOREIGN MINISTRY": ("CHINA’S FOREIGN MINISTRY", ["Rejects the spying allegation."], RED),
        "UNVERIFIED": ("NOT INDEPENDENTLY VERIFIED", ["Reuters was unable to verify the allegation independently.", "Reuters and the Financial Times were unable to reach Alice Huang for comment."], STEEL),
        "THE WHITE HOUSE": ("PRESIDENT TRUMP SAYS", ["The FBI is looking into the matter."], AMBER),
    }[who]
    head, lines, rgb = content
    x = MARGIN + 120; y = 330
    fr.rect(x - 60, y - 60, 6, 120 + len(lines) * 140, rgb, a)
    fr.label(head, x, y, 30, rgb, a, track=0.3)
    for k, l in enumerate(lines):
        for j, ll in enumerate(fr.wrap(l, "serif", 58, W - x - MARGIN - 100)):
            fr.text(ll, x, y + 110 + k * 150 + j * 68, "serif", 58, TEXT, a * ease_out((t - 0.3 - k * 0.6) / 0.6))


@template("letter")
def t_letter(fr, t, dur, beat, P):
    a = window(t, 0, dur, 0.4)
    x, y, w_, h_ = W / 2 - 330, 140 + (1 - ease_out(t / 0.9)) * 60, 660, 860
    _paper(fr, x, y, w_, h_, a, angle=2)
    fr.text("CONGRESS OF THE UNITED STATES", x + w_ / 2, y + 90, "serif_b", 26, INK, a, anchor="c", track=0.06)
    fr.text("Three House committee chairs", x + w_ / 2, y + 126, "serif", 22, INK, a * 0.8, anchor="c")
    fr.line((x + 60, y + 156), (x + w_ - 60, y + 156), INK, 1.2, a * 0.5)
    _redaction_lines(fr, x + 60, y + 220, w_ - 120, 9, a, rng_seed=8, redact_p=0.0)
    hy = y + 560
    fr.rect(x + 50, hy - 40, w_ - 100, 110, AMBER, a * 0.22 * ease_out((t - 1.0) / 0.6), r=4)
    fr.text("Request: a private briefing", x + 70, hy, "serif_b", 30, INK, a)
    fr.text("Contacts with Alice Huang · protection from espionage", x + 70, hy + 44, "serif", 22, INK, a)
    fr.c.restore()


@template("calendar")
def t_calendar(fr, t, dur, beat, P):
    import calendar as cal_
    a = window(t, 0, dur, 0.35)
    x0, y0, cw, ch = 520, 250, 126, 110
    fr.text("November 2026", x0, y0 - 40, "title", 64, TEXT, a)
    for k, d in enumerate("SMTWTFS"):
        fr.text(d, x0 + k * cw + cw / 2, y0 + 30, "mono_m", 20, DIM, a, anchor="c")
    weeks = cal_.Calendar(6).monthdayscalendar(2026, 11)
    marks = {18: ("BRIEFING REQUESTED", RED)}
    if P.get("mark") == "email":
        marks = {4: ("LETTER DATED", STEEL), 8: ("THE EMAIL", AMBER), 18: ("BRIEFING REQUESTED", RED)}
    for r, wk in enumerate(weeks):
        for c, d in enumerate(wk):
            if not d:
                continue
            x = x0 + c * cw; y = y0 + 60 + r * ch
            fr.rect(x + 4, y, cw - 8, ch - 8, BG2, a, r=6)
            fr.text(str(d), x + 18, y + 38, "mono_m", 26, TEXT if d in marks else DIM, a)
            if d in marks:
                lab, rgb = marks[d]
                am = a * ease_out((t - 0.5 - list(marks).index(d) * 0.6) / 0.5)
                fr.rect(x + 4, y, cw - 8, ch - 8, rgb, am, stroke=3, r=6)
                fr.circle(x + cw / 2, y + ch / 2 - 4, 46, rgb, am * 0.9, stroke=3, glow=6)
    if P.get("mark") == "email":
        am = a * ease_out((t - 1.6) / 0.6)
        ax = x0 + 3 * cw + cw / 2; bx = x0 + 0 * cw + cw / 2; yA = y0 + 60 + 0 * ch + ch / 2; yB = y0 + 60 + 1 * ch + ch / 2
        fr.path([(ax, yA + 40), (ax - 110, yB - 10), (bx + 50, yB)], AMBER, 2.5, am, dash=(8, 6), progress=ease_out((t - 1.6) / 0.8))
        fr.label("4 DAYS", ax - 60, yB + 6, 18, AMBER, am, anchor="c")
    # legend, one row per mark, right of the grid
    for k, (d, (lab, rgb)) in enumerate(marks.items()):
        am = a * ease_out((t - 0.8 - k * 0.6) / 0.5)
        ly = y0 + 110 + k * 70
        fr.circle(x0 + 7 * cw + 56, ly - 8, 10, rgb, am)
        fr.text(f"NOV {d}", x0 + 7 * cw + 80, ly, "mono_m", 22, rgb, am)
        fr.label(lab, x0 + 7 * cw + 190, ly, 20, TEXT, am)


@template("name_reveal")
def t_name(fr, t, dur, beat, P):
    a = window(t, 0, dur, 0.35)
    fr.label("HIS MESSAGE NAMES NO ONE", W / 2, 330, 24, DIM, a, anchor="c", track=0.4)
    g = ease_in_out((t - 0.8) / 1.0)
    x, y, w_ = W / 2 - 380, 430, 760
    fr.rect(x + w_ * g, y, w_ * (1 - g), 140, (30, 34, 40), a, r=4)
    fr.text("Alice Huang", W / 2, y + 112, "title", 130, TEXT, a * g, anchor="c")
    fr.text("Identified by The New York Times and the Financial Times", W / 2, y + 230, "sans", 28, DIM, a * ease_out((t - 1.8) / 0.6), anchor="c")


@template("statement_quote")
def t_stq(fr, t, dur, beat, P):
    a = window(t, 0.3, dur, 0.4)
    fr.rect(0, 0, W, H, (0, 0, 0), a * 0.35)
    fr.label("NVIDIA BOARD OF DIRECTORS", W / 2, 360, 22, DIM, a, anchor="c", track=0.4)
    for k, l in enumerate(fr.wrap("“" + P["text"] + "”", "quote", 70, W - 2 * MARGIN - 300)):
        fr.text(l, W / 2, 500 + k * 90, "quote", 70, TEXT, a, anchor="c", reveal=ease_out((t - 0.5 - k * 0.5) / 1.4))


@template("complaint_doc")
def t_complaint(fr, t, dur, beat, P):
    a = window(t, 0, dur, 0.4)
    x, y, w_, h_ = W / 2 + 80, 120 + (1 - ease_out(t / 0.9)) * 70, 680, 880
    _paper(fr, x, y, w_, h_, a, angle=-2)
    fr.text("SHAREHOLDER COMPLAINT", x + w_ / 2, y + 90, "serif_b", 30, INK, a, anchor="c", track=0.08)
    fr.text("against Nvidia and its CEO", x + w_ / 2, y + 128, "serif", 24, INK, a * 0.8, anchor="c")
    fr.line((x + 60, y + 160), (x + w_ - 60, y + 160), INK, 1.2, a * 0.5)
    _redaction_lines(fr, x + 60, y + 220, w_ - 120, 8, a, rng_seed=11, redact_p=0.0)
    hy = y + 540
    fr.rect(x + 50, hy - 40, w_ - 100, 110, RED, a * 0.18 * ease_out((t - 1.0) / 0.6), r=4)
    fr.text("Alleges investors were misled", x + 70, hy, "serif_b", 30, INK, a)
    fr.text("about the risks of dealings with Megaspeed", x + 70, hy + 44, "serif", 22, INK, a)
    fr.c.restore()
    fr.label("ALLEGATIONS · NOW BEFORE A COURT", MARGIN, H / 2, 26, TEXT, a)


@template("open_questions")
def t_open(fr, t, dur, beat, P):
    step = P.get("step", 1)
    a = window(t, 0, dur, 0.3)
    rows = [("Public finding that Megaspeed broke export rules", "NONE"),
            ("Nvidia board’s conclusions", "NOT PUBLISHED"),
            ("Evidence behind the reported intelligence assessment", "NOT PUBLIC")]
    fr.label("AS OF NOVEMBER 11, 2026", MARGIN, 240, 24, DIM, a, track=0.35)
    for k, (q, status) in enumerate(rows):
        if k + 1 > step:
            break
        newest = (k + 1 == step)
        ak = a * (ease_out(t / 0.6) if newest else 0.6)
        y = 380 + k * 170
        fr.line((MARGIN, y + 60), (W - MARGIN, y + 60), GRID, 1.5, ak)
        fr.text(q, MARGIN, y, "serif", 46, TEXT, ak)
        fr.rect(W - MARGIN - 330, y - 44, 330, 60, RED if newest else STEEL, ak, stroke=2, r=30)
        fr.label(status, W - MARGIN - 165, y - 4, 22, RED if newest else STEEL, ak, anchor="c")
