# Gap Analysis — Seldom (Nvidia part 1/2) vs Yarnhub / Fern / Atrium

Sources:
- Seldom: `nvidia_part1_contact_sheet.jpg` + REPORT (branch `claude/nvidia-part1-mp4`), `nvidia_part2_contact_sheet.jpg`, `nvidia_part2_v2_c5_17_contact_sheet.jpg` + REPORT (branch `claude/nvidia-part2-mp4`), and our character code `nvidia_doc/scenes/human.py`.
- Targets: the files in this folder (`YARNHUB_STYLE_BIBLE.md`, `02`–`07`).

Effort: **E** = Easy (rule or preset change) · **M** = Medium (new script or asset set, days) · **H** = Hard (new toolchain, weeks). "New tool" = something we don't have today.

## 0. Where we stand (from our contact sheets)

| Area | Seldom now (Nvidia) | Target |
|---|---|---|
| Format | 1920×816 = **2.35:1 already** ✔ | 21:9 ✔ (keep) |
| Sets | Clean, sparse, mostly white/grey (archive room, lobby, server hall, warehouse); few props; big empty floors | Dense, worn, layered sets with foreground objects (Yarnhub mud/grass; Atrium wallpaper, lamps, carpets) |
| Light | Flat even daylight in many interiors; good mood in the night offices (city windows, desk lamps) | One motivated key, deep falloff, practicals in frame |
| Colour | Neutral grey/white dominated, low saturation | Earthy (Yarnhub) or oxblood/walnut/brass (Atrium); measured palettes in the bibles |
| Characters | MakeHuman procedural bodies, **procedural `pose_walk()` cycle**, static poses (`pose_sit`, `fingers_curl`), no facial animation, no mocap, no IK, no collision check | Chest-up staging, mocap-quality body motion where shown, small facial expressions, hands only in single-action inserts |
| Shot motion | REPORT lists **6 frozen shots (zero motion)** and 2 mostly static in part 2 | Every shot has a motivated move or subject motion |
| Coverage | Mostly single wides/mediums per beat; few inserts and POVs | Establishing → MCU face → POV → insert → result (Yarnhub chain) |
| Titles | Two-line chapter title over a dimmed scene (`title_card.py`) ✔ | Fine; add date/place/name/spec/countdown cards |
| City/exteriors | Blocky low-detail skyline, empty roads | Photo-scanned ground, foliage, atmosphere, depth haze |

## 1. Characters (the user's three problems)

### Problem 1 — expressions, actions, "weird walks"

