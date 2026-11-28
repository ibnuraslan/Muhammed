"""Composite the overlays over the farm render and upscale to 2K.
    python3 composite_upscale.py <farm frames dir (MASTER output, 0001.png ...)> <overlay dir (ov_00001.png, bg.json)> <out.mp4>
Per frame: apply the overlay's background treatment (blur, dim) to the render; card-only shots (title, disclaimer,
boards) get black, or the blurred last frame of their plate shot; lay the alpha overlay on top; upscale 1920x1080 ->
2560x1440 (Lanczos + light unsharp r1.2/45 %); encode H.264 CRF 16 (or keep PNGs with --png <dir>)."""
import os, sys, json, subprocess, tempfile
from PIL import Image, ImageFilter
FR, OV, OUTMP4 = sys.argv[1], sys.argv[2], sys.argv[3]
PNG = sys.argv[sys.argv.index("--png") + 1] if "--png" in sys.argv else None
meta = json.load(open(os.path.join(OV, "bg.json")))
N = meta["frames"]; BG = {int(k): v for k, v in meta["bg"].items()}
frames = sorted(f for f in os.listdir(FR) if f.lower().endswith(".png"))
plate_last = {}
for t in meta["timeline"]:
    if t["plate"] not in ("own", None):
        src = next((u for u in meta["timeline"] if u["id"] == t["plate"]), None)
        if src:
            plate_last[t["id"]] = src["start"] + src["frames"] - 1


def shot_at(k):
    for t in meta["timeline"]:
        if t["start"] <= k < t["start"] + t["frames"]:
            return t


def main():
    out = PNG or tempfile.mkdtemp(prefix="romand_comp_"); os.makedirs(out, exist_ok=True)
    for k in range(1, N + 1):
        t = shot_at(k)
        if t["plate"] == "own":
            im = Image.open(os.path.join(FR, frames[k - 1])).convert("RGB")
        elif t["id"] in plate_last:
            im = Image.open(os.path.join(FR, frames[plate_last[t["id"]] - 1])).convert("RGB")
        else:
            im = Image.new("RGB", (1920, 1080))
        blur, dim = BG.get(k, (0, 0))
        if blur > 0.3:
            im = im.resize((960, 540), Image.BILINEAR).filter(ImageFilter.GaussianBlur(blur / 2)).resize((1920, 1080), Image.BILINEAR)
        if dim > 0.005:
            im = Image.blend(im, Image.new("RGB", im.size), dim)
        o = Image.open(os.path.join(OV, f"ov_{k:05d}.png")).convert("RGBA")
        im = im.convert("RGBA"); im.alpha_composite(o); im = im.convert("RGB")
        im = im.resize((2560, 1440), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.2, percent=45, threshold=2))
        im.save(os.path.join(out, f"c_{k:05d}.png"))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", os.path.join(out, "c_%05d.png"),
                    "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUTMP4], check=True)
    print("DONE", OUTMP4, N, "frames, 2560x1440")


if __name__ == "__main__":
    main()
