# DrunkTrain_v008: the from-scratch rebuild (batch 1, film 16)

**Status: CLIENT-APPROVED as is.** The client approved this exact build on Nov 26, 2026 (relayed by the director and confirmed by the user). A fresh reviewer had graded the final preview FAIL; those notes are kept below for the record. The delivered `.blend` is the exact file `review/preview.mp4` was rendered from (md5 `5f04c2e56dba8f4d60a475024c96744c`).

One drunk man, one rail worker, one cargo train, one continuous camera. It is built to the client's VO (the DrunkTrain v007 recording), frames **1–1735** at 60 fps, so no retime is needed. The beat frames are in `beats.json`.

The scripts are in `scripts/`:
- 00: the tee texture with the logo
- 01: the build
- 02: the animation
- 03: packaging

## The film
- **f1–96:** he staggers along the ballast beside the track with a green bottle in his left hand (Child Of the wrist, solved wrap grip).
- **f94–150:** the bottle slips and lands on its side on the ballast. The camera follows it down while he collapses off screen.
- **f150–440:** he lies across the track, outside the rails, with only the back of his head on the rail. He snores and breathes. A low shot runs along the rail as the cargo train's headlight grows behind him.
- **f440–537:** the camera crosses to the far side of the track. The locomotive covers him before contact, so the hit itself is never shown.
- **f537–650:** the locomotive and the wagon's front bogie pass over him. He is hidden here and the train always covers him.
- **f650–860:** he is dragged under the open middle of the first container wagon, log-rolling between the rails. The train brakes (sparks) and stops.
- **f860–1010:** the rail worker in hi-vis orange overalls runs up. He raises both hands in shock.
- **f1010–1118:** the man rolls out from under the wagon, sits up and stands. The worker steps back.
- **f1118–1186:** he stands dazed with loose arms. Then a short white flash.
- **f1186–1513:** the explainer, on a sky-blue gradient: a red muscle bundle hangs between two bone anchors and sways loosely ("completely loose"). An orange force arrow pushes it and it bows *with* the push, then springs back ("moved with it").
- **f1513–1735:** a flash back to the real scene. He walks along the stopped train, raises his right palm to look at the small cuts, and grins.

## Logo
DA KRAS FILMS is printed in white on his red tee. It reads in full in f1–90, **f1116–1182** and **f1520–1735** (about 3.6 s).

## Checks on the final animation (the same scene that was packed)
- **clip_scan:** 0 bad ranges (`review/clip_scan.json`).
- **limb_check:** only ARMBODY "2 pts" upper-arm points at the shoulder, which is the documented false positive (`review/limb_check.json`).
- **body_prop_cross (Bottle):** only the palm skin touching the bottle at the grip, in f1–91. The bottle-through-thigh crossing found in round 2 is fixed.
- **qa_check:**
  - EMPTY: the character-free bottle macro and the explainer.
  - INSIDE and CAMJUMP: only inside the two white flashes.
  - PROPMOVE: the bottle drop, the train and the arrow.

## Open faults (fresh reviewer, final preview), with my read
1. **10.6–10.8 s:** the camera drops past a container wall, so a flat green wall with one pale panel fills the frame for about 0.3 s. *Real.*
2. **7.6–7.9 s:** the camera rises from rail level to above the track quickly. It reads as a whip. *Real (minor).*
3. **11.5 s and 12.5 s:** he "flattens into a sliver". This is the log-roll seen edge-on behind the near rail head. clip_scan finds no body-through-rail. *Disputed.*
4. **17.25–17.33 s:** a "teleport". This is the roll-out over the rail between preview samples (one roll is 6 preview frames). *Disputed, but it reads fast.*
5. **25.3–26.6 s:** a slow walk toward the camera with hanging arms, which reads as a near-hold. *Minor.*
6. Others: the arrowhead touches the bundle surface at 23.3–23.9 s; the neck on the rail looks pressed (intended contact).

## Render check: PASS
I opened the exact packed `DrunkTrain_v008_60fps.blend` (74 MB) with `blender --factory-startup -b`:
- No errors and no warnings in the console when it opens.
- 0 linked libraries, 0 unpacked images, the VO sound packed, 0 drivers and 0 text blocks.
- Camera `CAM_Film`, 1080×1920 at 100 %, 60 fps, frames 1–1735, PNG to `//render/DrunkTrain_v008_####.png`, and the `VO` strip.
- Full-resolution test frames at 64 adaptive samples on a 4-core CPU: f300 123 s, f900 171 s, f1650 189 s. None is black, empty or pink.

Render frames **1–1735** at 60 fps and join them with `DrunkTrain_v008_VO.mp3` from frame 1. The render sheet is `SETTINGS.md`. The credits are in `CREDITS.md`, including the CC-BY models that must be credited.
