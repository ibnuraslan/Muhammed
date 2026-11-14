# ToucanBeak v005: moving-preview fixes on the approved v004b (Connect28)

- **File:** `ToucanBeak_v005_60fps.blend`, packed, 94.70 MB, normal git file (no LFS). Same format as v004b (`SETTINGS.md`).
- **Unchanged:** story-beat frames (`beats.json`). No voiceover has been added (the director syncs it).
- **Moving preview:** `review/preview.mp4`, made with `pipeline/preview.py` (every 5th frame, 270×480, Cycles 4 samples + OIDN) and `pipeline/watch_pages.sh`. It was rendered from this packed file. Every contact page was watched, both for v004b (before) and for v005 (after).
- **QA:** `review/qa_v005.json` (`qa_check.py`).

## Faults found by watching v004b in motion, and the fixes
Rules refer to `blender/LESSONS_LEARNED.md`.

| Frames | Fault in v004b | Fix in v005 |
|---|---|---|
| 121–166, 1590–1830 | Macros at f/5.6 read as blur in motion (rule 12) | Deep focus at f/11 everywhere |
| 566–601, 1881–1946 | VetB's right arm read as a stump. His right-hand IK poles pointed the elbow inward, across his own chest, so the blue upper arm vanished against the blue shirt. | Every right-hand pole now points outward, back and down: scanner, prosthetic, tweezers, release. |
| 766–856, 1051–1346 | See-through versions of solid things (rule 13): a translucent reference beak and an x-ray "ghost" bird with the perch showing through it | Both are solid matte models |
| 1031–1046, 1331–1346 | About 0.33 s of empty sky between explainer models | Faster camera keys (1042, 1325). The ghost bird and the cutaway appear earlier (1032 and 1318). |
| 1471–1491 | A printer upright filled half the frame: the camera was inside the printer frame | Camera moved to the printer's open front, between the uprights and below the gantry |
| 1506–1536 | Black bezel panels swept across the frame on the exit through the monitor | Quick, centred pass through the screen (keys 1500/1516/1532), above the monitor stand |
| 1596–1696 | A giant blurred fist filled 50–80 % of the frame and hid the beak seating on the stump | Medium shots (lens 32–42, about 55 cm). The hand, the prosthetic and the stump read together while the beak is seated. |
| 1421–1436 | About 0.33 s of empty sky on the whip from the cutaway to the printer (found in the first v005 preview) | Key 1432 frames the printer as the whip ends |
| 1506–1511 | The assistant's arm (at the mouse) swept past the lens on the exit (first v005 preview) | Exit path moved 12–25 cm away from his side. His arm now stays at the frame edge, sharp and attached to his body. |
| 1751–1836 | The syringe and tweezers hands took 30–40 % of the frame (first v005 preview) | Keys 1750 and 1800 pulled back about 10 cm. The hand, the tool and the beak read together. |

Checked and fine in motion:
- the bird's planted feet and flinch
- the lunges and the fig
- VetA's hand resting on the bird's back
- the prosthetic seated on the stump, with the seam visible
- the pen grip on the syringe
- the tweezers pinch
- the enclosure ending

Short whips under 0.25 s are kept at 506, 696, 751–756 and 1966. The director approved the whip style.

## Checks on the packed file
- **Factory-startup open:** 0 unpacked images, 0 libraries, frames 1–2250 at 60 fps. Check still: `package_check_lowres.jpg`.
- **Previews:** `review/preview.mp4` (v005) and `review/preview_v004b_before.mp4` (before).
- **qa_check.py** (director branch, latest): CAMJUMP 0, HOVER 0, FACEPRESS 0, BACKHEAD 0.

**PROPMOVE 199: almost all intended**
- The beak shards and tip fly off the strike (115–235).
- The fig falls (403–409) and is carried in the bird's beak at the end (2035–2131).
- The printer nozzle is a moving machine part (1429–1489).
- The glue bead grows in place (1747).

Two are real hand-prop flags, still open:
- Tweezers at 1951, a 31 cm move with no hand near: the clear-away just before the put-down.
- Pin at 1849, 1.2 cm.

**FAN 46 (open):** VetB's fingers fan 28–56° in the `grip_object` grips on the prosthetic, the syringe and the tweezers.

**CLAW 19:** VetB's right hand on the scanner wrap (565–595), the prosthetic carry (1531–1585) and the tweezers (1903–1939).

**EMPTY / FILL / INSIDE:** the same documented causes as v004:
- The qa counts only human rigs, so toucan-only shots read as empty.
- The non-rendering dust-mote emitter volume surrounds the camera.
- A hidden boolean cutter.
- Portal panels with camera visibility keyed off.
