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
| 1a (1–110) | B1 | Older woman (grey hair in a low ponytail, light lavender blouse and skirt) sits in the passenger seat, door open. A plain paper cup is wedged between her knees; her right hand pinches the lid edge. | Outside, low 3/4 through the open door opening (≥1.5 m from door frame, no glass near lens), slow push-in | Door frame / glass as lens blocker → camera well outside the car, door fully open and out of frame |
| 1b (111–300) | B1 | Her lap and face: she pinches the lid (thumb + index on the rim, lid Child Of her hand from the grip frame) and peels it up and away. The cup tips toward her; a dark coffee pool spreads over the skirt; steam rises. | From the open door, slightly high, her face and lap both in frame (a top-down lap-only view would crop her head: rejected fault) | Spill without a body crossing the cup: only her own lid hand, which lifts **away** from the cup; no other hand comes near it. No skin shown, no burn visuals: stain on fabric + steam |
| 1c (301–420) | B1 | Her face: she flinches, eyes wide, mouth slightly open, both hands lift up and out (open_alarm), body leans back into the seat | Medium close from the door side, f/8 | No teeth grimace; hands stay clear of the face and of each other |
| 2a (421–640) | B2 | A stainless coffee urn's tap pours a steaming stream into a white paper cup (DA KRAS FILMS logo) and the cup fills (the reference's pour) | Close front 3/4 on cup + spout, push-in, f/8 | No floating carafe: the urn pours, no hand needed. (The espresso machine's drip-tray lip hid the cup, so the pour moved to the urn.) |
| 2b (641–900) | B2 | The served cup on the counter, logo to camera, steam rolls up; camera rises to look into the cup (reference 9–12 s) | Crane up over the cup rim | Rim never inside the lens; stop 25 cm above |
| 2c (901–1200) | B2 | Top-down macro of the coffee surface: gentle simmer ripples, small bubbles, thick steam (reference 12–15 s) | Straight down, slow rotate + push, f/11 | Hero macro ≤ ~1 s per framing, keeps moving; nothing blurred |
| 3a (1201–1360) | B3 | Hospital: she lies propped up in bed, both thighs wrapped in clean white bandages (no wounds, no red), blanket at the shins; she breathes, shifts her shoulders, turns her head | Side medium from bed's long side, slow dolly | Clean bandages only; no distress close-up |
| 3b (1361–1560) | B3 | Doctor (blue scrubs) and nurse (green scrubs) at the foot of the bed; the doctor holds a clipboard at chest height in his left hand (pinch grip, Child Of) and reads; the nurse nods (reference 18–21 s) | Low over her bandaged legs toward the staff (her legs in the bottom third, no shoulder filling the frame) | Clipboards: `grip_object` Child Of hand bone; no arm crosses the patient; staff stay behind the foot rail |
| 3c (1561–1700) | B3 | Her face on the pillow: she looks toward the staff, small nod | Close, f/8 | Face fill ≤ 10 W; eyes checked |
| 4a (1701–1960) | B4 | Restaurant: a man (dark T-shirt) holds a steaming cup toward camera at chest height and looks at it, then at us (reference 21–24 s) | Medium close, slight orbit | One hand on the cup (cup_hold / grip_object), other arm relaxed; cup below the chin |
| 4b (1961–2280) | B4 | Wider: a line of 5 customers, 4 with steaming cups, each reacting: one looks down at the cup, one lifts it and shakes his head, others turn to each other | Lateral track along the line (reference 24–28 s) | Cups held low (chest), no cup at the lips (no "cup into face"); all clothes in clear non-skin colours |
| 5a (2281–2440) | B5 | Boardroom: an executive (grey suit) at the head of the table, a plain cup in front of him; he leans forward, both palms flat on the table, then sits back and exhales | Across the table, medium; a second executive's shoulder/back of head soft at frame edge (as in the reference, kept to < 1/4 of frame) | Hands flat on the table with fingertips on the surface; no hand to face |
| 5b (2441–2560) | B5 | Wide down the table: the boss at the far end, two executives at the sides turn to each other and nod | Wide from the other end of the table | — |
| 6a (2561–2700) | B6 | Employee (orange shirt, overalls) at the brewer reaches up and turns the temperature knob down | Medium side, his whole upper body in frame | Hand on knob via grip_object; knob rotates only while gripped |
| 6b (2701–2860) | B6 | Insert: the dial's arc gauge (blue → yellow → red, no text) and its needle swings from red back to yellow; steam over the cup below thins | Front-on clean insert, f/8, slow push (reference 32–35 s) | The needle is a gauge display, so it moves without a hand; no text on the dial |

## DA KRAS FILMS logo (1–2 placements)
- **L1, shots 2a/2b:** the white paper cup under the urn (and the served cup) carries the dark logo, flat to camera, ≥15% frame width, on screen > 1 s.
- **L2, shot 4a:** the same cup design in the man's hand, logo facing camera.
- Never in B1 (the injury) or B3 (hospital). **Question for the director:** the film brief's risk list says "no logo on
  the cup"; I read that as *no real brand logo*. If our logo must stay off cups too, I'll move L1/L2 to the menu-board
  frame above the counter and the employee's cap.

## Characters (MPFB default rig; built by re-fitting finished characters from our earlier films, see note)
- **Woman / patient**: female, age ≈ 0.92 (late 70s), grey bob, lilac top, grey sweatpants (B1); hospital gown in B3.
- **Doctor**, **Nurse**, **Hero customer**, 4–5 **customers**, 3 **executives**, **Employee**.
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
