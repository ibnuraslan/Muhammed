"""Compose the Nvidia concept sheet (quick plates) or the finals (full plates).
  python thumbnails/nvidia/make.py sheet      -> thumbnails/nvidia/nvidia_concepts_sheet.jpg
  python thumbnails/nvidia/make.py final chip -> thumbnails/nvidia/nvidia_final_text.jpg + _notext.jpg"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
from compose import load_plate, grade, draw_text, save, sheet, RED, WHITE

TEXT = {
    # name: (style label, lines, x, y, size, anchor)
    "chip":  ("Style 4 · Dark evidence", [[("COMPROMISED", WHITE), ("?", RED)]], 90, 760, 230, "la"),
    "memo":  ("Style 3 · Minimal evidence", [[("TARGETED", WHITE), ("?", RED)]], 90, 90, 250, "la"),
    "chair": ("Style 2 · Investigative", [[("RESIGNED", WHITE)]], 90, 420, 250, "la"),
}


def build(name, plate_dir, text=True):
    im = grade(load_plate(os.path.join(HERE, plate_dir, f"{name}.png")))
    if text:
        _, lines, x, y, size, anc = TEXT[name]
        im = draw_text(im, lines, x, y, size, anchor=anc)
    return im


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "sheet":
        tmp = []
        for n in ("chip", "memo", "chair"):
            p = os.path.join(HERE, "out_tmp", f"{n}.jpg"); save(build(n, "plates_quick"), p)
            words = "".join(t for ln in TEXT[n][1] for t, _ in ln)
            tmp.append((p, f"{n.upper()}  ·  {TEXT[n][0]}  ·  \"{words}\""))
        sheet(tmp, os.path.join(HERE, "nvidia_concepts_sheet.jpg"), "NVIDIA · 3 thumbnail concepts (quick renders)")
    elif sys.argv[2] == "targeted":           # approved: "NVIDIA" (white) over "TARGETED?" (lime), both behind the women
        from compose import LIME, WHITE, FONTS, grade, load_plate, draw_text
        from PIL import ImageFont, Image
        P = os.path.join(HERE, "plates")
        cx = lambda t, sz: 960 - ImageFont.truetype(os.path.join(FONTS, "Anton-Regular.ttf"), sz).getlength(t) / 2
        base = grade(load_plate(os.path.join(P, "targeted.png")), vignette=0.45, lift=0.01)
        t = draw_text(base, ["NVIDIA"], cx("NVIDIA", 230), 30, 230, color=WHITE, stroke=5, shadow=0.6)
        t = draw_text(t, ["TARGETED?"], cx("TARGETED?", 330), 250, 330, color=LIME, stroke=6, shadow=0.6)
        m = Image.open(os.path.join(P, "targeted_mask.png")).split()[-1].resize(base.size, Image.LANCZOS)
        im = Image.composite(base, t, m)
        save(im, os.path.join(HERE, "nvidia_final_text.jpg")); save(base, os.path.join(HERE, "nvidia_final_notext.jpg"))
        D = os.path.join(HERE, "download"); os.makedirs(D, exist_ok=True)
        im.save(os.path.join(D, "nvidia_thumbnail_NVIDIA_TARGETED.png")); base.save(os.path.join(D, "nvidia_thumbnail_notext.png"))
        im.save(os.path.join(D, "nvidia_thumbnail_NVIDIA_TARGETED_youtube.jpg"), quality=97, subsampling=0)
        base.save(os.path.join(D, "nvidia_thumbnail_notext_youtube.jpg"), quality=97, subsampling=0)
    else:
        n = sys.argv[2]
        save(build(n, "plates"), os.path.join(HERE, "nvidia_final_text.jpg"))
        save(build(n, "plates", text=False), os.path.join(HERE, "nvidia_final_notext.jpg"))
