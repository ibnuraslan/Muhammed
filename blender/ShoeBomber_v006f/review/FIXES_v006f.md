# ShoeBomber v006f: fixes for the director's v006e review (Nov 15)

The beat order and frames are the same as in v006e (1, 199, 373, 481, 655, 769, 1069, 1159, 1219). The film runs 1–1446, and shots are joined by hard cuts.

| # | Director's note | Fix (v006f frames) |
|---|---|---|
| 1 | Floating sneaker and mannequin arm at the airport | **No hand carry any more.** After he steps out of the sneaker (beat 9 opening), the film cuts at 1288 to **both sneakers already in the tray, riding the belt toward the X-ray** (1288–1353, camera tracking the tray). It then cuts back to him **standing in his socks** (1354 on). No kneel, no outstretched arm, no prop in a hand. |
| 2 | Shoes on a grey void | Beat 7 (1069–1158) is now **in the forward aisle of the cabin, with the seat rows and their legs on both sides and the aisle running away behind**. The cut-open shoe lies on the carpet with its top half beside it. The camera pushes from the wide (1069) to the cut sole, the putty slab and the cord in **about 1.2 s** (to 1140), then holds. |
| 3 | Pin overhead: lower to seated eye height from the aisle; faces; his face sideways | 580–776 is **one shot at seated eye height (1.1 m) from the left of the aisle**, with a slow push. The four empty seats behind the lens (04B/C, 05B/C) are hidden for this shot only. **The attendant (at his head), PaxA (over his back) and the steward (kneeling opposite, injecting) all face the camera.** **The bomber's face is turned sideways toward the camera** on the carpet the whole time. No top-down angle remains in 560–960. |
| 4 | PaxB at the feet: dark top-down shots of backs | 866–1068: **a low camera in the aisle in front of PaxB (0.95 m)**. He kneels face-on, pulls the shoes off and sets them down. The shoes and the bomber's socked feet are in the foreground. |

## The four rules
- **Rule 1, hand and prop risk.** Nobody carries a prop near a head or face. The cabin shoes are pulled off and set on the carpet. The beat-7 shoe is a still prop. At the airport the sneakers are only ever in the tray or on the floor.
- **Rule 2, no arm across another person.** The head-separation, arm push-out and hand push-out passes ran; `head_check` finds 0 merges.
- **Rule 3, no camera move past a body.** Every shot change is a hard cut (580, 778, 866, 1068, 1158, 1218, 1288, 1354). The moves that remain are slow pushes with nothing between the lens and the subject, and `cam_inside_check` is clean. `cam_speed_check` and `cam_turn_check` flag only 580, 778 and 866, which are those cuts.
- **Rule 4, every hand attached.** I checked this on every frame of the preview.

## Checks (run on the packaged file)
- **`qa_check.py`:** HOVER 0, CLAW 0, FACEPRESS 0, BACKHEAD 0, INSIDE 0. FILL 2 (151 and 517, the top of a head in a close shot).
  - EMPTY 71 is the "characters under 15 % of frame" heuristic. It counts:
    - the wide aisle shot (205–223)
    - the start of the pin (571–601)
    - the beat-7 shoe and the sky (1069–1213), which have no characters by design
    - the tray shot (1291–1351), which has no characters by design
- **`clip_scan.py`:** 709–721 and 763, the steward's hand on the bomber's arm during the injection.
- **`head_check.py`:** 0 merges.
- **`limb_check.py`:** the same artefacts as before (the shoulder joint is sampled, and there's no occlusion test).

## Watched
I watched `ShoeBomber_v006f_preview.mp4` frame by frame, start to finish: all 290 frames, rendered from the packaged `.blend` after the last change.
