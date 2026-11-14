"""Typewriters final B: clean grade + "THE SOVIETS SPIED ON AMERICA" / lime "USING A TYPEWRITER" behind the machine."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import cine
cine._grit.__defaults__ = (5, 0.0)
from cine import cine_grade, title, LIME, WHITE
from compose import load_plate
P = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "plates")
OUT = sys.argv[2] if len(sys.argv) > 2 else HERE
D = os.path.join(OUT, "download_b"); os.makedirs(D, exist_ok=True)
g = cine_grade(load_plate(os.path.join(P, "tw_b.png")), clarity=0.0, grain=0.0, bloom=0.15,
               shadows=(0.0, 0.0, 0.0), highs=(1.03, 1.0, 0.96), vignette=0.45)
t = title(g, "THE SOVIETS SPIED ON AMERICA", "USING A TYPEWRITER", LIME, WHITE, "anton", 190, 150, kicker_size=50, tracking_k=8,
          matte=os.path.join(P, "tw_b_mask.png"))
t.save(os.path.join(OUT, "typewriters_final_B.jpg"), quality=97, subsampling=0)
t.save(os.path.join(D, "typewriters_thumbnail_TYPEWRITER.png")); t.save(os.path.join(D, "typewriters_thumbnail_TYPEWRITER_youtube.jpg"), quality=96, subsampling=0)
g.save(os.path.join(D, "typewriters_thumbnail_notext.png")); g.save(os.path.join(D, "typewriters_thumbnail_notext_youtube.jpg"), quality=96, subsampling=0)
print("done")
