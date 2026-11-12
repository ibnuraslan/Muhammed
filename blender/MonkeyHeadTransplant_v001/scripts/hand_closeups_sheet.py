import sys, os, json
from PIL import Image, ImageDraw
D, OUT = sys.argv[1], sys.argv[2]
lab = json.load(open(os.path.join(D, "labels.json")))
S = Image.new("RGB", (270 * 6, 480 * ((len(lab) + 5) // 6)))
for k, L in enumerate(lab):
    im = Image.open(os.path.join(D, "c%02d.jpg" % L["i"])).convert("RGB"); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 270, 26), fill=(0, 0, 0)); d.text((3, 2), "f%d %s.%s" % (L["frame"], L["rig"], L["side"]), fill=(255, 255, 0)); d.text((3, 13), L["label"][:44], fill=(255, 255, 255))
    S.paste(im, ((k % 6) * 270, (k // 6) * 480))
S.save(OUT, quality=85); print(OUT)
