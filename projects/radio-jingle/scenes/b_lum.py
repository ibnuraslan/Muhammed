"""Hub check: mean luminance of each graded still (same grade as the sheets). Day shots must be >= 0.18.
  python b_lum.py [t]   -> one line per chat-B shot: label, day/night, mean luminance (sRGB-encoded Rec.709), PASS/FAIL
"""
import os, sys, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "nvidia_doc", "scenes"))
import numpy as np
from PIL import Image
import grade, b_shots

T = sys.argv[1] if len(sys.argv) > 1 else "0.5"
# night / deliberately dark interiors (the subject must still read; checked by eye, not by this threshold)
NIGHT = {("b_workshop", m) for m in ("solder", "letters")} | {("b_home81", "game"), ("b_home81", "moped"), ("b_home81", "curtain"),
         ("b_interro", "retract"), ("b_interro", "leave"), ("b_north", "watch"), ("b_north", "lock"), ("b_north", "dawn"), ("b_north", "away"),
         ("b_michael", "replay"), ("b_michael", "objection"), ("b_michael", "window"), ("b_chain", "booth"), ("b_chain", "mouth"),
         ("b_hall", "line_end"), ("b_hall", "offhook"), ("b_court", "lights"), ("b_court", "pullback"), ("b_archive", "tube"),
         ("b_media", "scrub"), ("b_media", "paused"), ("b_ch5", "gate"), ("b_ch5", "wall"), ("b_chain", "poles")}
tmp = tempfile.mkdtemp(); fails = 0
for ch, rows in b_shots.CHAPTERS.items():
    for s, m, lab in rows:
        d = f"/tmp/claude-0/st/{s}_{m}_{T}"
        if not os.path.exists(os.path.join(d, "plate.exr")):
            print(f"{lab:46s} MISSING"); continue
        meta = json.load(open(os.path.join(d, "plate.json"))); out = os.path.join(tmp, "g.png")
        grade.grade_file(os.path.join(d, "plate.exr"), out, look="cinematic", exposure=meta["exposure"], cine=meta.get("cine") or None)
        a = np.asarray(Image.open(out).convert("RGB"), dtype=np.float32) / 255.0
        lum = float((a @ np.array([0.2126, 0.7152, 0.0722])).mean())
        night = (s, m) in NIGHT
        ok = night or lum >= 0.18
        fails += not ok
        print(f"{lab:46s} {'night' if night else 'day  '} {lum:.3f} {'ok' if ok else 'FAIL'}")
print("FAILS", fails)
