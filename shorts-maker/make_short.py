#!/usr/bin/env python3
"""
make_short.py - build a vertical "story short" (TikTok / Reels / YouTube Shorts)

The format:
  * 1080x1920, 30 fps
  * a narrator tells a short story, with an occasional character voice line
  * a new shot every 1-2 seconds (images get a slow zoom/pan, video clips play)
  * big bold 1-2 word captions in the lower middle, timed to each spoken word
  * ends on a cliffhanger ("follow for part 2")

You supply:  script.txt  +  scenes/ (images or clips)  [+ voice.mp3] [+ music.mp3]
You get:     a finished .mp4 ready to upload.

Usage:
  python3 make_short.py example/              # renders example/out.mp4
  python3 make_short.py myvideo/ --music bg.mp3 --voice en-US-AndrewNeural

See README.md for the script format and the full workflow.
"""
import argparse
import asyncio
import difflib
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

W, H, FPS = 1080, 1920, 30
HERE = Path(__file__).resolve().parent
FONTS_DIR = HERE / "fonts"
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv", ".m4v", ".gif"}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def run(cmd, quiet=True):
    """Run a command, raising with its stderr on failure."""
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        sys.exit(f"\nCommand failed:\n  {' '.join(map(str, cmd))}\n\n{r.stderr[-3000:]}")
    if not quiet:
        print(r.stdout)
    return r.stdout


def duration_of(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=nw=1:nk=1", str(path)])
    return float(out.strip())


def norm(word):
    """Normalise a word for matching script text against recognised speech."""
    return re.sub(r"[^a-z0-9]", "", word.lower())


# --------------------------------------------------------------------------- #
# 1. parse the script
# --------------------------------------------------------------------------- #
MARK_RE = re.compile(r"\[([^\]]+)\]")     # [03]  -> cut to scene 03 here
VOICE_RE = re.compile(r"<([A-Za-z]{2}-[A-Za-z]{2}-\w+)>")  # <en-US-ChristopherNeural>


def parse_script(text):
    """
    Returns a list of lines: {"voice": str|None, "words": [{"text", "shot"}]}
    "shot" is the scene id that starts on that word (or None).
    """
    lines = []
    for raw in text.splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        voice = None
        m = VOICE_RE.search(raw)
        if m:
            voice = m.group(1)
            raw = VOICE_RE.sub(" ", raw)
        words, pending = [], None
        for tok in re.split(r"(\[[^\]]+\])|\s+", raw):
            if not tok:
                continue
            mm = MARK_RE.fullmatch(tok)
            if mm:
                pending = mm.group(1).strip()
                continue
            words.append({"text": tok, "shot": pending})
            pending = None
        if words:
            lines.append({"voice": voice, "words": words})
    return lines


# --------------------------------------------------------------------------- #
# 2. voiceover + word timings
# --------------------------------------------------------------------------- #
async def _tts_line(text, voice, rate, pitch, out_path):
    import edge_tts
    import edge_tts.communicate as ec
    import ssl

    # Respect a custom CA bundle / proxy if the machine needs one.
    cafile = os.environ.get("SSL_CERT_FILE")
    if cafile and os.path.exists(cafile):
        ec._SSL_CTX = ssl.create_default_context(cafile=cafile)
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")

    comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch,
                                boundary="WordBoundary", proxy=proxy)
    words = []
    with open(out_path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({"text": chunk["text"],
                              "start": chunk["offset"] / 1e7,
                              "end": (chunk["offset"] + chunk["duration"]) / 1e7})
    return words


def tts_voiceover(lines, tmp, voice, rate, pitch, gap):
    """Generate narration line by line with Microsoft Edge neural voices (free)."""
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        sys.exit("edge-tts is not installed. Run:  pip install edge-tts\n"
                 "(or record/generate your own voice.mp3 and put it in the project folder)")
    parts, timed, t = [], [], 0.0
    silence = tmp / "gap.wav"
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
         "-t", f"{gap}", str(silence)])
    for i, line in enumerate(lines):
        text = " ".join(w["text"] for w in line["words"])
        mp3 = tmp / f"line_{i:03d}.mp3"
        wav = tmp / f"line_{i:03d}.wav"
        v = line["voice"] or voice
        print(f"  voice [{v}] {text}")
        expected = len([w for w in line["words"] if norm(w["text"])])
        for attempt in range(5):
            # the free Edge service sometimes drops or truncates a line - retry
            try:
                words = asyncio.run(_tts_line(text, v, rate, pitch, mp3))
                if len(words) >= 0.7 * expected:
                    break
                err = f"only {len(words)}/{expected} words came back"
            except Exception as e:  # network hiccup / NoAudioReceived
                err = f"{type(e).__name__}: {e}"
            print(f"    retrying ({err})")
            time.sleep(1.5 * (attempt + 1))
        else:
            sys.exit(f"Text-to-speech kept failing for: {text}\nLast error: {err}\n"
                     f"If it says NoAudioReceived, check the voice name '{v}' exists "
                     f"(edge-tts --list-voices).")
        run(["ffmpeg", "-y", "-i", str(mp3), "-ar", "44100", "-ac", "1", str(wav)])
        for w in words:
            timed.append({"text": w["text"], "start": t + w["start"], "end": t + w["end"]})
        t += duration_of(wav)
        parts.append(wav)
        if i < len(lines) - 1:
            parts.append(silence)
            t += gap
    out = tmp / "voice.wav"
    lst = tmp / "voice_list.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)])
    return out, timed


