# ShoeBomber v006d: fixes for the director's moving-preview review (Nov 14)
Times are in the synced v007 film, mapped to v006 frames through the anchors. No beat frame moved (1, 199, 373, 481, 655, 769, 1069, 1249, 1393).

| # | Fault (v007 time → v006 frames) | Fix |
|---|---|---|
| 1 | Stewardess walks with stiff "mannequin" arms (3.25–4.5 s → 250–349) | `swing()` rewritten: hands hang by the thighs (±0.19 m, z 0.80) with a small forward swing, and elbow poles point back. This applies to every walker. |
| 2a | Heads merge in the struggle (6.25–6.5 s, 8.25 s → 485–505, 643) | New `03c_head_separate.py`: no two head centres closer than 0.28 m. A passenger's root yields before a crew member's, and the bomber never moves. The attendant leans less in the grab, and PaxA keeps his head up. `head_check.py` reports 0 merges over the whole film. |
| 2b | A seat tray cuts through a head (6.75 s → 524) | The tray stays stowed. |
| 3 | Stewardess kneels with her shins sunk in the floor (10.75–11 s → 795–813) | Root cause: the fuselage shell's bottom sat about 0.18 m above the carpet in the whole cabin, so every kneel and foot was partly buried. 04 now flattens it onto the carpet. |
| 4 | His face is pushed into the security tray (20.25 s → ~1448) | Hips 0.35 m back in the squat, less bend, head up: he picks the shoe up with his face clear of the tray. |
| 5 | Blurred bodies and sleeves fill the frame (8.5–9.5 s → 660–718) | The arm macro is gone. Beat 5 is one steady window-side shot along the steward's eyeline (−0.80, 1.25, 1.60): injection, then the two-shot on "finally sedated", then the attendant's face at 769. |

## The director's four rules (Nov 14)
- **Rule 1, remove hand risk.** Beat 6 is simplified. PaxB, already kneeling at the bomber's feet, pulls the shoes off and sets them down on the carpet (released at 930; they settle the last few cm). The fuse close-ups and the push into the sole frame the shoes alone on the floor. Nobody holds the shoes up any more, so the hand/prop/head faults of the raised shoes are gone.
- **Rule 2, no arm across another person.** Head separation, arm push-out and hand push-out passes; hands only touch where they grab or pin.
- **Rule 3, no camera move past a body.**
  - Moves are rerouted over the seat backs or along the seat rows below the bins.
  - The pin is held from the side.
  - Beat 5 is held from the window side.
  - The camera moves to PaxB only after PaxA has sat back down.
  - The push into the sole goes straight down onto the shoes. It enters Shoe_L at 1057–1067, which is the covered black wipe into the studio.
  - The attendant no longer walks the aisle past the camera; she stays kneeling at his head.
- **Rule 4, every hand attached.** Checked on every frame of the preview: each visible hand has its arm on screen or leaves the frame edge.

## Checks (packaged film)
- `qa_check.py`: HOVER 0, CLAW 0, FACEPRESS 0, BACKHEAD 0. EMPTY/FILL/INSIDE come only from:
  - the studio and sky cutaways (1063–1392)
  - the push into the sole (1057–1068)
  - the cloud-bank wipes (1243, 1255)
- `clip_scan.py`: one sampled frame (745).
- `head_check.py`: 0 merges.
- Camera:
  - speed check: no move over 0.25 m per frame.
  - turn: no turn over 20°/frame, except a single 21° whip-pan at 475, within the 60° whip-pan allowance.
  - inside: only the covered wipes.
- `limb_check.py` (`review/limb_check_v006d.json`). Most flags are artefacts of the check:
  - **Shoulder joint:** points are sampled from the shoulder joint, which always lies inside the shoulder mesh. Without the shoulder joint, ARMBODY falls from 1025 to 235.
  - **No occlusion test:** characters in other sets are counted as visible. Examples are the airport Traveller and Officer during cabin frames 411–759, and sleepers behind seat backs.
  - **What remains:**
    - arms resting close to their owner's torso (attendant in the grab, PaxA, PaxD)
    - the bomber's right arm pinned behind his back (ARMBACK 573–673, staged as written)
    - PaxA's grab (ARMBACK 465–505)
  - None of these reads as an arm through a body in the preview.
- PROPHEAD:
  - smoke puffs drifting through heads (soft volumes)
  - SeatScreen_05D touching the steward's head for 2 sampled frames (695–701)

## Watched
`ShoeBomber_v006d_preview.mp4`: every 5th frame, 270×480, Cycles 4 samples + denoise, played at 12 fps, so it runs at real speed. All 324 frames were watched as frame-numbered pages, start to finish, after the last change.
