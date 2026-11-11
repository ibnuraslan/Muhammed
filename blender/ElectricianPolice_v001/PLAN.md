# ElectricianPolice: plan (checkpoint A)

1080×1920, 60 fps, frames 1–1560 (26.0 s), Cycles CPU. One camera `CAM_Film` on one Catmull-Rom spline (continuous velocity, no cuts, no camera markers). Our 73-word script; beats timed to the brief's target times until the VO arrives, then `retime_to_vo.py`.

## World layout (one scene, all sets connected in space so the camera can fly between them)
- **Town road** along +Y (x = 0, y = −10…90): asphalt, dust, two rows of 2–3 storey plaster/brick shop-houses with roller shutters, market stalls with fruit, crates, street lamps, utility poles with sagging wires, auto-rickshaws (procedural), parked bikes, pedestrians.
- **Substation** in an open lot on the east side (x = 10…34, y = 12…40) behind a chain-link fence: transformers, pylons, lines running out over the town.
- **Utility office**: a single-storey block at the back of the substation (x ≈ 30, y ≈ 44) with a window the camera flies through. Desk, laptop, office chair, notepads, the switchgear cabinet on the side wall.
- **Police station**: a two-storey building on the west side further up the road (x ≈ −14, y ≈ 70) with 8 lit windows, front porch, sign board with no text. Interior room behind the first-floor windows.

## Beats and camera (frame = 1 + 60·t)
| # | t / frame | Line | On screen | Camera (one framing ≈ 1 s) |
|---|---|---|---|---|
| 1 | 0.0 / 1 | "He was riding his motorcycle without a helmet," | Man in red shirt, bare-headed, on a small commuter bike weaving past a rickshaw; dust kicks up, stall awnings flap, pedestrians cross. | Low ground-skimming chase alongside the front wheel (0–1 s) → rises to a 3/4 front on his bare head and hair (1–2 s) → swings ahead as he passes stalls (2–2.8 s). |
| 2 | 2.8 / 169 | "and the police gave him a fine." | Traffic officer in khaki steps out, whistles, waves him over; he brakes, foot down; officer writes on a pad, tears the slip and hands it over; man snatches it, annoyed head shake. | Swing round to the officer's wave (2.8–3.7) → over-the-shoulder push on the pad and the hand-over (3.7–4.7). |
| 3 | 4.7 / 283 | "But he was an electrician" | He grabs a yellow hard hat off the bike's rear rack and pulls it on; **whip-pan** right (motion blur) lands on him at the substation gate in hard hat and hi-vis vest, transformers humming (heat shimmer, blinking indicator). | Close on the hat going on (4.7–5.3) → whip-pan 90° (5.3–5.6) → slow push past the fence wire to his face (5.6–6.6). |
| 4 | 6.6 / 397 | "with access to the power grid." | He unlocks the gate and walks in; insulators, pylons, lines carrying a glowing pulse out over the rooftops. | Crane up the pylon lattice (6.6–7.5) → tilt over the town with the lines spreading to the horizon (7.5–8.4). |
| 5 | 8.4 / 505 | "So he checked the records" | Utility office: he sits at a laptop, types, scrolls. Screen = rows of building icons + bars, no text. Fan, papers, tea glass. | Dive down from the sky and fly **through the office window** (8.4–9.3) → over his shoulder onto the screen (9.3–10.3). |
| 6 | 10.3 / 619 | "and found that the police station hadn't paid its electricity bill in three years." | One row turns red: police-badge icon, three calendar pages flip; he leans in, slow grin. | Push into the screen (10.3–11.3) → orbit to his face lit red (11.3–12.5) → macro on the flipping calendars (12.5–13.7) → rack back to his grin (13.7–14.9). |
| 7 | 14.9 / 895 | "And that bill was huge," | The red bar grows huge, bursts past the bezel into the room; he sits back, arms out, delighted. | Pull back fast as the bar extends (14.9–15.9) → follow the bar's tip across the room (15.9–16.8) to the switchgear cabinet (16.8–17.6). |
| 8 | 17.6 / 1057 | "so he cut off their power." | Gloved hand grips the big lever and throws it: clunk, spark burst, panel lights go out. | Macro on the gloved grip (17.6–18.4) → pull back out of the window, sparks still falling (18.4–19.4). |
| 9 | 19.4 / 1165 | "For five hours, the police station sat in the dark," | Fly over rooftops at golden hour; police station windows go dark one by one, ceiling fan visible slowing. | Rise and race over the roofs (19.4–20.0) → arrive at the station, windows popping off (20.0–20.5). |
| 10 | 20.5 / 1231 | (cont.) | Inside: three officers in the dark, one fanning with papers, one holding a phone torch, one slumped with feet up; ceiling fan stopped; wall clock hands spin five hours; sweat sheen. | **Fly through a dark window** (20.5–21.3) → slow orbit between the officers, the torch beam crossing camera (21.3–22.2) → push into the spinning clock (22.2–23.0). |
| 11 | 23.0 / 1381 | "all because they fined the wrong guy." | Out through the front door to the street at dusk: he strolls past the dark station, hands in pockets, turns his head to camera and smirks. Neighbouring buildings still lit. | Back out through the doorway (23.0–23.8) → dolly alongside him (23.8–25.0) → settle on his face (25.0–26.0). |

