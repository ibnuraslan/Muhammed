# DonationBin_v001: PLAN (checkpoint A)

Connect09. Branch `claude/connect09-donation-bin`. 1080×1920 at 60 fps, frames 1–2490 (41.5 s). Cycles CPU. There's one camera, `CAM_Film`, on a continuous Catmull-Rom spline with a key framing about every 1 s, baked per frame. There are no cuts and no camera markers.

There's no VO yet, so beats are built to the brief's target times (frame = 1 + t·60). `beats.json` is written for `pipeline/retime_to_vo.py`.

## World layout (metres)
- **Bin:** `Bin` stands at the origin, footprint 1.5 (x) × 1.2 (y), height 2.15. Walls are 3 mm steel, painted dark green, with rust and grime but no logos.
  - The chute is on the front face (−y) at z 1.30–1.80, 0.85 wide, with a sloped hopper lip.
  - `Flap` is a steel door hinged on its top edge. It swings **inward** only; a stop bar on the outside stops it opening outward. A counterweight arm and a spring are visible in the cutaway.
  - Inside: a floor at z 0.05, a heap of bags and loose clothes up to about 0.75, and smooth walls. The slot light comes through the chute.
- **Lot:** asphalt with painted bay lines, puddles and leaves. A brick wall with a roller shutter stands behind (+y).
  - Props: a covered car, a street lamp, a chain-link fence, a utility box, a trash can, trash bags, a road barrier, weeds and shrubs.
  - Life: a rat runs along the wall, leaves and a paper bag drift in the wind, and a pigeon pecks. Lots of parked cars sit in the far background (HDRI `suburban_parking_area`).
- **More bins (for beat 11):** 3 more identical bins at 6–14 m along the wall, hidden by the camera framing until the final rise.

## Beat table (target times; the camera has a new framing about every 1 s)
| # | t (s) / frame | Line | On screen | Camera (continuous) |
|---|---|---|---|---|
| 1 | 0.0 / 1 | "She was reaching into a clothing donation bin" | A woman (in her 40s, jeans and a jacket) on tiptoe, one hand on the hopper lip, the other arm deep in the chute; her heels lift. Leaves drift past and the rat crosses the background. | Opens wide and low over the asphalt (18 mm), pushes in past the trash can (f60), then arcs over her shoulder to the chute (f120). |
| 2 | 2.5 / 151 | "when someone shoved her from behind" | A hooded figure (generic, face shadowed) steps in, hands planted on her back, and shoves. She pitches forward over the lip with arms flailing and her feet leaving the ground. | A whip-arc onto the hands at contact (f165), then the camera follows her head-first through the chute: **the dive** (f200–290). |
| 3 | 4.9 / 295 | "The heavy door slammed shut as she tumbled inside" | Inside: she tumbles down onto the clothes and the bags bounce and settle (squash). The flap swings back and slams; the light beam cuts to a thin slit and dust motes swirl. | Inside the bin, the camera rolls with her fall (f300–350), whips up to the flap at the slam (f370), then settles low over her (f440). |
| 4 | 8.4 / 505 | "These bins are built with one-way flaps that only swing inward" | **X-ray cutaway:** the bin shell turns to a cyan fresnel ghost (clean explainer, studio gradient). A ghost bag pushes the flap: it rotates inward, then swings back. Arrows are geometry, not text. She is visible as a ghosted figure on the pile. | The camera exits through the side wall (the steel goes x-ray as we pass, f505–540) into a side-profile orbit of the mechanism (f560–760). |
| 5 | 12.8 / 769 | "Once you drop through, the door locks behind you" | The flap tries to swing outward and **clacks** against the stop bar; a latch pawl drops. The macro shows the bar, hinge pin and pawl with vibration on impact. | A push to macro on the hinge (60 mm, f790–900), then a roll back out as the shell returns to steel (f900–955). |
| 6 | 16.0 / 961 | "There's no handle, no latch, just smooth metal walls too high to climb" | Back inside: her palms pat the smooth wall (planted contacts), she searches the flap's inner face (no handle), jumps with fingers stretching up, slides down, and lands on the pile. | Over the shoulder at her palms (f980), then a pan along the bare wall (f1100). **Crane up** the full wall height to the slit far above (f1180–1300). |
| 7 | 22.0 / 1321 | "She screamed for help, but nobody heard her" | Close on her face screaming (jaw open, neck tense, hands cupped to her mouth). Outside, the lot is empty: wind, a blowing bag, the rat, a distant passing car with no one stopping. | A push to a face close-up (f1330–1380), then a **pull back through the steel wall** (f1400) to wide over the empty lot (f1480). |
| 8 | 25.0 / 1501 | "For three days, she lay curled up on a pile of old clothes, with no food or water" | Time-lapse: the light through the slot cycles from day to dusk, night (blue), dawn and day, with shadows sweeping. She is curled on the clothes and shifts pose each phase, getting weaker (slumped shoulders). An empty bottle lies beside her. | The camera drops back in through the slot. A slow top-down spiral above her (f1520–1820) with a lens drift from 24 to 35 mm. |
| 9 | 30.7 / 1843 | "Finally, someone heard her cries" | Outside in daylight: a passer-by walking a dog (or with a shopping bag) stops, turns his head and leans an ear to the bin, then knocks. | Rises out of the bin through the chute (f1843–1880) and swings around to his face and ear by the steel (f1930). |
| 10 | 33.0 / 1981 | "and firefighters cut her free" | 2 firefighters in turnout gear and helmets. One runs a rotary cutter along the side panel: **sparks** spray (keyframed spark streaks) and the cut line glows. The second braces the panel with gloved hands and peels it open, and daylight floods into the bin. | An orbit around the sparks (f1990–2060), then a push through the opening as the panel folds (f2080). |
| 11 | 34.9 / 2095 | "But this wasn't the first time. She'd already been rescued from a donation bin twice before." | She's helped out wrapped in a grey blanket, a firefighter's hand on her arm; she steps down onto the asphalt. **More bins** line the wall nearby (the irony beat). Settle. | Pulls back out with her (f2095–2200), then a **crane up** and back to reveal the row of bins (f2260–2430) and settles on a slow drift (f2430–2490). |

