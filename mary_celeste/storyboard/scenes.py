"""Scene builders: each takes a Canvas and keyword params from the shot list."""
from sketch import Canvas, Cam, W, H


def put(c, cam, X, Z, h=1.75, Y=0.0, **kw):
    x, yf = cam.p(X, Y, Z)
    c.fig(x / W, yf / H, cam.scale(Z) * h / H, **kw)


def figs(c, cam, people):
    for p in sorted(people or [], key=lambda q: -q.get("Z", 3)):
        q = dict(p)
        X, Z = q.pop("X", 0), q.pop("Z", 3)
        h = q.pop("h", 1.75)
        Y = q.pop("Y", 0.0)
        put(c, cam, X, Z, h=h, Y=Y, **q)


def sc_sea(c, hy=0.5, ships=(), boats=(), island=None, rock=None, rain=False, clouds=True, sky=(215, 170),
           sea=(135, 60), fg=None, people=(), fog=0, coast=None, sun=None):
    c.sky_sea(hy=hy, sky=sky, sea=sea, fog=fog)
    if sun:
        c.ell(sun[0] * W, sun[1] * H, 70, 70, 250)
    if clouds:
        c.clouds(n=10, tone=min(255, sky[0] + 20), y0=0.04, y1=hy - 0.12)
    if island:
        c.island(island[0], hy, island[1], island[2], tone=island[3] if len(island) > 3 else 100)
    if rock:
        c.rock_gib(rock[0], hy, rock[1], tone=rock[2] if len(rock) > 2 else 110)
    if coast:
        c.island(coast[0], hy, coast[1], coast[2], tone=coast[3])
    for s in ships:
        s = dict(s)
        c.ship(s.pop("x"), s.pop("y", hy + 0.01), s.pop("L"), **s)
    for b in boats:
        b = dict(b)
        c.small_boat(b.pop("x"), b.pop("y"), b.pop("L"), **b)
    if fg == "rail":
        c.poly([(0, H * 0.80), (W, H * 0.74), (W, H), (0, H)], 55)
        c.line([(0, H * 0.80), (W, H * 0.74)], 160, 14)
    elif fg == "bow":
        c.poly([(W * 0.2, H), (W * 0.5, H * 0.72), (W * 0.8, H)], 50)
        c.line([(W * 0.5, H * 0.72), (W * 0.62, H * 0.40)], 45, 16)
    elif fg == "gap":
        c.poly([(0, H * 0.70), (W * 0.30, H * 0.66), (W * 0.30, H), (0, H)], 60)
        c.poly([(W * 0.70, H * 0.66), (W, H * 0.62), (W, H), (W * 0.70, H)], 68)
        c.line([(0, H * 0.70), (W * 0.30, H * 0.66)], 170, 14)
        c.line([(W * 0.70, H * 0.66), (W, H * 0.62)], 170, 14)
        c.poly([(W * 0.30, H * 0.86), (W * 0.70, H * 0.86), (W * 0.75, H), (W * 0.25, H)], 120)
    for p in people:
        p = dict(p)
        c.fig(p.pop("x"), p.pop("y"), p.pop("h"), **p)
    if rain:
        c.rain()


def sc_hull(c, boat=True, climber=True, sky=(205, 170)):
    c.sky_sea(hy=0.30, sky=sky, sea=(120, 55), waves=True)
    c.poly([(W * 0.0, H * 0.05), (W * 1.0, H * 0.18), (W * 1.0, H * 0.82), (0, H * 0.74)], 52)
    for k in range(12):
        c.line([(0, H * (0.1 + k * 0.055)), (W, H * (0.22 + k * 0.05))], 40, 3)
    c.line([(0, H * 0.05), (W, H * 0.18)], 170, 16)
    c.poly([(0, H * 0.74), (W, H * 0.82), (W, H * 0.86), (0, H * 0.79)], 120)
    if boat:
        c.small_boat(0.55, 0.93, 0.6, people=2, tone=40)
    if climber:
        c.fig(0.46, 0.66, 0.40, view="back", pose="stand", hat="cap", arms=[(-1, -0.05, -0.36), (1, 0.06, -0.30)], tone=30)


def sc_deck(c, cam=None, people=(), **kw):
    cam = cam or Cam(hz=0.42, camH=1.5)
    if isinstance(cam, dict):
        cam = Cam(**cam)
    c.deck(cam, **kw)
    figs(c, cam, people)


