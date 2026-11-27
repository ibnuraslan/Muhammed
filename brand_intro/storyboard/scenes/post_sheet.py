"""Post pass + storyboard sheet for the brand intro key frames.
Post: the world is monochrome and Seldom yellow is the ONLY colour. Every pixel whose hue is near yellow is pushed to
the brand hue (#E3FF00) and keeps its saturation; everything else is drained to neutral grey. Then fine grain.
Sheet: 6 key frames in a 2x3 grid with timings, the transition out of each, and the end hold on the official logo."""
import os, json, colorsys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "..", "out"); FR = os.path.join(HERE, "..", "frames")
K = "/home/user/Muhammed/brand_overlays/kit_v1/fonts/"
os.makedirs(FR, exist_ok=True)
YEL = (227, 255, 0); WHITE = (243, 241, 234); GREY = (150, 146, 136); INK = (11, 10, 8)
BH = 66.6 / 360.0


def post(src, dst):
    a = np.asarray(Image.open(src).convert("RGB")).astype(np.float32) / 255.0
    mx = a.max(2); mn = a.min(2); d = mx - mn + 1e-6
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) / 6.0
    s = np.where(mx > 0, d / (mx + 1e-6), 0)
    near = np.clip(1 - np.abs(((h - BH + 0.5) % 1.0) - 0.5) / 0.09, 0, 1) * np.clip((s - 0.12) / 0.2, 0, 1)
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    # brand-hue version keeping value (max channel) and saturation
    v = mx; s2 = np.clip(s * 1.08, 0, 1)
    br = np.array(YEL, np.float32) / 255.0
    tint = v[..., None] * (1 - s2[..., None] + s2[..., None] * br[None, None, :])
    grey = np.repeat(lum[..., None], 3, 2) * np.array([1.0, 0.995, 0.975])[None, None, :]
    o = grey * (1 - near[..., None]) + tint * near[..., None]
    rng = np.random.default_rng(len(src))
    o = o + rng.normal(0, 0.012, o.shape[:2])[..., None]
    Image.fromarray((np.clip(o, 0, 1) * 255).astype(np.uint8)).save(dst, quality=94)


SHOTS = [
    ("k1_chalk", "01", "CHALK OUTLINE", "0.0 – 2.4 s",
     "Top-down over wet night asphalt. A chalk outline, a yellow evidence marker '1'. A faceless figure stands out of frame; only his long shadow lies across the body, head to head. Camera drifts down and turns slowly.",
     "MORPH: the camera tilts from top-down to floor level; the chalk line of the arm stretches and thins into the strip of light under a door."),
    ("k2_door", "02", "DOOR AJAR", "2.4 – 4.8 s",
     "A dark corridor. The door at the end stands open a hand's width; yellow light knifes out across the boards. A faceless silhouette waits in the gap. Slow push down the hall.",
     "MORPH: the wedge of yellow light races along the floor toward the lens; we drop with it to floor level and it pools around a glove."),
    ("k3_glove", "03", "THE DROPPED GLOVE", "4.8 – 7.0 s",
     "Floor level, shallow focus. A black leather glove lies in the yellow pool; behind it, out of focus, the figure's legs walk away into the dark.",
     "MORPH: rack focus to the walker; his shadow climbs the wall and its line coils into a telephone cord."),
    ("k4_phone", "04", "OFF THE HOOK", "7.0 – 9.4 s",
     "A rotary phone on a small cabinet. The yellow receiver hangs on its coiled cord, still swinging; a head-and-shoulders shadow fills the wall behind it.",
     "MORPH: the receiver's swing becomes a pendulum whip-pan; the cord's coils stretch into falling rain streaks."),
    ("k5_car", "05", "CAR IN THE RAIN", "9.4 – 11.8 s",
     "Night, heavy rain. A parked '71 sedan, headlights on: two yellow beams through the downpour. A faceless figure stands at the edge of the light, watching.",
     "MORPH: a wiper-like sweep of rain across the lens; the water sheet turns into the crinkled plastic of an evidence bag, top-down."),
    ("k6_evidence_logo", "06", "EVIDENCE BAG → LOGO", "11.8 – 15.0 s",
     "Top-down on a steel table: the glove from shot 03, sealed in a clear bag under a yellow tamper strip. The camera settles on the label, where the official Seldom logo is printed (logo art, not 3D text).",
     "END: from 13.6 s the bag and table fall to black, the label paper dissolves, and the logo holds alone on black until 15.0 s."),
]