## Characters (MPFB2, MakeHuman CC0)
- **Man_Road**: red shirt, jeans, bare head (short hair), rides the bike, gets ticketed, pulls on the hard hat.
- **Man_Work**: same phenotype and skin, plus hi-vis vest (a displaced copy of the shirt mesh with retro-reflective stripes), hard hat and work gloves. Used for substation → office → cabinet → final stroll (repositioned only while off-camera).
- **Officer_A** (traffic, khaki uniform + cap), later one of the three inside; **Officer_B**, **Officer_C** inside the station.
- 2 background pedestrians on the road.

## Assets
| Asset | Source | Licence |
|---|---|---|
| Motorcycle (Silas6), Substation Transformer (HalfCarrot), Old Soviet Transformer Low-Poly as switchgear (MrUnity), 400kV Power Pylon (h1pp0p0t4mu5), market stall (Kisielev Mikhail), Smartphone (Rafael Benites de Souza), Office chair (AK STUDIO) | Sketchfab via Objaverse | CC-BY 4.0 (credit block in CREDITS.md) |
| classic_laptop, metal_office_desk, wall_clock, modular_electricity_poles, modular_chainlink_fence, power/utility boxes, monobloc chair, street lamp, notepads, clipboard, roller-shutter door/windows, crates, boxes, ceiling fan, aircon unit, bananas, basket, drawer cabinet, plant, trash can, limes; textures asphalt_02, concrete_wall_008, painted_plaster_wall, gravel_concrete_03, brick_wall_10, dry_ground_01, corrugated_iron_02, wood_floor_deck; HDRIs kloppenheim_06_puresky (day), venice_sunset (dusk) | Poly Haven | CC0 |
| Humans, clothes, hair | MPFB2 / MakeHuman system assets | CC0 |
| Auto-rickshaws, hard hat, vest, buildings, screen UI, sparks, police badge icon | built procedurally in our scripts | ours |

## Trickiest shots
1. **Riding**: IK hands locked to the handlebar grips, feet on pegs, root parented to the bike's path; foot goes down onto the asphalt (ray-cast) at the stop. Hair "blow" = jiggle on head/neck + shirt flutter via a small wave modifier on the shirt.
2. **Costume change (beat 3)**: hat grasp on the road is real (hand IK to the hat, hat child-of the hand, then the head); the vest appears across the whip-pan, which is a single fast camera yaw on the same spline (no cut).
3. **Laptop screen**: not a texture; small emissive 3D planes (icons, bars, badge, calendar pages) sitting just in front of the screen, so they can animate and the red bar can physically burst out of the bezel and lead the camera to the cabinet.
4. **Lever throw**: lever pivots on a hinge empty; glove IK keyed to the handle at every frame of the throw; spark burst = particle-free animated emissive streak mesh instances (no sim caches for the farm).
5. **Day → dusk → dark** across 18.4–23 s: sun strength/angle, world HDRI mix and exposure keyed; window emission keyed off in sequence.
6. **Interior in the dark**: phone torch = spot light parented to the phone in the officer's hand; moonlight-blue fill through windows; clock hands driven by keyframes (5 full hour-hand-equivalents).
7. **Through-window flights**: windows built as openings with no glass in the camera's path; audit checks the camera never sits inside a mesh.

## Review
- B: 1-per-second sheet (270×480, 8 samples) + camera path plot.
- C: 0.2 s sheets + audit script (feet/ground distance, hands to grips/lever/phone/papers, chair seat contact, camera-in-geometry ray test).
