# DwarfGiant_v007c: theatre shot 1601–1716 re-staged

This is the same film, timeline and story-beat frames as v002 (`beats.json` is unchanged), with the client's acting notes of Nov 12 applied. Nothing else was changed: same look, same package rules.

- `DwarfGiant_v007c_60fps.blend`: 92.6 MB, packed and compressed, a normal git file. Settings are in SETTINGS.md.
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

## v007c changes (director review of v007b)
1601–1716 is now a side medium shot from the head end of the bed: his face on the pillow in front, the masked surgeon beyond him with both arms visible. Nothing passes through the bed rails. The second surgeon and the nurse are off for this shot. The drape stays one colour until the cut at 1717. Only 1596–1721 was re-rendered from this exact package for `review/preview.mp4`.

## v007b changes (director review of v007)
Beat frames and `beats.json` are unchanged. The changed ranges were re-rendered from this exact package for `review/preview.mp4`: 311–601, 691–876, 1236–1481, 1596–1721 and 1856–1900.
- **1601–1716:** both surgeons are framed whole with their arms (no hand without a body). The standing surgeon works with his hands from 1600.
- **1241–1300:** the POV is 1 s, with nobody behind the officer's head. 1301–1481 is the ear-cup medium shot, starting earlier.
- **813–874:** the mirror shot is cut and replaced by a close-up of his surprised face.
- **Slow push-ins:** on 313–440, 441–600 (as he grows) and 696–812.
- **1858–1899:** the normal man's fringe is moved off his eye.

## v007 changes (director review of v006)
Story-beat frames are unchanged and no VO is added. The preview is `review/preview.mp4`, from this file: every shot watched, and every first frame after a cut re-rendered and watched after the focus fix.
- **Theatre (1482–1857):**
  - 1482–1545: the patient's face on the bed.
  - 1546–1600: the surgeon in green scrubs, eyes over the mask, laying his hand on the drape.
  - 1601–1716: side medium of the patient and surgeons.
  - 1717–1790: the second surgeon working with both hands.
  - 1791–1857: the patient's face.
  - It then cuts to the two men's faces.
- **Office:**
  - 1151–1210: the officer's face looking up, 1 s.
  - 1211–1240: the hero's face looking down.
  - 241–312: the two-shot cut to 1.2 s.
- **Brain inset:** a dark slate card; the orange pituitary is kept.
- **Focus:** the camera focus is keyed on every frame. Keys every 4 frames lagged after each cut and blurred the first frame.

## v006 changes (director review of v005)
Story-beat frames are unchanged and no VO is added. The preview is `review/preview.mp4`, rendered from this exact file.

Shots, joined by 18 clean cuts:

| Frames | Shot |
|---|---|
| 1–150 | Office |
| 151–240 | Brain inset |
| 241–371 | The officer and the boy, faces |
| 372–440 | His face |
| 441–600 | Locked shot by the height rod as he shoots up |
| 601–695 | His surprised face |
| 696–812 | Full body at the desk |
| 813–874 | The mirror |
| 875–1150 | Second beat: he lifts his hands and looks at them |
| 1151–1240 | The officers look up at him |
| 1241–1365 | His-eyes POV |
| 1366–1481 | Ear cup |
| 1482–1600 | Theatre, wide |
| 1601–1716 | Side medium: patient and surgeons |
| 1717–1857 | Patient's face, blanket and surgeon |
| 1858–1899 | The normal man's face |
| 1900–1940 | The tall man's face |
| 1941–1999 | Headstones |
| 2000–2340 | The two figures at sunset |

- **Growth:** he shoots up between 500 and 600 in one locked shot by the height rod, past the officer. The shot is framed by his face before and after.
- **Second beat:** he lifts his hands and looks at them, then the camera cuts to the officers reacting.
- **Brain inset:** centred and whole, with a slow push. The pituitary glows warm orange.
- **Dust specks:** off.
- **Opening:** the clerk's hand no longer shows; it was a floating hand at the frame edge.
- **Mirror:** his head is out of frame.

## v005 changes (director review of v004)
Story-beat frames are unchanged and no VO is added. The film is now a series of shots joined by **clean cuts**, so the camera no longer flies into heads, walls or windows. The preview is `review/preview.mp4`, rendered from this exact file.

