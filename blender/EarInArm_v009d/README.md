# EarInArm_v009d — farm package

29.5 s vertical short (1080×1920, 60 fps, frames 1–1770): growing a replacement ear in the forearm. Ready for RenderStreet. No render has been submitted.

- `EarInArm_v009d_60fps.blend`: the self-contained scene, 70 MB compressed, with every texture packed. Stored as plain git (no LFS).
  - It opens and renders in factory-startup Blender 5.2.2 with no add-ons.
  - One camera, `CAM_Film`, in one continuous move. There are no cuts, jumps or markers.
- `beats.json`: beat start frames (unchanged: 1, 127, 343, 565, 775, 1063, 1309, 1501, 1645; end 1770).
- `SETTINGS.md`: render settings and suggested test frames.
- `CREDITS.md`: the CC-BY block for the video description.
- `review/`: the acting-fix review material (see below).
- **Voiceover: none.** Retime later with `pipeline/retime_to_vo.py` using `beats.json`.

## Source and build
The source scripts are in `../EarInArm_v001/scripts/`. Build order: `01_build_humans.py` (MPFB2), `02_build_sets.py`, `03_animate.py` (uses `pipeline/hand_poses.py`), `03b_hands_v009b.py` (hand pass), `03c_dress_v009d.py` (scrubs, nurse dress), `04_camera_fx.py`, `pipeline/anim_look.py`, `05_anim_look_fix.py`, then `pipeline/package_for_farm.py`. The helper `../EarInArm_v001/work/build_v009b.sh` runs steps 3–5.

## Review (`review/`)
- `sheet_after_v009d_05s.jpg`: one frame every 0.5 s from the packed v009d file (270×480, 8 samples).
- `sheet_before_v007_05s.jpg`: the same frames from v007.
- `hand_contacts_v009d.jpg`: a close-up of every hand contact (14 shots).
- `qa_v009d.json`, `qa_v007_before.json`: `pipeline/qa_check.py` output (step 6, with `beats.json`).
- `clip_scan_v009d.json`: `pipeline/clip_scan.py` (director 3cfc53c, skin only) output (step 6).
- `ACTING_notes.md`: what was wrong in v007, what changed, and every remaining flag with its reason.

## Beats (start frame, first words)
| # | Frame | Line | On screen |
|---|---|---|---|
| 1 | 1 | Lose an ear in an accident… | Bald patient, side profile, shocked (both hands up, open, in front of his chest), clean gauze dressing on the left ear. The camera pushes to the dressing. |
| 2 | 127 | A surgeon takes some cartilage… | The surgeon presses his gloved hand on the chest. The tee turns x-ray glass and the rib cage shows inside. A glowing cut line circles the cartilage, the forceps lift the piece out, and he carries it to the tray. |
| 3 | 343 | and carves it into the shape of an ear | The chair reclines and the patient sleeps. The surgeon carves, shavings fly and land on the tray, and the hands lift away to reveal the ear. |
| 4 | 565 | Then it's slipped into a pocket… | The ear is carried in forceps to the arm. The incision opens, the ear goes in, and the skin closes into a bump. |
| 5 | 775 | Inside your arm, it grows… | X-ray: the forearm skin turns glassy around the pocket and the camera orbits the ear inside the real arm. Tapered, branching vessels grow over it and pink skin creeps across it. |
| 6 | 1063 | Once it's fully developed… | The x-ray fades. The incision reopens and the pink ear is lifted out with forceps. |
| 7 | 1309 | The blood vessels are connected… | Fly to the head. The ear is lowered into place, vessels reach in from both sides, and the join glows. |
| 8 | 1501 | and the skin is carefully stitched… | Macro: the needle holder travels along the front edge, and nine stitches appear in turn. |
| 9 | 1645 | giving you a brand new ear | The chair rises and the camera pulls out and orbits to the front. He touches the new ear and smiles; the nurse smiles. |

## v009d vs v009c: the client's rejection of v010 (23 items)
All 23 items are listed with their cause and fix in `review/ACTING_notes.md`. The new scripts are `EarInArm_v001/scripts/03c_dress_v009d.py` (scrubs under the clothes, nurse dress) and the two new checks `pipeline/limb_scan.py` and `pipeline/cam_clear.py`. `review/preview_v009d_270x480_every2nd.mp4` is the moving preview.

