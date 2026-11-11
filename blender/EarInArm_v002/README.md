# EarInArm_v002 — farm package

29.5 s vertical short (1080×1920, 60 fps, frames 1–1770): growing a replacement ear in the forearm. Ready for RenderStreet. No render has been submitted.

- `EarInArm_v002_60fps.blend`: the self-contained scene, 55 MB compressed, with every texture packed.
  - It opens and renders in factory-startup Blender 5.2.2 with no add-ons.
  - One camera, `CAM_Film`, with no cuts or markers.
- `SETTINGS.md`: render settings, the four hidden set changes, and suggested test frames.
- `CREDITS.md`: the CC-BY block for the video description.
- `package_check_f1560_lowres.png`: a 20 %, 4-sample frame rendered from the packed file in factory Blender. It shows the package works; it is not a quality reference.
- **Voiceover: none yet** (no mp3 was supplied).
  - `../EarInArm_v001/beats.json` lists each beat's start frame and first words.
  - When the VO arrives, get the word times with `pipeline/transcribe.py`, then run `pipeline/retime_to_vo.py` with anchors built from `beats.json`. That warps every keyframe so each beat starts on its word, and adds the VO strip at frame 1.

## Source and build
The source scripts are in `../EarInArm_v001/scripts/`. Build order:
1. `01_build_humans.py` (MPFB2 required)
2. `02_build_sets.py`
3. `03_animate.py`
4. `04_camera_fx.py`
5. `audit.py`
6. `pipeline/package_for_farm.py`

Review material is in `../EarInArm_v001/review/`:
- 1 s blocking sheet, 0.2 s polish sheets
- camera path plot
- audit output (`audit_C.txt`, `audit.txt`)

## Beats (start frame, first words)
| # | Frame | Line | On screen |
|---|---|---|---|
| 1 | 1 | Lose an ear in an accident… | Bald patient, side profile, shocked (hand to mouth), clean gauze dressing on the left ear. The camera pushes to the dressing. |
| 2 | 127 | A surgeon takes some cartilage… | Gloved hand on his chest. Dive through the chest into the rib-cage studio. A glowing cut line, then the gloved scalpel lifts out the pale cartilage block. |
| 3 | 343 | and carves it into the shape of an ear | The camera comes out of the block onto the tray. The surgeon carves, shavings fly and land on the tray, and the hands lift away to reveal the ear. |
| 4 | 565 | Then it's slipped into a pocket… | The ear is carried in forceps to the arm. The incision opens, the ear goes in, and the skin closes into a bump. |
| 5 | 775 | Inside your arm, it grows… | X-ray glow, then a dive under the skin into the tissue studio. Vessels draw on across the ear, pink skin creeps over it, and it pulses. |
| 6 | 1063 | Once it's fully developed… | Out through the skin. The incision reopens and the pink ear is lifted out with forceps. |
| 7 | 1309 | The blood vessels are connected… | Fly to the head. The ear is lowered into place, vessels reach in from both sides, and the join glows. |
| 8 | 1501 | and the skin is carefully stitched… | Macro: the needle holder travels along the front edge, and nine stitches appear in turn. |
| 9 | 1645 | giving you a brand new ear | The chair rises and the camera pulls out and orbits to the front. He touches the new ear and smiles; the nurse smiles. |

## Known issues
- **Gloves:** the surgeon's gloved hands look slightly inflated and simplified in the macros, because MPFB hands carry a smooth glove material.
- **Hand contact:** finger poses are procedural curls, so there's no per-finger contact solve on the scalpel or forceps. Prop-to-palm distance stays under 9 cm in the audit.
- **Shavings:** they are small curled rings, not true curls.
- **Fly-throughs:** two of them hold a near-flat skin frame for about 0.3–0.4 s (12.8–13.2 s and 17.8–18.0 s). They read as dives through skin, but they could be faster.
- **Nurse:** her left heel hangs about 7 cm up at the end of one walk (f686–696), and the surgeon's heel is about 4 cm up at f1381. Both are in the background, behind macro shots.
- **Tray ear:** the ear forms under the block during carving. The full ear shape on the tray reads clearly only from about 9.2 s.
- **Old ear:** the original left ear is collapsed to a small stump (shape key), not removed. The dressing hides it until the graft covers it.
- **Faces:** expressions (shock, sleep, smile) use MakeHuman expression targets on the body only. Eyebrows and eyelashes don't follow the shape keys exactly.
