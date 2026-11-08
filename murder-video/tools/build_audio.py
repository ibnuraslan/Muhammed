#!/usr/bin/env python3
"""Step 1 of the pipeline.

Reads a story JSON, generates every voice line with Piper TTS, works out the
timing of every shot from the real speech lengths, and writes:

  build/<story>/timeline.json  - consumed by the renderer (shot times, captions, lip-sync)
  build/<story>/audio.wav      - full soundtrack (voices + synthesized music + sfx)

Usage: python3 tools/build_audio.py stories/crippen.json
"""
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import wave

import numpy as np
from scipy.signal import butter, sosfilt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 44100
FPS = 30
RNG = np.random.default_rng(7)


# ----------------------------------------------------------------- io helpers
def read_wav(path):
    with wave.open(path, "rb") as w:
        n = w.getnframes()
        data = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768
        if w.getnchannels() == 2:
            data = data.reshape(-1, 2).mean(axis=1)
        return data, w.getframerate()


def write_wav(path, stereo):
    stereo = np.clip(stereo, -1, 1)
    pcm = (stereo * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def tts(text, voice, cache_dir):
    model = os.path.join(ROOT, "assets", "voices", voice["model"] + ".onnx")
    speed = voice.get("speed", 1.0)
    key = hashlib.md5(f"{text}|{voice['model']}|{speed}".encode()).hexdigest()[:16]
    raw = os.path.join(cache_dir, key + ".raw.wav")
    out = os.path.join(cache_dir, key + ".wav")
    if not os.path.exists(out):
        subprocess.run(
            [sys.executable, "-m", "piper", "-m", model, "-f", raw,
             "--length-scale", str(1.0 / speed), "--sentence-silence", "0.12"],
            input=text.encode(), check=True, capture_output=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-ar", str(SR), "-ac", "1", out], check=True)
        os.remove(raw)
    audio, _ = read_wav(out)
    # trim leading / trailing silence
    thr = 0.012
    idx = np.where(np.abs(audio) > thr)[0]
    if len(idx):
        audio = audio[max(0, idx[0] - 600): min(len(audio), idx[-1] + 2200)]
    return audio


# ----------------------------------------------------------------- dsp helpers
def bp(x, lo, hi, order=2):
    sos = butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return sosfilt(sos, x)


def lp(x, hi, order=2):
    return sosfilt(butter(order, hi, btype="low", fs=SR, output="sos"), x)


def hp(x, lo, order=2):
    return sosfilt(butter(order, lo, btype="high", fs=SR, output="sos"), x)


def noise(sec):
    return RNG.standard_normal(int(sec * SR)).astype(np.float32)


def env_ad(n, a, d_curve=4.0):
    t = np.linspace(0, 1, n)
    a_n = max(1, int(a * SR))
    e = np.exp(-d_curve * t)
    e[:a_n] *= np.linspace(0, 1, a_n)
    return e


def tvec(sec):
    return np.arange(int(sec * SR)) / SR


def add(buf, sig, at, gain=1.0):
    i = int(at * SR)
    if i >= len(buf) or i + len(sig) <= 0:
        return
    if i < 0:
        sig, i = sig[-i:], 0
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i] * gain


def reverb(x, taps=((0.031, 0.35), (0.053, 0.28), (0.079, 0.22), (0.113, 0.16), (0.167, 0.1))):
    y = x.copy()
    for d, g in taps:
        k = int(d * SR)
        y[k:] += x[:-k] * g
    return y


# ----------------------------------------------------------------- sfx library
def sfx_wind(sec):
    t = tvec(sec)
    n = bp(noise(sec), 180, 900)
    return n * (0.5 + 0.5 * np.sin(2 * np.pi * 0.13 * t) ** 2) * 0.10


def sfx_rain(sec):
    return hp(noise(sec), 3000) * 0.045


def sfx_clock(sec):
    out = np.zeros(int(sec * SR), np.float32)
    for k in range(int(sec) + 1):
        click = bp(noise(0.03), 2500 if k % 2 else 1800, 6000) * env_ad(int(0.03 * SR), 0.001, 12)
        add(out, click, k * 1.0 + 0.2, 0.35)
    return out


def sfx_teacup(sec=0.9):
    t = tvec(sec)
    s = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((2350, 1), (3720, 0.6), (5110, 0.35)))
    return s * np.exp(-t * 9) * 0.18


def sfx_whoosh(sec=0.6):
    n = bp(noise(sec), 400, 3000)
    t = np.linspace(0, 1, len(n))
    return n * np.sin(np.pi * t) ** 2 * 0.25


