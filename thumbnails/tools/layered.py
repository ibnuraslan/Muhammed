"""Text behind the subject: draw the word over the plate, then put the matted subject back on top."""
from PIL import Image
from compose import load_plate, grade, draw_text, W, H


def layered(plate, mask, lines, x, y, size, **kw):
    base = grade(load_plate(plate), vignette=kw.pop("vignette", 0.45))
    txt = draw_text(base, lines, x, y, size, **kw)
    m = Image.open(mask).split()[-1].resize((W, H), Image.LANCZOS)
    return Image.composite(base, txt, m)
