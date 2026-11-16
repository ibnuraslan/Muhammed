# Milgram: plan (Phase 1, checkpoint P1)

ConnectB25. Branch `claude/connectB25-milgram`. 1080×1920, 60 fps, Cycles CPU, hard cuts (each shot has its own camera,
bound by a timeline marker at its first frame), shots of 1–3 s. Reference: `briefs/batch2/B25_Milgram_reference_1fps.jpg`
(53 s, current style). We follow its shot order, subjects and framing ideas with our own sets and characters.

Until the VO arrives, every shot is a self-contained clip about 1.3× its reference slot, laid end to end in
`shots_provisional.json` (frames 1–4068). In Phase 2 that table gets the VO frames and `02_shots.py` rebuilds each
clip at its VO frame and **trims** it (no time-stretching of character animation).

## Cast (generic, no real likeness): MPFB2 rigs re-used from our own packages, re-dressed
| Role | Look | Donor rig |
|---|---|---|
| **Stranger** (the actor/learner) | bald, salmon-pink tee, khaki trousers; MPFB expression shape keys (mouth open, brows, smile) | EarInArm_v011 `Patient` |
| **Subject** ("you", the teacher) | grey hair, light-blue shirt, dark-grey trousers | ElectricianPolice_v010 `Man` (vest and gloves removed) |
| **Doc** (the man in the lab coat) | dark hair (fringe cut back so both eyes show), white lab coat over white shirt and tie, dark trousers | TitanicIceberg_v014 `ExpertA` |

All three: eye fix (EnhancedEye cornea → transparent mix) checked, camera-only catchlight per shot, elbow IK limit opened
(−40°…100°), `hand_poses` wrist/finger limits, relaxed hands, clothes in non-skin colours (coloured by rest-pose height,
so a seated pose does not move the shirt/trouser line).

## Sets (one scene)
- **LAB A (origin), the subject's room:** periwinkle-blue walls as in the reference, grey carpet, white skirting and ceiling.
  Wooden table (Poly Haven WoodenTable_01, scaled) with the **shock generator**: a light-grey console, 30 lever switches
  with a red lamp over each, colour bands from grey through yellow/orange to deep red (the danger end), a blank meter and
  a dial. **No text or numbers** anywhere on it. Red "wrong answer" dome lamp on the back wall. A school chair (Poly Haven).
  The generator's cable runs over the table edge, along the carpet, and ends in a plug lying **unplugged** next to the
  wall socket (the "shocks aren't real" reveal). A clipboard on the table carries a sheet with the subject's photo and
  grey lines (no text). Filing cabinet, and our **DA KRAS FILMS** poster on the back wall.
- **LAB B (x=20), the stranger's room:** same walls and carpet, wooden table, school chair, a wall speaker. The electrode
  cuff is a dark strap with a metal electrode, Child Of the right forearm bone.
- **HOME (x=40), the 1960s living room:** yellow patterned wallpaper, wooden floor, red rug, vintage TV (Poly Haven
  Television_01) on a low table showing the subject's portrait in black and white, a picture frame, a standard lamp.

## Shot table (provisional frames in `shots_provisional.json`)
| # | Ref s | Line (reference) | Who and what they physically do | Camera |
|---|---|---|---|---|
| 01 | 0–1 | When the stranger got an answer | Stranger at his table, right forearm on the table with the cuff; he lifts his left index finger to answer, brows up. | 3/4 front, 30 mm, slow push, f/8 |
| 02 | 1–2 | …wrong | The red wall lamp lights up (glow on the wall). | 36 mm, push toward the lamp |
| 03 | 2–3 | you would press | First person: the subject's hand comes in from the frame bottom, index finger on lever 3, presses it down; its lamp lights. | FP just in front of his face (head behind the lens), 30 mm, f/8 |
| 04 | 3–5 | that would shock him | Close on the strapped wrist on the table: small stylised arcs at the electrode; the hand clenches into a fist. | 38 mm, f/10, slow push |
| 05 | 5–7 | And this was all part of an experiment | Doc standing beside the subject, arms relaxed; looks down (as if at notes), then up at the subject. | medium, 32 mm |
| 06 | 7–8 | this happened | 3/4 behind the subject at the generator; the red lamp flashes twice above it; his head lifts. | 26 mm |
| 07 | 8–10 | the shock got stronger | First person: two presses in a row (levers 7, 8); the lamps climb along the panel. | FP |
| 08 | 10–11.5 | until the stranger screamed | Stranger jolts back, mouth open, brows up; left hand grips the strapped right forearm (one hand on the hurt place). | 3/4 front, 34 mm |
| 09 | 11.5–13 | and begged to stop | He leans toward us over the table, left palm raised "stop", pleading brows, talking. Face clear of the table. | front, 34 mm |
| 10 | 13–15 | But a man in a lab coat | Doc points at the generator with his right hand, talking (jaw). | 30 mm |
| 11 | 15–16 | told you to keep going | Subject looks back over his right shoulder toward the doctor, then turns back to the panel. | face 3/4, 40 mm |
| 12 | 16–18 | so you do | First person: the next lever goes down (lever 13). | FP |
| 13a | 18–20 | Even when you think he has collapsed | Stranger on his knees on the floor beside his chair, hands on his thighs, arcs flicker round him, pained face. | low front 3/4, 28 mm |
| 13b | 20–22 | on the floor in pain | He sinks back toward his heels, left palm goes to the floor to hold him up, head drops to one side. Arcs fade out. | low side-front, 30 mm |
| 14 | 22–23 | you keep listening | Side view of the subject at the panel, head lifts and tilts (listening). | 30 mm |
| 15 | 23–25 | to the man in the lab coat | Doc closer: talks, looks at the subject, then looks down. | 36 mm |
| 16 | 25–26 | what you don't know | We follow the generator's cable along the carpet toward the wall. | 26 mm tracking |
| 17 | 26–28 | is that the shocks actually aren't real | The plug lying on the carpet next to the wall socket: never plugged in. | 32 mm, f/10, push |
| 18 | 28–31 | and the stranger is an actor | Stranger sits back relaxed, smiles (corner puller), gives a small wave with his left hand. | front 3/4, 34 mm |
| 19 | 31–32 | are actually… | Subject surprised: head jerks back, jaw drops. | face 3/4, 40 mm |
| 20 | 32–34 | the real test subject | The clipboard on the table: the sheet carries **the subject's own photo** (B&W). Push in. | 34 mm, f/10 |
| 21 | 34–36 | despite the cries | Subject close: uneasy, glances toward the doctor, back to the panel. | face 3/4, 42 mm |
| 22 | 36–37 | you keep going | The subject at the panel, the doctor standing behind him. | 26 mm |
| 23 | 37–39 | even to the point of killing the person | First person: the finger moves into the red danger switches (levers 25, 26). | FP |
| 24 | 39–42 | an authority figure in a lab coat | Doc from below, straightening up, talking. | low angle, 26 mm |
| 25 | 42–44 | told you to | First person: the last lever (30) goes down. | FP |
| 26 | 44–45 | And this experiment | Wide of the lab: subject at the generator, the doctor beside him, the red lamp, **our poster**. | 22 mm, f/10 |
| 27 | 45–47 | was actually done in the sixties | 1960s living room: the TV shows the subject's portrait in B&W; slow push. | 30 mm |
| 28 | 47–50 | proving how far ordinary people will go | Subject's face: looks down toward the panel, breathes. | face 3/4, 40 mm |
| 29 | 50–53 | when we think we're just following orders | Doc points toward the subject, talking; slow push. | 30 mm |