def transcribe_words(audio_path, model_size):
    """Word-level timestamps for a voiceover you recorded / generated elsewhere."""
    try:
        from faster_whisper import WhisperModel
        import numpy as np
    except ImportError:
        sys.exit("To time captions to your own voice file, run:  pip install faster-whisper")
    print(f"  transcribing {audio_path.name} with whisper-{model_size} (first run downloads the model)...")
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(audio_path), "-ac", "1",
                          "-ar", "16000", "-f", "f32le", "-"], stdout=subprocess.PIPE).stdout
    audio = np.frombuffer(pcm, dtype=np.float32)
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segs, _ = model.transcribe(audio, word_timestamps=True)
    timed = []
    for s in segs:
        for w in s.words:
            timed.append({"text": w.word.strip(), "start": w.start, "end": w.end})
    return timed


def align(script_words, timed_words):
    """
    Give every script word a start/end time by matching it to the recognised /
    synthesised words. Unmatched words are interpolated between neighbours.
    """
    a = [norm(w["text"]) for w in script_words]
    b = [norm(w["text"]) for w in timed_words]
    times = [None] * len(a)
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            tw = timed_words[blk.b + k]
            times[blk.a + k] = (tw["start"], tw["end"])
    # handle a "39" vs "thirty nine" style mismatch: spread over the gap
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "replace" and j2 > j1:
            s, e = timed_words[j1]["start"], timed_words[j2 - 1]["end"]
            n = i2 - i1
            for k in range(n):
                times[i1 + k] = (s + (e - s) * k / n, s + (e - s) * (k + 1) / n)
    # interpolate anything still missing
    known = [i for i, t in enumerate(times) if t]
    if not known:
        sys.exit("Could not match any script words to the voiceover - is it the right audio?")
    for i in range(len(times)):
        if times[i]:
            continue
        prev = max([k for k in known if k < i], default=None)
        nxt = min([k for k in known if k > i], default=None)
        if prev is None:
            times[i] = (times[nxt][0], times[nxt][0])
        elif nxt is None:
            times[i] = (times[prev][1], times[prev][1] + 0.3)
        else:
            s, e = times[prev][1], times[nxt][0]
            frac = (i - prev) / (nxt - prev)
            times[i] = (s + (e - s) * frac, s + (e - s) * frac)
    for w, (s, e) in zip(script_words, times):
        w["start"], w["end"] = s, max(e, s + 0.05)


