"""CH1 SETS 6A / 7A: generic CG skylines in the house style (no landmarks, no glitter).
  shanghai : dusk across a wide river, tall glass towers, barges moving on the water
  singapore: bright tropical day across a bay, glass and stone towers, palms on the promenade
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from sc_home import facade, haze_mix

EXPOSURE = -0.8
VARIANT_FOR = {"shanghai_drift": "shanghai", "singapore_drift": "singapore", "beijing_night": "beijing", "singapore_dusk": "sgdusk", "beijing_eye": "beijing"}
DUR = {"singapore_dusk": 14.0, "beijing_eye": 11.0, "shanghai_drift": 5.0, "singapore_drift": 5.0, "beijing_night": 6.0}     # estimates until the chapter 1 voiceover arrives


def build(variant=None):
    c = {}
    sg = variant in ("singapore", "sgdusk")          # sgdusk: the Singapore skyline at dusk (CH4 8A)
    sgday = variant == "singapore"
    rng = np.random.default_rng(3 if sg else 8)
    bj = variant == "beijing"
    if bj:
        world_flat((0.004, 0.006, 0.012), 1.0)
        haze_col = (0.05, 0.06, 0.09)
    elif sgday:
        world_sky(sun_elev_deg=38, sun_rot_deg=230, strength=0.16, tint=(0.92, 0.96, 1.0), aerosol=2.2)
        sun(38, 230, energy=1.1, color=(1.0, 0.95, 0.88), angle_deg=1.0)
        haze_col = (0.5, 0.56, 0.62)
    else:
        world_sky(sun_elev_deg=1.5, sun_rot_deg=20, strength=0.6, tint=(1.0, 0.82, 0.7), aerosol=3.5)
        sun(1.5, 20, energy=1.6, color=(1.0, 0.55, 0.3), angle_deg=1.5)
        haze_col = (0.62, 0.55, 0.55)
    H = lambda m, k=0.8: haze_mix(m, color=haze_col, start=300, end=5000, strength=k)
    water = pbr("Water", (0.01, 0.02, 0.025) if not sgday else (0.02, 0.05, 0.06), 0.04, 0.0, **{'Specular IOR Level': 0.7})
    N = water.node_tree.nodes; L = water.node_tree.links; tc = N.new("ShaderNodeTexCoord")
    wv = N.new("ShaderNodeTexWave"); wv.inputs['Scale'].default_value = 0.05; wv.inputs['Distortion'].default_value = 6; L.new(tc.outputs['Object'], wv.inputs['Vector'])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 0.3; nz.inputs['Detail'].default_value = 8; L.new(tc.outputs['Object'], nz.inputs['Vector'])
    ad = N.new("ShaderNodeMath"); ad.operation = 'ADD'; L.new(wv.outputs['Fac'], ad.inputs[0]); L.new(nz.outputs['Fac'], ad.inputs[1])
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.12; L.new(ad.outputs[0], bp.inputs['Height']); L.new(bp.outputs['Normal'], N["Principled BSDF"].inputs['Normal'])
    if not bj:
        box("Water", (0, 600, -1), (8000, 1400, 1), water)
    else:                                            # a lit street grid instead of the river
        st = emissive("StreetGlow", (1.0, 0.62, 0.32), 1.4)
        for k in range(-30, 31):
            box("AvenueX", (0, 1500 + k * 110, 0.6), (8000, 4, 0.2), st)
            box("AvenueY", (k * 120, 2500, 0.6), (4, 5000, 0.2), st)
        box("CityFloor", (0, 2500, 0), (8000, 5000, 1), pbr("CityNight", (0.02, 0.02, 0.025), 0.9))
    # far shore: embankment, promenade, then the towers
    ground = H(pbr("Ground", (0.18, 0.18, 0.17), 0.85))
    box("FarShore", (0, 2600, 0), (8000, 2800, 2), ground)
    box("Embank", (0, 1200, 1), (8000, 8, 4), H(pbr("Embank", (0.35, 0.34, 0.32), 0.7)))
    near = pbr("Promenade", (0.32, 0.31, 0.29), 0.75)
    box("NearShore", (0, -150, 0), (8000, 300, 2), near)
    lf = 0.0 if sgday else (0.38 if bj else 0.12)
    types = [facade("GlassA", (0.05, 0.08, 0.11), (0.45, 0.47, 0.5) if not bj else (0.08, 0.085, 0.09), floor=4.0, bay=1.6, lit_frac=lf, refl=0.45),
             facade("GlassB", (0.07, 0.1, 0.1), (0.55, 0.55, 0.52), floor=3.8, bay=1.5, lit_frac=0.0 if sgday else 0.1, refl=0.4),
             facade("Stone", (0.08, 0.085, 0.09), (0.66, 0.62, 0.56), floor=3.6, bay=1.4, lit_frac=0.0 if sgday else 0.15, refl=0.12),
             facade("Dark", (0.03, 0.035, 0.045), (0.22, 0.23, 0.25), floor=4.2, bay=1.8, lit_frac=0.0 if sgday else 0.08, refl=0.5)]
    for m in types:
        H(m, 0.7)
    cx = 0.0
    for k in range(85):
        x = rng.normal(cx, 700); y = 1300 + abs(rng.normal(0, 380)) + 40
        hgt = max(60.0, (420 if not sg else 280) * math.exp(-abs(x - cx) / 900) * rng.uniform(0.35, 1.0))
        w = rng.uniform(30, 60); d = rng.uniform(30, 60); m = types[rng.integers(len(types))]
        kind = rng.random()
        if kind < 0.3 and hgt > 180:                     # tapering setback supertall
            z = 0.0
            for tier, (fw, fh) in enumerate(((1.0, 0.5), (0.82, 0.25), (0.62, 0.15), (0.4, 0.1))):
                box("Tower", (x, y, z + hgt * fh / 2), (w * fw, d * fw, hgt * fh), m); z += hgt * fh
            cyl("Spire", (x, y, z + 20), 1.2, 40, pbr("Spire", (0.6, 0.6, 0.62), 0.3, 1.0), verts=12)
        elif kind < 0.5:
            cyl("Tower", (x, y, hgt / 2), w * 0.5, hgt, m, verts=32)
        else:
            box("Tower", (x, y, hgt / 2), (w, d, hgt), m)
            box("Crown", (x, y, hgt + 4), (w * 0.6, d * 0.6, 8), m)
    low = facade("Low", (0.07, 0.08, 0.09), (0.5, 0.48, 0.45), floor=3.4, bay=2.0, lit_frac=0.0 if sgday else 0.1, refl=0.08)
    H(low, 0.75)
    for k in range(900):
        x = rng.uniform(-3500, 3500); y = rng.uniform(1220, 3800); hgt = rng.uniform(12, 45)
        box("Low", (x, y, hgt / 2), (rng.uniform(25, 60), rng.uniform(25, 60), hgt), low)
    # boats on the water (slow) — barges at dusk / ferries by day
    hullm = pbr("BoatHull", (0.05, 0.05, 0.06), 0.6); deck = pbr("BoatDeck", (0.6, 0.58, 0.52), 0.6)
    boats = []
    for k in range(6):
        parts = [box("BH", (0, 0, 1.5), (60 if not sg else 28, 11 if not sg else 8, 3), hullm, bevel=0.6),
                 box("BC", (-20 if not sg else -6, 0, 5), (10, 9 if not sg else 6, 5), deck, bevel=0.3)]
        b = join(parts, f"Boat{k}"); b.location = (rng.uniform(-1500, 1500), rng.uniform(300, 1000), 0)
        boats.append((b, rng.uniform(4, 8) * (1 if k % 2 else -1)))
    c["boats"] = boats
    if sg:     # palms along the near promenade (scanned tree)
        import ph
        root, ms = ph.model("island_tree_02", loc=(0, 0, -300))
        for k in range(14):
            instance(ms[0], (-300 + k * 46 + rng.uniform(-6, 6), -12 + rng.uniform(-3, 3), 1.0), rot=(0, 0, rng.uniform(0, 6.28)), scale=(3.0, 3.0, 3.0))
        rail = pbr("Rail", (0.5, 0.5, 0.52), 0.3, 1.0)
        box("RailTop", (0, 0, 2.1), (8000, 0.08, 0.08), rail)
    return c


def anim_boats(c, t, seconds):
    for b, v in c["boats"]:
        if "x0" not in b:
            b["x0"] = b.location.x
        b.location.x = b["x0"] + v * t * seconds


def _drift(c, t, seconds, start, end, tgt):
    anim_boats(c, t, seconds)
    e = ease(t)
    return (Vector(start).lerp(Vector(end), e), Vector(tgt), 35)


MOVES = {
    "shanghai_drift": dict(kind="anim", far=6000.0, cam=lambda c, t: _drift(c, t, DUR["shanghai_drift"], (-260, -60, 70), (-120, 40, 85), (0, 1600, 180))),
    "beijing_night": dict(kind="anim", far=8000.0, cam=lambda c, t: _drift(c, t, DUR["beijing_night"], (-400, 300, 420), (-150, 650, 380), (200, 2200, 60))),
    "singapore_dusk": dict(kind="anim", far=6000.0, cam=lambda c, t: _drift(c, t, DUR["singapore_dusk"], (200, -45, 14), (90, -35, 18), (0, 1500, 140))),
    # CH5 5B: Beijing at night from low across the avenues: lit windows, haze, depth (not the high dotted aerial)
    "beijing_eye": dict(kind="anim", far=8000.0, cam=lambda c, t: _drift(c, t, DUR["beijing_eye"], (-300, 250, 60), (-180, 330, 70), (0, 1700, 150))),
    "singapore_drift": dict(kind="anim", far=6000.0, cam=lambda c, t: _drift(c, t, DUR["singapore_drift"], (180, -40, 12), (60, -30, 16), (0, 1500, 130))),
}
