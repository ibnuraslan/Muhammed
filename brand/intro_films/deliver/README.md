# Farm delivery: Seldom intro films 6 (Ice Station) and 8 (The Archivist)

Each film is ONE normal zip (143 MB, under 300 MB), stored here in 90 MB parts **only to get past git's file limit**.
Rebuild before sending; the user only ever gets the plain .zip:

    cat seldom_intro_film6.zip.part* > seldom_intro_film6.zip && sha256sum -c seldom_intro_film6.zip.sha256
    cat seldom_intro_film8.zip.part* > seldom_intro_film8.zip && sha256sum -c seldom_intro_film8.zip.sha256

Zip contents: `MASTER.blend` (scene MASTER: the 4 shot scenes linked from `//shots/S0x.blend`, scene camera set,
colour management copied from the shots, output `//frames/`), `shots/S01-S04.blend` (packed, textures <= 2K),
`filmN_shotlist.txt/.csv` (CapCut), `READ_ME_FIRST.txt`.

Note to send: "Extract all zips into ONE folder → upload the folder → render MASTER.blend, scene MASTER, frames 1–288."

Settings: 2560x1440, 24 fps, 288 frames (12 s), Cycles 64 spp adaptive + OIDN, motion blur.

Fresh-unzip test (both films): plain `unzip` into an empty folder → MASTER.blend opened, no missing files, camera
present → frames 1 / 144 / 288 rendered through the sequencer (at 25 % size to save CPU; `unzip_test_frames_25pct.jpg`).
Colour check: MASTER frame 1 vs S01.blend frame 1 rendered directly, mean abs difference 0.37/255 (film 8) and
0.39/255 (film 6), i.e. sampling noise only.

Motion: camera moves (push-ins, a lateral drift, handheld noise), blowing snow, breath and dust puffs, the stuck
drawer's shudder. The people hold the approved key-frame poses within each shot (no body animation).
Rebuild from source: `tools/pack_intro.py` (FILM=6|8 SHOT=1..4 PACKDIR=..., then MASTER=1).
