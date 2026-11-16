# AlcatrazSpoons: plan (Phase 1, checkpoint P1)

ConnectB07. Branch `claude/connectB07-alcatraz-spoons`. 1080×1920, 60 fps, Cycles CPU. Hard cuts, shots of 1–2.5 s.
Client direction (Nov 15): **match the reference still sheet** (`briefs/batch2/B07_AlcatrazSpoons_reference_1fps.jpg`, 49 s):
same shot order, subjects, framing ideas and pacing. We rebuild every shot ourselves (our sets, our characters, our look).

Until the VO arrives, each shot is a self-contained clip about 30% longer than its reference slot, laid end to end on
a provisional timeline. In Phase 2 the shot table (`shots.json`) gets the VO frames and the build script places and
**trims** each clip there (no time-stretching of character animation).

## Cast (generic, no real likeness)
MPFB2 rigs re-used from our own earlier packages (the MakeHuman asset server is down: 502), re-dressed:
- **P1, the leader**: dark short hair under a white knit cap, mid-30s.
- **P2**: lighter hair, white cap, slightly heavier build.
- **P3**: white cap, stubble-dark brows (the drill operator).
- **Guard**: 1960s grey-blue uniform shirt and trousers, peaked cap, flashlight.

Prisoners wear the reference's look: **white uniform with black horizontal stripes** (clothes only, never skin colour)
and white knit caps (Child Of the head bone; hair hidden under the cap, so no fringe over the eyes). All MPFB humans
get the eye fix, a camera-only catchlight, an opened elbow IK limit, relaxed hands with neutral wrists and the
`hand_poses` wrist and finger limits.

## Sets (one scene, separate areas; each shot has its own camera, bound by a marker at its first frame)
- **S1 Cell** (night, warm lamp plus blue moonlight, readable): pale green painted concrete, a steel bunk with
  pillow and blanket, a small basin, the vent grille low on the back wall under the basin, rubble on the floor, bars
  at the front.
- **S2 Service corridor**: a narrow utility corridor behind the cell row, the back of the same vent (a broken-out
  hole), pipes and conduits on the walls, dust in the air, a wooden supply crate (**logo**).
- **S3 Shaft and roof**: a brick utility shaft with a fixed steel ladder up to a roof hatch, then the outside brick
  wall with a vertical vent pipe (blue-grey) down to the ground.
- **S4 The bay** (dusk, deep blue but readable): a gently waving water plane, the grey raincoat raft (patchwork of
  rubberised raincoat panels, seams visible), the island's lights behind, and a generic suspension bridge far away
  (no real landmark details).

