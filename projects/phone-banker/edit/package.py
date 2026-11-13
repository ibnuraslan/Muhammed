"""Package the film for hand delivery: zips of at most 380 MB, every one holding the same top folder
phone_banker_film/ (with out/blend/... inside), so extracting all of them into one place rebuilds the tree.
  python edit/package.py  -> out/package/phone_banker_partXXofNN.zip, phone_banker_audio.zip,
                             MERGE_PHONE_BANKER.bat, README.txt, manifest.txt
Files are stored, not deflated: the .blend files are already zstd-compressed and the textures are JPEG/PNG."""
import os, sys, zipfile, glob, hashlib
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "out", "package"); os.makedirs(OUT, exist_ok=True)
LIMIT = 380 * 2**20; HEAD = 2 * 2**20                     # room for zip headers / central directory
TOP = "phone_banker_film"
files = []
for d in ("film", "sting", "intro", "ch1", "ch2", "ch3", "textures"):
    for p in sorted(glob.glob(os.path.join(ROOT, "out", "blend", d, "**", "*"), recursive=True)):
        if os.path.isfile(p) and not p.endswith((".log", ".lock", ".blend1", "jobs.txt")) and ".part" not in p:
            files.append(p)
big = [p for p in files if os.path.getsize(p) > LIMIT - HEAD]
if big:
    sys.exit(f"files larger than one part: {big}")
# first-fit decreasing into bins of LIMIT
bins = []
for p in sorted(files, key=os.path.getsize, reverse=True):
    s = os.path.getsize(p) + 200 + len(p)
    for b in bins:
        if b[0] + s <= LIMIT - HEAD:
            b[0] += s; b[1].append(p); break
    else:
        bins.append([s, [p]])
N = len(bins)
for z in glob.glob(os.path.join(OUT, "phone_banker_part*.zip")):
    os.remove(z)
BAT = r"""@echo off
setlocal enabledelayedexpansion
rem Rebuilds phone_banker_film\ from the %N% parts (Windows 10/11 built-in tar reads .zip files).
cd /d "%~dp0"
set /a have=0
for %%f in (phone_banker_part*of%NN%.zip) do set /a have+=1
if not "!have!"=="%N%" (
  echo Found !have! of %N% parts. Put all phone_banker_partXXof%NN%.zip files next to this script, then run it again.
  pause & exit /b 1
)
for %%f in (phone_banker_part*of%NN%.zip) do (
  echo Extracting %%f ...
  tar -xf "%%f"
  if errorlevel 1 ( echo FAILED on %%f - download that part again. & pause & exit /b 1 )
)
set /a n=0
for /r "phone_banker_film" %%f in (*) do set /a n+=1
echo Files in phone_banker_film: !n! (expected %COUNT%)
if "!n!"=="%COUNT%" (
  echo OK - open phone_banker_film\out\blend\film\phone_banker_film.blend
) else (
  echo MISMATCH - a part is incomplete; download it again and re-run this script.
)
pause
"""
README = """THE PHONE THAT KILLED A BANKER - render package
====================================================
%N% parts (phone_banker_part01of%NN%.zip ... phone_banker_part%NN%of%NN%.zip) + phone_banker_audio.zip

1. Put all %N% part zips and MERGE_PHONE_BANKER.bat in one folder.
2. Double-click MERGE_PHONE_BANKER.bat. It extracts every part into phone_banker_film\\ and checks that all
   %COUNT% files arrived. (Without Windows: extract every zip into the same folder; they share the top folder.)
3. Upload or open phone_banker_film\\out\\blend\\film\\phone_banker_film.blend and render the animation
   (frames 1-%FRAMES%, 1920x816, 24 fps, Cycles 32 samples, denoise). Keep the folder structure as it is: the film file
   links the shot files in out\\blend\\<part>\\ and the textures in out\\blend\\textures\\ by relative paths.

Audio (phone_banker_audio.zip): the full mix with voice and without voice, WAV 48 kHz and MP3 previews, exactly the
length of the film; lay either one under the rendered frames from frame 1.
"""
nn = f"{N:02d}"
for i, (sz, ps) in enumerate(bins, 1):
    zp = os.path.join(OUT, f"phone_banker_part{i:02d}of{nn}.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
        for p in sorted(ps):
            z.write(p, os.path.join(TOP, os.path.relpath(p, ROOT)))
    print(f"[zip] {os.path.basename(zp)} {os.path.getsize(zp) / 2**20:.1f} MB, {len(ps)} files", flush=True)
count = len(files)
frames = 9247
bat = BAT.replace("%N%", str(N)).replace("%NN%", nn).replace("%COUNT%", str(count))
open(os.path.join(OUT, "MERGE_PHONE_BANKER.bat"), "w", newline="\r\n").write(bat)
open(os.path.join(OUT, "README.txt"), "w", newline="\r\n").write(README.replace("%N%", str(N)).replace("%NN%", nn).replace("%COUNT%", str(count)).replace("%FRAMES%", str(frames)))
aud = os.path.join(OUT, "phone_banker_audio.zip")
with zipfile.ZipFile(aud, "w", zipfile.ZIP_DEFLATED) as z:
    for f in ("phone_banker_AUDIO_with_voice.wav", "phone_banker_AUDIO_no_voice.wav", "phone_banker_AUDIO_with_voice.mp3", "phone_banker_AUDIO_no_voice.mp3"):
        z.write(os.path.join(ROOT, "out", "deliver", f), os.path.join("phone_banker_audio", f))
print(f"[zip] phone_banker_audio.zip {os.path.getsize(aud) / 2**20:.1f} MB", flush=True)
with open(os.path.join(OUT, "manifest.txt"), "w") as m:
    for i, (sz, ps) in enumerate(bins, 1):
        for p in sorted(ps):
            m.write(f"part{i:02d}\t{os.path.getsize(p)}\t{os.path.join(TOP, os.path.relpath(p, ROOT))}\n")
print(f"[pkg] {N} parts, {count} files", flush=True)
