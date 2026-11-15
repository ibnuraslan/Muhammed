# B06 AshaDegree, Phase 1 plan

ConnectB06 · branch `claude/connectB06-asha-degree` · 1080×1920 · 60 fps · Cycles · hard cuts (one camera per shot, marker-bound).

**Timing is provisional.** It follows the reference sheet's pacing, about 1 s per reference frame, 48 s = frames 1–2880.
In Phase 2 the shot windows move to the VO word frames (`1 + round(s × 60)`). Each set's action is already animated about 30% past its window, so shots are trimmed and never stretched.
The shot list is in `shots_provisional.json`. The stills are in `review/P1_stills.jpg` (one 540×960 frame per shot, Cycles 8 spp).

The build is fully scripted (`scripts/01`–`05`). Characters are generic MPFB/MakeHuman CC0 bodies reused from earlier studio packages, because the MakeHuman asset server is unreachable from this container (proxy 502). Each was recoloured and re-dressed.

## Beats and shots (matching the reference order, subjects and framing)

| Beat (ref s) | Shot | Frames (prov.) | Who and what, physically | Camera |
|---|---|---|---|---|
| In 2000, a 9-year-old girl (0–2) | S01 | 1–120 | Girl kneels on the rug behind her pink book bag (two round badges: white, and a heart), hands flat on its top, smoothing and closing it. Toy-brick towers, floor lamp, plaid wallpaper. | Low three-quarter front, 1.6 m, slow push-in. |
| | S02 | 121–210 | Close: she looks down, then lifts her head and looks off to the side. Face readable. | 45 mm side-front, slight push. |
| named Asha, packed a book bag (2–4) | S03 | 211–330 | Standing with the bag on her back. She settles, turns and starts walking to the open French doors. Rain is visible outside. | Medium front, push-in. |
| left her house in the rain (4–7) | S04 | 331–420 | She walks to the open right door leaf and out into the rain, in profile. | Side tracking at 1.05 m. |
| really early in the morning (7–10) | S05 | 421–540 | Night highway sidewalk, rain, street lamps. She walks away under a red umbrella held in her right fist (shaft vertical, Child Of the wrist). | Low behind, tracking. |
| | S06 | 541–660 | Front three-quarter: her face under the umbrella. | Low front, tracking backward. |
| a passing motorist saw her (10–12) | S07 | 661–780 | A dark-blue sedan with headlights passes her from behind and slows. | Roadside, tracking. |
| walking along the highway (12–13) | S08 | 781–870 | Wide: tiny figure with umbrella; the car stopped ahead with tail lights. | High wide, slow drift. |
| he circled back / approached (14–15) | S09 | 871–960 | She stops and looks back over her left shoulder toward the car. | Low behind, right. |
| Asha ran into (16–17) | S10 | 961–1080 | She turns and runs off the sidewalk toward the tree line, umbrella lowered at her side. | Roadside, panning. |
| the woods, by daylight Asha was gone (18–20) | S11 | 1081–1170 | Running between firs in the rain (no umbrella after the cut). | Side tracking. |
| | S12 | 1171–1260 | Wide: she runs away and becomes small among the trees. "Gone" is shown as distance, not a dark frame. | Behind, slow follow. |
| leaving behind a few belongings in a nearby shed (21–24) | S13 | 1261–1380 | Day. White-sided shed, door open. A searcher in a yellow jacket crouches at the door; another in a hi-vis vest stands holding a clipboard. Small items on the shed floor (pencil, marker, hair bow). | Wide front. |
| | S14 | 1381–1500 | The clipboard searcher reads, then looks up toward the woods. | Medium, head and chest. |
| extensive searches, no trace (25–29) | S15 | 1501–1650 | Dusk woods, rain. Two searchers walk and sweep torches (spot beams, no volumetrics); one crouches by the bench. | Wide, slow push. |
| | S16 | 1651–1800 | Closer: a searcher walks forward sweeping his torch. Face lit. | Medium, side-front. |
| A year later her book bag was found (30–31) | S17 | 1801–1890 | Close on the pink bag lying in the dirt under a crinkled plastic wrap. | 40 mm close, push-in. Everything sharp (no DOF). |
| at a construction site, covered in a plastic bag (31–36) | S18 | 1891–2040 | A worker (hard hat, yellow sleeves, overalls) squats and reaches; his flat palm lands on the wrapped bag. A fallen school-crossing sign (pictogram only, no text) lies in the foreground. | Three-quarter front at 0.9 m. |
| | S19 | 2041–2190 | Close: his hand rests on the plastic over the bag. His arm runs back to his body in frame. | Close, slow drift. |
| but it revealed nothing (37) | S20 | 2191–2280 | Reverse angle: the worker crouched over the bag, looking at it. | Behind-side. |
| No one knows why she left (38–40) | S21 | 2281–2370 | Memory figure: a solid, softly glowing cyan girl with umbrella and bag walks along the wet night road. | Behind three-quarter, tracking. |
| or where she was going | S22 | 2371–2460 | The same figure in profile. | Side tracking. |
| one of the most puzzling unsolved cases (41–47) | S23 | 2461–2670 | A framed portrait on a warm wall: our own render of the generic girl holding a teddy bear. It is not the real child's photo. | Slow push-in. |
| | S24 | 2671–2880 | Closer, from a slight angle. | Drift and push. |

## DA KRAS FILMS logo
- **One placement:** the cardboard toy box in the living room (dark logo, S01 background). This is the neutral opening moment, before anything sad happens.
- There is **no** logo after S04. Every later beat concerns the missing child (searches, the found bag, the memorial), so the brief forbids it there.
- To fix in Phase 2: in S01 the box is partly cropped at the frame edge. I will move it so the logo is at least 15% of the frame width, flat-on and on screen for at least 1 s. **A second placement is not planned unless you want one.**

## Risky shots and the simplest safe staging
- **Real missing child.** Generic MPFB girl, no likeness. No distress close-ups, no speculation imagery. "Gone" is shown as distance in a lit wood. The final photo is our own render.
- **Night rain.** Every night frame has street-lamp, moon-fill and torch light. Faces are lit and no frame is empty or black. The rain is thin geometry-node streaks that fall continuously and fire no timed events.
- **Umbrella in hand.** The shaft is vertical through a wrap-grip fist (Child Of `wrist.R`), with the hand below the head.
- **Door.** The leaf is already open (no prop moving by itself, no hand on glass).
- **Book bag.** It is on the floor until the S02→S03 cut, then on her back (Child Of `spine03`). It is our own model: rounded body, pocket, badges, loop.
- **Searcher torches.** Spot lights only. I removed the beam cones because they blocked the lens.
- **Found bag.** The worker's flat palm rests on top (no grip, no peeling). The bag xy is solved from the palm position.

## Known issues (Phase 1, fixing while I wait for the VO)
1. S02: the floor-lamp shade sits directly behind her head (background merge). The camera will move.
2. Girl: the jacket hem has small jagged patches at the hips. Her face reads early-teen rather than 9 (the reused body's phenotype). She has no shoulder straps on the front.
3. S09: in the look-back pose the umbrella canopy tilts out to her side and is partly cut by the frame.
4. S17: the plastic wrap reads as white flakes on top, not a wrapped bag. The wrap needs a proper shrinkwrap shell.
5. The umbrella is a low-poly faceted model. A better one is pending.
6. S16: the torch arm reaches out sideways at the end of the shot.
7. Rain streaks occasionally pass close to the lens (one white streak in S12).
8. Checks (`clip_scan`, `qa_check`, `limb_check`, `body_prop_cross`) have not run yet. They run on the packed Phase 2 file.
