# BeethovenDeaf_v001: plan (checkpoint A)

- **Format:** 1080×1920, 60 fps, frames 1–1590 (26.5 s), Cycles.
- **Camera:** one camera, `CAM_Film`, on one Catmull-Rom spline through a framing about every 1 s. There are no cuts and no camera switches.
- **Timing:** built to the brief's target times. Frame = 1 + round(t × 60). `beats.json` is written for `retime_to_vo.py`.

## Beat table

| # | t (s) / frame | Line | On screen | Camera (one framing per ~1 s) |
|---|---|---|---|---|
| 1 | 0.0 / 1 | "He would bite down on a metal rod attached to his piano…" | Candlelit Viennese room at night. A composer in his 50s (MPFB generic face, wild grey hair, black tail coat, red cravat) leans into a wooden grand piano and **clamps his teeth on a thin brass rod** that runs from the piano case to his mouth. Candles flicker, a curtain stirs, sheet music is stacked on the desk. | 0.0 macro side-on of the teeth closing on the rod (jaw drops, then clamps) → 1.0 slide back into a profile close-up of the face and hair → 2.0 pull back along the rod to where it is fixed on the piano → 3.0 rise to a 3/4 front medium-wide showing composer, piano and room |
| 2 | 3.9 / 235 | "…as he played." | Both hands **crash across the keys**: big arm swings, shoulders and head drive, hair bounces. The rod stays clamped, and a candle flame gutters from the gust. | 3.9 drop fast to a low macro on the keys and fingers → 4.6 orbit up and round, starting to climb the rod |
| 3 | 5.2 / 313 | "The piano's vibrations traveled up the rod…" | **Cyan rings** pulse out of the soundboard and travel up the rod one after another, each with a soft glow. The rod shivers slightly. | 5.2 macro on the rod where it is fixed to the piano, rings being born → 6.2 ride along the rod beside a ring → 7.2 overtake toward the jaw → 8.2 arrive at the lips and teeth, the rings hitting the jaw |
| 4 | 8.6 / 517 | "…into his jawbone, and on to his inner ear." | **X-ray dive:** the skin, hair and coat around the head go glass-clear and then fade, revealing the skull (with real teeth on the rod). Rings run up the mandible to the temporal bone and the cochlea. The room dissolves into the clean cyan-to-white studio gradient. | 8.6 close side-on of the jaw while the skin fades → 9.6 push into the skull, mandible rings in frame → 10.6 travel along the jaw hinge to the temple → 11.6 approach the inner ear |
| 5 | 11.9 / 715 | "This sent the sound straight through the bones of his skull…" | The **whole skull glows** as a wave of light spreads from the jaw over the cranium. A cross-section cut-away of the ear opens beside the skull: ear canal, eardrum, the three tiny bones, cochlea. | 11.9 orbit to a 3/4 of the glowing skull → 13.0 rise over the cranium as the glow wave passes → 14.0 swing down to the side of the head → 15.0 push into the ear cross-section → 16.0 settle on the canal and eardrum |
| 6 | 16.4 / 985 | "…completely skipping his damaged eardrums…" | **Dull grey, torn eardrum.** A red pulse travels down the ear canal (the normal path), hits the torn drum and dies. The cyan rings arc *around* it through the bone straight into the cochlea. | 16.4 macro on the torn eardrum, red pulse arriving → 17.4 slide along the cyan bypass arc toward the cochlea |
| 7 | 18.4 / 1105 | "…so he could still hear." | The **cochlea lights up** (cyan to warm white, spiral fills from base to tip). Pull back out: skin, hair and room fade back in, and his **eyes close in bliss** with a small smile while he keeps playing. | 18.4 macro of the spiralling cochlea glow → 19.2 pull back through the temple to a 3/4 close-up of the face as the eyelids close |
| 8 | 20.1 / 1207 | "And by using this trick, Beethoven was able to keep composing music, even after he went deaf." | **Playing passionately**: big sweeps across the keyboard, his body rocking and hair flying. Sheet-music pages lift off the desk and spill across the floor, quill and inkwell on a side table, candles all around, curtains moving, rings still pulsing up the rod. | 20.1 pull out from the face → 21.0 crane to a high 3/4 → 22.0 orbit over the piano lid → 23.0 to 26.5 spiral up to a top-down overhead of him, the piano and the pages scattered on the parquet, still rising slowly at the end |

## Assets and licences

