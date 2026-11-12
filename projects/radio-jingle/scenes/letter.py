"""The cut-out ransom letter as an image: newspaper letters snipped out one by one, glued slightly crooked on a sheet.
Text (short, correctly spelled German): "2 MILLIONEN" / "GEBRAUCHTE" / "HUNDERTER". Nothing else is readable.
python letter.py -> nvidia_doc/assets/generated/rj_letter.png"""
import os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "..", "nvidia_doc", "assets", "generated", "rj_letter.png")
F = ["/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", "/usr/share/fonts/truetype/freefont/FreeSansBoldOblique.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "/usr/share/fonts/truetype/crosextra/Caladea-Regular.ttf",
     os.path.join(HERE, "..", "..", "..", "nvidia_doc", "assets", "fonts", "RobotoSlab-ExtraBold.ttf")]
LINES = ["2 MILLIONEN", "GEBRAUCHTE", "HUNDERTER"]


def make(path=OUT, W=1240, H=1754, seed=7):
    rnd = random.Random(seed)
    sheet = Image.new("RGB", (W, H), (232, 228, 214))
    d = ImageDraw.Draw(sheet)
    for _ in range(4000):                                   # faint paper grain
        x, y = rnd.randrange(W), rnd.randrange(H); g = rnd.randrange(215, 236)
        d.point((x, y), fill=(g, g - 3, g - 14))
    y = 300
    for line in LINES:
        size_line = rnd.randint(84, 96)
        pieces = []
        for ch in line:
            if ch == " ":
                pieces.append(None); continue
            sz = int(size_line * rnd.uniform(0.85, 1.15))
            f = ImageFont.truetype(rnd.choice(F), sz)
            bb = f.getbbox(ch); w, h = bb[2] - bb[0] + 26, bb[3] - bb[1] + 26
            bg = rnd.choice([(226, 222, 206), (238, 236, 226), (214, 210, 196), (60, 58, 56), (230, 226, 210)])
            fg = (24, 22, 22) if sum(bg) > 300 else (236, 232, 222)
            tile = Image.new("RGBA", (w, h), bg + (255,))
            td = ImageDraw.Draw(tile)
            for _ in range(6):                               # newsprint: faint lines of tiny text-like grey dashes
                yy = rnd.randrange(h); td.line((0, yy, w, yy), fill=tuple(max(0, c - 18) for c in bg) + (255,), width=1)
            td.text((13 - bb[0], 13 - bb[1]), ch, font=f, fill=fg)
            tile = tile.rotate(rnd.uniform(-7, 7), resample=Image.BICUBIC, expand=True)
            pieces.append(tile)
        widths = [p.size[0] if p else 60 for p in pieces]
        x = (W - sum(widths) - 4 * len(pieces)) // 2
        for p in pieces:
            if p is None:
                x += 60; continue
            sh = Image.new("RGBA", p.size, (0, 0, 0, 0)); sh.putalpha(p.split()[3].point(lambda a: a * 0.25))
            sheet.paste((40, 36, 30), (x + 4, y + 5), sh.split()[3])
            sheet.paste(p, (x, y + rnd.randint(-10, 10)), p)
            x += p.size[0] + rnd.randint(0, 8)
        y += size_line + 90
    sheet = sheet.filter(ImageFilter.GaussianBlur(0.6))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sheet.save(path)
    return path


if __name__ == "__main__":
    print(make())
