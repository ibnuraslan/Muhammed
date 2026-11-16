# B27 ChicagoRaised: shot plan (Phase 1, before the VO)

Film: 1080×1920, 60 fps, Cycles, hard cuts. One camera object, keyed per frame: a jump at every cut, a smooth move inside a shot.
Client direction (Nov 15): **match the reference sheet** (`briefs/batch2/B27_ChicagoRaised_reference_1fps.jpg`, 37 s) for shot order,
subjects, framing ideas and pacing. The "Ref s" column is reference seconds; Phase 2 moves every cut to the client's VO words.
Each action is keyed at 1× from its shot start and runs about 30% past the planned length, so the VO can trim it without stretching.

**Cast** (generic MPFB characters, re-dressed): **W1–W6** jack workers (work coveralls in blue, brown, grey-green and rust, bare-headed so faces read),
**Foreman** (dark brown suit), **Lady** (the resident inside, long dress), **Mason** (worker in tan overalls), **Townsfolk** for the flood street (two men, one woman, clothed in solid non-skin colours),
**Horse** (rigged horse from our WW1 package, dark bay, same model in every flood shot).

**Sets** (one scene, each at its own origin):
- **A, the square, 1850s:** the hero building (5-storey cream stone corner block, arched windows, CC-BY) on a cobbled square. A row of red cast-iron jackscrews sits under its ground beam, each with a side crank. Wooden cribbing stacks, timber piles and a new brick foundation get built under it.
- **B, the parlour:** a room inside the building, with a red armchair (Poly Haven), a bookshelf with books, a window and a rug.
- **C, the swamp:** wide wetland, reeds, pools, a muddy shore and low trees, under a blue sky.
- **D, the 1850s town:** a grid of low brick and wooden buildings on mud, with puddles and chimney smoke (aerial).
- **E, the flood street:** a street between brick fronts and Victorian houses under 30 cm of muddy brown water, with townsfolk and a horse.
- **F, modern Chicago:** a glass-tower skyline behind the old raised blocks, with a river and a bridge (aerial). No logos or text.