## DA KRAS FILMS logo (one placement)
- **26 (wide of the lab):** dark logo on a white framed poster on the back wall, right of the generator. Flat to the camera
  (about 20°), about 17% of the frame width, on screen for the whole shot (≥1 s), f/10. It is also visible in the background
  of 06. Not on any person, the generator, the cable or the clipboard.

## Risky shots and their simple staging
1. **First-person hand on the switches (03, 07, 12, 23, 25):** the index finger (`point` preset) is solved onto the lever tip
   (fingertip within 1–7 mm at contact), the lever rotates down only while the finger is on it, and the lamp lights after.
   The arm runs from the frame bottom edge to the (implied) shoulder. Right hand for the right half of the panel, left hand
   for the left half, so the arm never crosses the lens.
2. **The stranger in pain (08, 09, 13a, 13b):** his face stays up and visible (never pressed into the table or floor);
   one hand on the hurt forearm; the collapse is kneeling → sinking back with one palm on the floor, not lying face down.
3. **No on-screen text:** the generator has colour bands only, no "DANGER" or voltage labels; the clipboard sheet has a
   photo and grey lines; the poster carries only our logo.
4. **Lab coat and clipboard in the fingers:** tried twice (pinch on the edge, then palm under the board, both Child Of
   the wrist); `body_prop_cross` still found fingers/forearm through the board, so per LESSONS 2.15 **Doc holds nothing**
   and the clipboard only appears lying on the table (shot 20, with the subject's photo). Doc's coat is the white jacket
   of the elegant suit (shirt and tie kept in a front strip).
5. **Arcs:** stylised short white-yellow emissive bolts, keyed on/off every 3 frames (no Scene Time drivers); no wounds.

## Look
Bright clean 3D animation (`STYLE_ANIMATED.md`): AgX Punchy, soft area lights, smooth simple materials, clean surfaces.

## Build scripts (`scripts/`)
`01_build.py` (characters, sets, props) → `02_shots.py` (one function per shot: keys + camera + marker, placed from the
shot table; faces reset to neutral at every cut) → `frames.py` / `sheet.py` (review renders).
The portrait image used on the TV and the clipboard (`assets_gen/portrait.png`) is a crop of our own render of shot 28.
Poly Haven assets are fetched with `pipeline/fetch_polyhaven.py` into `assets/` (not committed; packed into the final .blend).

## Director P1 notes, applied while waiting for the VO (pushed with the Phase 2 package)
- Doc: hair swapped (short02 refitted from ExpertB, alpha-intact hair material), coat/trouser split by mesh island
  (no light band under the hem), weight shifts and nods, an open-palm "please continue" gesture in 05 and 24; 10/29 point.
- Seating: lab A chair lowered (seat scale 0.88) and moved back, lab table moved back 5 cm, heels slightly raised;
  the subject's idle hands rest on his thighs; the stranger's chair moved back, his strapped hand rests as a loose fist,
  his free hand on his thigh. Every lever press keys the fingertip along the lever's arc.
  `body_prop_cross`: 0 visible crossings (every 12th + mid + last frame of every shot; every frame of the lever shots).
- Lever shots varied: 03, 12, 25 tight on one lever; 07 over his shoulder at the panel; 23 the mid framing.
  Lamp colour ramps from amber (low switches) to deep red (danger end).
