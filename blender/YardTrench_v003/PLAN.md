# B37 YardTrench v002: built to the VO

VO: `YardTrench_v002_VO.mp3` (30.2 s), transcribed with `pipeline/transcribe.py` (`YardTrench_v002_VO.words.json`). Shot start = `1 + round(word_seconds × 60)`; film frames 1–1825 (frame_end 0.5 s after "deep.").
The VO wording differs from the reference: it ends "...could eventually turn into a trench several feet deep" (no "perfect for war"), so the playful helmet-and-sandbags peek plays on "turn into a trench" (S22) and the film ends on the depth shot (S21, walls above his head) on "several feet deep". The reference's S23 crane-out is dropped.
Every action is procedural and keyed at 1× to its VO window (no time-stretch). Director notes applied: relaxed bent elbows on every standing pose (hands beside the thighs), weight shift and looks in S21, turned-to-camera look in S20.

| Shot | Frames | VO words | What happens |
|---|---|---|---|
| S1 | 1–64 | If you walk across the | Boy walks the line on the lawn (front three-quarter, tracking). |
| S2 | 65–148 | exact same strip of grass | Top-down: he walks the same strip as it wears bare (time-lapse ground). |
| S3 | 149–240 | every single day, | High aerial: house, yard, the worn strip; the boy small on it. |
| S4 | 241–314 | your feet slowly crush | Shoe level: he walks away to the house over flattened blades. |
| S5 | 315–383 | the plants and compact | Low angle, full body: he walks past over the pressed blades (v002b). |
| S6 | 384–481 | the soil underneath. | Low angle: full body walking across the cut-away block; the grey stones below squash and pack (v002b). |
| S7 | 482–570 | Over time, the path becomes | Top-down close: the strip turns bare, shadows sweep. |
| S8 | 571–665 | bare and hard. | Top-down: it dries and cracks hard (time-lapse). |
| S9 | 666–756 | Then, when it rains, | Rain starts; the boy looks up, palm out. |
| S10 | 757–816 | water can't soak into | He looks down at the hard strip in the rain. |
| S11 | 817–871 | the packed soil as | Close: puddles form on the cracked crust. |
| S12 | 872–950 | easily, so it starts | Puddles spread and join along the strip. |
| S13 | 951–1015 | flowing through the groove | Ground level: water flows along the groove toward us. |
| S14 | 1016–1076 | instead. | Top-down: the stream flowing. |
| S15 | 1077–1228 | Each storm carries away a little more dirt, | Wide time-lapse: storm and sun alternate, the strip sinks to a groove. |
| S16 | 1229–1358 | making the path deeper and deeper. | Ground level: the groove deepens (~70 cm). |
| S17 | 1359–1415 | And if this keeps happening | Decades later: the grown man walks beside the groove toward us (logo on shirt). |
| S18 | 1416–1481 | for decades, | Top-down: he walks the groove floor as it deepens to a trench. |
| S19 | 1482–1560 | under the right conditions, | Wide: house, yard, the full trench; he walks in it. |
| S20 | 1561–1628 | that tiny footpath | From the rim: he stands deep in the trench, turns and looks up at us. |
| S22 | 1629–1729 | could eventually turn into a trench | Sandbags on the rims; in a helmet he rises on the fire step and peeks over (the playful war trench). |
| S21 | 1730–1825 | several feet deep. | Inside the trench: walls above his helmeted head (the depth, no text); weight shift, looks up at the rim with an open-hands shrug; legs lit by a fill (v002b). |

---

## Phase 1 plan (reference timing, kept for the record)


ConnectB37 · branch `claude/connectB37-yard-trench` · 1080×1920 · 60 fps · Cycles · hard cuts (one camera object, keyed every frame; a cut is a jump between two frames, smooth move inside each shot).

