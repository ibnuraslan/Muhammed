# Tsunami2004_v001 — plan (checkpoint A)

Connect25 · branch `claude/connect25-tsunami-2004` · 1080×1920, 60 fps, frames 1–2400 (40.0 s) · Cycles CPU.
Sensitive subject: people are shown confused, then fleeing, then gone from frame before impact. No bodies, nobody hit. Quiet, respectful ending.

## World layout (one continuous set, metres)
- Coast runs along **X**. Ocean is **+Y**, land is **−Y**. Sea level z = 0.
- Beach: dry sand y −20…0, wet sand 0…25. Shallow seabed (coral, rocks, sand ripples) slopes from z −0.3 at y 25 to z −4.5 at y 420, then drops to −30 (deep).
- Beachfront: palms, umbrellas, longtail boats drawn up, a 3-storey hotel at (0, −35).
- Town behind: streets of 1–2 storey plaster/wood houses with tile and corrugated roofs, parked cars, a mosque at (−30, −150).
- Under the sea offshore at y ≈ 520 (z −15…−60): the earthquake **cross-section diorama** inside a cyan-to-white studio bowl, reached only by diving through the surface.

## Key systems
- **Drawback**: the sea plane drops from z 0 to −4.6 over 0–4.5 s. The gentle slope makes the waterline race ~400 m out; the camera skims just above the falling water.
- **Wave**: one geometry-nodes sheet 2 km wide; the profile (height H, steepness, overhanging lip, foam band) is driven by keyframed object properties. H goes 2 m (offshore swell) → 12 m → 30 m (100 ft) rearing over the palms → collapse. Animated noise, foam texture, spray sheets with soft volume on the crest.
- **Surge**: a flood sheet whose front advances inland with churn noise, foam and a debris carpet; level rises over the town, then falls to still puddles for the aftermath.
- **Destruction** (keyframed, no sims): boats/cars tumble on paths, palms snap (pivot at break point), hotel ground-floor glass blows in, houses tilt, slide and sink into the flood and are replaced by rubble piles. The mosque stays.
- **Light**: morning HDRI mixed into a golden-hour HDRI from 30 s; the sun swings low and warm; dust-light volume in the aftermath.

## Beat table (frame = 1 + t·60) and camera
One camera `CAM_Film`, keyframed framings joined by a Catmull-Rom spline (continuous velocity), lens animated. ~1 framing per second.

