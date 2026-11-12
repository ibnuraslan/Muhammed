# LegoInNose: acting fix, v006 → v008

All 11 story-beat frames are unchanged: 1, 241, 457, 631, 757, 949, 1087, 1351, 1477, 1867 and 2077 (`beats.json`). No VO was added.

Before: `v008_BEFORE_v006_halfsec.jpg`. After: `v008_AFTER_halfsec.jpg`. Both sample every 30 frames at 270×480, 8 samples.

## 1. Review of v006: every problem found, with frames
| v006 time (frame) | Problem | Fix in v008 |
|---|---|---|
| 2.5–3.5 s (151–211) | Boy pushing the brick in: fingers hand-set (stiff, half-claw). The camera looks down onto his hair (hair 29–38 % of frame). | All fingers use `hand_poses.apply_pose` "pinch" (thumb on index, brick between). The camera is lowered to nose height (z 0.55). |
| 5.0–5.5 s (301–331) | Digging in the tub: tripod fingers flagged as CLAW (curl 40–45° with a straight base). | Relaxed hand going in, then "pinch" on the yellow brick. |
| 11.5 s (691–721) | Pushing the yellow brick in: the palm covers the face. | The pinch pose now reads as fingertips at the nostril. Listed below as intended contact. |
| 12.0 s (721) | Flat pink skin close-up on the dive. | A camera key at f721 holds the nose and nostril 5 cm out, then the camera enters within 4 frames. |
| 12–13 s, 14.5 s, 18.5 s, 21.7–22.2 s (tunnels) | Camera turns of 66–171° in one frame inside the nostril tunnels (CAMJUMP ×11). The view snaps to 179° at the nostril exits. | The path is monotone per axis (PCHIP, no overshoot loops). Inside each tunnel the view turns smoothly from the entry to the exit direction over the whole pass, at most about 6° per frame. Easing waypoints were added at both nostril exits. |
| Tunnels and studio (733–1324) | "Camera inside geometry": the camera saw the tube's back faces, and the cross-section head's inner surface was back faces. | Tunnel normals now face inward. The cut head gets an inner shell (Solidify) with front-facing cut-tissue material. |
| Whole film | Render-hidden objects (tunnels, hidden characters) still blocked the camera rays (FILL "Tunnel_Dive2" at f73 and similar). | `hide_viewport` is keyed together with `hide_render` on every visibility key. |
| 17.5 s (1051) | Tweezers pull: the frame is floor plus tweezers, with no face. | The camera is re-aimed between the boy's nose and face (45 mm). |
| 25.5–26.0 s (1531–1561) | Blowing the nose: both palms pressed on the face (FACEPRESS). The camera sees the top of his head (lean 22°). | The right hand alone holds the tissue to the nose with a wrap grip; the left hand rests on his lap. Lean is 10° and head 4°. |
| 28.5 s (1711) | Whip pan off the bench: the cell is bare wall. | A pan key frames the sofa (cat, pillows) on the way to the door. |
| 29–31 s (1741–1843) | Bedroom: the man covers only 10–14 % of the frame (wide, dark). The camera passes close to his head at 30.6 s (top of head, 87° turn). | Camera keys moved closer to his face (30–32 mm) and off his head path. Blue night fill light, plus the lamp. |
| 33–35 s (1981–2101) | Shower: hair or the top of his head fills the frame (lean 18–26°, head 16–24° down). | Lean 6–12° and head 4–10°, so the face stays readable while he presses the nostril ("point" pose). |
| 34–36 s (2041–2161) | The 85 mm macro gave blurred chest and skin cells. | 45–55 mm, framing the face, the brick and the palm together. |
| Whole film | Hand-set finger angles everywhere, and no official joint limits. | `add_hand_limits` on all four rigs. Every hand keyed with `apply_pose` presets: relaxed, pinch, wrap_grip, cup_hold, point, open_alarm and hold_flat_object. |

