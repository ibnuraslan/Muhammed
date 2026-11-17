"""Part 2 base pass: stream the RenderStreet zip (HTTP Range, never written whole), substitute the 14 redo clips 1:1,
clean-plate the old baked chapter titles in c4_01/c5_01 and apply the new title style (full-frame dim + clean title),
re-apply the master's opening fade-up (frames 1-25) over c4_01. Writes a high-quality 4:4:4 intermediate; cards and
captions are burned in by compose_part2_final.py.  Logs per-frame luma/diff and seam stats."""
import sys, os, json, time, subprocess, collections
import numpy as np
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from zload import Z
from titles import Title
url_file, members, clipdir, out_mp4, qa_csv, seam_json = sys.argv[1:7]
END = int(os.environ.get("END", 10155)); W, H = 1920, 816
REDO = [(1, 249, "c4_01_redo"), (443, 730, "c4_03_redo"), (1405, 1518, "c4_08_v2_redo"), (1519, 1815, "c4_09_redo"),
        (2398, 2593, "c4_12_redo"), (2785, 2972, "c4_14_redo"), (3571, 3769, "c4_18_redo"), (4103, 4317, "c5_01_redo"),
        (4775, 4929, "c5_04_redo"), (5507, 5754, "c5_07_redo"), (5994, 6129, "c5_09_redo"), (6392, 6588, "c5_11_redo"),
        (6984, 7235, "c5_14_redo"), (8375, 8601, "c5_20_redo")]
owner = {}
for a, b, c in REDO:
    for n in range(a, b + 1): owner[n] = (a, b, c)
z = Z(url_file, members)
TT = {"c4_01_redo": Title("4"), "c5_01_redo": Title("5")}
class Clip:
    def __init__(s, c, a, b):
        s.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", os.path.join(clipdir, c + ".mp4"), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                               stdout=subprocess.PIPE, bufsize=W * H * 3 * 2); s.n = 0; s.want = b - a + 1; s.c = c
    def next(s):
        buf = s.p.stdout.read(W * H * 3); assert len(buf) == W * H * 3, (s.c, s.n); s.n += 1
        if s.n == s.want:
            extra = s.p.stdout.read(1); assert not extra, s.c + " has more frames than its range"; s.p.wait()
        return np.frombuffer(buf, np.uint8).reshape(H, W, 3)
def fade_up(F):
    if F >= 25: return 1.0
    u = (F - 1) / 24.0; return u * u * (3 - 2 * u)
need_farm = [n for n in range(1, END + 1) if n not in owner]
# also fetch the replaced farm frames at each range's first/last frame (seam reference)
extra = sorted({x for a, b, c in REDO for x in (a, b) if x <= END})
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-framerate", "24", "-i", "-",
    "-c:v", "libx264", "-preset", "fast", "-crf", "6", "-pix_fmt", "yuv444p", "-r", "24", out_mp4], stdin=subprocess.PIPE)
q = open(qa_csv, "w"); q.write("frame,src,luma,std,diff\n"); prev = None; seams = {}; t0 = time.time()
def stats(img):
    s = img[::8, ::8].astype(np.float32); return 0.2126 * s[..., 0] + 0.7152 * s[..., 1] + 0.0722 * s[..., 2]
with ThreadPoolExecutor(8) as ex:
    pend = {}; order = need_farm + extra; it = iter(sorted(set(order)))
    queue = collections.deque(sorted(set(order)))
    def pump():
        while queue and len(pend) < 32:
            n = queue.popleft(); pend[n] = ex.submit(z.load, n)
    pump(); clip = None
    for n in range(1, END + 1):
        o = owner.get(n)
        if n in pend and (o is None or n in extra):
            farm = pend.pop(n).result(); pump()
        else:
            farm = None
        if o:
            a, b, c = o
            if n == a: clip = Clip(c, a, b)
            img = clip.next()
            local = n - a + 1
            if c in TT:
                T = TT[c]
                if T.Cr is None and local == 70: pass
                f = img.astype(np.float32)
                if T.Cr is None: T.Cr = np.array([196.5, 192.0, 189.0], np.float32)   # calibrated on both clips' hold frames
                if local <= 125: f = T.apply(f, local)
                if c == "c4_01_redo": f = f * fade_up(n)
                img = np.clip(f + 0.5, 0, 255).astype(np.uint8)
            if farm is not None:
                seams[f"{c}@{n}"] = dict(farm_same=stats(farm).mean().item(), clip=stats(img).mean().item(),
                    farm_rgb=farm.reshape(-1, 3).mean(0).round(2).tolist(), clip_rgb=img.reshape(-1, 3).mean(0).round(2).tolist())
            src = c
        else:
            img = farm; src = "farm"
        enc.stdin.write(img.tobytes())
        y = stats(img); d = -1 if prev is None else float(np.abs(y - prev).mean())
        q.write(f"{n},{src},{y.mean():.2f},{y.std():.2f},{d:.2f}\n")
        # seam: record neighbour-farm stats on both sides of every range
        for a, b, c in REDO:
            if n in (a - 1, a, b, b + 1):
                seams.setdefault(f"{c}:{n}", dict(src=src, luma=float(y.mean()), rgb=img.reshape(-1, 3).mean(0).round(2).tolist(), diff_from_prev=d))
        prev = y
        if n % 200 == 0:
            q.flush(); json.dump(seams, open(seam_json, "w"), indent=1); el = time.time() - t0
            print(f"frame {n} {n / el:.2f} fps eta {(END - n) / (n / el) / 60:.1f} min", flush=True)
enc.stdin.close(); rc = enc.wait(); q.close(); json.dump(seams, open(seam_json, "w"), indent=1)
print("DONE rc", rc, flush=True)
