"""STORYBOARD_FULL: the whole film in order. Part A frames (Cold Open, Ch1, Ch2) are captioned here from sb_a_shots.py and
the latest stills; part B frames (Ch3-5) come captioned from claude/radio-jingle-b (review/B_STORYBOARD_FRAMES).
  python sb_full.py <a_stills_dir> <a_durations.json> <b_frames_dir> <out_dir>
-> out_dir/frames/*.jpg (1280x774 each), out_dir/<part>_contact.jpg, out_dir/STORYBOARD_FULL.pdf, out_dir/INDEX.md
"""
import os, sys, json, glob, textwrap
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sb_a_shots as S

FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
FONT_R = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"
if not os.path.exists(FONT_R):
    FONT_R = FONT
W, IH, CH = 1280, 544, 230
PART_NAME = {"cold": "COLD OPEN", "ch1": "CHAPTER 1", "ch2": "CHAPTER 2"}
TITLES = {"cold": "Cold Open", "ch1": "Chapter One · Ten Minutes Home", "ch2": "Chapter Two · Seven Bolts",
          "ch3": "Chapter Three · The Man with the Spade", "ch4": "Chapter Four · The Clicks", "ch5": "Chapter Five · After the Verdict"}
LONG_T = {("path", "brush_long"): "0.55", ("woods", "night_long"): "0.6"}


def mmss(s):
    return f"{int(s // 60):02d}:{s % 60:04.1f}"


def still(d, set_, move):
    cands = []
    if (set_, move) in LONG_T:
        cands.append(os.path.join(d, f"hq_{set_}_{move}_{LONG_T[(set_, move)]}.png"))
    cands += [os.path.join(d, f"hq_{set_}_{move}.png"), os.path.join(d, f"{set_}_{move}_0.5.png")]
    cands += sorted(glob.glob(os.path.join(d, f"{set_}_{move}_*.png")))
    for p in cands:
        if os.path.exists(p):
            return p
    return None


def wrap_lines(draw, text, font, width):
    words = text.split(); lines = []; cur = ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def a_frame(img_path, head, vo, action, v2):
    fr = Image.new("RGB", (W, IH + CH), (14, 16, 20))
    if img_path:
        im = Image.open(img_path).convert("RGB")
        r = max(W / im.width, IH / im.height); im = im.resize((int(im.width * r + 0.5), int(im.height * r + 0.5)), Image.LANCZOS)
        x0 = (im.width - W) // 2; y0 = (im.height - IH) // 2; fr.paste(im.crop((x0, y0, x0 + W, y0 + IH)), (0, 0))
    d = ImageDraw.Draw(fr)
    f1 = ImageFont.truetype(FONT, 27); f2 = ImageFont.truetype(FONT_R, 20); f3 = ImageFont.truetype(FONT_R, 18)
    d.text((18, IH + 14), head + ("   [v2]" if v2 else ""), font=f1, fill=(240, 230, 205))
    y = IH + 56
    for ln in wrap_lines(d, "VO: " + vo, f2, W - 36)[:3]:
        d.text((18, y), ln, font=f2, fill=(222, 222, 222)); y += 25
    for ln in wrap_lines(d, "Action: " + action, f3, W - 36)[:4]:
        d.text((18, y), ln, font=f3, fill=(150, 185, 225)); y += 23
    return fr