| # | t (s) | Line | On screen | Camera framings |
|---|---|---|---|---|
| 1 | 0.0 | The sea began pulling back fast | Morning beach: palms, longtail boats, umbrellas, ~8 people (tourists, locals, kids). Waterline races out, boats left on sand. | 0.0 low on wet sand behind kids, 1.0 skim forward over the retreating edge, 2.0 low dolly chasing the waterline seaward |
| 2 | 3.0 | exposing the ocean floor | Exposed seabed: flapping fish, coral heads, tipped rowboats, wet ripples. | 3.0 macro fish flapping, 4.0 orbit over coral + tipped boat |
| 3 | 5.3 | People on the beach were confused | People walk out on the wet sand, point, a man bends to pick up a fish, two kids run. | 5.3 crane up to medium group, 6.3 orbit past pointing woman |
| 4 | 7.2 | noticed a wave coming toward the shore | White line on the horizon grows; heads turn; one man shouts and waves his arm. | 7.2 over-shoulder to horizon, 8.2 rack/push on white line, 9.2 whip back to shouting man close-up, 10.0 pull back |
| 5 | 10.8 | a massive tsunami | High above the coast: the wave front stretches across the ocean. | 10.8 fast crane up, 11.8 high wide, 12.6 tilt down and start dive |
| 6 | 13.1 | triggered by an undersea earthquake | Dive through the surface into the cyan studio cross-section: plates slip, seabed thrusts up, water column bulges. | 13.1 through surface, 13.8 wide cross-section, 14.8 push on the slip |
| 7 | 15.6 | As the wave got closer, it grew taller | Up out of the water facing the wave as it rears in shallow water: dark wall, spray. | 15.6 surface breach, 16.6 low on water racing backward, 17.5 tilt up the face |
| 8 | 18.3 | up to 100 feet in some places | Low angle from the beach: wall towers over palms and the 3-storey hotel. People flee past camera inland. | 18.3 ground-level low angle, 19.3 dolly back with runners, 20.3 crane to hotel + wall |
| 9 | 21.5 | slammed into the coast with unimaginable force | Impact: water bursts through the hotel ground floor, boats and cars tumble, palms snap. (People already gone.) | 21.5 side-on wide, 22.5 shake push-in on hotel, 23.5 orbit to boats/cars, 24.6 snap palm |
| 10 | 25.7 | destroying everything in its path | Camera rides the surge inland down a street of debris. | 25.7 on surge front, 26.8 between houses |
| 11 | 28.0 | swept entire neighbourhoods away | Aerial pull-up: water churns through the town, houses dissolve. | 28.0 rise, 29.0 high orbit, 30.4 top-down |
| 12 | 31.4 | leaving nothing behind but rubble | Aftermath: still water, rubble fields, lone mosque standing, dust in shafts of light. | 31.4 descend toward mosque, 32.6 slow glide over rubble |
| 13 | 33.8 | more than 167,000 people lost their lives | Slow crane up over the devastated coast at golden hour; settle into stillness (slow drift continues, never frozen). | 33.8, 35.5, 37.5, 39.5 slow rising crane, decelerating |

## Assets (licences)
- Poly Haven CC0: HDRIs `qwantani_mid_morning_puresky`, `qwantani_sunset_puresky` (2K); textures damp_beach_sand, coast_sand_01, aerial_beach_01, white_plaster_rough_01, yellow_plaster, clay_roof_tiles, corrugated_iron, worn_asphalt, rubble, concrete_debris, coral_mud_01, rough_plaster_broken, mud_cracked_dry_03, brown_mud, red_laterite_soil_stones (1K).
- Sketchfab CC-BY via Objaverse (full list in `assets/models/credits.json`, will be in CREDITS.md): Palm Tree (Surya), Plant Series – Palm Tree (UPWARD), Longtail boat (jorandp), Fishing boat (Pabooklas), Beach Umbrella (yacin_cheffai), Parasol lowpoly (Harold.Llanos), Small price car (Oliv1e), Low-Poly Sedan (scailman), Fishes (VivernaNeva), Coral Piece (Sharon Kunne), Wooden House Building (Rescue3D Assets), Wooden house (Johan Pindeville), Roof Rubble Pile scan and Debris wood planks scan (Pers Scans), Red Brick Pile (3DWALKABOUT), Mosque Cami (askardes).
- MPFB2 / MakeHuman CC0 humans (generic, no likeness). Hotel, houses' variants, terrain, water, diorama: built procedurally here.
- Any logo/text found on a downloaded model gets its texture replaced.

## Trickiest shots and approach
1. **Wave wall (7–9)**: a single procedural GN sheet with overhang lip, foam and spray; scale is sold by palms + hotel in frame. Fallback if overhang reads badly: steep wall with spray curtain.
2. **Dive into cross-section (6)**: honest fly-through: camera passes through the surface into a bowl under the sea; the bowl is the cyan studio. Out again the same way for beat 7.
3. **Impact (9)**: keyframed rigid motion on boats/cars/palms + water bursting through the hotel openings (flood sheet + spray planes). No sim caches, so the farm needs nothing baked.
4. **Houses dissolve (11)**: each house is split into wall/roof pieces that tilt, separate and sink into the churn; rubble piles rise in their place.
5. **People (1–4, 8)**: MPFB humans on the IK walk/run from `anim_lib.py`; pointing, shouting, a fish pick-up with visible grasp. All exit frame inland before impact and are hidden.
