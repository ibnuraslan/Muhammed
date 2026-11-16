# B15 NatashaRyan, Phase 1 plan

ConnectB15 · branch `claude/connectB15-natasha-ryan` · 1080×1920 · 60 fps · Cycles · hard cuts (one camera per shot, bound to timeline markers).

**Timing is provisional.** It follows the reference sheet's beat order and pacing (about 1 s per reference frame): 23 shots, frames 1–2820.
In Phase 2 the shot windows move to the VO word frames (`1 + round(s × 60)`). Every set's action is animated about 30% past its window, so shots get trimmed, never stretched.
The shot list is in `shots_provisional.json`.

**Old-style reference** (presenter + news footage): I took the story and beat order only. There is no presenter, no podcast mic, no newspaper text and no real photo. Every presenter beat became a story action. All people are generic MPFB characters, not likenesses.

The build is fully scripted (`scripts/01`–`04`):
- Characters are generic CC0 MPFB bodies reused from earlier studio packages (no asset server here), recoloured.
- Natasha is a fresh MPFB teen body (about 1.53 m). Her hair, eyes, clothes and shoes were carried over with Surface Deform.
- The eye fix is applied to every EnhancedEye group (9 groups), and the elbow IK limit is opened per rig (`nat_lib.setup_char`).
- Hands use the `hand_poses` presets (relaxed, flat_palm, open_alarm).

## Beats and shots

| Beat (ref s) | Shot | Frames (prov.) | Who and what, physically | Camera |
|---|---|---|---|---|
| In 1998, a 14-year-old girl (0–2) | S01 | 1–150 | School-photo sitting. Natasha (white blouse with closed neckline, navy skirt) sits on a stool before a mottled blue photo backdrop, hands on her lap. She straightens up and lifts her chin. Softbox stands are in frame. | Medium front, slow push-in, 50 mm. |
| Natasha (3) | S02 | 151–240 | Close: her face turns slightly toward camera. | 60 mm close, drift. |
| was dropped off (4–5) | S03 | 241–360 | Aerial: school campus, mother's blue car at the kerb, Natasha walking up the path with her backpack. The white delivery van with the **logo** is parked on the road. | High drone push toward the school. |
| by her mother (6) | S04 | 361–450 | The mother stands on the pavement by the car and gives a small shoulder-height wave. Natasha walks away up the school path. | Pavement-level three-quarter, slow drift. |
| at school. But she didn't (7) | S05 | 451–540 | Natasha walks up the path toward camera (face readable), backpack on. | Low front by the school entrance, crane up slightly. |
| return home later that day (8–9) | S06 | 541–660 | Dusk, porch light on. The mother walks down the family house path and looks up and down the street (head turns). | Street-side, slow push. |
| Her family contacted the police (10–11) | S07 | 661–780 | A searcher in orange overalls walks through knee-high grass (our own blade mesh), with a tree line behind. | Side tracking. |
| but they couldn't find her (12–13) | S08 | 781–900 | Wide: two searchers. One stops and crouches to look into the grass, hands on knees. | Wide, slow drift. |
| days turned into weeks, into months (14–16) | S09 | 901–1080 | Memorial table at the school fence: framed school photo (our own render of the generic girl), candles, bouquets. Two mourners stand at the sides, heads bowed. The sunlight goes from afternoon to golden evening during the shot (time passing). Replaces the newspaper. | Slow push to the photo. |
| her parents started to assume the worst (17–19) | S10 | 1081–1260 | Kitchen: the mother sits at the table, hands in her lap, head lowered. The father stands at the window, then turns to look at her. | Medium, slow push. |
| Then a year later, a local (20–21) | S11 | 1261–1380 | Outside a brick police station: two officers (navy shirts and caps) walk an older grey-haired man (brown overalls) down the steps toward camera. A police car is parked at the kerb. | Low front, slow push. |
| serial killer admitted (22–23) | S12 | 1381–1500 | Closer: the man walks with his head lowered. | 45 mm front, tracking back. |
| to the murder of Natasha (24) | S13 | 1501–1620 | Side profile of the three walking. | Side tracking. |
| Her family was devastated (25–26) | S14 | 1621–1740 | Kitchen: the mother at the table; the father stands beside her and lowers his head. | Three-quarter, push. |
| And four years later (27–28) | S15 | 1741–1860 | Courtroom wide: judge at the raised bench, counsel tables, gallery benches, tall windows with blinds and drapes (reference look). | High back corner, push-in. |
| her murder trial began (29–30) | S16 | 1861–1980 | The gallery from the side: the parents and other people seated, glancing around. | Side, slow drift. |
| in the middle of this trial the prosecutor (31) | S17 | 1981–2100 | The prosecutor (grey suit) stands at the lectern facing the judge and makes an open-palm gesture at chest height. | From the judge's side, over the lectern. |
| informed the court (32–33) | S18 | 2101–2220 | Closer: he turns his head toward the judge as he speaks. | 45 mm close. |
| that after five years (34–35) | S19 | 2221–2340 | Front row: the mother and father turn to look at each other. | Front of the gallery, low. |
| Natasha had been found alive (36–38) | S20 | 2341–2460 | Night, the same street. Natasha at 18 (black top) walks down the path of a house two doors from home beside a female officer, toward a police car with flashing red/blue bar lights. Street lamps and porch lights keep faces lit. | Low front by the kerb. |
| She was living (39) | S21 | 2461–2580 | A bedroom: she steps out of the open wardrobe (the hiding place; clothes on the rail); the officer stands in the room. | Room wide, push. |
| just 5 minutes down the road from her family (40–41) | S22 | 2581–2700 | Day: crane up from the house where she was found and pan along the street to the family house a few doors down. | Rising crane and pan. |
| the entire time (42–43) | S23 | 2701–2820 | Closer: Natasha standing by the wardrobe, small head turns. | 45 mm, slow push. |

