import json, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, resample_poly
SR = 44100
TL = json.load(open('../vo6/timeline.json')); SH = TL['shots']; DUR = TL['duration']; N = int(DUR * SR) + SR
rng = np.random.default_rng(5)
mus = np.zeros(N); amb = np.zeros(N)
def bp(x, a, b, o=2): return sosfilt(butter(o, [a, b], 'band', fs=SR, output='sos'), x)
def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def add(buf, x, t, g=1.0):
    i = int(t * SR)
    if i >= N or i + len(x) <= 0: return
    if i < 0: x = x[-i:]; i = 0
    x = x[:N - i]; buf[i:i + len(x)] += x * g
def mf(m): return 440 * 2 ** ((m - 69) / 12)
def noise(n): return rng.standard_normal(n)
def fade(x, a=.3, b=.3):
    n = len(x); e = np.ones(n); na, nb = min(n, int(a * SR)), min(n, int(b * SR)); e[:na] = np.linspace(0, 1, na); e[n - nb:] *= np.linspace(1, 0, nb); return x * e

MOOD = {}
for k in ['station_wide', 'train_pass', 'iron_throw', 'legionary_hit', 'stop_train', 'arrest', 'rifles_surrender', 'hidden_weapons', 'tribunal', 'boxcar', 'kuitun', 'pow_camp', 'pow_closeup', 'recon', 'junction', 'bridge_guard', 'tsar_fall', 'army_collapse', 'trench_empty', 'intervention']: MOOD[k] = 'tense'
for k in ['free_force', 'rail_battle', 'zborov']: MOOD[k] = 'battle'
for k in ['graves', 'graves_far', 'winter_sentry', 'legion_closeup', 'ship_sea']: MOOD[k] = 'sad'
for k in ['prague', 'homecoming', 'corps_parade', 'armistice', 'evac_port', 'volunteers', 'prisoners_march']: MOOD[k] = 'hope'
def shot_at(t):
    i = 0
    for k, s in enumerate(SH):
        if t >= s['start']: i = k
    return SH[i]
def mood_at(t): return MOOD.get(shot_at(t)['shot'].split(':')[0], 'neutral')

# ---------- music ----------
MINOR = [[50, 53, 57], [46, 50, 53], [48, 52, 55], [45, 49, 52]]   # Dm Bb C A
HOPE = [[50, 54, 57], [55, 59, 62], [47, 50, 54], [52, 55, 59]]    # D G Bm Em
def pad(notes, dur, bright=1.0):
    n = int((dur + 1.5) * SR); t = np.arange(n) / SR; y = np.zeros(n)
    for m in notes:
        for det in (-.07, 0, .07):
            f = mf(m) * 2 ** (det / 12); ph = rng.random() * 6
            for h, a in [(1, 1), (2, .45), (3, .25), (4, .12)]: y += a * np.sin(2 * np.pi * f * h * t + ph * h)
    e = np.minimum(1, t / 1.2) * np.where(t > dur, np.exp(-(t - dur) / .5), 1)
    return lp(y * e, 1400 * bright) / (len(notes) * 3)
def pluck(m, d=.5):
    n = int(d * SR); t = np.arange(n) / SR; f = mf(m); y = sum(np.sin(2 * np.pi * f * h * t) * np.exp(-t * (6 + h * 3)) / h for h in range(1, 7))
    return lp(y, 1500) * .5
def piano(m, d=3.0):
    n = int(d * SR); t = np.arange(n) / SR; f = mf(m)
    return sum(a * np.sin(2 * np.pi * f * k * 1.0007 ** k * t) * np.exp(-t * (1.1 + k * .6)) for k, a in enumerate([1, .45, .25, .12, .06], 1)) * np.minimum(1, t / .004) * .4
def taiko(g=1.0):
    n = int(1.2 * SR); t = np.arange(n) / SR; f = 52 + 70 * np.exp(-t * 18)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.5) + lp(noise(n), 200) * np.exp(-t * 14) * .5) * g
