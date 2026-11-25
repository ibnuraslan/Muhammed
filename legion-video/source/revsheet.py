# review sheets: 1 frame per second, 4x4 tiles, labelled with time + cue
import sys, json
from PIL import Image, ImageDraw
d, tl, prefix, t0, t1 = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5])
S = json.load(open(tl))['shots']
def cue(t): return max(i for i, x in enumerate(S) if x['start'] <= t + 1e-6)
ts = [t0 + k for k in range(int(t1 - t0))]; out = []
for p in range(0, len(ts), 16):
    sh = Image.new('RGB', (480 * 4, 300 * 4), (20, 20, 20)); dr = ImageDraw.Draw(sh)
    for i, t in enumerate(ts[p:p + 16]):
        f = int(t * 24)
        im = None
        for ff in (f, f - 1, f + 1, f - 2, f + 2):
            try: im = Image.open(f'{d}/{ff:05d}.jpg').resize((480, 270)); f = ff; break
            except Exception: pass
        if im is None: continue
        x, y = 480 * (i % 4), 300 * (i // 4); sh.paste(im, (x, y)); c = cue(t)
        dr.text((x + 4, y + 272), f'{int(t)//60}:{int(t)%60:02d} f{f} cue{c} {S[c]["shot"]}', fill=(255, 230, 80))
        dr.text((x + 4, y + 285), S[c]['text'][:78], fill=(200, 200, 200))
    fn = f'{prefix}_{p // 16:02d}.jpg'; sh.save(fn, quality=82); out.append(fn)
print(len(out))