def sc_cabin(c, cam=None, w=3.2, d=4.2, bunk=True, wet=True, hollow=False, table=True, slate=False, logbook=False,
             water=False, skylight=True, lamp=False, people=(), legend=False, coats=False, organ=False, chest=False,
             beams=True, port=False):
    cam = cam or Cam(hz=0.45, camH=1.45)
    if isinstance(cam, dict):
        cam = Cam(**cam)
    c.room(cam, w=w, h=2.0, d=d, beams=beams)
    if port:
        p = cam.p(-w / 2, 1.35, d * 0.55)
        c.ell(p[0] + 8, p[1], 30, 46, 235)
    if bunk:
        c.bunk(cam, -w / 2, -w / 2 + 1.0, 1.8, d - 0.2, wet=wet, hollow=hollow)
    if chest:
        c.box(cam, w / 2 - 0.8, w / 2 - 0.1, 0, 0.5, d - 1.2, d - 0.4, front=80, side=60, top=110)
    if organ:
        c.box(cam, w / 2 - 0.9, w / 2 - 0.1, 0, 0.95, d - 0.7, d - 0.2, front=75, side=55, top=120)
    if coats:
        p = cam.p(w / 2 - 0.1, 1.3, d * 0.5)
        c.prop("coats", p[0] / W - 0.06, p[1] / H, 0.12)
    if table:
        c.table(cam, -0.4, 0.8, 1.4, 2.4, tone=130)
        if slate:
            a = cam.p(-0.05, 0.76, 1.6); b = cam.p(0.45, 0.76, 2.0)
            c.poly([a, (b[0], a[1]), b, (a[0], b[1])], 30)
        if logbook:
            a = cam.p(0.2, 0.76, 1.9); b = cam.p(0.65, 0.76, 2.2)
            c.poly([a, (b[0], a[1]), b, (a[0], b[1])], 215)
        if legend:
            for X, Z in ((-0.1, 1.7), (0.4, 1.9), (0.2, 2.2)):
                p = cam.p(X, 0.78, Z)
                c.ell(p[0], p[1], 50, 18, 225)
                c.light_shaft([(p[0] - 20, p[1] - 140), (p[0] + 20, p[1] - 140)], [(p[0] - 10, p[1] - 20), (p[0] + 10, p[1] - 20)], 50)
    if water:
        c.water_floor(cam, w, d, 0.08, tone=135)
    if skylight:
        a, b = cam.p(-0.5, 2.0, 2.0), cam.p(0.5, 2.0, 2.6)
        c.light_shaft([(a[0], a[1]), (b[0], a[1])], [(a[0] - 120, H * 0.95), (b[0] + 60, H * 0.95)], 70)
    if lamp:
        p = cam.p(0.2, 1.7, 2.0)
        c.ell(p[0], p[1], 22, 30, 255)
        c.light_shaft([(p[0] - 30, p[1]), (p[0] + 30, p[1])], [(p[0] - 500, H), (p[0] + 500, H)], 45)
    figs(c, cam, people)


def sc_galley(c, people=(), water=True, stove_off=True):
    cam = Cam(hz=0.5, camH=0.9)
    c.room(cam, w=2.4, h=1.9, d=3.0, beams=True)
    sx = 0.15 if stove_off else 0.6
    c.box(cam, sx, sx + 0.8, 0, 0.8, 2.1, 2.7, front=45, side=35, top=70)
    c.line([cam.p(sx + 0.4, 0.8, 2.4), cam.p(sx + 0.45, 1.5, 2.45)], 40, 18)
    c.line([cam.p(0.6 + 0.4, 1.6, 2.7), cam.p(1.0, 1.9, 2.7)], 40, 18)
    if water:
        c.water_floor(cam, 2.4, 3.0, 0.22, tone=140)
    c.box(cam, -1.4, 1.4, 0, 0.3, 0.3, 0.45, front=150, side=120, top=170)  # door lip/coaming
    c.poly([cam.p(-1.4, 0, 0.3), cam.p(-0.7, 0, 0.3), cam.p(-0.7, 1.9, 0.3), cam.p(-1.4, 1.9, 0.3)], 30)
    c.poly([cam.p(0.7, 0, 0.3), cam.p(1.4, 0, 0.3), cam.p(1.4, 1.9, 0.3), cam.p(0.7, 1.9, 0.3)], 30)
    figs(c, cam, people)


