# B08 BatBite — Phase 1 plan (ConnectB08)

Branch `claude/connectB08-bat-bite` · 1080×1920 · 60 fps · Cycles · hard cuts (one camera per shot, bound by timeline markers).
Matches the reference still sheet's shot order: crowd + flying bat → bat on the stage → picks it up → bites it (front close-ups)
→ shock with blood at the lips → wide reaction / bending over → hospital with the oxygen mask.

**Master timeline (no VO yet):** each beat's action is animated at 1× in its own block, about 30% longer than the expected
VO beat, so Phase 2 can shift and trim blocks to the VO frames without stretching any character animation. Hard cut at 1600
(stage → hospital), all keys CONSTANT across it.

| Beat | Block | Shot (master frames) | Who / what physically happens | Camera |
|---|---|---|---|---|
| 1. A fan throws what looks like a rubber bat on stage | 1–300 | **S01** 1–80 crowd POV | a crowd of 13 (each in its own non-skin colour) seen from behind, one or both fists up, bobbing; the singer sings into the mic on the stand (no hand on the stand; left fist pumps). The bat rises from between the fans (starts below frame) and flies in a tumbling arc, wings fluttering, over them toward the stage. **Logo:** DA KRAS FILMS banner hung from the top truss. | low behind the crowd, between two fans, looking up at the singer; slow push |
| | | **S02** 80–150 bat lands | bat drops onto the deck right-front of the singer, small bounce, lies belly-down, wings flat | reverse high wide from upstage over the singer's shoulder: the cheering crowd in the background |
| | | **S03** 150–300 notices | singer finishes the line, head turns down to the bat | medium front-right, slow push |
| 2. He picks it up and bites it, thinking it's a toy | 300–620 | **S04** 300–410 | lets go of the stand, two steps toward it, starts to crouch | 3/4 front-right medium-wide |
| | | **S05** 410–470 grabs | deep crouch, right hand reaches the bat's lower body and closes (`grip_object` + wrap_grip; the bat is baked to the IK hand every frame from here on). **Edit plan:** use 410–444 (the reach) and cut to S06 at 506, so the finger-contact frames 445–505 are not shown. | low front-right, face visible |
| | | **S06** 470–620 (used from 506) rises | stands up holding it at chest height, looks down at it, turns it | medium front-right, push-in |
| | 620–724 | **S07** 620–680 to the mouth | lifts the bat (wings folded, held in ONE fist round its body) toward his face | close-up 3/4 left |
| | | **S08** 680–718 bite | profile: the bat's head reaches his lips — **cut on contact** (nothing enters the mouth); other hand relaxed | close-up side profile from his left (~60°), framed on mouth + bat + fist |
| 3. It was real | 718–1280 | **S09** 718–800 recoil | jerks it away from his face and lets it fall to the deck | medium 3/4 front-right |
| | | **S10** 800–1100 shock | close-up, no bat in frame and no blood; looks down at it, mouth closed/slightly parted; left hand starts to rise | close-up front, slow push |
| | | **S11** 1100–1280 stares | stares down at the bat on the floor, left hand raised toward his mouth (fingertips ~7 cm clear), right arm relaxed | medium front-right |
| | 1280–1600 | **S12** 1280–1380 stagger | sways, hand still toward his mouth, right hand on his knee; bat on the floor | wide from behind the front row of the crowd (fists in the foreground) |
| | | **S13** 1380–1600 bends over | stagger continues, then (from 1395) bends forward, hands on the thighs above the knees, heavy breaths (no vomiting/blood spray) | low front-right wide, face visible |
| 4. Rushed to hospital for rabies shots | 1600–2100 | **S14** 1600–1800 hospital | reclined on a wedge pillow, blanket over the legs, oxygen mask on; the doctor (blue scrubs) reads a chart on a clipboard resting on his left palm, then looks up at the patient; syringe + vial on a tray cart (no hand contact) | medium on the patient's face from the bed's right side, doctor beside him |
| | | **S15** 1800–2100 mask close-up | breathing under the mask, catchlights in the eyes | close-up, slow push-in |

