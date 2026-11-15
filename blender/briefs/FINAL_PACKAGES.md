# Final RenderStreet packages (35 films, animated CGI look, hands checked)

Each package is a single packed `.blend` (1080×1920, 60 fps, Cycles, AgX Punchy), committed as a normal git file on its branch. Next to it are `SETTINGS.md` (render settings and test frames), `CREDITS.md` (the CC-BY block for the video description), `README.md` (known issues) and `beats.json` (for retiming to your voiceover).

Download a file from GitHub: open the branch → the folder → the .blend → **Download raw file**. Or clone the branch:

```
git clone --single-branch -b <branch> https://github.com/ibnuraslan/Muhammed
```

Voiceover: once you have the mp3, run `blender/pipeline/transcribe.py` and `retime_to_vo.py` with the film's `beats.json`, or send it to me and I'll do it.

**Synced to voiceover:** 01–10 (render these versions; the mp3 is in each folder).

| # | Film | Branch | Package folder |
|---|---|---|---|
| 01 | EarInArm | `claude/beautiful-ptolemy-c5vrcq` | `blender/EarInArm_v011/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1572)** — replaces v010 |
| 02 | MonkeyHeadTransplant | `claude/beautiful-ptolemy-c5vrcq` | `blender/MonkeyHeadTransplant_v012/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1656)** |
| 03 | LegoInNose | `claude/beautiful-ptolemy-c5vrcq` | `blender/LegoInNose_v011/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–2036)** |
| 04 | StanleyCup | `claude/beautiful-ptolemy-c5vrcq` | `blender/StanleyCup_v009/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1386)** — replaces v008 |
| 05 | SurgeonBrandsLivers | `claude/beautiful-ptolemy-c5vrcq` | `blender/SurgeonBrandsLivers_v011/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1644)** |
| 06 | PrisonKeyCake | `claude/beautiful-ptolemy-c5vrcq` | `blender/PrisonKeyCake_v010/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1836)** |
| 07 | ShoeBomber | `claude/beautiful-ptolemy-c5vrcq` | `blender/ShoeBomber_v007/` **ON HOLD: DO NOT RENDER (moving-preview review found body/hand/face faults; fix in progress)** |
| 08 | BeethovenDeaf | `claude/beautiful-ptolemy-c5vrcq` | `blender/BeethovenDeaf_v010/` **acting fixed + synced to your voiceover: READY TO RENDER (frames 1–1435)** |
| 09 | DonationBin | `claude/beautiful-ptolemy-c5vrcq` | `blender/DonationBin_v008/` **ON HOLD: DO NOT RENDER (moving-preview review found body/hand/face faults; fix in progress)** |
| 10 | BellyFat | `claude/beautiful-ptolemy-c5vrcq` | `blender/BellyFat_v010/` **acting fixed + synced to your voiceover: READY TO RENDER (frames 1–1273)** |
| 11 | WW1Assassination | `claude/beautiful-ptolemy-c5vrcq` | `blender/WW1Assassination_v007/` **checked moving + synced to your voiceover: READY TO RENDER (frames 1–1826)** |
| 12 | NoPilotPlane | `claude/connect12-no-pilot-plane` | `blender/NoPilotPlane_v007/` **acting fixed, approved, final commit 800e346 (VO sync when your voiceover arrives)** |
| 13 | FrozenTearsGun | `claude/beautiful-ptolemy-c5vrcq` | `blender/FrozenTearsGun_v010/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1655)** |
| 14 | ElectricianPolice | `claude/beautiful-ptolemy-c5vrcq` | `blender/ElectricianPolice_v010/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1446)** |
| 15 | GameBoxBullet | `claude/beautiful-ptolemy-c5vrcq` | `blender/GameBoxBullet_v010/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1311)** |
| 16 | DrunkTrain | `claude/connect16-drunk-train` | `blender/DrunkTrain_v005/` **acting fixed, approved, final commit 66c7cc0 (VO sync when your voiceover arrives)** |
| 17 | ToddlerWell | `claude/beautiful-ptolemy-c5vrcq` | `blender/ToddlerWell_v008/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1728)** |
| 18 | NukedWell | `claude/beautiful-ptolemy-c5vrcq` | `blender/NukedWell_v008/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1541)** |
| 19 | SpeakWithoutSight | `claude/beautiful-ptolemy-c5vrcq` | `blender/SpeakWithoutSight_v006/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1645)** |
| 20 | HeadsetBullet | `claude/beautiful-ptolemy-c5vrcq` | `blender/HeadsetBullet_v008/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1203)** |
| 21 | RingBullet | `claude/beautiful-ptolemy-c5vrcq` | `blender/RingBullet_v008/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1395)** |
| 22 | BelugaRescue | `claude/beautiful-ptolemy-c5vrcq` | `blender/BelugaRescue_v008/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1736)** |
| 23 | CaveRescue | `claude/connect23-cave-rescue` | `blender/CaveRescue_v006/` **acting fixed, approved, final commit ee86ff4 (VO sync when your voiceover arrives)** |
| 24 | RooseveltSpeech | `claude/beautiful-ptolemy-c5vrcq` | `blender/RooseveltSpeech_v011/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1307)** |
| 25 | Tsunami2004 | `claude/connect25-tsunami-2004` | `blender/Tsunami2004_v005/` **acting fixed, approved (VO sync when your voiceover arrives)** |
| 26 | DwarfGiant | `claude/connect26-dwarf-giant` | `blender/DwarfGiant_v003b/` **acting fixed, approved, final commit d1c0cfc (VO sync when your voiceover arrives)** |
| 27 | SwedishCoffee | `claude/beautiful-ptolemy-c5vrcq` | `blender/SwedishCoffee_v012/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1995)** |
| 28 | ToucanBeak | `claude/connect28-toucan-beak` | `blender/ToucanBeak_v004b/` **acting fixed, approved, final commit b38c05b (VO sync when your voiceover arrives)** |
| 29 | AIAsleep | `claude/beautiful-ptolemy-c5vrcq` | `blender/AIAsleep_v007/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–2046)** |
| 30 | FanCancer | `claude/connect30-fan-cancer` | `blender/FanCancer_v004/` **acting fixed, approved, final commit a270af3 (VO sync when your voiceover arrives)** |
| 31 | PopeShot | `claude/beautiful-ptolemy-c5vrcq` | `blender/PopeShot_v012/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1475)** |
| 32 | GoatOwner | `claude/beautiful-ptolemy-c5vrcq` | `blender/GoatOwner_v009/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1793)** |
| 33 | WaterTubes | `claude/beautiful-ptolemy-c5vrcq` | `blender/WaterTubes_v006/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1769)** |
| 34 | EscapeArtist | `claude/connect34-escape-artist` | `blender/EscapeArtist_v006b/` **acting fixed, approved, final commit 031e503 (VO sync when your voiceover arrives)** |
| 35 | TitanicIceberg | `claude/beautiful-ptolemy-c5vrcq` | `blender/TitanicIceberg_v014/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1464)** |