## Shot table (reference second → our shot)
| # | Ref s | Line (reference idea) | Shot: who and what they physically do | Camera |
|---|---|---|---|---|
| 1a | 0–2 | three prisoners, spoons | CU of P1 facing camera, lifting a spoon to chest height and looking at it; P2 and P3 lean in over his shoulders, eyes on the spoon. Spoon pinched in P1's fingers. | 50 mm, eye level, slow push-in, f/8 |
| 1b | 2–4.5 | dig through the walls | Same trio, slightly wider. P1 turns his head to the wall behind; P2 nods toward the vent. The dug-out vent opening is visible behind them. | 40 mm, slow lateral arc left |
| 1c | 4.5–7 | Alcatraz cell, 1962 | Wide of the cell at night: the trio crouches toward the vent under the basin; bunk, bars and a blanket-covered bed. | 24 mm from the bars' corner (inside the cell, ≥1 m from the bars), slow push |
| 2a | 7–8.5 | night after night | Low wide: P1 and P2 kneel at the vent under the basin, both scraping, rubble on the floor around their knees. | 28 mm, floor level, slight push |
| 2b | 8.5–10 | scraped away | 3/4 side of P1 kneeling, scraping the vent edge with the spoon; his face in profile-3/4, crumbs falling. | 35 mm, side, slow arc |
| 2c | 10–12 | concrete around the vents | Over the shoulder: P1's forearm and hand (arm runs to his shoulder in frame) scraping the corner of the grille. | 40 mm, f/8, slow push |
| 2d | 12–14 | gradually widening | Close on the grille corner: the spoon tip scrapes, the gap visibly widens (rubble grows), hand and sleeve run off the frame edge. | 50 mm, f/11, slight drift |
| 3a | 14–16 | a makeshift (drill) | P3 kneels and turns a small motor (vacuum motor with a fan housing) in both hands, cup hold, looking at it. | 35 mm, low 3/4 front |
| 3b | 16–17 | from a vacuum cleaner | Insert: the home-made drill resting on the floor (motor, spoon-bit, red cord); the fan spins up. No hands. | 50 mm, f/11, macro push |
| 3c | 17–20 | speed up the process | P3 crouches at the vent and holds the drill to the grille edge with both hands, red cord trailing; dust puffs. Face 3/4. | 35 mm, side-front, slow arc |
| 4a | 20–22 | lifelike dummy heads | CU: the dummy head (a painted plaster prop with real-looking hair tuft) on the pillow, blanket up to its chin; a flashlight beam slides across it. | 50 mm, f/8, slow push |
| 4b | 22–23.5 | fool the guards | Guard at the bars, medium: he raises the flashlight, looks in, nods and lowers it. Face lit. | 35 mm, inside the cell looking out through the bars (bars ≥1 m from lens) |
| 4c | 23.5–25 | during bed checks | The dummy head again from the other side as the beam leaves; slow pull. | 50 mm, f/8 |
| 5a | 25–27 | after months of digging | Corridor side: the vent grille in the green wall; dust trickles, the grille rattles. | 35 mm, low, slow push |
| 5b | 27–28.5 | broke through | P1's hands push the grille out from inside (forearms going into the hole, his face behind them); it drops to the floor, dust burst. | 35 mm, low |
| 5c | 28.5–31 | and crawled | P1 crawls out of the hole on hands and knees into the corridor through the dust. | 28 mm, floor level, side-front |
| 5d | 31–34 | the service corridor behind the wall | P1 stands and walks along the corridor among the pipes, looking up; P2 follows. The supply crate with our logo is on the left. | 28 mm tracking backward ahead of them |
| 6a | 34–36 | they climbed to the roof | P1 and P2 climb the fixed steel ladder up the shaft; hands on rungs, feet on rungs. | 24 mm, low looking up, slight crane |
| 6b | 36–38.5 | slid down a vent pipe | Outside at night: P1 slides down the vertical pipe, hands wrapped round it at chest height, knees and feet hugging it; lands. | 28 mm, side-wide, tilt down with him |
| 7a | 38.5–40 | to the island shore | The three in the raft, seen low from behind-side, the bay and the far bridge ahead. P1 paddles with a short board; P2 and P3 hold the raft's side ropes. | 28 mm, near water level |
| 7b | 40–42 | a raft | Side medium of the raft: raincoat patches and seams, three seated, swaying on the waves. | 35 mm, water level, lateral track |
| 7c | 42–44 | from raincoats | Front 3/4: the three faces, determined, raft bobbing. | 35 mm, slow push |
| 8a | 44–46 | despite a massive manhunt | From the island: a searchlight beam sweeps across the dark water; a patrol boat with a spotlight crosses the frame. | 35 mm, high on the shore |
| 8b | 46–49 | they were never found | Wide: the tiny raft drifts away toward the bridge into the dusk mist. Slow pull-back and rise. | 35 mm, slow crane up |

## DA KRAS FILMS logo (one placement, maybe two)
- **5d**: the dark logo printed on the side of the wooden supply crate in the corridor. It faces the camera (within 30°), is about 20% of the frame width and on screen for about 2 s, at f/8.
- Optional second placement: **8a**, the white logo on the patrol boat's hull, only if it reads at ≥15% width; otherwise left out.
- None on prisoners, the dummy head, the vent, the drill or the raft (key props).