def contact(frames, title, path, cols=4):
    tw, th = 480, 290
    rows = (len(frames) + cols - 1) // cols
    sh = Image.new("RGB", (cols * tw, 70 + rows * th), (10, 11, 14))
    d = ImageDraw.Draw(sh); d.text((16, 18), title, font=ImageFont.truetype(FONT, 32), fill=(240, 230, 205))
    for k, f in enumerate(frames):
        im = Image.open(f).convert("RGB").resize((tw - 8, th - 8), Image.LANCZOS)
        sh.paste(im, ((k % cols) * tw + 4, 70 + (k // cols) * th + 4))
    sh.save(path, quality=88)


def main(a_dir, durs_json, b_dir, out):
    os.makedirs(os.path.join(out, "frames"), exist_ok=True)
    durs = json.load(open(durs_json))
    parts = []
    idx = ["# Radio Jingle · STORYBOARD_FULL (whole film, in order)", "",
           "Realistic 3D in look v5 throughout. Times are estimates within each part (184 wpm, title lead, long takes at their own length) until the voiceover lands.",
           "v2 = reworked after the reference study. Hard rules applied: nothing moves by itself, no hand-only frames, no flat graphics.", ""]
    for p in ("cold", "ch1", "ch2"):
        t = 0.0; frames = []
        idx += [f"## {TITLES[p]} (part A)", "", "| # | Shot | Time | VO | Frame |", "|---|---|---|---|---|"]
        for k, ((set_, move, sid, title, vo, action, v2), dur) in enumerate(zip(S.A[p], durs[p])):
            head = f"{PART_NAME[p]}  ·  {sid}  ·  {mmss(t)}–{mmss(t + dur)}  ·  {title}"
            fr = a_frame(still(a_dir, set_, move), head, vo, action, v2)
            fn = os.path.join(out, "frames", f"{p}_{k + 1:02d}_{sid.replace('/', '-')}.jpg"); fr.save(fn, quality=90); frames.append(fn)
            idx.append(f"| {k + 1} | {sid} {title}{' (v2)' if v2 else ''} | {mmss(t)}–{mmss(t + dur)} | {vo} | frames/{os.path.basename(fn)} |")
            t += dur
        idx += ["", f"{len(frames)} shots · ≈ {mmss(t)}", ""]
        contact(frames, f"{TITLES[p]}  ·  {len(frames)} shots  ·  ≈ {mmss(t)}", os.path.join(out, f"{p}_contact.jpg"))
        parts.append((p, frames))
    for p in ("ch3", "ch4", "ch5"):
        frames = sorted(glob.glob(os.path.join(b_dir, f"{p}_[0-9][0-9]_*.jpg")))
        for f in frames:
            Image.open(f).convert("RGB").save(os.path.join(out, "frames", os.path.basename(f)), quality=90)
        frames = [os.path.join(out, "frames", os.path.basename(f)) for f in frames]
        contact(frames, f"{TITLES[p]}  ·  {len(frames)} shots (part B)", os.path.join(out, f"{p}_contact.jpg"))
        parts.append((p, frames))
        idx += [f"## {TITLES[p]} (part B)", "", f"{len(frames)} shots, captioned by chat B: see frames/{p}_*.jpg (VO and timing on each frame).", ""]
    # PDF: a title page per part, then pages of 2 x 3 frames
    pages = []
    PW, PH = 2 * W + 60, 3 * (IH + CH) + 140
    for p, frames in parts:
        tp = Image.new("RGB", (PW, PH), (10, 11, 14)); d = ImageDraw.Draw(tp)
        d.text((80, PH // 2 - 80), "The Kidnapper Who Only Played a Radio Jingle", font=ImageFont.truetype(FONT_R, 40), fill=(180, 180, 180))
        d.text((80, PH // 2 - 20), TITLES[p], font=ImageFont.truetype(FONT, 72), fill=(240, 230, 205))
        d.text((80, PH // 2 + 80), f"{len(frames)} shots", font=ImageFont.truetype(FONT_R, 36), fill=(160, 170, 180))
        pages.append(tp)
        for i in range(0, len(frames), 6):
            pg = Image.new("RGB", (PW, PH), (10, 11, 14)); d = ImageDraw.Draw(pg)
            d.text((24, 30), TITLES[p], font=ImageFont.truetype(FONT, 40), fill=(200, 195, 180))
            for j, f in enumerate(frames[i:i + 6]):
                pg.paste(Image.open(f).convert("RGB"), (20 + (j % 2) * (W + 20), 110 + (j // 2) * (IH + CH + 10)))
            pages.append(pg)
    small = [pg.resize((pg.width // 2, pg.height // 2), Image.LANCZOS) for pg in pages]
    small[0].save(os.path.join(out, "STORYBOARD_FULL.pdf"), save_all=True, append_images=small[1:], resolution=100, quality=85)
    open(os.path.join(out, "INDEX.md"), "w").write("\n".join(idx) + "\n")
    print("pages", len(pages), "frames", sum(len(f) for _, f in parts))


if __name__ == "__main__":
    main(*sys.argv[1:5])
