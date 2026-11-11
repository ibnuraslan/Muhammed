"""python3 04b_png8.py <tex_dir> : rewrite 16-bit PNGs from 04_slim_textures.py as 8-bit (half the packed size)"""
import sys, glob
import numpy as np
from PIL import Image
for f in glob.glob(sys.argv[1] + "/*.png"):
    a = np.array(Image.open(f))
    if a.dtype != np.uint8: a = (a / 257).astype(np.uint8)
    Image.fromarray(a).save(f, optimize=True)
