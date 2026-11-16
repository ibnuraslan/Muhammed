# DogShootsOwner_v002c: delivery package (director notes on v002b)

A vertical explainer film (1080×1920, 60 fps, Cycles, hard cuts), frames **1–1592** (26.5 s). The source version
`DogShootsOwner_v001` (Phase 1, passed) is untouched. Built from v002b (untouched). The scripts are in `scripts/`: `01d_wardrobe.py` (new outfits) runs on lib3 and makes lib4, and `02c_v002b.py` (the shot changes) is exec'd by `02_build.py`.

## Files
| File | What it is |
|---|---|
| `DogShootsOwner_v002c_60fps.blend` | The render package: compressed, every texture and the VO packed, one baked camera |
| `DogShootsOwner_v002c_VO.mp3` | The client voiceover (26.0 s). It is also packed in the .blend as a sound strip at frame 1 |
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
B=/opt/blender/blender-5.2.2-linux-x64/blender; S=scripts
$B -b lib3.blend --python $S/02_build.py -- film_vo.blend          # lib3 = 01_lib + 01b_lib2 + 01c_sleepdog
$B -b film_vo.blend --python $S/03_package.py -- DogShootsOwner_v002c_VO.mp3 pkg_big.blend
$B -b pkg_big.blend --python $S/04_shrink_images.py -- /tmp/shrink DogShootsOwner_v002c_60fps.blend
```
Clips are authored at their full 1× length and trimmed at the VO cut. No character animation is time-stretched.

## v002b changes (director notes on v002)
1. **Wardrobe** (every shot with him or the medic):
   - **Owner:** a collared button shirt in red/brown flannel plaid over blue jeans, with a dark leather belt. The MakeHuman `male_casualsuit01` mesh (CC0) was refitted from the medic's body onto his.
   - **Medic:** an EMS-blue shirt over dark charcoal work trousers, with a belt.
   - No one-colour suits remain.
2. **Shot 04, f261–320:** after the flash the shot cuts (marker `04b`, f264) to the paw on the trigger and the gun. The dog startles: head up, tail down.
3. **14a/14b (f1171–1297) and 15a–15d (f1298–1592):** the clean rigged dog replaces the melted-looking scan. It lies asleep on its side with relaxed legs, beside his legs on the bed and in the grass.
   - His palm rests on the dog's back. The build places it with a ray cast on the evaluated dog mesh, then lifts it in 5 mm steps until no hand or forearm vertex is within 3 mm of the dog.
4. **15a (f1298–1352) and 15d (f1508–1592):** he kneels by the dog and looks down.
   - 15a: his arms hang relaxed, then both hands go onto the dog (back and shoulder).
   - 15d: a slow push-in while his hand moves a little on the dog's back as he breathes.
   - The parked ambulance and the kennel/hospital sets are hidden during the clearing shots: they were in view of 15b.
5. **15c (f1449–1507):** a breath and a small head turn toward the dog.

## v002c changes (director notes on v002b; everything else is as approved in v002b)
1. **14a (f1171–1247):** opens on the approved 14b angle (6 % wider) and pushes in continuously into 14b. The crumpled wide of the dog is gone: its face rests forward and is visible.
2. **15a (f1298–1352) and 15d (f1508–1592):** the camera is at his front 3/4 from his right (the dog's head side), low and framed from the knees up. His face reads as he looks down at the dog, and the dog's sleeping face is in the foreground. 15d keeps its slow push-in to the end, which stays on his face. His head bow is lighter (18–24°) so the face shows.
