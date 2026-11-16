# B24 TongueFromArm, Phase 1 plan

ConnectB24 · branch `claude/connectB24-tongue-from-arm` · 1080×1920 · 60 fps · Cycles · hard cuts (one camera per shot, marker-bound).

**Timing is provisional.** It follows the reference sheet's pacing (22 s, about 1 s per reference line), shots 1–1392 (23.2 s).
In Phase 2 the shot windows move to the VO word frames (`1 + round(s × 60)`). Each set's action is one continuous clip that runs
well past its shots (OR and diagram clips to frame 1110, ward to 1520), so shots are trimmed, never stretched.
Shot list: `shots_provisional.json`. Build: `scripts/01_chars.py` → `02_dress.py` → `03_or.py` → `04_sets.py` → `05_shots.py`.

## Sets and cast
- **OR** (reused from EarInArm v011: room, teal reclining chair, arm board, lamps, trolley). Patient reclined asleep (eyes closed, breathing),
  surgeon (cap, mask, gloves) at her head, nurse at the arm board.
- **Diagram** (sky-blue gradient, colour-coded, glossy): real CC-BY dental model (teeth + gums, upper jaw hinged open) and a real CC-BY tongue model.
  The tongue is split into the front 90% (with a purple bumpy tumour) and the back stump. A forearm model (her own skin mesh) with an
  oval window: the red, fibred muscle flap lifts out with red artery, blue vein and yellow nerve strands. In the mouth, the flap
  (a slab-shaped copy of the tongue piece) sits on the stump, vessels grow back to red/blue/yellow neck stubs, stitch rings appear,
  then the slab morphs into the tongue's shape and turns tongue-pink.
- **Ward**: light-blue room, CC-BY hospital bed, pillow, blanket, bedside table, monitor, window with a bright sky panel, door to a corridor.
  Patient sitting up in bed (soft-blue gown), female doctor (white blouse, bare hands) at the right bedside, daughter (blue outfit) walks in.

## Beats and shots (reference order)
| Beat (ref s) | Shot | Frames (prov.) | Who and what, physically | Camera |
|---|---|---|---|---|
| They surgically removed (0–1) | S01 | 1–72 | OR: patient asleep in the reclined chair, surgeon leaning over at her head, hands held up in front of his chest (sterile pose). Nurse at the arm board. | High three-quarter front, slow push-in. |
| 90% of her tongue (1–3) | S02 | 73–132 | Diagram: open mouth model, tongue with the purple tumour. | Front-high, push-in. |
| | S03 | 133–192 | The front 90% of the tongue lifts up and out; the small stump stays. | Three-quarter high, tilts up with the piece. |
| because it had cancer (3–4) | S04 | 193–252 | The removed piece floats and turns, purple tumour on top. | Close orbit. |
| they cut a muscle (4–5) | S05 | 253–312 | OR: her arm on the arm board under the drape lamp; the nurse leans in, looking at the forearm. | Side-high over the board, push-in. |
| out of her arm (5–6) | S06 | 313–372 | Diagram forearm: the oval red muscle flap lifts out of the forearm with its artery, vein and nerve strands. | Three-quarter high, push-in. |
| They connected (7) | S07 | 373–432 | Mouth: the flap (slab) settles onto the stump; red and blue vessels grow from it to the neck vessels. | Three-quarter high. |
| the veins inside her mouth (8) | S08 | 433–492 | Close on the junctions: stitch rings close on artery and vein. | Close side. |
| and stitched the nerves (9) | S09 | 493–552 | The yellow nerve grows and gets its stitch. | Close, other side. |
| (stitching) | S10 | 553–612 | OR: surgeon's masked face, concentrating, small head moves; lamp behind. | Medium close, slow drift. |
| The muscle was shaped (10) | S11 | 613–672 | Diagram: the flat flap starts to take the tongue's shape. | Front-high. |
| onto what was left of her tongue (11–12) | S12 | 673–732 | Shaping completes, colour turns tongue-pink. | Other side. |
| matching its shape (13) | S13 | 733–792 | Full mouth with the new tongue. | Slow orbit. |
| its shape (14) | S14 | 793–852 | OR: surgeon straightens up and looks across; patient resting. | Wide three-quarter. |
| doctors said (15) | S15 | 853–942 | Ward wide: patient sitting up in bed, doctor at the bedside talking with a small hand gesture. Logo poster on the wall. | Foot of the bed, slow push. |
| she would never speak (16) | S16 | 943–1032 | Doctor medium: explains, small head shake. | Front three-quarter. |
| just days later (19–20) | S17 | 1033–1122 | The daughter walks in through the door (arms swinging). | From the bedside toward the door, pan. |
| she said hello (17) | S18 | 1123–1212 | Patient close: turns to the door, smiles, mouth opens for "hello". | Close front three-quarter, push-in. |
| to her daughter (18) | S19 | 1213–1302 | The daughter walks up to the left bedside; the doctor watches. | Wide from the foot, push. |
| (end) | S20 | 1303–1392 | Mother and daughter, both faces readable; the mother speaks again. | Medium, both faces. |

## DA KRAS FILMS logo
- **One placement:** a wall poster on the ward's back wall (dark logo on white, flat-on to the S15/S19 cameras, about 25–30% of frame width, on screen for 1.5 s+).
  The ward beats are the happy ending, so it is not in a sad moment. Nothing in the OR or the diagrams carries a logo.
- A second placement (e.g. a gift bag the daughter carries) is possible if you want one; not planned (it would add a hand grip).

