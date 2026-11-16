# B22 MosquitoDoctor — Phase 1 plan (ConnectB22)

Branch `claude/connectB22-mosquito-doctor` · 1080×1920 · 60 fps · Cycles · hard cuts (one camera per shot, bound by timeline markers).
Follows the reference still sheet's shot order: mosquito lands on the boy's arm → bites (macro) → doctor traps it in a glass vial →
lets it bite the back of his own hand → boy in bed / doctor at his desk with his theory → the bite → fever, yellow eyes →
sick over a basin / stain → organ cutaway → weak in bed, then the empty desk (death off-screen) → colleagues with his notes and the
vial → a ward of beds under mosquito nets.

**Master timeline (no VO yet):** every beat's action is animated at 1× in its own block, ~30% longer than the expected VO beat
(reference ≈ 40 s; master = 3190 frames ≈ 53 s), so Phase 2 can trim/shift blocks to the VO frames without stretching animation.

| Beat (VO idea) | Block | Shot (master frames) | Who / what physically happens | Camera |
|---|---|---|---|---|
| A mosquito landed on the arm of a sick boy | A 1–240 | **S01** 1–100 | mosquito (rigged Aedes, black/white banded legs) flies in, wings beating, legs down; lands on the boy's right wrist/hand, wings fold | macro, follows it in to the landing, f/8 |
| | | **S02** 101–240 | boy lying in an iron bed under a blue blanket, head on the pillow, breathing; turns his head toward his hand | 3/4 above from the room side, slow push |
| it pierced the skin with its needle-thin mouth | B 241–440 | **S03** 241–340 | mosquito pitches nose-down, proboscis meets the skin (1 mm in); abdomen starts to go red | macro side, level with the skin, f/8 |
| | | **S04** 341–440 | feeding, abdomen fills red | macro 3/4 front, slow orbit |
| Then a doctor trapped the mosquito in a glass vial | C 441–710 | **S05** 441–560 | doctor (dark suit, generic) on a chair at the bedside, leaning in, right hand holds an open glass vial upside down, lowering it toward the boy's hand | low front close-up of his face + the vial |
| | | **S06** 561–710 | the vial comes down over the mosquito (mouth stops 1.5 mm above the skin); the mosquito lifts off into the vial | macro from the fingertip side, f/8 |
| and let it bite his own hand | D 711–950 | **S07** 711–830 | at his desk: left hand flat on the desk (back up), right hand holds the vial upside down on its back; lifts the vial away at ~790 | 3/4 high front-left medium |
| | | **S08** 831–950 | the mosquito on the back of his left hand bites (proboscis down, abdomen reddening); his face behind | macro, f/8 |
| You see, the boy had a deadly illness… | E 951–1490 | **S09** 951–1110 | wide room: the boy in bed (foreground left), the doctor at his desk writing (background) | wide from the front-left corner, slow push |
| …and the doctor had a theory… | | **S10** 1111–1280 | writing in his notebook (dip pen in a pinch, left hand flat on the page), small strokes | front medium, push |
| …that it was spread by mosquitoes | | **S11** 1281–1490 | holds the corked vial at eye level, the mosquito inside; studies it | close front, eye level |
| And to prove it… he became the test subject | F 1491–1730 | **S12** 1491–1610 | looks down at the small red bite bump on the back of his left hand | close on the hand, face behind |
| | | **S13** 1611–1730 | writes the result in his notebook | side medium |
| Within a week he had a fever… | G 1731–2030 | **S14** 1731–1850 | slumped at the desk, heavy breathing, face flushing | front medium, push |
| …and turned yellow | | **S15** 1851–1940 / **S16** 1941–2030 | flushed face close-up; then his eye whites turn yellow and the skin yellows | close-up, then eyes close-up |
| and he began vomiting black sludge (kept mild) | H 2031–2270 | **S17** 2031–2150 | on the chair he bends toward a wooden basin on the floor, one hand on his stomach, the other on his knee, heaving (no fluid shown) | 3/4 front medium |
| | | **S18** 2151–2270 | a small dark stain on the floorboards beside the basin and his shoes (stain only) | low on the floor |
| Eventually his organs began to shut down | I 2271–2510 | **S19** 2271–2390 / **S20** 2391–2510 | standing; a clean cut-away window in his torso shows colour-coded organs (liver, stomach, intestines) in a pink cavity; the organs dull to a sick yellow-grey | front medium → close push-in |
| And within a few weeks he was dead | J 2511–2710 | **S21** 2511–2620 | lying in the bed under the blanket, yellow, weak, breathing | 3/4 above, slow push |
| | | **S22** 2621–2710 | death off-screen: the empty desk, chair pushed back, open notebook, the vial | slow push |
| But his death proved that mosquitoes were the carriers | K 2711–2950 | **S23** 2711–2830 | two colleagues at his desk: one reads the notebook (hands on the desk), one points at it | front medium |
| | | **S24** 2831–2950 | the corked vial stands on the desk; the colleague leans on the desk with both hands and studies it (no grip: the held version put his arm across the lens) | low across the desk |
| which ended up saving millions | L 2951–3190 | **S25** 2951–3070 | a bright ward of iron beds under mosquito nets, patients resting | dolly down the aisle |
| | | **S26** 3071–3190 | the boy, recovered, resting in a ward bed (net tied up) | 3/4 above, push |

