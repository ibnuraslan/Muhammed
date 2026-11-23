"""Split each delivery zip into git-transport parts (< 95 MB, GitHub's 100 MB file limit) with SHA256SUMS, so the hub
can reassemble the ORIGINAL normal zips byte-for-byte:  cat Antwerp_P1_1_of_3.zip.part* > Antwerp_P1_1_of_3.zip
The user still receives only the normal, independent zips (never these parts).   python3 tools/git_parts.py"""
import os, hashlib
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SRC = os.path.join(ROOT, "delivery"); DST = os.path.join(ROOT, "..", "deliver")
PART = 90 * 1024 * 1024
os.makedirs(DST, exist_ok=True)
sums = []
for z in sorted(f for f in os.listdir(SRC) if f.endswith(".zip")):
    h = hashlib.sha256(); p = os.path.join(SRC, z); k = 0
    with open(p, "rb") as f:
        while True:
            b = f.read(PART)
            if not b:
                break
            h.update(b); k += 1
            open(os.path.join(DST, f"{z}.part{k:02d}"), "wb").write(b)
    sums.append(f"{h.hexdigest()}  {z}")
    print(z, k, "parts", os.path.getsize(p) >> 20, "MB")
open(os.path.join(DST, "SHA256SUMS"), "w").write("\n".join(sums) + "\n")
open(os.path.join(DST, "README.txt"), "w").write(
    "Git transport only. Rebuild each normal zip with:  cat NAME.zip.part* > NAME.zip  then  sha256sum -c SHA256SUMS\n"
    "Deliver the rebuilt .zip files (normal, independent, each < 300 MB). Never deliver the .part files.\n"
    "Note for the user: Extract all zips into ONE folder -> upload the folder -> render MASTER.blend, scene MASTER, frames 1-N\n"
    "(P1: 1-3945, P2: 1-3551, P3: 1-4680).\n")
