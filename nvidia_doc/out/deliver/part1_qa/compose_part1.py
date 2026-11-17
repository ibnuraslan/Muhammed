import sys, json, re, io, struct, time, threading, subprocess, collections
import numpy as np, requests
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from scipy.ndimage import gaussian_filter
url_file, members, overlay, out_mp4, qa_csv = sys.argv[1:6]
start = int(sys.argv[6]) if len(sys.argv) > 6 else 1
import os; END = int(os.environ.get("END", 9949)); W, H = 1920, 816
url = open(url_file).read().strip()
m = json.load(open(members))
idx = {int(re.search(r'(\d+)\.png', x[0]).group(1)): x for x in m}
assert sorted(idx) == list(range(1, 9950))
tl = threading.local()
def sess():
    if not hasattr(tl, 's'): tl.s = requests.Session()
    return tl.s
def get(a, b):
    for i in range(10):
        try:
            r = sess().get(url, headers={'Range': f'bytes={a}-{b}'}, timeout=120)
            if r.status_code == 206 and len(r.content) == b - a + 1: return r.content
            raise IOError(f'status {r.status_code} len {len(r.content)}')
        except Exception as e:
            print('retry', a, i, e, flush=True); time.sleep(min(60, 2 ** i))
    raise IOError('fetch failed')
def load(n):
    name, off, cs, fs, ct = idx[n]
    d = get(off, off + 30 + len(name) + 512 + cs)
    assert d[:4] == b'PK\x03\x04'
    nl, el = struct.unpack('<HH', d[26:30]); s = 30 + nl + el
    png = d[s:s + cs]
    if len(png) < cs: png += get(off + len(d), off + s + cs - 1)
    im = Image.open(io.BytesIO(png)); im.load()
    a = np.asarray(im.convert('RGB'))
    assert a.shape == (H, W, 3)
    return a
# overlay decoder (ARGB qtrle -> rgba raw)
ov = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', overlay, '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'], stdout=subprocess.PIPE, bufsize=W*H*4*2)
def ov_frame():
    b = ov.stdout.read(W * H * 4); assert len(b) == W * H * 4
    return np.frombuffer(b, np.uint8).reshape(H, W, 4)
for _ in range(start - 1): ov_frame()
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-framerate', '24', '-i', '-',
    '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p', '-c:v', 'libx264', '-profile:v', 'high', '-preset', 'slow', '-crf', '18',
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', '-r', '24', '-movflags', '+faststart', out_mp4],
    stdin=subprocess.PIPE)
# Ch2 patch: the farm baked the wrong title ("BEHIND CLOSED DOORS") into Ch2 frames 4770-4870; cover its full extent with a
# soft dark plate rebuilt from the rows just above/below the text, then the overlay's "THE MEMO" goes on top.
C2 = (4770, 4870); Y0, Y1, X0, X1 = 330, 510, 230, 1690
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
def box_mask(feather=60):
    dx = np.maximum(np.maximum(X0 - xx, xx - X1), 0); dy = np.maximum(np.maximum(Y0 - yy, yy - Y1), 0)
    d = np.sqrt(dx ** 2 + dy ** 2)
    return np.clip(1 - d / feather, 0, 1)
PM = box_mask()[..., None]
def c2_patch(img, fade):
    top = img[Y0 - 22:Y0 - 6].astype(np.float32).mean(0); bot = img[Y1 + 6:Y1 + 22].astype(np.float32).mean(0)
    top = gaussian_filter(top, (25, 0)); bot = gaussian_filter(bot, (25, 0))
    t = np.clip((yy[:, :1] - (Y0 - 14)) / ((Y1 + 14) - (Y0 - 14)), 0, 1)[..., None]
    plate = (top[None] * (1 - t) + bot[None] * t) * 0.8
    a = PM * fade
    return img.astype(np.float32) * (1 - a) + plate * a
q = open(qa_csv, 'a'); prev = None
t0 = time.time()
with ThreadPoolExecutor(6) as ex:
    pending = collections.deque()
    nxt = start
    while nxt <= END and len(pending) < 24: pending.append((nxt, ex.submit(load, nxt))); nxt += 1
    while pending:
        n, fut = pending.popleft()
        img = fut.result()
        if nxt <= END: pending.append((nxt, ex.submit(load, nxt))); nxt += 1
        o = ov_frame(); oa = o[..., 3]
        if oa.max() > 0 or C2[0] - 2 <= n <= C2[1] + 2:
            f = img.astype(np.float32)
            if C2[0] - 2 <= n <= C2[1] + 2:
                fade = 1.0 if C2[0] <= n <= C2[1] else 0.0
                f = c2_patch(img, fade)
            al = oa.astype(np.float32)[..., None] / 255.0
            f = f * (1 - al) + o[..., :3].astype(np.float32) * al
            img = np.clip(f + 0.5, 0, 255).astype(np.uint8)
        enc.stdin.write(img.tobytes())
        s = img[::8, ::8].astype(np.float32); y = (0.2126 * s[..., 0] + 0.7152 * s[..., 1] + 0.0722 * s[..., 2])
        diff = -1 if prev is None else float(np.abs(y - prev).mean())
        q.write(f'{n},{y.mean():.2f},{y.std():.2f},{diff:.2f}\n'); prev = y
        if n % 200 == 0:
            q.flush(); el = time.time() - t0
            print(f'frame {n} {(n - start + 1) / el:.2f} fps eta {(END - n) / ((n - start + 1) / el) / 60:.1f} min', flush=True)
enc.stdin.close(); rc = enc.wait(); q.close()
print('DONE rc', rc, flush=True)
