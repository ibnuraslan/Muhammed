"""python3 make_icons.py : lane-sign pictograms for 02_build_scene.py"""
import os
def icon(path, kind):
    from PIL import Image as _I, ImageDraw as _D
    im = _I.new("RGB", (256, 128), (20, 40, 70)); d = _D.Draw(im)
    if kind == "shoe":
        d.polygon([(40, 90), (40, 50), (70, 45), (95, 70), (140, 75), (150, 90)], fill=(240, 240, 240))
        d.line([(170, 70), (220, 70)], fill=(255, 200, 60), width=10); d.polygon([(220, 55), (245, 70), (220, 85)], fill=(255, 200, 60))
    else:
        d.rectangle((60, 50, 140, 100), fill=(240, 240, 240)); d.rectangle((85, 35, 115, 50), outline=(240, 240, 240), width=6)
        d.line([(170, 70), (220, 70)], fill=(255, 200, 60), width=10); d.polygon([(220, 55), (245, 70), (220, 85)], fill=(255, 200, 60))
    im.save(path)
for k in ("shoe", "bag"):
    icon("/opt/assets/sb_tex/sign_%s.png" % k, k)
