# DogShootsOwner_v002: delivery package (built to the voiceover)

A vertical explainer film (1080×1920, 60 fps, Cycles, hard cuts), frames **1–1592** (26.5 s). The source version
`DogShootsOwner_v001` (Phase 1, passed) is untouched. The build scripts live in `../DogShootsOwner_v001/scripts/`.

## Files
| File | What it is |
|---|---|
| `DogShootsOwner_v002_60fps.blend` | The render package: compressed, every texture and the VO packed, one baked camera |
| `DogShootsOwner_v002_VO.mp3` | The client voiceover (26.0 s). It is also packed in the .blend as a sound strip at frame 1 |
| `beats.json` | Word-timed beats (frame = 1 + round(s × 60)) that the shots are cut to |
| `review/preview.mp4` | Low-res moving preview (every 5th frame, with VO) rendered from this exact package |
| `SETTINGS.md` | The farm render sheet |
| `CREDITS.md` | Third-party asset credits (CC-BY / CC0) |

## Shots (start frames)
01 dog 1 · 02 paw on gun 61 · 03 trigger 176 · 04 shot fired 245 · 05 bullet through seat 321 · 06 into the back 402 ·
07a–c thorax cutaway 453 / 519 / 597 · 08a–b phone call 716 / 805 · 09 ambulance interior 870 · 12 ambulance drives off 949 ·
13a–b animal control kennel 1056 / 1111 · 14a–b dog back with its owner 1171 / 1248 · 15a–d clearing, the dog's death (gentle, off-screen) 1298 / 1353 / 1449 / 1508.
Shots 10 (hospital doorway) and 11 (ambulance toward camera) were dropped because the VO gives them no time.

## Rebuild
```
B=/opt/blender/blender-5.2.2-linux-x64/blender; S=../DogShootsOwner_v001/scripts
$B -b lib3.blend --python $S/02_build.py -- film_vo.blend          # lib3 = 01_lib + 01b_lib2 + 01c_sleepdog
$B -b film_vo.blend --python $S/03_package.py -- DogShootsOwner_v002_VO.mp3 pkg_big.blend
$B -b pkg_big.blend --python $S/04_shrink_images.py -- /tmp/shrink DogShootsOwner_v002_60fps.blend
```
Clips are authored at their full 1× length and trimmed at the VO cut. No character animation is time-stretched.
