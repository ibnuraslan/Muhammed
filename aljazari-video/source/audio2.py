import json, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, resample_poly

SR = 44100
TL = json.load(open('../vo2/timeline.json'))
CU = TL['cues']; cs = lambda k: CU[k]['start']; ce = lambda k: CU[k]['end']
DUR = TL['duration'] + 0.2
N = int(DUR * SR) + SR
rng = np.random.default_rng(11)
music = np.zeros((N, 2)); sfx = np.zeros((N, 2))

def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)
def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def add(buf, x, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or i + len(x) <= 0: return
    if i < 0: x = x[-i:]; i = 0
    x = x[:N - i]; l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i:i + len(x), 0] += x * g * l * 1.414; buf[i:i + len(x), 1] += x * g * r * 1.414
def env(n, a, d): t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)
def mf(m): return 440 * 2 ** ((m - 69) / 12)
def noise(n): return rng.standard_normal(n)

# ---------- instruments ----------
def oud(m, dur=1.0):
    n = int(dur * SR); t = np.arange(n) / SR; f = mf(m) * (1 + .012 * np.exp(-t * 40))  # tiny slide into note
    ph = 2 * np.pi * np.cumsum(f) / SR; y = np.zeros(n)
    for k in range(1, 11): y += np.sin(ph * k + k * .7) * np.exp(-t * (3.2 + k * 1.9)) / k ** .9
    y += bp(noise(n), 1500, 5000) * np.exp(-t * 80) * .25  # pick noise
    return y * np.minimum(1, t / .002) * .45
def ney(m, dur):
    n = int(dur * SR); t = np.arange(n) / SR; f = mf(m) * (1 + .006 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(1, t / .6))
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) + .25 * np.sin(2 * ph) + .1 * np.sin(3 * ph) + lp(noise(n), 2500) * .12
    e = np.minimum(1, t / .35) * np.minimum(1, (dur - t) / .4).clip(0, 1)
    return y * e * .3
def drone(dur, root=38):
    n = int(dur * SR); t = np.arange(n) / SR; y = np.zeros(n)
    for m, a in [(root, 1), (root + 7, .6), (root + 12, .4)]:
        for det in (-.04, .04): y += a * np.sin(2 * np.pi * mf(m + det) * t + rng.random() * 6) * (1 + .15 * np.sin(2 * np.pi * .23 * t + m))
    return lp(y, 900) * .12
def dum(g=1.0):
    n = int(.6 * SR); t = np.arange(n) / SR; f = 70 + 60 * np.exp(-t * 25)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6) + lp(noise(n), 300) * np.exp(-t * 30) * .3) * g
def tak(g=1.0):
    n = int(.15 * SR); t = np.arange(n) / SR
    return (bp(noise(n), 2000, 7000) * np.exp(-t * 60) + np.sin(2 * np.pi * 700 * t) * np.exp(-t * 50) * .4) * g
def gong(dur=6):
    n = int(dur * SR); t = np.arange(n) / SR; y = np.zeros(n)
    for f, a, d in [(110, 1, 3.5), (171, .7, 3), (236, .5, 2.6), (318, .4, 2), (421, .3, 1.6), (557, .2, 1.2)]:
        y += a * np.sin(2 * np.pi * f * t * (1 + .002 * np.sin(2 * np.pi * 3 * t))) * np.exp(-t / d)
    y += bp(noise(n), 300, 3000) * np.exp(-t * 6) * .3
    return y * np.minimum(1, t / .01) * .4
def chime(m, dur=2.5):
    n = int(dur * SR); t = np.arange(n) / SR; f = mf(m)
    return (np.sin(2 * np.pi * f * t) + .4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 3) + .2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 6)) * np.exp(-t * 1.4) * .3

# ---------- music ----------
HIJAZ = [50, 51, 54, 55, 57, 58, 60, 62, 63, 66, 67, 69]  # D Eb F# G A Bb C D ...
BPM = 84; beat = 60 / BPM; bar = beat * 4
t_book = cs('c1') - .2; t_burn = cs('h1') - .3; t_museum = cs('i1') - .3; t_title = cs('j1') - .3
MOTIFS = [[0, 1, 2, 3, 2, 1, 0, -1], [3, 4, 5, 4, 3, 2, 1, 0], [0, 2, 3, 4, 3, 2, 1, 2], [4, 5, 7, 5, 4, 3, 2, 1], [7, 6, 5, 4, 3, 2, 1, 0]]
add(music, drone(t_burn + 1.5), .2, 1.0)
t = 1.2; bi = 0
while t < t_burn - .2:
    dense = t >= t_book; mot = MOTIFS[bi % len(MOTIFS)]
    for k, deg in enumerate(mot):
        if not dense and k % 2: continue
        tt = t + k * beat / 2
        if tt > t_burn - .3: break
        m = HIJAZ[deg] if deg >= 0 else 49
        add(music, oud(m + 12 * (bi % 4 == 3), 1.1), tt, .32 if k % 4 == 0 else .22, pan=(-.3 if k % 2 else .3))
    if dense:  # maqsum: D T . T D . T .
        for k, (kind, g) in enumerate([('d', 1), ('t', .8), (None, 0), ('t', .6), ('d', .9), (None, 0), ('t', .8), ('t', .4)]):
            tt = t + k * beat / 2
            if kind and tt < t_burn - .3: add(music, dum(g) if kind == 'd' else tak(g), tt, .45 if kind == 'd' else .3, pan=.15)
    t += bar; bi += 1
