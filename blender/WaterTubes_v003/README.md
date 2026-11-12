# WaterTubes v003: acting pass

- `WaterTubes_v003_60fps.blend`: 78 MB, packed and compressed, a normal git file. It opens and renders in factory Blender 5.2 (`package_check_factory_lowres.jpg`).
- Built from the approved v002 (commit c2c606d), with only acting, staging and camera fixes. Story-beat frames are unchanged; `beats.json` is the same as v002. No VO is added (the director retimes it).
- `review/ACTING_notes.md`: every problem found on the v002 half-second sheet, and what was fixed.
- `review/before_v002_halfsec.jpg` and `review/after_v003_halfsec.jpg`: half-second sheets (every 30 frames).
- `review/after_v003_hand_closeups.jpg` and `review/after_v003_nozzle_grip.jpg`: close-ups of the hand contacts.
- Checks: clip_scan has 0 bad ranges, the hand audit has 0 hits, and the camera is never inside geometry.
- Settings and credits are the same as v002 (`SETTINGS.md`, `CREDITS.md`). Build scripts are in `../WaterTubes_v001/scripts/`.

## Known issues
- The other ring segments swell as a time-lapse without the hose visibly attached to each.
- At 0.7 s the right fist sits about 3 cm beside the nozzle before it closes on it.
- The surge foam fills the lower frame for about 0.3 s as the wave passes under the camera at 10.5 s.
- The tube start caps have a small crease.
