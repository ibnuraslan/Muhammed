"""Paint out the joke logo, plate word and cartoon eyes from the truck GLB's base-colour texture (1024 px).
python3 -I clean_truck_tex.py <extracted base colour png> <out png>"""
import sys
from PIL import Image, ImageFilter
im = Image.open(sys.argv[1]).convert('RGB'); k = im.size[0] / 1024
src = im.crop((int(130*k), int(60*k), int(250*k), int(170*k))).filter(ImageFilter.GaussianBlur(2))
rust = im.crop((int(560*k), int(720*k), int(700*k), int(790*k))).filter(ImageFilter.GaussianBlur(2))
for box, s in (((20, 215, 110, 325), src), ((270, 215, 365, 325), src), ((25, 600, 220, 745), rust), ((0, 830, 200, 915), rust)):
    x0, y0, x1, y1 = [int(v * k) for v in box]; im.paste(s.resize((x1 - x0, y1 - y0)), (x0, y0))
im.save(sys.argv[2])
