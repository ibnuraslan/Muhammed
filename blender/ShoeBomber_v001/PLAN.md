# ShoeBomber_v001: plan (checkpoint A)

1080×1920, 60 fps, frames 1–1620 (27.0 s), Cycles CPU. One camera `CAM_Film` on one Catmull-Rom spline (location, aim, lens), with a framing key about every 60 frames.
Frame = 1 + round(t × 60). With no VO yet, it's built to the beat-table times. `beats.json` gives each beat's start frame for `retime_to_vo.py`.

## World layout (one scene, four sets far apart)
| Set | Where | Built from |
|---|---|---|
| Cabin (night) | origin. The aisle runs along +Y; the bomber sits in a left window seat (row 3, seat A) | Procedural fuselage shell: curved walls, oval windows showing a night sky, overhead bins, reading lights, carpet. 6 rows of 3+3 seats (Sketchfab "Seat", recoloured). |
| Studio | x = +200 | A cyan-to-white gradient cyclorama with a softbox key and a rim light |
| Sky | x = −3000 | The airliner model (737 Max, white, no livery) at dusk with cloud cards and a volumetric cloud deck below |
| Airport | x = +400 | A security lane: belt, X-ray tunnel with curtains, walk-through detector, grey trays, queue barriers, travellers, terrazzo floor, glass wall |

The camera never cuts. It crosses between sets only inside a fly-through, where the frame is fully covered:
- **6→7:** push into the shoe's sole, into black, and out of the floating shoe in the studio.
- **7→8:** pull back through a white cloud wipe, and out of the cloud bank beside the plane.
- **8→9:** dive down through the cloud deck, then through the terminal skylight, and descend onto the belt.

## Beat table
| # | Frames | t | Line | On screen | Camera (one framing per ~1 s) |
|---|---|---|---|---|---|
| 1 | 1–198 | 0.0 | "In the middle of a flight, he tried to set his shoe on fire." | Night cabin, dim blue light and reading-light pools. Bomber (tall, generic, hoodie) at window seat 3A, hunched, right foot up on his left knee, sneaker in his left hand. His right hand strikes a match: it flares and wobbles, and he brings it to the shoe tongue. A passenger asleep beside him (head bobbing), another reading in front, an overhead bin light flickering, clouds and wing light blinking past the window. | f1 low through the seat gap, push-in (35 mm) → f60 rising over the seatback to a 3/4 on his face lit by the match → f120 orbit down to a macro of the match touching the shoe → f180 pull back up and right into the aisle |
| 2 | 199–372 | 3.3 | "But a flight attendant smelled burning matches…" | The flight attendant pushes the drink trolley down the aisle, stops, and sniffs: head turns and her nose wrinkles. A thin smoke wisp drifts from row 3 into the aisle. Passengers react: one looks up from a phone. | f199 aisle, low dolly behind the trolley → f260 crane up as she stops → f300 fast whip-pan (motion blur) to her face, close → f350 slow push on her eyes narrowing |
| 3 | 373–480 | 6.2 | "…and caught him in the act." | Her POV over seat 2's back: match flame at the sneaker, bomber freezes and looks up, caught. | f373 over her shoulder, pushing over the seatback → f430 tight two-shot (35→50 mm), his startled face and the flame |
| 4 | 481–654 | 8.0 | "Passengers and crew tackled him to the floor…" | She lunges and grabs his wrist. Two passengers stand, a male steward runs in, and together they haul him out into the aisle and pin him face-down (shoulders, legs). A tray table drops and a cup spills (prop physics keyed). Other passengers lean out, and a child peeks over a seat. Impact read: a dust puff off the carpet and a seat shake. No injuries. | f481 handheld wide from the aisle, front of the cabin → f540 crane up to near top-down over the pile → f600 drop low to carpet level for the pin (24 mm) |
| 5 | 655–768 | 10.9 | "…and he was finally sedated." | A crew member's gloved hand presses a syringe to his upper arm (hand grasps the syringe barrel, thumb on the plunger). His struggling arm and head slacken and go limp. | f655 low-angle push to the arm → f710 macro on the syringe → f750 slow orbit to his face, eyes closing |
| 6 | 769–1068 | 12.8 | "When they checked his shoes, they found a fuse sticking out of each one." | The attendant kneels, unlaces and pulls off one sneaker, then the other (the shoes leave his feet with her hands on them), and holds both up under a reading light. Macro: a short dark fuse cord pokes from the inner sole of each shoe. Passengers crowd behind. | f769 kneeling-level medium → f830 rise with the shoes → f890 orbit to the soles → f950 macro push on shoe 1's fuse → f1010 rack focus to shoe 2's fuse → f1050 push into the sole of shoe 1 (into black) |
| 7 | 1069–1248 | 17.8 | "Both shoes were packed with enough explosives…" | Cyan studio. Both sneakers float and rotate slowly. Each splits horizontally into a cutaway (upper lifts, sole slides apart) to reveal a smooth grey putty slab in the heel cavity, with a soft emissive outline highlight on the slab. Abstract only: a plain grey block, no wiring or real detail. | f1069 out of black, pulling back from shoe 1 → f1120 orbit as it splits → f1180 low 3/4 on both cutaways → f1230 pull back fast into the white cloud wipe |
| 8 | 1249–1392 | 20.8 | "…to bring down the entire plane." | Dusk sky above the clouds. The airliner (no livery) cruising with navigation lights blinking and cloud wisps streaming past. A dramatic pull-out from a cabin window (the window light of row 3) to the full aircraft: tiny against a huge cloudscape. No explosion. | f1249 emerge from the cloud next to the fuselage window → f1300 fast pull back along the wing → f1350 big pull-out to wide (lens 50→18 mm) → f1385 tilt down into the cloud deck |
| 9 | 1393–1620 | 23.2 | "And that's why you have to take your shoes off at the airport." | Daytime airport security lane. A generic traveller (a different man in a jacket) stands at the belt, pulls off his sneakers (hand on heel), and sets them in a grey tray. The tray rolls into the X-ray tunnel. Background: a queue, an officer at the scanner screen (no text), a walk-through detector, people walking. | f1393 descend through the skylight → f1460 crane down to belt level → f1520 dolly alongside the tray → f1580 settle on the traveller in socks, slow push-in to the end |

