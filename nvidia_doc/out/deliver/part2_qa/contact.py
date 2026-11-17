"""Contact sheet of the final MP4: every redo-clip seam (frame before | after), both titles (start/mid/end), every card at hold."""
import sys, json, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
mp4, cards_json, out = sys.argv[1:4]
W, H = 1920, 816
REDO = [(1, 249, "c4_01"), (443, 730, "c4_03"), (1405, 1518, "c4_08_v2"), (1519, 1815, "c4_09"), (2398, 2593, "c4_12"), (2785, 2972, "c4_14"),
        (3571, 3769, "c4_18"), (4103, 4317, "c5_01"), (4775, 4929, "c5_04"), (5507, 5754, "c5_07"), (5994, 6129, "c5_09"), (6392, 6588, "c5_11"),
        (6984, 7235, "c5_14"), (8375, 8601, "c5_20")]
rows = []
seams = []
for a, b, c in REDO:
    if a > 1: seams.append((a - 1, a, f"IN {c}"))
    seams.append((b, b + 1, f"OUT {c}"))
seams = list(dict.fromkeys(seams))
for s in seams: rows.append([(s[0], f"{s[2]}  f{s[0]}"), (s[1], f"f{s[1]}")])
titles = [(f, f"TITLE ch4 f{f}") for f in (19, 24, 69, 114, 119)] + [(f, f"TITLE ch5 f{f}") for f in (4121, 4126, 4171, 4216, 4221)]
cards = json.load(open(cards_json))
cardt = [(c["frame"] + 4, f"CARD {c['name']} in f{c['frame']+4}") for c in cards] + [(c["frame"] + 40, f"CARD {c['name']} hold") for c in cards]
extra = [(7560, "c5_17 f7560 (patch window)"), (7700, "c5_17 f7700 (farm black; patch goes here)")]
flat = [x for r in rows for x in r] + titles + cardt + extra
want = sorted({f for f, _ in flat})
sel = "+".join(f"eq(n\\,{f-1})" for f in want)
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mp4, "-vf", f"select='{sel}',scale=480:204", "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, 204, 480, 3); assert len(fr) == len(want), (len(fr), len(want))
img = {f: Image.fromarray(fr[i]) for i, f in enumerate(want)}
tw, th, cols = 480, 204, 6; lab = 22
cells = [x for r in rows for x in r] + titles + cardt + extra
nrows = (len(cells) + cols - 1) // cols
sheet = Image.new("RGB", (cols * (tw + 6) + 6, nrows * (th + lab + 6) + 40), (16, 16, 20)); d = ImageDraw.Draw(sheet)
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
d.text((8, 10), "NVIDIA PART 2 — contact sheet: redo seams (pairs: before | after), titles, cards", fill=(240, 240, 240), font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20))
for i, (f, t) in enumerate(cells):
    x = 6 + (i % cols) * (tw + 6); y = 40 + (i // cols) * (th + lab + 6)
    d.text((x, y), t, fill=(240, 200, 120), font=F); sheet.paste(img[f], (x, y + lab))
sheet.save(out, quality=88); print(out, sheet.size, len(cells), "tiles")