| # | Gap | Fix in our Blender pipeline | Effort | New tool? |
|---|---|---|---|---|
| 1.1 | Walk is a procedural sine cycle (`pose_walk(h, phase)`) → no weight shift, foot sliding | **Replace with mocap clips**: CMU Mocap (BVH, free), Rokoko free packs (FBX), Mixamo (FBX, free with an Adobe account; check licence for commercial use), Adobe/Reallusion ActorCore free set. Retarget to the MakeHuman skeleton with **MPFB2** (MakeHuman's official Blender add-on: Rigify/Mixamo-compatible rigs + BVH import) or Rokoko's free Blender retargeting add-on | M | Yes: MPFB2 / Rokoko add-on + mocap library |
| 1.2 | Feet slide on the floor | Foot IK + **foot-lock**: bake mocap, then add IK targets on the ankles, key them locked during contact frames (detect contacts where foot height < 2 cm and velocity < 0.05 m/frame) | M | No (script) |
| 1.3 | Walks shown in full body on bare floors | **Staging rule from Yarnhub/Atrium**: never show a full-body walk longer than 2 s on a clean floor. Use: chest-up tracking, back view in low light, long lens through foreground, motion blur, or start/stop the shot on a static pose | E | No |
| 1.4 | No facial expression | MakeHuman/MPFB2 face rig (expression pose units: smile, frown, surprise, squint) or shape keys from the MakeHuman expression set. Keep to **small, held expressions** (Yarnhub level). Add blinks every 3–5 s and eye saccades (1–2° jitter) | M | MPFB2 face rig |
| 1.5 | No lip-sync | Don't lip-sync. Yarnhub/Atrium avoid it: dialogue = subtitled short lines over a non-speaking face, back view or OTS | E | No |
| 1.6 | Characters "stand and pose" | Every shot gets **one verb** from the script (aim, crank, read, grab, turn to look, sit back). Build a library of 30–40 short mocap actions (sit/stand, pick up, hand over, point, look over shoulder, phone call, typing, drinking, slump) | M | Mocap library |
| 1.7 | Emotion relies on the body | Emotion via **ECU eyes** + light change (Yarnhub 10:11, 10:51) + a short VO line | E | No |

### Problem 2 — hands through hands, hands through body

| # | Gap | Fix | Effort | New tool? |
|---|---|---|---|---|
| 2.1 | Arm/hand poses keyed by rotation only | IK for hands too: hand IK targets parented to props (cup, phone, gun, paper) with **Child Of** constraints; switch the constraint influence at grab/release frames | M | No |
| 2.2 | Interpenetration goes unnoticed | **Automatic collision QA** per frame: build a BVH tree (`mathutils.bvhtree.BVHTree.FromObject`) for each body part from vertex groups (hands, forearms, torso, thighs) and test overlaps; fail the shot if any hand vertex is inside the torso or another hand by >5 mm. Output a CSV + a red-highlight preview frame | M | No (script) |
| 2.3 | Fingers stiff | Use the mocap's hand data where available, else a pose library (relaxed, grip, point, flat on table) blended by a single "grip" slider | M | No |
| 2.4 | Hands visible in wides doing complex things | **Rule from Yarnhub**: complex hand actions only in **inserts** (close, short, 1–3 s, one action, gloved or dark-lit). In wides, hands rest, hold one prop, or are in pockets or out of frame | E | No |
| 2.5 | Self-intersection of clothes | Cloth as a proxy with a "Shrinkwrap + Corrective Smooth" after the armature, or a cloth sim only for hero shots | M | No |

### Problem 3 — every movement needs a proper human action

| # | Gap | Fix | Effort |
|---|---|---|---|
| 3.1 | Movement not motivated | Shot plan column **"action verb + reason"** (e.g. "turns head → hears the door") | E |
| 3.2 | No anticipation / follow-through | When keying by hand: add a 4–6 frame anticipation and a 6–10 frame settle; mocap gives this for free | E |
| 3.3 | Idle bodies frozen | Add a subtle breathing + weight-shift idle layer (mocap idle, 30–60 s loop) under every standing or seated character | E |
| 3.4 | Crowd walkers overlap | Crowd avoidance: Blender Geometry Nodes points on a nav path with min-distance (Poisson disk) + per-agent offsets; keep crowds out of focus (Fern/Atrium). For real crowds: CrowdRender-style instancing of 6–10 mocap cycles with random time offsets | M |

## 2. Render, shading, environment

| # | Gap | Fix | Effort | New tool? |
|---|---|---|---|---|
| 4.1 | Sparse, clean sets | Set-dressing pass per set: 3 depth layers (foreground prop/plant/edge, mid action, background detail). Use CC0 assets (Poly Haven, ambientCG) + Quixel-type scans where the licence allows | M | Asset library |
| 4.2 | New, clean materials | Wear layer: grime/edge-wear masks (AO + curvature node), dust on top faces, fingerprints/roughness breakup on glass and metal | M | No |
| 4.3 | Flat interior light | `look.py`: one key (window or practical), fill ≤ 1/8 of the key, practicals visible in frame, volumetric haze (density 0.002–0.01) for light shafts | E | No |
| 4.4 | Grey palette | Grade per film to a measured palette (Yarnhub earthy, Atrium period warm); keep look v5's real-colour rule | E | No |
| 4.5 | Exteriors look CG (blocky city) | Photo-scanned ground + scatter (grass, debris), HDRI sky, aerial perspective haze; for cities use detailed kits only in the foreground, silhouettes in the haze behind | M–H | Asset kits |
| 4.6 | Clean digital image | Add lens character in comp: slight vignette, 0.3–0.5 px chromatic aberration at the edges, fine grain, mild bloom on practicals and fire | E | No |
| 4.7 | VFX (fire, smoke, explosions) | Mantaflow for hero shots; for speed, licensed VDB/flipbook explosions and smoke columns composited | M | VDB library |

## 3. Camera and editing

| # | Gap | Fix | Effort |
|---|---|---|---|
| 5.1 | Frozen shots (6 in part 2) | QA gate in `chapter_shots.py`: reject any shot whose camera and subjects both move < 0.5 % of the frame width over its duration | E |
| 5.2 | Camera at eye height, centred | Default lower heights (hull/knee height for exteriors, seated eye line for interiors); rule-of-thirds framing | E |
| 5.3 | Single angle per beat | Coverage template per beat: wide → MCU → POV/insert → reaction (see `CINEMATIC_SHOT_PLAYBOOK.md`) | E |
| 5.4 | Moves are linear | Camera rig with ease-in/out, a subtle handheld noise modifier (0.2–0.5° rotation, 0.5–1 Hz) for interiors, slow dolly for exteriors | E |
| 5.5 | Shot length | Target **median 3.5–4.5 s**, p90 ≈ 10 s, one long take (15–30 s) per chapter (Yarnhub 3.9 s, Atrium 3.2–4.3 s, Fern 3.4–6 s) | E |
| 5.6 | POV shots missing | Mask library: binoculars, gun sight, periscope, keyhole, phone screen, CCTV | E |

## 4. Sound

| # | Gap | Fix | Effort |
|---|---|---|---|
| 6.1 | Mix level (ours −14 LUFS in part 1) | Fine for YouTube. Keep −14 integrated, LRA 4–6; refs measure −10.4 to −15.9 with LRA 3.3–3.8 | E |
| 6.2 | Beds | Never true silence; per-location beds (room tone, city hum, server whine) under everything | E |
| 6.3 | Foley density | Foley list generated from the shot plan's action verbs (each verb → 1 sound); `sound_design.py` places them on the action frames | M |
| 6.4 | Music | Cues per beat: tension pulse / action / decision stinger / aftermath pad; duck 6–8 dB under VO | E |

## 5. Biggest wins, in order

| Rank | Change | Effort | Fixes |
|---|---|---|---|
| 1 | **Staging rules**: chest-up / seated / back-view; no full-body walks on clean floors; complex hand actions only in inserts | E | Walks, hands, expressions |
| 2 | **MPFB2 + mocap library + retarget** (CMU / Rokoko free / Mixamo / ActorCore) replacing `pose_walk` and static poses | M | Walks, actions |
| 3 | **Collision QA script** (BVH overlap per frame) + hand IK to props | M | Hands through bodies |
| 4 | **Set dressing + wear + one-key lighting** | M | "CG empty room" look |
| 5 | **Coverage template + POV masks + no frozen shots** | E | Cinematic feel |
| 6 | Small facial expressions + blinks + ECU eyes | M | Expressions |
| 7 | Hybrid live-action close-ups (Fern Hansa) for the hardest acting moments | M, new tool (camera + actors) | Faces/hands at full realism |
