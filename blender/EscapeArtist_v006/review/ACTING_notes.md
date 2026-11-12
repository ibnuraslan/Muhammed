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