## v009c vs v009b: no starfish gloves (director reviews of v009b and v009d)
- **Cause of the starfish gloves:** the `GloveThin` Displace modifier (added in v003) pulled the hand surface in 3.2 mm along its normals. On the subdivided glove it thinned every finger and opened gaps between them, so the long, separate fingers read as splayed.
  - The bones and the skinning were correct: the evaluated finger curls match the keys, finger vertices sit within about 1 cm of their bones, and the weights sum to 1. A test render changes when the finger bones change.
  - `GloveThin` is removed in `03b_hands_v009b.py`.
- **Poses:** the forceps pinch now tucks the middle, ring and little fingers in a gentle gradient under the index (`pinch_tuck`), and relaxed hands use an even curl (`relaxed_even`). Both are added to the `hand_poses` table with spread 0.
- **Spread 0 everywhere:** every surgeon and nurse finger key is rebuilt from a clean `hand_poses` schedule with `spread=0`. The finger `HandLimit` side range is reset to ±10° (`LIMITS`).
  - Forceps hand: `pinch`. Thumb and index meet on the shafts; the middle, ring and little fingers curl under them.
  - Tray hands: `relaxed`.
  - Chest and scalp hands: `flat_palm`, fingers together.
  - Scalpel: `cup_hold`. Needle holder: `tripod`.
- **Nurse:** her arms hang at her sides from 9.5 s; she no longer carries the dish, which stays on the counter. She stands 12 cm further from the tray and lowers her arms while the surgeon passes her (9.5–10 s).
- **Camera:** pulled back 25 cm along its view line at 2.9–4.4 s (chest) and 20 cm at 14.5–17.2 s (x-ray). The 10 s key is raised above head height so the nurse no longer walks into the lens.
- **Released tools:** the forceps (331) and the scalpel (464) lie flat on the tray where the hand lets go. Before, they glided 22 cm back to a rest spot (qa PROPMOVE).
- **f1–45:** the surgeon stands 10 cm further from the patient's knee, so the patient's resting left hand no longer touches his hip.

## v009b vs v009: hands closed on what they hold (director review of v009)
`EarInArm_v001/scripts/03b_hands_v009d.py` runs after `03_animate.py`. Every contact uses `pipeline/hand_poses.py`:
- **Forceps hand (R, 1.7–5.6 s and 9.5–25 s):** `grip_object` (pinch) on the forceps shafts every 12 frames. The forceps and whatever rides in it (the chest piece, the ear) are then re-baked to the final pinch point, so thumb and index stay closed on the shafts.
- **Chest x-ray (2.6–4.6 s):** the free left hand is `place_hand` + `flat_palm` on the tee beside the forceps. The wrist follows the placed orientation only inside this window.
- **Tray (8.9–9.4 s):** the left hand pinches the carved ear (`grip_object`, pinch), and the right hand is flat on the tray (`place_hand`).
- **Ear placement (23.2–25 s):** the left hand is flat on the scalp above the ear (`place_hand` on the skin surface).
- **Patient's free (right) hand, reclined (8–27 s):** relaxed on the armrest (`place_hand`).
- **Nurse:** relaxed hands (v009d: arms at her sides, no dish).
- **Unclip pass:** a hand vertex inside or within 1 cm of a nearby body is pushed out along the surface normal at f13–49, 139–283, 562–599, 637–715, 1357–1396 and 1405–1465.
- **Camera:** starts beside the surgeon (no back-of-head fill at 0.5 s). The tray shot (8.7–10 s) is seen from across the tray. The arm shots (11.5–13.5 s and 16.5–18.8 s) are raised about 25–30 cm, so the hands and the arm with the ear read over the gown.

## v009 vs v007: acting fix (client stopped the render: "very weird actions")
Full list in `review/ACTING_notes.md`. In short:
- Every hand pose goes through `pipeline/hand_poses.py` (`add_hand_limits`, `apply_pose`). No finger angles are set by hand.
- No hand touches a face during the shock beat; both hands come up open.
- Beat 2 is restaged in the room as a chest x-ray, so both camera jumps and the rib studio (with its cloned surgeon) are gone.
- Tools sit at the thumb–index pinch point, and a 3-pass solve puts each tool tip on its target.
- Macros are pulled back to at least 15 cm with longer lenses.
- QA (v007 → v009): CLAW 104 → 0, FACEPRESS 20 → 0, CAMJUMP 2 → 0, EMPTY 29 → 0, INSIDE 1 → 0, ROLL 0 → 0, HOVER 1 → 1 (listed), FILL 70 → 15.

Earlier history (v002–v007) is in `../EarInArm_v007/README.md`.
