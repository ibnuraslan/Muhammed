"""Grade the EXR frames written by b_anim.py (same grade as the sheets) and encode a 24 fps H.264 MP4.
  python b_mp4.py DIR out.mp4 [--label "text"]
"""
import os, sys, json, subprocess, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "nvidia_doc", "scenes"))
import grade

d, out = sys.argv[1], sys.argv[2]
label = sys.argv[sys.argv.index("--label") + 1] if "--label" in sys.argv else ""
meta = json.load(open(os.path.join(d, "plate.json")))
step = meta.get("step", 3)
tmp = tempfile.mkdtemp()
exrs = sorted(f for f in os.listdir(d) if f.endswith(".exr"))
for i, f in enumerate(exrs):
    grade.grade_file(os.path.join(d, f), os.path.join(tmp, f"g{i:04d}.png"), look="cinematic", exposure=meta["exposure"], cine=meta.get("cine") or None)
vf = "scale=trunc(iw/2)*2:trunc(ih/2)*2"
if label:
    vf += (",drawtext=fontfile=/usr/share/fonts/opentype/inter/Inter-SemiBold.otf:text='" + label.replace("'", "") +
           "':x=14:y=12:fontsize=18:fontcolor=white@0.85:box=1:boxcolor=black@0.45:boxborderw=6")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(24 / step), "-i", os.path.join(tmp, "g%04d.png"),
                "-vf", vf, "-r", "24", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", out], check=True)
print("[mp4]", out, len(exrs), "frames")
