"""Labelled contact sheet of thumbnail renders (labels are for review only, never on the thumbnails).
  python contact.py OUT.jpg "1 Watched=path.png" "2 Flash=path.png" ...
Also draws a phone-size (320x180) strip under each tile, to judge readability at a glance."""
import sys
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"


def sheet(out, items, cols=2, tw=960):
    th = tw * 9 // 16
    lab = 46
    rows = (len(items) + cols - 1) // cols
    W, H = cols * tw + (cols + 1) * 12, rows * (th + lab + 12) + 12
    img = Image.new("RGB", (W, H), (14, 15, 18))
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype(FONT, 26)
    except Exception:
        f = ImageFont.load_default()
    for k, (label, path) in enumerate(items):
        r, c = divmod(k, cols)
        x = 12 + c * (tw + 12); y = 12 + r * (th + lab + 12)
        d.text((x + 4, y + 8), label, font=f, fill=(235, 235, 235))
        t = Image.open(path).convert("RGB").resize((tw, th), Image.LANCZOS)
        img.paste(t, (x, y + lab))
        small = Image.open(path).convert("RGB").resize((192, 108), Image.LANCZOS)   # phone-size check, bottom-right
        img.paste(small, (x + tw - 192 - 8, y + lab + th - 108 - 8))
        d.rectangle((x + tw - 192 - 9, y + lab + th - 108 - 9, x + tw - 8, y + lab + th - 8), outline=(235, 235, 235))
    img.save(out, quality=92)


if __name__ == "__main__":
    items = [a.split("=", 1) for a in sys.argv[2:]]
    sheet(sys.argv[1], items)