Shots: office 1–150 | brain inset 151–240 | office, growth 241–812 | mirror 813–874 | office, second beat 875–1240 | his-eyes POV 1241–1365 | ear-cup medium shot 1366–1481 | theatre 1482–1640 | surgeons at the head of the bed 1641–1716 | patient and nurse 1717–1940 | cemetery and ending 1941–2340.

- **x-ray:** no see-through body in either beat. The real man is shown, and the spine and hormone stream are gone.
- **Brain:** one 1.5 s brain inset on a neutral card (151–240, f/22, sharp). There is no surgical brain macro and no tweezers without a hand.
- **Ear cup:** a medium shot with his hand at his own ear.
- **Growth:** full-body framing with his face (690–812), instead of leg and arm macros.
- **Arms:** the hero's hanging arms are closer to his sides (no 30° A-pose).
- **POV:** no blurred-vision POV.
- **Cuts instead of pans:** the empty ceiling and wall pans (1366, 1461–1491), the theatre lamp and window crane (1941–1996) and the fly into the patient's head (1621–1646) are all replaced by cuts.

## v004 changes (moving preview of v003b, watched page by page)
Story-beat frames are unchanged and no VO is added. The preview is `review/preview.mp4` (every 5th frame, 12 fps, real speed), rendered from this exact file.
- **Tongue (f836–891):** the hero's tongue poked out of his mouth when his head turned. Tongue meshes are now off for render on every character.
- **Folded leg (f466–476):** the cutaway card sliced through his shins. The card now sits behind the whole body in both x-ray beats.
- **x-ray:**
  - The bend deformer threw two upper-spine pieces out of the body (f1101–1236). They also rendered as a black neck column. Both are off.
  - Both cutaways render only the x-ray figure, brain and spine while the card is opaque, with 8-frame card fades (470–478 and 1232–1240).
- **Eyes:** the director's eye fix is applied, so the cornea no longer blocks the iris.
- **Focus:**
  - The temple dive (166–205) and the brain macro (1650–1712) are at f/64.
  - The blurred-vision POV is cut to about 0.25 s.
- **Camera:**
  - It swings wide of the head at f830.
  - During the ear cup it is in front of the face, so the hand stays behind the head instead of filling the lens.
  - It frames the lying patient from the feet side, so the face is upright.
  - It stays clear of the nurse's hands at f1740.
  - The ending arcs to a front three-quarter, so both faces read.
- **Nurse:** she keeps the sterile pose; her blanket tuck hovered.
- **Package:** saved without persistent data.

## v003b changes (director review of v003)
Story-beat frames are unchanged; v003 is otherwise kept as is.
- **x-ray slab (1170–1235):** the camera-attached cutaway card sat behind the hero, so the office floor, wall and desk crossed it and showed a straight-edged translucent slab. While the card is fully opaque (1091–1231), only the x-ray figure and spine render (`scripts/03e_xray_clean.py`), so the cutaway is clean.
- **Blank grey-blue fade (1245–1262):** the card used to fade over 22 frames while the camera flew off the hero toward the POV. It now fades in 8 frames (1232–1240), while the body is still framed. The x-ray ends at 1240 and the normal hero is back at 1241.
- **Blur (1290–1330):** this is the scripted blurred-vision POV (beat 8, f-stop 1.4). It is intended and unchanged.
- **Review strip:** `review/V003b_strip.jpg` shows frames 1086, 1094, 1180, 1210, 1232, 1236, 1240, 1244, 1250 and 1258.

## Known issues
- The whip from the ear into the theatre (f1456–1481) still has a few bare-wall frames, under 0.25 s in a row.
- The temple dive has about 0.25 s of soft frames as the camera passes the skin (f176–186). (unchanged from v002 unless noted)
- No officer caps. The CC-BY cap import lost its axis conversion; see the v002 README.
- Sleeves and hems don't ride up during the growth.
- During the x-ray beat, Officer 2 stays visible at the left edge, in front of the cutaway card.
- The forehead dive (≈27.5 s) and temple dive (≈3 s) are skin macros of about 5 frames each.
