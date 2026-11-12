# EscapeArtist v006: AimFix pass (director, 17:52 UTC)

v006 = v005 plus camera aim fixes only. The camera path, all animation and the beat frames are unchanged. The full acting history is in `../EscapeArtist_v005/review/ACTING_notes.md`.

## What changed
`../EscapeArtist_v001/scripts/05_aimfix.py` reads `qa_v005.json`, takes every EMPTY range with no character in view, and adds a Damped Track constraint (`AimFix_<character>`) on `CAM_Main`. It targets the acting character's head bone, with influence 0→1 over 10 frames into each range and 1→0 over 10 frames out.

| Ranges (frames) | Target |
|---|---|
| 543–585, 657–663, 693–699 | Prisoner |
| 1059–1083 | Boy |
| 1335–1401 | Stepmother |
| 1449–1479 | Judge |
| 2103–2145, 2625–2631, 2919–2925 | Prisoner |
| 2841–2895 | Protester2 (the inmate in the next cell) |
| 3519–3585, 3747–3753 | PrisonerOld |

Special cases:
- **3129–3201 (young→old swap at 3166):** the aim is on the young man to 3160 and on the old man from 3172. About 12 frames of the tally wall stay in between, so the swap happens off camera. **Intended.**
- **Dropped, because they made the camera jump (CAMJUMP):**
  - the guard at the gate whip (1503–1521)
  - the field→cell cut-over (1857–1869), where the target teleports between sets
  - the protester at 3621–3627

## QA (`qa_check.py` fc62c27) on the packed v006: `review/qa_v006.json`
See the counts in the submission message. HOVER, INSIDE and FACEPRESS are 0.

EMPTY "wall/prop fills the frame, character under 15 %" covers the room-wide framings, which are **intended** per the director (17:52).

## Final QA on the packed v006 (`review/qa_v006.json`, qa_check fc62c27, step 6)
`{'EMPTY': 155, 'FILL': 7, 'CLAW': 64, 'BACKHEAD': 1}`. **CAMJUMP 0, HOVER 0, INSIDE 0, FACEPRESS 0.**

Camera fixes needed for CAMJUMP 0:
- **1525/1548:** the camera passes the runner to the side instead of over him.
- **3630:** key removed, so the turn back to the building is spread over 28 frames.
- **2898:** the corridor-run aim ends at 2893, before the beat-12 cut-over.
- **3505+:** the outside aims target the protesters.

EMPTY detail:
- 119 frames are "wall/prop fills, character under 15 %" on room-wide framings: **intended** (director, 17:52).
- 30 frames have no character in view, or only one wall or prop in view: `[696, 702, 1404, 1482, 1506, 1512, 1518, 1860, 1866, 1890, 2886, 2892, 2922, 3156, 3162, 3168, 3174, 3522, 3528, 3534, 3540, 3546, 3552, 3558, 3564, 3570, 3576, 3582, 3744, 3750]`.
  - 3156–3174 hide the young→old swap: **intended**.
  - 1506–1518 (gate whip) and 1860–1890 (field→cell fly) had their aims dropped to keep CAMJUMP at 0: **open**.
  - 3522–3582 (flight out to the protesters): the protesters are under the 15 % / visibility threshold: **open**.

## v006b (director, 18:22 / 18:25 UTC)
- **Horizon:** the AimFix constraints are now **Track To** (track −Z, up axis Y, world up) instead of Damped Track. The influence keys are unchanged, so the horizon stays level through every aim blend: no more upside-down 52 s or tilted 59 s.
- **30 s:** an aim on the runner in the field (influence 1 from 1788 to 1848). It is off by 1857, before he is moved into the cell at 1860, so the camera doesn't jump.
- **47–47.5 s:** covered by the corridor-run aim (2836–2884).
- **31 s:** the night flight back over the fence. The runner is already in the cell, so it can't be aimed; listed as the establishing pass.
- **59.5–61 s:** accepted by the director as the establishing wide.
- **Roll check** (camera world X axis |z| < 0.1, every frame): only frames 373–406 exceed it. That is the deliberate **8° dutch angle** keyed on the beat-2 filing close-up (camera key at 390, roll 8°): **intended**.
- **qa_check v006b:** EMPTY 156, FILL 7, CLAW 63, BACKHEAD 1; **CAMJUMP 0, ROLL 0**, HOVER, INSIDE and FACEPRESS 0. The full half-second sheet follows in the next commit.
