"""Time the edit to the recorded voiceover.

  python edit/align.py vo/voiceover.wav            -> edit/timeline.json (beats timed to the VO, word by word)
  python edit/align.py --estimate                  -> edit/timeline.json from the 130 wpm estimate (no VO yet)

How it works
  1. faster-whisper transcribes the VO with per-word timestamps.
  2. The recognised words are aligned to the script's words (difflib on normalised tokens); unmatched script words
     get times interpolated from their neighbours. Each narrated beat starts at its first word.
  3. The narration excludes chapter titles, so the title card and chapter cards get their own time: the VO is cut
     at the silence before each chapter and the card is inserted there (audio_edl lists the VO pieces + gaps).
"""
import os, sys, re, json, difflib, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from beats import BEATS, est_duration

LEAD_IN = 0.8          # black/quote breathing room before the first word
TAIL_GAP = 0.25        # beat ends this long after its last word if the next beat starts later


def norm_tokens(text):
    t = text.lower().replace("’", "'").replace("—", " ")
    t = re.sub(r"(\d),(\d)", r"\1\2", t)
    return re.findall(r"[a-z0-9']+", t)


# numbers in the script are spelled out ("thirty-three million"); whisper may write digits. Normalise both ways a bit.
NUM = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"}


def canon(tok):
    if tok.isdigit() and len(tok) == 1:
        return NUM[tok]
    return tok


def transcribe(path, model="small.en"):
    from faster_whisper import WhisperModel
    import wave, numpy as np
    m = WhisperModel(model, device="cpu", compute_type="int8")
    with wave.open(path) as w:   # 16 kHz mono PCM written by ffmpeg; decode ourselves (avoids PyAV version issues)
        audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
    segs, info = m.transcribe(audio, word_timestamps=True, vad_filter=True, beam_size=5)
    words = []
    for s in segs:
        for w in s.words:
            for tk in norm_tokens(w.word):
                words.append((canon(tk), w.start, w.end))
    return words, info.duration


def script_tokens():
    toks = []
    for bi, b in enumerate(BEATS):
        for tk in norm_tokens(b["text"]):
            toks.append((canon(tk), bi))
    return toks


def align(words, dur):
    st = script_tokens()
    a = [t for t, _ in st]; b = [w for w, _, _ in words]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    t_start = [None] * len(a); t_end = [None] * len(a)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            t_start[blk.a + k] = words[blk.b + k][1]; t_end[blk.a + k] = words[blk.b + k][2]
    matched = sum(x is not None for x in t_start)
    # interpolate gaps
    known = [i for i, v in enumerate(t_start) if v is not None]
    for i in range(len(a)):
        if t_start[i] is None:
            prev = max([k for k in known if k < i], default=None); nxt = min([k for k in known if k > i], default=None)
            if prev is None and nxt is None:
                t_start[i] = t_end[i] = 0.0
            elif prev is None:
                t_start[i] = t_end[i] = t_start[nxt]
            elif nxt is None:
                t_start[i] = t_end[i] = t_end[prev]
            else:
                f = (i - prev) / (nxt - prev)
                t_start[i] = t_end[prev] + (t_start[nxt] - t_end[prev]) * f; t_end[i] = t_start[i]
    first, last = {}, {}
    for i, (_, bi) in enumerate(st):
        first.setdefault(bi, t_start[i]); last[bi] = t_end[i]
    return first, last, matched / max(len(a), 1)


def build_timeline(first=None, last=None, vo_dur=None):
    """Lay out beats on the output timeline. Card beats (no narration) insert time: the VO is cut in the pause
    before the next narrated word and resumes when the card ends. Returns (beats, audio_edl)."""
    tl, audio = [], []
    t_out = 0.0
    if first is None:                                   # estimate mode (no VO yet)
        for b in BEATS:
            d = est_duration(b) if b["text"] else b["pad"]
            tl.append(dict(id=b["id"], start=t_out, end=t_out + d)); t_out += d
        return tl, audio
    shift = LEAD_IN                                     # output time = vo time + shift (grows at each card)
    vo_cursor = 0.0
    narrated = [i for i, b in enumerate(BEATS) if b["text"]]
    for i, b in enumerate(BEATS):
        if b["text"]:
            s = max(first[i] + shift, t_out) if tl else 0.0
            if tl:
                tl[-1]["end"] = s
            # the pad lets a beat linger when a card follows (the next narrated beat overrides the end otherwise)
            tl.append(dict(id=b["id"], start=s, end=last[i] + shift + TAIL_GAP + b["pad"]))
            t_out = tl[-1]["end"]
            continue
        # card: cut the VO in the pause between the previous and the next narrated words
        prev_n = max([k for k in narrated if k < i], default=None)
        next_n = min([k for k in narrated if k > i], default=None)
        if prev_n is not None and next_n is not None:
            cut = (last[prev_n] + first[next_n]) / 2
        elif prev_n is not None:
            cut = vo_dur
        else:
            cut = 0.0
        if cut > vo_cursor:
            audio.append(dict(kind="vo", src_start=vo_cursor, src_end=cut, at=vo_cursor + shift))
            vo_cursor = cut
        card_start = max(t_out, cut + shift)
        if tl:
            tl[-1]["end"] = card_start
        tl.append(dict(id=b["id"], start=card_start, end=card_start + b["pad"]))
        audio.append(dict(kind="gap", at=card_start, dur=b["pad"]))
        t_out = card_start + b["pad"]
        shift = t_out - cut
    if vo_cursor < vo_dur:
        audio.append(dict(kind="vo", src_start=vo_cursor, src_end=vo_dur, at=vo_cursor + shift))
    return tl, audio


def main():
    out = os.path.join(HERE, "timeline.json")
    if "--estimate" in sys.argv or len(sys.argv) < 2:
        tl, audio = build_timeline()
        meta = dict(mode="estimate", wpm=130)
    else:
        src = sys.argv[1]
        wav = os.path.join(HERE, "..", "vo", "_vo16k.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-ac", "1", "-ar", "16000", wav], check=True)
        words, dur = transcribe(wav, os.environ.get("WHISPER_MODEL", "small.en"))
        first, last, q = align(words, dur)
        tl, audio = build_timeline(first, last, dur)
        meta = dict(mode="vo", vo=os.path.abspath(src), vo_duration=dur, match_ratio=round(q, 3), words=len(words))
        print(f"aligned {len(words)} words · {q * 100:.1f}% of script words matched")
    json.dump(dict(meta=meta, beats=tl, audio=audio), open(out, "w"), indent=1)
    total = tl[-1]["end"]
    print(f"timeline: {len(tl)} beats · {int(total // 60)}:{total % 60:04.1f} -> {out}")


if __name__ == "__main__":
    main()