**Logo (DA KRAS FILMS, dark version):** one placement, on the side of a wooden supply crate at the ward entrance (S25, hopeful
beat, flat to camera, not over the action). A second placement can go on the room's crate if the director wants two; never in the
sick-boy, fever, cutaway or death beats.

## Risky shots and the simplest safe staging used
- **Vial in the fingers:** one hand only (`grip_object` wrap on the vial's outer wall near its bottom), the vial baked to the
  wrist every frame, so it can't float. The vial never touches a face. Capping happens off-screen (cut).
- **Mosquito on the hand:** on the boy's wrist and on the back of the doctor's left hand only (never face or eye). It is a real
  rigged model (wings beat every frame in flight, fold on landing).
- **Bite:** proboscis tip 1 mm into the skin; the "blood" is only the abdomen tint going red. No blood on skin; the bite mark is
  a small red bump.
- **Black vomit:** no fluid on screen. He bends over the basin, then a small dark stain on the floor.
- **Organ cutaway:** a rectangular window cut (boolean) through the suit and skin, a pink cavity lining, real organ model
  (Sketchfab CC-BY) colour-coded, clean and glossy. No gore.
- **Death off-screen:** weak in bed, then a cut to the empty desk.
- **Generic people only:** MPFB CC0 characters from our earlier packages, re-staged (no likeness of the real doctor).

## Notes
- MakeHuman's asset server is down (502), so the humans are appended from our own packages (SpeakWithoutSight Father → Doctor,
  CaveRescue Boy1 → Boy, RingBullet Owner → ColA, TitanicIceberg ExpertA → ColB). Eye fix on every EnhancedEye group,
  elbow IK limit opened to −40°, hand limits, `hand_poses` presets, catchlight per camera.
- Scripts: `scripts/01_chars.py … 04_cams.py` (`build_all.sh`).

## Contact checks (P1)
- 3 frames per shot (first, middle, last) at 540×960, Cycles 8: `review/P1_stills_3perShot_540x960.jpg` (26 shots, 78 frames).
- `body_prop_cross.py` step 3, all rigs, props: Vial, Cork, Pen, notebook pages + cover, both blankets, desk (3 meshes), both chairs,
  basin, bed frame/sheet/pillow, cutaway lining. Results: `review/P1_body_prop_cross.json` + `review/P1_body_prop_cross_summary.txt`.
- Fixes made because of the checks and the sheet: hide keys extrapolated backwards (rigs/blanket invisible from frame 1); the boy slid
  across the room between blocks (hold keys); vial/pen/mosquito drifted between blocks (hold keys); crossed arms while writing
  (pen hand moved to his right); a colleague stood inside the pushed-back chair (chair moved further back); a colleague's leg at the
  desk corner (moved); fingertips into the bed sheet / desk / notebook (hands raised, moved off the notebook); knuckle into the vial
  (grip contact moved out); S11/S24 grips replaced with the vial standing on the desk; S17 camera moved low so his face shows; the
  bed moved 0.6 m into the room.
