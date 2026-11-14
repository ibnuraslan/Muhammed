# EscapeArtist v007: moving-preview review and fixes

Source: v006b. I watched it as a moving preview (`pipeline/preview.py`, every 5th frame) and checked it with `body_prop_cross.py`. The fixes are in `EscapeArtist_v001/scripts/06_fix_v007.py`, which runs on the v006b build. Beat start frames are unchanged and no VO is added. All frame numbers are film frames (60 fps).

## Faults found in v006b and how v007 fixes them
| Frames | Fault (v006b) | v007 fix |
|---|---|---|
| everywhere | DOF at f/4–5.6: blurred macros, blurred bars and props across the lens | DOF kept on at **f/11** (director, 21:37): no visible blur at these distances. The preview was rendered with DOF off; f/11 was set in the package afterwards, as the director asked. |
| 150–300 | white "KeyGlow" memory overlay floating by his eyes, a giant blurred shape in the lens | removed |
| 30–145 | the guard's back fills the frame for about 2 s | camera keys 45 and 95 moved to a high corner (lens 22–24) |
| 265–285, 520–540 | near-empty wall and arm frames | camera keys 276 and 535 aim at him |
| 300–540 | **file and scrap not in his hands**: the handle floats beside the fist; extreme hand macros | file baked into the right fist (wrap grip), scrap pinched in the left; medium shots (keys 330, 390, 450, 510); 8° dutch removed |
| 541–627 | **key not in his hand**: the fist floats beside the lock | key baked into the right pinch until it is in the lock; IK snaps the pinch onto the key in the lock (pinch-to-key distance about 2 cm) |
| 682–708 | black frame and empty wall while the camera flies through the corridor wall | the camera faces the memory room before the wall; `Corridor_FarWall` hidden (render and viewport) for 682–708; AimFix off for 689–709 |
| 850–865 | the back of the boy's head fills the lens | camera keys 830 and 890 moved off his head |
| 1000–1085 | **the toolbox moves by itself** beside the father, then floats in front of the boy; oversized | scaled to 75%; carried in the father's right fist at his side, handed fist to fist at 1048, carried at the boy's side |
| 1150–1420 | the stepmother's pointing arm is locked straight out | elbow bent (target pulled in, pole behind) |
| 1380–1547 | **the gavel floats** in front of the judge's hand; giant gavel in the lens | gavel in the judge's fist in a hammer grip; the fist does the strike; camera key 1445 pulled back |
| 1600–1792 | **fence**: head, face and feet through the chain-link; hands grab above the mesh top; legs through the mesh and razor wire going over | re-staged on the real geometry (top rail 3.1 m, outrigger to y −14.18 at 3.58 m); see below |
| 2186–2440 | **sawing**: both hands at x ±0.15, exactly on bars 1 and 3, so fingers and arms pass through the bars | one-handed diagonal stroke across bar 2, with the handle toward the cell; left hand braced on the wall at his left side; saw baked into the right fist |
| 2566–2898 | tube parented to the wrist with an offset | the bent tube is baked into his right fist (wrap grip) |

### Found while watching the v007 preview (fixed, re-rendered and spliced)
| Frames | Fault | Fix |
|---|---|---|
| 243–253, 583–593 | the camera passes through the cell-front bars (qa INSIDE at 252) | `CellFront_0` hidden (render and viewport) only while the camera crosses its plane (248–253, 588–593; found automatically) |
| 276, 558 | the back of his head on the beat-2 and beat-3 start frames (qa BACKHEAD) | camera keys 276 and 558 moved in front of and beside him |
| 1410–1455 | the gavel head is rotated 90° about the handle and reads as a paddle | the head's axis follows the arm, so the face strikes down |
| 1775–1785 | the camera flies through the fence outrigger | key 1785 above the coil (z 4.55) |
| 3570–3580, 3630–3635 | the camera flies through the fence top on the way to the protesters and back | keys 3570, 3590 and 3632 keep it above 4.7 m over the fence |

## Fence re-stage (beat 8)
1. **Climb (1600–1700):** his body stays 0.5 m off the mesh. His hands stay below the top rail, fingers hooked into the chain-link, and his feet are on the mesh.
2. **Over the top (1700–1741):** a dark wool blanket covers a 1.2 m gap cut in the razor coil, draped over the top rail and the outrigger. He hoists over the rail, swings his legs over above the outrigger, and sits on the blanket's edge facing out.
3. **Jump (1743–1792):** a free fall (g = 9.8 m/s²) forward and away from the fence into the existing 1792 landing crouch, then the run.

## Checks on the packed v007 file
- `body_prop_cross` on the bars (WinBar_0_*, 2172–2484): **0 visible crossings** (`bpc_bars.json`).
- `body_prop_cross` on the fence (Object_8, RazorWire_Top, Blanket, 1600–1795): `bpc_fence.json`.
  - The remaining hits are **fingers hooked into the chain-link** during the climb. A real chain-link grip puts the fingers through the holes. I checked by position: the crossing points are 0.11–0.2 m below the wrists, along the fingers.
  - There are small seat and body contacts on the blanket while he sits on it (1720–1744).
  - Tool note: `body_prop_cross` labels each crossing body part by vertex index, and MPFB's mask modifiers reorder the evaluated vertices. So its labels (for example "head|Object_8") are wrong on MPFB bodies; check by position.
- `qa_check` on the delivered file (`qa_v007.json`):
  - **CAMJUMP 0, ROLL 0, INSIDE 0, HOVER 0, FACEPRESS 0.**
  - BACKHEAD 1: frame 3498, the old man, unchanged since v006b.
  - FILL 4, CLAW 41: grip_object holds on thin props.
  - EMPTY 159: room-wide frames, as in earlier rounds.

## Preview of the delivered file
`review/preview.mp4` and `review/pages/` show the delivered `EscapeArtist_v007_60fps.blend`.
- The full pass is `preview.py`, every 5th frame. The ranges changed after it were re-rendered from the final package at the same settings and spliced in: 205–660, 1380–1550, 1710–1830 and 3495–3670.
- A per-frame camera dump of every build shows that nothing changed outside those ranges.
- I watched every page.

## Known remaining items (not fixed in this round)
- **2885–2895, 3485–3490, 2500–2505:** about 0.15–0.25 s of empty cell while a character has just left or not yet arrived.
- **3505–3520:** the camera slides past the window jamb on the way out. The wall fills half the frame for about 0.25 s, with his hand on the bar.
- **3740:** one preview frame of brick as the camera pulls out to the closing exterior wide (59.5–61 s, accepted earlier).
- **1505–1528:** about 0.3 s of cell wall while the camera crosses cell 6 to its window, on the way into the yard.
- **1400–1405, 1485:** single preview frames where the camera passes a wall (under 0.1 s).
- The court back-wall light reads as a bright soft rectangle (1460–1480).
