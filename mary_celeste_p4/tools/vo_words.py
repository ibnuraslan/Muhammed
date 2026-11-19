"""Word timestamps of the voice-over with faster-whisper -> vo/words.json  [{w, s, e}, ...]"""
import sys, json, os
from faster_whisper import WhisperModel
src = sys.argv[1]; out = sys.argv[2]
m = WhisperModel(os.environ.get("WHISPER", "small.en"), device="cpu", compute_type="int8")
import subprocess, numpy as np
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True, check=True).stdout
audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0
segs, info = m.transcribe(audio, word_timestamps=True, beam_size=5, vad_filter=False)
words = [dict(w=w.word.strip(), s=round(w.start, 3), e=round(w.end, 3)) for s in segs for w in s.words]
json.dump(words, open(out, "w"), indent=0)
print(len(words), "words", words[-1]["e"] if words else 0)
