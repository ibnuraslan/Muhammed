"""Romand map card: the kit_v1 `map` template, generalised (data file, highlighted country, minor cities) and fed with
France / Switzerland outlines (Natural Earth 10m via world-atlas 2.0.2, public domain; data/france_alps_10m.json).
Same look and motion as kit_v1 map: card scales in, pin drops and pulses, the dashed yellow route draws leg by leg.
    import rmap; fr = rmap.map_fr(t, route=[...], bbox=(lon0, lat0, lon1, lat1), label="...")"""
import os, json, math
from PIL import Image, ImageDraw, ImageChops
import seldom_kit as K
from seldom_kit import (Frame, in_out, seg, layer, fade, font, draw_text, poly_draw, poly_point, clamp, out_cubic, out_back,
                        glow, shadow, grain, with_alpha, W, H, YEL, WHITE, GREY, INK)
HERE = os.path.dirname(os.path.abspath(__file__))
GEO = json.load(open(os.path.join(HERE, "data", "france_alps_10m.json")))
CITIES = [(6.1432, 46.2044, "GENEVA"), (4.8357, 45.7640, "LYON"), (5.2251, 46.2052, "BOURG-EN-BRESSE"), (6.0241, 47.2378, "BESANCON"),
          (5.9278, 46.5662, "LONS-LE-SAUNIER"), (6.6323, 46.5197, "LAUSANNE"), (5.0415, 47.3220, "DIJON"), (2.3522, 48.8566, "PARIS"),
          (1.9093, 47.9029, "ORLEANS"), (1.6747, 46.8114, "CHATEAUROUX"), (5.7245, 45.1885, "GRENOBLE")]