## DA KRAS FILMS logo
- **One placement:** the dark logo on the road-facing side of the white delivery van parked outside the school (S03, and S04 background). This is the neutral opening moment, before she goes missing.
- There is **no** logo after S05. Everything later concerns the missing girl, the search, the trial and the discovery, so the brief forbids it there.
- In Phase 2 I will frame the van so the logo is at least 15% of the frame width and on screen for at least 1 s. If you want a second, neutral placement, I suggest a cardboard box on the kitchen counter (S10). Say if you want it.

## Risky shots and the simplest safe staging
- **Real people:** generic characters only. There are no distress close-ups of the girl. The killer is never shown with a victim; he is only walked out by police. The courtroom reveal is shown through clear faces: the prosecutor's head turn and the parents turning to each other.
- **Courtroom reveal with clear faces:** cameras sit on the judge's side and at the front of the gallery, so the faces read. Nobody's back fills a shot.
- **Hand contacts are minimal:** no handcuffs, no hands on people, no held props. The mother's hands rest in her lap (table contact dropped after the first check, §2.15). The prosecutor gestures in free air. The crouching searcher's hands rest on his knees.
- **Sitting:** the stool, the mother's kitchen chair, the gallery benches (our own build: seat, backrest, ends) and the judge's chair.
  - Seats are at real heights (0.42–0.47 m) and the hips sit just above them.
  - The judge's feet stand on the dais and hers on the wardrobe base (a raised floor in `ground_z`).
  - The extras in skirts stand rather than sit, so no skirt drapes through a seat.
- **Wardrobe:** our own carcass with both doors open 100°. She walks out through the clear opening. The cameras are placed away from the door leaves (lens-blocker rule).
- **Night (S20):** street lamps, porch lights, the flashing bar lights (keyed constant, not Scene Time) and a raised moon fill.

## P1 checks
- **Sheets:** `review/P1_sheet_3frames_1.jpg` and `_2.jpg`. They show the first, middle and last frame of every shot at 540×960, Cycles 8 spp.
- **`body_prop_cross`:** the whole film, step 6, on every held or touched prop and set piece per set, on the visible characters at every 6th frame plus the first, middle and last frame of every shot (516 frames). **Result: 0 visible crossings** (`review/body_prop_cross_P1.json`).

## Fixed during P1 (from my own sheet review and `body_prop_cross`)
- **Seats:** they are now at real heights, with the hips sitting just above them.
- **Kitchen:** the drawer desk is replaced by a real table (her knees were going into the drawers), and the father stands in S14.
- **Courtroom:**
  - The two extras in skirts or with long legs now stand at the back wall instead of sitting.
  - The prosecutor stands beside the lectern and gestures with the hand nearer the camera.
- **Natasha:**
  - A closed neckline (undershirt) under the blouse.
  - Her knees are together on the stool.
  - The backpack is raised off her skirt.
- **Ceilings** added in the kitchen, courtroom and bedroom (the sky showed above the walls before).
- **Grass** is our own blade mesh. The school model is rescaled (the cameras were inside it).
- **Lens blockers:** the S04 camera is moved off the fence and the S23 camera off the wardrobe door.
- **Faces:** the S21 officer is turned to profile (she was back-only for the whole shot).

## Known items, unsure, or left for Phase 2
1. **Road asphalt renders near-black** in S03, S04, S05 and S22, although its material is mid-grey. I'm still looking for the cause, and it will be fixed before Phase 2.
2. **The memorial photo (S09) reads as a blank board** at this distance. In Phase 2 I will fix the photo texture and push in closer so the face reads.
3. **Dusk and night house windows are dark** (S06, S20). I plan warm lit interiors behind the glass.
4. **The logo van (S03)** is small in the aerial. In Phase 2 I will add a low pass by the van so the logo is at least 15% of the frame width for at least 1 s.
5. **Asset credits** (CC-BY, Sketchfab via Objaverse) are in `review/asset_credits.json`: the school, two houses, the sedan, the van, candles, desk, chair, bed, flowers and tree. They go in CREDITS.md at Phase 2.
