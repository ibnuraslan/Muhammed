# NoPilotPlane_v001 — Plan (checkpoint A)

72.5 s, 1080×1920, 60 fps, frames 1–4350. One camera (`CAM_Film`), first-person POV: the camera is baked
from the head bone of our own MPFB character **YOU** (generic young man), so hands, forearms, knees and
feet are real geometry that moves with the body. In beat 19 the camera blends off the head and floats out
to reveal YOU's face. No cuts, no camera markers.

## World layout (metres, +Y = nose)
- **Cabin** (narrow-body, 2+2 seating, 14 rows, pitch 0.81): y −13 … −1.2; aisle x ±0.30; floor z 0; ceiling ~2.05.
  Overhead bins, window strip with 14 shades (some half down), ceiling light strip, seat-back screens (blank, no logos), tray tables.
  YOU sits in the left **aisle** seat of row 4 (y ≈ −3.9), so the window passenger is a foreground layer when YOU looks out.
- **Galley + cockpit door** y −1.2 … 0 (plain door, no text, hinged on the left, swings inward).
- **Cockpit** y 0 … 2.7: two seats (x ±0.5, y 1.55), two yokes, centre pedestal with throttle levers and
  radio handset on a hook, glare-shield panel with **symbol-only gauges** (discs, ticks, needles, coloured arcs — no digits),
  overhead panel of button grids, windscreen + side windows.
- **Exterior** lives under one empty `EXT_PIVOT` centred on the cockpit: patchwork fields (procedural Voronoi
  farmland), roads, a box-instanced town, a river, the long green landing field, cloud card layers, a sky dome and the sun.
  The airliner never moves; pitch, roll, descent and forward speed are all animated on `EXT_PIVOT`
  (keeps rigs simple and the interior stable). Cabin shake = noise on the camera plus a small rattle on loose props.

## Beat table (target starts, one framing ≈ every 1 s)
| # | t (s) | frames | Line | On screen | Camera (head-cam) framings |
|---|---|---|---|---|---|
| 1 | 0.0 | 1 | Imagine you wake up… everyone unconscious | YOU stirs in the aisle seat; hands rise into frame rubbing face then grip armrests. Window passenger slumped against the shade, aisle-across passenger head lolled, drink tipping in a tray table (cup slides, liquid tilts). Rows ahead: heads at odd angles. | 0.0 blurry low look at own lap/hands → 1.2 look up at row ahead → 2.3 turn right across aisle (lolling passenger, hanging headphones) → 3.4 look down at tipping drink → 4.6 swing back left past neighbour |
| 2 | 5.8 | 349 | flying perfectly level | Lean over the slumped window neighbour; window fills frame: level horizon, cloud deck, fields far below, wing tip. | 5.8 push toward window → 6.9 close on window, horizon dead level → 8.0 tilt down to fields |
| 3 | 9.0 | 541 | the pilots must be fine, right? | Hands push on armrests, stand into the aisle, walk forward with head bob; slumped passengers both sides, dangling headphones, an arm hanging into the aisle. | 9.0 rise (camera lifts 0.5 m) → 9.9 turn forward down the aisle → 10.8 glance right at a passenger → 11.5 forward |
| 4 | 12.0 | 721 | You make your way to the cockpit | Galley curtain swept aside by left hand, right hand flat on the plain cockpit door, door swings open. | 12.0 door approaches → 13.0 hand on door, push → 13.6 door swings, light from windscreen floods in |
| 5 | 14.1 | 847 | One pilot has collapsed in the doorway | Look down: captain crumpled on the floor across the threshold; YOU steps high over his legs, hand on the door frame. | 14.1 tilt down to pilot → 15.1 own foot steps over → 16.0 tilt up |
| 6 | 16.8 | 1009 | The other is slumped over in his seat | First officer slumped against the right side window, arm hanging. | 16.8 look right at FO → 17.8 push closer to his face against glass → 18.8 drift past to the panel |
| 7 | 19.7 | 1183 | grab the radio and scream for help | Right hand grabs the handset off the pedestal hook, lifts it to the mouth; shaky panic (camera tremor, breathing bob); radio panel lights. | 19.7 down to pedestal, hand reaches → 20.8 hand closes on handset → 21.8 handset rising past camera → 22.8–25 close tremble on hand/handset, panel lights flicker behind |
| 8 | 25.2 | 1513 | No one answers | Handset lowers; radio panel lights blink green/amber; static only. | 25.2 hold-drift on the blinking panel, slow push |
| 9 | 26.9 | 1615 | pull the pilot out of his seat | Both hands grab the FO's shoulders, haul back; his limp arm drags across and shoves the yoke forward (yoke translates/tilts). | 26.9 swing to FO → 28.0 hands on shoulders → 29.0 haul back (camera pulls back with body) → 30.5 his arm sweeps the yoke → 31.8 yoke slams forward, look at it |
| 10 | 33.7 | 2023 | Alarms blare. Lights flash. | Red master-warning lamps strobe, cockpit tinted red pulses, cabin shakes; horizon tilts and the nose drops (EXT pitch −25°, roll 20°). | 33.7 jolt up to warning lights → 34.6 whip to windscreen as horizon tilts → 35.5 shake |
| 11 | 36.5 | 2191 | diving fast | Through the windscreen: ground rushing up, town spinning below (EXT roll continues, altitude falls fast). | 36.5 push to windscreen → 37.6 town rotating fills frame |
| 12 | 38.8 | 2329 | You grab the controls… heavy and confusing | YOU drops into the right seat, both hands on the yoke, arms straining (yoke shakes); gauge needles spin. | 38.8 drop into seat (camera falls 0.4 m) → 39.8 look down at hands on yoke → 40.8 glance at spinning gauges → 41.8 back to windscreen |
| 13 | 42.5 | 2551 | you sort of figure it out | Pull back slowly; horizon creeps level (EXT pitch/roll → ~0), camera tremor fades, breathing calms. | 42.5 windscreen, horizon creeping → 43.6 hands easing → 44.7 horizon nearly level → 45.8 settle |
| 14 | 47.1 | 2827 | roughly level… still slowly losing height | Altimeter needle (no numbers) unwinds slowly; ground closer (altitude 400 m). | 47.1 down to altimeter (macro-ish lean in) → 48.4 needle → 49.6 up to windscreen, ground near → 51.0 side window, fields passing → 52.3 forward |
| 15 | 53.5 | 3211 | a long stretch of open field | Long green field beyond the town fills the windscreen. | 53.5 lean forward to the glass → 54.6 field centred → 55.7 tilt along its length |
| 16 | 56.8 | 3409 | You could try to land right now… throttle | Right hand hovers over the throttle levers, glances at the field, back to the yoke; indecisive look around. | 56.8 down to throttle, hand hovering → 58.0 field → 59.2 throttle (fingers touch levers) → 60.4 yoke → 61.5 field → 62.6 left at empty captain seat → 63.6 throttle |
| 17 | 64.6 | 3877 | keep flying and hope someone wakes up | Turn over the shoulder: crew on the floor, cockpit door open to the cabin, slumped passengers in rows. | 64.6 turn over right shoulder → 65.8 down to floor pilots → 66.9 out through door into cabin → 67.9 back round |
| 18 | 68.9 | 4135 | this field might be your only chance | Turn back to the field filling the windscreen, sun flare. | 68.9 swing forward → 70.0 push to field, flare |
| 19 | 71.9 | 4315 | What do you do? | Camera leaves the head (blend off the head bone), rises and swings round to YOU's face: wide-eyed, gripping the yoke. | 70.9 start float-up/out → 71.9 face reveal → 72.5 settle |

