"""Part 2 final pass: base intermediate -> PERSON/PLACE cards (callout.py, slide in/out) + burned-in captions
(callout.caption, hard cut, exact script text from nvidia_part2.srt) -> H.264 High CRF 18 slow yuv420p bt709 + AAC 320k."""
import sys, os, json, subprocess, time
import numpy as np
from PIL import Image
KIT = sys.argv[1]; sys.path.insert(0, os.path.join(KIT, "scenes"))
import callout
from PIL import ImageFilter
_halo = {}
def halo_layer(layer, key):
    """Soft dark halo from a callout layer's alpha (same look, more legible): used only over bright backgrounds."""
    if key not in _halo:
        a = layer.split()[-1].filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(14))
        _halo[key] = np.asarray(a, np.float32) / 255
    return _halo[key]
def boost(img, layer, key, region):
    """Strength from the background brightness under the text (0 on normal/dark frames, up to 0.6 on white)."""
    x0, y0, x1, y1 = region
    a = np.asarray(img, np.float32)[y0:y1:4, x0:x1:4]
    L = (0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]).mean()
    k = float(np.clip((L - 110) / 80, 0, 1)) * 0.6
    if k <= 0: return img, 0.0
    h = halo_layer(layer, key) * k
    f = np.asarray(img, np.float32) * (1 - h[..., None])
    return Image.fromarray(np.clip(f + 0.5, 0, 255).astype(np.uint8)), k
from caption_burnin import parse_srt
base, srt, cards_json, audio, out_mp4, qa_csv = sys.argv[2:8]
W, H, FPS = 1920, 816, 24
cues = parse_srt(srt); cards = json.load(open(cards_json))
T_IN, HOLD, T_OUT = 0.35, 3.0, 0.3; DUR = T_IN + HOLD + T_OUT
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", base, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, bufsize=W * H * 3 * 2)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-framerate", "24", "-i", "-",
    "-i", audio, "-map", "0:v", "-map", "1:a",
    "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p", "-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-crf", "18",
    "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", "-r", "24",
    "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out_mp4], stdin=subprocess.PIPE)
q = open(qa_csv, "w"); q.write("frame,luma,std,diff,caption,card\n"); prev = None; n = 0; t0 = time.time()
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    n += 1; t = (n - 1) / FPS
    im = None; cap_i = ""; card_i = ""
    for c in cards:
        sec = (n - c["frame"]) / FPS
        if 0 <= sec < DUR:
            im = im or Image.frombytes("RGB", (W, H), buf)
            sl = callout.card_slide(sec, DUR, T_IN, T_OUT)
            crop = tuple(c["crop"]) if c.get("crop") else None
            fn = callout.person_right if c["kind"] == "person" else callout.place_left
            side = "right" if c["kind"] == "person" else "left"
            lay = callout._card_layer(W, H, c["photo"], c["name"], c["role"], side, crop) if ("lay", c["name"]) not in _halo else _halo[("lay", c["name"])]
            _halo[("lay", c["name"])] = lay
            dx = sl * callout._travel((W, H), side)
            sh = Image.new("RGBA", lay.size, (0, 0, 0, 0)); sh.alpha_composite(lay, (int(round(dx)), 0)) if dx >= 0 else sh.paste(lay.crop((int(round(-dx)), 0, W, H)), (0, 0))
            reg = (int(W * 0.6), int(H * 0.45), W, int(H * 0.82)) if side == "right" else (0, int(H * 0.45), int(W * 0.4), int(H * 0.82))
            im, kb = boost(im, sh, ("card", c["name"], int(round(dx))), reg)
            im = fn(im, c["photo"], c["name"], c["role"], slide=sl, crop=crop); card_i = c["name"] + (f" boost{kb:.2f}" if kb else "")
    for k, (a, z, text) in enumerate(cues, 1):
        if a <= t < z:
            im = im or Image.frombytes("RGB", (W, H), buf)
            cl = callout._cache_cap.get(text) if hasattr(callout, "_cache_cap") else None
            if cl is None:
                callout._cache_cap = getattr(callout, "_cache_cap", {}); cl = callout._cache_cap[text] = callout.caption_layer(W, H, text)
            im, kb = boost(im, cl, ("cap", text), (int(W * 0.25), int(H * 0.88), int(W * 0.75), int(H * 0.97)))
            im = callout.caption(im, text); cap_i = str(k) + (f" boost{kb:.2f}" if kb else ""); break
    out = im.tobytes() if im is not None else buf
    enc.stdin.write(out)
    a = np.frombuffer(out, np.uint8).reshape(H, W, 3)[::8, ::8].astype(np.float32)
    y = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    d = -1 if prev is None else float(np.abs(y - prev).mean()); prev = y
    q.write(f"{n},{y.mean():.2f},{y.std():.2f},{d:.2f},{cap_i},{card_i}\n")
    if n % 500 == 0:
        q.flush(); el = time.time() - t0; print(f"frame {n} {n / el:.2f} fps", flush=True)
enc.stdin.close(); rc = enc.wait(); q.close(); print("DONE frames", n, "rc", rc, flush=True)
