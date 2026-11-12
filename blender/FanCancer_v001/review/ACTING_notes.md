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

Fixed: f1519, a 161° aim flip with 8 cm of movement during the move around the bed. The 25.45 s key now stays on the front side of the bed, so the look vector never reverses.
