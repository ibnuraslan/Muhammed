import json, wave, numpy as np
from scipy.signal import butter, sosfilt, resample_poly

SR = 44100
TL = json.load(open('../vo/timeline.json'))
CU = TL['cues']; cs = lambda k: CU[k]['start']; ce = lambda k: CU[k]['end']
DUR = TL['duration'] + 0.35
N = int(DUR * SR) + SR
rng = np.random.default_rng(7)
music = np.zeros((N, 2)); sfx = np.zeros((N, 2))

def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)
def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def add(buf, x, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or i + len(x) <= 0: return
    if i < 0: x = x[-i:]; i = 0
    x = x[:N - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i:i + len(x), 0] += x * g * l * 1.414; buf[i:i + len(x), 1] += x * g * r * 1.414
def env(n, a, d):  # attack + exp decay (seconds)
    t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)
def mf(m): return 440 * 2 ** ((m - 69) / 12)

# ---------------- instruments ----------------
def pluck(m, dur=1.2, bright=1.0):
    n = int(dur * SR); t = np.arange(n) / SR; f = mf(m); y = np.zeros(n)
    for k in range(1, 9):
        y += np.sin(2 * np.pi * f * k * t + k) * np.exp(-t * (2.5 + k * 1.6 / bright)) / k ** 1.1
    return y * np.minimum(1, t / .003) * .5
def piano(m, dur=2.5):
    n = int(dur * SR); t = np.arange(n) / SR; f = mf(m); y = np.zeros(n)
    for k, a in enumerate([1, .5, .3, .18, .1, .06], 1):
        y += a * np.sin(2 * np.pi * f * k * 1.0008 ** k * t) * np.exp(-t * (1.2 + k * .5))
    return y * np.minimum(1, t / .004) * .45
def pad(notes, dur, a=.8, r=1.0):
    n = int((dur + r) * SR); t = np.arange(n) / SR; y = np.zeros(n)
    for m in notes:
        for det in (-.07, .0, .07):
            f = mf(m) * 2 ** (det / 12)
            for k, amp in enumerate([1, .35, .15], 1): y += amp * np.sin(2 * np.pi * f * k * t + rng.random() * 6)
    e = np.minimum(1, t / a) * np.where(t > dur, np.exp(-(t - dur) / (r / 3)), 1)
    return lp(y * e, 2200) / (len(notes) * 3)
def kick(g=1):
    n = int(.5 * SR); t = np.arange(n) / SR; f = 45 + 90 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) * g
def boom():
    n = int(3 * SR); t = np.arange(n) / SR; f = 38 + 60 * np.exp(-t * 12)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    y += lp(rng.standard_normal(n), 300) * np.exp(-t * 4) * .6
    return y
def noise(n): return rng.standard_normal(n)

# ---------------- music ----------------
BPM = 92; beat = 60 / BPM; bar = beat * 4
t_war = cs('g1') - .12; t_lift = cs('i1') - .15; t_zip = cs('l1') - .06; t_title = cs('l2') - .3
minor = [[57, 60, 64], [53, 57, 60], [50, 53, 57], [52, 56, 59]]      # Am F Dm E
major = [[48, 52, 55], [55, 59, 62], [57, 60, 64], [53, 57, 60]]      # C G Am F
t = 0.4; bi = 0
while t < t_zip - .05:
    lift = t >= t_lift - .01; war = t_war <= t < t_lift
    ch = (major if lift else minor)[bi % 4]
    L = min(bar, t_zip - t)
    add(music, pad([c + 12 * lift for c in ch] + [ch[0] - 12], L, a=.6 if not war else .3, r=.8), t, .22 if not war else .28)
    add(music, piano(ch[0] - 24, 2.4), t, .55)
    # arpeggio plucks (8ths)
    arp = [ch[0], ch[1], ch[2], ch[1] + 12, ch[2] + 12, ch[1] + 12, ch[2], ch[1]]
    for k in range(8):
        tt = t + k * beat / 2
        if tt >= t_zip - .05: break
        if not lift and not war and k % 2 == 1 and t < 10: continue
        add(music, pluck(arp[k] + 12 * (1 if lift else 0), 1.0, 1.5 if lift else 1.0), tt, .32 if k % 2 == 0 else .22, pan=(-.4 if k % 2 else .4))
        if lift and k in (0, 3, 6): add(music, pluck(arp[k] + 36, .8, 2.5), tt, .1, pan=.6)
    if war or lift:
        for k in range(4):
            tt = t + k * beat
            if tt < t_zip - .05 and (war or k % 2 == 0): add(music, kick(1.0 if k % 2 == 0 else .6), tt, .55 if war else .35)
    if war:  # staccato low strings
        for k in range(8):
            tt = t + k * beat / 2
            if tt < t_lift: add(music, lp(pluck(ch[0] - 12, .25, 3) + pluck(ch[0], .25, 3), 1800), tt, .35)
    t += bar; bi += 1
