# MountainTunnel (B30): plan (Phase 1, checkpoint P1)

ConnectB30. Branch `claude/connectB30-mountain-tunnel`. 1080×1920, 60 fps, Cycles CPU. Hard cuts, shots of 1–2.5 s.
Client direction (Nov 15): **match the reference still sheet** (`briefs/batch2/B30_MountainTunnel_reference_1fps.jpg`, 49 s):
same shot order, subjects and framing ideas. Every shot is rebuilt with our own sets and characters in the current look.

Until the VO arrives each shot is a self-contained clip about 30% longer than its reference slot, laid end to end
(`shots_provisional.json`, 4720 frames). In Phase 2 the clip table gets the VO frames and each clip is **trimmed**
(never time-stretched).

## Cast (generic, no real likeness)
MPFB2 rigs re-used from our packages, re-dressed and re-toned (warm brown skin, dark-brown irises, dark hair):
- **Man** (the hero, donor ShoeBomber `Sleeper1`): white T-shirt, cream dhoti-style trousers, short-cropped dark hair
  (a scalp shell replaces the donor's fringe hair, which covered one eye). **Ageing** is one keyed value `Age`:
  hair and brows go grey (0.45) then white (0.85–0.95); a white beard shell appears from Age 0.6.
- **Wife** (donor SpeakWithoutSight `Mother`, long skirt): red sari-style skirt with a gold hem, green blouse, long dark hair.
- **V1, V2, V3** villagers (Tsunami2004 `Fisher`, `TouristM_C08`; CaveRescue `Coach`): plain shirts (blue, pink, yellow)
  and checked lungi-style trousers (green, blue, black checks). No skin-coloured clothes.

All MPFB humans: eye fix (all 5 EnhancedEye groups), camera-only catchlight per shot, opened elbow IK limit
(−40°…100°), `hand_poses` limits and presets, V3's brow/lash cards replaced (donor cards had lost alpha).

## Sets (one landscape)
- **The ridge**: a 530 m rock ridge along X, crest ~30 m, steep sandstone faces (Poly Haven rock_face_03, warm tint),
  feet at |y| = 55 m. The hero section (x ±30 m) is a closed solid with two boolean cutters:
  - **Cutter** = the passage, 3.6 m wide, open to the sky; its +Y end (`Cutter.location.y`) is keyed per shot:
    a shallow notch on day one (y = −52.4), deep in the 22-year shots, through (y = +61) at the end. It carries the
    packed-dirt gorge floor and a displaced close-up rock face (`CutFace`, shown only in the strike close-ups).
  - **LedgeCutter** = a shelf path carved into the west face at z = 6 m (the wife's path).
- **Village** (south, y −80…−105): 9 mud-plaster huts with thatch gable roofs, trees, shrubs; a wooden crate (logo).
- **Hospital** (north, y +100, straight through the ridge from the village): white two-storey block with wings,
  window rows, entrance canopy, red-cross panels (front and roof, symbol only, no text), packed-earth forecourt, a crate (logo).
- **The road** (asphalt, double yellow centre line): from the village east, round the ridge's far end (x ≈ 290),
  back west to the hospital. Long enough to read as "the long way round" from the air.
- Map graphics (no text anywhere): blue arrow (village → hospital), red X on the ridge, white route ribbon along the
  road (keyed build), green two-headed length arrow along the finished passage.
- Day light: one sun, gradient blue sky, AgX Punchy.

## Shot table (reference second → our shot; provisional clip length in frames)
| # | Ref s | Line | Who / what they physically do | Camera |
|---|---|---|---|---|
| 1a | 0–1 | He hit the chisel | CU: chisel in his left hand on the rock face, hammer in his right lands on its butt; chips fall. Face 3/4 above the hands. (160) | 32→34 mm, 3/4 side, slow push, f/8 |
| 1b | 1–2 | chipping off pieces | Aerial: the ridge, the village at its foot, the tiny worksite (he keeps striking). (150) | 30 mm drone, slow descent |
| 2a | 2–4 | of the mountain to build | Wide low: the man small at the foot of the huge face, striking. (200) | 24 mm, low, slow push |
| 2b | 4–6 | the entire tunnel all by himself | He walks across the grass to the rock face, arms swinging. (150) | 26 mm, side track |
| 3a | 6–8 | villagers laughed | Three villagers laugh (heads tip back in beats, shoulders shake); V1 points at the ridge; logo crate beside them. (180) | 26 mm, eye level |
| 3b | 8–9 | (laughed) | Closer: V2 laughs, V3 bends forward, hands on his thighs. (130) | 30 mm, slow arc |
| 4a | 9–10 | But he returned day after day | Low side: he walks back to the face in morning light. (130) | 22 mm, ground level |
| 4b | 10–11 | with just a hammer | Medium side: the strike cycle, full body. (150) | 30 mm, side |
| 4c | 11–12 | and a chisel | Macro: chisel edge on the rock, hammer lands, chips (forearms run to the frame edge). (120) | 40 mm, f/11 |
| 5a | 12–14 | Years earlier, his wife | She walks along the ledge path high on the rock face. (150) | 28 mm, below the ledge |
| 5b | 14–15 | had fallen | Her foot slips at the crumbling edge, arms come up, pebbles break away. **Cut before any fall.** (100) | 30 mm, feet/knees |
| 5c | 15–16 | off a cliff | Stones tumble down the face (no person on screen). (90) | 28 mm, from the foot |
| 5d | 16–18 | and was badly injured | She lies on the grass at the foot, still, face turned away from camera; no close-up. (160) | 28 mm, high side, slow push |
| 6a | 18–21 | But the nearest hospital was blocked by the mountain | Map: blue arrow grows village → hospital; red X stamps on the ridge. (260) | top-down 26 mm |
| 7a | 21–23 | And the only route went around it | He drags her on a bamboo drag-stretcher along the road (poles in his fists at hip height, rear ends on the road). (160) | 26 mm side track |
| 7b | 23–26 | stretching over 40 miles | Map: the white route ribbon draws along the road round the ridge's far end to the hospital. (220) | high aerial |
| 7c | 26–27 | (40 miles) | Front 3/4: he leans into the pull. (130) | 28 mm, backing up |
| 8a | 27–29 | His wife's injuries were too severe | He kneels at the roadside beside the stretcher, right hand on the bamboo pole, head bowing. (180) | 28 mm, slow push |
| 8b | 29–30 | and she died before they could reach the hospital | Close on him: head bowed, then lifts a little; she is not in close-up. (150) | 38 mm |
| 9a | 30–32 | So the man swore | Low angle: he turns to the mountain and looks up; fists close. (150) | 24 mm, ground level |
| 9b | 32–33 | no one else would suffer the same fate | Close: his determined face, the rock behind. (120) | 40 mm |
| 10a | 33–35 | And for 22 years | Aerial time-lapse: the cut creeps into the ridge. (180) | 28 mm drone |
| 10b | 35–37 | he chipped away | Deep in the gorge, hair greying (Age 0.45): striking. (150) | 26 mm |
| 10c | 37–38 | at solid rock | Older, white beard (Age 0.85): the strike, closer. (130) | 30 mm |
| 11a | 38–40 | until a passage finally cut | Last wall: his last blows, the slab cracks and falls outward, daylight pours in. (180) | 24 mm, behind-side |
| 11b | 40–42 | through the cliffs | He walks out through the finished passage toward the light. (150) | 26 mm, following |
| 12a | 42–44 | It was as long as a football field | Aerial: green two-headed arrow spans the passage end to end. (220) | 26 mm drone |
| 13a | 44–46 | and served as a quick route to the hospital | Two villagers walk through the passage toward the hospital. (150) | 24 mm, behind |
| 13b | 46–47 | which has saved | At the hospital: villagers walk to the door; the old man watches beside the crate (logo). (160) | 26 mm |
| 13c | 47–49 | countless lives | Close: the old man's face, a quiet nod, hospital behind. (160) | 40 mm |

## DA KRAS FILMS logo (two placements, never in the sad beats)
- **3a**: dark logo on the wooden crate beside the laughing villagers (village). Flat-on within 30°, ≥15% frame width, ≥1 s, f/8.
- **13b**: dark logo on the wooden crate by the hospital entrance (hopeful final beat).
- None in 5–8 (the wife's fall, the stretcher, her death).

## Risky shots and their simplest staging
1. **Hammer and chisel (1a, 2a, 4b, 4c, 10b, 10c, 11a).** He stands 0.85 m back from the face. The chisel is gripped once
   (`grip_object` wrap, Child Of the left wrist) with its edge on the rock, slightly left of his centre line; the left hand is
   re-keyed at the same matrix so the chisel never moves. The hammer is gripped once at the handle (wrap, Child Of the right
   wrist); the contact pose puts the striking face on the chisel butt with the handle running out to his right. The swing is a
   rigid move of that hand matrix: draw back 17 cm and out to the right with a 15° lift (the head stays at chest height, well
   below the hairline and away from his face and chest), fast hit, 3-frame hold, recoil. (Two earlier swing designs drove the
   head into his chest and up to his chin; both were caught on frames and by `body_prop_cross` and replaced.) Chips spawn at each hit and fall under keyed gravity. If a grip does not read cleanly,
   4c becomes the chisel tip and chips only, with the hands framed out.
2. **The wife's fall (5a–5d).** No fall on screen: her foot slips and pebbles break away (5b, cut), stones tumble alone (5c),
   then she lies still on the grass at the foot (5d), face turned from camera, no blood, no close-up.
3. **Lying body (5d, 7a/7c, 8a/8b).** The wife's rig is keyed in a straight standing-rest pose in armature space and the
   object is laid on its back (−90° X) on the grass or on the stretcher bed. Nothing touches her face.
4. **Drag-stretcher (7a, 7c).** The stretcher is keyed along the road with its rear ends on the asphalt and the pole tips
   at his hip height; his fists are keyed on the pole tips (wrap_grip, palm inward); his legs stay between the poles' 0.62 m
   spacing. `body_prop_cross` runs on the poles and slats.
5. **Kneeling by her (8a, 8b).** His right hand rests on the bamboo pole, never on her; the left on his thigh.
6. **Ageing.** One keyed `Age` value per shot (constant inside a shot): 0 → 0.1 → 0.45 → 0.85 → 0.95, beard from 0.6.
7. **Map and route.** 3D terrain from above with arrows and a ribbon only; no "40 miles" or "HOSPITAL" text.

## Look
Bright clean 3D animation (`STYLE_ANIMATED.md`): AgX Punchy, high sun, gradient blue sky, warm sandstone, saturated
grass, clean clothes. f/8–f/11 everywhere, no motion blur.
