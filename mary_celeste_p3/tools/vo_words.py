"""Word timestamps for the Part 3 voice-over (faster-whisper, CPU) -> vo/words.json [{w, s, e}]."""
import sys, json, os
from faster_whisper import WhisperModel
src = sys.argv[1]; out = sys.argv[2]
m = WhisperModel(os.environ.get("WHISPER", "small.en"), device="cpu", compute_type="int8")
import subprocess, numpy as np
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True, check=True).stdout
audio = np.frombuffer(pcm, np.float32)                  # decoded with ffmpeg (the installed PyAV is newer than faster-whisper expects)
segs, info = m.transcribe(audio, word_timestamps=True, language="en", beam_size=5, vad_filter=False)
words = [dict(w=w.word.strip(), s=round(w.start, 3), e=round(w.end, 3)) for s in segs for w in s.words]
json.dump(words, open(out, "w"), indent=0)
print(len(words), "words", words[-1]["e"] if words else 0)