| # | Ref s | Beat (VO idea) | Shot: who / what physically happens | Camera | Risk → simplest safe staging |
|---|---|---|---|---|---|
| S1 | 0–1 | "The jackscrews" | W1 turns his jack's crank with both hands, leaning into it, mouth set with effort. | Low 3/4 front medium (waist up), slow push. | Both hands on the single crank grip (wrap_grip, palms 1 cm off the grip axis), the grip moves on a 0.16 m circle at hip height, elbows 85–110°. No arm crosses the jack body. |
| S2 | 1–3 | "were hand-cranked beneath" | Wide on the hero building on the cobbled square. Six workers along its front at their jacks all turn their cranks. **Logo 1: DA KRAS FILMS (dark) on the cream shop-sign board over the ground-floor door.** | Wide from across the square at about 2 m height, slow push-in. | Workers small in frame, same crank cycle. Sign flat to camera, ≥15% frame width, ≥1 s. |
| S3 | 3–4 | "the buildings" | The Foreman raises his right arm, open palm, and calls the turn. His other arm hangs relaxed. | Medium 3/4 front, chest-up, slight push. | No megaphone (no hand at the mouth). The raised hand is in the `point` preset, palm forward, below head height plus 25 cm, elbow bent. |
| S4 | 4–5.5 | "was turned" | The row of workers along the building's base turn their cranks in unison. | Low dolly along the row from the end, building beam above. | Same crank rig as S1. Workers spaced 1.6 m apart so no arm reaches a neighbour. |
| S5 | 5.5–7 | "at exactly the same time" | Reverse angle: two workers at the front, the row behind; the ground beam visibly lifts 2 cm on the jacks. | Low front 3/4, slow push. | Same. |
| S6 | 7–9 | "the building, with people still inside" | Parlour: the Lady sits in the red armchair with a closed book resting on her lap, her hands resting on it. She looks up and turns her head toward the window; outside, the street view slides down as the room rises. | Medium from the room's open side, slow push. | The book rests on her thighs (no grip). Palms lie flat on its pages (place_hand, 1 cm). |
| S7 | 9–10 | "still inside" | Under the building's edge: two workers crank side by side. | Low, between jacks, in empty space ≥1 m from any jack. | Same crank rig. |
| S8 | 10–12 | "Wooden supports were stacked" | W2 pushes a timber broadside onto a crisscross cribbing stack under the raised needles (palms flat on top of the timber), stepping with it. Other stacks already stand. The windlass cranks are off the jacks from here on. | Side 3/4 from the building side (face readable), slow push. | Palms on top of the timber, never wrapped. The timber slides only while he pushes; his feet step (walk cycle), no sliding. |
| S9 | 12–13 | "beneath" | Wide: the whole building now stands on cribbing stacks about 1.5 m above the old ground. | Low wide, slow push. | No characters near the stacks. |
| S10 | 13–15 | "until it reached higher street level" | The building rises the last 30 cm on the cribbing to the new street line; the camera cranes up from the old ground to the beam. | Crane-up from cobbles to beam level. | Nothing crosses the lens; camera stays ≥1.5 m off the stacks. |
| S11 | 15–17 | "And brand-new foundations" | The Mason stands behind the new brick foundation wall (under the raised building), leans over and presses a brick into place with both palms flat on top. A new course appears each cycle. | Front 3/4 from the street, his face over the wall. | Palms flat on the brick top; the brick moves only under his hands. Courses appear one by one (keyed visibility, hide_render + hide_viewport). |
| S12 | 17–18 | "were constructed" | Wider: the brick foundation is complete across the front, under the jacks' needles. | Medium-wide, slow pull-back. | Camera only (the Mason is behind the finished wall). |
| S13 | 18–20 | "as the building remained (open)" | Hero building facade, low angle, as it sits on its new brick foundation. | Tilt up the facade. | Camera only. |
| S14 | 20–21 | "You see," | Same facade, the camera rises over the cornice to the sky and the city beyond. | Crane over the roof. | Camera stays in empty space ≥2 m off the roof. |
| S15 | 21–22.5 | "Chicago was originally built" | Aerial swamp: reed beds, pools and mud flats under a blue sky. | Slow aerial push. | Reed clumps scattered by Geometry Nodes; water is dark teal, no green glow. |
| S16 | 22.5–25 | "on a swamp" | Aerial: the low 1850s town of brick blocks and timber houses on the mud, with puddles and mud streets, the lake beyond. | Aerial descent. | Camera only. |
| S17 | 25–26 | "the streets were constantly (flooded)" | Street level: the muddy flooded street, townsfolk wading. | Eye-level wide down the street. | Water is opaque muddy brown, specular ≤0.05 (no sky sheet). |
| S18 | 26–28 | "and this caused" | The horse stands in the water and lifts its head; a man wades past behind it. | Low 3/4 on the horse. | Horse legs go into the water (no floating). The man walks with swinging arms. |
| S19 | 28–30 | "disease to spread" | A man in the street doubles over coughing: one hand 6 cm in front of his mouth, the other on his knee. A woman behind him looks on. | Medium 3/4 front, slow push. | Hand never touches the mouth. No distress close-up. |
| S20 | 30–31 | "around the city" | The horse turns its head; a woman walks away down the flooded street. | Wide, slow lateral move. | Same horse model and colour as S18. |
| S21 | 31–34 | "so they raised (the city) away from the swamp" | The flooded street level beside the red brick block: the building stands raised on its new brick foundation, high above the water, with a raised street filled in front. | Rise from the water line up the new foundation to the raised walk. | Camera-only, no characters near the lens. |
| S22 | 34–37 | "And Chicago still sits on those foundations to this day" | Modern skyline: glass towers behind the old cream and red blocks, a river and a bridge; morning light. | Aerial push and orbit. | No logos or text on any tower. |

## Logo
One placement: **DA KRAS FILMS** (dark version) on the cream shop-sign board above the hero building's ground-floor door. It shows in S2 (≥1 s, flat to camera, ≥15% frame width, f/8+) and again in S9 and S13 if they frame it. It never appears in the disease beats.

## Crank rig (the main contact risk)
Each jackscrew is a red cast-iron body with a vertical screw and a side gearbox carrying a crank arm, 0.16 m radius, with a horizontal wooden grip at hip height.
The crank arm and grip turn by keyed rotation. The worker's two hands sit side by side on the grip (wrap_grip), their positions re-solved every 2 frames from the grip's world position. Elbows stay at 85–110°, and the torso leans a few degrees with the push. `body_prop_cross` runs on every jack, grip, crank arm, the cribbing, the timber, the brick and the book.