def sc_hold(c, water=None, lantern=False, people=(), vapor=False, light=True):
    c.grad((0, 0, W, H), 40, 15)
    c.barrel_stack(0.0, 0.1, 1.05, 0.95, 0.075, tone=85)
    if water is not None:
        c.poly([(0, water * H), (W, water * H - 10), (W, H), (0, H)], 60)
        for i in range(30):
            x = c.rng.random() * W
            c.line([(x, water * H + c.rng.random() * 80), (x + 90, water * H + c.rng.random() * 80)], 110, 3)
    if vapor:
        def draw(l, m):
            for i in range(14):
                x, y = c.rng.random() * W, H * (0.6 + c.rng.random() * 0.35)
                l.ellipse([x - 250, y - 50, x + 250, y + 50], fill=170)
                m.ellipse([x - 250, y - 50, x + 250, y + 50], fill=90)
        c.blur_layer(draw, 45)
    if lantern:
        c.ell(W * 0.55, H * 0.35, 26, 36, 255)
        c.light_shaft([(W * 0.53, H * 0.33), (W * 0.57, H * 0.33)], [(W * 0.2, H), (W * 0.9, H)], 60)
    if light:
        c.light_shaft([(W * 0.42, 0), (W * 0.58, 0)], [(W * 0.30, H), (W * 0.62, H)], 55)
    for p in people:
        p = dict(p)
        c.fig(p.pop("x"), p.pop("y"), p.pop("h"), **p)


def sc_xray(c, water=0.0, barrels=True, rod=False, pumps=True, vapor=False, seep=False, lantern=False):
    """Side cutaway of the brigantine as a white maquette (explainer 3D)."""
    c.grad((0, 0, W, H), 235, 200)
    c.poly([(0, H * 0.62), (W, H * 0.62), (W, H), (0, H)], 175)
    X0, X1, Yd, Yk = W * 0.10, W * 0.90, H * 0.30, H * 0.80
    c.poly([(X0, Yd - 30), (X1, Yd - 60), (X1 - 60, Yk - 80), (W * 0.5, Yk), (X0 + 40, Yk - 60)], 205, outline=120, w=6)
    c.line([(X0, Yd), (X1, Yd - 25)], 120, 8)
    c.line([(W * 0.37, Yd), (W * 0.37, 0)], 150, 16)
    c.line([(W * 0.70, Yd - 18), (W * 0.70, 0)], 150, 16)
    c.poly([(W * 0.14, Yd + 10), (W * 0.30, Yd + 6), (W * 0.30, Yd + 120), (W * 0.15, Yd + 120)], 225, outline=140, w=4)
    if barrels:
        for row in range(4):
            for k in range(22):
                x = W * 0.33 + k * W * 0.024 + (row % 2) * W * 0.012
                y = H * 0.73 - row * H * 0.075
                if x < W * 0.86 - row * 20:
                    c.ell(x, y, W * 0.012, H * 0.036, 150, outline=110)
    if water:
        yw = Yk - water * (Yk - Yd)
        c.poly([(X0 + 60, yw), (X1 - 70, yw - 8), (X1 - 60, Yk - 80), (W * 0.5, Yk), (X0 + 40, Yk - 60)], 120)
    if pumps:
        c.line([(W * 0.62, Yd - 40), (W * 0.62, Yk - 10)], 90, 12)
        c.line([(W * 0.645, Yd - 40), (W * 0.645, Yk - 10)], 90, 12)
    if rod:
        c.line([(W * 0.60, Yd - 70), (W * 0.60, Yk - 20)], 40, 6)
    if vapor:
        def draw(l, m):
            for i in range(10):
                x, y = W * (0.35 + c.rng.random() * 0.45), H * (0.45 + c.rng.random() * 0.25)
                l.ellipse([x - 160, y - 30, x + 160, y + 30], fill=240)
                m.ellipse([x - 160, y - 30, x + 160, y + 30], fill=120)
        c.blur_layer(draw, 30)
    if seep:
        c.ell(W * 0.55, H * 0.72, 30, 20, 70)
    if lantern:
        c.ell(W * 0.50, H * 0.40, 20, 28, 255)


def sc_insert(c, prop="slate", side="l", arm_to=(0.5, 0.6), px=0.56, py=0.6, ps=0.22, surface=(150, 110),
              hat=None, female=False, bg=None, ots_tone=22, extra=None):
    if bg == "deck":
        for k in range(10):
            c.line([(0, H * (0.4 + k * 0.07)), (W, H * (0.35 + k * 0.07))], 90, 3)
        c.grad((0, 0, W, H * 0.3), 180, 140)
    elif bg == "sea":
        c.sky_sea(hy=0.35, sky=(220, 190), sea=(140, 70))
    else:
        c.grad((0, 0, W, H), surface[0] - 50, surface[0] - 70)
        c.poly([(0, H * 0.4), (W, H * 0.35), (W, H), (0, H)], surface[1])
    c.prop(prop, px, py, ps)
    if extra:
        for e in extra:
            e = dict(e)
            c.prop(e.pop("prop"), **e)
    if side:
        c.ots(side=side, arm_to=arm_to, hat=hat, female=female, tone=ots_tone)


