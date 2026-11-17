import json, re, difflib, wave, numpy as np, sys
R = '/home/user/Muhammed'
OUT = sys.argv[1]
txt = open(f'{R}/nvidia_doc/edit/script_ch4_ch5.md', encoding='utf-8').read()
sec = txt.split('## Fact-check notes')[0]
parts = re.split(r'^## .*$', sec, flags=re.M)[1:]
parts = [p.strip() for p in parts]
assert len(parts) == 2
W = json.load(open(f'{R}/nvidia_doc/vo/ch45_words.json'))
words = [W['4']['words'], W['5']['words']]
FPS = 24; place = {0: 73, 1: 4175}          # ch45 mix VO start frames (sound_ch45.py EDL: chapter start + 3.0 s LEAD)
# voice audio for offset refinement
w = wave.open(sys.argv[2]); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2)[:, 0].astype(np.float32) / 32768
SR = 48000; hop = 480; env = np.sqrt(np.convolve(a ** 2, np.ones(hop) / hop, 'same')[::hop])   # 10 ms rms
voiced = env > 0.02
def norm(t): return re.sub(r"[^a-z0-9]", "", t.lower().replace('’', "'"))
caps = []; report = []
for k in range(2):
    toks = re.findall(r'\S+', parts[k].replace('\n', ' '))
    sw = [norm(t) for t in toks]; aw = [norm(x[0]) for x in words[k]]
    sm = difflib.SequenceMatcher(None, sw, aw, autojunk=False)
    tim = [None] * len(toks)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal':
            for d in range(i2 - i1): tim[i1 + d] = tuple(words[k][j1 + d][1:])
        else:
            report.append(f'part {k}: script {toks[i1:i2]} <-> aligner {[x[0] for x in words[k][j1:j2]]}')
            if j2 > j1 and i2 > i1:              # spread the aligner span over the script span
                t0, t1 = words[k][j1][1], words[k][j2 - 1][2]
                for d in range(i2 - i1): tim[i1 + d] = (t0 + (t1 - t0) * d / (i2 - i1), t0 + (t1 - t0) * (d + 1) / (i2 - i1))
    for i in range(len(tim)):                     # fill gaps by interpolation
        if tim[i] is None:
            p = max([j for j in range(i) if tim[j]], default=None); n = min([j for j in range(i + 1, len(tim)) if tim[j]], default=None)
            tim[i] = (tim[p][1], tim[n][0]) if p is not None and n is not None else (tim[p][1], tim[p][1] + .3)
    # refine global offset: words-mask vs voiced energy, search +-0.6 s
    base = (place[k] - 1) / FPS
    L = int(max(t[1] for t in tim) * 100) + 100; mask = np.zeros(L, bool)
    for t0, t1 in tim: mask[int(t0 * 100):int(t1 * 100)] = True
    best = max(range(-60, 61), key=lambda o: np.sum(mask & voiced[int(base * 100) + o:int(base * 100) + o + L]))
    off = base + best / 100
    report.append(f'part {k}: EDL start {base:.3f}s, energy-refined offset {off:.3f}s ({best*10:+d} ms)')
    caps.append([(toks[i], tim[i][0] + off, tim[i][1] + off) for i in range(len(toks))])
json.dump(caps, open(OUT + '.words.json', 'w'))
print('\n'.join(report))
