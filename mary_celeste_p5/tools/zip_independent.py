"""Pack a delivery folder into independent normal .zip files, each under LIMIT and each holding whole files with the
folder structure kept (MASTER.blend, shots/Sxx.blend), so extracting every zip into one folder rebuilds the folder.
Every zip opens on its own with Windows "Extract All".

    python3 tools/zip_independent.py <folder> <out prefix> [limit MB]
"""
import os, sys, zipfile

src, prefix = os.path.abspath(sys.argv[1]), sys.argv[2]
LIMIT = float(sys.argv[3] if len(sys.argv) > 3 else 290) * 1024 * 1024
files = []
for root, _, fs in os.walk(src):
    for f in fs:
        p = os.path.join(root, f); files.append((os.path.getsize(p), os.path.relpath(p, src)))
big = [r for s, r in files if s > LIMIT]
if big:
    raise SystemExit(f"files over the limit, cannot ship whole: {big}")
# MASTER.blend first, then largest-first into the first zip with room (first-fit decreasing)
files.sort(key=lambda x: (x[1] != "MASTER.blend", -x[0]))
bins = []
for s, r in files:
    for b in bins:
        if b[0] + s + 1e6 < LIMIT:
            b[0] += s; b[1].append(r); break
    else:
        bins.append([s, [r]])
n = len(bins)
for i, (s, rels) in enumerate(bins, 1):
    z = f"{prefix}_{i}of{n}.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as zf:
        for r in sorted(rels):
            zf.write(os.path.join(src, r), r)
    print(f"{os.path.basename(z)}  {os.path.getsize(z) / 1048576:.1f} MiB  {len(rels)} files: {' '.join(sorted(rels))}")
