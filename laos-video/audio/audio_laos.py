import json, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, resample_poly
SR = 44100
TL = json.load(open('../vo_laos/timeline.json')); SH = TL['shots']; DUR = TL['duration']; N = int(DUR * SR) + SR
rng = np.random.default_rng(9)
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
C = [s['start'] for s in SH]; NAMES = [s['shot'].split(':')[0] for s in SH]
def dur(i): return SH[i]['end'] - SH[i]['start']
# ---------- moods ----------
def mood(i):
    n = NAMES[i]
    if i >= 130 or n in ('garden', 'school_gate', 'school_teacher', 'team_destroy') and i > 112: return 'hope'
    if n in ('tonnage', 'duds_rain', 'jets_trail', 'jets_north', 'missions', 'clock', 'cluster_drop', 'cluster_open', 'counter', 'karst_jets', 'nva_march', 'trail_trucks', 'life_split', 'family_bunker', 'treaty_burn', 'hmong'): return 'war'
    if 46 <= i <= 78: return 'cave'
    if n in ('teacher_memory', 'bomb_ground', 'hoe_strike', 'child_find', 'scrap_search', 'scrap_hand', 'atta_find', 'atta_think', 'atta_bury', 'atta_fear', 'bombie_soil', 'bombie_path', 'poverty_risk', 'danger_moves', 'look_down'): return 'tense'
    if i <= 6 or 107 <= i <= 123: return 'calm'
    return 'neutral'
def mood_at(t):
    k = 0
    for i, s in enumerate(SH):
        if t >= s['start']: k = i
    return mood(k)
# ---------- music: khaen-like reed drone + khim-like plucks, pentatonic ----------
PENT = [0, 2, 4, 7, 9]
def reed(m, d, bright=1.0):
    n = int((d + 1.2) * SR); t = np.arange(n) / SR; f = mf(m) * (1 + .003 * np.sin(2 * np.pi * 5.2 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR; y = sum(np.sin(ph * h) / h ** 1.1 for h in range(1, 9))
    e = np.minimum(1, t / 1.0) * np.where(t > d, np.exp(-(t - d) / .5), 1)
    return lp(y * e, 900 * bright) * .25
def khim(m, d=1.6):
    n = int(d * SR); t = np.arange(n) / SR; f = mf(m)
    y = sum(a * np.sin(2 * np.pi * f * k * t) * np.exp(-t * (3 + k * 2.5)) for k, a in enumerate([1, .5, .35, .2, .1], 1))
    return y * np.minimum(1, t / .002) * .35
def drum(g=1.0, f0=60):
    n = int(1.0 * SR); t = np.arange(n) / SR; f = f0 + 80 * np.exp(-t * 20)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4) + lp(noise(n), 300) * np.exp(-t * 16) * .4) * g
ROOT = {'calm': 57, 'hope': 57, 'neutral': 52, 'tense': 50, 'cave': 45, 'war': 45}
SLOT, BEAT = 4.8, .6
t = 0.0; slot = 0
while t < DUR - 1:
    md = mood_at(t + SLOT / 2); r = ROOT[md]
    add(mus, reed(r - 12, SLOT, .8), t, .7); add(mus, reed(r - 5, SLOT, .7), t, .35 if md in ('calm', 'hope', 'neutral') else .5)
    if md in ('calm', 'hope'):
        seq = [0, 2, 4, 2, 7, 4, 9, 7] if slot % 2 == 0 else [4, 7, 9, 12, 9, 7, 4, 2]
        for k, s in enumerate(seq): add(mus, khim(r + 12 + s, 1.4), t + k * BEAT, .5 if md == 'hope' else .38)
    if md == 'neutral':
        for k, s in enumerate([0, 4, 7, 4]): add(mus, khim(r + 12 + s, 2.0), t + k * BEAT * 2, .3)
    if md == 'tense':
        for k in range(4): add(mus, khim(r + 12 + (1 if k % 2 else 0), 2.2), t + k * BEAT * 2, .28)
        add(mus, reed(r - 11, SLOT, .5), t, .25)
    if md == 'cave':
        for k, s in enumerate([0, 3, 7]): add(mus, khim(r + 24 + s, 3.0), t + .4 + k * BEAT * 2.6, .2)
    if md == 'war':
        for k in range(8):
            if k % 2 == 0 or k == 7: add(mus, drum(1 if k % 4 == 0 else .6), t + k * BEAT, .55)
        add(mus, reed(r - 24, SLOT, .5), t, .4)
    t += SLOT; slot += 1
