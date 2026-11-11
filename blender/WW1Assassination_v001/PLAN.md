# WW1Assassination: plan (checkpoint A)

Connect11 · branch `claude/connect11-ww1-assassination` · 1080×1920, 60 fps, frames 1–2130 (35.5 s) · Cycles CPU.
Our script (91 words) is in `../briefs/11_WW1Assassination.md`. There is no VO yet, so beats are built to the target times and listed in `beats.json` for `retime_to_vo.py`.

## Core idea: one world, one camera, a story clock
Everything happens on **one set**: Sarajevo's riverside quay, where it meets a narrow side street by a stone bridge and a café. The bomb happens further down the same quay.
- **Story time vs. film time.** The script opens on the ending (beats 1–2 are the moment just before the fatal shots), rewinds (beat 3), plays the morning (4–6), then returns to the corner (7–9).
  - All world animation (cars, couple, assassins, crowd, flags) is written as functions of a *story clock* `S(f)`.
  - Every frame is baked in film time: rewind = `S` running backwards, slow motion = `S` slowing. The camera runs only on film time.
  - Because it is all baked keyframes, `retime_to_vo.py` still warps everything consistently.
- **The map swap** (beat 10) happens inside a fully white cloud layer while the camera keeps rising: the city is hidden and the relief map is shown at the same place. The camera's move is unbroken. This is the only "trick", and it is the classic through-the-clouds wipe.

## Beat table (target start, frame = 1 + 60·t)
Each row lists one framing per ~1 s; the camera spline passes through each framing without stopping.

| # | t / frame | Line | On screen | Camera (one framing ≈ 1 s) |
|---|---|---|---|---|
| 1 | 0.0 / 1 | He fired at the car as it turned the corner | Sunny stone quay, river on one side, crowds 3 deep with hats, flags and bunting on the facades. The open 1910s touring car comes along the quay and turns into the side street by the bridge. | Low dolly alongside the front wheel (0 s) → rise to the rear-seat level, riding alongside (1 s) → drift ahead of the bonnet as it swings into the turn (2 s) |
| 2 | 3.0 / 181 | aiming at the Archduke and Duchess of Austria-Hungary | The car slows and stalls by the café. The Archduke (pale-blue uniform, plumed helmet) and the Duchess (white dress, wide white hat, parasol) turn their heads. A young man's hand and pistol rise in the out-of-focus foreground. | Orbit around the rear seat: the Archduke's face (3 s) → the Duchess's face (4 s) → swing behind the gunman's shoulder, with the pistol hand rising out of focus and the couple sharp (5–6.9 s) |
| 3 | 6.9 / 415 | But he wasn't the first assassin to try | Rewind: the gunman lowers the pistol backwards, the car reverses out of the corner and back down the quay at speed, the crowd walks backwards, and flags flap in reverse. The grade goes cool and desaturated, with a flicker. | Pull back fast and high (7 s) → long backward sweep down the quay over the crowd's heads (8–9 s) → drop to head height in a new stretch of crowd (10 s) |
| 4 | 10.1 / 607 | Earlier, two would-be assassins lost their nerve | Morning, story clock running forwards again. Two young men in the crowd. One slides a hand inside his coat and grips; the car approaches. They exchange looks, turn and push back into the crowd. | Push in on the pair, past shoulders (10 s) → close on the hand in the coat (11 s) → follow them turning away, the car crossing behind (12 s) |
| 5 | 12.4 / 745 | Then a third threw a bomb at the couple, but it bounced off | A third man steps to the kerb and throws a small dark object, which arcs in slow motion. It hits the folded roof at the back of the car and bounces off onto the cobbles. The Archduke raises an arm. | Whip-orbit from the thrower's arm (12.4 s) → track the object in its arc (13 s) → macro on the folded roof hit (14 s) → low on the cobbles as it bounces (15 s) |
| 6 | 15.5 / 931 | and exploded under the car behind them | It rolls under the second car, then a flash, a smoke burst and flying cobble and wood debris, with no bodies. The crowd scatters, two escort horses rear, and hats fly. | Ground-skim behind the rolling object (15.5 s) → flash, with a camera shake and pull back (16 s) → rise and orbit over the scattering crowd and rearing horses (17–18 s) |
| 7 | 18.5 / 1111 | Later, their driver turned onto the wrong street | Later: the first car speeds back along the quay, turns into the narrow side street, brakes, stalls and starts to reverse. The driver grips the wheel and looks back. | Chase low behind the car (18.5 s) → crane up and over (19.5 s) → overhead top-down as it turns the corner (20.5 s) → tilt down beside the driver as he stalls and reverses (21.5 s) |
| 8 | 22.4 / 1345 | right where another assassin was waiting | A young man under a striped café awning (tables, chairs, waiter in the background) looks up, steps forward off the kerb and reaches into his coat. | Swing to the café front (22.4 s) → push in on his face (23.3 s) → extreme close-up on his eyes (24.2 s) |
| 9 | 24.8 / 1489 | He fired twice, killing the Archduke and his wife | From behind the gunman: two muzzle flashes (light pops on the faces and car paint). The Duchess slumps against the Archduke and he slumps forward. No blood or wounds. The crowd surges in and an officer grabs the gunman's arm. | Over the gunman's shoulder, flash 1 (25 s) → flash 2 (26 s) → soft rack to the couple slumping (27 s) → camera starts to rise over the surging crowd (28 s) |
| 10 | 28.1 / 1687 | Their country declared war, dragging in its allies | Rise above the rooftops into a cloud layer. Above it lies a textured 3D relief map of 1914 Europe with no text. Austria-Hungary and Serbia light up, each with a small flag on a pole, then the glow runs like fire to Russia, Germany, France, Britain and the Ottoman Empire. | Crane up through the rooftops (28 s) → through the clouds in a whiteout (29 s) → tilt down onto the map, Sarajevo in centre (30 s) → push across to follow the fire front (31 s) |
| 11 | 32.0 / 1921 | and that's how World War One began | The whole continent glows, with tiny marching columns along roads, smoke plumes rising and flashes along the front lines. | Wide pull-back over the continent (32–33.5 s) → slow rotate, settling the framing (34–35.5 s) |