## Assets and licences
- **Humans: MPFB2 + MakeHuman system assets (CC0).** The woman uses a female base with `young_caucasian_female` skin, hair `bob02` and `female_casualsuit02`. The shover is male with `male_casualsuit03`, darkened as a hood (only arms and torso read). The passer-by is male with `male_casualsuit01`. The 2 firefighters are male with `male_worksuit01` tinted tan or black turnout, plus procedural reflective bands and procedural helmets.
- **Poly Haven (CC0):**
  - HDRI `suburban_parking_area`.
  - Textures: `asphalt_02`, `brick_wall_02`, `green_metal_rust`, `painted_metal_shutter`, `concrete_floor_02`, `denim_fabric`, `terry_cloth`.
  - Models: `covered_car`, `street_lamp_01`, `trashbag`, `compost_bags`, `fire_hydrant`, `metal_trash_can`, `concrete_road_barrier`, `cardboard_box_01`, `street_rat`, `shrub_01`, `weed_plant_02`, `utility_box_01`, `modular_chainlink_fence`, `plastic_crate_01`.
- **Built procedurally (ours):** the bin and its mechanism, the clothing pile (randomised soft bag meshes with Poly Haven fabric), the rotary cutter, helmets, sparks, dust motes, x-ray shader and blanket.
- **CC-BY:** none planned. If I add one from Objaverse (a dog, perhaps), it goes in `CREDITS.md` with its CC-BY block.

## Trickiest shots and how I'll do them
1. **Dive through the chute (beat 2→3).** One camera follows the head through a 0.85 × 0.5 opening. The camera spline threads the chute centre with lens 20 mm and clip_start 0.02. Collision-checked in the audit: no frame has the camera inside the steel, except the planned wall pass-through in beats 4 and 7, which is 1–2 frames.
2. **Tumble and land.** I don't have physics, so I'll keyframe the root and spine on an arc with rotation. The limbs use FK flail curves and the hands are IK at landing. The landing contact is ray-cast against the pile mesh so she rests on the clothes, not inside them. Bags under her get a squash scale key.
3. **X-ray transition (beats 4–5).** The bin shell material mixes steel with a cyan fresnel and transparent ghost through one animated factor. The world blends from the HDRI to a cyan-white studio gradient over 20 frames while the camera passes through the wall, then reverses at beat 5's end. It reads as diving into an explainer and back out, with no cut.
4. **Jump and slide (beat 6).** The jump is root-driven with arms reaching up, and the hands are IK-planted on the wall at the top. The slide down keeps the hands on the wall plane (audited distance ≈ 0), and the feet land on the pile's ray-cast surface.
5. **Time-lapse (beat 8).** Keyframed sun and world strength, colour and exposure, plus a slot-beam spotlight sweeping. She has 4 curled poses, each blended over about 12 frames as she shifts, so she never holds still.
6. **Cutting (beat 10).** The cutter is in the firefighter's hands (both IK hands on the grips). There are about 150 recycled emissive spark streaks on ballistic arcs with a bounce off the asphalt, a glowing cut line that grows along the panel, and the panel "peels" by hinge rotation plus a Simple Deform bend.
7. **Contacts.** I'll write `audit.py` to check foot sole to ground or pile distance, hands on the lip, wall or cutter, camera-inside-mesh tests, and penetration of hands into the bin walls.

## Schedule
A by ~19:20, B (1 still/s blocking sheet + camera path) by 21:45, C (0.2 s sheets + audit) by 23:45, D (package `blender/DonationBin_v002/`) by 01:00.