## 2. Intended flags left in `qa_v008.json` (with reasons)
QA is run on the packed v008 file at step 6 with `beats.json`. Final counts are at the bottom.

**EMPTY, "no character in view" or "only Tunnel_… in view":**
- f733–865 and f1111–1315 are the cross-section studio and the nostril tunnels.
- This is the brief's explainer beat: a 6× sagittal cut of the boy's own head (real skull and sinus scans).
- No rig is in view by design. The anatomy is the subject.

**EMPTY, "wall/prop fills the frame, character under 15 %":**
- f283–349, the tub dig: a macro of the boy's hand in the brick tub. His arm and hand are the subject.
- f481–571, the "click together" dream macro: two floating bricks snapping together, with the boy's face in soft focus behind.
- f1087–1093: the tweezers being held up (the brick is the subject).
- f1465–1471, f1729–1747: the pans between rooms, each about 0.3 s.

**FILL, "surface <12 cm":**
- f721, 871–877, 1099–1105, 1327–1333: the camera entering or leaving the nostril (a macro of the nose).
- f1879: the camera passing through the bedroom/bathroom wall. The wall is hidden from the camera, but ray casts still hit it.

**Hand-audit contact (the BVH hand audit, not QA):**
- Fingertips at the boy's nostril while pushing the brick in: a real pinch.
- Mom's left hand cradling the boy's chin for the tweezers.
- The man's hands on his own shirt while he sits up in bed.

## 3. Checks (final numbers, packed v008)
- **QA, step 6:** `{'EMPTY': 146, 'FILL': 8, 'INSIDE': 1}`. Before (v006): EMPTY 432, FILL 216, INSIDE 29, CLAW 17, CAMJUMP 13.
  - **0:** CAMJUMP, ROLL, CLAW, HOVER and FACEPRESS.
  - **INSIDE 1, not fixed:** frame 727, the frame the camera passes the nostril opening into the dive tunnel.
- **clip_scan: 5 bad ranges, not 0:** `[[1, 13], [265, 265], [955, 973], [991, 997], [1363, 1363]]`.
  - **How it was run:**
    - The stock script crashes on this film: the man's clothing mask switches off in the shower, which changes his vertex count. I used a local copy with a one-line bounds guard.
    - It ran on a scan-only copy with MPFB's "Delete" clothing masks off, so hands are tested against the full body. With the masks on, the torso under the shirts is deleted, and the scan reported whole hands "inside" his torso while they rest on the mattress.
  - **Remaining ranges:**
    - 0.0–0.2 s and 4.4 s: the boy's resting hand at his thigh.
    - 15.9–16.6 s: the boy's flailing hand while Mom arrives, and Mom as she kneels.
    - 22.7 s: the boy's hand at his thigh in the time-lapse.
  - These are short, but **open**.
- **Grips:** the bricks are 4–6 mm from the pinch, tweezers 2 mm mean, inhaler 0 mm.
- **Close-ups of every hand contact:** `v008_hand_closeups.jpg`. Debug lights; the shower close-up keeps the frosted glass.

## 4. Open items I could not finish in this round (honest list)
- **Tunnel cells:** 12.0 s, 14.5 s, 18.5 s and 22.0 s in the after sheet are still mostly flat pink tunnel or skin. The tunnels have veins and hairs, but at 270×480 those cells read as near-empty.
- **27.0–27.5 s, inhaler:** the camera is low under the ceiling, and his hand fills the frame. It needs a reframe to his face.
- **28.5 s:** the pan cell shows the sofa, pillows and cat, with no person.
- **Shower nostril press (32.5–34.5 s):** the "point" pose with the index on the nose can read as a "shush" gesture.
- **Hand close-ups:**
  - The f735 close-up is inside the tunnel (pink), not a hand.
  - The Mom left-hand (chin) close-up shows her back.
  - The shower palm close-up is partly behind the frosted-glass rail.
- **Tweezers grip:** mean 10 mm, with one frame at 95 mm after the hand re-key pass.
