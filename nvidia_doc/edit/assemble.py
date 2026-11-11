"""Assemble the film from edit/timeline.json: plates/animations + 2.5D camera moves + grading + graphics + finish.

  python edit/assemble.py --storyboard [--plates DIR] [--chapter 1]     one still per beat -> out/storyboard_*.png
  python edit/assemble.py --frames [--from ID --to ID] [--half]         render frames -> out/frames/
  python edit/assemble.py --encode                                      mux frames + mixed audio -> out/the_spy_allegations.mp4

Plates live in out/plates/<scene>/<move>/ as either f0000.png... (true 3D animation, 12 fps) or plate.png + depth.png
(one frame, moved in 2.5D here). Anything missing renders as a labelled placeholder, so the cut can be reviewed early.
"""
import os, sys, json, math, glob, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "mograph"))
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates
from beats import BEATS
import style
from style import W, H, FPS, BG, ease_in_out, clamp
from canvas import Frame, over, solid
import templates, templates2  # noqa: F401
from templates import TEMPLATES, draw_overlays

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
PLATES = arg("--plates", os.path.join(ROOT, "out", "plates"))
OUT = os.path.join(ROOT, "out")
BEAT = {b["id"]: b for b in BEATS}

# ----------------------------------------------------------------------------- per-scene grade (lift, gain, sat)
GRADE = {
    "chip_macro": ((0.004, 0.010, 0.016), (0.96, 1.0, 1.06), 1.05), "gpu_module": ((0.004, 0.010, 0.016), (0.96, 1.0, 1.06), 1.0),
    "datacenter": ((0.002, 0.010, 0.018), (0.92, 1.0, 1.08), 0.95), "datacenter_build": ((0.006, 0.006, 0.008), (1.04, 1.0, 0.94), 0.9),
    "boardroom": ((0.004, 0.008, 0.016), (1.0, 0.98, 0.96), 0.9), "shanghai": ((0.004, 0.008, 0.018), (1.0, 0.98, 0.96), 1.0),
    "singapore_tower": ((0.004, 0.008, 0.018), (0.98, 1.0, 1.04), 0.95), "port": ((0.010, 0.010, 0.014), (1.04, 0.98, 0.92), 0.9),
    "office_door": ((0.004, 0.008, 0.012), (0.98, 1.0, 1.03), 0.75), "capitol": ((0.008, 0.010, 0.018), (1.0, 0.98, 0.97), 0.85),
    "party": ((0.010, 0.006, 0.016), (1.02, 0.98, 1.0), 1.0), "restaurant": ((0.010, 0.006, 0.004), (1.04, 0.98, 0.9), 0.95),
    "memo_desk": ((0.004, 0.006, 0.010), (1.03, 0.99, 0.94), 0.85), "courthouse": ((0.008, 0.010, 0.014), (0.98, 1.0, 1.02), 0.7),
    "doors": ((0.006, 0.004, 0.004), (1.04, 0.98, 0.92), 0.95),
}


def grade(img, scene):
    lift, gain, sat = GRADE.get(scene, ((0.005, 0.008, 0.012), (1, 1, 1), 0.9))
    y = (img * np.array([0.2126, 0.7152, 0.0722])).sum(-1, keepdims=True)
    img = y + (img - y) * sat
    img = img + 0.22 * (img - img * img) * (img - 0.5) * 2.0       # gentle S-curve
    return np.clip(np.array(lift) + img * (np.array(gain) - np.array(lift)), 0, 1)


# ----------------------------------------------------------------------------- plates
_cache = {}


def _load(path, size=(W, H)):
    if path not in _cache:
        im = Image.open(path)
        a = np.asarray(im.convert("L" if os.path.basename(path).startswith("depth") else "RGB").resize(size, Image.LANCZOS)).astype(np.float32) / 255.0
        _cache[path] = a
        if len(_cache) > 64:
            _cache.pop(next(iter(_cache)))
    return _cache[path]


def move_params(move):
    """2.5D camera move from the move's name: (zoom_end, pan_x, pan_y). Parallax scales with nearness."""
    m = move or ""
    if any(k in m for k in ("push", "close", "zoom", "nameplate", "dossier", "letter")):
        return (1.07, 0.0, 0.0)
    if any(k in m for k in ("rise", "tilt", "crane")):
        return (1.03, 0.0, -0.035)
    if any(k in m for k in ("drift", "bokeh", "columns", "focus")):
        return (1.03, 0.03, 0.0)
    return (1.05, 0.012, 0.0)