Logo placements (2): the bass-drum front head (white logo on black, covering the drum's stock brand print) and a black banner
hung from the top truss (≥15% of frame width in S01, flat to camera, f-stop irrelevant: DOF off). Never on skin, never in the hospital.

## Risky shots and the simplest safe staging used
- **Generic singer, no likeness:** MPFB generic male, long dark-blond hair, black tee + black jeans + black shoes. No tattoos, no costume details of the real person.
- **Bat in the fingers:** ONE hand only: the right fist wraps the bat's body (`grip_object` + wrap_grip) from the grab (450) until he lets it fall (760); wings folded along the body the whole time (clear of his arms and torso); every hand target clamped to arm reach (IK error 0 mm), and the bat baked to the IK hand every frame, so it can't float. From 762 the bat lies on the deck.
- **Bite:** profile only; the bat's head stops at his lips (contact, 2 mm in front of the lip line) and the shot cuts on contact; no front-on bite shot; the other hand stays relaxed.
- **No blood** (director / LESSONS hard limit): the 'it's real' beat is his recoil, the dropped bat and his shocked face.
- **Oxygen mask:** a rigid, roughly triangular clear cup (narrow at the nose bridge, wide at the chin, light green tint, visible green rim) over nose and mouth only, max 2.7 cm off the face; built by ray casts on his posed face and carried Child Of the head bone; thin tube from the bottom; elastic strap from the cup's sides over the cheek and then over the hair round the back of the head, 5 mm off the outermost surface.
- **Hospital hands:** syringe and vial on a tray cart (no hand contact); the doctor's clipboard rests flat on his palm (`hold_flat_object`, baked to the hand every frame); the patient's hands rest on his belly above the blanket.
- **Set (director note 5):** black stage deck, 8 par cans with coloured lenses + spot lights on the top truss, two floor wedge monitors, floor cables, amps, PA stacks, drum kit, banner; a crowd of 13; the bay and the bridge fade into a bright haze with distance.

## Contact checks (director rule, Nov 15)
- First, middle and last frame of every shot at 540×960, Cycles 8: `review/P1_stills_3perShot_540x960.jpg` (45 frames, 9 per row = 3 shots per row).
- `body_prop_cross.py` (step 3, every frame range, props Bat, MicStand, OxygenMask, OxyTube, Blanket, Wedge, Bed; all 5 rigs):
  `review/P1_body_prop_cross.json` + `review/P1_body_prop_cross_summary.txt`.
  - **0** visible crossings: mic stand, oxygen mask + tube, blanket, wedge pillow, bed (whole film), doctor, fans.
  - **Bat, still listed:**
    - 445–466 ring/little fingers + 484–505 forearm/thigh while the hand closes and rises → **cut out in the edit** (S05 410–444, S06 from 506).
    - 709–901 lips (oris) on the bat's head = the bite itself (head 8 mm between the lips). Intended contact.
    - single frames 670, 736, 871–877, 976: index/thumb root a few mm into the bat's fur in the fist.
- Mic clearance: the stand sits 2.5 cm further out and he takes a planted step back before looking down; min distance mic ↔ face/hair over 1–420 = 3.8 cm.
- Fixes made because of these checks: no hand on the mic stand (thumb crossed the shaft); he steps back and sideways before turning (his head passed through the mic, 322–361); every IK hand target is clamped to the arm's reach (the bat floated up to 22 cm off the hand at 480–495); the rise lifts the bat straight up first (it passed through his thighs); the raise to the mouth stays 40+ cm out (it passed through his chest/shoulder 640–670); bat legs curl while held; fingers stay closed until the release; bat lands/drops clear of the stand base and his shoes; blanket covers the legs only, draped from ray hits with a dilation pass; legs/heels raised clear of the mattress; oxygen mask rebuilt as a clean grid cap 6–18 mm off the posed face, Child Of the head bone (the hole-filled version cut through the lips).

## Built so far (Phase 1)
- `scripts/01_chars.py` … `06_cams.py`, `build_all.sh` (see below for the asset note); 3-frame still sheet (see above).
- Characters: eye fix applied to every EnhancedEye group; elbow IK limit opened to −40° per character; `add_hand_limits`; relaxed hands via `hand_poses` presets; all clothes non-skin colours.
- Checked first and last frame of every shot at 270×480: no lens blockers within 1 m, heads in frame, eyes readable.

## Notes / open points
- **MakeHuman asset server is down** (files.makehumancommunity.org returns 502), so `setup_env.sh` can't fetch the MPFB clothes/hair packs. The humans are appended from our own earlier packages (ShoeBomber_v008: Bomber, Officer, Sleeper2's long01 hair; PopeShot_v012: crowd), stripped of animation and control bones, rescaled to real heights, re-tinted. All CC0 MakeHuman/MPFB assets.
- Still to do in Phase 2: lay blocks to the VO frames, trim, then clip_scan / qa_check / limb_check / body_prop_cross on the packed file, full preview, watch every page.