## Risky shots and their simple staging
1. **Spoon at the grille (1a, 2b–2d).** The spoon is Child Of P1's right hand bone via `hand_poses.grip_object` (pinch), with no gap. In 2c the whole forearm runs to a visible shoulder. In 2d the hand is at most 30% of frame and the sleeve leaves the frame edge; if the grip isn't clean after one retry, 2d becomes the spoon tip and rubble only, with the hand framed out.
2. **Dummy head (4a, 4c).** A stand-alone prop head lying on the pillow (not a character's face pushed into anything). It's a painted plaster look: matte, eyes closed, hair tuft, blanket over its "body". No hands touch it.
3. **Pipe slide (6b).** The pipe is 12 cm thick and 25 cm off the wall. Both hands wrap it (`wrap_grip`) at chest height, never above the head; the knees and feet hug it. Wide side view so the hands are small. The body slides at constant speed and lands with a knee bend.
4. **Raft seating (7a–7c).** Each man sits on the raft floor with his legs inside the tube; hands rest on the side rope or knees (one holds a short paddle board in `wrap_grip`). The raft and bodies bob together (one parent empty), so nothing passes through the tube. `body_prop_cross` runs on the raft.
5. **Ladder climb (6a).** Rungs every 30 cm, hands on rungs at head height at most, feet on rungs (no feet on nothing). A slow 1× climb cycle, seen from below-behind with faces turning up 3/4.
6. **Crawl (5c).** Hands and knees on the floor (`ground_z`), short crawl cycle at 1×; then he rises.
7. **Breakthrough (5b).** The grille only moves while P1's hands are on it (keyed contact frames), then it falls under gravity to the floor. Never moves by itself.
8. **Drill (3a–3c).** The motor rests in both palms (`cup_hold`) in 3a; in 3b it rests on the floor; in 3c both hands wrap the housing. Cord is a curve from the motor to off frame.
9. **Guard (4b).** Shot from inside the cell; the bars are at least 1 m from the lens; the guard's flashlight hand is at chest height with a visible arm.

## Look
Bright clean 3D animation (`STYLE_ANIMATED.md`): AgX Punchy. Night scenes are blue-tinted with warm practical lights and
faces lit (fill ≤10 W). Smooth, simple textures; bump ≤0.35. No text anywhere except the logo crate.

## Build scripts (`scripts/`)
`01_chars.py` (append and re-dress rigs, eye fix, caps, stripes) → `02_sets.py` (S1–S4, props) → `03_shots.py`
(one function per shot: animation + camera, placed from `shots.json`) → `04_stills.py` (P1 sheet).
Phase 2 reruns `03_shots.py` with VO frames in `shots.json`.

## P1 status (checkpoint, Nov 15)
- Built: `scripts/01_chars.py` (characters), `02_sets.py` (S1–S4 + props), `03_shots.py` (24 clips + cameras + markers),
  `shots_provisional.json` (clips laid end to end, about 1.3× each reference slot, frames 1–3822).
  Phase 2 only rewrites the shot table to the VO frames and trims; every clip keys its own first and last frame.
- Review: `review/P1_still_sheet.jpg` (one 540×960 Cycles 8-sample frame per shot) and `review/P1_stills_540x960/`.
  First, middle and last frame of every shot were rendered and checked over five rounds.
- Fixed while building:
  - black lash and brow cards from the donor rigs (alpha restored);
  - dark image eyes (now procedural EnhancedEye);
  - heads pressed into the wall at the vent;
  - an arm behind the back and hands on the backside in 2a;
  - the dummy's neck cut;
  - the guard's flashlight lighting his own chest;
  - the corridor hole that wasn't cut (non-manifold cutter);
  - shot edges interpolating into the next shot;
  - a camera inside the basin (2b);
  - lens blockers (basin, stool, crate);
  - the searchlight cone showing outside 8a.
- Changes from the plan:
  - 1a: P1 sits on a stool so P2 and P3 can lean over his shoulders, as in the reference.
  - The basin sits beside the vent, not above it (head room for the kneelers).
  - The corridor floor is level with the vent sill, so the crawl is flat.
  - The logo crate is mid-corridor (5d), dark logo, about 20% of frame width.

## P1 PASSED (director, Nov 16, commit e25a431)
Phase-2 to-do (no P1 round):
- **2a:** P1 bends forward with his face turned down into the wall corner, so the face doesn't read.
  - Lift his head and turn it 3/4 toward the camera while he scrapes, e.g. `head=(10, -35)` in his `p_kneel_scrape` call for 2a.
  - Re-check the spoon grip with `body_prop_cross` afterwards.
