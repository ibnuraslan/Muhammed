"""STORYBOARD_FULL: every shot of the film in order (intro, Ch1-3), one frame each, labelled
shot id · chapter · approx time · the VO line it covers.  Run with the render env python (needs bpy for the sets' DUR):
  python tools/storyboard_full.py review/STORYBOARD_FULL.jpg
Image per shot: out/sbv2/after/<set>_<move> (storyboard v2 shots) > out/handfix > out/hands (look v5 stills, Nov 12)."""
import os, sys, re, textwrap, importlib
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path[:0] = [os.path.join(ROOT, "scenes"), os.path.join(ROOT, "..", "..", "nvidia_doc", "scenes")]
from PIL import Image, ImageDraw, ImageFont
import shots
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "review", "STORYBOARD_FULL.jpg")
LEAD = {"intro": 2.5, "ch1": 3.0, "ch2": 3.0, "ch3": 3.0}
TITLE = {"intro": "INTRO", "ch1": "CHAPTER ONE · The House on Moncrieff Place", "ch2": "CHAPTER TWO · The Closet",
         "ch3": "CHAPTER THREE · Five Weeks Earlier"}
mods = {}
def dur(st, mv):
    if st not in mods:
        mods[st] = importlib.import_module("sc_" + st)
    return mods[st].DUR.get(mv, 5.0)
def img(st, mv):
    for d in ("out/sbv2/after", "out/handfix", "out/hands"):
        p = os.path.join(ROOT, d, f"{st}_{mv}", "plate.png")
        if os.path.exists(p):
            return p, d.endswith("after")
    return None, False
COLS, W = 4, 470; H = int(W * 816 / 1920); LAB = 92; PAD = 12; HB = 46
FB = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 17)
FS = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 14)
FT = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", 34)
FH = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", 22)
blocks = []; t = 0.0
for ch in ("intro", "ch1", "ch2", "ch3"):
    t += LEAD[ch]; items = []
    for k, (st, mv, tt, lab) in enumerate(shots.CHAPTERS[ch]):
        d = dur(st, mv)
        sid = lab.split()[0]
        vo = re.sub(r"\s*\[v2:.*?\]", "", lab[len(sid):]).strip(" ·")
        v2 = re.search(r"\[v2: (.*?)\]", lab)
        items.append(dict(sid=sid, ch=ch, t0=t, d=d, vo=vo, v2=v2.group(1) if v2 else None, img=img(st, mv)[0], src=f"{st}:{mv}"))
        t += d
    blocks.append((ch, items))
total = t
rows = sum((len(it) + COLS - 1) // COLS for _, it in blocks)
Wt = COLS * W + (COLS + 1) * PAD
Ht = 110 + len(blocks) * (HB + PAD) + rows * (H + LAB + PAD) + 40
sheet = Image.new("RGB", (Wt, Ht), (16, 16, 18)); d = ImageDraw.Draw(sheet)
d.text((PAD, 18), "THE KILLER WAS STILL IN THE HOUSE · full storyboard (v2, Nov 14)", font=FT, fill=(240, 236, 228))
d.text((PAD, 66), f"{sum(len(i) for _, i in blocks)} shots · approx {int(total // 60)}:{int(total % 60):02d} (DUR estimates + title leads; final timing from the VO) · "
       "realistic 3D, look v5 · stills: approved look-v5 renders (Nov 12) and v2 test stills · ★ = storyboard v2 shot", font=FS, fill=(170, 170, 170))
y = 110
fmt = lambda s: f"{int(s // 60)}:{int(s % 60):02d}"
for ch, items in blocks:
    d.rectangle([PAD, y, Wt - PAD, y + HB], fill=(44, 34, 26)); d.text((PAD + 12, y + 10), TITLE[ch] + f"   (title lead {LEAD[ch]:.1f} s)", font=FH, fill=(240, 210, 160))
    y += HB + PAD
    for i, it in enumerate(items):
        x = PAD + (i % COLS) * (W + PAD); yy = y + (i // COLS) * (H + LAB + PAD)
        if it["img"]:
            sheet.paste(Image.open(it["img"]).convert("RGB").resize((W, H), Image.LANCZOS), (x, yy))
        else:
            d.rectangle([x, yy, x + W, yy + H], fill=(50, 26, 26)); d.text((x + 12, yy + 12), "no still", font=FS, fill=(230, 190, 190))
        if it["v2"]:
            d.rectangle([x, yy, x + W - 1, yy + H - 1], outline=(220, 170, 80), width=3)
        star = "★ " if it["v2"] else ""
        d.text((x, yy + H + 4), f"{star}{it['ch'].upper()} {it['sid']}  ·  {fmt(it['t0'])}–{fmt(it['t0'] + it['d'])}  ·  {it['d']:.1f}s", font=FB, fill=(240, 225, 190) if it["v2"] else (225, 225, 225))
        lines = textwrap.wrap("VO: " + it["vo"], 62)[:2] + (textwrap.wrap(it["v2"], 62)[:2] if it["v2"] else [it["src"]])
        for k, ln in enumerate(lines[:4]):
            d.text((x, yy + H + 28 + k * 16), ln, font=FS, fill=(200, 200, 200) if k < 2 else (150, 150, 150))
    y += ((len(items) + COLS - 1) // COLS) * (H + LAB + PAD)
sheet = sheet.crop((0, 0, Wt, y + 20))
sheet.save(OUT, quality=85, optimize=True)
pdf = OUT.rsplit(".", 1)[0] + ".pdf"
print("[storyboard]", OUT, sheet.size, "total", fmt(total), "shots", sum(len(i) for _, i in blocks))