def sc_face(c, bg="sea", view="3q_l", light="l", hat=None, female=False, child=False, s=0.42, cx=0.5, cy=0.42,
            expr="neutral", beard=False, second=None, rain=False, tone=40):
    if bg == "sea":
        c.sky_sea(hy=0.55, sky=(215, 175), sea=(130, 70))
        c.blur_all(14)
    elif bg == "cabin":
        c.grad((0, 0, W, H), 70, 35)
        c.light_shaft([(W * 0.2, 0), (W * 0.4, 0)], [(W * 0.1, H), (W * 0.5, H)], 60)
        c.blur_all(10)
    elif bg == "warm":
        c.grad((0, 0, W, H), 90, 30)
        c.ell(W * 0.82, H * 0.3, 40, 55, 255)
        c.blur_all(18)
    elif bg == "court":
        c.grad((0, 0, W, H), 110, 50)
        for k in range(4):
            c.poly([(W * (0.1 + k * 0.25), H * 0.1), (W * (0.18 + k * 0.25), H * 0.1), (W * (0.18 + k * 0.25), H * 0.5), (W * (0.1 + k * 0.25), H * 0.5)], 200)
        c.blur_all(20)
    elif bg == "storm":
        c.grad((0, 0, W, H), 80, 30)
        c.blur_all(10)
    elif bg == "dark":
        c.grad((0, 0, W, H), 30, 10)
    elif bg == "window":
        c.grad((0, 0, W, H), 90, 40)
        c.poly([(W * 0.6, H * 0.08), (W * 0.95, H * 0.08), (W * 0.95, H * 0.8), (W * 0.6, H * 0.8)], 225)
        c.line([(W * 0.775, H * 0.08), (W * 0.775, H * 0.8)], 60, 14)
        c.blur_all(12)
    if second:
        q = dict(second)
        c.bust(q.pop("cx"), q.pop("cy"), q.pop("s"), **q)
    c.bust(cx, cy, s, view=view, light=light, hat=hat, female=female, child=child, expr=expr, beard=beard, tone=tone)
    if rain:
        c.rain(500, 210)


def sc_pier(c, barrels=True, people=(), sky=(225, 195), ship=True, ramp=True):
    c.grad((0, 0, W, H * 0.55), sky[0], sky[1])
    for k in range(6):
        x = k * W * 0.18
        c.poly([(x, H * 0.55), (x, H * (0.22 + 0.08 * (k % 3))), (x + W * 0.16, H * (0.22 + 0.08 * (k % 3))), (x + W * 0.16, H * 0.55)], 150 - k * 8)
    c.grad((0, H * 0.55, W, H * 0.62), 120, 90)
    if ship:
        c.ship(0.38, 0.64, 0.62, face=-1, sails="bare", tone=45)
    c.poly([(0, H * 0.66), (W, H * 0.62), (W, H), (0, H)], 130)
    for k in range(12):
        c.line([(0, H * (0.68 + k * 0.03)), (W, H * (0.64 + k * 0.031))], 105, 2)
    if ramp:
        c.poly([(W * 0.55, H * 0.70), (W * 0.62, H * 0.70), (W * 0.50, H * 0.53), (W * 0.46, H * 0.53)], 110)
    if barrels:
        for i, (x, y, r) in enumerate([(0.72, 0.80, 0.05), (0.80, 0.83, 0.05), (0.88, 0.78, 0.05), (0.66, 0.90, 0.06), (0.92, 0.92, 0.07)]):
            c.barrel(x, y, r, tone=95, lying=(i % 2 == 0))
    for p in people:
        p = dict(p)
        c.fig(p.pop("x"), p.pop("y"), p.pop("h"), **p)


