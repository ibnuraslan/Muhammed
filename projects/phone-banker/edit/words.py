"""Transcribe every VO part with word timestamps -> vo/words.json {part: {"words": [[token, start, end]], "dur": s}}."""
import os, sys, json, subprocess, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); VO = os.path.join(HERE, "..", "vo")
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "nvidia_doc", "edit"))
from align import norm_tokens, canon
from faster_whisper import WhisperModel
m = WhisperModel("small.en", device="cpu", compute_type="int8")
out = {}
for part in ("intro", "ch1", "ch2", "ch3"):
    mp3 = os.path.join(VO, f"{part}_vo.mp3"); wav = os.path.join("/tmp", f"pb_{part}.wav")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", mp3, "-ac", "1", "-ar", "16000", wav], check=True)
    with wave.open(wav) as w:
        audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
    segs, info = m.transcribe(audio, word_timestamps=True, vad_filter=True, beam_size=5)
    words = []
    for s in segs:
        for w in s.words:
            for tk in norm_tokens(w.word):
                words.append([canon(tk), round(w.start, 3), round(w.end, 3)])
    out[part] = dict(words=words, dur=round(len(audio) / 16000, 3))
    print(part, len(words), "words", out[part]["dur"], "s:", " ".join(x[0] for x in words[:14]), flush=True)
json.dump(out, open(os.path.join(VO, "words.json"), "w"), indent=0)
