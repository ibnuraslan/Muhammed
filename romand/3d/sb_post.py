"""Romand storyboard post: lay the kit overlays (brand_overlays/kit_v1/seldom_kit.py) on each key frame, then build the
contact sheet and the PDF.
    KIT=<kit_v1 dir> RAW=<dir of 3D key frames> python3 sb_post.py 1
Writes romand/review/p<n>/frames/<ID>.jpg (1920x1080, overlay at its settled moment), contact_sheet.jpg, storyboard.pdf."""
import os, sys, json, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
KIT = os.environ["KIT"]; RAW = os.environ["RAW"]
sys.path.insert(0, KIT)
import seldom_kit as K
PART = int(sys.argv[1]) if len(sys.argv) > 1 else 1
OUT = os.path.join(ROOT, "review", f"p{PART}"); FR = os.path.join(OUT, "frames"); os.makedirs(FR, exist_ok=True)
SH = json.load(open(os.path.join(ROOT, "shots", "shots.json")))[str(PART)]
W, H = 1920, 1080


def plate(sid):
    p = os.path.join(RAW, sid + ".png")
    if not os.path.exists(p):
        return None
    return Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS)


def black():
    return Image.new("RGB", (W, H), (0, 0, 0))


def crop(sid, box):
    """A portrait crop from one of our own renders (faceless mannequins only), box in 960x540 plate pixels."""
    p = os.path.join(RAW, sid + ".png")
    im = Image.open(p).convert("RGB")
    return im.crop(box)


# Overlays per shot: (template, params, t) -- t = the settled moment shown on the board. Plates: None = own render.
def overlays():
    ph = {}
    try:
        ph["chantal"] = crop("P1-13", (360, 20, 600, 330))
        ph["romand"] = crop("P1-26", (195, 270, 335, 440))
        ph["florence"] = crop("P1-26", (255, 180, 355, 300))
        ph["aime"] = crop("P1-26", (410, 230, 640, 400))
        ph["kids"] = crop("P1-21", (240, 160, 780, 440))      # children: no portrait, their boots by the door
        ph["paris"] = crop("P1-18", (200, 60, 800, 400))
        ph["lyon"] = crop("P1-33", (150, 60, 810, 430))
    except Exception as e:
        print("photo crops:", e)
    g = ph.get
    fam_cards = [dict(photo=g("romand"), name="JEAN-CLAUDE ROMAND", role="\"WHO RESEARCHER\"", pos=(0.5, 0.06), t=0.4),
                 dict(photo=g("florence"), name="FLORENCE", role="WIFE", pos=(0.2, 0.40)),
                 dict(photo=g("kids"), name="CAROLINE & ANTOINE", role="CHILDREN", pos=(0.5, 0.40)),
                 dict(photo=g("aime"), name="AIME & ANNE-MARIE", role="PARENTS", pos=(0.8, 0.40))]
    fam_links = [(0, 1, 1.0, "WIFE"), (0, 2, 2.0, "CHILDREN"), (0, 3, 3.0, "PARENTS")]
    return {
        "P1-09": [("phrase", dict(text="a nylon cord"), 2.2)],
        "P1-13": [("person", dict(photo=g("chantal"), name="CHANTAL", role="PARIS"), 2.2)],
        "P1-16": [("phrase", dict(text="a doctor"), 1.8)],
        "P1-18": [("place", dict(photo=g("paris"), name="PARIS", country="FRANCE", coords="48.8566° N  2.3522° E"), 2.6)],
        "P1-24": [("title", dict(text="[ FILM TITLE ]", sub="PLACEHOLDER UNTIL THE TITLE IS CHOSEN"), 3.9)],
        "P1-25": [("disclaimer", dict(discretion=True), 6.0)],
        "P1-26": [("person", dict(photo=g("romand"), name="JEAN-CLAUDE ROMAND", role="\"WHO RESEARCHER\""), 2.2)],
        "P1-27": [("linkboard", dict(cards=fam_cards, links=fam_links), 6.2)],
        "P1-28": [("phrase", dict(text="no job"), 1.6)],
        "P1-29": [("phrase", dict(text="no qualification"), 2.2)],
        "P1-31": [("datestamp", dict(top="JANUARY", big="1993"), 1.8)],
        "P1-32": [("timeline", dict(events=(("1975", "", "LYON"), ("1980", "", "MARRIAGE"), ("1988", "", "THE MONEY"),
                                            ("JAN 1993", "", "THE MURDERS")), now=0), 4.0)],
        "P1-33": [("place", dict(photo=g("lyon"), name="LYON", country="FRANCE", coords="45.7640° N  4.8357° E"), 2.6)],
    }


