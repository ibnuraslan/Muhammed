# ToucanBeak v004b: camera polish of the approved v004 (Connect28)

**v004b change only:** the camera aim flipped for one frame at f677 (172°) and f695 (175°), because the up-vector flips near a straight-down view. Frames 660–710 now carry the previous orientation forward (parallel transport) and blend back into the standard aim over 700–710. No other frame, key or object is changed. qa_check (fc62c27) reports CAMJUMP 0, and every other qa count is identical to v004 (`review/qa_v004b.json`). Largest one-frame turns left (all under the 60° cut threshold, and outside the scope of this fix): 49° at 508 (the whip into the clinic), 45° at 1498 (the exit whip) and 23° at 1338.

The v004 notes follow; the review sheets for v004 are in `../ToucanBeak_v004/review/`.

# ToucanBeak v004: acting pass (Connect28). Built from v003.

- **File:** `ToucanBeak_v004b_60fps.blend`, packed, 94.70 MB, normal git file, no LFS. It opens in factory Blender 5.2.2 with 0 unpacked images and 0 linked libraries. Check still: `package_check_lowres.jpg` (frame 1700, 270×480, 8 samples).
- **Format:** same as v003. See `SETTINGS.md`. Story-beat frames (`beats.json`) are unchanged. No voiceover was added.
- **Fix list:** `review/ACTING_notes.md`.
- **Sheets:** `review/before_v003_0p5s_0..2.jpg` and `review/after_v004_0p5s_0..2.jpg`.
- **Hand close-ups:** `review/hands_closeups_v004.jpg`, 18 shots.
- **Checks:**
  - `review/qa_v004.json`: qa_check.py at c6240b2, step 6.
  - `review/clip_scan_v004.json`: 0 bad ranges.
  - `review/audit_v004.txt`: step 6.

## QA (qa_check.py) results
| Flag | Count | Status |
|---|---|---|
| HOVER | 0 | |
| FACEPRESS | 0 | |
| BACKHEAD | 0 | |
| CLAW | 31 | Intended contact. VetB's right hand wraps the scanner handle (541–589) and the prosthetic (1543–1693), and there are 2 frames of the tweezers pinch. grip_object stops each finger about 8 mm off the surface, so qa's 2 cm fingertip ray misses it. The wraps are visible in `review/hands_closeups_v004.jpg` (shots 0, 1, 6 and 7). |
| EMPTY | 613 | False positive or intended (see below). |
| FILL | 35 | False positive or intended (see below). |
| INSIDE | 58 | False positive (see below). |

Why the EMPTY, FILL and INSIDE flags are false positives or intended:
- qa_check counts only human rigs as characters. The jungle (1–528), the void explainer (690–1500) and the enclosure (1976–2250) feature the toucan or the beak model, so they read as "no character". These cells are readable in the after sheets.
- **Mote_emitter** is the dust-particle volume, and its mesh is not rendered (`show_instancer_for_render = 0`). The camera is inside it, which causes all 58 INSIDE flags and 11 FILL/EMPTY flags.
- **Extrude_cutter** is a boolean cutter with `hide_render` on.
- **Void_front, Wall_patch and Monitor_back** have camera visibility keyed off on the flagged portal frames (745–769, 1501–1537).

## Audit (audit_v004.txt, every 6 frames): open items
- **Wrist:** the copy-rotation influence is now 1.0, as the director approved, and every hold is re-placed with `hand_poses.grip_object`.
- **HAND_IN_BIRD 21 and HAND_IN_PROP 24:** VetB's right hand is 1–5 vertices deep in the beak and the prosthetic, 1519–1692.
- **HAND_SELF 35:** mostly VetB's right hand against his own torso while he holds the scanner (547–590).
- Every other check is 0. clip_scan reports 0 bad ranges.
