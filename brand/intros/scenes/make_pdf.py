import sys, os
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from PIL import Image
W, H = 1920, 1080
src, out, pre = sys.argv[1], sys.argv[2], sys.argv[3]
pdfmetrics.registerFont(TTFont("R", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("B", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("M", "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf"))
BG, FG, DIM, ACC = (0.06,0.06,0.07), (0.93,0.93,0.9), (0.62,0.62,0.6), (0.85,0.95,0.1)
def img(name):
    p = os.path.join(src, pre + name + ".png"); j = p[:-4] + "_pdf.jpg"
    Image.open(p).convert("RGB").save(j, quality=86); return ImageReader(j)
def wrap(c, txt, x, y, w, font, size, lead, color):
    c.setFont(font, size); c.setFillColorRGB(*color); line = ""
    for word in txt.split():
        t = (line + " " + word).strip()
        if c.stringWidth(t, font, size) > w: c.drawString(x, y, line); y -= lead; line = word
        else: line = t
    if line: c.drawString(x, y, line); y -= lead
    return y
C = [
 ("c1_searchlight", "1  SWEEP", "searchlights", "6 s",
  "Night, fog, a perimeter fence. Tower searchlights hunt through the fog, miss, swing back, and lock one by one onto the 3D logo standing in the yard.",
  "Wind, chain-link rattle, a heavy arc-lamp CLUNK as each light locks, sub boom on the last one."),
 ("c2_stamp", "2  STAMPED", "case file", "5 s",
  "A lamp-lit desk and a closed case file. A wooden rubber stamp drops into frame and slams down. It lifts away and the name stays in wet ink; loose sheets jump from the hit.",
  "Room tone, a clock ticking, a doubled wooden THUNK with a low hit, paper flutter."),
 ("c3_lighthouse", "3  BEACON", "lighthouse", "7 s",
  "A stormy bay. The lighthouse beam swings across the lens and flares white. On its next pass it lands on the headland, where a weathered iron Seldom sign stands, and holds there.",
  "Surf, rain, the hum of the turning lamp; a low foghorn note on the reveal."),
 ("c4_archive", "4  DUST", "archive", "6 s",
  "An endless archive aisle with one shaft of window light. A box slides out on its own, dust drifts off the lid into the light, and a brass Seldom plate shows underneath.",
  "Fluorescent buzz, a cardboard scrape, one breath of air, shimmering dust, a single low piano note."),
 ("c5_ink", "5  BLOOM", "ink in water", "6 s",
  "A dark water tank. One drop falls and yellow pigment blooms in slow, curling clouds that gather and set into the solid letters.",
  "Muffled underwater room, a drop PLINK, a reversed swell, a deep bubble rumble, a soft low tone on the logo."),
 ("c6_projector", "6  REEL", "old cinema", "6 s",
  "An empty old cinema. A 16 mm projector clatters to life, the beam cuts through the dust over the seats, film leader flickers, and the screen settles on the logo.",
  "Motor whirr, film flutter, sprocket clicks slowing down, mains hum, a soft bulb pop."),
 ("c7_uv", "7  LATENT", "forensic UV", "5 s",
  "A pitch-black evidence table. A UV torch clicks on and its violet pool sweeps past a glass, a marker and keys, then finds a hidden latent print that glows into the logo.",
  "Torch click, a high ballast whine, glove creak, a glow shimmer, a low hit."),
 ("c8_match", "8  STRIKE", "match", "5 s",
  "Total black. A match strikes, flares and steadies. Its small warm light finds an old brick wall and a rusted iron Seldom sign as smoke curls up.",
  "Silence, then the scratch and flare of the match, the breath of the flame, one heartbeat-like low hit."),
]
c = canvas.Canvas(out, pagesize=(W, H)); c.setTitle("Seldom channel intros, concepts")
def page_bg():
    c.setFillColorRGB(*BG); c.rect(0, 0, W, H, fill=1, stroke=0)
# ---------------- page 1: the 8 concepts
page_bg()
c.setFont("B", 34); c.setFillColorRGB(*FG); c.drawString(40, H-62, "Seldom: 8 channel intro concepts")
c.setFont("R", 17); c.setFillColorRGB(*DIM)
c.drawString(40, H-92, "Each one is 4-8 s, works for any film, and ends on the Seldom name. Real 3D in Blender. Final output 2560x1440, 24 fps. Frames below are concept renders. Sound notes are for the sound chat.")
mx, gap, cols = 40, 24, 4
tw = (W - 2*mx - gap*(cols-1)) / cols; ih = tw * 9/16
for i, (f, title, tag, dur, idea, snd) in enumerate(C):
    col, row = i % cols, i // cols
    x = mx + col*(tw+gap); ytop = H - 120 - row*475
    c.drawImage(img(f), x, ytop-ih, tw, ih)
    y = ytop - ih - 30
    c.setFont("B", 21); c.setFillColorRGB(*ACC); c.drawString(x, y, title)
    c.setFont("R", 15); c.setFillColorRGB(*DIM); c.drawRightString(x+tw, y, tag + "  ·  " + dur)
    y = wrap(c, idea, x, y-24, tw, "R", 14.5, 19, FG)
    wrap(c, "Sound: " + snd, x, y-4, tw, "R", 13, 17, DIM)
c.showPage()
# ---------------- page 2: viewer discretion opener
page_bg()
c.setFont("B", 34); c.setFillColorRGB(*FG); c.drawString(40, H-62, "Viewer discretion opener: 3 scripts, 3 ways to show it")
iw = 900; c.drawImage(img("c9_telegram"), W-40-iw, H-110-iw*9/16, iw, iw*9/16)
c.setFont("R", 14); c.setFillColorRGB(*DIM)
c.drawString(W-40-iw, H-130-iw*9/16, "Concept render for presentation A: the warning arrives as a period telegram (script 1).")
x, y, w = 40, H-125, W-40-iw-70
c.setFont("B", 22); c.setFillColorRGB(*ACC); c.drawString(x, y, "Scripts"); y -= 36
S = [("1  Telegram cadence (recommended)", "VIEWER DISCRETION ADVISED. STOP. WHAT FOLLOWS IS REAL. STOP. NAMES, DATES AND PLACES ARE TRUE. STOP. SOME IMAGES MAY DISTURB. STOP."),
     ("2  Plain and direct", "This film is about real events and real people. Some scenes show violence and its aftermath. Viewer discretion is advised."),
     ("3  Short and personal", "Everything you are about to see happened. Parts of this story are hard to watch. Please watch with care.")]
for t, s in S:
    c.setFont("B", 17); c.setFillColorRGB(*FG); c.drawString(x, y, t); y -= 26
    y = wrap(c, "“" + s + "”", x+18, y, w-18, "R", 16, 22, DIM) - 16
y -= 6
c.setFont("B", 22); c.setFillColorRGB(*ACC); c.drawString(x, y, "Ways to present it (each 5-7 s, before the intro)"); y -= 36
P = [("A  Telegram (render on the right)", "A lamp-lit desk. Strips of teletype tape print and paste onto a telegram form one line at a time. The camera drifts in, the last STOP lands, and we cut to black. Sound: teletype clatter, a carriage bell on each STOP, room tone."),
     ("B  Burned into the case file", "A closed manila case file. The words char through the cover from behind: brown scorch, then glowing edges and a thin curl of smoke, until the warning is readable and the ember dies. Sound: a low crackle, a hiss, one soft breath."),
     ("C  A whisper over black", "Pure black. A whispered voice reads script 3 while the words fade in very small, one at a time, centred. One bare bulb flickers once in the dark before the cut. Sound: a near-silent room, the whisper close to the mic, a single filament tick.")]
for t, s in P:
    c.setFont("B", 17); c.setFillColorRGB(*FG); c.drawString(x, y, t); y -= 26
    y = wrap(c, s, x+18, y, w-18, "R", 15, 21, DIM) - 14
# old intros (task 1), lower right under the render
ox, oy, ow = W-40-iw, H-180-iw*9/16, iw
c.setFont("B", 20); c.setFillColorRGB(*ACC); c.drawString(ox, oy, "For reference: the earlier intros (same files on both old branches)"); oy -= 30
O = ["Four 5-6 s logo stings, 2.35:1 (nvidia_doc/scenes/sc_logo.py, brand/): TORCH, a flashlight sweeps a concrete wall and finds the logo (the searchlight one the user liked); BOARD, red strings pull tight on an evidence board; BAG, an evidence bag drops on a case table; TAPE, crime-scene tape in rain and police lights.",
     "Only BAG was rendered as an MP4: brand/seldom_sting_preview.mp4 (5.9 s, 960x408, low-res, with sound). There is no full-res master of any of the four. Stills: brand/logo_sting_concepts.jpg.",
     "The intro_* files (intro_plan.html, storyboard, intro_feedback.md) are the Nvidia film's story intro, not the channel ident. That intro is on hold and has no MP4. Concept 1 (SWEEP) builds on TORCH."]
for o in O: oy = wrap(c, "• " + o, ox, oy, ow, "R", 14, 19, DIM) - 8
c.showPage(); c.save()
print("ok", out)
