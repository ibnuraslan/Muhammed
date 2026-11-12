# RooseveltSpeech: acting review (v006 → v007)

- **Before:** `ACTING_before_v006_0.5s.jpg`, 1 still every 30 frames (0.5 s), 270×480, 8 samples.
- **After:** `ACTING_after_v007_0.5s.jpg`.
- Story-beat frames are unchanged: 1, 187, 337, 445, 721, 877, 1003, 1189, 1285 (`beats.json`).

## Problems found in v006, and the fix in v007
| # | Time / frames | Problem | Fix (v007) |
|---|---|---|---|
| 1 | 1.0–1.5 s (f 60–100) | The camera sits at crowd-head height, so dark silhouette heads fill most of the frame. | The camera lane is raised to 1.3 m above the street (frames 100 and 116), so it looks over the heads at the shooter and the car. |
| 2 | 2.0 s (f 116–125) | The shooter's raised arm fills half the frame at the muzzle flash. | The camera starts 0.7 m further back and higher (frame 116), so the arm is a silhouette in the corner and the flash and the car read. |
| 3 | 1.3 s (f 79) | clip_scan bad range: the shooter's right hand passes through his own thigh as he raises the arm. The arm was interpolated straight from hanging to aiming. | The arm swings out to the side and up (a three-point arc), clear of the leg. |
| 4 | 3.0–3.5 s (f 181–215), beat 2 | The camera looks down into the footwell at his legs. His face is cut off on the beat "he stayed on his feet". | A full-body framing from the front: the feet planting and his face are both readable on the beat. |
| 5 | 5.5–7.0 s (f 300–420) | His chin is tipped up and he stares at the sky, which reads as a held pose with no reason. | The head is levelled and he looks out over the crowd as he straightens. The look still drifts with the crowd turn. |
| 6 | 19.7–20.3 s (f 1182–1216), beat 8 | **The manuscript slid up out of the pocket by itself** before the hand reached it (props must not move on their own). | The paper stays put until the fingers pinch its top edge. It rises only from frame 1205 to 1216, while the hand pulls it up, and the hand follows the paper's edge every frame. Then the hand-off to the wrist happens. |
| 7 | 19.8–20.5 s (f 1219–1227) | As he lifts the paper, the hand brushes into the coat lapel. | The lift arcs further away from the chest. The hand audit is back to one 4 mm sample. |
| 8 | 2.9–8 s (f 175–505) | **The policeman slid about 30 cm across the cobbles** while restraining the shooter, with no steps. | His feet stay planted: he leans in further and grabs the shooter's arm. The location keys are removed. |
| 9 | 12.4–12.6 s (f 745–760) and 15.5–16.0 s (f 930–960) | Inside the x-ray, the paper stack fills most of the frame. | The camera is pulled back 1.4× at those framings (frames 780 and 940), so the paper, the case and the ghost torso all read. |

## Checked and kept (not acting faults)
- **Freeze-frame, 5.6–19.8 s:**
  - The street world runs at 3 % speed, so the crowd and the hero are nearly still.
  - This is the brief's scripted "freeze-frame feel" for "So how was that possible?". Secondary motion (breathing, crowd drift) continues at the slowed rate.
- **X-ray camera, 7.4–19.8 s:**
  - The camera travels among the ghosted torso layers. This is the approved cutaway design: the body is rendered as a see-through ghost on the sky backdrop.
  - Outside the x-ray dome, the camera is never inside a body or a wall (`audit_v3`: 0 hits).
- **Hero feet:** IK-planted on the car floor and the stage. There is one deliberate half-step back at the hit (frames 200–222).
  - `audit_v3`: 0 hover, sink or slide.
- **Hat:** held by the brim until the hit (Child Of the right wrist), then the hand releases it and it tumbles to the street. It never moves without a cause.
- **Glasses case:** it stays in the pocket and is only touched by the bullet (the dent). It never moves.
- **Grips:**
  - the rail (left hand, wrapped)
  - the podium edge (left hand resting)
  - the manuscript (right fist, thumb opposing)
  - the raised fist

  See `v7_hand_closeups.jpg`.
- **Faces on the story beats:**
  - beat 1: wide on him waving
  - beat 2: full body, fixed above
  - beat 3: face close
  - beats 4–7: the x-ray, by design
  - beat 8: face at the podium
  - beat 9: face, then the crane up behind him

## Checks on v007
- `clip_scan_v007.json` (director tool, step 6): **0 bad ranges**. `clip_scan_v006.json` had 1: the shooter's hand in his thigh at frame 79.
- `hand_audit_v7.json` (every 2 frames): 1 hit, 0 joint-range violations.

## Still open (minor)
- At about 12.5 s (around frame 750), a single 0.5 s still shows the page face filling about 70 % of the frame. It shows handwriting and fibre detail, not a blank colour.
- At 2.0 s, the shooter's silhouette arm is still a large foreground shape. It frames the flash and is intended.
