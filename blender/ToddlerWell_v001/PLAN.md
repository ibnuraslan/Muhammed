# ToddlerWell: plan (checkpoint A)

Connect17, branch `claude/connect17-toddler-well`. 1080×1920 at 60 fps, frames 1–1950 (32.5 s). Cycles CPU only. One camera, no cuts.
The script is ours (98 words). With no VO yet, I build to the target times in the brief. `beats.json` holds each beat's start frame for `retime_to_vo.py`.

## World layout (metres, Z up)
- **Field:** a dusty farm field (Poly Haven `dry_ground_01` with sparse grass scatter). Tree line and shrubs at 25–60 m, plus a weathered pickup and the excavator.
- **The well:** a narrow pipe at the origin, Ø 0.56 m and **15 m (50 ft) deep**. It has a rusty steel casing ring 12 cm proud of the ground, and a wooden rescue tripod with a pulley over it from beat 2.
- **Underground, built for a clean cross-section** with no camera cut:
  - `EarthBack` is the soil block at y > 0. Its front face at y = 0 is a stratified soil cut face (`excavated_soil_wall`, with layer tint, roots and stones).
  - `EarthFront` is the soil at y < 0, plus the ground slab's y < 0 part. Both have a keyed `xsec` property that drives a transparency mask. The camera only flips it while it is passing *through* the ground surface, so it reads as "flying through the earth into the cross-section".
  - The pipe wall is one tube with inward normals. Its shader is opaque on front faces and transparent on back faces. From inside the shaft it is a full pipe. From outside, the near half disappears automatically, giving a half-pipe groove in the cut face.
- **Rescue pit:** a crater at x = +1.6 m, cut into the ground and both earth blocks with an animated Boolean. Its depth grows from 0 to 0.9 m over beats 3–4 ("only a few feet"), next to a growing spoil heap.
- **Sky:** a physical sky texture plus a sun lamp, both keyed so the sun crosses the sky in the beat 4 time-lapse. Shadows sweep and the light warms from noon to golden hour, then holds golden to the end.

## Cast (all generic MPFB2 / MakeHuman CC0)
| Name | Who | Look |
|---|---|---|
| `Toddler` | boy of about 2 (MPFB age ≈ 0.03) | t-shirt and shorts, bare arms |
| `Teen` | slim 16-year-old boy (age ≈ 0.30, low weight) | casual T-shirt and jeans; head torch (strap + lamp + spot light) parented Child Of to the head bone |
| `ResA`, `ResB`, `ResC` | rescuers, mixed ages and ethnicities | work suits tinted hi-vis orange/yellow with reflective bands, hard hats (CC-BY model) Child Of to the head |
| `Mother` | woman in her late 20s | casual clothes, behind the tape until beat 11 |
| Crowd | 4 more MPFB villagers, plus collection instances mirrored and rotated to make 10–12 | behind a red-white barrier tape on stakes, y ≈ +6…+9 |

