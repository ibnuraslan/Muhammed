# DwarfGiant — PLAN (checkpoint A)

1080×1920 @ 60 fps, frame_end 2340 (39.0 s). One camera (`CAM_Film`) on one catmull spline, a new framing about every 50–60 frames, never a cut. Sets swap only while a macro surface (skin, wall plaster, sheet, window glass) fills the frame for ≤6 frames; the camera position and velocity stay continuous through those swaps.

## Beat table
| # | frame (t) | line | on screen | camera |
|---|---|---|---|---|
| 1 | 1 (0.0) | far too short to join the army | 1917 recruitment office (plaster walls, wooden desk, height rod with brass slider, window, door frame). Short young man in shirt + braces at the rod; two officers in olive tunics + peaked caps shake heads, one lowers the slider onto his head, a clerk writes; recruits queue and shuffle in the doorway; dust in window light. | starts high over the officers' shoulders → cranes down to his eye level (0.0–1.5) → slow arc around him (1.5–3.0), pushing toward his temple |
| 2 | 180 (3.0) | a tumor was quietly growing in his brain | push into his temple: skin macro ≤6 f → realistic brain (CC-BY model, wet SSS) floating in deep teal→navy studio gradient; pituitary under the brain glows warm and swells (tumour mass grows, pulsing) | macro dive → orbit under the brain to the pituitary (two framings) |
| 3 | 372 (6.2) | flooded his body with growth hormone | pull back out of the brain: he is now an x-ray body (glass/fresnel skin over skeleton); glowing gold particles stream from the pituitary down the neck, arms and legs vessels | fast pull-back + tilt down the body following the stream |
| 4 | 468 (7.8) | the four-foot-six man started to grow | x-ray fades back to skin in the office; time-lapse: he rises past the door-frame lintel marks; shirt pulls tight, sleeves ride up on the forearms, trouser hems lift over the ankles; light sweeps (time-lapse sun) | pull out to medium-wide with door frame on the side; slow rise matching his head |
| 5 | 696 (11.6) | hands, feet and even his tongue got bigger | macro: his hand flat on the desk spreading wider (knuckles thicken); shoe leather splits at the seam as his foot grows; mirror on the wall shows his jaw thickening and tongue pushing out | drop to hand on desk → slide down to shoes → rise to mirror (3 framings) |
| 6 | 882 (14.7) | shot up more than two feet in just a few years | he now towers over both officers (they look up, step back); window behind: tree goes green → autumn → snow → green | wide low orbit around the group (≈120°), lens 24 |
| 7 | 1074 (17.9) | his spine began to curve | his body goes x-ray again; real spine model curves sideways (scoliosis, curve deform) as he stoops forward | push-in to back, spine fills frame, slight orbit |
| 8 | 1248 (20.8) | His vision blurred… struggled to hear | camera into his eye line: officers talking go out of focus (DOF + double image); then camera swings around to his ear macro, he cups a hand to it; officers' mouths move, dust motes trembling | POV push → whip around his head to ear macro |
| 9 | 1476 (24.6) | Doctors finally removed the tumor | through the plaster wall into a 1930s operating theatre: tiled walls, big round lamp, three surgeons in gowns/caps/masks around him on the table, nurse with tray; dive into the brain studio again: forceps lift the tumour from the pituitary (clean, no blood) | through-wall fly → overhead lamp framing → dive to brain macro |
| 10 | 1710 (28.5) | slowed his growth, but didn't stop it | he lies in a long iron bed, feet sticking out past the foot rail, blanket too short; nurse adjusts a stool under his feet; curtains move | low slide along him from feet to head |
| 11 | 1860 (31.0) | By the time he died… seven foot eight | older tall man stands beside a normal-height man and a door (head at lintel); soft window light; then camera rises, through the window into a dusk cemetery: grave with plain stone (no text), wind in grass, crows | side dolly → crane up and out through window → pull-up over grave |
| 12 | 2040 (34.0) | both a dwarf and a giant | dusk field by the cemetery: two silhouettes side by side, the short young man and the tall older man, backlit by the setting sun; grass and coat moving | camera rises slowly, settles at ~38.5 s |

Beat starts (beats.json): 1, 180, 372, 468, 696, 882, 1074, 1248, 1476, 1710, 1860, 2040.

## Assets (all CC0/CC-BY, credits in CREDITS.md)
- Humans: MPFB2 / MakeHuman CC0 (hero man ×2 ages, 2 officers, clerk, 2–3 recruits, 3 surgeons, nurse, normal-height man). Officer uniform = male_worksuit tinted olive wool + MPFB fedora reshaped/peaked cap model; no insignia text.
- Brain: Sketchfab CC-BY "Human brain, Cerebrum & Brainstem" (FrankJohansson) or "Human Brain" (Versal) — will pick from thumbnails.
- Spine: "Human Spine" (EdwinCaBe, CC-BY) / "The Human Spine" (Cesar Gonzalez).
- Skeleton for x-ray: "X-Ray Skeleton" (B3D Interactive, CC-BY) if it is a real skeleton mesh.
- Door: "Door with frame" (witnessk). Height gauge: "Vertical Height Gauge" (vramstudio). Tables/chairs: Wooden Table/Chair (J0Y). Hospital/iron bed: "Old and worn out hospital bed" or loxfear. Mirror: "Mirror for bedroom". Gravestones: "Gravestones" (Mateus Schwaab) — realistic ones only.
- Poly Haven CC0: plaster/brick walls, wood floor, tiles, forest ground/grass, HDRIs (interior + dusk sky) at 1K–2K.

## Trickiest shots and approach
1. **Growth time-lapse (4–6):** one MPFB rig; armature scale animated 1.0 → ~1.7 (1.37 m → 2.35 m) with extra hand/foot/jaw bone scale. Clothes tight: shirt/trouser proxies get a shrink-free scale lag (sleeve/hem bones scaled less) so wrists and ankles show. Feet replanted on the floor every key (root z re-solved from foot ground contact).
2. **Continuous camera across 4 sets:** sets live at separate positions, each set's parent empty is moved (stepped) so the entry point sits where the camera is when a macro surface fills the frame (temple skin, wall plaster, window glass). Camera spline itself has no jump.
3. **X-ray body:** duplicate of the hero body mesh with a fresnel glass/emission shader + skeleton/spine models parented to the bones; mix factor keyed for the fade in/out.
4. **Brain interior:** real CC-BY brain with wet SSS pink-grey tissue, sulci from the model; pituitary + tumour sculpted from displaced icosphere with noise displacement and SSS + emission pulse; deep teal→navy gradient backdrop.
5. **Faces:** MPFB face bones (brows, lids, jaw, lips) keyed per beat: worried/hopeful in 1, strain in 4–5, awe on officers in 6, pain in 7, squint in 8, calm in 11–12.
6. **Clipping:** hands on desk/ear/rod and feet on floor/bed rail checked by a BVH audit plus 270×480 contact close-ups.

## Risks / questions
- Budget is tight (4 CPUs, ~4 h): I will build office + brain studio + x-ray first (beats 1–8, 60 % of the film), then theatre, bed and dusk.
- Package delivered as normal git file < 95 MB, no LFS (batch 2 rule overrides the brief's LFS line).
