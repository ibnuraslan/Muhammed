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
| 01 | EarInArm | `claude/beautiful-ptolemy-c5vrcq` | `blender/EarInArm_v008/` **synced to your voiceover** |
| 02 | MonkeyHeadTransplant | `claude/beautiful-ptolemy-c5vrcq` | `blender/MonkeyHeadTransplant_v007/` **synced to your voiceover** |
| 03 | LegoInNose | `claude/beautiful-ptolemy-c5vrcq` | `blender/LegoInNose_v007/` **synced to your voiceover** |
| 04 | StanleyCup | `claude/beautiful-ptolemy-c5vrcq` | `blender/StanleyCup_v006/` **ON HOLD: acting fix in progress, do not render** |
| 05 | SurgeonBrandsLivers | `claude/beautiful-ptolemy-c5vrcq` | `blender/SurgeonBrandsLivers_v008/` **ON HOLD: acting fix in progress, do not render** |
| 06 | PrisonKeyCake | `claude/beautiful-ptolemy-c5vrcq` | `blender/PrisonKeyCake_v006/` **ON HOLD: acting fix in progress, do not render** |
| 07 | ShoeBomber | `claude/beautiful-ptolemy-c5vrcq` | `blender/ShoeBomber_v005/` **ON HOLD: acting fix in progress, do not render** |
| 08 | BeethovenDeaf | `claude/beautiful-ptolemy-c5vrcq` | `blender/BeethovenDeaf_v010/` **acting fixed + synced to your voiceover: READY TO RENDER (frames 1–1435)** |
| 09 | DonationBin | `claude/beautiful-ptolemy-c5vrcq` | `blender/DonationBin_v005/` **ON HOLD: acting fix in progress, do not render** |
| 10 | BellyFat | `claude/beautiful-ptolemy-c5vrcq` | `blender/BellyFat_v010/` **acting fixed + synced to your voiceover: READY TO RENDER (frames 1–1273)** |
| 11 | WW1Assassination | `claude/connect11-ww1-assassination` | `blender/WW1Assassination_v004/` |
| 12 | NoPilotPlane | `claude/connect12-no-pilot-plane` | `blender/NoPilotPlane_v006/` |
| 13 | FrozenTearsGun | `claude/connect13-frozen-tears-gun` | `blender/FrozenTearsGun_v005/` |
| 14 | ElectricianPolice | `claude/connect14-electrician-police` | `blender/ElectricianPolice_v005/` |
| 15 | GameBoxBullet | `claude/connect15-game-box-bullet` | `blender/GameBoxBullet_v008/` **acting fixed, approved (VO sync when your voiceover arrives)** |
| 16 | DrunkTrain | `claude/connect16-drunk-train` | `blender/DrunkTrain_v004/` |
| 17 | ToddlerWell | `claude/connect17-toddler-well` | `blender/ToddlerWell_v003/` |
| 18 | NukedWell | `claude/connect18-nuked-well` | `blender/NukedWell_v003/` |
| 19 | SpeakWithoutSight | `claude/connect19-speak-without-sight` | `blender/SpeakWithoutSight_v002/` |
| 20 | HeadsetBullet | `claude/connect20-headset-bullet` | `blender/HeadsetBullet_v006/` **acting fixed, approved (VO sync when your voiceover arrives)** |
| 21 | RingBullet | `claude/connect21-ring-bullet` | `blender/RingBullet_v005/` |
| 22 | BelugaRescue | `claude/connect22-beluga-rescue` | `blender/BelugaRescue_v004/` |
| 23 | CaveRescue | `claude/connect23-cave-rescue` | `blender/CaveRescue_v004/` |
| 24 | RooseveltSpeech | `claude/connect24-roosevelt-speech` | `blender/RooseveltSpeech_v006/` |
| 25 | Tsunami2004 | `claude/connect25-tsunami-2004` | `blender/Tsunami2004_v004/` |
| 26 | DwarfGiant | `claude/connect26-dwarf-giant` | `blender/DwarfGiant_v002/` |
| 27 | SwedishCoffee | `claude/connect27-swedish-coffee` | `blender/SwedishCoffee_v004/` |
| 28 | ToucanBeak | `claude/connect28-toucan-beak` | `blender/ToucanBeak_v003/` |
| 29 | AIAsleep | `claude/connect29-ai-asleep` | `blender/AIAsleep_v003/` |
| 30 | FanCancer | `claude/connect30-fan-cancer` | `blender/FanCancer_v002/` |
| 31 | PopeShot | `claude/connect31-pope-shot` | `blender/PopeShot_v003/` |
| 32 | GoatOwner | `claude/beautiful-ptolemy-c5vrcq` | `blender/GoatOwner_v003/` (director fix of v002) |
| 33 | WaterTubes | `claude/connect33-water-tubes` | `blender/WaterTubes_v002/` |
| 34 | EscapeArtist | `claude/connect34-escape-artist` | `blender/EscapeArtist_v003/` |
| 35 | TitanicIceberg | `claude/connect35-titanic-iceberg` | `blender/TitanicIceberg_v004/` **acting fixed, approved (VO sync when your voiceover arrives)** |
