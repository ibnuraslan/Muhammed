# SurgeonBrandsLivers_v001 — PLAN (checkpoint A)

1080×1920, 60 fps, frames 1–1710 (28.5 s). Cycles CPU. One camera `CAM_Film`, one continuous Catmull-Rom spline, a new framing about every 0.8–1.2 s. Beat start frame = 1 + round(t × 60).

## World layout (one connected world, so the camera can travel without cuts)
| Set | Where | Look |
|---|---|---|
| **Operating room (OR)** | centre, origin; table along X at z≈0.95 | real set: tiled walls/floor, twin surgical lamps, monitors (wave lines, no text), instrument trolley, IV pole, nurse |
| **Macro studio** | directly under the OR table, z = −6 (a 10 m dome, cyan→white gradient) | clean explainer look: realistic liver, soft studio key + rim |
| **Home** (living room) | through the OR's east wall, x ≈ +7 | real set: wood floor, sofa, lamp, window with daylight, coffee table, TV (off), plant |
| **Hearing room** | through the OR's west wall, x ≈ −7.5 | wood panelling, raised panel desk, 3 panel members, lectern, certificate + gavel; translucent "anatomy wall" behind the surgeon |

The camera moves between sets by **diving through skin/table** (OR ↔ studio) and **flying through walls** (OR ↔ home ↔ OR ↔ hearing). Each pass-through is 8–14 frames with motion blur.

## Beat table
| # | t (s) / frame | Line | On screen | Camera (one framing per ~1 s) |
|---|---|---|---|---|
| 1 | 0.0 / 1 | "During a transplant, a surgeon used a high-powered laser to burn his initials into the patient's new liver." | OR mid-surgery: surgeon 1 (generic, cap + mask) over the draped patient, nurse passing instruments, lamps blazing, monitor pulsing. He raises a medical argon-beam pen. Inside (studio): the glistening donor liver; the tip writes a glowing **S** then **B**, sparks spit, a wisp of smoke curls up, the tissue darkens behind the glow. | f1 high over the lamps, crane down past a lamp (f60) → push over his shoulder onto the pen (f110) → dive into the abdomen (f130–145) → studio macro on the tip writing S (f150–210, slow orbit) → rack/arc across to B (f210–270) → pull back to the whole liver, letters glowing (f270–300) |
| 2 | 5.0 / 301 | "Then he stitched her up and acted like nothing had happened." | Rise back out of the abdomen: the needle driver pulls sutures; stitch knots appear one by one along the incision in the drape window. He drops the instruments on the tray, pulls his mask down: a calm, smug smile, a little nod; nurse oblivious in background. | rise up through the body (f300–315) → top-down on the stitching hands (f330) → slide along the incision (f390) → crane up and orbit to his face (f440–500) → mask comes down in a close-up (f500–560) |
| 3 | 9.4 / 565 | "a week later," | Wall calendar beside the OR door: pages flip forward 7 days (blank grid squares, a red cross marches across; no numbers or words), motion-blurred. | whip-pan from his face to the calendar (f565–585) → drift past it (f590–630) and fly through the wall (f630–645) |
| 4 | 10.6 / 637 | "the new liver started to fail." | Home: the woman (patient, casual clothes) is carrying a mug, freezes, doubles over clutching her right side, drops the mug (bounces, coffee splash), sags onto the sofa arm. An x-ray glow of her liver shows through her shirt, pulsing from blue to red. Daylight through the window, curtains swaying, a cat-free generic room. | out of the wall into a low wide (f650) → push in as she buckles (f700) → orbit to the x-ray glow on her side (f740) → whip back toward the OR wall (f770–790) |
| 5 | 13.0 / 781 | "She went back into surgery, but this time with a different doctor," | OR corridor doors swing open; the hospital bed rolls in pushed by the nurse (hands on the rail, walking); the woman on it. Surgeon 2 (a different person: female, different build/skin/hair) walks in snapping on gloves, takes position at the table. | fly through the wall into the OR (f790–805) → track beside the rolling bed (f830–900) → low angle as surgeon 2 steps in (f920–980) → arc behind her to the table (f990–1044) |
| 6 | 17.4 / 1045 | "who soon found the initials inside." | Studio macro: purple-gloved hands lift the liver up into a shaft of light; it turns and the **SB** brand is revealed (dark seared letters, faint ember glow). Back in the OR: surgeon 2's eyes widen over her mask, brows up, she leans back. | dive into the abdomen past her hands (f1045–1060) → studio: rise with the liver (f1070–1130) → orbit to the brand (f1130–1180) → rise out (f1180–1195) → push into her widening eyes (f1195–1230) |
| 7 | 20.5 / 1231 | "The surgeon admitted it wasn't the first time he'd branded a patient," | Hearing room: surgeon 1 (now in a suit) at the lectern, head drops, shoulders slump, hands spread in a confession gesture, nods. Behind him a translucent anatomy wall: five ghostly x-ray livers in a row, each with a faint glowing brand, lighting up one after another. Panel members lean in, one takes notes. | from her eyes whip-pan through the west wall (f1231–1250) → slide across the anatomy wall (f1260–1320) → orbit around the lectern (f1320–1400) → low angle up at the panel (f1400–1500) |
| 8 | 25.0 / 1501 | "and he eventually lost his medical license." | The chair raises the gavel and slams it down (squash on the block, papers jump, dust in the light shaft). A panel member brings a stamp down on the license certificate (seal and lines only, no readable text): a red diagonal mark. Surgeon 1 closes his eyes. | from the panel push down to the gavel (f1501–1560) → push onto the certificate as the stamp lands (f1580–1640) → slow settle with a gentle drift (f1640–1710) |