# riser into the zip
n = int(1.6 * SR); tt = np.arange(n) / SR
add(music, hp(noise(n), 1500) * (tt / 1.6) ** 2 * .12, t_zip - 1.6)
# final chord
add(music, pad([48, 55, 60, 64, 67, 72], DUR - t_title - 1.2, a=.15, r=1.3), t_title + .05, .4)
add(music, piano(36, 4) + piano(48, 4) + piano(55, 4) + piano(64, 4), t_title + .05, .5)
add(music, boom(), t_title + .02, .6)
for k, m in enumerate([72, 76, 79, 84]): add(music, pluck(m, 1.5, 2.5), t_title + .4 + k * .12, .18, pan=(k - 1.5) / 2)

# ---------------- sfx ----------------
def click(g=1.0):  # typewriter key
    n = int(.04 * SR); y = bp(noise(n), 1500, 6000) * env(n, .0005, .006) + bp(noise(n), 200, 800) * env(n, .0005, .012) * .6
    return y * g
def typing(t0, dur, rate=14):
    k = 0
    while k / rate < dur:
        add(sfx, click(.35 + rng.random() * .2), t0 + k / rate + rng.random() * .02, pan=rng.random() * .4 - .2); k += 1
def thud(g=1.0):
    n = int(.35 * SR); return (lp(noise(n), 400) * env(n, .001, .05) * 1.5 + bp(noise(n), 800, 3000) * env(n, .001, .015) * .5) * g
def whoosh(dur=.45, g=1.0):
    n = int(dur * SR); tt = np.arange(n) / SR; x = noise(n)
    e = np.sin(np.pi * tt / dur) ** 2
    lo = bp(x, 300, 1200) * (1 - tt / dur); hi = bp(x, 1500, 6000) * (tt / dur)
    return (lo + hi * .7) * e * g
def zipsound(dur, rate0=90, rate1=220, g=1.0):
    n = int(dur * SR); y = np.zeros(n); tt = 0.0
    while tt < dur:
        p = tt / dur; i = int(tt * SR); m = int(.006 * SR)
        if i + m < n: y[i:i + m] += bp(noise(m), 2500, 9000) * env(m, .0002, .0015)[:m] * (0.6 + .4 * rng.random())
        tt += 1 / lerp(rate0, rate1, p) * (0.8 + .4 * rng.random())
    bed = bp(noise(n), 1000, 5000) * .15 * np.sin(np.pi * np.arange(n) / n) ** .5
    return (y + bed) * g
def lerp(a, b, p): return a + (b - a) * p
def stampsfx(): return thud(1.4) + np.pad(click(.8), (0, int(.31 * SR)))[:int(.35 * SR)]

# scene starts (mirror of scenes.js)
starts = [cs('b1') - .2, cs('c1') - .15, cs('d1') - .15, cs('e1') - .15, cs('f1') - .15, cs('g1') - .12, cs('h1') - .15, cs('i1') - .15, cs('j1') - .15, cs('k1') - .15]
for s in starts: add(sfx, whoosh(.45), s - .22, .35, pan=rng.random() - .5)
# A: clock ticks + pen scratch
for k in range(6): add(sfx, bp(noise(int(.02 * SR)), 2000, 7000) * env(int(.02 * SR), .0003, .003), .3 + k, .25 if k % 2 else .35, pan=-.5)
n = int(1.7 * SR); tt = np.arange(n) / SR
add(sfx, bp(noise(n), 2500, 7000) * (0.5 + .5 * np.abs(np.sin(tt * 2 * np.pi * 5))) * .07, .55)
typing(.15, .7, 18); typing(2.4, .6, 14)
# paper strip pops
for tt0 in [cs('a1') + 1.9, cs('a2'), cs('b1') + .05, cs('b1') + .3, cs('b1') + 1.3, cs('b2') + .1, cs('e1') + .5, cs('f1') + .7, ce('f1') - 1.3, cs('g2'), cs('h1'), cs('h2'), cs('h3'), cs('h3') + .9, cs('j2') + .1, cs('j3')]:
    add(sfx, thud(.45), tt0 + .05, pan=rng.random() * .6 - .3)