## Beat table (frame = 1 + round(t × 60)); one new framing about every second, all on one spline
| # | t (s) / frame | Line | On screen | Camera (continuous) |
|---|---|---|---|---|
| 1 | 0.0 / 1 | The toddler fell 50 feet down a narrow well | Toddler toddles across the dusty field, with blowing dust, and the pipe opening ahead. He steps onto the casing rim, his foot slips, and he drops in, arms flailing. He falls 15 m, lands on the sandy bottom (squash, dust puff, sand trickle), then sits up crying with arms up. | 0.0 low ground-skim dolly behind him → 1.0 swing round to a front 3/4 on his face → 1.6 high over the opening as he slips → 2.0 tilt straight down and **dive into the pipe** → 2.0–3.2 fall with him (speed ramp, the walls whip past) → 3.4 brake above him → 3.8 slow push down onto his upturned crying face |
| 2 | 4.0 / 241 | Rescuers lowered ropes, trying to loop them around the little boy | **Whip up the shaft** and out the opening into a wide on the rescue scene: the tripod, three rescuers in hi-vis and hard hats feeding a looped rope hand over hand, and the crowd arriving. The loop descends, and in the shaft view it swings past his raised arms, misses, and he cries. | 4.0 rocket up the shaft → 4.8 burst out of the opening, crane up → 5.4 orbit to the rescuers' hands feeding rope → 6.2 tilt down the rope into the hole → 6.6–7.0 drop down the shaft along the loop → 7.2 the loop swings past his arms and misses |
| 3 | 7.7 / 463 | They even brought in heavy machinery to dig the pipe out | **Fly through the shaft wall into the cross-section** (soil strata, the tiny toddler at the bottom), and rise up the cut face through the surface into a wide. The excavator rolls in and digs beside the well: bucket bites, dirt flies, the spoil heap grows, the crowd is behind the tape, and exhaust puffs. | 7.7 pass through the pipe wall, pull back to the cross-section → 8.4 rise along the cut face → 9.2 break the surface, wide on the excavator rolling in → 10.0 low orbit to the bucket teeth biting soil (dirt spray) → 10.8 pull up over the cab |
| 4 | 11.2 / 673 | But after 11 hours, they had only dug a few feet down | Time-lapse: the sun arcs across the sky, shadows sweep round, clouds race and the light warms. The excavator works in fast motion, but the pit grows only to about 0.9 m. Workers slump, sit on the spoil heap, wipe their brows and pass water bottles. | 11.2 high crane wide, starting a slow 120° orbit → 12.2 over the pit → 13.2 **sink through the ground into the cross-section** to show the shallow pit against the 15 m shaft, with the toddler far below → 14.2 rise back up to the tired workers → 15.0 drift toward the crowd |
| 5 | 15.2 / 913 | Finally, a teenager passing by offered to go in himself | A slim teen pushes through the crowd, slips under the tape with his hand raised, and walks up to the rescuers. They turn, talk and gesture at the hole, and he nods and points at himself. | 15.2 a push between the crowd's shoulders → 16.0 track the teen ducking the tape → 16.8 dolly alongside his walk → 17.6 over-shoulder of the rescuer looking at the teen → 18.4 swing to the teen's face as he points at himself |
| 6 | 18.9 / 1135 | A rope was tied around his waist | A rescuer's hands loop the rope around his waist and pull the knot tight. The teen lifts his arms out of the way and the other rescuer checks the line on the tripod. | 18.9 drop to waist height → 19.6 close-up push on the knot hands → 20.4 macro on the knot being cinched → 21.0 tilt up his torso to his determined face |
| 7 | 21.6 / 1297 | and he was lowered in head first | Two rescuers hold his ankles. He goes upside down, arms forward, and they lower him into the pipe while the rope pays out over the pulley. | 21.6 orbit to the side as he flips → 22.2 follow his head down to the opening, descending beside him |
| 8 | 22.6 / 1357 | With a flashlight strapped to his forehead | Inside the pipe the head-torch beam swings across the walls: dust motes in the beam, roots poking out of the wall, sand trickling. | 22.6 inside the pipe below him, looking up at the torch on his forehead → 23.4 the beam swings and the camera turns with it across the roots → 24.2 sinking ahead of him, the light raking the walls |
| 9 | 25.0 / 1501 | he reached out his arms and grabbed the child | At the bottom of the shaft his hands reach and grip the toddler's upper arms, and the toddler grabs his wrists and clings. | 25.0 low at the bottom looking up at both → 25.6 macro on the hands closing on the toddler's arms → 26.4 slight orbit to the toddler's face clinging |
| 10 | 27.1 / 1627 | And when they pulled him back to the surface | **Fly out through the wall into the cross-section side view.** The rope tightens and the pair rise together up the half-pipe. Up top, the crew hauls hand over hand. | 27.1 back out through the pipe wall to the cross-section → 27.8 rise with the pair along the cut face → 28.6 break the surface onto the crew hauling hand over hand |
| 11 | 29.4 / 1765 | he brought the toddler up alive | Both emerge (feet, then the teen, then the toddler). The crowd cheers, arms up, and the teen lifts the toddler. The mother ducks the tape, rushes in and takes him in a hug, while rescuers clap and throw down their hats. | 29.4 low angle at the opening as they emerge → 30.2 orbit around the teen lifting the toddler → 31.0 the mother runs in → 31.8 **crane up and settle** high and wide on the cheering crowd in golden light |

## Assets and licences
| Asset | Source | Licence |
|---|---|---|
| Humans, clothes, hair, skins | MPFB2 + MakeHuman system assets | CC0 |
| Ground `dry_ground_01`, soil `excavated_soil_wall`, `rusty_metal_02` (casing), `sparse_grass` | Poly Haven | CC0 |
| `grass_medium_01`, `shrub_02`, `tree_small_02`, `island_tree_02`, `wooden_bucket_01` | Poly Haven | CC0 |
| "Excavator Animation" by tori1243 | Sketchfab via Objaverse | CC-BY 4.0 |
| "Hard Hat" by Kristiyan Marinov | Sketchfab via Objaverse | CC-BY 4.0 |
| "Sunny's pickup truck" by alban (background, badge-free; I'll check for logos) | Sketchfab via Objaverse | CC-BY 4.0 |
| Tripod, pulley, ropes, tape, stakes, head torch, pipe casing, roots, dust/sand particles | built procedurally in the scene | ours |

## Trickiest shots and how I'll do them
1. **Cross-section without a cut** (beats 3, 4 and 10). The camera passes through the ground surface or the pipe wall. The front earth and front slab switch to transparent only while the camera is exactly inside the surface. The back-face-transparent pipe gives the groove automatically. Characters in those beats sit at y ≥ 0.
2. **Head-first lowering in a 0.56 m pipe** (beats 7–9). The teen's root rotates 180° about X with his arms overhead on IK, and he is lowered on a keyed path. His ankles are held by IK hands of `ResA`/`ResB` until his feet pass the rim. A clearance check makes sure no shoulder or hand vertex is outside the pipe radius.
3. **The grasp and the rise** (beats 9–10). The teen's IK hands are keyed onto the toddler's upper arms. After the grip, the toddler's root is keyed relative to the teen's hands every 2 frames, so they stay locked. The toddler's hands grip the teen's wrists.
4. **Hand-over-hand rope** (beats 2 and 10). The rope is a curve whose points are keyed every 2 frames from the pulley, the load and the haulers' hands. The haulers' IK hands alternate gripping a point on that rope line, so a hand is always on it.
5. **Time-lapse** (beat 4). The sky sun, sun lamp, cloud texture offset, pit depth and excavator arm cycle all run fast. Characters key a slump/sit/wipe pose sequence. The camera orbit stays at normal speed, so it reads as a time-lapse and not a cut.
6. **Contact.** Feet use `Human.walk` with planted IK. Hats and the head torch are Child Of the head bone. I'll write an audit for foot/ground, hand/prop and head-item gaps, plus a BVH penetration count, and render close-up contact passes before each sheet.

## Schedule (UTC)
A about 19:50 · B (1 s blocking sheet) 23:00 · C (0.2 s sheets + audit) 00:30 · D (package in `blender/ToddlerWell_v002/`) 01:15.
