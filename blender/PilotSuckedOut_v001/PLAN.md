# PilotSuckedOut (B17): plan (Phase 1, before the VO)

ConnectB17. Branch `claude/connectB17-pilot-sucked-out`. 1080×1920, 60 fps, Cycles CPU.
Reference: `briefs/batch2/B17_PilotSuckedOut_reference_1fps.jpg` (42 s, 1 frame/s). Shot order, subjects and framing follow it
in our current look. Hard cuts, about 1.7–3 s per shot at the provisional (1.3×) lengths.

Phase 1 timing is provisional: every shot is its own clip keyed at 1× from its first frame (`scripts/shots.py`). In Phase 2 the
lengths become the VO frames and `03_shots.py` is re-run: shots are only trimmed or extended at 1×, never stretched.

## Cast and sets
- **Captain** (MPFB "CAPT" from NoPilotPlane_v011: navy uniform jacket, white shirt, striped tie, cuff stripes; epaulettes
  removed because his arms go overhead). One rig, moved between sets at the cuts.
- **First officer** (MPFB "FO" from NoPilotPlane_v011, uniform with epaulettes), seated in the right seat, hands on the yoke.
- **Flight attendant** (MPFB "Attendant" from ShoeBomber_v008: dark pinstripe jacket, grey skirt, ponytail). Eye fix applied.
- Sets, far apart in one scene:
  1. **Cockpit** (origin): NoPilotPlane's cockpit (seats, panels, yokes, overhead, sky and farmland outside, sun shades removed).
  2. **737 exterior** (0, −3000, 0): ShoeBomber's plain-white 737 (no livery, no text), heading +X, the captain's front
     windscreen pane removed; a dark liner inside the nose so the open frame shows a dark cockpit. Cloud clusters drift aft.
  3. **Landing field** (0, −20000, −3000, on the farmland 3 km below): runway with plain markings (no numbers or text),
     grass, rolling hills, a landing copy of the 737 with simple gear, and a white service van (CC-BY) carrying our logo.

