# DrunkTrain_v006: farm package (moving-preview pass on the approved v005)

v006 is v005 after a watch of the film moving, start to finish (director, Nov 14 19:04). Every fault from `LESSONS_LEARNED.md` section 1 that I found is fixed, and his body no longer passes through the rails or the train. Beat frames are unchanged (`beats.json`) and there is no VO. The full fault and fix list is in `review/V006_notes.md`.

## Files
- `DrunkTrain_v006_60fps.blend` (73 MB, compressed, a plain git file with no LFS). Every texture is packed. Factory-startup check: `CAM_Film`, frames 1–2070, 60 fps, f/11, 0 unpacked images.
- `review/preview.mp4`: the moving preview at real speed (`pipeline/preview.py`: every 5th frame, 270×480, Cycles 4 samples + OIDN, frame numbers burned in). `review/pages/p01–p09.jpg` are the contact pages of every preview frame.
  - The preview frames were rendered from the v006 build in stages, then each changed range was re-rendered from the final build.
  - The animation is identical to the packed file. The only exceptions are two small camera re-aims that are not re-rendered in the preview. Both were checked with `qa_check` on the final build:
    - 966–1015: looking down into the coupling gap.
    - 1155–1185: the camera kept in the gap.
- `beats.json`, `SETTINGS.md` (frame range 1–2070, f/11), `CREDITS.md` and `models_credits.json`.

## Checks
All checks ran on the packed file.
- `clip_scan.py` (stock, b6d7900): **0 bad ranges** (`review/clip_scan_v006.json`).
- `body_prop_cross.py` (rails, loco, both wagons, all four wheelsets; Lad), `review/body_prop_cross_v006.json`:
  - v005 had about 100 frames in 6 ranges.
  - v006 has **4 visible frames**:
    - 649, 724 and 754: glancing contact with the loco underframe while he is dragged under it; his head has 0.5–1.3 m of clearance straight up.
    - 1192: a toe on the rail head as he climbs over it.
- `qa_check.py` (c6240b2, step 6, beats.json), `review/qa_v006.json` plus the re-checked ranges `qa_v006_946-1030.json`. The 1140–1215 range was re-checked after the last camera fix and has 0 INSIDE and 0 FILL.
  - **EMPTY:** the wide outdoor shots (ballast or the train side within 3 m counts as a wall), as listed in v005. On every frame he or the witnesses are in view, except the transitions noted in `V006_notes.md`.
  - **BACKHEAD:**
    - 541 (beat 4): the train hits his head as he lies across the rail.
    - 871 (beat 6): he is face down under the train.
    - 1024: WitA turns while running.
  - **INSIDE:** 721 is a single frame under the train during the drag. 1177 and 1183 are fixed (the camera is now in the open coupling gap).
- `limb_check.py`, `review/limb_check_v006.json`:
  - ARMBODY: 3–4 points at the shoulder of all four characters on most frames. These are the known upperarm01 points near the shoulder; nothing is visible in the preview.
  - ARMBACK: Lad's arms flung back by the impact and drag (543–725) and in the replay (1641–1663), and the witnesses' running arm swing (1009–1033).

## Known issues
- **The replay at 26.5–30.5 s is simplified.** It is now Lad in his clothes going limp and rolling with the force in the white studio. There is no x-ray body, no see-through train (rule 13), and no muscles. The x-ray anatomy stays only for beat 10 (23.5–26.5 s), with glass-only forearms. If the director wants the muscle layer back in the replay, the muscle mesh needs re-weighting first.
- There are 4 frames of contact with the rails or train; see above.
- The swig (21.4–21.6 s): the T-shirt bulges where his arm crosses his chest.
- In the low-sample preview, deep shadows between ballast stones look black. Check them in the farm test frames.
- No audio.
