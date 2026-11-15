# FanCancer: acting review of v002 (half-second sheet `review/ACTING_before_0.5s.jpg`)

Frames are v002 frames (frame = 1 + 60·t). Every story-beat start frame in `beats.json` stays unchanged.

| # | t (s) / frames | Problem | Fix in v003 |
|---|---|---|---|
| 1 | 0–13 / 1–780 | The fan's feet are re-placed under the pelvis at every pose key, so they **slide** as she leans in, glances and nods. | Feet planted at fixed world spots for the whole rink sequence; only the hips and spine move. |
| 2 | 0–16 / 1–980 | The manager's idle yaw sway rotates both feet on the spot (**foot sliding**). | Feet planted; only the pelvis, spine and head turn. |
| 3 | 16.2–18.0 / 973–1081 | The manager's turn to the knock is a **root spin on planted feet** (0°, 40°, 120°, 180°). | Real stepping turn: right foot lifts and steps, then left, then right, with weight shift and head leading. |
| 4 | 1.0 / 61 | A bench player sprawls over the boards with his arms flung out: an odd, unmotivated pose. | Bench players sit with their forearms on their knees and react with small lean-ins and head turns. |
| 5 | 2.5 / 151 | The camera goes **through the glass / board top**; the frame is filled by the board. | The camera rises above the glass (z ≈ 2.9) before crossing it. |
| 6 | 13.0 / 781 | The frame is filled by the **top of her beanie** (she bows toward the camera). | Lower, more frontal camera; she stays upright. |
| 7 | 12.6–13.0 / 757–781 | The phone **appears in her hand by itself**. | Her right hand goes to her hip pocket and draws the phone (it appears under the hand), then lifts it. |
| 8 | 13.4–15.8 / 805–949 | Typing posture: deep hunch, **head hanging**, phone jammed against her face. | Upright stance, phone at chest height in front of her, head tilted 14°, thumbs typing. |
| 9 | 15.9–17.5 / 955–1051 | The slap reaches **through the glass plane** (hand target 10 cm past it) and is overhead; the knock hand also goes past the glass. | The phone lands flat on the glass at eye level (z 1.40); the knuckles stop on the glass surface. |
| 10 | 17.5 / 1051 | A near-black frame filled by the board and floor while the camera crosses over the glass. | Camera framed on the manager as it comes over the glass. |
| 11 | 18.0–19.0 / 1081–1141 | The **back of the manager's head fills the frame** (over-shoulder too close). | Wider, higher over-shoulder that shows the phone on the glass and his profile. |
| 12 | 20.9–28 / 1255–1681 | The manager walks with **arms frozen** at his sides; the nurse does the same. | Natural counter-swing of the arms with the steps (both walkers). |
| 13 | 23–25.4 / 1381–1525 | The dermatoscope lens glows like a **floating white ball** next to his neck. | Lens is plain dark glass; the scope is visible in her gloved hand. |
| 14 | 25.4 / 1525 | The dermatoscope **vanishes from her hand**. | Her hand goes to her coat pocket and the scope goes in there. |
| 15 | 25.5 / 1531 | Half the frame is his blurred shoulder (the camera swings through him). | The camera arcs around behind the bed to the doctor's face. |
| 16 | 26.0 / 1561 | The frame top is filled by the **doctor's ponytail**. | New path; the camera stays clear of her head. |
| 17 | 26.0 / 1561 | The forceps **appear in her hand by themselves**. | Drawn from her pocket under the hand. |
| 18 | 26.5–28.3 / 1591–1699 | The camera sits **behind his back**: the back fills the frame and her hands are barely visible. | Side views from his right that show both gloved hands at the neck and his profile. |
| 19 | 28.2 / 1693 | The **bandage pops onto the neck** by itself. | She carries the bandage in her left hand from her pocket and presses it on (Child Of hand, then the neck). |
| 20 | 28.4 / 1705 | The forceps vanish mid-air. | Returned to her pocket by her hand. |
| 21 | 30.0 / 1801 | His phone **appears in his hand by itself**. | His right hand goes to his hip pocket, draws the phone, and lifts it. |
| 22 | 34.5 / 2071 | A **black frame**: the camera clips geometry in the city. | Camera path re-routed down the middle of the street. |
| 23 | 35.0–35.5 / 2101–2131 | The camera **enters the building facade** (dark wall fill) before the window pass. | It stops 2.6 m in front of the lit window and passes through it while the window fills the frame. |
| 24 | 37.5 / 2251 | A blurred orange frame: the camera approaches the laptop screen **from behind** (the normal sign was wrong). | It approaches from her side; the screen fills the frame. |