**Timing is provisional.** It follows the reference sheet's pacing (`briefs/batch2/B37_YardTrench_reference_1fps.jpg`, 38 s, one frame per second), so the film is frames 1–2310 (38.5 s).
In Phase 2 every cut moves to the VO word frames (`1 + round(s × 60)`) by passing a timing JSON to `scripts/03_anim.py`. Every character action is **procedural** (walk solver at a fixed speed in m/s, stands and breaths at fixed rates), keyed at 1× from the shot start to the shot's cut. A longer VO window simply generates more walking or standing at the same speed, and a shorter one generates less, so nothing is ever time-stretched. I tried a fixed 30% overrun first, but each shot's overrun keys bled into the next shot of the same character (the S09 raised hand leaked into S10), so actions now end exactly at the cut. The environment time-lapses (groove depth, bare/dry strip, water level, sun) are scene states keyed to each shot window, not character animation.
Shot windows: `shots_provisional.json`. Stills: `review/P1_sheet_3frames_540.jpg` (first, middle and last frame of all 23 shots, 540×960, Cycles 8 spp).

The build is fully scripted: `scripts/01_chars.py` → `02_sets.py` → `03_anim.py` (+`03a_shots.py`). A full rebuild takes about 30 s.

## Cast and set
- **Boy** (beats 1–3): generic MPFB teen (from HeadsetBullet_v008), navy T-shirt, blue jeans, sneakers.
- **Man** (beats 4–5, "decades" later): generic MPFB adult (from WaterTubes_v006), white top with the DA KRAS FILMS print, blue jeans.
  Both have the eye fix, elbow IK limits opened (-40°..100°), wrist limits in YXZ with forearm twist free, and hand limits. Relaxed hands throughout; no held props at all.
- **Yard:** one set. A two-storey white clapboard house (CC-BY model, clean painted materials), wooden privacy fences, a mown lawn (CC0 Poly Haven grass texture plus geometry-node grass blades, dense near the path), HDRI sky with soft clouds.
- **The worn line** runs from the porch to the back fence. The ground is one mesh whose groove is driven by three shape keys keyed in sequence: **Rut** (3.5 cm compacted strip) → **Groove** (30 cm) → **Trench** (1.95 m, about 6 ft, with steep soil walls). The ground material and the grass blades read the same keyed values: `bare` (grass thins away), `crush` (blades lie flat), `dry` (fresh mud → cracked hard crust), `wet` (rain darkening). Blades also flatten under the boy's shoes (probes on his feet).
- **Rain:** geometry-node streaks driven by a keyed clock (no Scene Time). **Water:** a flat sheet clipped by the ground, its level and flow keyed, so puddles form in the rut's hollows and join into a stream.
- **Cross-section block** (S06, its own spot): lawn on top, soil clods below, on the sky.

## Beats and shots (reference order, subjects and framing)