## Shot table (provisional frames, 60 fps)
| # | Frames | Ref (s) / words | Who and what they physically do | Camera |
|---|---|---|---|---|
| 01 | 1–156 | 0–2 "In 1990" | The 737 cruising past cloud clusters. | Front-left high, 30 mm, slow push toward the nose. |
| 02 | 157–266 | 2–3 "a pilot got sucked" | Captain is pulled up out of the open windscreen in 0.4 s, arms fly up, mouth opens. | Front-left of the nose, 35 mm, small rise. |
| 03 | 267–422 | 3–5 "out of a cockpit mid-air" | Out to the waist, leaning back in the wind, arms thrown up and flailing, shouting. | Front, medium, slow orbit. |
| 04 | 423–572 | 5–7 "his legs" | Inside: his legs rise from the seat area into the windscreen, kicking slightly. | Low behind-left of the captain's seat looking up, 22 mm. |
| 05 | 573–722 | 7–9 "preventing him from being fully ejected" | His legs lie over the glareshield, shoes hooked behind it above the yoke. | Left side window, level with the glareshield, 24 mm. |
| 06 | 723–862 | 9–11 "windshield had suddenly broken off" | Close on the empty frame at his waist; plain white papers whip out of the cockpit and tumble away. | Close front-left of the frame, 30 mm, f/11. |
| 07 | 863–1032 | 11–14 "causing the cabin to become rapidly" | Low exterior: the wind pushes him further back (24→40°), arms swept back, papers fly. | Low left, looking up past the nose, 28 mm. |
| 08 | 1033–1142 | 14–15 "depressurized" | Close: head back, shouting into the wind. | Close, 40 mm. |
| 09 | 1143–1302 | 15–17 "A flight attendant managed" | Attendant (kneeling on the captain's seat) lunges forward and grips both his shins, hands on the outer sides. | Front-left inside, her face 3/4, 22 mm. |
| 10 | 1303–1492 | 17–20 "the pilot's legs, and held on" | She holds on, leaning her weight back, face set. | Closer on her face and hands, 26 mm. |
| 11 | 1493–1648 | 20–22 "as the co-pilot attempted" | First officer flying, both hands on the yoke horns, small corrections. | Front-right inside, 22 mm. |
| 12 | 1649–1768 | 22–23 "to stabilize" | FO close, eyes on the windscreen. | 35 mm close. |
| 13 | 1769–1868 | 23–24 "His head was repeatedly" | Attendant holding, looks up toward the window. | Left, slightly above her, 26 mm. |
| 14 | 1869–2048 | 24–27 "striking the fuselage" | Captain folded back over the roof, head rocks toward the skin (never touches the lens or presses in; clear profile). | Side profile, 32 mm. |
| 15 | 2049–2198 | 27–29 "the crew thought he was dead" | Limp: arms trail aft, head lolled, mouth slightly open. | Slow push from the front-left. |
| 16 | 2199–2328 | 29–31 "But they kept holding" | Attendant braces harder; the FO glances at her, hands on the yoke. | From above the pedestal looking back at both faces, 18 mm. |
| 17 | 2329–2438 | 31–32 "so his body wouldn't fly off" | Wide front of the nose: the limp captain on the roof. | Wide, 35 mm. |
| 18 | 2439–2588 | 32–34 "and damage an engine" | Along the left side of the fuselage to the wing and engine. | Tracking aft, 28 mm. |
| 19 | 2589–2698 | 34–35 "or wing" | Engine and wing close, clouds streaming past. | Low beside the engine, 30 mm. |
| 20 | 2699–2868 | 35–37 "twenty minutes later" | The 737 descends over green hills toward the runway, gear down. | Low beside the runway, panning with it. |
| 21 | 2869–3018 | 37–39 "the plane landed" | Touchdown and roll-out. | Low right side, 30 mm. |
| 22 | 3019–3158 | 39–40 "and miraculously" | The nose rolls toward camera. | Low front-right, 35 mm. |
| 23 | 3159–3328 | 40–42 "the pilot ended up surviving" | The 737 rolls past the white service van parked by the runway (**logo**). | Low behind the van, 26 mm. |

Provisional total: 3328 frames (55.5 s). The VO decides the real lengths.

## Director P1 notes (Nov 16) and what changed (P1c)
1. FO eyes: his irises were pale blue on a pale sclera and read white; now brown irises, sclera toned to 0.82 on every character, catchlight kept.
2. Captain's arms (03/06/07/08): no Y pose; upper arms swept back along the fuselage with bent elbows, varying per key (seeded), mouth only parted (jaw 6–8°).
3. S14: lean 26–33° back and 20° to his left; head bone ≥17 cm from the skin, side profile camera in clear air.
4. Exterior look: deeper sky ramp and lower sky/world strength, sun 7.5 (shadows), farmland darker and more saturated, cloud clusters toned down; S18 reframed on wing + engine with sky.
5. Landing: 4 hangars and a control tower (CC-BY), perimeter fence, edge lights, Poly Haven trees and shrubs; S20 and S21 cameras pushed in.
6. S09: the attendant grips his shins from the first frame. FO framed out of S05.

## Logo (DA KRAS FILMS)
1. Side of the white service van by the runway, shot 23 (dark logo on white, flat-on, about 25% of frame width, f/11, >1 s).
Never on the plane (brief), never on a person, never during the captain's danger beats.

## Risky shots and the simple staging used
- **Crew hands on his legs (09, 10, 13, 16):** the attendant's palms sit on the OUTER sides of his shins (hand_poses
  `place_hand` + `wrap_grip`), her arms stay outside his legs, no arm crosses a body. Checked at the first, middle and last
  frame of every shot.
- **Body through the windscreen:** the 737's captain pane is really removed (a hole, not a texture); in the cockpit set the
  windows are shader cut-outs, so `bpc_b17.py` ignores crossings inside the window mask and reports everything else.
- **Face vs fuselage (14, 15, 17):** the torso leans back and to his left, where the fuselage falls away; the head keeps a gap
  of several cm and is filmed in clear profile. No face is pressed into the skin.
- **Seat belt / shoulder at frame edge:** no belts modelled; framing keeps shoulders inside the frame or clearly cut by an edge with the body implied.
- **No logo on the plane.** The 737 is plain white with no text.
