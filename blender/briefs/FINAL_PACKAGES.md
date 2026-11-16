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
| 07 | ShoeBomber | `claude/beautiful-ptolemy-c5vrcq` | `blender/ShoeBomber_v008/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1469)** — replaces v007 |
| 08 | BeethovenDeaf | `claude/beautiful-ptolemy-c5vrcq` | `blender/BeethovenDeaf_v010/` **acting fixed + synced to your voiceover: READY TO RENDER (frames 1–1435)** |
| 09 | DonationBin | `claude/beautiful-ptolemy-c5vrcq` | `blender/DonationBin_v009/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–2388)** — replaces v008 |
| 10 | BellyFat | `claude/beautiful-ptolemy-c5vrcq` | `blender/BellyFat_v010/` **acting fixed + synced to your voiceover: READY TO RENDER (frames 1–1273)** |
| 11 | WW1Assassination | `claude/beautiful-ptolemy-c5vrcq` | `blender/WW1Assassination_v007/` **checked moving + synced to your voiceover: READY TO RENDER (frames 1–1826)** |
| 12 | NoPilotPlane | `claude/beautiful-ptolemy-c5vrcq` | `blender/NoPilotPlane_v011/` **fixed (watched moving, hands/faces zoomed) + synced to your voiceover: READY TO RENDER (frames 1–3481)**, replaces rejected v010 |
| 13 | FrozenTearsGun | `claude/beautiful-ptolemy-c5vrcq` | `blender/FrozenTearsGun_v010/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1655)** |
| 14 | ElectricianPolice | `claude/beautiful-ptolemy-c5vrcq` | `blender/ElectricianPolice_v010/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1446)** |
| 15 | GameBoxBullet | `claude/beautiful-ptolemy-c5vrcq` | `blender/GameBoxBullet_v010/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1311)** |
| 16 | DrunkTrain | `claude/beautiful-ptolemy-c5vrcq` | `blender/DrunkTrain_v007/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1735)** |
| 17 | ToddlerWell | `claude/beautiful-ptolemy-c5vrcq` | `blender/ToddlerWell_v008/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1728)** |
| 18 | NukedWell | `claude/beautiful-ptolemy-c5vrcq` | `blender/NukedWell_v008/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1541)** |
| 19 | SpeakWithoutSight | `claude/beautiful-ptolemy-c5vrcq` | `blender/SpeakWithoutSight_v006/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1645)** |
| 20 | HeadsetBullet | `claude/beautiful-ptolemy-c5vrcq` | `blender/HeadsetBullet_v008/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1203)** |
| 21 | RingBullet | `claude/beautiful-ptolemy-c5vrcq` | `blender/RingBullet_v008/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1395)** |
| 22 | BelugaRescue | `claude/beautiful-ptolemy-c5vrcq` | `blender/BelugaRescue_v008/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1736)** |
| 23 | CaveRescue | `claude/beautiful-ptolemy-c5vrcq` | `blender/CaveRescue_v010/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–2436)** |
| 24 | RooseveltSpeech | `claude/beautiful-ptolemy-c5vrcq` | `blender/RooseveltSpeech_v011/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1307)** |
| 25 | Tsunami2004 | `claude/beautiful-ptolemy-c5vrcq` | `blender/Tsunami2004_v012/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–2066)** |
| 26 | DwarfGiant | `claude/beautiful-ptolemy-c5vrcq` | `blender/DwarfGiant_v008/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–2083)** |
| 27 | SwedishCoffee | `claude/beautiful-ptolemy-c5vrcq` | `blender/SwedishCoffee_v012/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1995)** |
| 28 | ToucanBeak | `claude/beautiful-ptolemy-c5vrcq` | `blender/ToucanBeak_v009/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1931)** |
| 29 | AIAsleep | `claude/beautiful-ptolemy-c5vrcq` | `blender/AIAsleep_v007/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–2046)** |
| 30 | FanCancer | `claude/beautiful-ptolemy-c5vrcq` | `blender/FanCancer_v011/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–2120)** |
| 31 | PopeShot | `claude/beautiful-ptolemy-c5vrcq` | `blender/PopeShot_v012/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1475)** |
| 32 | GoatOwner | `claude/beautiful-ptolemy-c5vrcq` | `blender/GoatOwner_v009/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1793)** |
| 33 | WaterTubes | `claude/beautiful-ptolemy-c5vrcq` | `blender/WaterTubes_v006/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1769)** |
| 34 | EscapeArtist | `claude/beautiful-ptolemy-c5vrcq` | `blender/EscapeArtist_v010/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–2815)** |
| 35 | TitanicIceberg | `claude/beautiful-ptolemy-c5vrcq` | `blender/TitanicIceberg_v014/` **fixed (watched moving) + synced to your voiceover: READY TO RENDER (frames 1–1464)** |

