import json, numpy as np, soundfile as sf, sys
sys.path.insert(0, '')
from kokoro_onnx import Kokoro
K = Kokoro('../kokoro/model.onnx', '../kokoro/voices.npz')
VOICE, SPEED = 'bm_george', 0.92
# (id, text, gap_after_seconds)
CLIPS = [
 ("a1", "In twelve oh-six, in a palace on the banks of the river Tigris,", .2),
 ("a2", "an engineer finished a book... that would outlive empires.", .7),
 ("b1", "His name was Ismaeel Al-Jazari.", .35),
 ("b2", "For twenty-five years, he served the Artuqid kings, building machines the world had never seen.", .6),
 ("c1", "His book had a long name. The Book of Knowledge of Ingenious Mechanical Devices.", .35),
 ("c2", "Inside were fifty machines, each one drawn and explained, so that others could build them too.", .6),
 ("d1", "There was a clock... shaped like an elephant.", .3),
 ("d2", "Every half hour, a bird would sing, a ball would drop into a dragon's mouth,", .1),
 ("d3", "and the driver on its neck would beat his drum.", .6),
 ("e1", "There was a boat of mechanical musicians, that floated on a lake at royal parties.", .3),
 ("e2", "Change the pegs inside its drum, and the band played a different rhythm.", .35),
 ("e3", "A programmable machine... eight hundred years ago.", .7),
 ("f1", "There was a peacock, for washing hands.", .25),
 ("f2", "Water poured from its beak, and a little servant appeared, holding soap... then a towel.", .6),
 ("g1", "And beyond the wonders, he built pumps that lifted water, using cranks and pistons,", .1),
 ("g2", "ideas that still move machines today.", .8),
 ("h1", "But empires fell. Libraries burned.", .4),
 ("h2", "And for centuries, his name was almost forgotten.", .8),
 ("i1", "Today, his pages sit in museums around the world.", .3),
 ("i2", "Engineers have rebuilt his machines... and they still work.", .7),
 ("j1", "Some now call him...", .5),
 ("j2", "the father of robotics.", 3.0),
]
LEAD, SR = .8, 24000
out = [np.zeros(int(LEAD * SR), np.float32)]; t = LEAD; cues = {}
for cid, text, gap in CLIPS:
    a, sr = K.create(text, voice=VOICE, speed=SPEED, lang='en-gb'); assert sr == SR
    idx = np.where(np.abs(a) > .01)[0]; a = a[max(0, idx[0] - 240):idx[-1] + 1200]
    d = len(a) / SR; cues[cid] = {"start": round(t, 3), "end": round(t + d, 3), "text": text}
    out += [a, np.zeros(int(gap * SR), np.float32)]; t += d + gap
sf.write('vo_full.wav', np.concatenate(out), SR)
json.dump({"duration": round(t, 3), "cues": cues}, open('timeline.json', 'w'), indent=1)
print('total', round(t, 2))
for k, c in cues.items(): print(k, c['start'], c['end'])
