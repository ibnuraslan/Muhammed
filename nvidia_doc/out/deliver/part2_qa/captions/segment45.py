import json, sys, re
src, out = sys.argv[1], sys.argv[2]
parts = json.load(open(src))
MAXL, MAXD, MIND = 50, 4.5, 1.0
WEAK = {'and','but','or','that','which','who','where','when','because','to','in','on','at','for','from','with','about','into','as','if','while','after','before','between','across'}
ABBR = {'U.S.', 'H.'}
MONTHS = ('January','February','March','April','May','June','July','August','September','October','November','December')
def glued(w, nxt):
    if not nxt: return False
    if w in ABBR: return True
    if w[0].isupper() and nxt[0].isupper() and not re.search(r'[,;:.!?”]$', w): return True     # names
    if nxt.strip('.,') in ('billion', 'million', 'dollar', 'dollars'): return True
    if re.match(r'\d{4}', nxt) and re.search(r'(first|second|third|th),$', w): return True        # “May twenty-second, 2025”
    if w in MONTHS: return True
    if (w.lower(), nxt.lower().strip('.,')) in {('and','a'),('a','half'),('closed','doors'),('data','center'),('export','controls'),('kinds','of'),('can','also'),('tell','you')}: return True
    if nxt.lower().strip('.,') in ('you','him','them'): return True
    NUM = {'one','two','three','four','five','six','seven','eight','nine','ten','thirty-three','and','a','half'}
    if w.lower() in NUM and nxt.lower().strip('.,') in NUM | {'billion','million'} and w.lower() not in ('and','a'): return True
    return False
GLUE = {'is','are','was','were','can','could','be','will','would','has','have','had','it','they','he','she','we','you','its','no','the','a','an','of','to','his','her','its','their','my','your','our','this','that','these','those','kinds','kind','same','who','which'}
def wrap(ws):
    t = ' '.join(ws)
    if len(t) <= MAXL: return (0, [t])
    return None
    best = None
    for k in range(1, len(ws)):
        a, b = ' '.join(ws[:k]), ' '.join(ws[k:])
        if len(a) > MAXL or len(b) > MAXL: continue
        lone = 30 if k >= 2 and re.search(r'[.!?]["”’]?$', ws[k-2]) and ws[k-2] not in ABBR else 0
        c = lone + abs(len(a) - len(b)) + (60 if glued(ws[k-1], ws[k]) else 0) + (0 if re.search(r'[,;:.!?”]$', ws[k-1]) else 30 if ws[k-1].lower() in GLUE else 12 if ws[k].lower() in ('of','to') else 8 if ws[k].lower().strip('“') in WEAK else 16)
        if best is None or c < best[0]: best = (c, [a, b])
    return best
def bq(w, nxt):
    if glued(w, nxt): return 60
    if re.search(r'[.!?]["”’]?$', w): return 0
    if re.search(r'[,;:]$', w): return 3
    if w.lower() in GLUE or (nxt and nxt.lower() in ('of', 'to')): return 45
    if nxt and nxt.lower() in WEAK: return 9
    if nxt and nxt.lower() in ('the', 'a', 'an'): return 38
    return 28
caps = []
for P in parts:
    n = len(P); INF = 1e9
    best = [INF] * (n + 1); prev = [-1] * (n + 1); best[0] = 0
    for j in range(1, n + 1):
        for i in range(max(0, j - 18), j):
            if best[i] >= INF: continue
            ws = [x[0] for x in P[i:j]]
            wr = wrap(ws)
            if wr is None: continue
            d = P[j-1][2] - P[i][1]
            if d > MAXD: continue
            gaps = [P[k+1][1] - P[k][2] for k in range(i, j-1)]
            c = 4 + 0.5 * wr[0] + bq(P[j-1][0], P[j][0] if j < n else None) * (0 if j == n else 1)
            if d < 1.2: c += 30
            c += max(0, 22 - len(' '.join(ws))) * 0.8   # avoid very short one-liners
            if gaps and max(gaps) > 0.9: c += 25                       # don't straddle a long pause
            # sentence end inside a caption (not at end) is ok only if short tail; mild penalty
            c += sum(6 for k in range(i, j-1) if re.search(r'[.!?]["”’]?$', P[k][0]) and P[k][0] not in ABBR)
            if best[i] + c < best[j]: best[j] = best[i] + c; prev[j] = i
    cuts = []; j = n
    while j > 0: cuts.append((prev[j], j)); j = prev[j]
    for i, j in reversed(cuts):
        caps.append({'start': P[i][1], 'wend': P[j-1][2], 'lines': wrap([x[0] for x in P[i:j]])[1]})
# display timing
for k, c in enumerate(caps):
    nxt = caps[k+1]['start'] if k + 1 < len(caps) else 1e9
    end = c['wend'] + 0.3
    if nxt - end < 0.6: end = nxt - 0.05                              # chain through short pauses
    end = min(end, nxt - 0.05, c['start'] + MAXD)
    if end - c['start'] < MIND: end = min(c['start'] + MIND, nxt - 0.05)
    c['end'] = end
def ts(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
with open(out, 'w', encoding='utf-8', newline='\n') as f:
    for k, c in enumerate(caps, 1):
        f.write(f"{k}\n{ts(c['start'])} --> {ts(c['end'])}\n" + '\n'.join(c['lines']) + '\n\n')
json.dump(caps, open(out + '.json', 'w'))
# QA
L = [len(l) for c in caps for l in c['lines']]; D = [c['end'] - c['start'] for c in caps]
ov = [k for k in range(len(caps) - 1) if caps[k]['end'] > caps[k+1]['start']]
gaps = [(k+1, round(caps[k+1]['start'] - caps[k]['end'], 2)) for k in range(len(caps) - 1) if caps[k+1]['start'] - caps[k]['end'] > 2.0]
print(f'{len(caps)} captions; max line {max(L)}; max lines {max(len(c["lines"]) for c in caps)}; dur {min(D):.2f}-{max(D):.2f}s; <1s: {[k+1 for k,d in enumerate(D) if d < 1.0]}; overlaps {ov}')
print('gaps >2s (caption index, s):', gaps)