## Assets and licences
| Asset | Author | Licence | Source |
|---|---|---|---|
| Seat (airline seat) | maximmus | CC BY 4.0 | sketchfab.com/3d-models/8336f7cd7d1d438182d349e8e7bdb085 (via Objaverse) |
| 737 Max-8 (Free) | AMPG | CC BY 4.0 | sketchfab …/197ae72ceb5441efa91b8bdc2ee37050. Livery and text will be stripped and painted plain white/grey. |
| sneakers / Brown Sneakers | abazibiz / yanix | CC BY 4.0 | …/689c29ec…, …/e6c51d2e…. One is chosen after the logo check; any logo patch gets a plain recolour. |
| Syringe | stfuaahil / Stakler | CC BY 4.0 | …/324b3ed0…, …/79062c72… |
| Simple rubber conveyor | scailman | CC BY 4.0 | …/0819b51c… |
| Metal detector (entrance) | propmaker1 | CC BY 4.0 | …/e05f5f48… |
| HDRIs: Kloppenheim 02 Pure Sky (night), Qwantani Dusk 2 Pure Sky | Greg Zaal, Jarod Guest | CC0 | polyhaven.com |
| Textures: Dirty Carpet, Fabric Pattern 07, Large Grey Tiles, Denim Fabric, Rubber Tiles | Poly Haven authors | CC0 | polyhaven.com |
| Humans: bomber, flight attendant, steward, 3–4 passengers, airport traveller, officer | MakeHuman community | CC0 | MPFB2 + MakeHuman system assets |
| Procedural: cabin shell, bins, trolley, matches, fuse cord, putty slab, trays, X-ray tunnel, studio cyc, clouds | ours | — | built in scripts |

## Trickiest shots and how I'll do them
1. **The tackle (beat 4).** Five rigs in one aisle. I'll use the MPFB IK control rig (`make_human_ctrl`). The bomber's root is keyed along an arc from the seat to the aisle floor. The helpers' hands are IK-targeted to his wrist, shoulders and ankles, so the grasps are visible and their feet stay planted on the carpet (foot IK at ground z). Contact is checked numerically in the audit: hands within 3 cm of the target, feet at floor height.
2. **Match flame and smoke.** An emissive flame mesh with a flicker noise driver, keyed scale. Smoke is a set of animated, rising, alpha-textured cards. No simulation, so there's no cache for the farm.
3. **Shoe removal (6) and the tray (9).** The shoe is parented to the foot bone (Child Of constraint), then its influence is switched to the hand bone at the frame of the grasp. I'll key both constraints so nothing pops.
4. **Cutaway (7).** Duplicated sneaker with a Boolean bisect into an upper and a sole, plus a capped interior. The grey slab is a bevelled box with a putty noise texture. Plain and abstract.
5. **Set crossings.** Each one teleports inside a fully covered frame (black shoe interior, or a white cloud card stack in front of the lens), with velocity kept through the crossing so it reads as one move.
6. **Render cost.** The cabin is lit with a few area lights plus emissive reading lights, the volumes are limited to the cloud deck, and textures are capped at 2K.

## Schedule
A plan by about 19:25 → B blocking 1 s sheet by 21:45 → C polish 0.2 s + audit by 23:45 → D package `blender/ShoeBomber_v002/` by 01:00.
