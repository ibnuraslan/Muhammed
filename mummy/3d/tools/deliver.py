"""Farm packaging, step 3: normal independent zips (< 300 MB each, never split archives) of the delivery folder,
the CapCut shot list (.txt + .csv), and git transport parts (< 95 MB) with SHA256SUMS.

    python3 tools/deliver.py P1 <PKG dir> <out dir>
"""
import os, sys, json, zipfile, hashlib

PART, PKG, OUT = sys.argv[1], os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LIMIT = 280 * 1024 * 1024          # stay well under 300 MB per zip
GITPART = 90 * 1024 * 1024
os.makedirs(OUT, exist_ok=True)
tim = json.load(open(os.path.join(ROOT, "vo", PART + "_timing.json")))
N = tim["frames_total"]
NOTE = f"Extract all zips into ONE folder -> upload the folder -> render MASTER.blend, scene MASTER, frames 1-{N}."
open(os.path.join(PKG, "README_RENDER.txt"), "w").write(NOTE + "\n2560x1440, 24 fps, Cycles 64 spp adaptive + OIDN. Output: //frames/\n")

# --- CapCut shot list
paras = [p.strip() for p in open(os.path.join(ROOT, "..", "vo", f"MUMMY_{PART}_VO.txt")).read().split("\n\n") if p.strip()]
src = open(os.path.join(ROOT, "scenes", PART.lower() + ".py")).read()
import re
desc = dict(re.findall(r'\("(S\d+)",\s*\d+,\s*[\d.]+,\s*"([^"]*)"\)', src))
def tc(f):          # frame (1-based) -> HH:MM:SS:FF at 24 fps
    f0 = f - 1; s, ff = divmod(f0, 24); m, s = divmod(s, 60); h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}:{ff:02d}"
base = f"MUMMY_{PART}_capcut_shotlist"
with open(os.path.join(OUT, base + ".csv"), "w", encoding="utf-8") as fc, open(os.path.join(OUT, base + ".txt"), "w", encoding="utf-8") as ft:
    fc.write("shot,frame_in,frame_out,frames,tc_in,tc_out,seconds,vo_paragraph,description,vo_text\n")
    ft.write(f"MUMMY {PART} - CapCut shot list. One render: MASTER.blend scene MASTER frames 1-{N} (24 fps, {N / 24:.2f} s = VO length).\n"
             f"Lay the rendered frame sequence at 00:00:00:00 and the VO (MUMMY_{PART}_VO.mp3) at 00:00:00:00. Cuts below are already in the render.\n\n")
    for o in tim["shots"]:
        a, b = o["start"], o["start"] + o["frames"] - 1
        vo = paras[o["para"] - 1].replace('"', "'")
        fc.write(f'{o["shot"]},{a},{b},{o["frames"]},{tc(a)},{tc(b)},{o["frames"] / 24:.2f},{o["para"]},"{desc.get(o["shot"], "")}","{vo}"\n')
        ft.write(f'{o["shot"]}  frames {a:5d}-{b:5d}  {tc(a)} - {tc(b)}  ({o["frames"] / 24:.2f} s)  VO para {o["para"]}\n    {desc.get(o["shot"], "")}\n')

# --- zips: MASTER.blend + README in zip 1, then shots and textures packed by size
files = []
for d, _, fs in os.walk(PKG):
    for f in fs:
        p = os.path.join(d, f); rel = os.path.relpath(p, PKG)
        if rel.startswith("frames") or rel.endswith(".blend1"):
            continue
        files.append((rel, os.path.getsize(p)))
first = [f for f in files if f[0] in ("MASTER.blend", "README_RENDER.txt")]
rest = sorted([f for f in files if f not in first], key=lambda f: (not f[0].startswith("shots"), f[0]))
groups = [list(first)]; size = sum(s for _, s in first)
for rel, s in rest:
    assert s < LIMIT, ("single file too big for one zip", rel, s)
    if size + s > LIMIT:
        groups.append([]); size = 0
    groups[-1].append((rel, s)); size += s
zips = []
for k, g in enumerate(groups):
    zp = os.path.join(OUT, f"MUMMY_{PART}_farm_{k + 1}of{len(groups)}.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for rel, _ in g:
            z.write(os.path.join(PKG, rel), rel)
    zs = os.path.getsize(zp)
    assert zs < 300 * 1024 * 1024, (zp, zs)
    zips.append(zp)
    print(f"{os.path.basename(zp)}  {zs / 1e6:.1f} MB  {len(g)} files", flush=True)
json.dump([os.path.basename(z) for z in zips], open(os.path.join(OUT, "zips.json"), "w"))
print("NOTE:", NOTE)