def sfx_sparkle(sec=1.2):
    out = np.zeros(int(sec * SR), np.float32)
    for i, f in enumerate((2637, 3136, 3951, 4699, 5274)):
        t = tvec(0.6)
        add(out, np.sin(2 * np.pi * f * t) * np.exp(-t * 8) * 0.07, i * 0.07)
    return out


def sfx_sting(sec=3.0):
    t = tvec(sec)
    boom = np.sin(2 * np.pi * (55 * t - 8 * t ** 2)) * np.exp(-t * 1.6) * 0.9
    boom += np.sin(2 * np.pi * 110 * t) * np.exp(-t * 3) * 0.3
    hit = lp(noise(sec), 1200) * np.exp(-t * 6) * 0.5
    return (boom + hit) * 0.7


def sfx_riser(sec=0.8):
    n = hp(noise(sec), 2000)
    return n * np.linspace(0, 1, len(n)) ** 3 * 0.25


def sfx_drip(sec):
    out = np.zeros(int(sec * SR), np.float32)
    k = 0.6
    while k < sec:
        t = tvec(0.15)
        d = np.sin(2 * np.pi * (1400 - 2500 * t) * t) * np.exp(-t * 30) * 0.12
        add(out, reverb(np.pad(d, (0, 9000))), k)
        k += 1.7 + RNG.random() * 1.6
    return out


def sfx_brick(sec):
    out = np.zeros(int(sec * SR), np.float32)
    for k in np.arange(0.4, sec - 0.4, 1.1):
        scrape = bp(noise(0.35), 300, 2200) * env_ad(int(0.35 * SR), 0.05, 5) * 0.25
        thud = np.sin(2 * np.pi * 80 * tvec(0.25)) * np.exp(-tvec(0.25) * 18) * 0.4
        add(out, scrape, k)
        add(out, thud, k + 0.3)
    return out


def sfx_waves(sec):
    t = tvec(sec)
    n = lp(noise(sec), 500)
    return n * (0.45 + 0.55 * np.sin(2 * np.pi * 0.11 * t) ** 2) * 0.22


def sfx_horn(sec=2.6):
    t = tvec(sec)
    s = sum(((t * f) % 1 * 2 - 1) * a for f, a in ((98, 1), (147, 0.7), (196, 0.3)))
    s = lp(s, 700)
    e = np.minimum(1, t / 0.25) * np.minimum(1, (sec - t) / 0.8)
    return reverb(s * e) * 0.16


def sfx_steps(sec):
    out = np.zeros(int(sec * SR), np.float32)
    for k in np.arange(0.2, sec * 0.85, 0.52):
        th = lp(noise(0.12), 600) * np.exp(-tvec(0.12) * 35)
        add(out, th, k, 0.6)
    return out


def sfx_bell(sec=5.0):
    t = tvec(sec)
    s = sum(np.sin(2 * np.pi * f * t) * a * np.exp(-t * d)
            for f, a, d in ((220, 1, 0.6), (440 * 1.19, 0.5, 0.9), (220 * 2.76, 0.35, 1.3), (220 * 5.4, 0.2, 2)))
    return reverb(s) * 0.22


def sfx_hum(sec):
    t = tvec(sec)
    return (np.sin(2 * np.pi * 60 * t) * 0.5 + np.sin(2 * np.pi * 120 * t) * 0.25) * 0.03


MORSE = {"A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.", "G": "--.", "H": "....",
         "I": "..", "J": ".---", "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---", "P": ".--.",
         "Q": "--.-", "R": ".-.", "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-",
         "Y": "-.--", "Z": "--..", " ": " "}


def morse_intervals(text, start, end, unit=0.075):
    out, t = [], start
    while t < end:
        for ch in text:
            if ch == " ":
                t += unit * 4
                continue
            for sym in MORSE.get(ch, ""):
                d = unit if sym == "." else unit * 3
                if t + d > end:
                    return out
                out.append([round(t, 3), round(t + d, 3)])
                t += d + unit
            t += unit * 2
        t += unit * 6
    return out


def sfx_morse(intervals, total):
    out = np.zeros(int(total * SR), np.float32)
    for s, e in intervals:
        t = tvec(e - s)
        beep = np.sin(2 * np.pi * 760 * t) * 0.16
        crack = hp(noise(e - s), 4000) * 0.06
        fade = np.minimum(1, np.minimum(t, (e - s) - t) / 0.004)
        add(out, (beep + crack) * fade, s)
    return out


ONE_SHOTS = {"teacup": sfx_teacup, "whoosh": sfx_whoosh, "sparkle": sfx_sparkle, "sting": sfx_sting,
             "horn": sfx_horn, "bell": sfx_bell}
