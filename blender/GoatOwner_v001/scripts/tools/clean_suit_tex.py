"""Remove the chest emblem from MakeHuman female_casualsuit01 (rescuer, official B).  python3 -I clean_suit_tex.py <in png> <out png>"""
import sys
from PIL import Image, ImageFilter
im = Image.open(sys.argv[1]).convert('RGB'); W, H = im.size
src = im.crop((int(0.60 * W), int(0.13 * H), int(0.70 * W), int(0.33 * H))).filter(ImageFilter.GaussianBlur(1))
box = (int(0.712 * W), int(0.150 * H), int(0.872 * W), int(0.335 * H))
im.paste(src.resize((box[2] - box[0], box[3] - box[1])), box[:2])
im.save(sys.argv[2])