| Beat (ref s) | Shot | Frames (prov.) | Who and what, physically | Camera |
|---|---|---|---|---|
| If you walk across (0–1) | S01 | 1–60 | The boy walks along the lawn on the line toward the back fence; arms swing, face readable. A faint worn line under his feet. | Front three-quarter at chest height, tracking backward with him; house behind him. |
| the exact same line (1–3) | S02 | 61–180 | Top-down: he walks the line while it wears bare under his steps (time-lapse on the ground, walk at 1×). | Straight down from 7 m, drifting with him. |
| in your yard every day (3–5) | S03 | 181–300 | High aerial: house at the top, the worn strip from the porch to the back fence, the boy small on it. | Straight down from 24 m, slow crane-up. |
| Your feet slowly crush (5–7) | S04 | 301–420 | Shoe level: his sneakers walk away from the lens toward the house over flattened blades; the reveal climbs to his whole body and the house. | Low (20 cm) behind him, slight push. f/stop sharp, no DOF. |
| the grass (7–8) | S05 | 421–480 | Side, low: each shoe lands and the blades under it press flat. | Low side tracking at 30 cm. |
| and compact (8–9.5) | S06 | 481–570 | Cut-away block of lawn and soil: he walks across the top (legs and block in frame); the clods under his steps squash and pack together. | Front of the block, slow truck right. |
| causing the strip (9.5–11) | S07 | 571–660 | Top-down close: the strip turns bare, blades vanish, shadows sweep (time-lapse). | Straight down from 2.7 m, slow push. |
| to turn bare and hard over time (11–14) | S08 | 661–840 | Top-down closer: the mud dries and cracks into a hard crust; the sun swings round (time-lapse). The reference's clock overlay is replaced by the moving shadows (no on-screen graphics). | Straight down, 1.9 → 1.35 m push. |
| Now when it rains (14–15) | S09 | 841–900 | Rain starts. The boy beside the strip looks up and raises his right palm (elbow bent, arm clear of his body). | Low front, looking up at his face, house behind. |
| water (15–16) | S10 | 901–960 | He looks down at the hard strip in the rain. | Side-front three-quarter, his face toward the lens. |
| can't soak in (16–17) | S11 | 961–1020 | Close on the cracked strip: water collects in puddles on the crust. | 0.6 m above, looking down at 45°. |
| as easily. So it starts (17–19) | S12 | 1021–1140 | The puddles spread and join along the strip. | Higher three-quarter, looking along the strip toward the house. |
| flowing along the groove instead (19–21) | S13 | 1141–1260 | The water runs along the groove toward the lens, rain falling. | Ground level (35 cm) looking up the groove, slow push. |
| the groove instead (21–22) | S14 | 1261–1320 | Top-down: the stream flowing. | Straight down from 2.2 m, drifting with the flow. |
| Each storm scrapes a little more soil away (22–25) | S15 | 1321–1500 | Wide time-lapse of the house and yard: storm (dark, rain) and sun alternate and the strip sinks into a groove. | High three-quarter wide, slow push. |
| causing the groove to grow deeper (25–27) | S16 | 1501–1620 | Ground level: the groove deepens to about 70 cm with grass edges. | Low along the groove, slow push. |
| And if you walk (27–28) | S17 | 1621–1680 | Decades later: the grown man walks beside the groove toward the lens, logo readable on his shirt. | Front medium, pulling back. |
| back and forth for several decades (28–31) | S18 | 1681–1860 | Top-down: he walks the groove floor as it deepens into a trench under him (his feet follow the floor every frame). | Straight down from 6 m, drifting. |
| while the conditions are just right (31–33) | S19 | 1861–1980 | Wide: house, yard and the full trench; he walks in it. | High three-quarter wide, slow push. |
| That small groove (33–34) | S20 | 1981–2040 | He stands deep in the trench and looks up toward the rim. | From the lawn rim looking down at 45°. |
| into a six-foot (34–35.5) | S21 | 2041–2130 | Inside the trench: he stands with the walls rising above his head (the depth is read by the person, no "6 FT" text). Logo on his shirt. | In the trench at chest height, 2.6 m in front of him. |
| deep trench (35.5–36.8) | S22 | 2131–2208 | Sandbags line both rims; in a helmet he rises on the fire step and peeks over, scanning left and right. | Low on the lawn behind the sandbags, facing him. |
| perfect for war (36.8–38.5) | S23 | 2209–2310 | Playful pull-back: the yard is now a "war trench" with sandbags, the helmeted man peeking out. **No zombies, no gore, no severed head** (the reference ends on one). | Crane-up and back to a high wide. |

## DA KRAS FILMS logo
- **One placement:** printed on the man's white shirt front (dark logo, about 21 cm wide), mapped in the shirt's rest space so it moves with the cloth. Readable in S17 (front medium, about 25–30% of the frame width, about 1 s) and S21. It is never on skin and never over the key action.
- A second placement is not planned (the boy's scenes have no natural brand surface). I can add a cardboard box on the porch if you want two.

## Risky shots and the simplest safe staging
- **Feet on the ground:** the walk solver plants each foot on the evaluated ground at the frame being keyed, so feet stay on the sinking trench floor in S18–S19 with no sliding. Checked in the first, middle and last frames.
- **Groove erosion:** one clean time-lapse driven by shape keys and material values (no particles, no simulations), so it reads as one continuous change and is exact on every frame.
- **Depth without text:** S20–S21 show the man standing in it with the walls above his head. No "6 FT" label.
- **Ending:** the war punchline is a playful helmet-and-sandbags peek with a crane-out. No zombies, gore or severed head.
- **Hands:** no props are held in the whole film. The only hand action is the boy's open palm in the rain (S09), clear of his body. The helmet rides on the head bone (keyed every 2 frames).
- **Lens:** the low cameras (S04, S05, S13, S16) sit in empty air above the lawn with nothing within 1 m of the lens; S21's camera is in the empty trench, with the walls at the frame edges only.
