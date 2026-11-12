# DrunkTrain_v005: farm package (the acting pass on the approved v004)

v005 is v004 with only the acting pass from `briefs/ACTING_FIX_04-10.md` (client, Nov 12). The look, assets, beat frames and length are unchanged.
- The full list of what was wrong and how it was fixed is in `review/ACTING_notes.md` (19 items).
- `review/BEFORE_v004_sheet_0.5s.jpg` and `review/AFTER_v005_sheet_0.5s.jpg` are the half-second sheets (every 30 frames, 270×480, 8 samples).
- `clip_scan.py` reports 0 bad ranges. The hand audit has 2 single-frame brushes. `review/v005_hand_closeups.jpg` has close-ups of every hand contact.
- The camera is never inside a body: the x-ray studio is now a bubble that grows out of his chest and later collapses back into it.

- `DrunkTrain_v005_60fps.blend` (73 MB, compressed, a normal git file with no LFS): the self-contained scene. Every texture is packed.
- `beats.json`: the start frame of each of the 12 beats. There is no voiceover yet, so the film is built to the brief's target beat times. When the VO arrives, retime with `pipeline/retime_to_vo.py`, using these frames as the old anchors and the VO's word times as the new ones.
- `SETTINGS.md`: render settings, test frames and the measured frame cost. `CREDITS.md`: the CC-BY block for the video description (`models_credits.json` has the full metadata).
- `package_check_f760_lowres.jpg` and `package_check_f1700_lowres.jpg`: 25 %, 8-sample frames rendered from this packed file opened in factory Blender. They show the package works; they are not a quality reference.
- `review/`: the 1 s sheet in this look, hand close-ups and the hand audit.

The source is `../DrunkTrain_v001/scripts`. Build order: `01_build_people.py`, then `02_build_scene.py` (which runs `02b_fit_muscles.py`), then `03_animate.py` (which runs `03b_fx_camera.py`), then `pipeline/anim_look.py`, then `05_package.py`. The hand checks are `06_hand_audit.py` and `07_hand_closeups.py`. `04_audit.py` is the audit.

## Beats (frame = 1 + t × 60)
1 stumble 0.0 · 2 head on the rail 2.5 · 3 train rushing 5.5 · 4 impact and spin 9.0 · 5 dragged beneath 11.0 · 6 screech to a stop 14.5 · 7 witnesses 17.0 · 8 stands up 19.5 · 9 flash-back swig 21.0 · 10 x-ray, loose muscles 23.5 · 11 slow-motion replay with force arrows 26.5 · 12 walks off, cuts on his palm 31.0

## Known issues
- **Brief contacts.** He touches the loco under-gear in 5 sampled frames during the drag and the crawl-out (11.1, 12.6, 19.6 s). They are a few centimetres and in dark frames. The camera passes 6 mm from the under-frame at 13.7 s.
- **Under-gear opened up.** To give a body-sized gap between the rails, the locomotive's low centre under-gear and the bottom plate of its pilot were removed, and its wheel discs were replaced by our spinning wheelsets. This is not visible in the shots.
- **Feet in the air.** His feet are in the air for about a second during the sit and flop (3.8–5.0 s). While he lies on the ballast, his heels rest about 3 cm above the base plane, covered by loose stones.
- **Small details.** The final grin is subtle. The three palm cuts are small and only read at full resolution.
- **Studio whip.** The whip out of the x-ray studio (30.6–31.0 s) passes 3 sparse cyan frames.
- **No audio.** There is no audio in the file.
