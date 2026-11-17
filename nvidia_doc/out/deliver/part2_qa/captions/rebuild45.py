import json, sys
words, capfile, out = sys.argv[1:4]
parts = json.load(open(words)); stream = [(p, w) for p, P in enumerate(parts) for w in P]
lines = [l.strip() for l in open(capfile, encoding='utf-8') if l.strip()]
caps = []; pos = 0
for l in lines:
    rows = [r.strip() for r in l.split('|')]
    toks = ' '.join(rows).split()
    seg = stream[pos:pos + len(toks)]
    assert [w[0] for _, w in seg] == toks, (l, [w[0] for _, w in seg])
    assert len({p for p, _ in seg}) == 1, ('caption spans two parts', l)
    assert all(len(r) <= 58 for r in rows) and len(rows) == 1, ('too long', l)
    caps.append({'start': seg[0][1][1], 'wend': seg[-1][1][2], 'lines': rows, 'part': seg[0][0], 'fw': seg[0][1]}); pos += len(toks)
assert pos == len(stream), 'not all script words used'
if len(sys.argv) > 4:                     # snap starts to real voice onsets after a pause
    import wave, numpy as np
    w = wave.open(sys.argv[4]); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2)[:, 0].astype(np.float32) / 32768
    db = 20 * np.log10(np.sqrt(np.convolve(a ** 2, np.ones(480) / 480, 'same')[::48]) + 1e-9)   # 1 ms steps
    snapped = 0
    def onset(t):
        i = int(t * 1000); best = None
        for on in range(i - 450, i + 300):
            if db[on] > -40 and db[on - 80:on].max() <= -40 and db[on:on + 120].max() > -30 and (best is None or abs(on - i) < abs(best - i)): best = on
        return best
    for k, c in enumerate(caps):
        on = onset(c['start'])
        lo = caps[k-1]['wend'] if k else 0
        if on is not None and on / 1000 - 0.05 > lo + 0.05: c['start'] = on / 1000 - 0.05; snapped += 1
        else:                                  # aligner stretched the first word over a pause: find the real onset inside it
            fw = c['fw']; dur = fw[2] - fw[1]; i = int(c['start'] * 1000)
            if dur > 0.15 + 0.07 * len(fw[0]):
                for o in range(i + 60, int((fw[2] - 0.08) * 1000)):
                    if db[o] > -45 and db[o - 100:o].max() <= -45 and db[o:o + 120].max() > -35:
                        c['start'] = o / 1000 - 0.05; snapped += 1; break
    print('snapped', snapped, 'caption starts to voice onsets')
for k, c in enumerate(caps):
    nxt = caps[k+1]['start'] if k + 1 < len(caps) else 1e9
    end = c['wend'] + 0.3
    if nxt - end < 0.6: end = nxt - 0.05
    end = min(end, nxt - 0.05, c['start'] + 5.0)
    if end - c['start'] < 1.0: end = min(c['start'] + 1.0, nxt - 0.05)
    c['end'] = end
def ts(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
with open(out, 'w', encoding='utf-8', newline='\n') as f:
    for k, c in enumerate(caps, 1): f.write(f"{k}\n{ts(c['start'])} --> {ts(c['end'])}\n" + '\n'.join(c['lines']) + '\n\n')
json.dump(caps, open(out + '.json', 'w'))
D = [c['end'] - c['start'] for c in caps]; W = [c['wend'] - c['start'] for c in caps]
print(len(caps), 'captions; display', round(min(D), 2), '-', round(max(D), 2), 's; speech span >6s:', [(k+1, round(w, 2)) for k, w in enumerate(W) if w > 6.0])
print('short <1s:', [(k+1, round(d, 2)) for k, d in enumerate(D) if d < 1.0])
print('overlaps:', [k+1 for k in range(len(caps)-1) if caps[k]['end'] > caps[k+1]['start']])
print('gaps >2s:', [(k+1, round(caps[k+1]['start'] - caps[k]['end'], 2), 'chapter break' if caps[k]['part'] != caps[k+1]['part'] else 'IN SPEECH') for k in range(len(caps)-1) if caps[k+1]['start'] - caps[k]['end'] > 2.0])