def map_fr(t, route=((6.0942, 46.2550, "PREVESSIN-MOENS"), (6.1340, 46.2327, "GENEVA (WHO)", "r")), pin=0,
           bbox=(5.2, 45.75, 7.0, 46.75), label="PAYS DE GEX · FRANCE / SWITZERLAND", highlight=("France",), route_t=(1.6, 3.6),
           legs=None, cities=None, dur=6.5, fig="FIG. 01"):
    fr = Frame()
    fr.bg = dict(blur=6 * in_out(seg(t, 0.0, 0.6)), dim=0.7 * in_out(seg(t, 0.0, 0.6)) * (1 - in_out(seg(t, dur - 0.4, dur))))
    mw, mh = 1160, 760; mx0, my0 = (W - mw) / 2, (H - mh) / 2 + 10
    lon0, lat0, lon1, lat1 = bbox
    k = math.cos(math.radians((lat0 + lat1) / 2))
    s = min(mw / ((lon1 - lon0) * k), mh / (lat1 - lat0))
    ox = mx0 + (mw - (lon1 - lon0) * k * s) / 2; oy = my0 + (mh - (lat1 - lat0) * s) / 2

    def P(lon, lat):
        return (ox + (lon - lon0) * k * s, oy + (lat1 - lat) * s)
    M = layer(); dm = ImageDraw.Draw(M)
    dm.rectangle([mx0 - 20, my0 - 20, mx0 + mw + 20, my0 + mh + 20], fill=(16, 14, 10, 235))
    for name, rings in GEO.items():
        for r in rings:
            pts = [P(x, y) for x, y in r]
            if name in highlight:
                dm.polygon(pts, fill=(30, 27, 18, 255))
            dm.line(pts, fill=(YEL + (200,)) if name in highlight else (120, 112, 96, 160), width=2 if name in highlight else 1)
    mk = Image.new("L", (W, H), 0); ImageDraw.Draw(mk).rectangle([mx0 - 20, my0 - 20, mx0 + mw + 20, my0 + mh + 20], fill=255)
    M.putalpha(ImageChops.multiply(M.split()[3], mk))
    ImageDraw.Draw(M).rectangle([mx0 - 20, my0 - 20, mx0 + mw + 20, my0 + mh + 20], outline=WHITE + (170,), width=2)
    names = {st[2] for st in route}
    for (lo, la, nm) in (cities if cities is not None else CITIES):
        if not (lon0 < lo < lon1 and lat0 < la < lat1) or any(nm.split(" ")[0] in n for n in names):
            continue
        q = P(lo, la); ca = int(170 * fade(t, 0.5, 1.2))
        dm.ellipse([q[0] - 3, q[1] - 3, q[0] + 3, q[1] + 3], fill=GREY + (ca,))
        draw_text(M, (q[0] + 10, q[1] + 6), nm, font("label_light", 20), GREY + (ca,), tracking=3)
    pts = [P(st[0], st[1]) for st in route]
    ll = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    if legs is None and ll:
        T0, T1 = route_t; acc = 0.0; legs = []
        for l in ll:
            legs.append((T0 + (T1 - T0) * acc / sum(ll), T0 + (T1 - T0) * (acc + l) / sum(ll))); acc += l
    legs = legs or []
    dmm = ImageDraw.Draw(M); arrive = [legs[0][0] if legs else 1.0] + [e for _, e in legs]
    for i, (a0, a1) in enumerate(legs):
        lp = clamp((t - a0) / max(a1 - a0, 1e-6))
        poly_draw(M, [pts[i], pts[i + 1]], lp, YEL + (255,), 4, dash=(16, 10))
        if 0 < lp < 1:
            hx, hy = poly_point([pts[i], pts[i + 1]], lp)
            dmm.ellipse([hx - 7, hy - 7, hx + 7, hy + 7], fill=WHITE + (255,))
    for i, st in enumerate(route):
        lo, la, nm = st[:3]; side = st[3] if len(st) > 3 else "r"
        q = P(lo, la); ta = arrive[i] if i else 1.0
        tx, anc = (q[0] + 22, "ls") if side == "r" else (q[0] - 22, "rs")
        lpv = out_cubic(seg(t, ta, ta + 0.5))
        if i and nm and lpv > 0:
            kk = out_back(seg(t, ta, ta + 0.3)); r = 7 * kk
            dmm.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=YEL + (255,))
        if lpv > 0 and nm:
            draw_text(M, (tx, q[1] - 14), nm, font("label", 30), WHITE + (int(255 * lpv),), tracking=3, anchor=anc)
            draw_text(M, (tx, q[1] + 14), f"{la:.4f}°N  {lo:.4f}°E", font("plex", 16), GREY + (int(230 * lpv),), tracking=1, anchor=anc)
    q = P(route[pin][0], route[pin][1]); pp = out_back(seg(t, 0.8, 1.2))
    if pp > 0:
        py = q[1] - 50 * (1 - pp)
        dmm.ellipse([q[0] - 11, py - 11, q[0] + 11, py + 11], fill=YEL + (255,)); dmm.ellipse([q[0] - 4, py - 4, q[0] + 4, py + 4], fill=INK + (255,))
        if t > 1.2:
            pr = ((t - 1.2) * 1.1) % 1.0; rr = 12 + 40 * pr
            dmm.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], outline=YEL + (int(220 * (1 - pr)),), width=2)
    draw_text(M, (mx0, my0 - 34), label, font("label", 28), WHITE + (230,), tracking=5)
    draw_text(M, (mx0 + mw, my0 - 34), fig, font("plex", 18), YEL + (220,), tracking=3, anchor="rs")
    p = out_cubic(seg(t, 0.0, 0.9)); sc = 0.94 + 0.06 * p
    Mi = M.resize((int(W * sc), int(H * sc)), Image.BICUBIC)
    L = layer(); L.alpha_composite(Mi, dest=(int((W - Mi.width) / 2), int((H - Mi.height) / 2)))
    a = p * (1 - in_out(seg(t, dur - 0.35, dur)))
    fr.rgba = grain(with_alpha(shadow(glow(L, 10, 0.25), (0, 10), 20, 0.8), a), t, 0.06)
    return fr


K.TEMPLATES["map_fr"] = map_fr
