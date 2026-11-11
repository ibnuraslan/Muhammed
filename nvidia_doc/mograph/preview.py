"""Render one still frame of a beat (graphics only, or over a plate if one exists) for look-dev / storyboard.
Usage: python preview.py <beat_id> [<fraction 0..1>] [out.png] [--plates DIR]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "edit"))
import numpy as np
from PIL import Image
from style import W, H, BG
from canvas import Frame, over, solid
import templates  # noqa: F401  (registers)
import templates2  # noqa: F401
from templates import TEMPLATES, draw_overlays
from beats import BEATS, est_duration


def plate_image(scene, plates_dir):
    if not scene or not plates_dir:
        return None
    for cand in (os.path.join(plates_dir, scene, "plate.png"), os.path.join(plates_dir, scene + ".png")):
        if os.path.exists(cand):
            im = Image.open(cand).convert("RGB").resize((W, H), Image.LANCZOS)
            return np.asarray(im).astype(np.float32) / 255
    return None


def frame_for(beat, t, plates_dir=None):
    dur = est_duration(beat)
    shot = beat["shot"]
    base = solid(BG)
    scene = shot.get("scene") or shot.get("bg")
    pl = plate_image(scene, plates_dir)
    if pl is not None:
        dim = 1.0 if shot["kind"] == "3d" else 0.35
        base = pl * dim + base * (1 - dim)
    elif shot["kind"] == "3d":
        fr = Frame(bg=None)
        fr.text(f"[3D · {scene} · {shot.get('move')}]", W / 2, H / 2, "mono", 30, (90, 100, 112), 1, anchor="c")
        base = over(base, fr.rgba())
    fr = Frame()
    tpl = shot.get("template")
    if tpl:
        TEMPLATES[tpl](fr, t, dur, beat, shot)
    draw_overlays(fr, t, dur, beat)
    return over(base, fr.rgba())


if __name__ == "__main__":
    bid = sys.argv[1]; frac = float(sys.argv[2]) if len(sys.argv) > 2 else 0.7
    out = sys.argv[3] if len(sys.argv) > 3 else f"/tmp/{bid}.png"
    plates = sys.argv[sys.argv.index("--plates") + 1] if "--plates" in sys.argv else None
    beat = next(b for b in BEATS if b["id"] == bid)
    img = frame_for(beat, est_duration(beat) * frac, plates)
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(out)
    print(out)
