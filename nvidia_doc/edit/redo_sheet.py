"""Before/after sheet for the Ch4-5 redo: per shot, the OLD frame (rendered from the delivered master, mid-cut) next to
the NEW shot at t 0 / 0.5 / 1 (rendered through a master-style scene, the same brightness path). The split screen is
assembled as the patch will lay it out (middle 960 px of each half side by side). Title shots also get an 'as cut'
tile: the new picture at the title hold with the delivered title overlay .mov composited on top.
  python edit/redo_sheet.py -> out/ch45_preview/ch45_redo_before_after.jpg"""
import os, sys, glob, subprocess, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.join(HERE, "..")
from redo_ch45 import table
PREV = os.path.join(ROOT, "out", "ch45_redo_prev"); OLD = os.path.join(ROOT, "out", "ch45_sb_final")
MOV = os.path.join(ROOT, "out", "title_overlay_ch45", "nvidia_ch45_title_overlay.mov")
TW, TH, pad = 420, 179, 10
F = lambda z: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", z)
f1, f2, fh = F(16), F(13), F(24)


def load(p, size=(1920, 816)):
    return Image.open(p).convert("RGB").resize(size, Image.LANCZOS)


def split(tag):
    L = load(os.path.join(PREV, f"new_c4_01_L_{tag}.png")); R = load(os.path.join(PREV, f"new_c4_01_R_{tag}.png"))
    out = Image.new("RGB", (1920, 816)); out.paste(L.crop((480, 0, 1440, 816)), (0, 0)); out.paste(R.crop((480, 0, 1440, 816)), (960, 0))
    d = ImageDraw.Draw(out); d.rectangle([958, 0, 961, 816], fill=(0, 0, 0))
    return out


def overlay(img, F_):
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", MOV, "-vf", f"select=eq(n\\,{F_ - 1})", "-frames:v", "1",
                        "-f", "rawvideo", "-pix_fmt", "rgba", "-"], capture_output=True).stdout
    ov = np.frombuffer(b, np.uint8).reshape(816, 1920, 4).astype(np.float32) / 255
    base = np.asarray(img.resize((1920, 816))).astype(np.float32) / 255
    a = ov[..., 3:4]
    return Image.fromarray((np.clip(base * (1 - a) + ov[..., :3] * a, 0, 1) * 255 + .5).astype(np.uint8))


rows = table()
cols = 5
img = Image.new("RGB", (pad + cols * (TW + pad), 54 + len(rows) * (TH + 46)), (18, 18, 22)); d = ImageDraw.Draw(img)
d.text((pad, 14), "NVIDIA CH4-5 REDO · before / after  (OLD = delivered master, mid-cut · NEW at t 0 / 0.5 / 1 · same brightness path)",
       fill=(240, 240, 245), font=fh)
y = 54
for r in rows:
    sid = r["id"]
    old = sorted(glob.glob(os.path.join(OLD, f"{sid}_*.png")))
    tiles = []
    tiles.append((load(old[0]) if old else Image.new("RGB", (1920, 816), (40, 40, 40)), "OLD"))
    for tag, lab in (("t000", "NEW t 0"), ("t050", "NEW t 0.5"), ("t100", "NEW t 1")):
        if sid == "c4_01":
            im = split(tag)
        else:
            p = os.path.join(PREV, f"new_{sid}_{tag}.png")
            im = load(p) if os.path.exists(p) else Image.new("RGB", (1920, 816), (60, 20, 20))
        tiles.append((im, lab))
    if sid in ("c4_01", "c5_01"):                      # as cut: hold frame (local 66) + the delivered overlay
        if sid == "c4_01":
            hold = split("t026") if os.path.exists(os.path.join(PREV, "new_c4_01_L_t026.png")) else split("t000")
        else:
            p = os.path.join(PREV, "new_c5_01_t030.png")
            hold = load(p) if os.path.exists(p) else tiles[1][0]
        tiles.append((overlay(hold, r["master_in"] + 65), "AS CUT: title hold + overlay"))
    d.text((pad, y + 2), f"{sid}  ·  {r['label']}  ·  {r['frames']} f  ·  master {r['master_in']}-{r['master_out']}", fill=(240, 200, 120), font=f1)
    for k, (im, lab) in enumerate(tiles):
        x = pad + k * (TW + pad)
        img.paste(im.resize((TW, TH), Image.LANCZOS), (x, y + 22))
        d.text((x + 4, y + 26), lab, fill=(255, 255, 255) if k else (255, 150, 120), font=f2)
    y += TH + 46
out = os.path.join(ROOT, "out", "ch45_preview", "ch45_redo_before_after.jpg")
img.save(out, quality=90); print("wrote", out, img.size)
