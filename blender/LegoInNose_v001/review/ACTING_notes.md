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

## 5. v008b: director's v008 review
Package: `../../LegoInNose_v008b/LegoInNose_v008b_60fps.blend`. Sheets: `v008b_halfsec.jpg` (every 30 frames) and `v008b_hand_closeups.jpg`. Both are 270×480 at 8 samples. The beat frames are unchanged and there's no VO.

| Note | Fix |
|---|---|
| 6.0 s: a knee fills the frame | The camera key at 378 sits between the boy's pinch and his face, at nose height. |
| 26.5–28.5 s: keep the man in frame | Track To on Man's `head` bone (−Z, up Y, world up). Influence 0→1 over 1585–1595, held, then 1→0 over 1716–1726. The sofa pan key (1713) is removed. |
| 30.5 s: top half black | It was z-fighting, not missing geometry. The bedroom's east wall and the bathroom's west wall were the same 12 cm slab, and the dark back of the bathroom tiles won. `split_walls.py` gives each room its own 6 cm half, and does the same for the living room / bedroom wall. |
| Flat tunnel cells | The dives and returns are shorter, so each flat pink stretch is 15 frames or less: in 722–740, 854–872, 1100–1119, 1309–1327. |
| Shower: index on the nose reads as "shush" | The right thumb presses the side of one nostril (the "pinch" pose at 1958–2077). **This is intended contact.** |
| Resting hand at the thigh | `place_hand` + `flat_palm` on the thigh top. `leg_fix.py` then lifts every boy hand that is more than 1.5 cm inside his legs, pelvis or belly. `hand_fix.py` never tested legs. Hits went from 281 to 14 frames (11 rounds). |
| clip_scan | The official `pipeline/clip_scan.py` (3cfc53c) runs unmodified, skin only, no masks-off copy. It used to crash because the man's Delete clothing masks switched off in the shower and changed his vertex count. Those masks are now off for the whole film, so the count is constant. The shirts cover his body. |
| Close-ups | The 4.0 s tunnel cell is replaced by f700 (the brick at the nostril). Mom's chin-hand shot looks at her left wrist from 0.5 m, from the side with a clear line of sight. |