PLATES2D = {"P1-24": "P1-20", "P1-25": None, "P1-27": None, "P1-32": None}


def build_frames():
    ov = overlays()
    done = []
    for r in SH["rows"]:
        sid = r["id"]
        if sid in PLATES2D:
            src = PLATES2D[sid]
            bg = plate(src) if src else black()
        else:
            bg = plate(sid)
        if bg is None:
            print("missing plate", sid); continue
        for (tpl, params, t) in ov.get(sid, []):
            fr = K.TEMPLATES[tpl](t, **params)
            bg = K.composite(bg, fr)
        bg.save(os.path.join(FR, sid + ".jpg"), quality=90)
        done.append(sid)
    return done


def fnt(size, bold=False):
    return ImageFont.truetype(os.path.join(KIT, "fonts", "Oswald-Medium.ttf" if bold else "IBMPlexMono-Regular.ttf"), size)


def card(r, tw=640):
    """One storyboard cell: frame + caption (ID, start, duration, VO, camera, action, overlay, SFX)."""
    th = tw * 9 // 16
    im = Image.open(os.path.join(FR, r["id"] + ".jpg")).resize((tw, th), Image.LANCZOS)
    cap_h = 250
    c = Image.new("RGB", (tw, th + cap_h), (14, 13, 11)); c.paste(im, (0, 0)); d = ImageDraw.Draw(c)
    y = th + 10
    d.text((10, y), f"{r['id']}", font=fnt(30, True), fill=(227, 255, 0))
    m, s = divmod(r["t0"], 60)
    d.text((150, y + 8), f"{int(m)}:{s:04.1f}  ·  {r['dur']:.1f}s  ·  {r['set']} / {r['kind']}", font=fnt(17), fill=(170, 165, 150))
    y += 44
    vo = r["vo"] or "(no VO)"
    for ln in textwrap.wrap("VO: " + vo, 62)[:3]:
        d.text((10, y), ln, font=fnt(17), fill=(243, 241, 234)); y += 22
    for lab, key, n in (("CAM", "cam", 1), ("ACT", "act", 3), ("OVL", "ov", 1), ("SFX", "sfx", 1)):
        if r[key]:
            for ln in textwrap.wrap(f"{lab}: {r[key]}", 66)[:n]:
                d.text((10, y), ln, font=fnt(15), fill=(150, 146, 136) if lab != "OVL" else (200, 220, 90)); y += 19
    return c


def sheets(done):
    rows = [r for r in SH["rows"] if r["id"] in done]
    cells = [card(r) for r in rows]
    cw, chh = cells[0].size
    cols = 4; gap = 14
    # one big contact sheet
    nrows = (len(cells) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cw + (cols + 1) * gap, nrows * chh + (nrows + 1) * gap + 90), (6, 6, 5))
    d = ImageDraw.Draw(sheet)
    d.text((gap, 20), f"ROMAND · PART {PART} STORYBOARD · key frames (960x540 preview, low spp, OIDN; overlays from kit_v1)",
           font=fnt(40, True), fill=(243, 241, 234))
    for i, c in enumerate(cells):
        x = gap + (i % cols) * (cw + gap); y = 90 + gap + (i // cols) * (chh + gap)
        sheet.paste(c, (x, y))
    sheet.save(os.path.join(OUT, "contact_sheet.jpg"), quality=86)
    small = sheet.resize((sheet.width // 2, sheet.height // 2), Image.LANCZOS); small.save(os.path.join(OUT, "contact_sheet_small.jpg"), quality=85)
    # PDF: 6 cells per landscape page
    pages = []; per = 6; pc = 3
    for k in range(0, len(cells), per):
        pg = Image.new("RGB", (pc * cw + (pc + 1) * gap, 2 * chh + 3 * gap + 70), (6, 6, 5)); dd = ImageDraw.Draw(pg)
        dd.text((gap, 16), f"ROMAND · PART {PART} STORYBOARD   ({k // per + 1}/{(len(cells) + per - 1) // per})", font=fnt(34, True), fill=(243, 241, 234))
        for j, c in enumerate(cells[k:k + per]):
            pg.paste(c, (gap + (j % pc) * (cw + gap), 70 + gap + (j // pc) * (chh + gap)))
        pages.append(pg)
    pages[0].save(os.path.join(OUT, "storyboard.pdf"), save_all=True, append_images=pages[1:], resolution=150)
    print("sheet", sheet.size, "pages", len(pages))


if __name__ == "__main__":
    d = build_frames()
    print(len(d), "frames")
    sheets(d)