## Batch 2 (37 films, built to the client's VO, Nov 16)

Same format as above: one packed `.blend` per folder on `claude/beautiful-ptolemy-c5vrcq`, with the VO mp3, `SETTINGS.md`, `CREDITS.md`, `README.md` and `beats.json`. Only rows marked READY have been watched moving start to finish by the director.

| # | Film | Package folder | Status |
|---|---|---|---|
| B18 | PhoneCrazy | `blender/PhoneCrazy_v003/` | **READY TO RENDER (frames 1–1931)**, watched moving |
| B19 | ClosetBathroom | `blender/ClosetBathroom_v003/` | **READY TO RENDER (frames 1–1881)**, watched moving |
| B13 | WomanSuckedOut | `blender/WomanSuckedOut_v003/` | **READY TO RENDER (frames 1–1651)**, watched moving |
| B07 | AlcatrazSpoons | `blender/AlcatrazSpoons_v003/` | **READY TO RENDER (frames 1–2007)**, watched moving |
| B12 | IronRodHead | `blender/IronRodHead_v003/` | **READY TO RENDER (frames 1–1909)**, watched moving |
| B16 | TitanImplosion | `blender/TitanImplosion_v003/` | **READY TO RENDER (frames 1–1825)**, watched moving |
| B14 | MomLiftsCar | `blender/MomLiftsCar_v003/` | **READY TO RENDER (frames 1–1577)**, watched moving |
| B24 | TongueFromArm | `blender/TongueFromArm_v003/` | **READY TO RENDER (frames 1–1404)**, watched moving |
| B29 | FakeDrainRescue | `blender/FakeDrainRescue_v003/` | **READY TO RENDER (frames 1–1752)**, watched moving |
| B20 | SafetyPin | `blender/SafetyPin_v003/` | **READY TO RENDER (frames 1–1857)**, watched moving |
| B35 | BalconyToddler | `blender/BalconyToddler_v003/` | **READY TO RENDER (frames 1–1751)**, watched moving |
| B37 | YardTrench | `blender/YardTrench_v003/` | **READY TO RENDER (frames 1–1825)**, watched moving |
| B11 | FridgeTenYears | `blender/FridgeTenYears_v003/` | **READY TO RENDER (frames 1–1651)**, watched moving |
| B10 | SodaMouse | `blender/SodaMouse_v003/` | **READY TO RENDER (frames 1–1702)**, watched moving |
| B25 | Milgram | `blender/Milgram_v003/` | **READY TO RENDER (frames 1–1982)**, watched moving |
| B03 | WeepingStatue | `blender/WeepingStatue_v003/` | **READY TO RENDER (frames 1–1724)**, watched moving |
| B33 | BogBurials | `blender/BogBurials_v003/` | **READY TO RENDER (frames 1–2187)**, watched moving |
| B26 | TenDimes | `blender/TenDimes_v003/` | **READY TO RENDER (frames 1–1868)**, watched moving |
| B22 | MosquitoDoctor | `blender/MosquitoDoctor_v003/` | **READY TO RENDER (frames 1–2113)**, watched moving |
| B15 | NatashaRyan | `blender/NatashaRyan_v003/` | **READY TO RENDER (frames 1–2136)**, watched moving |
| B04 | LincolnAssassination | `blender/LincolnAssassination_v003/` | **READY TO RENDER (frames 1–1503)**, watched moving |
| B34 | LakeSword | `blender/LakeSword_v003/` | **READY TO RENDER (frames 1–1826)**, watched moving |