SLOT, BEAT = 4.8, .6
slot = 0; t = 0.0
while t < DUR - 2:
    md = mood_at(t + SLOT / 2); chords = HOPE if md == 'hope' else MINOR; ch = chords[slot % 4]
    add(mus, pad([m - 12 for m in ch] + [ch[0] - 24] + ([ch[2] + 12] if md == 'hope' else []), SLOT, 1.3 if md == 'hope' else 1.0), t, .9)
    if md in ('tense', 'battle'):
        for k in range(8): add(mus, pluck(ch[0] - 12 + (7 if k % 4 == 3 else 0), .4), t + k * BEAT, .5 if md == 'battle' else .3)
    if md == 'battle':
        for k in range(8):
            if k % 2 == 0 or k == 7: add(mus, taiko(1 if k % 4 == 0 else .6), t + k * BEAT, .5)
    if md == 'sad':
        for k, m in enumerate([ch[2] + 12, ch[1] + 12, ch[0] + 12]): add(mus, piano(m), t + .3 + k * BEAT * 2.4, .45)
    if md == 'hope':
        for k, m in enumerate([ch[0] + 24, ch[1] + 24, ch[2] + 24, ch[1] + 24]): add(mus, piano(m, 2.0), t + k * BEAT * 2, .3)
    t += SLOT; slot += 1
# title: low swell + single hit
add(mus, taiko(1.0), 0.05, .5)
# finale: warm major chord swell
add(mus, pad([50, 57, 62, 66, 69], 8, 1.4), DUR - 9, 1.1)

# ---------- ambience & sfx per shot (real CC0 recordings from Freesound) ----------
SFXD = '../sfx/wav/'
_cache = {}
def smp(name):
    if name not in _cache:
        a, sr = sf.read(SFXD + name + '.wav'); a = a / (np.abs(a).max() + 1e-9); _cache[name] = a
    return _cache[name]