# burning: dark drone + ney lament
add(music, drone(t_museum - t_burn + 1.5, 26) * 1.4, t_burn, 1.0)
for k, (m, d) in enumerate([(62, 1.6), (63, 1.0), (62, 1.4), (58, 2.2)]):
    add(music, ney(m, d), t_burn + .4 + sum(x[1] for x in [(62, 1.6), (63, 1.0), (62, 1.4), (58, 2.2)][:k]), .55)
# museum: gentle oud rebuild
t = t_museum + .2
for k, deg in enumerate([0, 2, 3, 4, 5, 4, 3, 2, 3, 4, 5, 7, 5, 4, 3, 4]):
    tt = t + k * beat / 2
    if tt < t_title - .2: add(music, oud(HIJAZ[deg], 1.0), tt, .25, pan=(-.3 if k % 2 else .3))
add(music, drone(t_title - t_museum + .5), t_museum, .8)
# title: gong + full chord + ney
add(music, gong(), t_title + .1, .9)
add(music, drone(DUR - t_title, 38) * 1.6, t_title + .1, 1.0)
for k, m in enumerate([50, 57, 62, 66, 69]): add(music, oud(m, 3.0), t_title + .1 + k * .07, .3, pan=(k - 2) / 3)
add(music, ney(69, 2.2), cs('j2') + .1, .5); add(music, ney(66, 2.0), cs('j2') + 2.0, .4)
for k in range(4): add(music, dum(.9 - k * .15), t_title + .1 + k * beat * 2, .35)

# ---------- sfx ----------
def whoosh(dur=.5):
    n = int(dur * SR); tt = np.arange(n) / SR; x = noise(n); e = np.sin(np.pi * tt / dur) ** 2
    return (bp(x, 300, 1200) * (1 - tt / dur) + bp(x, 1500, 6000) * (tt / dur) * .7) * e
def thud(g=1.0):
    n = int(.35 * SR); return (lp(noise(n), 400) * env(n, .001, .05) * 1.5 + bp(noise(n), 800, 3000) * env(n, .001, .015) * .5) * g
def stampsfx(): return thud(1.5)
def flip():
    n = int(.25 * SR); tt = np.arange(n) / SR; return bp(noise(n), 800, 6000) * np.sin(np.pi * tt / .25) ** 3 * .6
def quill(dur):
    n = int(dur * SR); tt = np.arange(n) / SR; return bp(noise(n), 3000, 8000) * (.5 + .5 * np.abs(np.sin(tt * 2 * np.pi * 4.3))) * .06
def chirp():
    n = int(.12 * SR); tt = np.arange(n) / SR; f = 2600 + 1800 * np.sin(np.pi * tt / .12)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / .12) * .3
def ping(f=1800):
    n = int(.6 * SR); tt = np.arange(n) / SR; return (np.sin(2 * np.pi * f * tt) + .5 * np.sin(2 * np.pi * f * 2.4 * tt)) * np.exp(-tt * 8) * .4
def waterbed(dur, g=1.0):
    n = int(dur * SR); tt = np.arange(n) / SR
    return bp(noise(n), 300, 2500) * (.6 + .4 * np.sin(2 * np.pi * .5 * tt)) * np.minimum(1, tt / .5) * np.minimum(1, (dur - tt) / .5).clip(0, 1) * .12 * g
def stream(dur):
    n = int(dur * SR); tt = np.arange(n) / SR; return bp(noise(n), 1200, 6000) * np.minimum(1, tt / .3) * np.minimum(1, (dur - tt) / .3).clip(0, 1) * .14
def ticks(dur, rate, g=.3, f=(2500, 7000)):
    out = np.zeros(int(dur * SR)); m = int(.015 * SR); k = 0
    while k / rate < dur - .02:
        i = int(k / rate * SR); out[i:i + m] += bp(noise(m), *f) * env(m, .0003, .003) * (.7 + .3 * rng.random()); k += 1
    return out * g
def crackle(dur):
    n = int(dur * SR); tt = np.arange(n) / SR; y = np.zeros(n); idx = rng.integers(0, n, int(dur * 60)); y[idx] = rng.standard_normal(len(idx))
    y = bp(y, 800, 6000) * 2 + lp(noise(n), 250) * .25
    return y * np.minimum(1, tt / .6) * np.minimum(1, (dur - tt) / .8).clip(0, 1) * .25
def creak():
    n = int(.6 * SR); tt = np.arange(n) / SR; f = 90 + 40 * np.sin(np.pi * tt / .6)
    saw = (np.cumsum(f) / SR) % 1 - .5; return bp(saw * (.5 + .5 * np.abs(np.sin(tt * 60))), 200, 2000) * np.sin(np.pi * tt / .6) * .5

