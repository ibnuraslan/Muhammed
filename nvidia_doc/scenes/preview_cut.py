"""Cut the intro preview: each shot's 12 fps preview frames -> motion-interpolated to 24 fps (never across a cut),
shots joined in order, film grain, voiceover underneath -> out/intro_preview.mp4"""
import os, subprocess, glob
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PREV = os.path.join(ROOT, "out", "preview", "intro")
LEAD = 2.5          # the voiceover starts 2.5 s in
SHOTS = [("home_behind", 138), ("home_front", 112), ("invest_drawer", 77), ("invest_reveal", 84),
         ("street_bus_reveal", 78), ("street_walk_track", 64), ("cafe_title_push", 68), ("cafe_pull_back", 100)]
FAST = {"invest_reveal", "cafe_pull_back"}
clips = []
for name, n in SHOTS:
    d = os.path.join(PREV, name); out = os.path.join(PREV, name + ".mp4")
    frames = sorted(glob.glob(os.path.join(d, "f*.png")))
    if not frames:
        print("missing frames for", name); continue
    interp = "fps=24" if name in FAST else "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:vsbmc=1"   # fast moves: no interpolation smear
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "12", "-pattern_type", "glob", "-i", os.path.join(d, "f*.png"),
                    "-vf", interp + ",tpad=stop_mode=clone:stop=4",
                    "-frames:v", str(n), "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", out], check=True)
    clips.append(out)
lst = os.path.join(PREV, "list.txt")
open(lst, "w").write("".join(f"file '{c}'\n" for c in clips))
final = os.path.join(ROOT, "out", "intro_preview.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", os.path.join(ROOT, "vo", "intro_vo.mp3"),
                "-af", f"adelay={int(LEAD * 1000)}:all=1", "-vf", "scale=1920:816:flags=lanczos,noise=c0s=7:c0f=t+u", "-c:v", "libx264", "-crf", "18", "-preset", "slow",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final], check=True)
print("[cut] wrote", final)