### v008b results (final package)
- **clip_scan, official 3cfc53c, unmodified, step 6:** `bad_ranges` `[[973, 973]]`. That is 16.2 s, one sample, inside the accepted 15.9–16.6 s window (0.3 s or less).
  - Before the leg and Mom passes, the scan also flagged 0.1–0.3 s, 4.4 s, 6.1 s and 22.7–23.0 s (the boy's hands in his legs) and 17.8–17.9 s (his hand inside Mom).
  - The Mom range was fixed with `leg_fix.py … Boy other=Mom 1055-1090`.
- **QA, 771d2da, with beats.json:** `{'EMPTY': 139, 'FILL': 9, 'INSIDE': 1}`. CAMJUMP, ROLL, CLAW, HOVER and FACEPRESS are 0.
  - EMPTY, intended (same as section 2): the tub, the dream bricks, the cross-section studio and the tunnels.
  - EMPTY, new: 1723–1837, the bedroom. The man lies on the mattress and covers 10–14 % (the bed fills the rest).
  - FILL: the nostril entries and exits, plus the bedroom/bathroom wall pass at 1873–1879.
  - INSIDE: f727, the nostril opening, as before.
- **Hand audit:** 10 hits. Mom's shirt 1. The man's own shirt 7, sitting up in bed, which is intended. The man's own body 2.
- **Grips:** the bricks 4–6 mm. The tweezers are still at 95 mm max and 10 mm mean. **Open.**
- **Half-second sheet:** 6.0, 26.5–28.5 and 30.5 s are fixed. The tunnel cells at 12.0, 14.5, 18.5 and 22.0 s are pink, as accepted.

### v008b: props in hand (director's mandatory check, qa_check.py e7b25f7)
`qa_v008b.json` is now from `pipeline/qa_check.py` at e7b25f7: `{'EMPTY': 139, 'FILL': 9, 'INSIDE': 1, 'PROPMOVE': 114}`. **ATTACH is 0.** No masks, caps or glasses are worn in this film.
- **Fixed:** `scripts/prop_snap.py` keys each held brick every frame, within 2 cm of the nearest finger joint that QA measures:
  - big brick in the boy's pinch, 1–150 (it was up to 4.5 cm off)
  - small brick in his pinch, 336–736 (up to 5 cm)
  - small brick in the man's palm in the shower, 2152–2310 (up to 8.3 cm)

  None of these are flagged now. The tweezers, inhaler, tissue, gamepad and phone were never flagged.
- **All 114 remaining PROPMOVE flags are intended.** No hand holds these by design:
  - **Brick_Big, 151–1045:** the red brick stuck in the boy's left nostril. It moves with his head, which is the story.
  - **Brick_Big, 1063–1081:** the red brick in the tweezer tips. Mom holds the tweezers in her pinch, and the tips are 8.8 cm from her fingers.
  - **Brick_Small, 2095–2149:** the yellow brick shooting out of the man's nostril into his palm. It's in flight, like "a brick falling".
  - **Dream_Red / Dream_Yellow, 481–583, and FX_Sparkle03/04/11, 523–541:** the floating dream macro, two bricks clicking together, with sparkles.
  - **XS_Brick_Big / XS_Brick_Small, 757–847:** the bricks inside the 6× cross-section head model in the studio. That's a diagram, with no character.

## 6. v008c: director's v008b review
Package: `../../LegoInNose_v008c/LegoInNose_v008c_60fps.blend`. It's v008b plus three post-passes: `mom_arm.py`, then `fix_v8c.py`, then `chin_ease.py`. Strip: `v008c_director_strip.jpg`, with frames 944, 950, 955, 979 (film camera and a tweezers close-up), 1087 and 1867.

| Note | Fix |
|---|---|
| f944–955: Mom's left forearm went through her chest and belly | The walk-in had no left-hand keys, so the IK target held the 965 chin-reach offset across her body. Now the hand is low at her left side, with a small swing, and the elbow points out to the side. Every frame 870–1145 was tested (her forearm, wrist and hand against her own torso): 0 frames inside. I checked the frames by eye at 944, 950, 955, 958, 968, 975 and 1066. |
| f1087, beat 6: empty sofa | The aim holds the boy's nose 1082–1092 and blends back by 1098. His face is in frame. QA adds FILL "hair / top of head 31 %" at 1087, because his hair takes the top third of the frame. |
| f1867, beat 9: blank wall | The camera holds the man's face 1856–1867, then makes one eased move to the shower framing at 1882. The wall crossing happens inside the 1871–1892 wall-hide window. CAMJUMP is 0. |
| Tweezers grip | Keyed every frame from 960 to 1145, with the origin in Mom's right pinch: worst 0.0 mm, mean 0.0 mm (it was 100 mm at f979). The brick in the tips moves with them. |
| clip_scan 16.9–17.0 s | This appeared after the elbow change: Mom's chin-cradle fingers were counted inside the boy's jaw. `chin_ease.py` keeps her hand 1.5 cm further off his chin over 1005–1031. |

**Final checks on v008c:**
- **qa_check e7b25f7:** `{'EMPTY': 138, 'FILL': 9, 'INSIDE': 1, 'PROPMOVE': 114}`. ATTACH, CAMJUMP, ROLL, CLAW, HOVER and FACEPRESS are 0. PROPMOVE is the intended list from section 5, and the tweezer-tip range now starts at 1057.
- **clip_scan 3cfc53c:** `[[991, 997]]`. That's 16.5–16.6 s, inside the accepted window, and 0.1 s long.
- **Open:** INSIDE f727, the nostril opening.
