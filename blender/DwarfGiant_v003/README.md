# DwarfGiant_v003 — acting pass on the approved v002

This is the same film, timeline and story-beat frames as v002 (`beats.json` is unchanged), with the client's acting notes of Nov 12 applied. Nothing else was changed: same look, same package rules.

- `DwarfGiant_v003_60fps.blend`: 92.6 MB, packed and compressed, a normal git file. Settings are in SETTINGS.md.
- Review files are in `../DwarfGiant_v001/review/`:
  - `ACT_before_v002_0p5s.jpg` and `ACT_after_v003_0p5s.jpg`: half-second sheets.
  - `ACTING_notes.md`: every problem found, with its frames and fix.
  - `ACT_v003_hand_closeups.jpg`: 270×480 close-ups of every hand contact.
  - `ACT_v003_clip_scan.json`: director's `clip_scan.py`.
  - `ACT_v003_hand_audit.txt`: BVH hand audit every 2 frames.
  - `qa_v003.json`: director's `qa_check.py` (intended flags are listed in ACTING_notes.md).

## What changed (see ACTING_notes.md for frames)
- **Clerk:** palms on the desk (`place_hand` onto the ray-cast desk surface); he writes in the ledger with his right hand while his left holds the page.
- **Officer 1:** steadies the real height rod with his left palm flat on the bar while he measures.
- **Hands:** every hand uses the shared `pipeline/hand_poses.py` presets (relaxed, flat_palm, cup_hold) and its joint limits.
- **Standing characters:** everyone breathes and shifts weight. Arms hang close with soft elbows, with no stiff A-pose.
- **Hero's growth:** his feet stay planted in world space, with small re-plant steps, instead of sliding outward as he scales.
- **Ear cup:** elbow out, cupped hand behind the ear, and the face readable.
- **Surgeons:** they hold a sterile hand pose, and Surgeon 1 lays a hand on the drape at the patient's shoulder. The nurse tucks the blanket with both hands.
- **Young and old selves:** they breathe and look at each other.
- **Camera:** it no longer goes inside the desk, the x-ray head, the lying head (now entered through the forehead), an officer's body or the bed rail. There are no wall-filled, shoe-filled or tile-only frames; the wall fly-through opens just before the camera reaches it.

## Known issues (unchanged from v002 unless noted)
- No officer caps. The CC-BY cap import lost its axis conversion; see the v002 README.
- Sleeves and hems don't ride up during the growth.
- During the x-ray beat, Officer 2 stays visible at the left edge, in front of the cutaway card.
- The forehead dive (≈27.5 s) and temple dive (≈3 s) are skin macros of about 5 frames each.
