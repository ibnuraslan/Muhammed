"""Look-frame PDF: one 2560x1440 frame per page with a slim caption bar."""
import os, sys
from PIL import Image, ImageDraw, ImageFont
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FR = os.path.join(D, "out", "frames")
FONT = ImageFont.truetype(os.path.join(D, "assets", "fonts", "CourierPrime-Regular.ttf"), 34)
PAGES = [("a_sighting.png", "(a)  4 December 1872, shortly after noon. From the Dei Gratia: the Mary Celeste on the open Atlantic."),
         ("b_cabin.png", "(b)  The captain's cabin. Deveau by lantern light: the bedding is wet; an impression on the bed."),
         ("c_rail.png", "(c)  A section of rail taken out and laid flat. The gap where the boat was launched.")]
pages = []
for fn, cap in PAGES:
    im = Image.open(os.path.join(FR, fn)).convert("RGB")
    w, h = im.size; bar = 90
    pg = Image.new("RGB", (w, h + bar), (12, 12, 12)); pg.paste(im, (0, 0))
    dr = ImageDraw.Draw(pg); dr.text((40, h + 26), cap, font=FONT, fill=(225, 220, 210))
    dr.text((w - 560, h + 26), "Seldom · look frames · Cycles", font=FONT, fill=(140, 140, 135))
    pages.append(pg)
out = os.path.join(D, "out", "MaryCeleste_look_frames.pdf")
pages[0].save(out, save_all=True, append_images=pages[1:], resolution=150, quality=92)
print(out, os.path.getsize(out))
