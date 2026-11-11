# EarInArm_v001 — Plan (checkpoint A)

1080×1920, 60 fps, frames 1–1770 (29.5 s). Cycles CPU. One camera `CAM_Film` on one catmull spline (camera, aim, lens keyed every 3 frames), a new framing every ~1 s.

## World layout
There are two physical sets in one .blend, placed apart. The camera only moves between them by flying *through* a surface that fills the frame: skin on one side, a matching membrane on the other, so there's no visible cut.
- **OR set** (real, at the origin): a small procedure room with tiled floor, plaster walls, ceiling surgical lamps (CC-BY), instrument trolley + tray, IV stand, heart monitor with a moving trace (no text), and a scrub nurse in the background.
  - **Patient:** MPFB adult male, bald, plain tee. He sits in a reclining procedure chair with his left arm on an arm board.
  - **Surgeon:** MPFB male in teal scrubs (tinted casualsuit), with a cap, mask and blue nitrile gloves (body material split by hand weights).
- **Studio set** (explainer look, at x = +40 m): a soft cyan-to-white gradient cyclorama with a 3-point studio rig, holding a large-scale anatomy slice. It's used for beat 2 (rib-cage cross-section) and beat 5 (cross-section of the forearm tissue around the ear).

## Beat table (start frame = 1 + t·60)
| # | t (s) / frame | Line | On screen | Camera (one framing per ~1 s) |
|---|---|---|---|---|
| 1 | 0.0 / 1 | Lose an ear in an accident, and doctors can actually grow you a new one. | The patient sits up in the chair, side profile, shocked. His hand rises toward a clean white gauze dressing over the left ear (no wound visible). The nurse crosses behind; the monitor beeps. | Wide, low 3/4 (f1). Push in to his shocked face (f60). Arc round to the left-side profile on the bandage (f110). |
| 2 | 2.1 / 127 | A surgeon takes some cartilage from your rib cage | Gloved hand presses on his chest. Dive through the tee and skin into the studio, where a rib-cage cross-section (CC-BY thorax plus a pale-blue cartilage block on the lower ribs) turns slowly. A gloved hand with a scalpel cuts round the block and lifts it out. | Push into the chest (f127–175, the skin fills the frame; the hidden jump is at f170). Come out of the studio membrane into an orbit of the rib cage (f180–240). Push to macro on the scalpel lifting the block (f260–340). |
| 3 | 5.7 / 343 | and carves it into the shape of an ear. | In the OR at the trolley, the surgeon carves the block with the scalpel. Shavings fly as particles keyed as objects. The block morphs into the ear shape (a shape key from block to ear, plus the CC-BY ear model swapped in at the end). The patient is now reclined and asleep in the background, with the nurse handing over an instrument. | Pull out of the studio block, which becomes the real block on the tray (jump hidden in a full-frame cartilage close-up, f343). Orbit the surgeon's hands 180° (f350–560). |
| 4 | 9.4 / 565 | Then it's slipped into a pocket of skin on your forearm. | Macro on the forearm: a short clean incision line opens (shape key). Forceps slide the cartilage ear into the pocket, and the skin closes into an ear-shaped bump (shape keys on a skin patch that matches the arm). | Carry from the trolley along with the ear in forceps to the arm (f565–640). Drop low across the forearm (f640–700). Macro as the bump forms (f700–770). |
| 5 | 12.9 / 775 | Inside your arm, it grows new blood vessels and skin. | X-ray: the arm patch turns glassy. Dive under it into a studio tissue slice: red vessels grow over the cartilage ear (curves with animated bevel end), pink skin creeps across (gradient mask keyed), and the tissue pulses gently (scale and emission pulse on the heartbeat). | Push into the bump (f775–830, hidden jump at f828 inside the glassy skin). Two slow orbits around the growing ear (f830–1060). |
| 6 | 17.7 / 1063 | Once it's fully developed, the new ear is removed from your arm. | Back in the OR: the incision reopens and the surgeon's forceps lift out the finished pink ear. The bump flattens and the nurse holds out a dish. | Pull back out through the skin (hidden jump f1063). Rise to an over-the-shoulder of the surgeon (f1100–1200). Follow the lifted ear up (f1200–1300). |
| 7 | 21.8 / 1309 | The blood vessels are connected beside your ear canal, | The ear is carried to the head and lowered onto the left side of the head. Thin red vessel stubs on the ear and on the head reach out and meet, with a small soft glow pulse at the join. | Fly along with the ear to the head (f1309–1380). Arc to the side of the head (f1380–1440). Push to macro on the vessel join (f1440–1500). |
| 8 | 25.0 / 1501 | and the skin is carefully stitched to your head, | A curved needle in a needle holder pulls thread through. Stitches appear in sequence along the ear's edge (8 stitch objects scaled on in turn). | Macro tracking along the edge with the needle (f1501–1640). |
| 9 | 27.4 / 1645 | giving you a brand new ear. | The chair rises. The patient, now sitting up, touches the new ear with his left hand and smiles (expression shape keys). The nurse smiles. | Pull out and orbit to his front (f1645–1740), then settle with a slow drift (f1740–1770). |

