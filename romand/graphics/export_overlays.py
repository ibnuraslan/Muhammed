"""Export a part's on-screen graphics as an alpha PNG sequence timed to MASTER (frame k = MASTER frame k), plus
bg.json with the background treatment each frame asks for (blur px, dim 0..1) and the card-only shots' plates.
Same templates and parameters as the storyboard (romand/3d/sb_post.py overlays()).
    KIT=<kit_v1> RAW=<storyboard stills for photo crops> python3 export_overlays.py 1 <out_dir>
Every frame is a full 1920x1080 RGBA PNG (most are fully transparent and tiny), so any editor can drop the sequence
on a track above the MASTER render; composite_upscale.py does it in one pass."""
import os, sys, json
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.environ["KIT"]); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "3d"))
import seldom_kit as K
import rmap  # noqa: F401  (registers map_fr)
import sb_post as SP
PART = int(sys.argv[1]); OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
ROWS = json.load(open(os.path.join(ROOT, "shots", "shots.json")))[str(PART)]["rows"]
FPS = 24


def main():
    ov = SP.overlays(); blank = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    bg = {}; k = 0; tl = []
    for r in ROWS:
        n = max(12, round(r["dur"] * FPS)); tl.append(dict(id=r["id"], start=k + 1, frames=n,
                                                           plate=SP.PLATES2D.get(r["id"], "own") if r["id"] in SP.PLATES2D else "own"))
        for i in range(n):
            k += 1; t = i / FPS; im = blank; blur = dim = 0.0
            for (tpl, params, _t) in ov.get(r["id"], []):
                fr = K.TEMPLATES[tpl](t, **params)
                im = Image.alpha_composite(im, fr.rgba) if im is not blank else fr.rgba
                blur = max(blur, fr.bg.get("blur", 0)); dim = max(dim, fr.bg.get("dim", 0))
            im.save(os.path.join(OUT, f"ov_{k:05d}.png"), optimize=True)
            if blur > 0.3 or dim > 0.005:
                bg[k] = [round(blur, 2), round(dim, 3)]
    json.dump(dict(part=PART, frames=k, fps=FPS, bg=bg, timeline=tl), open(os.path.join(OUT, "bg.json"), "w"))
    print("OVERLAYS", k, "frames ->", OUT)


if __name__ == "__main__":
    main()
