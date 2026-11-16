# ScaldingCoffee (B09): plan (checkpoint P1)

ConnectB09. Branch `claude/connectB09-scalding-coffee`. 1080×1920, 60 fps, Cycles CPU, hard cuts.
Reference: `briefs/batch2/B09_ScaldingCoffee_reference_1fps.jpg` (35 s, old style). Client direction (Nov 15): match its
shot order, subjects, framing ideas and pacing, rebuilt with real sets in our current look (`STYLE_ANIMATED.md`).
VO not in yet. Each beat is animated at 1× as its own clip, about 30% longer than the reference beat, in its own frame
window below. In Phase 2 each clip is **shifted** (never stretched) so its start lands on the VO word, and trimmed.

## Phase-1 timeline (clip windows; replaced by VO frames in Phase 2)
| Beat | Clip window (frames) | Ref. time | Story line |
|---|---|---|---|
| B1 spill | 1–420 (7.0 s) | 0–5 s | 1992: a woman spills hot coffee into her lap |
| B2 the coffee | 421–1200 (13.0 s) | 5–15 s | served at 190°F, only 22° from boiling |
| B3 hospital | 1201–1700 (8.3 s) | 15–21 s | skin grafts, 8 days in hospital |
| B4 complaints | 1701–2280 (9.7 s) | 21–28 s | over 700 earlier complaints |
| B5 backlash | 2281–2560 (4.7 s) | 28–31 s | massive backlash |
| B6 lower temp | 2561–2860 (5.0 s) | 31–35 s | so they lower the temperature |

## World layout (one scene, separate sets far apart, one camera object per shot, bound with markers for the hard cuts)
- **SetCar** (x = 0): parked 1980s sedan (Volvo-240-style model; badges, grille logo and plates removed/blanked) on a
  sunny car park, passenger door swung open. Interior: real front seats, a dashboard and a steering wheel we model.
- **SetCafe** (x = 40): fast-food style counter, a stainless coffee urn with a tap (the pour), and an espresso machine
  (brand lettering removed) carrying our temperature dial (coloured arc, needle, no text) and knob, white paper cups (plain, no brand), blank menu boards with food pictures only,
  tiled wall, bright ceiling panels. Used in B2 (pour, cup, surface macro), B4 (customers) and B6 (dial).
- **SetHospital** (x = 80): bright ward room, hospital bed, IV stand, window with blinds (never near a lens), curtain.
- **SetBoard** (x = 120): boardroom: long wood table, office chairs, plant, big window wall with a sky view, a cup.

