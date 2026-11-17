import json, re, io, struct, time, threading, numpy as np, requests
from PIL import Image
W, H = 1920, 816
class Z:
    def __init__(s, url_file, members):
        s.url = open(url_file).read().strip()
        s.idx = {int(re.search(r'(\d+)\.png', x[0]).group(1)): x for x in json.load(open(members))}
        s.tl = threading.local()
    def get(s, a, b):
        if not hasattr(s.tl, 's'): s.tl.s = requests.Session()
        for i in range(10):
            try:
                r = s.tl.s.get(s.url, headers={'Range': f'bytes={a}-{b}'}, timeout=120)
                if r.status_code == 206 and len(r.content) == b - a + 1: return r.content
                raise IOError(f'status {r.status_code} len {len(r.content)}')
            except Exception as e:
                print('retry', a, i, e, flush=True); time.sleep(min(60, 2 ** i))
        raise IOError('fetch failed')
    def load(s, n, raw=False):
        name, off, cs, fs, ct = s.idx[n]
        d = s.get(off, off + 30 + len(name) + 512 + cs)
        assert d[:4] == b'PK\x03\x04'
        nl, el = struct.unpack('<HH', d[26:30]); st = 30 + nl + el
        png = d[st:st + cs]
        if len(png) < cs: png += s.get(off + len(d), off + st + cs - 1)
        if raw: return png
        im = Image.open(io.BytesIO(png)); im.load()
        a = np.asarray(im.convert('RGB')); assert a.shape == (H, W, 3), a.shape
        return a