BEDS = {"wind": sfx_wind, "rain": sfx_rain, "clock": sfx_clock, "drip": sfx_drip, "brick": sfx_brick,
        "waves": sfx_waves, "steps": sfx_steps, "hum": sfx_hum}


# ----------------------------------------------------------------- music
def note(n):  # midi -> hz
    return 440 * 2 ** ((n - 69) / 12)


def music_track(total, shots):
    """Dark music-box + pad score in D minor. Mood per shot: calm / tense / drop / end."""
    n = int(total * SR)
    pad = np.zeros(n, np.float32)
    box = np.zeros(n, np.float32)
    sub = np.zeros(n, np.float32)
    pulse = np.zeros(n, np.float32)
    chords = [(50, 53, 57), (46, 50, 53), (43, 46, 50), (45, 49, 52)]  # Dm Bb Gm A
    bar = 3.2
    t_all = np.arange(n) / SR
    # pad
    for ci in range(int(total / bar) + 1):
        ch = chords[ci % 4]
        t0 = ci * bar
        seg = tvec(bar + 1.0)
        s = np.zeros_like(seg)
        for m in ch:
            for det in (-0.12, 0.0, 0.12):
                f = note(m + det)
                s += ((seg * f) % 1 * 2 - 1)
        s = lp(s, 700) / 9
        e = np.minimum(1, seg / 0.8) * np.minimum(1, (bar + 1.0 - seg) / 1.0)
        add(pad, s * e, t0)
        # sub drone
        add(sub, np.sin(2 * np.pi * note(ch[0] - 24) * seg) * e * 0.5, t0)
        # music box arpeggio
        arp = [ch[0] + 24, ch[1] + 24, ch[2] + 24, ch[1] + 24, ch[0] + 36, ch[2] + 24, ch[1] + 24, ch[2] + 12]
        for k, m in enumerate(arp):
            tt = tvec(1.6)
            f = note(m)
            tone = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt) + 0.12 * np.sin(2 * np.pi * 3.01 * f * tt))
            add(box, tone * np.exp(-tt * 3.5) * 0.11, t0 + k * bar / 8)
    box = box + np.concatenate([np.zeros(int(0.3 * SR)), box[:-int(0.3 * SR)]]) * 0.35
    # heartbeat pulse
    for k in np.arange(0, total, 0.86):
        th = np.sin(2 * np.pi * 50 * tvec(0.18)) * np.exp(-tvec(0.18) * 22)
        add(pulse, th, k)
        add(pulse, th * 0.6, k + 0.22)

    # mood automation
    g_pad, g_box, g_pulse = (np.zeros(n, np.float32) for _ in range(3))
    for s in shots:
        a, b = int(s["start"] * SR), int(s["end"] * SR)
        mood = s.get("music", "calm")
        gp, gb, gu = {"calm": (0.55, 0.9, 0.0), "tense": (0.7, 0.35, 0.9), "drop": (0.25, 0.0, 0.0),
                      "end": (0.6, 0.7, 0.0)}[mood]
        g_pad[a:b], g_box[a:b], g_pulse[a:b] = gp, gb, gu
    k = int(0.25 * SR)
    smooth = lambda g: np.convolve(g, np.ones(k) / k, mode="same")
    mix = pad * smooth(g_pad) * 0.5 + box * smooth(g_box) + sub * smooth(g_pad) * 0.35 + pulse * smooth(g_pulse) * 0.5
    # fade in / out
    mix *= np.minimum(1, t_all / 1.5) * np.minimum(1, (total - t_all) / 2.0)
    return mix