`beats.json` gets these start frames: 1, 301, 565, 637, 781, 1045, 1231, 1501.

## Characters (MPFB2 + MakeHuman CC0, generic, no likeness)
- **Surgeon 1** — male, 40s, mixed features; scrubs (tinted `male_casualsuit` → surgical teal), surgical cap (modelled shell), mask (CC-BY model, rigged to head; lowered by rotating to the chin); hearing-room suit `male_elegantsuit01` (swap visibility).
- **Patient** — female, 30s; gown on the table/bed, casual clothes at home; under a surgical drape in the OR.
- **Surgeon 2** — female, 40s, different skin tone and build; scrubs, cap, mask, purple nitrile gloves (hand-skin tint).
- **Nurse** — male, scrubs; passes instruments, pushes the bed.
- **Glove hands (studio)** — a copy of surgeon 2 with a Mask modifier keeping only forearms + hands, gloved.
- **Panel** — 3 seated members (`male_elegantsuit01` / `female_elegantsuit01`), upper-body acting only.
- Smile, eye widening and brow raise use the MakeHuman default rig face bones (oris/risorius/levator, orbicularis, oculi) keyed directly.

## Assets and licences
| Asset | Source | Licence |
|---|---|---|
| MPFB2 humans, clothes, hair, skins | MakeHuman system assets | CC0 |
| Human liver ("Liver" by Thata, cf66ae46) | Sketchfab via Objaverse | CC-BY 4.0 |
| Operating table + surgical lamp (shashkinv1ad, e3a45122) | Sketchfab via Objaverse | CC-BY 4.0 |
| Hospital bed (Yvo Pors, 60651eac) | Sketchfab via Objaverse | CC-BY 4.0 |
| Gavel (rutesh sakpal, 44581bee) | Sketchfab via Objaverse | CC-BY 4.0 |
| Surgical mask (BrightMoon, f54ed08e) | Sketchfab via Objaverse | CC-BY 4.0 |
| Sofa (katjagricishina, 03550a35) | Sketchfab via Objaverse | CC-BY 4.0 |
| HDRIs, tiles, plaster, wood, fabric; TV, coffee table, plant, armchair, table | Poly Haven | CC0 |
| Argon pen, sutures, calendar, studio dome, certificate, stamp, monitors, x-ray livers | modelled in script | ours |
Exact authors go in `CREDITS.md` from `credits.json` and the Poly Haven printout.

## Trickiest shots and how
1. **Writing SB on the liver.** Two curves laid onto the liver surface (shrink-wrapped, projected along the camera axis); a glowing bevelled tube grows along each with keyed `bevel_factor_end`, the pen tip is constrained to the growing end (Follow Path offset keyed in sync). A darker "seared" copy trails behind the glow and stays. Sparks are script-keyed ballistic streaks (no simulation). Smoke = a few soft volumetric puffs with a noise density, kept small for render cost.
2. **Continuous camera through bodies and walls.** One spline. The dives are aimed through the drape window; the inside of the patient/table is hidden by keeping the pass-through to ~10 frames with motion blur and a dark interior "skin" shell so it reads as a dive, not a glitch. Wall fly-throughs go through a hollow section of wall so the frame never shows back-faces.
3. **Hands that grasp.** IK hands (`anim_lib.make_human_ctrl`) keyed to prop handles: pen, needle driver, mug, bed rail, liver, gavel, stamp. Props parent to the hand only between grasp and release; fingers curl before the prop moves.
4. **Planted feet.** `Human.walk` for the nurse pushing the bed and surgeon 2 walking in; everybody else stands with keyed feet that never move unless stepping. Audit script checks foot height and slide per frame.
5. **Face acting.** Smile, mask-down, eye widening from face bones; checked in close-up stills.
6. **Render cost.** Many sets, so each set is hidden from render (keyed `hide_render`) when the camera is elsewhere; textures at 1K–2K; HDRI 2K. Target .blend < 150 MB.

## Schedule
A 19:20 plan · B 21:45 blocking (1 s sheet + camera path) · C 23:45 polish (0.2 s sheets + audit) · D 01:00 package in `SurgeonBrandsLivers_v002/`.

## Unsure / flags
- The brief says "laser"; the staging says "medical argon-beam tip". I use a pen-like argon/laser coagulator with a bright cyan-white tip glow; no weapon or real device detail.
- 'SB' is the only lettering in the film (it's the story's brand). No other text anywhere.