## Assets
| Asset | Source | Licence |
|---|---|---|
| Archduke, Duchess, driver, 4 assassins, waiter, officer, crowd (about 6 base bodies × instances) | MPFB2 + MakeHuman system assets | CC0 |
| Plumed helmet, wide hat, parasol, pistol (silhouette only), bomb (plain dark sphere), flat caps | Built in Blender (no construction detail) | ours |
| Open touring car ×2 | Sketchfab/Objaverse CC-BY (search in progress; fallback: ours, procedural 1910s phaeton) | CC-BY / ours |
| Escort horses ×2 | Sketchfab "Armored Horse" by naminoff (98c3f1c4), rigged with `rig_quadruped.py` | CC-BY |
| Street lamps | Sketchfab "Vintage lamp post" by dasmodal (56f6dcb3) | CC-BY |
| Café chairs and tables | Poly Haven gallinera_chair / gallinera_table | CC0 |
| Facades, cobbles, bridge stone, map relief | Poly Haven beige_wall_001, yellow_plaster_02, white_stucco, red_plaster_weathered, plaster_stone_wall_01, grey_plaster_02, castle_brick_07, cobblestone_floor_08, rock_wall_10, aerial_rocks_02 | CC0 |
| HDRI | Poly Haven german_town_street (2K) | CC0 |
| Map coastlines and borders | Natural Earth 1:50m admin-0 (public domain). Countries are grouped into **approximate 1914 states** (Austria-Hungary, German Empire, Russian Empire, Ottoman Empire, Serbia, and so on) | PD |

Buildings, bunting, flags, the river, the bridge, the café awning, clouds and FX are procedural, built by our scripts.

## Trickiest shots and how to do them
1. **Story clock / rewind (beat 3).** Animation is written as functions of story seconds and baked per film frame through `S(f)`. A rewind is the same motion played backwards, and walk cycles still plant their feet. The look is a keyed compositor grade (desaturate, cool, slight lens-distortion flicker).
2. **The bomb bounce (beat 5).** A ballistic arc solved in code: thrower's hand → release → contact on the folded roof → bounce → roll under car 2, in a slow-mo stretch of `S`. It is parented to the hand until release, and the hand visibly holds it.
3. **The explosion (beat 6).** An emission flash with a point light, a volumetric smoke puff, an expanding shock disc, and about 40 debris chunks on baked ballistic paths with ground bounces. Car 2 lifts and lurches but stays intact. No bodies. Horses rear through torso pitch with the hind hooves planted.
4. **Seated people in a moving car.** The couple and driver are parented to the car. Their poses are seated, with feet IK-planted on the car floor and the driver's hands IK on the wheel. Reactions, slumps and the parasol are keyed on top.
5. **Crowd.** A few MPFB bodies (subdiv 0, different clothes and skins) are linked-duplicated into about 60 people with per-person procedural cheer, wave, sway and turn-to-car cycles on the story clock, and a scatter run on the walker for beat 6. Only people near the camera get hand detail.
6. **Map (beats 10–11).** Natural Earth polygons are triangulated and extruded with a noise relief (mountain bands boosted by a rock texture), over a sea plane. Each state's "ignite time" drives a fire-front shader on a keyed clock. Flag poles pop up on Austria-Hungary and Serbia, with tiny marching columns (instanced capsules on paths) and smoke plumes.
7. **Camera.** One `CAM_Film` on a Catmull-Rom spline through about 36 framings, with an animated lens and DOF focus on an aim empty. Motion blur is on in the farm settings.

## Risks / flags
- 1914 borders are approximations built from modern country groupings; they're fine for a no-text stylised map, but not cartographically exact.
- The crowd's density versus CPU memory is a risk; I'll trim it if the scene gets heavy.
- If no decent CC-BY open touring car turns up, I'll model a simple procedural 1910s double phaeton (no badges).

## Schedule (UTC)
A plan 19:45 · B blocking (1 still/s) by 22:30 · C polish (0.2 s sheets + audit) by 00:15 · D package `blender/WW1Assassination_v002/` by 01:00.