## Shot list (1–2.5 s each, hard cuts; every shot has a moving subject or a push-in)
| Shot | Beat | Who / what, physical action | Camera | Risk → safe staging |
|---|---|---|---|---|
| 1a (1–110) | B1 | Older woman (grey hair in a low ponytail, light lavender blouse and skirt) sits in the passenger seat, door open. A small plain paper cup (no logo), lid already off and lying on the dashboard, sits between her knees, steaming; her hands rest on her thighs. | Outside, low 3/4 through the open door opening (≥1.4 m from the door frame, no glass near the lens), slow push-in | Door frame and glass as lens blockers: the camera stays well outside the car, and the door is fully open and out of frame |
| 1b (111–300) | B1 | Her lap and face: she leans forward to look at the cup, shifts on the seat, and the cup tips forward toward her knees; a dark coffee pool spreads over her lap; steam rises. **No hand touches the cup or lid** (a lid pinch was tried and failed the contact check repeatedly, so it was re-staged per LESSONS §2.15). | From the open door, slightly high, her face and lap both in frame | The small cup sits between the knees without touching them (body_prop_cross 0) |
| 1c (301–420) | B1 | Her face: she flinches, eyes wide, both open hands lift up and out (open_alarm), and she leans back into the seat | Medium close from the door opening, f/8, lens 55, framed below the roof lining | No teeth grimace; hands clear of the face and of each other |
| 2a (421–640) | B2 | A stainless coffee urn's tap pours a steaming stream into a white paper cup (DA KRAS FILMS logo) and the cup fills (the reference's pour) | Close front 3/4 on cup + spout, push-in, f/8 | No floating carafe: the urn pours, no hand needed. (The espresso machine's drip-tray lip hid the cup, so the pour moved to the urn.) |
| 2b (641–900) | B2 | The served cup on the counter, logo to camera, steam rolls up; camera rises to look into the cup (reference 9–12 s) | Crane up over the cup rim | Rim never inside the lens; stop 25 cm above |
| 2c (901–1200) | B2 | Top-down macro of the coffee surface: gentle simmer ripples, small bubbles, thick steam (reference 12–15 s) | Straight down, slow rotate + push, f/11 | Hero macro ≤ ~1 s per framing, keeps moving; nothing blurred |
| 3a (1201–1360) | B3 | Hospital: she lies propped up in bed, both thighs wrapped in clean white bandages (no wounds, no red), blanket at the shins; she breathes, shifts her shoulders, turns her head | Side medium from bed's long side, slow dolly | Clean bandages only; no distress close-up |
| 3b (1361–1560) | B3 | Doctor (blue scrubs) and nurse (green scrubs) at the foot of the bed, hands relaxed; the doctor looks down at her, the nurse nods (reference 18–21 s). Clipboard dropped: the doctor's grip on it failed the contact check | Low over her blanketed legs toward the staff | No arm crosses the patient; staff stay behind the foot rail |
| 3c (1561–1700) | B3 | Her face on the pillow: she looks toward the staff, small nod | Close, f/8 | Face fill ≤ 10 W; eyes checked |
| 4a (1701–1960) | B4 | Restaurant: a man (dark T-shirt) holds a steaming logo cup at chest height, looks down at it, then at us (reference 21–24 s) | Medium close, slight push | One hand wraps the cup (palm 2.5 cm off the wall, fingers closed onto the sleeve), the other arm relaxed; cup below the chin |
| 4b (1961–2280) | B4 | Wider: a line of 5 customers; two hold steaming cups, the others react (head shake, turn to each other) | Lateral track along the line (reference 24–28 s) | Cups held low (chest); no cup at the lips; clothes in clear non-skin colours |
| 5a (2281–2440) | B5 | Boardroom: the boss (grey suit, white hair) at the head of the table, a plain cup in front of him; he leans in and looks down at the cup, then sits back | Across the table, medium | Hands rest in his lap under the table edge (palms-on-table failed the contact check) |
| 5b (2441–2560) | B5 | Close 3/4 on the boss: he looks up, exhales and gives a small head shake | Close from the side of the table, f/8 | Side executives dropped (fewer bodies, no chair contacts) |
| 6a (2561–2700) | B6 | Employee (orange shirt, overalls) stands in the aisle and reaches straight forward to the temperature knob on the machine's side panel (the machine is turned so this panel faces the aisle) and turns it down | Front 3/4 from his right, his face and hand in frame | Tripod grip on the knob rim (fingertips 3 mm from the target point); the knob rotates only while gripped (body_prop_cross 0) |
| 6b (2701–2860) | B6 | Insert: the dial's arc gauge (blue → yellow → red, no text) and its needle swings from red back to yellow; steam over the cup below thins | Front-on clean insert, f/8, slow push (reference 32–35 s) | The needle is a gauge display, so it moves without a hand; no text on the dial |

## DA KRAS FILMS logo (1–2 placements)
- **L1, shots 2a/2b:** the white paper cup under the urn tap (and the served cup) carries the dark logo, flat to camera, ≥15% frame width, on screen > 1 s.
- **L2, shot 4a:** the same cup design in the man's hand, logo facing camera.
- Never in B1 (the injury) or B3 (hospital). Confirmed by the director (Nov 15).

## Characters (MPFB default rig; built by re-fitting finished characters from our earlier films, see note)
- **Woman / patient**: female, age ≈ 0.92 (late 70s), short grey hair (MakeHuman short02, refitted), light lavender blouse and skirt (B1); pale blue gown tint in B3.
- **Doctor**, **Nurse**, 5 **customers** (the hero is C4), the **boss** (B5), the **Employee** (B6).
- Every character: eye fix (`LegoInNose_v001/scripts/eye_fix.py`), camera-only catchlight, elbow IK limit opened,
  relaxed hands (`hand_poses`), neutral wrists, clothes in clear non-skin colours, fringe off the eyes.
- **Note:** the MakeHuman asset server (files.makehumancommunity.org) is down, so the MPFB clothes/hair/eye library
  can't be installed. Characters are appended from our earlier packages (CC0 MakeHuman assets), given a new phenotype
  (age, weight, height) and every proxy is refitted with MPFB's own `create_mhclo_from_clothes_matching` →
  `reapply_macro_details` → `fit_clothes_to_human` → `refit_existing_armature`.

## Assets
Sketchfab CC-BY via Objaverse (credits in CREDITS.md): Volvo-240-styled sedan (Libau Media), Front Car Seats
(D0uble_Zer0), Simple Hospital Bed (Yvo Pors), IV Stand and Bag (Somar52), Regular ole Clipboard (Maggatron),
Commercial Coffee Machine (M.Reslan) / Canarian Cafe Coffee Machine (Lanzaman), Conference Table 6 m (MozillaHubs),
Office Chair (Tytan). Poly Haven CC0 textures/HDRI. Cups, steam, coffee surface, brewer dial, counter: modelled by us.

## Contact check (body_prop_cross, step 3, per beat, on every held or touched prop)
Props: B1 cup, lid, car seats, door, dash, floor, wheel · B3 bed, mattress, backrest wedge, pillow, blanket, IV stand,
cabinet · B4 customer cups, counter · B5 table, chairs, cup · B6 dial knob, dial, machine, both counters.
Result: **0 visible crossing frames in every beat** (`review/body_prop_cross_summary.txt`). The steam volumes are
excluded because they are gas, not solid.
