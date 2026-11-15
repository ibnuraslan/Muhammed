# B08 BatBite — Phase 1 plan (ConnectB08)

Branch `claude/connectB08-bat-bite` · 1080×1920 · 60 fps · Cycles · hard cuts (one camera per shot, bound by timeline markers).
Matches the reference still sheet's shot order: crowd + flying bat → bat on the stage → picks it up → bites it (front close-ups)
→ shock with blood at the lips → wide reaction / bending over → hospital with the oxygen mask.

**Master timeline (no VO yet):** each beat's action is animated at 1× in its own block, about 30% longer than the expected
VO beat, so Phase 2 can shift and trim blocks to the VO frames without stretching any character animation. Hard cut at 1600
(stage → hospital), all keys CONSTANT across it.

| Beat | Block | Shot (master frames) | Who / what physically happens | Camera |
|---|---|---|---|---|
| 1. A fan throws what looks like a rubber bat on stage | 1–300 | **S01** 1–80 crowd POV | 3 fans (red, green, yellow clothes) seen from behind, fists up and bobbing; the singer sings at the mic stand (right hand round the shaft, left fist pumps). The bat rises from between the fans (starts below frame) and flies in a tumbling arc, wings fluttering, over them toward the stage. **Logo:** DA KRAS FILMS banner hung from the top truss. | low behind the crowd, between two fans, looking up at the singer; slow push |
| | | **S02** 80–150 bat lands | bat drops onto the deck right-front of the singer, small bounce, lies belly-down, wings flat | low front-left over the stage edge, drum kit (bass-drum **logo**) behind |
| | | **S03** 150–300 notices | singer finishes the line, head turns down to the bat | medium front-right, slow push |
| 2. He picks it up and bites it, thinking it's a toy | 300–620 | **S04** 300–410 | lets go of the stand, two steps toward it, starts to crouch | 3/4 front-right medium-wide |
| | | **S05** 410–470 grabs | deep crouch, right hand closes on the bat's lower body (`grip_object`, wrap; the bat is baked to the IK hand every frame from here on) | low front-right, face visible |
| | | **S06** 470–620 rises | stands up holding it at chest height, looks down at it, turns it | medium front-right, push-in |
| | 620–960 | **S07** 620–700 to the mouth | lifts it to his face, jaw opens | close-up 3/4 left |
| | | **S08** 700–860 bite | bat's head between his lips, jaw closes on it, playful head shakes; hand holds the bat from below (lower body), fingers clear of the face | close-up front, slightly left |
| | | **S09** 860–960 bite front | same bite, straight-on (reference frames 9–12) | close-up front |
| 3. It was real: blood in his mouth | 960–1280 | **S10** 960–1100 shock | pulls it away fast; mouth slightly open; a thin light red trace appears at the right lip corner (keyed visible from 984); stares at the bat | close-up front, slow push |
| | | **S11** 1100–1280 stares | holds it out at chest height, left hand open in shock (not touching the face) | medium front-right |
| | 1280–1600 | **S12** 1280–1380 drops it | fingers open, the bat falls to the deck | wide front |
| | | **S13** 1380–1600 bends over | bends forward, hands on the thighs above the knees, heavy breaths (no vomiting/blood spray) | low front-right wide, face visible |
| 4. Rushed to hospital for rabies shots | 1600–2100 | **S14** 1600–1800 hospital | reclined on a wedge pillow under a draped blanket, oxygen mask on; doctor (blue scrubs) beside the bed, hands relaxed, looking at him and nodding; syringe + vial on a steel tray cart (no hand contact) | medium from the foot-right of the bed |
| | | **S15** 1800–2100 mask close-up | breathing under the mask, catchlights in the eyes | close-up, slow push-in |

Logo placements (2): the bass-drum front head (white logo on black, covering the drum's stock brand print) and a black banner
hung from the top truss (≥15% of frame width in S01, flat to camera, f-stop irrelevant: DOF off). Never on skin, never in the hospital.

## Risky shots and the simplest safe staging used
- **Generic singer, no likeness:** MPFB generic male, long dark-blond hair, black tee + black jeans + black shoes. No tattoos, no costume details of the real person.
- **Bat in the fingers:** one grip only (right hand, wrap round the bat's lower body, solved by `grip_object`), reach error at the grab 0.0 mm; the bat is baked to the IK hand every frame while held, so it can't float. The landing spot is computed from the crouch pose so the hand really reaches it.
- **Bite at the mouth, not into the face:** the bat's head goes 8–12 mm between the lips along the face direction; the hand holds the bat from below by its lower body (~10 cm from the face) so no finger touches the face.
- **Blood light:** one thin red streak from the right lip corner (3 mm wide, 3 cm long), carried by the jaw, shrink-wrapped to the skin. No drips, no spray, no puddle (the reference's floor blood is dropped).
- **Oxygen-mask fit:** the mask cup is built from the singer's own face mesh (nose + mouth region pushed out into a dome, 6–26 mm off the skin) and carried by the head bone, so it can't slide off; tube and strap carried by the head too. Jaw closed in the hospital.
- **Hospital hands:** syringe on a tray instead of in the doctor's hand (the grip didn't read cleanly; simplify rule).

## Built so far (Phase 1)
- `scripts/01_chars.py` … `06_cams.py`, `build_all.sh` (see below for the asset note), still sheet `review/P1_stills_540x960.jpg` (one mid frame per shot, Cycles 8 samples, after `anim_look.py`).
- Characters: eye fix applied to every EnhancedEye group; elbow IK limit opened to −40° per character; `add_hand_limits`; relaxed hands via `hand_poses` presets; all clothes non-skin colours.
- Checked first and last frame of every shot at 270×480: no lens blockers within 1 m, heads in frame, eyes readable.

## Notes / open points
- **MakeHuman asset server is down** (files.makehumancommunity.org returns 502), so `setup_env.sh` can't fetch the MPFB clothes/hair packs. The humans are appended from our own earlier packages (ShoeBomber_v008: Bomber, Officer, Sleeper2's long01 hair; PopeShot_v012: crowd), stripped of animation and control bones, rescaled to real heights, re-tinted. All CC0 MakeHuman/MPFB assets.
- Still to do in Phase 2: lay blocks to the VO frames, trim, then clip_scan / qa_check / limb_check / body_prop_cross on the packed file, full preview, watch every page.
