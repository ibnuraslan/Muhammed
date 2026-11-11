"""Labelled preview sheet (2 columns, a dark label bar over each still), like nvidia_doc/out/ch1_preview.

  python sheet.py out.jpg "1A Truck rolls in=path/a.png" "1B Rope pulled tight=path/b.png" ...
"""
import sys
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"


def sheet(out, items, W=960, bar=44):
    H = int(W * 816 / 1920)
    rows = (len(items) + 1) // 2
    img = Image.new("RGB", (2 * W, rows * (H + bar)), (14, 16, 20))
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype(FONT, 26)
    except Exception:
        f = ImageFont.load_default()
    for k, (label, path) in enumerate(items):
        x = (k % 2) * W; y = (k // 2) * (H + bar)
        im = Image.open(path).convert("RGB").resize((W, H), Image.LANCZOS)
        img.paste(im, (x, y + bar))
        d.text((x + 14, y + 8), label, font=f, fill=(235, 235, 235))
    img.save(out, quality=88)
    return out


if __name__ == "__main__":
    items = [a.split("=", 1) for a in sys.argv[2:]]
    sheet(sys.argv[1], items)
