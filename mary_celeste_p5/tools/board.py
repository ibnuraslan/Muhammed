"""Storyboard sheet: overlays the exact-script caption and the slide-in card (shared callout.py, card shown at
rest) on each rendered 3D frame, writes review/Sxx.jpg, review/contact_sheet.jpg and review/STORYBOARD.md.

    python3 tools/board.py [frames_dir]
"""
import os, sys, glob
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); P5 = os.path.join(HERE, "..")
sys.path.insert(0, P5); sys.path.insert(0, os.path.join(P5, "..", "nvidia_doc", "scenes"))
import callout as CO
from shots import SHOTS

FR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(P5, "out", "frames")
REV = os.path.join(P5, "review"); os.makedirs(REV, exist_ok=True)
PHOTOS = os.path.join(P5, "assets", "photos")
WPM = 145.0


def placeholder(key):
    """Until the free-licence photo is in assets/photos/<key>.jpg: a neutral print marked as pending."""
    p = os.path.join(PHOTOS, key + ".jpg")
    if os.path.exists(p):
        return p
    os.makedirs(os.path.join(P5, "out", "ph"), exist_ok=True)
    q = os.path.join(P5, "out", "ph", key + ".png")
    im = Image.new("L", (460, 500), 120); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(CO.ROLE_FONT, 40)
    d.text((230, 230), "PHOTO", font=f, fill=200, anchor="mm"); d.text((230, 280), "PENDING", font=f, fill=200, anchor="mm")
    im.save(q); return q


rows = []; t = 0.0
thumbs = []
for sid, scene, vo, see, cam, sfx, card in SHOTS:
    words = len(vo.split()); dur = max(2.0, words / WPM * 60 + 0.35) if vo else 9.0
    src = os.path.join(FR, sid + ".png")
    if os.path.exists(src):
        # the frame stays clean: no burned-in cards or captions (the user adds them in CapCut); the shot label sits
        # on a strip under the frame, outside the picture
        fr = Image.open(src).convert("RGB").resize((1280, 720), Image.LANCZOS)
        im = Image.new("RGB", (1280, 756), (18, 18, 18)); im.paste(fr, (0, 0))
        d = ImageDraw.Draw(im); f = ImageFont.truetype(CO.ROLE_FONT, 22)
        d.text((12, 726), f"{sid}  {t:5.1f}s  ({dur:.1f}s)" + (f"   [card in edit: {card[1]}]" if card else ""), font=f, fill=(220, 220, 220))
        out = os.path.join(REV, sid + ".jpg"); im.save(out, quality=90)
        thumbs.append((sid, im))
    rows.append((sid, t, dur, vo, see, cam, sfx, card))
    t += dur

# contact sheet, 4 across
cw, ch = 480, 284; cols = 4; n = len(thumbs); rws = (n + cols - 1) // cols
sheet = Image.new("RGB", (cols * cw + (cols + 1) * 8, rws * (ch + 8) + 8), (18, 18, 18))
for i, (sid, im) in enumerate(thumbs):
    sheet.paste(im.resize((cw, ch), Image.LANCZOS), (8 + (i % cols) * (cw + 8), 8 + (i // cols) * (ch + 8)))
sheet.save(os.path.join(REV, "contact_sheet.jpg"), quality=88)

with open(os.path.join(REV, "STORYBOARD.md"), "w") as f:
    f.write("# Part 5 storyboard — \"The Ship That Came Back Without Its Crew\"\n\n")
    f.write("Section: \"A boat could also have been lowered as a temporary precaution.\" → \"...were never found.\" "
            f"Total ≈ {t:.0f} s at {WPM:.0f} wpm (retimed to the VO in the edit). Frames are real Cycles renders of the 3D scenes "
            "(half res, low samples). Frames are clean: captions and cards are added by the user in CapCut (Card column = what goes there).\n\n")
    f.write("| Shot | Start | Dur | VO (exact) | Picture | Camera | SFX | Card |\n|---|---|---|---|---|---|---|---|\n")
    for sid, t0, dur, vo, see, cam, sfx, card in rows:
        c = f"{card[0]}: {card[1]} / {card[2]}" if card else ""
        f.write(f"| [{sid}]({sid}.jpg) | {t0:.1f} | {dur:.1f} | {vo} | {see} | {cam} | {sfx} | {c} |\n")
print("board:", len(thumbs), "frames,", f"{t:.1f}s")