# --------------------------------------------------------------------------- #
# 3. captions (ASS subtitle file burned in by ffmpeg/libass)
# --------------------------------------------------------------------------- #
def chunk_words(words, max_words, max_chars):
    chunks, cur = [], []
    for w in words:
        if cur and (len(cur) >= max_words or
                    len(" ".join(x["text"] for x in cur + [w])) > max_chars or
                    (w["start"] - cur[-1]["end"]) > 0.35):
            chunks.append(cur)
            cur = []
        cur.append(w)
        if re.search(r"[.,!?;:—]$", w["text"]):
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


def ass_time(t):
    t = max(t, 0)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def write_ass(words, total, path, args):
    chunks = chunk_words(words, args.words_per_caption, args.max_chars)
    y = int(H * args.caption_y)
    pop = r"{\fscx85\fscy85\t(0,90,\fscx100\fscy100)}" if args.pop else ""
    events = []
    for i, ch in enumerate(chunks):
        start = ch[0]["start"]
        nxt = chunks[i + 1][0]["start"] if i + 1 < len(chunks) else total
        # stay on screen until the next caption, unless there's a long pause
        end = min(nxt, ch[-1]["end"] + 0.6)
        text = " ".join(w["text"] for w in ch)
        if args.uppercase:
            text = text.upper()
        text = text.replace("{", "(").replace("}", ")")
        events.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Cap,,0,0,0,,"
                      f"{{\\an5\\pos({W // 2},{y})}}{pop}{text}")
    path.write_text(f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{args.font},{args.font_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,{args.outline},{args.shadow},5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(events) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# 4. shots
# --------------------------------------------------------------------------- #
def find_scene(scenes_dir, shot_id):
    if not scenes_dir.exists():
        return None
    cands = sorted(p for p in scenes_dir.iterdir()
                   if p.suffix.lower() in IMAGE_EXT | VIDEO_EXT)
    for p in cands:  # exact stem first, then prefix ("03" matches "03_boss_angry.png")
        if p.stem == shot_id:
            return p
    for p in cands:
        if p.stem.startswith(shot_id):
            return p
    return None


def plan_shots(words, total, scenes_dir, max_shot):
    """Turn [NN] markers into a list of (scene_id, start, end)."""
    shots = []
    for w in words:
        if w["shot"]:
            shots.append({"id": w["shot"], "start": w["start"]})
    if not shots:
        # no markers: auto-cut at punctuation / every ~max_shot seconds,
        # cycling through whatever is in scenes/
        files = sorted(p.stem for p in scenes_dir.iterdir()
                       if p.suffix.lower() in IMAGE_EXT | VIDEO_EXT) if scenes_dir.exists() else []
        if not files:
            files = ["01"]
        last = -99.0
        for i, w in enumerate(words):
            prev_punct = i > 0 and re.search(r"[.,!?;:]$", words[i - 1]["text"])
            if i == 0 or (w["start"] - last >= max_shot) or (prev_punct and w["start"] - last >= 1.0):
                shots.append({"id": files[len(shots) % len(files)], "start": w["start"]})
                last = w["start"]
    shots[0]["start"] = 0.0
    for i, s in enumerate(shots):
        s["end"] = shots[i + 1]["start"] if i + 1 < len(shots) else total
    return [s for s in shots if s["end"] - s["start"] > 0.02]


MOVES = ["zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up", "pan_down"]


def render_shot(src, frames, out, move, label):
    cover = (f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
             f"crop={W}:{H},setsar=1")
    enc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
           "-r", str(FPS), "-an"]
    dur = frames / FPS
    if src is None:
        # placeholder so you can check timing before the art exists
        txt = label.replace(":", r"\:").replace("'", "")
        run(["ffmpeg", "-y", "-f", "lavfi", "-i",
             f"color=c=0x{random.randint(0x202020, 0x707070):06x}:s={W}x{H}:r={FPS}",
             "-frames:v", str(frames), "-vf",
             f"drawtext=fontfile={FONTS_DIR / 'Montserrat-ExtraBold.ttf'}:text='SCENE {txt}':"
             f"fontcolor=white@0.5:fontsize=90:x=(w-tw)/2:y=h*0.3", *enc, str(out)])
    elif src.suffix.lower() in VIDEO_EXT:
        run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(src), "-frames:v", str(frames),
             "-vf", f"{cover},fps={FPS}", *enc, str(out)])
    else:
        # Ken Burns on a 2x canvas so the motion is smooth, not jittery
        n = max(frames - 1, 1)
        z0, z1 = {"zoom_in": (1.0, 1.15), "zoom_out": (1.15, 1.0)}.get(move, (1.12, 1.12))
        z = f"{z0}+({z1 - z0})*on/{n}"
        cx, cy = "(iw-iw/zoom)/2", "(ih-ih/zoom)/2"
        x, y = {"pan_left": (f"(iw-iw/zoom)*(1-on/{n})", cy),
                "pan_right": (f"(iw-iw/zoom)*on/{n}", cy),
                "pan_up": (cx, f"(ih-ih/zoom)*(1-on/{n})"),
                "pan_down": (cx, f"(ih-ih/zoom)*on/{n}")}.get(move, (cx, cy))
        vf = (f"scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase:flags=lanczos,"
              f"crop={W * 2}:{H * 2},setsar=1,"
              f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS}")
        run(["ffmpeg", "-y", "-loop", "1", "-i", str(src), "-frames:v", str(frames),
             "-vf", vf, *enc, str(out)])