def seg(name, d, off=None, fa=.4, fb=.5):
    a = smp(name); n = int(d * SR)
    if len(a) < n: a = np.tile(a, n // len(a) + 1)
    o = int((off if off is not None else rng.random() * max(0, len(a) / SR - d)) * SR); o = min(o, len(a) - n)
    return fade(a[o:o + n].copy(), fa, fb)
def oneshot(name, t, g):
    add(amb, smp(name), t, g)
def shot_sfx(i, name, v, t0, d, newshot):
    snowy = 'snow' in v or name in ('winter_sentry', 'pow_camp', 'graves', 'graves_far', 'pow_closeup')
    moving_train = name in ('train_east', 'train_pass') or (name == 'homecoming' and v in ('', '1'))
    if moving_train: add(amb, seg('steampass_1', d), t0, .35)
    elif name in ('station_wide', 'junction', 'stop_train', 'homecoming'): add(amb, seg('steamidle_0', d), t0, .3); add(amb, seg('murmur_1', d), t0, .12)
    if name in ('rail_battle', 'zborov'):
        add(amb, seg('battle_' + str(i % 3), min(d, 6.5)), t0, .45)
        for k, bt in enumerate([.4, 1.7, 3.1, 4.6]):
            if bt < d: oneshot('explosion_' + str((i + k) % 3), t0 + bt, .5)
        for k in range(int(d * 2)): oneshot('rifle_' + str((i + k) % 4), t0 + rng.random() * d, .18)
    if name == 'free_force':
        oneshot('doorbang_1', t0 + .4, .6)
        for k in range(5): oneshot('rifle_' + str(k % 4), t0 + 1 + k * .45, .25)
    if name in ('prague', 'homecoming', 'mobilize'): add(amb, seg('cheer_' + str(i % 3), d), t0, .3)
    if name in ('revolution', 'volunteers', 'diplomats', 'corps_parade', 'arrest', 'rifles_surrender'): add(amb, seg('murmur_' + str(i % 3), d), t0, .18)
    if name in ('mobilize', 'prisoners_march', 'intervention', 'corps_parade') or (name == 'revolution' and 'white' in v): add(amb, seg('marching_1', d), t0, .35)
    if snowy or name in ('winter_sentry',): add(amb, seg('wind_' + str(i % 3), d, fa=.8, fb=.8), t0, .3)
    if name in ('ship_sea', 'vladivostok', 'intervention', 'evac_port'): add(amb, seg('waves_' + str(i % 2), d, fa=.8, fb=.8), t0, .35)
    if name in ('ship_sea', 'evac_port', 'vladivostok') and i % 2 == 0: oneshot('shiphorn_1', t0 + .8, .3)
    if name in ('exiles', 'kuitun', 'tribunal', 'masaryk', 'hidden_weapons', 'tsar_fall'): add(amb, seg('clock_0', d), t0, .25)
    if name == 'boxcar': add(amb, seg('stove_2', d), t0, .35)
    if name == 'kuitun' and v in ('2', '4'): add(amb, seg('pen_0', min(d, 2.5)), t0 + .6, .5)
    if name in ('tribunal',) and v == '2': oneshot('thud_1', t0 + .9, .6)
    if name == 'tsar_fall': oneshot('metalclang_2', t0 + 1.5, .4)
    if name == 'hidden_weapons': oneshot('doorbang_0', t0 + .4, .25)
    if name == 'empire' and v == '4': oneshot('explosion_1', t0 + .8, .35)
    # ---- section-1 cinematic events ----
    if newshot:
        if i == 1: add(amb, seg('steamidle_0', d), t0, .35); add(amb, seg('murmur_1', d), t0, .2)
        if i == 2: add(amb, seg('steamleave_0', d, off=8), t0, .45); oneshot('whistle_2', t0 + .5, .35)
        if i == 3: add(amb, seg('steampass_2', d), t0, .3); oneshot('paper_0', t0 + .2, .0)
        if i == 4: add(amb, seg('steampass_2', d), t0, .25); oneshot('metalclang_1', t0 + .35, .6); oneshot('thud_2', t0 + 1.3, .6); add(amb, seg('murmur_2', d), t0, .25)
        if i == 5: add(amb, seg('steamidle_0', d), t0, .4); oneshot('whistle_0', t0 + .2, .3); add(amb, seg('murmur_0', d), t0, .3)
        if i == 8: add(amb, seg('battle_1', min(d, 6.5)), t0, .35)
        if i in (9, 11): add(amb, seg('murmur_1', d), t0, .15)
        if i == 10: add(amb, seg('wind_2', d), t0, .15); add(amb, seg('whistle_1', min(d, 3)), t0 + .5, .25)
        if i == 12: add(amb, seg('steampass_1', d), t0, .3)
        if i == 13: add(amb, seg('wind_1', d), t0, .35); add(amb, seg('steamidle_0', d), t0, .15)

def screech(d):
    n = int(d * SR); tt = np.arange(n) / SR; f = 2400 + 300 * np.sin(2 * np.pi * 7 * tt)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * .5 + bp(noise(n), 3000, 9000) * .6
    return fade(y * (0.6 + .4 * np.sin(2 * np.pi * 13 * tt) ** 2), .05, .4)
def swish(d):
    n = int(d * SR); tt = np.arange(n) / SR; return bp(noise(n), 300, 2500) * np.sin(np.pi * tt / d) ** 2 * (1 + .5 * np.sin(2 * np.pi * 3 * tt))
C = [s['start'] for s in SH]
def at(i, dt, fn): EV.append((C[i] + dt, fn))
EV = []
# section 1 (Chelyabinsk)
at(0, 0, lambda: add(amb, seg('steamidle_0', 1.8), C[0], .3)); at(0, 0, lambda: add(amb, seg('murmur_1', 1.8), C[0], .15))
at(1, 0, lambda: add(amb, seg('steampass_1', 3.2, off=20), C[1], .75)); at(1, 2.8, lambda: add(amb, seg('steampass_2', 5.2), C[1] + 2.8, .35)); at(1, 2.8, lambda: add(amb, seg('murmur_2', 5.2), C[1] + 2.8, .15))
at(2, 0, lambda: add(amb, seg('steampass_2', 1.0), C[2], .3)); at(2, .9, lambda: add(amb, fade(swish(1.5)), C[2] + .9, .4))
at(3, .35, lambda: oneshot('metalclang_1', C[3] + .35, .75)); at(3, 1.2, lambda: oneshot('thud_2', C[3] + 1.2, .7)); at(3, 1.7, lambda: add(amb, seg('marching_2', 1.1), C[3] + 1.7, .5))
at(4, 0, lambda: add(amb, screech(1.5), C[4], .35)); at(4, 0, lambda: add(amb, seg('steamidle_0', 5.1), C[4], .4)); at(4, 1.5, lambda: add(amb, seg('murmur_0', 2.2), C[4] + 1.5, .35)); at(4, 3.84, lambda: oneshot('rifle_1', C[4] + 3.84, .7)); at(4, 4.02, lambda: oneshot('rifle_2', C[4] + 4.02, .6))
at(5, 0, lambda: add(amb, seg('marching_2', 3.5), C[5], .4)); at(5, 0, lambda: add(amb, seg('murmur_1', 3.5), C[5], .2)); at(5, 3.1, lambda: oneshot('doorbang_2', C[5] + 3.1, .55))
at(6, 0, lambda: add(amb, seg('marching_1', 1.2), C[6], .5)); at(6, 1.75, lambda: oneshot('doorbang_0', C[6] + 1.75, .8)); at(6, 1.8, lambda: oneshot('rifle_0', C[6] + 2.0, .3))
at(7, 0, lambda: add(amb, fade(swish(1.2)), C[7], .2)); at(7, 2.25, lambda: oneshot('explosion_0', C[7] + 2.25, .9)); at(7, 3.1, lambda: add(amb, seg('stove_1', 1.4), C[7] + 3.1, .6)); at(7, 3.1, lambda: add(amb, seg('battle_2', 1.4), C[7] + 3.1, .3))
at(8, 0, lambda: add(amb, seg('steampass_1', 3.8, off=60), C[8], .2)); at(8, 0, lambda: add(amb, seg('wind_2', 3.8), C[8], .15))
at(9, 0, lambda: add(amb, seg('steampass_1', 2.7, off=60), C[9], .25)); at(9, 0, lambda: add(amb, seg('wind_1', 2.7), C[9], .2))
at(10, 0, lambda: add(amb, seg('steamleave_0', 2.0, off=10), C[10], .5)); at(10, 1.4, lambda: add(amb, seg('battle_0', 2.0), C[10] + 1.4, .45)); at(10, 1.6, lambda: oneshot('explosion_2', C[10] + 1.6, .4)); at(10, 3.6, lambda: add(amb, seg('cheer_0', 1.8), C[10] + 3.6, .55))
at(11, 0, lambda: add(amb, seg('stove_2', 2.4), C[11], .45)); at(12, 0, lambda: add(amb, seg('wind_1', 5.4, fa=.6, fb=1.2), C[12], .4))
# later sections: specific visual events
at(22, 1.4, lambda: add(amb, fade(swish(.8)), C[22] + 1.4, .4)); at(22, 1.6, lambda: oneshot('rifle_3', C[22] + 1.65, .15))
for k in range(6): at(27, 1.2 + k * .01, lambda k=k: oneshot('rifle_' + str(k % 4), C[27] + 1.2 + k * .012, .35))
at(33, .9, lambda: oneshot('metalclang_2', C[33] + 1.0, .55))
at(34, 2.5, lambda: oneshot('paper_1', C[34] + 2.5, .5))
at(36, 0, lambda: add(amb, seg('clock_1', 2.4), C[36], .45))
at(46, 0, lambda: add(amb, seg('pen_0', 1.8), C[46] + .1, .55))
at(57, .5, lambda: oneshot('metalclang_0', C[57] + .8, .35)); at(57, 2.0, lambda: oneshot('metalclang_2', C[57] + 2.2, .3))
at(59, 0, lambda: add(amb, seg('pen_1', 2.6), C[59], .5))
at(61, .1, lambda: oneshot('doorbang_0', C[61] + .1, .3))
at(67, .4, lambda: oneshot('metalclang_1', C[67] + .5, .4)); at(67, 1.2, lambda: oneshot('metalclang_0', C[67] + 1.3, .4))
at(68, 0, lambda: add(amb, seg('pen_1', 3.0), C[68], .45))
for i in (72, 78):
    for k in range(3): at(i, .3 + k * 1.2, lambda i=i, k=k: oneshot('explosion_' + str(k % 3), C[i] + .3 + k * 1.2, .6))
at(74, 1.2, lambda: add(amb, seg('cheer_1', 1.0), C[74] + 1.0, .35))
at(87, .0, lambda: add(amb, seg('stove_1', 2.4), C[87], .5)); at(87, 2.9, lambda: oneshot('explosion_1', C[87] + 2.9, 1.0)); at(87, 5.1, lambda: add(amb, seg('wind_0', 2.6), C[87] + 5.1, .3))
at(90, 1.8, lambda: add(amb, fade(bp(noise(int(1.8 * SR)), 2000, 7000) * .5, .05, .3), C[90] + 1.8, .35))
for k in range(4): at(99, .3 + k * 1.1, lambda k=k: oneshot('thud_' + str(k % 3), C[99] + .3 + k * 1.1, .6))
at(100, 1.0, lambda: add(amb, seg('cheer_2', 1.7), C[100] + 1.0, .5))
at(102, 2.6, lambda: add(amb, seg('cheer_0', 3.1), C[102] + 2.6, .6))
at(107, 0, lambda: add(amb, seg('clock_0', 1.3), C[107], .5)); at(107, 1.3, lambda: add(amb, seg('cheer_1', 1.7), C[107] + 1.3, .6))
for k in range(5): at(117, .7 + k * .5, lambda k=k: oneshot('rifle_' + str(k % 4), C[117] + .7 + k * .5, .3))
at(123, 4.0, lambda: add(amb, seg('pen_0', 2.0), C[123] + 4.0, .5))
at(126, .2, lambda: oneshot('shiphorn_0', C[126] + .2, .45)); at(128, .5, lambda: oneshot('shiphorn_2', C[128] + .5, .45))
at(131, .2, lambda: oneshot('whistle_0', C[131] + .2, .4)); at(131, 0, lambda: add(amb, seg('steamleave_1', 4.9), C[131], .35))
at(142, 0, lambda: add(amb, seg('cheer_2', 6.8), C[142], .5)); at(143, 0, lambda: add(amb, seg('cheer_1', 6.0), C[143], .45)); at(143, 0, lambda: add(amb, seg('steamidle_0', 6.0), C[143], .3))
for i, sh in enumerate(SH):
    if i < 13: continue
    nm, _, vv = sh['shot'].partition(':'); shot_sfx(i, nm, vv, sh['start'], sh['end'] - sh['start'], False)
for _, f in EV: f()

# ---------- VO + mix ----------
vo, _ = sf.read('../vo6/vo_full.wav'); vo = resample_poly(vo, 147, 80); vo = hp(vo, 70); vo = vo / np.abs(vo).max() * .85
v = np.zeros(N); v[:min(N, len(vo))] = vo[:N]
envv = lp(np.abs(v), 5, 1); duck = 1 - .35 * np.clip(envv / .06, 0, 1)
r = lambda x: 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
MG, AG = .08, .25
print('VO dB', round(r(v), 1), 'music dB', round(r(mus * MG), 1), 'amb dB', round(r(amb * AG), 1))
L = (mus * MG + amb * AG) * duck + v
end = int(DUR * SR); L = L[:end]; L[-int(2 * SR):] *= np.linspace(1, 0, int(2 * SR))
L = np.tanh(L / np.abs(L).max() * 1.15) * .9
sf.write('mix6.wav', np.stack([L, L], 1), SR, subtype='PCM_16'); print('mix', round(len(L) / SR, 1))