## Also fixed in v003 (found by `clip_scan.py` / `qa_check.py` and on the sheets)
| # | Problem | Fix |
|---|---|---|
| 25 | MPFB helper geometry (skirt, tights, joint cubes) became live when the scanners switch off the MASK modifier, so neighbouring fans' hands read as "inside" each other. | The helper geometry is deleted from every body mesh (it is never rendered). |
| 26 | Crowd fans' cheering arms swung forward into the row in front, and their resting hands hovered over the seat backs. | The cheer is a V shape, capped at 145°; resting hands lie on the thighs. |
| 27 | The manager's hands on his hips sank into his hips. | The hands sit on the hip surface. |
| 28 | The doctor stood inside the exam-bed footprint, and her hands at his neck went through his torso. | The bed moved +0.6 m; her hands work at the back of his neck from outside. |
| 29 | The city had a 5 m street, the bus drove inside a building, and window cards floated in the sky (glTF quaternion rotation ignored). | A real 28 m street with buildings rotated, and only window cards that have a facade behind them. |
| 30 | The tunnel run (21.8–23 s, beat 8) had no one in frame. | Two staff walk up the tunnel toward the camera. |
| 31 | Beats 5–7: the camera passed through the glass. | The camera stays on the ice side; the double-sided phone screen shows the blurred note from the front. |
| 32 | Hands: hand-set finger angles. | `hand_poses.py`: `add_hand_limits` on all 96 rigs, `apply_pose` for every action (flat palms on the boards, phone hold, fist knock, wrap on the dermatoscope, pinch on the forceps and bandage, open shrug, flat-palm clap), and `grip_object` on both cheque edges. |

## qa_check.py flags kept on purpose (reason)
- **EMPTY 301–516 (5.0–8.6 s):** the skin cutaway. The beat is the mole and the cells, so no character is in view by design.
- **EMPTY 1903–2140 (31.7–35.6 s):** city establishing shots and the bus. The riders are small inside the bus.
- **EMPTY/FILL 1381 (23.0 s), 2143–2155 (35.7–35.9 s), 2251–2269 (37.5–37.8 s):** surface passes through the clinic door, the lit window and curtain, and the laptop screen. Each is under 0.4 s and shows macro detail.
- **FILL 271 (4.5 s), 517 (8.6 s):** the dive into and out of the skin at the mole.
- **BACKHEAD 235 (beat 3, 3.9 s):** her POV of the mole on the back of his neck, which is the story point.
- **HOVER Fan.L near the glass 991–1033 (16.5–17.2 s):** the knock. Between knuckle strikes the fist pulls back from the glass.
- **HOVER near confetti (finale):** confetti falling past hands.

## Camera cuts (v004c, director's cut/roll check): every one-frame jump is covered on both sides
Strips: `review/CAMCUT_strips.jpg` (F−1 and F at each cut, rendered from the package). Roll is 0.

