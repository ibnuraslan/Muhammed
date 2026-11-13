"""Final Ch4/Ch5 storyboards from the BAKED shots in the delivered master (out/blend/ch45/nvidia_ch45.blend).
One frame per shot at mid-cut, rendered through the master's sequencer (low samples, 25%), labelled with shot id,
start time and length; both title frames (66 and 4168) with the title overlay .mov composited.
  python scenes/storyboard_final_ch45.py   -> out/ch45_preview/ch4_storyboard_final.jpg, ch5_storyboard_final.jpg
Nothing is saved back into the master."""
import os, sys, json, subprocess
import numpy as np
import bpy
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FPS, PCT, SAMPLES = 24, 25, int(os.environ.get("SBF_SAMPLES", 10))
TMP = os.path.join(ROOT, "out", "ch45_sb_final"); os.makedirs(TMP, exist_ok=True)
tim = json.load(open(os.path.join(ROOT, "vo", "ch45_timing.json")))
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "out", "blend", "ch45", "nvidia_ch45.blend"))
m = bpy.data.scenes["NVIDIA_CH45"]
m.render.resolution_percentage = PCT
for sc in bpy.data.scenes:
    if sc != m:
        sc.cycles.samples = SAMPLES; sc.cycles.adaptive_threshold = 0.1
        sc.render.resolution_percentage = PCT
items = []; f = 1
for c in ("4", "5"):
    for sh in tim[c]:
        mid = f + sh["frames"] // 2
        items.append(dict(c=c, name=sh["name"], label=sh["label"], start=f, frames=sh["frames"], render=mid,
                          title=(sh["name"] in ("c4_01_hq_dusk_push", "c5_01_interview_passport_slide"))))
        f += sh["frames"]
for it in items:
    if it["title"]:                                   # the title frames show the card at full hold (+ overlay)
        it["render"] = it["start"] + 65
    out = os.path.join(TMP, f"{it['name']}_f{it['render']:05d}.png"); it["png"] = out
    patch = os.path.join(TMP, f"{it['name']}_PATCH.png")         # a shot replaced by a patch file: show the patch
    if os.path.exists(patch):
        it["png"] = patch; it["patched"] = True
    if not os.path.exists(out) and not it.get("patched"):
        m.frame_set(it["render"]); m.render.filepath = out
        bpy.ops.render.render(write_still=True, scene=m.name)
    print("[sbf]", it["name"], it["render"], flush=True)

# overlay frames for the two title frames, from the shipped .mov
mov = os.path.join(ROOT, "out", "title_overlay_ch45", "nvidia_ch45_title_overlay.mov")
def overlay_frame(F):
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", mov, "-vf", f"select=eq(n\\,{F - 1})", "-frames:v", "1",
                        "-f", "rawvideo", "-pix_fmt", "rgba", "-"], capture_output=True).stdout
    return np.frombuffer(b, np.uint8).reshape(816, 1920, 4)

F_ = lambda z: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", z)
f1, f2, fh = F_(17), F_(14), F_(26)
tc = lambda fr: f"{int((fr / FPS) // 60)}:{(fr / FPS) % 60:04.1f}"
TW, TH, cols, pad = 432, 184, 4, 12
for c, title in (("4", "CHAPTER 4 — The Second Employee"), ("5", "CHAPTER 5 — The Passport and the Paper Trail")):
    its = [it for it in items if it["c"] == c]
    c0 = its[0]["start"]
    rows = (len(its) + cols - 1) // cols
    img = Image.new("RGB", (pad + cols * (TW + pad), 54 + rows * (TH + 52)), (18, 18, 22)); d = ImageDraw.Draw(img)
    d.text((pad, 12), f"NVIDIA · {title} · FINAL (baked shots, nvidia_ch45.blend, mid-cut)", fill=(240, 240, 245), font=fh)
    for k, it in enumerate(its):
        x = pad + (k % cols) * (TW + pad); y = 54 + (k // cols) * (TH + 52)
        im = Image.open(it["png"]).convert("RGB")
        if it["title"]:
            ov = overlay_frame(it["render"]).astype(np.float32) / 255
            base = np.asarray(im.resize((1920, 816), Image.LANCZOS)).astype(np.float32) / 255
            a = ov[..., 3:4]; im = Image.fromarray((np.clip(base * (1 - a) + ov[..., :3] * a, 0, 1) * 255 + .5).astype(np.uint8))
        img.paste(im.resize((TW, TH), Image.LANCZOS), (x, y))
        lab = it["label"]
        if it["title"]: lab = lab.split(" + ")[0] + " + title (overlay)"
        if it.get("patched"): lab = lab + " · PATCH"
        while d.textlength(lab, font=f1) > TW - 4: lab = lab[:-2]
        d.text((x, y + TH + 4), lab, fill=(235, 225, 180) if not it.get("patched") else (255, 160, 120), font=f1)
        d.text((x, y + TH + 25), f"{it['name']}   {tc(it['start'] - c0)}  ·  {it['frames'] / FPS:.1f}s", fill=(150, 165, 180), font=f2)
    out = os.path.join(ROOT, "out", "ch45_preview", f"ch{c}_storyboard_final.jpg")
    img.save(out, quality=90); print("[sbf] wrote", out, img.size, flush=True)
