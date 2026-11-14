import os, sys, textwrap
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "/home/user/Muhammed/projects/drain-diamond/scenes")
T = "/home/user/Muhammed/projects/drain-diamond/out/test"
src = open("/home/user/Muhammed/projects/drain-diamond/scenes/make_master.py").read()
ns = {}; exec(src[src.index("CHAPTERS = {"):src.index("\n}\n") + 3], ns); CH = ns["CHAPTERS"]
NEW = {  # inserted / replaced v2 shots: (after_or_replace, key, label, dur)
    "intro": [("after", "drain_container", "void_ring", "Ring  'a thirty-one-carat diamond ... came from Harry Winston' (object on black, jeweller's tag '31 ct')", 3.5)],
    "ch2": [("after", "boutique2_getaway", "void_suitcase", "Suitcase  'jewelry worth seventy-one million euros' (luggage tag typed '71 000 000 EUR')", 3.5)],
    "ch3": [("after", "unit_read", "void_cctv", "Prints  'Investigators are also looking at one of the guards' (CCTV stills, timestamps 07:52-07:54)", 4.0)],
    "ch4": [("replace", "court_file", "void_dna", "Evidence  'traces of their DNA in the boutique' (swab rack, sealed bag 'SCELLE N 14')", 3.5)],
}
TITLES = {"intro": "Intro", "ch1": "Ch 1 · The Service Door", "ch2": "Ch 2 · The Front Door", "ch3": "Ch 3 · A Little Cement", "ch4": "Ch 4 · The Night Before"}
LEAD = {"intro": 2.5, "ch1": 3.0, "ch2": 3.0, "ch3": 3.0, "ch4": 3.0}
seq = []
t = 0.0; n = 0
for ch in ("intro", "ch1", "ch2", "ch3", "ch4"):
    shots = [(k, lab, 9.0, False) for k, lab in CH[ch]]
    for mode, ref, key, lab, dur in NEW.get(ch, []):
        i = [s[0] for s in shots].index(ref)
        if mode == "after":
            shots.insert(i + 1, (key, lab, dur, True))
        else:
            shots[i] = (key, lab, dur, True)
    t += LEAD[ch] if ch != "intro" else 0.0
    for k, lab, dur, new in shots:
        n += 1
        st, mv = k.split("_", 1)
        seq.append(dict(n=n, ch=ch, key=k, path=os.path.join(T, st, mv, "plate.png"), lab=lab, t=t, new=new))
        t += dur
W, TH = 600, 255; COLS = 3; PAD = 14; CAP = 112
fb = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 19)
fr = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Regular.otf", 16)
fh = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 30)
# layout rows by chapter
rows = []; cur = None
for s in seq:
    if s["ch"] != cur:
        rows.append(("H", s["ch"])); cur = s["ch"]; line = []
        rows.append(("R", line))
    if len(rows[-1][1]) == COLS:
        line = []; rows.append(("R", line))
    rows[-1][1].append(s)
H = 90 + sum(56 if r[0] == "H" else TH + CAP + PAD for r in rows) + 40
img = Image.new("RGB", (COLS * (W + PAD) + PAD, H), (16, 16, 18)); d = ImageDraw.Draw(img)
d.text((PAD, 20), f"The $25 Million Hidden in a Drain · STORYBOARD (full, {len(seq)} shots, ~{int(t // 60)}:{int(t % 60):02d})   ·   orange = new v2 shot", fill=(235, 235, 235), font=fh)
y = 90
for r in rows:
    if r[0] == "H":
        d.text((PAD, y + 12), TITLES[r[1]] + ("" if r[1] == "intro" else f"   (title card, {LEAD[r[1]]:.1f} s lead before the voice)"), fill=(240, 190, 120), font=fb); y += 56; continue
    for i, s in enumerate(r[1]):
        x = PAD + i * (W + PAD)
        im = Image.open(s["path"]).convert("RGB").resize((W, TH))
        img.paste(im, (x, y))
        if s["new"]:
            d.rectangle([x, y, x + W - 1, y + TH - 1], outline=(240, 140, 40), width=4)
        mm, ss = divmod(int(s["t"]), 60)
        tag = f"#{s['n']:02d}  {s['ch'].upper()}  ~{mm}:{ss:02d}  {s['key']}" + ("   NEW v2" if s["new"] else "")
        d.text((x, y + TH + 6), tag, fill=(240, 150, 60) if s["new"] else (225, 225, 225), font=fb)
        for k, ln in enumerate(textwrap.wrap(s["lab"], 64)[:4]):
            d.text((x, y + TH + 32 + 19 * k), ln, fill=(185, 185, 185), font=fr)
    y += TH + CAP + PAD
out = "/home/user/Muhammed/projects/drain-diamond/review/STORYBOARD_FULL.jpg"
img.save(out, quality=86); print(out, img.size, len(seq), round(t))