| Asset | Source | Licence |
|---|---|---|
| Old Wooden Grand Piano (Mikael H.) | Sketchfab c7c82e24… via Objaverse | CC BY 4.0 |
| Human Skull Model (Plastic) (Yu) and Human Skull (Nick Broad): one will be used after a look test | Sketchfab 017c6f4a… / 33174ba0… | CC BY 4.0 |
| Inner ear (R. van den Berg): cochlea and canals | Sketchfab ebd6a65b… | CC BY 4.0 |
| Ear (osuecampus): inner-ear backup with ossicles | Sketchfab 92d3fe7b… | CC BY 4.0 |
| Candelabra (AndreiVNK), Candles Asset Pack (Em Marshall) | Sketchfab f00558f1… / 56a68205… | CC BY 4.0 |
| Sheet Music (cScott), Piano Chair (conn0) | Sketchfab d444261c… / d6c16ede… | CC BY 4.0 |
| Herringbone Parquet, Plastered Wall 02, Painted Plaster Wall, Dark Wooden Planks, Wood Table Worn, Velour Velvet | Poly Haven, 2K | CC0 |
| HDRIs: Old Hall (room fill), Studio Small 09 (explainer) | Poly Haven, 2K | CC0 |
| Composer: base mesh, rig, old-male skin, hair, suit, shoes, eyes | MakeHuman/MPFB2 system assets | CC0 |
| Built procedurally | Brass rod, cravat, cyan rings, eardrum and ear-canal cross-section, room shell, window, curtains, quill and inkwell, side tables, page music (staff lines only, no text) | ours |

Sheet music uses staff lines and note blobs only, with no titles or legible text. The face is generic MPFB, not a portrait copy. No brands or logos appear anywhere.

## Trickiest shots and how I'll do them

1. **Teeth on the rod for the whole film.** The rod is pinned at the piano end. A `DAMPED_TRACK` and `STRETCH_TO` aim it at a "bite" empty parented to the head bone between the incisors. The body can sway and the teeth never leave the rod; the rod pivots a few degrees, as a real one would. The jaw bone is keyed to clamp the teeth.
2. **Big piano playing with planted hands.** The MPFB IK control rig gets hand targets keyed to key positions sampled from the piano mesh: a strike, a lift and a cross-hand sweep, with finger curls on contact. The hips stay planted on the bench and the feet on the pedals. The spine, shoulders and head drive the motion, constrained by the bite. The audit measures fingertip height above the key plane and hip-to-bench contact.
3. **Continuous dive from the room into the anatomy and back out (beats 4–7).** This is one camera with no cut:
   - A spherical x-ray porthole (the goat-rescue pattern) on every composer material, keyed open.
   - The skull is fitted inside the head and attached to the head bone, with the jaw following the jaw bone.
   - A cyan-to-white gradient backdrop sphere around the head fades in while the camera is inside the porthole, and the room lights dim. Everything reverses on the way out.
4. **Rings travelling along paths.** Each ring is a torus with emission, driven along a curve (rod → mandible → temporal bone → cochlea, and the bypass arc around the eardrum) by `FOLLOW_PATH` with keyed offsets, a scale pulse and keyed visibility. The red air-path pulse uses the same rig.
5. **Ear cross-section.** A procedural ear canal (a cut tube), a torn eardrum (a dull grey membrane with a ragged slit), ossicles, and the downloaded cochlea, scaled up about 2.5× for readability inside the translucent skull. The cut faces are solid pink-grey with clean bone, never gory.
6. **Pages flying in beat 8.** About ten sheet planes on keyed ballistic arcs with flutter rotation, each landing flat on the parquet. The audit checks that no page sinks into the floor.

## Schedule
- A: this plan.
- B (21:45): blocking sheet.
- C (23:45): 0.2 s sheets and audit.
- D (01:00): package in `blender/BeethovenDeaf_v002/`.

## Checkpoint B (blocking)
- **Sheet:** `review/B_blocking_1s.jpg`, 1 still per second.
- **Camera path:** `review/B_camera_path.png`, a top view and a height curve coloured by beat. It is one `CAM_Film` on one Catmull-Rom spline with 33 framings.
- **Build:** `scripts/01…05`, run in order. See the README in v002 once it is packaged.
- **Known at B:**
  - Hand contact is not audited yet.
  - A red shape shows under the skull at about 14 s (still finding its source).
  - Lighting is not graded yet.