**Note on beat 19:** only 0.6 s remains after 71.9 s with frame_end 4350. I start the float-out at ~70.9 s (late in beat 18) so the
face lands at 71.9 s and settles by 72.5. If the director prefers, I can extend the tail to ~73.5 s (frame_end 4410) — no other change needed.

## Assets (all CC0 unless noted)
| Asset | Source | Licence |
|---|---|---|
| YOU, 2 pilots, ~6 passenger variants (duplicated with shared mesh data) | MPFB2 / MakeHuman system assets (bodies, clothes, hair, skins) | CC0 |
| Cabin, seats, bins, galley, door, cockpit, yokes, pedestal, panels, gauges, handset | built procedurally in Python (`02_build_set.py`) | ours |
| Exterior fields/town/river/clouds/sky | procedural (`02_build_set.py`) | ours |
| Seat fabric, carpet, plastic, metal textures | Poly Haven (fabric/carpet) via `fetch_polyhaven.py`, 1K | CC0 |
| Ambient interior HDRI (optional) | Poly Haven 1K/2K | CC0 |
No Sketchfab CC-BY models planned, so the CC-BY block will likely be empty (MakeHuman + Poly Haven are CC0; credited anyway).

## Trickiest shots and approach
1. **Head-cam with real hands.** Camera is baked per frame from the evaluated head bone (eye point offset, near clip 3 cm) so hands
   driven by IK are always consistent with the body. Hand IK targets are placed in world space on the props (armrest, door, handset,
   shoulders, yoke, throttle) → hands visibly grasp before anything moves (props parented/keyed to the hand during holds).
2. **Head stability.** A real head bob is nauseating; the baked camera gets a low-pass filter on rotation plus authored bob
   (walk) and authored tremor (panic, dive). Framing per ~1 s is authored as look-at targets that the neck/spine follow.
3. **Dive & recovery.** All exterior motion on `EXT_PIVOT` (pitch, roll, altitude, forward drift), so the horizon tilt is exact and
   interior lighting from the sun swings with it. Red alarm = keyed emission strobes + red point lights.
4. **Stepping over the floor pilot / dragging the FO.** Feet planted with the anim_lib Human walk on the flat floor; the step-over
   gets a manual high foot arc checked against the pilot's legs. FO drag: his root follows YOU's hands with lag; his limp right arm is
   keyed to sweep across the yoke, and the yoke is keyed forward from the contact frame.
5. **Beat 19 float-out.** Camera matrix blends from head-cam to a free path (slerp) over ~1 s; YOU's head mesh is real, so the face
   reveal needs no swap.
6. **Speed.** 4350 frames is long; blocking will be keyed every 2 frames for walks, camera baked every frame, stills at 270×480 / 8 spp.

## Schedule
A 19:45 (this) · B 22:30 blocking sheet · C 00:15 polish 0.2 s sheets + audit · D 01:00 package `blender/NoPilotPlane_v002/`.

## Scripts (planned, `scripts/`)
`01_build_humans.py` (MPFB) → `02_build_set.py` (cabin, cockpit, exterior, lights, materials) → `03_animate.py`
(YOU, pilots, passengers, props, EXT dive, alarms, camera bake) → `audit.py` → `beats.json`.
