"""Flatten embossed lettering/logos in the truck GLB's normal map (same regions as clean_truck_tex.py; the plate word is embossed here).
python3 -I clean_truck_normal.py <in png> <out png>"""
import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert('RGB'); k = im.size[0] / 1024
for box in ((20, 215, 110, 325), (270, 215, 365, 325), (25, 600, 220, 745), (0, 830, 200, 915)):
    x0, y0, x1, y1 = [int(v * k) for v in box]
    im.paste(Image.new('RGB', (x1 - x0, y1 - y0), (128, 128, 255)), (x0, y0))
im.save(sys.argv[2])