`beats.json` will hold these start frames with their first words. Retiming happens later with `pipeline/retime_to_vo.py`.

## Assets (all free)
| Asset | Licence | Source |
|---|---|---|
| Human Ear Model, ssavish274 | CC BY | sketchfab e1f0f4b6fae54d59bdc3c6b2534eb411 (via Objaverse) |
| Thorax, Team Skeleton Wars | CC BY | sketchfab 83d435a04aa945898161eae1a2a9cf04 |
| Scalpel - Bisturi, centronina3d | CC BY | sketchfab 8e1d854692234e50b927e2383d0ae520 |
| Operating room lamps, House Doctor | CC BY | sketchfab 04a8ddf6e47141289ce0372e9e842167 |
| Metal Tray, Silver Shield | CC BY | sketchfab baf3242c524f4e4483d7f6df5f0d9848 |
| HDRI Surgery (Oliksiy Yakovlyev), HDRI Studio Small 09 (Sergej Majboroda) | CC0 | polyhaven |
| Floor Tiles 02, Grey Plaster (Rob Tuytel) | CC0 | polyhaven |
| Patient, surgeon, nurse | CC0 | MakeHuman assets via MPFB2 |
| Procedural (mine): chair, arm board, trolley, monitor, IV stand, forceps, needle holder, needle, thread, stitches, vessels, cartilage block, skin patch, cyclorama | — | — |

## Trickiest shots and how
1. **Dives through skin (beats 2, 3, 5 and 6) without cuts.** The camera pushes until a textured skin or cartilage surface fills the frame (DOF and lens widen). The location jumps in that frame to a matching full-frame membrane in the studio, then the camera pulls out. Each jump is a single frame, with both sides close to identical. I'll check this on 0.2 s sheets.
2. **Carving the block into an ear.** A block mesh with a shape key to an ear-like rough. A clean CC-BY ear fades in on top with a dissolve shader, while the surgeon's gloved IK hands hold the block and the scalpel strokes it. 20–30 shaving objects fly off on keyed arcs.
3. **Skin pocket and bump on the forearm.** A subdivided skin patch parented to the forearm bone with the patient's skin material, plus shape keys for the incision opening and the ear-shaped bump (a displacement from an ear depth map).
4. **Vessel growth.** About 20 bevelled bezier curves wrapped on the ear surface (shrinkwrap plus a keyed `bevel_factor_end`), with emission pulses.
5. **Hands planted.** IK hands keyed to world positions on the props. The audit checks hand–prop distances, hover and sink against the chair and floor, and the camera inside geometry.

## Risks
- Facial expressions (shock, smile) rely on MPFB face-pose bones/shape keys. If they look poor, I'll lean on head and body acting plus the hand-to-ear gesture.
- CPU time: 4 cores. Review stills only, at 270×480 and 8 samples.