def parallax(rgb, depth, t, move):
    """Layered 2.5D move: near layers scale/translate more than far ones; far-to-near composite fills disocclusion."""
    z1, px, py = move_params(move)
    e = ease_in_out(t)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    out = None
    edges = [0.0, 0.08, 0.18, 0.32, 0.5, 0.75, 1.01]
    for k in range(len(edges) - 1, 0, -1):          # far -> near
        lo, hi = edges[k - 1], edges[k]
        near = 1.0 - (lo + hi) / 2                  # 1 = near, 0 = far
        z = 1 + (z1 - 1) * e * (0.35 + 0.65 * near)
        sx = px * e * W * (0.3 + 0.7 * near); sy = py * e * H * (0.3 + 0.7 * near)
        u = (xx - W / 2 - sx) / z + W / 2; v = (yy - H / 2 - sy) / z + H / 2
        layer = np.stack([map_coordinates(rgb[..., c], [v, u], order=1, mode="nearest") for c in range(3)], -1)
        if out is None:
            out = layer
            continue
        d = map_coordinates(depth, [v, u], order=1, mode="nearest")
        a = np.clip((hi - d) / 0.04, 0, 1) * np.clip((d - lo + 0.04) / 0.04, 0, 1)
        a = np.maximum(a, (d < lo).astype(np.float32))   # anything nearer also covers
        out = out * (1 - a[..., None]) + layer * a[..., None]
    return out


def plate_frame(scene, move, t):
    d = os.path.join(PLATES, scene, move)
    frames = sorted(glob.glob(os.path.join(d, "f*.png")))
    if frames:
        f = t * (len(frames) - 1); i0 = int(f); fr = f - i0
        a = _load(frames[i0]); b = _load(frames[min(i0 + 1, len(frames) - 1)])
        return a * (1 - fr) + b * fr
    for cand in (os.path.join(d, "plate.png"), os.path.join(PLATES, scene, "plate.png")):
        if os.path.exists(cand):
            rgb = _load(cand)
            dp = cand.replace("plate.png", "depth.png")
            if os.path.exists(dp):
                d = _load(dp); lo, hi = np.percentile(d, 1), np.percentile(d, 99)
                return parallax(rgb, np.clip((d - lo) / max(hi - lo, 1e-3), 0, 1), t, move)   # use the full layer range
            z1, px, py = move_params(move); z = 1 + (z1 - 1) * ease_in_out(t)
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            u = (xx - W / 2) / z + W / 2 - px * W * t; v = (yy - H / 2) / z + H / 2 - py * H * t
            return np.stack([map_coordinates(rgb[..., c], [v, u], order=1, mode="nearest") for c in range(3)], -1)
    fr = Frame(bg=(14, 16, 20))
    fr.text(f"{scene} · {move}", W / 2, H / 2, "mono", 34, (90, 100, 112), 1, anchor="c")
    fr.text("3D plate not rendered yet", W / 2, H / 2 + 50, "sans", 24, (70, 78, 90), 1, anchor="c")
    return fr.rgba()[..., :3]


# ----------------------------------------------------------------------------- film finish
_rng = np.random.default_rng(5)
_YY, _XX = np.mgrid[0:H, 0:W].astype(np.float32)
_R = np.sqrt(((_XX - W / 2) / (W / 2)) ** 2 + ((_YY - H / 2) / (H / 2)) ** 2 * 0.6)
_VIG = (1 - 0.33 * np.clip(_R - 0.4, 0, None) ** 1.7)[..., None]