def sc_relief(c, pins=(), ripple=None, line=None, people=(), route=None, ots=None, model=None):
    """Oblique view of a physical sea-relief maquette (Azores to Gibraltar) on a table."""
    c.grad((0, 0, W, H), 40, 25)
    c.poly([(W * 0.0, H * 0.28), (W * 1.0, H * 0.22), (W * 1.0, H * 1.0), (0, H)], 120)
    for k in range(40):
        y = H * (0.3 + k * 0.018)
        c.line([(0, y), (W, y - 30)], 112 + (k % 3) * 6, 2)
    for (x, y, w, h) in [(0.18, 0.55, 0.05, 0.025), (0.24, 0.62, 0.035, 0.02), (0.12, 0.48, 0.03, 0.018)]:
        c.ell(x * W, y * H, w * W, h * H, 175)
    c.poly([(W * 0.86, H * 0.22), (W, H * 0.2), (W, H * 0.7), (W * 0.93, H * 0.6), (W * 0.9, H * 0.4)], 175)
    c.poly([(W * 0.84, H * 0.75), (W, H * 0.72), (W, H), (W * 0.80, H)], 170)
    if route:
        c.pencil_line(route, tone=40, w=5)
    if line:
        c.pencil_line(line, tone=30, w=6)
    for (x, y) in pins:
        c.pin(x, y)
    if ripple:
        c.ripple(ripple[0], ripple[1], 0.07)
    if model:
        c.ship(model[0], model[1], 0.05, face=1, sails="torn", tone=50)
    if ots:
        c.ots(side=ots.get("side", "l"), arm_to=ots.get("arm_to"), tone=20)
    for p in people:
        p = dict(p)
        c.fig(p.pop("x"), p.pop("y"), p.pop("h"), **p)
    c.light_shaft([(W * 0.4, 0), (W * 0.6, 0)], [(W * 0.15, H), (W * 0.85, H)], 40)


def sc_court(c, people=(), cam=None, piles=False):
    cam = cam or Cam(hz=0.42, camH=1.6)
    c.room(cam, w=9, h=5, d=12, wall=(120, 95), floor=(100, 70), ceil=70, beams=False)
    for k in range(4):
        X = -3 + k * 2
        c.poly([cam.p(X - 0.5, 2.2, 12), cam.p(X + 0.5, 2.2, 12), cam.p(X + 0.5, 4.2, 12), cam.p(X - 0.5, 4.2, 12)], 225)
    c.light_shaft([cam.p(-0.5, 4.2, 12), cam.p(0.5, 4.2, 12)], [(W * 0.2, H), (W * 0.6, H)], 50)
    c.box(cam, -2.5, 2.5, 0, 1.4, 10, 11, front=70, side=55, top=95)
    c.box(cam, -3.5, -1.0, 0, 0.9, 5, 5.6, front=80, side=60, top=110)
    c.box(cam, 1.0, 3.5, 0, 0.9, 5, 5.6, front=80, side=60, top=110)
    if piles:
        for k in range(5):
            c.box(cam, 1.4 + k * 0.1, 1.9 + k * 0.1, 0.9, 0.9 + 0.05 * (k + 1), 5.1, 5.4, front=210, side=190, top=230)
    figs(c, cam, people)


def sc_under(c, diver=True, hull=True):
    c.grad((0, 0, W, H), 170, 40)
    if hull:
        c.poly([(0, 0), (W, 0), (W, H * 0.25), (W * 0.5, H * 0.42), (0, H * 0.3)], 45)
        for k in range(10):
            c.line([(0, H * (0.03 * k)), (W, H * (0.025 * k))], 60, 3)
        c.line([(0, H * 0.3), (W * 0.5, H * 0.42), (W, H * 0.25)], 140, 10)
    c.light_shaft([(W * 0.6, 0), (W * 0.7, 0)], [(W * 0.4, H), (W * 0.65, H)], 50)
    if diver:
        c.fig(0.42, 0.95, 0.55, view="3q_r", hat="helmet", tone=60, arms=[(-1, -0.05, 0.3), (1, 0.15, -0.28)])
        c.line([(W * 0.42, H * 0.38), (W * 0.5, 0)], 80, 5)
    for i in range(30):
        c.ell(W * (0.44 + c.rng.random() * 0.05), H * (0.05 + c.rng.random() * 0.35), 6, 6, 220)