## Risky shots and the simplest safe staging
- **Surgery:** never a real open mouth. All cutting, removing, connecting and stitching is shown on the clean colour-coded diagram model
  (teeth, gums, tongue, red muscle, red artery, blue vein, yellow nerve). No blood, no wounds. The OR shots show people only (asleep patient, faces readable).
- **Instruments in gloved fingers:** avoided. The surgeon and nurse keep their gloved hands up in front of their own chests (sterile pose); no tool touches the patient.
  If you want a scalpel shot, I'll add an insert with `grip_object` on the EarInArm scalpel in Phase 2.
- **Arm muscle:** shown on the forearm diagram only; on the real patient her arm just rests on the arm board.
- **Ending:** mother and daughter faces readable; no hug (no arms crossing bodies). The daughter stops at the bedside; the mother turns to her and speaks.
- **Patient legs** are under the blanket in the ward; in the OR chair her leggings are dark.

## Known items for Phase 2
1. Lip-sync for "hello" is a small jaw open/close only.
2. The OR camera paths may be re-aimed once the VO sets the shot lengths.
3. The four package checks run again on the packed Phase 2 file.

## P1b fixes (director notes on cf4dcf0, one rebuild)
- **A. Ward exposure:** ceiling lights 90→40 W, fill 60→22 W, ceiling panel and window emission lowered, walls/sheets/bed frame a touch darker, so the whites read with shading.
- **B. Patient clothing:** a loose short-sleeved top and trousers in a navy-dotted hospital print (the surgeon's MPFB scrub suit refitted to her body with Surface Deform), with a normal crew neckline. The skin-copy gown and its neck seam are gone.
- **C. OR patient re-staged with IK** in the reclined chair: hips on the seat (item 1 fixed), feet on the leg rest, right forearm on the chair arm (no crossing), left forearm forward on the arm board (re-angled to run forward beside the chair arm). No arm out to the side. S01 and S14 are shot from her left side, so her legs run across the frame instead of toward the lens.
- **D. Surgeon:** a mask over nose and mouth and a fitted scrub cap, both built from his own face/scalp surface; the old ball cap and low mask were removed. His hands are held low in front of him (item 6).
- **E. Nurse:** removed from the film (simplest re-stage, LESSONS 2.15). She blocked the arm shots, and her fringe and waist band were faults. The surgeon is the only OR staff.
- **F. Blanket:** a soft sheet shaped over her legs (ray-cast onto her legs, smoothed, draping over the mattress sides); her hands rest on top of it (item 2 fixed); shoes hidden in bed.
- Item 3: S19 reframed wider left. Item 4: the logo poster moved to the left of the back wall (visible whole in S15 and S19, never behind her head in S18). Item 5: S20 is now a reverse angle on the daughter's face. Item 7: the doctor nods, shakes her head and gestures through S15–S16. Item 8: S09 is wider than S08.

## P1b checks
- **Sheets:** `review/P1b_sheet_3frames_1.jpg` (S01–S10) and `_2.jpg` (S11–S20): first/middle/last of every shot at 540×960, Cycles 8 spp, every cell looked at.
- **`body_prop_cross`** (`review/body_prop_cross_P1b.json`, the 60 sheet frames; the script copy `scripts/bpc_frames.py` now tests each prop only against edges inside its own bounds, and only counts hits within 8 m of the shot's camera, since the sets are 40 m apart):
  - OR (S01, S05, S10, S14): 3 edges of her right little-finger tip touch the chair arm (hand resting on it). No other contact: hips on the seat, right forearm on the chair arm, left forearm on the board, surgeon clear.
  - Ward: hits remain between the bed patient and the blanket/mattress, all **under the opaque blanket**: legs, feet and toes sit a few cm into the mattress or pierce the sheet from below, and the blanket's top edge starts inside her waist (tucked look). Her fingertips dip a few mm into the soft blanket top. None of this shows on the sheet; I'll clean the leg/foot depth in Phase 2.

## P1 checks (first round, Nov 16)
- **Sheets:** `review/P1_sheet_3frames_1.jpg` (S01–S10) and `_2.jpg` (S11–S20): first, middle and last frame of every shot at 540×960, Cycles 8 spp. I looked at every cell.
- **`body_prop_cross`** (`review/body_prop_cross_P1.json`, the 60 sheet frames, props: chair parts, arm board + drape, tray, trolley, bed parts, blanket, sheet, pillow, table, door frame, walls). It reports real crossings that I fix before Phase 2:
  1. **OR patient sits 3–5 cm into the chair seat** (the EarInArm pose was a taller male), and her right forearm passes through the chair's arm/back. Fix: raise her root and re-pose the right arm onto the armrest.
  2. **Ward patient's forearms dip into the blanket top** (wrists at the surface, forearms slope in). Fix: raise the hands about 5 cm. Her legs and feet are inside the blanket volume by design (hidden under it); the blanket is opaque.
  Nothing else is crossed (no surgeon/nurse/doctor/daughter hits).

## Faults I see on the sheet, to fix before Phase 2
- S19 first/last: the daughter is half out of frame on the left (reframe wider left).
- S18: the logo poster sits right behind her head and "FILMS" is cut by the right edge (move the camera so the poster is either whole or out).
- S20: over-the-shoulder; the daughter's face is not readable here (it is in S17). I'll add a reverse angle or turn her 3/4.
- S14: the surgeon's gloved hands are close to her face (no contact); I'll pull them lower.
- S16: the doctor is fairly static (small head moves only); the hand gesture is not reading; I'll add a clear nod/gesture.
- S08/S09: similar macro framings; vessels/stitches are small. I'll widen one of them.
