"""Render the kit demos: every template composited over the v3 vault live-test clip, one MP4 per element, plus a
stills contact sheet.
    python3 demo.py <clean_bg_frames_dir> [element ...]
Background frames are the 1920x1080 clip frames WITHOUT the burned-in overlay (f_0001.png ... f_0120.png); the
clip ping-pongs if a demo is longer than 5 s. Placeholder photos are cut from our own renders (faceless mannequins).
"""
import os, sys, json, subprocess
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seldom_kit as K

HERE = os.path.dirname(os.path.abspath(__file__))
BG = sys.argv[1]
ONLY = sys.argv[2:]
OUT = os.path.join(HERE, "demos"); TMP = os.path.join(HERE, "_tmp"); os.makedirs(OUT, exist_ok=True)
A = os.path.join(HERE, "assets")
NBG = len([f for f in os.listdir(BG) if f.endswith(".png")])


def bg_frame(i):
    k = i % (2 * NBG - 2); k = k if k < NBG else 2 * NBG - 2 - k
    return Image.open(os.path.join(BG, f"f_{k + 1:04d}.png"))


P = lambda n: os.path.join(A, n)
DEMOS = [
    ("01_datestamp", "datestamp", dict(top="16 FEBRUARY", big="2003")),
    ("02_quote", "quote", dict(text="They didn't touch the alarm. They didn't need to. They already knew every sensor in that room.",
                               who="LEAD INVESTIGATOR")),
    ("03_phrase", "phrase", dict(text="“nothing was broken”")),
    ("04_section", "section", dict(text="THE VAULT", index="02")),
    ("05_title", "title", dict(text="THEY STOLE $100 MILLION", sub="THEN THREW AWAY THE EVIDENCE")),
    ("06_person", "person", dict(photo=P("person_a.jpg"), name="LEONARDO N.", role="THE TENANT · SUSPECT")),
    ("07_person_pair", "person_pair", dict(photos=(P("person_b.jpg"), P("person_c.jpg")), names=("THE GENIUS", "THE MONSTER"),
                                           roles=("ALARM SPECIALIST", "LOCKS AND KEYS"))),
    ("08_place", "place", dict(photo=P("place.jpg"), name="ANTWERP DIAMOND CENTRE", country="BELGIUM")),
    ("09_disclaimer", "disclaimer", dict(discretion=True)),
    ("09b_disclaimer_no_discretion", "disclaimer", dict(discretion=False, dur=6.0)),
    ("10_document", "document", dict()),
    ("11_timeline", "timeline", dict()),
    ("12_linkboard", "linkboard", dict(
        cards=[dict(photo=P("person_a.jpg"), name="LEONARDO N.", role="THE TENANT", pos=(0.5, 0.05), t=0.4),
               dict(photo=P("person_b.jpg"), name="THE GENIUS", role="ALARMS", pos=(0.25, 0.37)),
               dict(photo=P("person_c.jpg"), name="THE MONSTER", role="LOCKS", pos=(0.75, 0.37)),
               dict(photo=P("person_d.jpg"), name="SPEEDY", role="LOOKOUT", pos=(0.5, 0.69))],
        links=[(0, 1, 1.4, "PARTNER"), (1, 2, 2.9, "CREW"), (2, 3, 4.4, "BROTHER")])),
    ("13_map", "map", dict()),
    ("14_lineart", "lineart", dict(source=P("lineart_src.png"), accent_box=(820, 560, 1120, 760))),
]


def frame_job(args):
    key, name, params, i, dur, d = args
    fr = K.TEMPLATES[name](i / K.FPS, dur=dur, **params)
    im = K.composite(bg_frame(i), fr)
    im.save(os.path.join(d, f"f_{i + 1:04d}.jpg"), quality=93)
    return i


if __name__ == "__main__":
    stills = []
    for key, name, params in DEMOS:
        if ONLY and key not in ONLY and name not in ONLY:
            continue
        params = dict(params); dur = params.pop("dur", K.TEMPLATES[name].DUR); n = int(round(dur * K.FPS)); d = os.path.join(TMP, key); os.makedirs(d, exist_ok=True)
        with Pool(4) as pool:
            pool.map(frame_job, [(key, name, params, i, dur, d) for i in range(n)])
        mp4 = os.path.join(OUT, f"{key}.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(K.FPS), "-i", os.path.join(d, "f_%04d.jpg"),
                        "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4], check=True)
        st = int(n * {"title": 0.62, "phrase": 0.9, "lineart": 0.7, "document": 0.75, "linkboard": 0.8, "disclaimer": 0.78, "timeline": 0.8, "map": 0.75}.get(name, 0.6))
        Image.open(os.path.join(d, f"f_{st + 1:04d}.jpg")).save(os.path.join(OUT, f"{key}_still.jpg"), quality=90)
        if name == "phrase":
            json.dump(dict(typing_sfx_cues_s=K.phrase_cues(params["text"])), open(os.path.join(OUT, "03_phrase_typing_cues.json"), "w"), indent=1)
        print("done", key, n, "frames", flush=True)
    # contact sheet of all stills present
    ks = sorted(f for f in os.listdir(OUT) if f.endswith("_still.jpg"))
    if ks:
        tw, th, cols, pad, lab = 640, 360, 3, 14, 34
        rows = (len(ks) + cols - 1) // cols
        sh = Image.new("RGB", (cols * tw + (cols + 1) * pad, rows * (th + lab) + (rows + 1) * pad + 60), (14, 13, 11))
        dd = ImageDraw.Draw(sh); f = ImageFont.truetype(K.FONT["label"], 24); ft = ImageFont.truetype(K.FONT["label_bold"], 34)
        dd.text((pad, 14), "SELDOM  ·  ON-SCREEN GRAPHICS KIT v1", font=ft, fill=K.YEL)
        for i, k in enumerate(ks):
            x = pad + (i % cols) * (tw + pad); y = 60 + pad + (i // cols) * (th + lab + pad)
            dd.text((x, y), k.replace("_still.jpg", "").replace("_", " ").upper(), font=f, fill=K.WHITE)
            sh.paste(Image.open(os.path.join(OUT, k)).resize((tw, th), Image.LANCZOS), (x, y + lab))
        sh.save(os.path.join(HERE, "contact_sheet.jpg"), quality=90)
