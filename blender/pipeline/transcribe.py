"""Word timestamps for a voiceover (faster-whisper small.en, CPU).
/opt/venv/whisper/bin/python -I transcribe.py vo.mp3   -> vo.words.json  [[start, end, word], ...]"""
import sys, json, os, subprocess
import numpy as np
from faster_whisper import WhisperModel
m = WhisperModel("small.en", device="cpu", compute_type="int8")
for path in sys.argv[1:]:
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"])
    segs, _ = m.transcribe(np.frombuffer(raw, np.float32), word_timestamps=True)
    words = [(round(w.start, 2), round(w.end, 2), w.word.strip()) for s in segs for w in s.words]
    out = os.path.splitext(path)[0] + ".words.json"
    json.dump(words, open(out, "w"))
    print(out, len(words), "words, speech %.2f-%.2f s" % (words[0][0], words[-1][1]) if words else "")