# ----------------------------------------------------------------- captions
def chunk_words(text, maxlen=17):
    words = text.split()
    chunks, cur = [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        if len(cand) > maxlen and cur:
            chunks.append(cur)
            cur = w
        else:
            cur = cand
        if re.search(r"[.!?]$|\.\.\.$", w) and len(cur) > 6:
            chunks.append(cur)
            cur = ""
    if cur:
        chunks.append(cur)
    return chunks


def envelope(audio):
    hop = SR // FPS
    frames = int(math.ceil(len(audio) / hop))
    rms = np.array([np.sqrt(np.mean(audio[i * hop:(i + 1) * hop] ** 2) + 1e-9) for i in range(frames)])
    ref = np.percentile(rms, 92) + 1e-6
    e = np.clip(rms / ref, 0, 1)
    e = np.where(e < 0.12, 0, e)
    return [round(float(v), 2) for v in e]


# ----------------------------------------------------------------- main
def main():
    story_path = sys.argv[1]
    story = json.load(open(story_path))
    name = os.path.splitext(os.path.basename(story_path))[0]
    out_dir = os.path.join(ROOT, "build", name)
    cache = os.path.join(ROOT, "build", "tts_cache")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(cache, exist_ok=True)

    cursor = 0.0
    tl_shots, tl_lines, voice_clips = [], [], []
    for si, shot in enumerate(story["shots"]):
        start = cursor
        t = start
        line_starts = []
        for li, line in enumerate(shot.get("lines", [])):
            voice = story["voices"][line["who"]]
            audio = tts(line.get("say", line["text"]), voice, cache)
            t += line.get("pre", 0.25 if li == 0 else 0.18)
            dur = len(audio) / SR
            words = line["text"].split()
            chunks = chunk_words(line["text"]) if not line.get("big") else [line["text"]]
            weights = [len(c) + 3 for c in chunks]
            acc, ch_out = t, []
            for c, wgt in zip(chunks, weights):
                d = dur * wgt / sum(weights)
                ch_out.append({"text": c.upper(), "start": round(acc, 3), "end": round(acc + d, 3)})
                acc += d
            tl_lines.append({"shot": si, "who": line["who"], "text": line["text"], "start": round(t, 3),
                             "dur": round(dur, 3), "env": envelope(audio), "chunks": ch_out,
                             "big": bool(line.get("big"))})
            voice_clips.append((t, audio, line["who"]))
            line_starts.append(t)
            t += dur
        end = max(t + shot.get("post", 0.4), start + shot.get("dur", 0))
        rec = {k: v for k, v in shot.items() if k not in ("lines",)}
        rec.update({"index": si, "start": round(start, 3), "end": round(end, 3), "lineStarts": line_starts})
        if shot.get("telegram"):
            rec["morse"] = morse_intervals("CQD CRIPPEN ABOARD MONTROSE", start + 0.3, end - 0.1)
        tl_shots.append(rec)
        cursor = end

    total = cursor
    print(f"total duration: {total:.2f}s, shots: {len(tl_shots)}, lines: {len(tl_lines)}")

    # ---------------- mix
    n = int(total * SR) + SR
    vo = np.zeros(n, np.float32)
    for t, audio, who in voice_clips:
        a = audio / (np.max(np.abs(audio)) + 1e-6) * 0.9
        if who != "narrator":
            a = reverb(a, ((0.019, 0.18), (0.037, 0.12), (0.061, 0.08)))
        add(vo, a, t)

    sfx = np.zeros(n, np.float32)
    for s in tl_shots:
        length = s["end"] - s["start"]
        for item in s.get("sfx", []):
            if isinstance(item, str):
                if item == "morse":
                    add(sfx, sfx_morse([[a - s["start"], b - s["start"]] for a, b in s["morse"]], length), s["start"])
                else:
                    bed = BEDS[item](length + 0.6)
                    fade = np.minimum(1, np.minimum(tvec(length + 0.6) / 0.15, (length + 0.6 - tvec(length + 0.6)) / 0.5))
                    add(sfx, bed * fade, s["start"])
            else:
                at = s["start"] + item.get("at", 0)
                if "atLine" in item:
                    at = s["lineStarts"][item["atLine"]]
                if item["name"] == "sting":
                    add(sfx, sfx_riser(), at - 0.8, item.get("gain", 1.0))
                add(sfx, ONE_SHOTS[item["name"]](), at, item.get("gain", 1.0))

    music = np.zeros(n, np.float32)
    music[: int(total * SR)] = music_track(total, tl_shots)[: int(total * SR)]
    # duck music under voice
    k = int(0.3 * SR)
    duck = np.convolve((np.abs(vo) > 0.02).astype(np.float32), np.ones(k) / k, mode="same")
    music *= 1 - 0.55 * np.clip(duck * 3, 0, 1)

    mono_bed = music * 0.55 + sfx
    # simple stereo: widen music with a tiny delay, voice centered
    d = int(0.012 * SR)
    left = mono_bed + vo
    right = np.concatenate([np.zeros(d), mono_bed[:-d]]) + vo
    st = np.stack([left, right], axis=1)
    st = st / (np.max(np.abs(st)) + 1e-6) * 0.92
    st = st[: int(total * SR)]
    write_wav(os.path.join(out_dir, "audio.wav"), st)

    timeline = {"fps": FPS, "duration": round(total, 3), "title": story.get("title"), "handle": story.get("handle"),
                "hook": story.get("hook"), "endcard": story.get("endcard"), "cast": story["cast"],
                "shots": tl_shots, "lines": tl_lines}
    json.dump(timeline, open(os.path.join(out_dir, "timeline.json"), "w"))
    print("wrote", out_dir)


if __name__ == "__main__":
    main()