def sc_lab(c, people=(), sword=True):
    cam = Cam(hz=0.45, camH=1.5)
    c.room(cam, w=4, h=2.8, d=4, wall=(140, 110), floor=(90, 70), beams=False)
    c.poly([cam.p(-1.8, 1.1, 4), cam.p(-0.4, 1.1, 4), cam.p(-0.4, 2.4, 4), cam.p(-1.8, 2.4, 4)], 235)
    c.light_shaft([cam.p(-1.8, 2.4, 4), cam.p(-0.4, 2.4, 4)], [(W * 0.15, H), (W * 0.55, H)], 55)
    c.table(cam, -1.6, 1.6, 1.8, 2.6, y=0.9, tone=140)
    for k in range(5):
        p = cam.p(-1.0 + k * 0.3, 0.9, 2.1)
        c.d.rounded_rectangle([p[0] - 10, p[1] - 70, p[0] + 10, p[1]], radius=8, fill=215)
    if sword:
        c.line([cam.p(0.2, 0.92, 2.0), cam.p(1.4, 0.92, 2.2)], 200, 8)
    figs(c, cam, people)


def sc_modern(c, people=(), parts=True, docs=True):
    cam = Cam(hz=0.45, camH=1.3)
    c.room(cam, w=4.5, h=2.7, d=4.5, wall=(110, 85), floor=(80, 60), beams=False)
    c.table(cam, -1.4, 1.4, 1.5, 2.5, y=0.78, tone=150)
    p = cam.p(0.9, 1.4, 2.3)
    c.ell(p[0], p[1], 20, 20, 255)
    c.light_shaft([(p[0] - 20, p[1]), (p[0] + 20, p[1])], [(p[0] - 400, H * 0.9), (p[0] + 200, H * 0.9)], 55)
    if docs:
        for k in range(3):
            a = cam.p(-1.1 + k * 0.45, 0.79, 1.7)
            b = cam.p(-0.75 + k * 0.45, 0.79, 2.0)
            c.poly([a, (b[0], a[1]), b, (a[0], b[1])], 225)
    if parts:
        a = cam.p(0.3, 0.8, 1.7)
        c.line([a, (a[0] + 160, a[1] - 20)], 70, 20)
    figs(c, cam, people)


def sc_home(c, people=(), snow=True, crates=False, organ=False):
    cam = Cam(hz=0.45, camH=1.2)
    c.room(cam, w=5, h=2.6, d=5, wall=(130, 100), floor=(95, 70), beams=False)
    a, b = cam.p(0.6, 0.9, 5), cam.p(1.9, 2.2, 5)
    c.poly([a, (b[0], a[1]), b, (a[0], b[1])], 230)
    c.line([((a[0] + b[0]) / 2, a[1]), ((a[0] + b[0]) / 2, b[1])], 70, 10)
    if snow:
        for i in range(80):
            x = a[0] + c.rng.random() * (b[0] - a[0])
            y = b[1] + c.rng.random() * (a[1] - b[1])
            c.ell(x, y, 3, 3, 255)
    c.light_shaft([(a[0], b[1]), (b[0], b[1])], [(W * 0.2, H), (W * 0.9, H)], 40)
    if crates:
        c.box(cam, -1.2, 0.0, 0, 0.7, 2.2, 3.0, front=150, side=120, top=180)
        c.box(cam, 0.3, 1.1, 0, 0.5, 2.0, 2.6, front=160, side=130, top=190)
    if organ:
        c.box(cam, -1.1, -0.1, 0.7, 1.6, 2.4, 2.9, front=80, side=60, top=120)
    figs(c, cam, people)


def sc_black(c, text=None):
    c.grad((0, 0, W, H), 0, 0)


def sc_shipyard(c, people=()):
    c.grad((0, 0, W, H * 0.6), 200, 170)
    c.ship(0.5, 0.7, 0.75, face=1, sails="bare", tone=55)
    for k in range(8):
        c.line([(W * (0.15 + k * 0.1), H * 0.7), (W * (0.12 + k * 0.1), H * 0.35)], 90, 10)
    c.poly([(0, H * 0.7), (W, H * 0.7), (W, H), (0, H)], 110)
    for i in range(60):
        c.ell(c.rng.random() * W, H * (0.72 + c.rng.random() * 0.25), 8, 4, 40)
    for p in people:
        p = dict(p)
        c.fig(p.pop("x"), p.pop("y"), p.pop("h"), **p)


SCENES = {k[3:]: v for k, v in globals().items() if k.startswith("sc_")}


def render(spec, path, label=None, move=None, card=None, tag=None, silence=False, seed=1):
    spec = dict(spec)
    scene = spec.pop("scene")
    mood = spec.pop("mood", "noon")
    spec_flag = spec.pop("spec", False)
    blur = spec.pop("blur", 0)
    c = Canvas(mood=mood, seed=seed)
    SCENES[scene](c, **spec)
    if blur:
        c.blur_all(blur)
    c.finish(path, label=label, move=move, card=card, tag=tag, silence=silence, spec=spec_flag)