starts = [cs('b1') - .25, cs('c1') - .2, cs('d1') - .2, cs('e1') - .2, cs('f1') - .2, cs('g1') - .2, cs('i1') - .3]
for s in starts: add(sfx, whoosh(), s - .25, .35, pan=rng.random() - .5)
for s in [cs('h1') - .3, cs('j1') - .3]: add(sfx, whoosh(.6), s - .3, .45)
# 1 map
add(sfx, quill(3.4), .2, 1.0); add(sfx, thud(.8), cs('a1') + .3); add(sfx, thud(.5), cs('a1') + 2.6); add(sfx, thud(.5), cs('a2') + .2)
# 2 portrait
add(sfx, chime(74), cs('b1') + 1.6, .6); add(sfx, chime(81), cs('b1') + 1.75, .35, .3)
add(sfx, stampsfx(), cs('b2') + .4, .8); add(sfx, thud(.5), cs('b2') + 1.8)
# 3 book
add(sfx, quill(3.2), cs('c1') + 2.0, 1.2)
for k in range(7): add(sfx, flip(), cs('c2') + .2 + k * 2.6 / 7, .7, pan=.2)
add(sfx, ticks(2.4, 20, .2), cs('c2') + .1); add(sfx, thud(.5), cs('c2') + 2.6)
# 4 elephant clock
tb, tball, tdrum = cs('d2') + .9, cs('d2') + 2.9, cs('d3') + 1.5
for k in range(10): add(sfx, chirp(), tb + .05 + k * .22 + rng.random() * .05, .5, pan=.3)
add(sfx, ticks(.9, 14, .25, (1500, 5000)), tball); add(sfx, ping(1400), tball + .9, .7, -.3)
for k in range(4): add(sfx, dum(1.0), tdrum + .3 + k * .6, .5, .4)
add(sfx, ticks(4, 1, .2), cs('d1'))
# 5 boat
add(sfx, waterbed(cs('f1') - cs('e1') + .2), cs('e1') - .2, 1.0)
add(sfx, ticks(cs('f1') - cs('e2'), 3.6, .25, (1500, 5000)), cs('e2'))
add(sfx, stampsfx(), cs('e3') + .25, .9); add(sfx, thud(.5), cs('e3') + 1.7)
# 6 peacock
add(sfx, stream(cs('g1') - cs('f2') - .3), cs('f2') + .15, 1.0)
add(sfx, creak(), cs('f2') + 2.3, .6); add(sfx, thud(.5), cs('f2') + 2.7); add(sfx, thud(.5), cs('f2') + 4.6)
# 7 pump
pd = cs('h1') - cs('g1'); add(sfx, waterbed(pd, .8), cs('g1') - .2); add(sfx, ticks(pd, 2.4, .35, (600, 3000)), cs('g1'))
add(sfx, ticks(1.6, 6, .2, (1500, 6000)), cs('g2') - .2); add(sfx, thud(.5), cs('g2') + .3)
# 8 fire
add(sfx, lp(noise(int(1.2 * SR)), 600) * np.linspace(0, 1, int(1.2 * SR)) ** 2 * .4, cs('h1') + .3)
add(sfx, crackle(cs('i1') - cs('h1') - .8), cs('h1') + 1.2, 1.0)
add(sfx, thud(1.0), cs('h1') + .1); add(sfx, thud(.8), cs('h1') + 1.3)
# 9 museum
add(sfx, ticks(4, 2, .25), cs('i2') + 2.0); add(sfx, stampsfx(), cs('i2') + 2.45, .9)
for k in range(3): add(sfx, thud(.25), cs('i1') + .2 + k * .5)
# 10 title
add(sfx, chime(86, 3), cs('j2') + .05, .5); add(sfx, chime(81, 3), cs('j2') + .2, .35, -.3)
# crackle bed
cr = np.zeros(N); idx = rng.integers(0, N, int(DUR * 20)); cr[idx] = rng.standard_normal(len(idx)) * .4
cr = hp(cr, 1500); sfx[:, 0] += cr * .4; sfx[:, 1] += cr * .4

# ---------- VO + mix ----------
vo, vsr = sf.read('../vo2/vo_full.wav'); vo = resample_poly(vo, 147, 80); vo = hp(vo, 70)
vo = vo / (np.max(np.abs(vo)) + 1e-9) * .85
v = np.zeros(N); v[:min(N, len(vo))] = vo[:N]
envv = lp(np.abs(v), 6, 1); duck = 1 - .4 * np.clip(envv / .08, 0, 1)
music *= duck[:, None]
r = lambda x: 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
MG, SG = .3, .55
print('VO dB', round(r(v), 1), 'music dB', round(r(music * MG), 1), 'sfx dB', round(r(sfx * SG), 1))
mix = music * MG + sfx * SG + np.stack([v, v], 1)
end = int(DUR * SR); fade = int(.9 * SR)
mix[end - fade:end] *= np.linspace(1, 0, fade)[:, None]; mix = mix[:end]
mix = np.tanh(mix / np.max(np.abs(mix)) * 1.2) * .89
sf.write('mix.wav', mix, SR, subtype='PCM_16'); print('mix', round(len(mix) / SR, 2), 's')