if __name__ == "__main__":
    for k, *_ in SHOTS:
        post(os.path.join(OUT, k + ".png"), os.path.join(FR, k + ".jpg"))
    # end card: the official logo alone on black
    logo = Image.open(os.path.join(HERE, "..", "logo.png")).convert("RGBA")
    ec = Image.new("RGBA", (1280, 720), INK + (255,)); lw = 760; lh = int(logo.height * lw / logo.width)
    gl = logo.resize((lw, lh), Image.LANCZOS)
    halo = Image.new("RGBA", ec.size, (0, 0, 0, 0)); halo.alpha_composite(gl, ((1280 - lw) // 2, (720 - lh) // 2))
    halo = halo.filter(ImageFilter.GaussianBlur(40)); halo.putalpha(halo.split()[3].point(lambda v: int(v * 0.35)))
    ec.alpha_composite(halo); ec.alpha_composite(gl, ((1280 - lw) // 2, (720 - lh) // 2))
    ec.convert("RGB").save(os.path.join(FR, "k7_end_hold.jpg"), quality=94)

    # ---- the sheet
    fb = lambda n, s: ImageFont.truetype(K + n, s)
    TW, TH = 900, 506; PAD = 40; COLS = 2; TXT = 250
    rows = 3; Wd = PAD + COLS * (TW + PAD); Ht = 230 + rows * (TH + TXT + PAD) + 330
    sh = Image.new("RGB", (Wd, Ht), (12, 11, 10)); d = ImageDraw.Draw(sh)
    d.text((PAD, 40), "SELDOM  ·  BRAND INTRO", font=fb("Oswald-Bold.ttf", 64), fill=WHITE)
    d.text((PAD, 122), "STORYBOARD v1  ·  6 KEY FRAMES  ·  15 s  ·  ONE CONTINUOUS CAMERA, MORPH TRANSITIONS (NO CUTS)", font=fb("IBMPlexMono-Regular.ttf", 24), fill=YEL)
    d.text((PAD, 160), "Monochrome world. Seldom yellow is the only colour. Faceless black silhouettes. Ends on the official logo.", font=fb("IBMPlexMono-Regular.ttf", 22), fill=GREY)

    def wrap(t, f, w):
        out, cur = [], ""
        for word in t.split():
            tr = (cur + " " + word).strip()
            if d.textlength(tr, font=f) > w and cur:
                out.append(cur); cur = word
            else:
                cur = tr
        return out + [cur]
    fT = fb("Oswald-Medium.ttf", 34); fM = fb("IBMPlexMono-Regular.ttf", 20); fD = fb("IBMPlexMono-Regular.ttf", 19)
    for i, (k, n, title, tm, desc, trans) in enumerate(SHOTS):
        x = PAD + (i % COLS) * (TW + PAD); y = 230 + (i // COLS) * (TH + TXT + PAD)
        sh.paste(Image.open(os.path.join(FR, k + ".jpg")).resize((TW, TH), Image.LANCZOS), (x, y))
        d.rectangle([x, y, x + 64, y + 40], fill=YEL); d.text((x + 32, y + 21), n, font=fb("Oswald-Bold.ttf", 28), fill=INK, anchor="mm")
        d.text((x, y + TH + 14), title, font=fT, fill=WHITE); d.text((x + TW, y + TH + 22), tm, font=fM, fill=YEL, anchor="ra")
        yy = y + TH + 62
        for ln in wrap(desc, fD, TW):
            d.text((x, yy), ln, font=fD, fill=(205, 202, 194)); yy += 25
        yy += 6
        for j, ln in enumerate(wrap(trans, fD, TW - 24)):
            d.text((x + 24, yy), ln, font=fD, fill=YEL if j == 0 else (200, 214, 120)); yy += 25
        d.text((x, yy - 25 * len(wrap(trans, fD, TW - 24))), "→", font=fD, fill=YEL)
    # end-hold strip
    y = 230 + rows * (TH + TXT + PAD)
    sh.paste(Image.open(os.path.join(FR, "k7_end_hold.jpg")).resize((480, 270), Image.LANCZOS), (PAD, y))
    d.text((PAD + 520, y + 6), "END HOLD  ·  13.6 – 15.0 s", font=fT, fill=WHITE)
    for j, ln in enumerate(["The official logo art (brand/intros/scenes/logo.png) alone on black, a faint yellow bloom,",
                            "film grain. Never 3D text. Sound: the phone's last ring is cut by a single low hit on the logo.",
                            "",
                            "Camera path: one unbroken move. Top-down crane (01) → tilt to floor level (02) → floor-skim",
                            "dolly (03) → rise up the wall (04) → pendulum whip into the rain (05) → overhead settle (06).",
                            "Every transition is a shape match (line → light → cord → rain → plastic)."]):
        d.text((PAD + 520, y + 60 + j * 28), ln, font=fD, fill=(205, 202, 194))
    sh.save(os.path.join(HERE, "..", "storyboard_sheet.jpg"), quality=90)
    print("sheet", sh.size)