def write_timings_report(proj, lines, words, total):
    """timings.json (every word) + timings.txt (every line and shot marker) for planning."""
    (proj / "timings.json").write_text(json.dumps(
        [{"word": w["text"], "start": round(w["start"], 3), "end": round(w["end"], 3)} for w in words], indent=1))
    out = [f"TOTAL {total:.2f}s  ({len(words)} words, {len(words) / max(total, 1):.2f} words/s)", ""]
    for ln in lines:
        ws = ln["words"]
        out.append(f"[{ws[0]['start']:6.2f} - {ws[-1]['end']:6.2f}]  {' '.join(w['text'] for w in ws)}")
        for w in ws:
            if w["shot"]:
                out.append(f"      shot [{w['shot']}] starts {w['start']:6.2f}  on '{w['text']}'")
    (proj / "timings.txt").write_text("\n".join(out) + "\n")
    print("\n".join(out))
    print(f"\nwrote {proj / 'timings.txt'} and timings.json")


def make_preview(proj, anim, shots, words, tmp, only, at):
    """Render a few stills of every animated shot into contact sheets (fast review)."""
    todo = [(i, s) for i, s in enumerate(shots) if not only or s["id"] in only]
    jobs = []
    for i, s in todo:
        for k, u in enumerate(at):
            jobs.append({"id": s["id"], "frames": s["frames"], "still": u, "out": str(tmp / f"still_{i:03d}_{k}.jpg")})
    jf = tmp / "preview_jobs.json"
    jf.write_text(json.dumps(jobs))
    print(f"3/3 rendering {len(jobs)} preview stills")
    subprocess.run(["node", str(HERE / "animator" / "render.js"), str(Path(anim).resolve()), str(jf)])
    font = FONTS_DIR / "Montserrat-ExtraBold.ttf"
    labeled = []
    for n, j in enumerate(jobs):
        if not Path(j["out"]).exists():
            continue
        s = next(s for s in shots if s["id"] == j["id"])
        said = " ".join(w["text"] for w in words if s["start"] <= w["start"] < s["end"])[:38]
        lab = tmp / f"label_{n}.txt"
        lab.write_text(f"[{s['id']}] u={j['still']:.1f}  {s['end'] - s['start']:.1f}s\n{said}")
        dst = tmp / f"lab_{len(labeled):03d}.jpg"
        run(["ffmpeg", "-y", "-i", j["out"], "-vf",
             f"scale=360:640,drawbox=y=0:w=iw:h=74:color=black@0.65:t=fill,"
             f"drawtext=fontfile={font}:textfile={lab}:fontcolor=white:fontsize=19:x=8:y=8:line_spacing=6",
             "-q:v", "3", str(dst)])
        labeled.append(dst)
    per = len(at) * 4  # 4 shots per sheet
    for old in proj.glob("preview_*.jpg"):
        old.unlink()
    sheets = []
    for sidx in range(0, len(labeled), per):
        chunk = labeled[sidx:sidx + per]
        lst = tmp / f"sheet_{sidx}.txt"
        for k, f in enumerate(chunk):
            shutil.copy(f, tmp / f"sh_{sidx}_{k:03d}.jpg")
        out = proj / f"preview_{sidx // per + 1}.jpg"
        cols = len(at) * 2
        run(["ffmpeg", "-y", "-framerate", "1", "-i", str(tmp / f"sh_{sidx}_%03d.jpg"), "-vf",
             f"tile={cols}x{-(-len(chunk) // cols)}:padding=6:color=white", "-frames:v", "1", "-q:v", "3", str(out)])
        sheets.append(out)
    print("\npreview sheets:\n  " + "\n  ".join(map(str, sheets)))


