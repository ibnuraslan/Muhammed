"""Assemble a part's preview MP4: rendered shot frames in VO order, 2D kit cards for the card-only shots, the kit
overlays animated in time over their shots (same templates/params as the storyboard post), shot ID burned small in
the corner (preview only; the delivery has no burned-in text).
    KIT=<kit_v1> FR=<anim out dir> python3 prev_assemble.py 1 <out.mp4> [WxH]"""
import os, sys, json, subprocess, shutil
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
KIT = os.environ["KIT"]; FR = os.environ["FR"]
sys.path.insert(0, KIT); sys.path.insert(0, os.path.join(ROOT, "graphics"))
import seldom_kit as K
os.environ.setdefault("RAW", os.path.join(FR, "_stills"))
import sb_post as SP
PART = int(sys.argv[1]); OUTMP4 = sys.argv[2]
W, H = map(int, (sys.argv[3] if len(sys.argv) > 3 else "1280x720").split("x"))
SH = json.load(open(os.path.join(ROOT, "shots", "shots.json")))[str(PART)]["rows"]
FPS = 24
TMP = os.path.join(FR, "_assemble"); shutil.rmtree(TMP, ignore_errors=True); os.makedirs(TMP)
font = ImageFont.truetype(os.path.join(KIT, "fonts", "IBMPlexMono-Regular.ttf"), 14)


def shot_frames(sid):
    d = os.path.join(FR, "frames", sid)
    return sorted(os.path.join(d, f) for f in os.listdir(d)) if os.path.isdir(d) else []


def main():
    ov = SP.overlays()
    k = 0
    for r in SH:
        sid = r["id"]; N = max(12, round(r["dur"] * FPS))
        src = shot_frames(sid)
        plate_sid = SP.PLATES2D.get(sid, "missing") if sid in SP.PLATES2D else sid
        if sid in SP.PLATES2D:
            src = shot_frames(plate_sid)[:1] if plate_sid else []
        for i in range(N):
            if src:
                bg = Image.open(src[min(i, len(src) - 1)]).convert("RGB").resize((1920, 1080), Image.BILINEAR)
            else:
                bg = Image.new("RGB", (1920, 1080))
            t = i / FPS
            for (tpl, params, _t) in ov.get(sid, []):
                bg = K.composite(bg, K.TEMPLATES[tpl](t, **params))
            im = bg.resize((W, H), Image.BILINEAR)
            ImageDraw.Draw(im).text((8, H - 20), f"{sid}  {r['set']}/{r['kind']}  PREVIEW", font=font, fill=(150, 146, 136))
            im.save(os.path.join(TMP, f"f_{k:05d}.jpg"), quality=88); k += 1
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(TMP, "f_%05d.jpg"),
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUTMP4], check=True)
    print("MP4", OUTMP4, k, "frames", round(k / FPS, 1), "s")


if __name__ == "__main__":
    main()
