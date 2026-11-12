# BelugaRescue — acting review of v004 (half-second sheet `ACTING_before_0.5s_part1/2.jpg`)

Frames = v004 frames (60 fps, frame = 1 + 60·t). Story-beat start frames are unchanged in v005 (`beats.json`).

| # | Time (frames) | Problem | Fix in v005 |
|---|---|---|---|
| 1 | 9.8 s (589) | **Prop moves by itself:** her right fin pops off the foot with no hand on it. | End of the cramp (468–516): she draws the cramping right foot in (hip 126°, knee 118°), leans over it, braces on her left hand on the tiles, grips the fin root with her right hand, lifts it off the foot (486–516) and lets go; the released fin sinks, tips flat and settles on the tiles. |
| 2 | 0–36 s (gallery) | **Feet slide:** gallery spectators and keeper turn on the spot (yaw keyed ±5–12°) with planted FK feet. | Constant facing; they look around with head and upper-body twist instead. |
| 3 | 6–8 s (361–481) | **Hands not gripping:** on the calf the fingers curl into claws with the thumb up ("thumbs-up"), palms off the leg. | Calf grip re-keyed: palms resting on the calf, fingers lightly wrapped (curl 28°, thumb opposing 22°); she reaches for the calf from the moment she lands (264). |
| 4 | 9–10.5 s (541–631) | **Unnatural hands:** clawing up reads as repeated thumbs-up. | Swimming hands: cupped, fingers together (curl 25, thumb 12). |
| 5 | 11.5–13 s (691–781) | **Head thrown back** to the limit for 1.5 s (neck over-extended). | Head tilt reduced (looks up at the light, −20° instead of −38°), chest still heaves. |
| 6 | 13.5 s (811) | **Camera frame filled** with blank white (passes into an ice boulder after the clearance push). | Framing at 13.5–14 s moved out of the rocks; clearance now also keeps 0.4 m from the boulders. |
| 7 | 15.5–16.5 s (931–991) | **Whale fills the frame** (head/body blob, no context). | Camera pulled back beside the whale with the ring and window in shot. |
| 8 | 24–25 s (1441–1501) | **Frame filled** by the whale's body and her legs at the grab. | Grab framed from the side at 1.3 m: mouth, ankle and her body in one shot. |
| 9 | 25–27 s (1501–1621) | **Frog legs:** her free leg is splayed (hip 62°, knee 100°, wide abduction) while she rides up. | Free leg drawn in under her, knee bent, close to the body (abduction 22° → 9°), gentle sway — kneeling on the whale's head instead of splayed. |
| 10 | 28.5 s (1711) | **Camera sees the top of her head** and mask strap only. | Framing lowered to face height in front of her. |
| 11 | 29–31.5 s (1741–1891) | **Frozen pose** for ~3 s while rising (arms fixed out to the sides). | Arms float out and slightly down in the up-flow and sway every key, fingers relaxed (she is nearly out of breath); they reach up again as she breaks the surface. |
| 12 | 32–33 s (1921–1981) | **Physics:** she pops out of the water to the waist and stands there. | Head and shoulders break the surface (pelvis stays under water), then she floats. |
| 13 | all | **Default hands** half-claw on idle characters. | Relaxed curl (fingers 28°, thumb 14°) as the default. |

## Re-check (v005)
- Half-second sheet after the fixes: `ACTING_after_0.5s_part1/2.jpg` (before: `ACTING_before_0.5s_part1/2.jpg`).
- Hand-contact close-ups: `v005_hand_closeups.jpg` (incl. new `fin_pull_grip_f0490`, `fin_pull_off_f0512`).
- `blender/pipeline/clip_scan.py` (director branch), step 6, depth 2 cm: **0 bad ranges** (`clip_scan_v005.json`).
- Story-beat frames unchanged (`beats.json` identical to v004).
- Hands: all finger poses come from `blender/pipeline/hand_poses.py` (`apply_pose` presets via `hp_key`; `add_hand_limits` on every rig in `04_hand_limits.py`). Pointing / fist pump → `open_alarm`; buoy carry → `wrap_grip`; calf → `cup_hold`; fin root → `wrap_grip`.

## QA (`blender/pipeline/qa_check.py` @ c6240b2, step 6, `review/qa_v005.json`)
Fixed in v005: CLAW (pointing/fist poses), HOVER (helper card / particulates were hit by rays; now hidden or excluded), BACKHEAD at frame 1 (camera reframed in front of the diver), FILL/EMPTY from the hidden explainer card (now hidden to rays outside 329–501), INSIDE from the ice walls (face normals flipped toward the tank), EMPTY from the water volume (explicit transparent surface, render-neutral), tighter lenses at 650/1925/1965/2010.

Remaining flags — all intended:
| Flag | Frames | Reason |
|---|---|---|
| INSIDE | 163–205, 1147–1249, 1555–1903 | The camera is underwater, i.e. inside the `Water_Volume` box; every back-face hit is `Water_Volume` / `Water_Surface` (checked ray by ray). |
| EMPTY "no character" | 853, 925, 931 | Whale-only shots: the beluga is the acting character; QA counts only MPFB rigs. |
| EMPTY "wall/prop fills" | 1291–1315, 1387, 1435–1477 | The beluga (and its jaw) fills the frame next to the diver at the approach and leg grab; QA counts the whale as a prop. |
| EMPTY "wall/prop fills" | 265–307 | Low floor-level shot of the cramp: she is lying on the tank floor, the floor around her fills the frame (diver 10–11%). Kept for the story beat; not changed under the deadline. |
