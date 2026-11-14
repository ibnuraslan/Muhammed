"""Storyboard frames for Ch3-5: every shot in film order, one labelled frame each (shot id, chapter, approx
timecode in the chapter, VO line, v2 action note), plus a contact sheet per chapter and an index.
  python b_frames.py ST_DIR OUT_DIR [t]
"""
import os, sys, json, tempfile, textwrap
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "nvidia_doc", "scenes"))
from PIL import Image, ImageDraw, ImageFont
import grade
import b_shots as S

st, out = sys.argv[1], sys.argv[2]
T = sys.argv[3] if len(sys.argv) > 3 else "0.5"
os.makedirs(out, exist_ok=True)
W, H = 1280, 544
CAP = 230
f_big = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 28)
f_txt = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Medium.otf", 20)
f_it = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Medium.otf", 18)
TITLES = {"ch3": "Chapter 3 · The Man with the Spade", "ch4": "Chapter 4 · The Clicks", "ch5": "Chapter 5 · After the Verdict"}
tmp = tempfile.mkdtemp()
index = ["# Radio Jingle · chat B storyboard frames (Ch3–5)", "",
         "Every shot in film order. Times are estimates within the chapter (184 wpm, 3 s title lead, long takes at their own length) until the voiceover lands.",
         "Frames are quick low-sample stills at mid-shot. v2 = reworked after the reference study; the action note follows the hub's hard rules: nothing moves by itself, real marks, no line rings.", ""]


def tc(s):
    return f"{int(s // 60):02d}:{s % 60:04.1f}"


for ch in ("ch3", "ch4", "ch5"):
    rows = S.seconds(ch)
    t0 = 0.0
    thumbs = []
    index += [f"## {TITLES[ch]}", "", "| # | Shot | Time | VO | Frame |", "|---|---|---|---|---|"]
    for k, ((s, m, lab, v1id), (_, _, _, sec)) in enumerate(zip(S.CHAPTERS[ch], rows)):
        sid = lab.split(" ")[0]; name = lab[len(sid) + 1:]
        d = os.path.join(st, f"{s}_{m}_{T}")
        if os.path.exists(os.path.join(d, "plate.exr")):
            meta = json.load(open(os.path.join(d, "plate.json"))); png = os.path.join(tmp, "g.png")
            grade.grade_file(os.path.join(d, "plate.exr"), png, look="cinematic", exposure=meta["exposure"], cine=meta.get("cine") or None)
            img = Image.open(png).convert("RGB").resize((W, H), Image.LANCZOS)
        else:
            img = Image.new("RGB", (W, H), (30, 30, 34)); ImageDraw.Draw(img).text((40, H // 2 - 14), "frame pending", font=f_big, fill=(170, 170, 170))
        fr = Image.new("RGB", (W, H + CAP), (16, 17, 20)); fr.paste(img, (0, 0)); d_ = ImageDraw.Draw(fr)
        v2 = sid in S.CHANGED
        head = f"{TITLES[ch].split(' · ')[0].upper()}  ·  {sid}  ·  {tc(t0)}–{tc(t0 + sec)}  ·  {name}" + ("   [v2]" if v2 else "")
        d_.text((18, H + 12), head, font=f_big, fill=(245, 236, 210) if v2 else (235, 235, 235))
        y = H + 56
        for ln in textwrap.wrap("VO: " + S.VO.get(sid, ""), 118)[:3]:
            d_.text((18, y), ln, font=f_txt, fill=(210, 210, 210)); y += 26
        act = S.ACTION.get(sid)
        if act:
            for ln in textwrap.wrap("Action: " + act, 128)[:3]:
                d_.text((18, y), ln, font=f_it, fill=(160, 190, 215)); y += 23
        fn = f"{ch}_{k + 1:02d}_{sid}.jpg"
        fr.save(os.path.join(out, fn), quality=84)
        thumbs.append(fr)
        index.append(f"| {k + 1} | {sid} {name}{' (v2)' if v2 else ''} | {tc(t0)}–{tc(t0 + sec)} | {S.VO.get(sid, '')} | [{fn}]({fn}) |")
        t0 += sec
    # contact sheet: 3 per row, small
    tw, th = 640, int(640 * (H + CAP) / W)
    cols = 3; rws = (len(thumbs) + cols - 1) // cols
    cs = Image.new("RGB", (tw * cols, th * rws), (10, 10, 12))
    for k, im in enumerate(thumbs):
        cs.paste(im.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
    cs.save(os.path.join(out, f"{ch}_contact.jpg"), quality=82)
    index += ["", f"Contact sheet: [{ch}_contact.jpg]({ch}_contact.jpg) · {len(thumbs)} shots · ≈ {tc(t0)}", ""]
    print("[frames]", ch, len(thumbs), "shots", tc(t0))
open(os.path.join(out, "INDEX.md"), "w").write("\n".join(index) + "\n")
print("[frames] done", out)