def render_animation(episode, todo, tmp):
    """Render shots with the three.js animator (animator/render.js) via headless Chromium."""
    if not shutil.which("node"):
        sys.exit("Animated shots need Node.js - install it from https://nodejs.org (see README.md)")
    if not (HERE / "node_modules" / "three").exists():
        sys.exit(f"Animated shots need three.js. Run once:\n  cd {HERE} && npm install && npx playwright install chromium")
    jobs = [{"id": s["id"], "frames": s["frames"], "out": str(tmp / f"anim_{i:03d}.mp4")} for i, s in todo]
    jf = tmp / "anim_jobs.json"
    jf.write_text(json.dumps(jobs))
    r = subprocess.run(["node", str(HERE / "animator" / "render.js"), str(Path(episode).resolve()), str(jf)])
    if r.returncode != 0:
        print("  (some animated shots failed - they fall back to placeholders)")
    out = {}
    for (i, _), j in zip(todo, jobs):
        if Path(j["out"]).exists():
            out[i] = Path(j["out"])
    return out


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Build a vertical story short from a script + scenes.")
    ap.add_argument("project", type=Path, help="folder with script.txt and scenes/")
    ap.add_argument("-o", "--out", type=Path, help="output file (default: <project>/out.mp4)")
    ap.add_argument("--voice", default="en-US-AndrewNeural",
                    help="narrator voice for edge-tts (run `edge-tts --list-voices`)")
    ap.add_argument("--rate", default="+12%", help="narration speed, e.g. +10%%")
    ap.add_argument("--pitch", default="+0Hz")
    ap.add_argument("--gap", type=float, default=0.12, help="pause between script lines (s)")
    ap.add_argument("--voice-file", type=Path,
                    help="use your own voiceover instead of TTS (default: <project>/voice.mp3 if present)")
    ap.add_argument("--whisper-model", default="small")
    ap.add_argument("--animation", type=Path,
                    help="episode file with animated 3D shots (default: <project>/animation.js if present)")
    ap.add_argument("--music", type=Path, help="background music (default: <project>/music.mp3 if present)")
    ap.add_argument("--music-volume", type=float, default=0.18)
    ap.add_argument("--sfx", type=Path, help="sound-effects track mixed at full level, not ducked (default: <project>/sfx.wav if present)")
    ap.add_argument("--font", default="Montserrat ExtraBold")
    ap.add_argument("--font-size", type=int, default=116)
    ap.add_argument("--outline", type=float, default=8)
    ap.add_argument("--shadow", type=float, default=4)
    ap.add_argument("--caption-y", type=float, default=0.70, help="caption height, 0=top 1=bottom")
    ap.add_argument("--words-per-caption", type=int, default=3)
    ap.add_argument("--max-chars", type=int, default=12, help="max characters per caption")
    ap.add_argument("--uppercase", action="store_true")
    ap.add_argument("--pop", action="store_true", help="little scale-up pop on each caption")
    ap.add_argument("--max-shot", type=float, default=2.2, help="auto-cut length when script has no [NN] markers")
    ap.add_argument("--tail", type=float, default=0.6, help="seconds to hold after the last word")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--keep-temp", action="store_true")
    ap.add_argument("--timings-only", action="store_true",
                    help="just time the voiceover against the script, write timings.txt, and stop")
    ap.add_argument("--preview", action="store_true",
                    help="render a few stills per animated shot into preview_N.jpg contact sheets, and stop")
    ap.add_argument("--preview-at", default="0.1,0.5,0.9", help="moments (0-1) of each shot to preview")
    ap.add_argument("--shots", help="with --preview: only these shot ids, e.g. 03,07,12")
    ap.add_argument("--rerender", help="full render re-animating only these shot ids (e.g. 06,11); "
                    "all other shots reuse their last render. Use '' to reuse everything cached")
    args = ap.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            sys.exit(f"{tool} not found - install ffmpeg first (see README.md)")

    proj = args.project
    script_path = proj / "script.txt"
    if not script_path.exists():
        sys.exit(f"{script_path} not found")
    scenes_dir = proj / "scenes"
    out = args.out or proj / "out.mp4"
    random.seed(args.seed)

    lines = parse_script(script_path.read_text(encoding="utf-8"))
    words = [w for ln in lines for w in ln["words"]]
    if not words:
        sys.exit("script.txt has no words in it")

    tmp = Path(tempfile.mkdtemp(prefix="short_"))
    try:
        # -- voice -------------------------------------------------------------
        voice_file = args.voice_file
        if voice_file is None:
            for name in ("voice.mp3", "voice.wav", "voice.m4a"):
                if (proj / name).exists():
                    voice_file = proj / name
                    break
        print("1/5 voiceover")
        cache = proj / ".cache"
        cache.mkdir(exist_ok=True)
        if voice_file:
            # whisper is slow: cache the word timings per voice file
            key = hashlib.sha1(voice_file.read_bytes()).hexdigest()[:16] + "_" + args.whisper_model
            cf = cache / f"whisper_{key}.json"
            if cf.exists():
                timed = json.loads(cf.read_text())
                print(f"  using cached word timings for {voice_file.name}")
            else:
                timed = transcribe_words(voice_file, args.whisper_model)
                cf.write_text(json.dumps(timed))
            voice_path = voice_file
        else:
            spoken = json.dumps([[ln["voice"], [w["text"] for w in ln["words"]]] for ln in lines])
            key = hashlib.sha1((spoken + args.voice + args.rate + args.pitch + str(args.gap)).encode()).hexdigest()[:16]
            cw, cf = cache / f"tts_{key}.wav", cache / f"tts_{key}.json"
            if cw.exists() and cf.exists():
                voice_path, timed = cw, json.loads(cf.read_text())
                print("  using cached narration")
            else:
                voice_path, timed = tts_voiceover(lines, tmp, args.voice, args.rate, args.pitch, args.gap)
                shutil.copy(voice_path, cw); cf.write_text(json.dumps(timed)); voice_path = cw
        align(words, timed)
        speech_end = duration_of(voice_path)
        total = speech_end + args.tail
        if args.timings_only:
            write_timings_report(proj, lines, words, total)
            return

        # -- captions ------------------------------------------------------------
        print("2/5 captions")
        ass = tmp / "captions.ass"
        write_ass(words, total, ass, args)
        (proj / "timings.json").write_text(json.dumps(
            [{"word": w["text"], "start": round(w["start"], 3), "end": round(w["end"], 3)} for w in words],
            indent=1))

        # -- shots ---------------------------------------------------------------
        shots = plan_shots(words, total, scenes_dir, args.max_shot)
        frame_pos = 0
        for s in shots:
            s["frames"] = max(round(s["end"] * FPS) - frame_pos, 1)
            frame_pos += s["frames"]

        # animated shots: render any shot without a scene file from animation.js
        anim = args.animation or (proj / "animation.js" if (proj / "animation.js").exists() else None)
        if args.preview:
            if not anim:
                sys.exit("--preview needs an animation.js in the project")
            only = set(x.strip() for x in args.shots.split(",")) if args.shots else None
            make_preview(proj, anim, shots, words, tmp, only, [float(x) for x in args.preview_at.split(",")])
            return
        animated = {}
        if anim:
            todo = [(i, s) for i, s in enumerate(shots) if not find_scene(scenes_dir, s["id"])]
            # shot cache: with --rerender, reuse every other shot's last render (same length)
            acache = cache / "anim"; acache.mkdir(exist_ok=True)
            cpath = lambda s: acache / f"{s['id']}_{s['frames']}.mp4"
            if args.rerender is not None:
                redo = set(x.strip() for x in args.rerender.split(",") if x.strip())
                for i, s in todo:
                    if s["id"] not in redo and cpath(s).exists():
                        animated[i] = cpath(s)
                todo = [(i, s) for i, s in todo if i not in animated]
                print(f"  reusing {len(animated)} cached shots")
            if todo:
                print(f"3/5 animating {len(todo)} shots from {anim.name} (3D render, takes a few minutes)")
                fresh = render_animation(anim, todo, tmp)
                for i, f in fresh.items():
                    shutil.copy(f, cpath(shots[i]))
                animated.update(fresh)
        print(f"{'3b' if anim else '3'}/5 preparing {len(shots)} shots")
        clips, last_move = [], None
        for i, s in enumerate(shots):
            frames = s["frames"]
            src = find_scene(scenes_dir, s["id"]) or animated.get(i)
            move = random.choice([m for m in MOVES if m != last_move])
            last_move = move
            tag = src.name if src else "(placeholder)"
            if i in animated:
                tag = "(animated)"
            print(f"  shot {i + 1:02d}  [{s['id']}] {tag:<28} {frames / FPS:4.2f}s  {move if src and src.suffix.lower() in IMAGE_EXT else ''}")
            clip = tmp / f"shot_{i:03d}.mp4"
            render_shot(src, frames, clip, move, s["id"])
            clips.append(clip)

        print("4/5 joining shots")
        lst = tmp / "shots.txt"
        lst.write_text("".join(f"file '{c}'\n" for c in clips))
        joined = tmp / "joined.mp4"
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)])

        # -- final: captions + audio mix -----------------------------------------
        print("5/5 captions + audio mix")
        music = args.music or next((proj / n for n in ("music.mp3", "music.wav", "music.m4a")
                                    if (proj / n).exists()), None)
        ass_arg = str(ass).replace("\\", "/").replace(":", r"\:")
        vf = f"subtitles=filename='{ass_arg}':fontsdir='{FONTS_DIR}'"
        sfx = args.sfx or (proj / "sfx.wav" if (proj / "sfx.wav").exists() else None)
        cmd = ["ffmpeg", "-y", "-i", str(joined), "-i", str(voice_path)]
        if music:
            cmd += ["-stream_loop", "-1", "-i", str(music)]
            # music sits under the narration and ducks when someone talks
            af = (f"[1:a]aresample=44100,aformat=channel_layouts=stereo,apad,asplit=2[vo][sc];"
                  f"[2:a]aresample=44100,aformat=channel_layouts=stereo,volume={args.music_volume}[m];"
                  f"[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[md];"
                  f"[vo][md]amix=inputs=2:duration=first:normalize=0,"
                  f"afade=t=out:st={total - 0.4:.2f}:d=0.4[a]")
        else:
            af = "[1:a]aresample=44100,aformat=channel_layouts=stereo,apad[a]"
        if sfx:
            # sound effects sit on top, never ducked
            n = 3 if music else 2
            cmd += ["-i", str(sfx)]
            af = af.replace("[a]", "[pre]") + f";[{n}:a]aresample=44100,aformat=channel_layouts=stereo,apad[fx];[pre][fx]amix=inputs=2:duration=first:normalize=0[a]"
        cmd += ["-filter_complex", f"[0:v]{vf}[v];{af}", "-map", "[v]", "-map", "[a]",
                "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", str(out)]
        run(cmd)
        print(f"\nDone -> {out}  ({total:.1f}s, {len(shots)} shots, {len(words)} words)")
    finally:
        if args.keep_temp:
            print(f"temp files kept in {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