typing(cs('b1') + 1.4, 1.1, 16)
# C: rolling counter + stamp
typing(cs('c1') - .05, 1.15, 22); add(sfx, stampsfx(), cs('c1') - .15 + .95, .8)
# D
add(sfx, whoosh(.4, .6), cs('d1') - .15, .4)
typing(cs('d1') + .05, .9, 16); typing(ce('d1') - .8, .5, 16); add(sfx, thud(.6), cs('d1') + .4); add(sfx, thud(.5), cs('d1') + 1.05)
add(sfx, stampsfx(), cs('d2') + .6, .9); typing(cs('d2') + .9, .7, 18)
# E: crowd murmur
s0, s1 = cs('e1') - .15, cs('f1') - .15; n = int((s1 - s0 + .3) * SR); tt = np.arange(n) / SR
murmur = bp(noise(n), 250, 1100) * (0.6 + .4 * np.sin(tt * 3.1) * np.sin(tt * 1.7)) * np.minimum(1, tt / .4) * np.minimum(1, (tt[-1] - tt) / .3)
add(sfx, murmur, s0, .09)
add(sfx, thud(.7), cs('e2')); add(sfx, thud(.7), cs('e3')); add(sfx, thud(1.0), cs('e3') + .3)
# F
add(sfx, thud(.7), cs('f1') + .05); typing(cs('f1') + 1.2, .6, 16); typing(cs('f1') + .6, 1.2, 18)
add(sfx, zipsound(ce('f1') - cs('f1') + .1, 40, 70, .12), cs('f1') + .3)
# G: slams
add(sfx, boom(), cs('g1') + .02, .65)
add(sfx, thud(1.6), cs('g1') + .02); add(sfx, thud(1.8), cs('g1') + .6)
n = int(.3 * SR); add(sfx, bp(noise(n), 3000, 8000) * env(n, .001, .05) * .5, cs('g1') + .6)  # metal clink
add(sfx, thud(1.2), cs('g2') + 1.0)
# H: long zip up
h0 = cs('h1') - .15 + .1; add(sfx, zipsound(ce('h3') - h0, 60, 160, .32), h0)
# I
add(sfx, whoosh(.5, .7), cs('i2') - .1, .5); typing(cs('i1') + .65, .6, 16); typing(cs('i2') + .2, 1.0, 16)
for k in range(8): add(sfx, click(.25), cs('i1') + k * .045)
add(sfx, thud(.7), cs('i2') + 1.15)
# J
add(sfx, stampsfx(), cs('j1') + .5, 1.0); add(sfx, thud(1.0), cs('j2') + 1.7)
add(sfx, thud(1.3), cs('j3') + .2, pan=-.3); add(sfx, thud(1.3), cs('j3') + .35, pan=.3)
# K/L
typing(cs('k1') + .05, .8, 18); typing(cs('k1') + .9, .6, 14)
for d in (0, .12, .24): add(sfx, thud(.5), cs('k1') - .05 + d)
add(sfx, zipsound(.32, 250, 400, .9), t_zip - .3); add(sfx, boom() * .5, t_zip + .1); add(sfx, thud(1.6), t_zip + .1)
# title
add(sfx, zipsound(1.1, 120, 220, .35), t_title + .3)
typing(t_title + 1.1, .5, 14); typing(t_title + 1.5, .8, 16)
# vinyl crackle bed
cr = np.zeros(N); idx = rng.integers(0, N, int(DUR * 25)); cr[idx] = rng.standard_normal(len(idx)) * .5
cr = hp(cr, 1500) + lp(noise(N), 200) * .01
sfx[:, 0] += cr * .5; sfx[:, 1] += cr * .5

# ---------------- VO + mix ----------------
w = wave.open('../vo/vo_full.wav'); vo = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
vo = resample_poly(vo, 2, 1); vo = hp(vo, 80)
# gentle presence + compression-ish
vo = vo / (np.max(np.abs(vo)) + 1e-9) * .85
v = np.zeros(N); v[:min(N, len(vo))] = vo[:N]
# duck music under VO
envv = lp(np.abs(v), 6, 1); duck = 1 - .45 * np.clip(envv / .08, 0, 1)
music *= duck[:, None]
mix = music * .4 + sfx * .5 + np.stack([v, v], 1) * 1.0
# fade
fade_n = int(.6 * SR); end = int(DUR * SR)
mix[end - fade_n:end] *= np.linspace(1, 0, fade_n)[:, None]; mix[end:] = 0
mix = mix[:end]
mix = np.tanh(mix / np.max(np.abs(mix)) * 1.2) * .89
with wave.open('mix.wav', 'wb') as o:
    o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR); o.writeframes((mix * 32767).astype(np.int16).tobytes())
print('mix', len(mix) / SR, 's')