def finish(img, grain=0.014):
    hi = np.clip(img - 0.78, 0, None)
    if hi.max() > 0:
        small = hi[::4, ::4]
        bl = np.stack([gaussian_filter(small[..., c], 6) for c in range(3)], -1)
        bl = np.asarray(Image.fromarray((np.clip(bl, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        img = img + bl * np.array([1.2, 0.95, 0.85]) * 0.35
    img = img * _VIG
    g = _rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    g = np.asarray(Image.fromarray(g).resize((W, H), Image.BICUBIC))
    return np.clip(img + g[..., None] * grain, 0, 1)


# ----------------------------------------------------------------------------- one frame
def compose(beat, t, dur):
    shot = beat["shot"]
    scene = shot.get("scene") or shot.get("bg")
    kind = shot["kind"]
    tn = clamp(t / max(dur, 1e-3))
    if kind in ("3d", "over") or (kind == "mg" and scene):
        base = grade(plate_frame(scene, shot.get("move", "slow_push") if kind != "mg" else "drift", tn), scene)
        if kind == "over":
            base = base * 0.42
        elif kind == "mg":
            base = gaussian_filter(base, (3, 3, 0)) * 0.3
    else:
        base = solid(BG)
    fr = Frame()
    tpl = shot.get("template")
    if tpl:
        TEMPLATES[tpl](fr, t, dur, beat, shot)
    draw_overlays(fr, t, dur, beat)
    return over(base, fr.rgba())


def load_timeline():
    p = os.path.join(HERE, "timeline.json")
    if not os.path.exists(p):
        subprocess.run([sys.executable, os.path.join(HERE, "align.py"), "--estimate"], check=True)
    return json.load(open(p))


def frame_at(T, tl, i_hint=0):
    """Output time T -> composited frame, with short dissolves between beats and fades at the ends."""
    beats = tl["beats"]
    i = next((k for k in range(len(beats)) if beats[k]["start"] <= T < beats[k]["end"]), len(beats) - 1)
    bt = beats[i]; b = BEAT[bt["id"]]; dur = bt["end"] - bt["start"]; t = T - bt["start"]
    HOLD = 0.6   # graphics are laid out as if the beat ran a little longer, so they don't fade out right before the cut
    img = compose(b, t, dur + HOLD)
    XF = 0.25    # dissolve length (s) when the visual kind changes; cuts otherwise
    if i + 1 < len(beats) and bt["end"] - T < XF:
        nb = beats[i + 1]; n = BEAT[nb["id"]]
        if n["shot"]["kind"] != b["shot"]["kind"] or n.get("ch"):
            f = 1 - (bt["end"] - T) / XF
            img = img * (1 - f) + compose(n, 0.0, nb["end"] - nb["start"] + HOLD) * f
    total = beats[-1]["end"]
    img = img * clamp(T / 0.8) * clamp((total - T) / 1.5)
    return finish(img)


def save(img, path, size=None):
    im = Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))
    if size:
        im = im.resize(size, Image.LANCZOS)
    im.save(path)


def storyboard(tl, chapter=None):
    """One frame per beat (at 60% through it), captioned with the narration, tiled per chapter."""
    from PIL import ImageDraw, ImageFont
    os.makedirs(OUT, exist_ok=True)
    groups = {}
    ch = "open"
    for bt in tl["beats"]:
        b = BEAT[bt["id"]]
        ch = b.get("ch") or ch
        groups.setdefault(ch, []).append(bt)
    fnt = ImageFont.truetype(style.F["sans"], 15); fb = ImageFont.truetype(style.F["mono_m"], 14)
    for ch, items in groups.items():
        if chapter and ch != chapter:
            continue
        tw, th = 480, 270; cap = 70; cols = 4
        rows = (len(items) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw + (cols + 1) * 12, rows * (th + cap) + (rows + 1) * 12), (5, 6, 8))
        d = ImageDraw.Draw(sheet)
        for k, bt in enumerate(items):
            b = BEAT[bt["id"]]; dur = bt["end"] - bt["start"]
            img = compose(b, dur * 0.6, dur)
            im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize((tw, th), Image.LANCZOS)
            x = 12 + (k % cols) * (tw + 12); y = 12 + (k // cols) * (th + cap + 12)
            sheet.paste(im, (x, y))
            d.text((x, y + th + 6), f"{bt['id']}  {bt['start'] // 60:.0f}:{bt['start'] % 60:04.1f}  ({dur:.1f}s)", font=fb, fill=(150, 160, 173))
            txt = b["text"] or f"[{b['shot'].get('template')}]"
            words, line, lines = txt.split(), "", []
            for w_ in words:
                if d.textlength(line + " " + w_, font=fnt) > tw - 6:
                    lines.append(line); line = w_
                else:
                    line = (line + " " + w_).strip()
            lines.append(line)
            for j, l in enumerate(lines[:2]):
                d.text((x, y + th + 26 + j * 19), l + (" …" if j == 1 and len(lines) > 2 else ""), font=fnt, fill=(225, 230, 236))
        p = os.path.join(OUT, f"storyboard_{ch}.png")
        sheet.save(p); print("[storyboard]", p)


def render_frames(tl, a=None, b=None, half=False):
    d = os.path.join(OUT, "frames"); os.makedirs(d, exist_ok=True)
    beats = tl["beats"]
    t0 = next((x["start"] for x in beats if x["id"] == a), 0.0) if a else 0.0
    t1 = next((x["end"] for x in beats if x["id"] == b), beats[-1]["end"]) if b else beats[-1]["end"]
    for n in range(int(t0 * FPS), int(t1 * FPS)):
        p = os.path.join(d, f"{n:06d}.png")
        if os.path.exists(p):
            continue
        save(frame_at(n / FPS, tl), p, (W // 2, H // 2) if half else None)
        if n % 48 == 0:
            print(f"[frames] {n / FPS:.1f}s", flush=True)


def encode(tl):
    wav = os.path.join(OUT, "mix.wav")
    subprocess.run([sys.executable, os.path.join(HERE, "score.py"), wav], check=True)
    mp4 = os.path.join(OUT, "the_spy_allegations.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(OUT, "frames", "%06d.png"), "-i", wav,
                    "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-tune", "film",
                    "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", mp4], check=True)
    print("[done]", mp4)


if __name__ == "__main__":
    tl = load_timeline()
    if "--storyboard" in sys.argv:
        storyboard(tl, arg("--chapter", None))
    if "--frames" in sys.argv:
        render_frames(tl, arg("--from", None), arg("--to", None), "--half" in sys.argv)
    if "--encode" in sys.argv:
        encode(tl)