| Cut (F−1 → F) | F−1 | F |
|---|---|---|
| 300 → 301 | macro of the mole on his neck | skin-macro mole (cutaway) |
| 516 → 517 | skin-macro mole | mole decal on his neck at 1.5 cm |
| 1902 → 1903 | clinic ceiling diffuser grid | lit city window at 35 cm (new covered pull-back to the street by 32.25 s) |
| 2154 → 2155 | lit facade window | curtain knit |
| 2280 → 2281 | laptop-screen pixel grid | blank cheque face at 12 cm (new: the cut moved from 37.9 s to 38.0 s, when the cheque exists on the ice; beat 13's frame is unchanged) |

Fixed in v004d: the laptop push (2276–2279) is clamped in front of the screen plane, and the neck pull-back at 518 eases straight back before the swing. CAMJUMP is only the 5 covered cuts. Strip: `review/CAMCUT_strip_v004d.jpg` (516–520 and 2272–2284).

Fixed: f1519, a 161° aim flip with 8 cm of movement during the move around the bed. The 25.45 s key now stays on the front side of the bed, so the look vector never reverses.

## v005 (client VO arrived): moving preview check (`review/preview.mp4`, pages in `review/preview_pages_v005/`)
I watched every page of the 270×480 preview (every 5th frame) and fixed these faults. Beat frames are unchanged, and no VO has been added.

| t (s) / frames | Fault | Fix |
|---|---|---|
| 16.0–20.5 / 961–1231 | The phone went **through the glass**. The wrist limit clamped her pose, so the phone was 6 cm past the glass. | The phone is pinned flat on the fan's side of the glass, 1–10 mm from the glass face, and stays in her hand (influence 16.0→20.5 s). The slap and knock hand targets are pulled back. |
| 1.9 / 115 | The manager's face filled the frame, blurred. | A wider key at 1.95 s. |
| 3.3–3.9 / 199–235 | Her beanie filled the POV. | The camera is raised and pulled back. |
| 17.2–17.8 / 1033–1069 | The camera skimmed the manager's head. | A key at 17.4 s swings wide of his head. |
| 19.5–19.9 / 1171–1195 | The camera went **through the manager's head** (inside of the ear). | The arc goes back out behind him (19.8 s and 20.2 s keys at y −1.6). |
| 19.0–19.4 | The camera skimmed his shoulder. | A key at 19.0 s keeps it wide. |
| 22.8 / 1371 | A tunnel staff face filled the frame. | The staff are spread to y −1.80 and −0.32. |
| 30–33 | The city walkers collapsed. | They are removed. |

## v006 (director review of v005): fixes. The preview `review/preview.mp4` (528 frames) is rendered from the final v006 package, with pages in `review/preview_pages_v006/`
| Frames | Fault | Fix |
|---|---|---|
| f1–60, 661–1001, 2381–2640 | **Black human silhouettes** in the stands. These were the seat backs: the seat glb's custom split normals broke when the build scaled the model, so the seats shaded pure black. | The custom normals are cleared in `02_build_scene.py`, and the seats render blue and grey. |
| 241–300 | The push into the back of his neck until skin filled the frame. | The shot stops on his head and shoulders with the mole visible, then hard-cuts into the skin at f301. |
| 2151–2296 | The dive into the laptop screen: a giant blurred face, a pink smear, plain white. | The camera holds on her at the laptop, then cuts straight to a medium rink shot at f2281. |
| 1901–2150 | 4 s of empty city. | He stays in frame posting on his phone until 34.0 s (f2041). The city and bus pass with phone-holding riders now lasts 1.9 s. |
| 1381–1700 | The doctor's coat merged into his back. | She stands 12 cm further back with less lean (hand reach adjusted). The camera at 24.3 s is at his left front so she reads beside him, and the overhead pass goes around the front. |
| 2516–2640 | The ending pulled back until the people were specks. | It ends on a medium shot of her with the cheque and the players. |
Beat frames are unchanged and there is no VO.

## v007 (director review of v006): fixes. The preview `review/preview.mp4` is rendered from the final v007 package, with pages in `review/preview_pages_v007/`
| Item | Fault | Fix |
|---|---|---|
| 1 | Headless framing of him posting (1831–2041) and the pink stool blob. | He is framed head to knees from 30.0 to 35.9 s. The stool leaves the clinic after 29.3 s. |
| 2 | She was a black silhouette at the glass, and the phone covered her face (961–1006). | A fill light on her face and torso (hidden from the camera, reflections and the glass). The phone is pressed on the glass at chest height by her fingertips, and her face shows above it. She stands 8 cm further back with less lean, so her chest never touches the glass. Check: phone y 0.009–0.018, fan body min y ≥ 0.007 (glass face 0.008). |
| 3, 4 | A floating glove, and the doctor's A-pose. | Camera keys at 27.4 and 28.3 s from his left front show her whole. Her hands rest at her coat pockets (25.6 and 29.2 s). |
| 5 | Stray orange shapes. | A copy of the home desk lamp sat in the clinic. It is hidden. |
| 6 | Dark eye holes. | The EnhancedEye cornea fix (LESSONS §3) is now applied to every character (`03e_eyes.py`). |
| 7 | Empty and in-wall city frames. | The city pass is removed: a straight cut from him posting to her at the laptop at f2155. |
| 8 | Her forearms crossed. | Both palms go to her chest, apart. |
| 9 | The beanie popped on at 2276. | It is off for the whole home shot and comes on at the rink cut, f2281. |
| 10 | The ending was wide, with mannequin players. | A medium shot from about 2 m: her with the cheque, the man clapping beside her, and players around her clapping, fist-pumping and turning with their arms moving. The cheque stays text-free (director confirmed the rule). It reads as a big cheque from its oversized board, a blue band across the top, a signature line and an ink scribble. |
| 11 | Minor items. | The camera passes higher above him at 1.9 s, and the POV is moved off her beanie at 3.3–3.9 s. |

## v008 (director review of v007): fixes. The film is now **1–2490 (41.5 s)**. The preview `review/preview.mp4` (498 frames) is rendered from the final v008 package, with pages in `review/preview_pages_v008/`
| Item | Fault | Fix |
|---|---|---|
| 1 | The phone posting was a 7 s static shot, and the phone was a dark dot at his knee. | 28.75–30.8 s: relief, with the doctor beside him (she no longer walks across the lens). At **beat 10 (f1849)** a cut to a medium shot: he lifts the phone to his chest and thumb-types, his face lit by a phone glow light (2.6 s). At **f2005**, a 1.2 s insert of the phone screen filling the frame: a blank post layout with a photo of her at the glass, share icons pulsing and a share bar filling. No text. Beat 11 (f2029) falls in the insert. At **f2077**, a cut to her at the laptop. |
| 2 | The ending: the cheque hid her, a player's head sat on hers, and the shot was static and wide. | She holds the cheque at waist height, so her face and shoulders are clear. Nobody stands directly behind her. The camera is about 0.3 m higher with a slow push-in (2.75 → 2.05 m). The shot is cut to 3.5 s (f2281–2490), so the film ends at f2490. |
| 3 | Her arms crossed at the laptop. | Both hands rise together from the laptop to her chest, palms flat (the hand-to-mouth swing is removed). |
| 4 | An empty corridor, sky and door frame. | A clean cut at **beat 8 (f1333)** from him walking at the rink to the clinic. |
| 5 | Bodies near the lens. | The clinic camera keys are moved to stay at least about 1.2 m from people. The doctor stays put. The nurse stays in the far corner. The rink exit camera is raised above the bench players. |
The beat frames are unchanged, and there is no on-screen text.

## v009 (director review of v008). The preview `review/preview.mp4` (498 frames) is rendered from the final v009 package, with pages in `review/preview_pages_v009/`
| Item | Fault | Fix |
|---|---|---|
| 1 | The ending was a static wide, her face unreadable, with mannequin players. | The camera is at about 1.6 m and chest height, with a slow push to 1.4 m. She is framed from the waist up over the cheque, which she holds at her waist; her face is clear and smiling. Two people stand close beside her and clap with IK hands meeting in front of the chest: a new player `FinPlayer` on her right (kept under the ice before the cut) and the man on her left. The other players stand well back (≥ 4.5 m), off to the sides. |
| 2 | Clawed hands on her collarbones. | Her right palm is open with the fingers together (`shield`), raised at her chest in surprise, and her left hand stays on her lap. No claw and no crossing. |
| 3 | His head passed close to the lens (f121–131). | The 1.95 s key is 0.5 m further back and higher. |

## v010 (director review of v009). The preview `review/preview.mp4` (498 frames) is rendered from the final v010 package, with pages in `review/preview_pages_v010/`
| Item | Fault | Fix |
|---|---|---|
| 1 | The cheque filled the bottom half as a white slab. | The camera is about 0.4 m higher (z 1.74–1.78), tilted down onto her at lens 38. The cheque reads as a band across the lower third, with its blue border and signature line visible, and the slow push is kept. |
| 2 | Her expression read as shocked or screaming. | The finale and the end of the laptop shot use a happy smile: smile 1.0, lips slightly parted (jaw 5), and eyes narrowed. The stunned open mouth stays only at 36.4–37.2 s, at the first moment at the laptop. |
| 3 | His head near the lens at 121–136. | The 1.95 s and 2.2 s keys are higher (2.65–2.75 m) and further back. He now passes mid-frame below the camera. |

## v010b (director review of v010). The preview `review/preview.mp4` (498 frames) comes from the exact v010b package: f1331–1461, f1846–2006 and f2281–2490 were re-rendered from it, and every other frame is unchanged from v010. Pages are in `review/preview_pages_v010b/`
| Item | Fault | Fix |
|---|---|---|
| 1 | The ending: an A-pose, a neutral face, no movement, and a clapper's face cut by the frame edge. | She holds the cheque by its top edge with both hands, elbows bent, in front of her chest; the cheque hangs below as the lower band. A small bounce, a sway and a head tilt are keyed every 0.3 s, with a happy smile (smile, squint, lids). Both clappers stand closer (x −0.68 and +0.08), and their faces stay inside the frame through the slow push (1.70 → 1.50 m). |
| 2 | The posting shot was near-frozen (1851–2001). | The push-in is stronger (lens 38 → 46 → 52). He lifts his head once (about 32.0 s), his body sways, and his thumb keeps tapping. |
| 3 | The exam room opened on a static wide (1336–1426). | A slow push into the room (22.2 → 23.6 s, lens 30 → 36). |
