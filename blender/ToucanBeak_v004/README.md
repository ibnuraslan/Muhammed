# ToucanBeak v004: acting pass (Connect28). Built from v003.

- **File:** `ToucanBeak_v004_60fps.blend`, packed, 94.67 MB, normal git file, no LFS. It opens in factory Blender 5.2.2 with 0 unpacked images and 0 linked libraries. Check still: `package_check_lowres.jpg` (frame 1700, 270×480, 8 samples).
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
| CLAW | 0 | Fixed after the director's review: the hand is placed on the tool, then a library preset is keyed (`wrap_grip` scanner, `cup_hold` prosthetic, `pinch` syringe and tweezers, including pick-up and put-down), then `relaxed` after each release. |
| EMPTY | 611 | False positive or intended (see below). |
| FILL | 35 | False positive or intended (see below). |
| INSIDE | 58 | False positive (see below). |

Why the EMPTY, FILL and INSIDE flags are false positives or intended:
- qa_check counts only human rigs as characters. The jungle (1–528), the void explainer (690–1500) and the enclosure (1976–2250) feature the toucan or the beak model, so they read as "no character". These cells are readable in the after sheets.
- **Mote_emitter** is the dust-particle volume, and its mesh is not rendered (`show_instancer_for_render = 0`). The camera is inside it, which causes all 58 INSIDE flags and 11 FILL/EMPTY flags.
- **Extrude_cutter** is a boolean cutter with `hide_render` on.
- **Void_front, Wall_patch and Monitor_back** have camera visibility keyed off on the flagged portal frames (745–769, 1501–1537).

## Audit (audit_v004.txt, every 6 frames, from the build before the director-review hand fix): open items
- **HAND_IN_BIRD 33 and HAND_IN_PROP 28:** VetB's right hand goes 1–3 vertices into the beak and the prosthetic, 1525–1692. These are new in v004, because the prosthetic now actually reaches the beak (in v003 it was keyed to the scene origin).
- **HAND_SELF 23:** the assistant's library `relaxed` fingers touch his own thighs, 1–4 vertices.
- Every other check is 0.
