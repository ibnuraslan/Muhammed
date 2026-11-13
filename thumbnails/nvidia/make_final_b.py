"""Final for the approved B look: cine grade + "NVIDIA'S EX-CEO" / lime "TARGETED?" behind the people, plus the download pack."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
from cine import cine_grade, title, LIME, WHITE
from compose import load_plate
P = os.path.join(HERE, "plates"); D = os.path.join(HERE, "download_b"); os.makedirs(D, exist_ok=True)
from PIL import ImageFilter
import cine
cine._grit.__defaults__ = (5, 0.0)                       # flat, clean letters
g = cine_grade(load_plate(os.path.join(P, "targeted_final.png")), clarity=0.0, grain=0.0, bloom=0.15,
               shadows=(0.0, 0.0, 0.0), highs=(1.03, 1.0, 0.96), vignette=0.4)   # clean: no grain, no sharpening, no cool shadow tint
t = title(g, "NVIDIA'S EX-CEO", "TARGETED?", LIME, WHITE, "anton", 360, 80, matte=os.path.join(P, "targeted_final_mask.png"))
t.save(os.path.join(HERE, "nvidia_final_B.jpg"), quality=97, subsampling=0)
t.save(os.path.join(D, "nvidia_thumbnail_EXCEO_TARGETED.png")); t.save(os.path.join(D, "nvidia_thumbnail_EXCEO_TARGETED_youtube.jpg"), quality=96, subsampling=0)
g.save(os.path.join(D, "nvidia_thumbnail_notext.png")); g.save(os.path.join(D, "nvidia_thumbnail_notext_youtube.jpg"), quality=96, subsampling=0)
print("done")