add(mus, reed(45, 9, 1.0) + reed(52, 9, 1.0) + reed(57, 9, 1.2) + reed(64, 9, 1.0), DUR - 10.5, .6)
# ---------- sfx library ----------
D1, D2 = '../sfx/wav/', '../sfx2/wav/'
_c = {}
def smp(name):
    if name not in _c:
        try: a, sr = sf.read(D2 + name + '.wav')
        except Exception: a, sr = sf.read(D1 + name + '.wav')
        if a.ndim > 1: a = a.mean(1)
        _c[name] = a / (np.abs(a).max() + 1e-9)
    return _c[name]
def seg(name, d, off=None, fa=.4, fb=.5):
    a = smp(name); n = int(d * SR)
    if len(a) < n: a = np.tile(a, n // len(a) + 1)
    o = int((off if off is not None else rng.random() * max(0, len(a) / SR - d)) * SR); o = max(0, min(o, len(a) - n))
    return fade(a[o:o + n].copy(), fa, fb)
def peak(name, d, pre=.5):   # segment whose loudest moment sits at fraction `pre`
    a = smp(name); w = int(.25 * SR); cs = np.concatenate([[0], np.cumsum(a ** 2)]); en = np.zeros(len(a)); en[w // 2:len(a) - w // 2] = (cs[w:] - cs[:-w])[:len(a) - 2 * (w // 2)]; i = int(np.argmax(en)); n = int(d * SR); o = max(0, min(len(a) - n, i - int(pre * n)))
    return fade(a[o:o + n].copy(), .3, .6)
def one(name, t, g): add(amb, smp(name), t, g)
def beep(n=3, gap=.35):
    out = np.zeros(int((n * gap + .2) * SR))
    for k in range(n): tt = np.arange(int(.09 * SR)) / SR; b = np.sin(2 * np.pi * 1800 * tt) * fade(np.ones(len(tt)), .005, .02); i = int(k * gap * SR); out[i:i + len(b)] += b
    return out * .5
def engine(d, f0=38, rough=1.0):
    n = int(d * SR); tt = np.arange(n) / SR; f = f0 * (1 + .04 * np.sin(2 * np.pi * .7 * tt)); ph = 2 * np.pi * np.cumsum(f) / SR
    y = sum(np.sign(np.sin(ph * h)) / h ** 1.5 for h in range(1, 6)) * .3 + lp(noise(n), 400) * .4 * rough
    return fade(lp(y, 900), .5, .6)
def digs(d, rate=1.4):
    out = np.zeros(int(d * SR))
    for k in range(int(d * rate)):
        n = int(.18 * SR); tt = np.arange(n) / SR; y = bp(noise(n), 200, 2500) * np.exp(-tt * 22) + np.sin(2 * np.pi * 90 * tt) * np.exp(-tt * 30) * .6; i = int((k / rate + .1) * SR)
        if i + n < len(out): out[i:i + n] += y
    return out * .8
def bell(d=2.5):
    n = int(d * SR); tt = np.arange(n) / SR; return sum(a * np.sin(2 * np.pi * 880 * r * tt) * np.exp(-tt * (1.5 + r)) for r, a in [(1, 1), (2.76, .5), (5.4, .25)]) * .4
def muffle(x): return lp(x, 500)
# ---------- per-shot ambience ----------
BIRDS = {'school_wide', 'teacher_close', 'clearance_school', 'children_run', 'village_reveal', 'rebuild', 'karst', 'cave_enter', 'fields_day', 'day_night', 'cave_threshold', 'stretcher_night', 'bombie_soil', 'bombie_path', 'return_land', 'hoe_strike', 'child_find', 'house_plan', 'look_down', 'need_land', 'poverty_risk', 'scrap', 'scrap_yard', 'scrap_search', 'generation', 'atta_find', 'atta_think', 'atta_bury', 'atta_fear', 'team_arrive', 'team_found', 'garden', 'school_return', 'school_teacher', 'school_gate', 'deminer', 'measure_shelter', 'measure_ground', 'finale', 'hmong', 'nva_march', 'villagers_between', 'aftermath_field', 'sky_clear'}
NIGHT = {'night_farm_teaser', 'night_farm', 'night_breath', 'measure_hours', 'measure_night', 'cave_hospital_teaser'}
CAVE = {'cave_rooms', 'cave_theatre', 'cave_office', 'cave_class', 'cave_ward', 'cave_work', 'hunger', 'cave_drip', 'sick_bed', 'hospital_cave', 'hospital_roof', 'hospital_build'}
PLAY = {'school_wide', 'teacher_close', 'teacher_memory', 'children_run', 'bomb_ground', 'school_return', 'school_teacher', 'finale', 'garden', 'generation', 'risk_class'}
for i, s in enumerate(SH):
    n, d, t0 = NAMES[i], dur(i), C[i]
    if n in BIRDS: add(amb, seg('jungle_' + str(i % 3), d, fa=.6, fb=.6), t0, .22)
    if n in NIGHT or (n == 'day_night' and s['shot'].endswith(':2')): add(amb, seg('crickets_' + ('0' if i % 2 else '2'), d, fa=.6, fb=.6), t0, .35)
    if n in CAVE or (46 <= i <= 78 and n.startswith('cave')): add(amb, seg('drip_0', d, fa=.5, fb=.5), t0, .3); add(amb, lp(seg('murmur_' + str(i % 3), d), 1200), t0, .12)
    if n in PLAY: g = .12 if n in ('teacher_memory', 'bomb_ground') else .3; x = seg('playground_' + ('0' if i % 2 else '2'), d, fa=.5, fb=.5); add(amb, lp(x, 600) if n == 'bomb_ground' else x, t0, g)
    if n in ('geneva', 'geneva_flags', 'planner_map', 'cave_office', 'cave_theatre'): add(amb, seg('murmur_' + str(i % 3), d), t0, .15)
    if n in ('nva_march',): add(amb, seg('marching_1', d), t0, .25)
    if n in ('aftermath_field', 'rebuild', 'ruined_home', 'cave_mouth', 'cave_exit', 'karst', 'hmong', 'last_plane'): add(amb, seg('wind_' + str(i % 3), d, fa=.8, fb=.8), t0, .18)
    if n in ('ruined_home',): add(amb, seg('stove_1', d), t0, .35)
# ---------- specific events ----------
def jet(t, g=.6, d=5.0, muff=False): x = peak('jet_' + ('0' if int(t) % 2 else '2'), d, .45); add(amb, muffle(x) if muff else x, t, g)
def boom(t, g=.6, k=0, muff=False): x = smp('explosion_' + str(k % 3)); add(amb, muffle(x) if muff else x, t, g)
add(amb, beep(4, .5), C[3] + .6, .25); add(amb, beep(3, .4), C[3] + 3.0, .25)
for k in range(6): one('thud_' + str(k % 3), C[3] + .5 + k * .7, .12)
jet(C[4] - .4, .35, 4.0, True)
add(amb, lp(seg('jet_2', dur(8)), 400), C[8], .5); [boom(C[8] + 1.5 + k * .9, .25, k, True) for k in range(4)]
jet(C[9] + 2.0, .7)
jet(C[10] - 1.0, .4, 3.0, True)
[boom(C[14] + .4 + k * .7, .35, k, True) for k in range(3)]; [one('thud_' + str(k % 3), C[14] + 1.2 + k * .25, .3) for k in range(4)]
one('pen_0', C[22] + .3, .5); one('paper_0', C[23] + .2, .5)
add(amb, engine(dur(24)), C[24], .35)
add(amb, engine(dur(31), 34), C[31], .45); add(amb, seg('crickets_2', dur(31)), C[31], .2)
jet(C[29] + 1.6, .55); jet(C[32] - .3, .7); [boom(C[32] + 1.3 + k * .35, .6, k) for k in range(3)]
jet(C[33] - .5, .5); [boom(C[33] + 1.4 + k * .4, .4, k) for k in range(4)]
add(amb, engine(dur(26), 60, .3) * .6, C[26], .3)
add(amb, lp(seg('jet_2', dur(36)), 1200), C[36], .3)
add(amb, seg('clock_0', dur(37)), C[37], .45)
for k in range(3): add(amb, digs(.4, 3), C[42] + .2 + k * .5, .4)
jet(C[54] + .2, .5, 5, True); [boom(C[54] + 1.8 + k * .5, .5, k, True) for k in range(3)]
boom(C[57] + .6, .4, 1, True)
jet(C[71], .6, 3)
jet(C[79], .55, dur(79)); add(amb, seg('wind_1', dur(80)), C[80], .3); one('metalclang_0', C[80] + .8, .3)
[boom(C[81] + k * .45, .3, k, True) for k in range(8)]
jet(C[88], .35, 3.2, True)
add(amb, digs(dur(90) - .4, 2), C[90], .5)
one('metalclang_1', C[100] + .3, .3); one('metalclang_2', C[101] + .4, .4)
add(amb, beep(6, .9), C[102] + .8, .2)
add(amb, digs(4.0, 1.6), C[107], .45); add(amb, digs(dur(109), 2.5), C[109], .5); add(amb, digs(dur(110), 1.2), C[110], .3)
add(amb, engine(2.6, 50, .5), C[111], .4); one('doorbang_0', C[111] + 2.2, .3)
add(amb, beep(4, .15), C[112], .35)
boom(C[113] + 1.2, .9, 2)
add(amb, bell(), C[121] + .3, .35); add(amb, engine(2.5, 70, .4), C[121], .2)
add(amb, digs(dur(123), 1.0) * .5, C[123], .35)
one('paper_1', C[124] + .2, .45); one('paper_0', C[125] + .1, .45)
add(amb, seg('crickets_0', dur(127)), C[127], .35); add(amb, seg('crickets_2', dur(128)), C[128], .35)
jet(C[132] - .5, .3, 3.5, True)
# ---------- VO + mix ----------
vo, _ = sf.read('../vo_laos/vo_full.wav'); vo = resample_poly(vo, 147, 80); vo = hp(vo, 70); vo = vo / np.abs(vo).max() * .85
v = np.zeros(N); v[:min(N, len(vo))] = vo[:N]
envv = lp(np.abs(v), 5, 1); duck = 1 - .35 * np.clip(envv / .06, 0, 1)
r = lambda x: 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
MG, AG = .09, .3
print('VO dB', round(r(v), 1), 'music dB', round(r(mus * MG), 1), 'amb dB', round(r(amb * AG), 1))
Lm = (mus * MG + amb * AG) * duck + v
end = int(DUR * SR); Lm = Lm[:end]; Lm[-int(2.4 * SR):] *= np.linspace(1, 0, int(2.4 * SR))
Lm = np.tanh(Lm / np.abs(Lm).max() * 1.15) * .9
sf.write('mix_laos.wav', np.stack([Lm, Lm], 1), SR, subtype='PCM_16'); print('mix', round(len(Lm) / SR, 1))
