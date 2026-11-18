"""Look-development test frames: blockout + atmosphere/grade passes (fog, bloom, DOF, spray, grain)."""
import os, random
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageChops
from sketch import Canvas, Cam, W, H
import scenes

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames")


def grade(img, shadows, mids, highs):
    return ImageOps.colorize(img, black=shadows, mid=mids, white=highs)


def bloom(rgb, thresh=200, radius=40, k=0.6):
    g = ImageOps.grayscale(rgb).point(lambda p: 255 if p > thresh else 0)
    glow = Image.composite(rgb, Image.new("RGB", rgb.size), g).filter(ImageFilter.GaussianBlur(radius))
    return ImageChops.add(rgb, glow.point(lambda p: int(p * k)))


def fog(rgb, col, y0, y1, a=0.6):
    m = Image.new("L", rgb.size, 0)
    d = ImageDraw.Draw(m)
    for y in range(int(y0 * H), int(y1 * H)):
        t = 1 - abs((y - (y0 + y1) / 2 * H) / ((y1 - y0) / 2 * H))
        d.line([(0, y), (W, y)], fill=int(255 * a * max(0, t)))
    return Image.composite(Image.new("RGB", rgb.size, col), rgb, m.filter(ImageFilter.GaussianBlur(30)))


def grain(rgb, amt=10, seed=3):
    rnd = random.Random(seed)
    n = Image.effect_noise(rgb.size, amt * 4).convert("RGB")
    return Image.blend(rgb, ImageChops.overlay(rgb, n), 0.18)


def vign(rgb, k=0.55):
    v = Image.new("L", rgb.size, 0)
    ImageDraw.Draw(v).ellipse([-W * 0.1, -H * 0.15, W * 1.1, H * 1.15], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(200))
    return Image.composite(rgb, rgb.point(lambda p: int(p * (1 - k))), v)


def spray(rgb, n=900, seed=5):
    rnd = random.Random(seed)
    lay = Image.new("RGBA", rgb.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i in range(n):
        x, y = rnd.random() * W, rnd.random() * H
        r = rnd.random() * 4 + 1
        d.ellipse([x - r, y - r, x + r, y + r], fill=(230, 240, 245, rnd.randint(40, 140)))
    for i in range(500):
        x, y = rnd.random() * W, rnd.random() * H
        d.line([(x, y), (x - 25, y + 90)], fill=(200, 215, 225, 70), width=2)
    return Image.alpha_composite(rgb.convert("RGBA"), lay.filter(ImageFilter.GaussianBlur(1.2))).convert("RGB")


def frame_storm():
    """Night gale, lightning rim, lantern on deck, spray. Ref: Atrium night exteriors."""
    c = Canvas(seed=11)
    scenes.sc_sea(c, hy=0.52, ships=[dict(x=0.52, L=0.5, sails="bare", face=1, y=0.6)], clouds=True, sky=(95, 55), sea=(70, 20))
    c.light_shaft([(W * 0.62, 0), (W * 0.70, 0)], [(W * 0.55, H * 0.52), (W * 0.75, H * 0.52)], 70)
    rgb = grade(c.img, (3, 6, 12), (40, 58, 78), (190, 215, 235))
    d = ImageDraw.Draw(rgb)
    d.ellipse([W * 0.44 - 14, H * 0.47 - 20, W * 0.44 + 14, H * 0.47 + 20], fill=(255, 190, 110))
    lay = Image.new("RGB", rgb.size)
    ImageDraw.Draw(lay).ellipse([W * 0.44 - 220, H * 0.47 - 180, W * 0.44 + 220, H * 0.47 + 180], fill=(150, 80, 25))
    rgb = ImageChops.add(rgb, lay.filter(ImageFilter.GaussianBlur(90)))
    rgb = fog(rgb, (60, 75, 92), 0.40, 0.62, 0.55)
    rgb = spray(rgb)
    rgb = bloom(rgb, 190, 35, 0.7)
    return grain(vign(rgb, 0.6))


def frame_cabin():
    """Captain's cabin, cold skylight shaft, wet bedding, dust in the beam, shallow DOF."""
    c = Canvas(seed=12)
    cam = Cam(hz=0.45, camH=1.45)
    scenes.sc_cabin(c, cam=cam, water=True, hollow=True, people=[dict(X=0.7, Z=3.2, view="3q_l", hat="cap")])
    c.blur_layer(lambda l, m: (l.rectangle([0, 0, W, H * 0.25], fill=40), m.rectangle([0, 0, W, H * 0.25], fill=160)), 25)
    rgb = grade(c.img, (6, 9, 12), (62, 74, 82), (215, 228, 232))
    lay = Image.new("RGBA", rgb.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    rnd = random.Random(2)
    for i in range(260):
        x, y = W * (0.36 + rnd.random() * 0.24), H * (0.1 + rnd.random() * 0.8)
        r = rnd.random() * 2.5 + 0.5
        d.ellipse([x - r, y - r, x + r, y + r], fill=(235, 240, 240, rnd.randint(60, 180)))
    rgb = Image.alpha_composite(rgb.convert("RGBA"), lay).convert("RGB")
    rgb = bloom(rgb, 175, 45, 0.55)
    return grain(vign(rgb, 0.65))


def frame_dawn():
    """Santa Maria at dawn: warm low sun, sea haze, ship in silhouette, island in aerial perspective."""
    c = Canvas(seed=13)
    scenes.sc_sea(c, hy=0.56, ships=[dict(x=0.36, L=0.42, sails="full", face=1, y=0.62)], island=(0.78, 0.26, 0.045, 150),
                  sky=(250, 200), sea=(170, 60), sun=(0.66, 0.46))
    rgb = grade(c.img, (18, 10, 12), (150, 92, 62), (255, 228, 180))
    rgb = fog(rgb, (240, 190, 140), 0.48, 0.64, 0.45)
    rgb = bloom(rgb, 215, 60, 0.6)
    return grain(vign(rgb, 0.45))


FRAMES = [("look_storm.jpg", frame_storm, "Night gale near the Strait: blue-black storm, lantern as the only warm light, rain and spray, lightning rim on sails"),
          ("look_cabin.jpg", frame_cabin, "Captain's cabin, 4 Dec: one cold skylight shaft, dust in the beam, wet bedding, everything else falls to black"),
          ("look_dawn.jpg", frame_dawn, "25 Nov, Santa Maria: low gold sun through sea haze, ship in silhouette, island softened by distance")]

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn, _ in FRAMES:
        fn().resize((1600, 900), Image.LANCZOS).save(os.path.join(OUT, name), quality=90)
    print("ok")
