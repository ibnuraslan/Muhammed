# StanleyCup v007b: fixes for the v008 hold (director, Nov 14 14:38)

Built on v007 (the approved acting pass). Same 1530-frame timeline at 60 fps, so the director's VO warp (v007 to v008) applies unchanged.
Story-beat frames unchanged: 1, 139, 271, 391, 607, 973, 1285, 1417 (`beats.json`).
v008 times converted to v007 frames with the bullet-key map: 12.0 s = f758, 13.5 s = f838, 15.25 s = f933, 16 s = f973,
19 s = f1265, 20 s = f1338, 21 s = f1404, 22 s = f1465, 23 s = f1525.

Moving preview: `review/StanleyCup_v007b_preview.mp4` (every 5th frame, 270x480, Cycles 4 samples + OpenImageDenoise, 12 fps, so it plays at real speed).
Before/after on the flagged times: `review/hold_fixes_before_after.jpg` (top: v007, bottom: v007b).

## The faults and the fixes

1. **19–21 s, end: a grey sleeve with no body, and her hand frozen open in front of her chest for 2+ s.**
   - Restaged the ending as a two-shot. After the floor bounces, the camera cranes up on his side of the table, crosses above the
     table top and settles on her side wall. From there both bodies read whole: her in three-quarter view, him half-risen and
     facing the camera, with the cup between them. It holds from f1417 (beat 8) to the end. A path check confirms the camera
     never enters the table.
   - She pulls back. After the flinch her left hand comes down into her lap, and her right hand goes to her chest, then down to
     her lap. Her torso leans back. Nothing is held still: every hand has a key at least every ~45 frames.
   - He grabs the cup handle. His right hand closes on the handle at f1385, using the library `grip_object` on a mesh copy of the
     handle (fingers close until contact, thumb on top). From f1400 he lifts the cup about 12 cm and draws it toward himself,
     turning it, while his hand stays on the handle. The cup is keyed only while it is in his hand. His torso turns toward the cup,
     so his reach is no longer at full extension (the IK target was 15 cm out of reach before).
   - Her grab of the handle and his reach for her forearm are removed, so the two characters' hands never meet.
2. **15.25–16 s: his arm locked straight across the table.** The reach target moved closer to his body, with the elbow pole
   out and down. The angle at the elbow between the upper arm and the forearm is now 84–101° through f600–1298. In v007 it sat
   at the 135° IK limit, the straightest this rig allows. He still reaches toward her and the cup, but with a soft, bent arm.
3. **12 s: face cut off.** The f748/f772 framings now aim at her real head bone (they used a fixed estimate before). At f772 the
   aim moves from the cup to her head. A new f783 framing puts the cup in the foreground with her face behind it, so the
   move from her face to the lid passes a shirt-only view for only ~6 frames of a fast pan (0.1 s).
   A new f806 framing rises off the lid onto his face, for the same reason.
   **13.5 s: his arm filling the frame.** The f815/f842 framings moved to his left side, so his reaching (right) arm is on the far
   side of his body. The top-down lid framing (f795) moved to the far side of the cup, so his nearer reaching hand stays out of the
   lens.

## Same fault elsewhere (found while watching the preview, also fixed)
- **f861–876 (v008 ~14 s):** his sleeve reached into a cup insert from the frame edge. f885 is now an over-the-shoulder shot from
  behind her right shoulder: the cup, his reaching arm and his face are in one frame.
- **f1121–1150 (v008 ~17.5 s):** after the impact, his arm crossed the frame toward her with no body. f1160/f1220 are now the
  two-shot from her side wall, with both reactions in frame.
- Remaining moments without a face are fast camera moves lasting 1–2 preview frames (f456, f536, f791, f1111–1131). Also left:
  the v007 condensation macro (f686–716), which is unchanged.

## Hands and wrists (found while watching, also fixed)
- **Wrist flips.** The arm IK has no forearm twist, so the wrist takes 50–180° of pronation. The wrist Limit Rotation clamped twist
  at ±30° in XYZ order. That gimbal-flipped the hand 180° in a single frame: `pop.py` found 45 single-frame hand pops in v007.
  The wrist limit now runs in YXZ order: the gimbal sits on flexion, which is clamped to ±60°, and twist is free. Hand keys that
  asked for more than 110° of twist are turned back about the forearm axis; table rests and the handle grip are left as placed.
  Pops: 3 left, each a 3.6–3.9 cm fingertip move on his braced left hand.
- **Resting hands in the cloth.** The fingertips of his left hand were 4–6 cm below the cloth, and so were hers between sparse keys.
  The fix adds a lift-to-contact step after `place_hand`, makes the fingers follow the forearm direction, and adds denser rest keys
  while the spine leans. `audit.py` fingers: deepest is now 9 mm (8 frames at step 3), down from 6 cm.
- Dust motes that drifted through a head are hidden. That was the v007 limb_check PROPHEAD flag: DustMote.087 inside her head at f1486–1526.

## Checks on the final build (step in brackets)
| Tool | v007 | v007b |
|---|---|---|
| `pipeline/limb_check.py` (5) | ARMBODY 306, PROPHEAD 9 | **ARMBODY 373, PROPHEAD 0, ARMBACK 0** (see below) |
| `pipeline/qa_check.py` (6, beats.json) | EMPTY 148, FILL 32, INSIDE 15, BACKHEAD 1 | **EMPTY 135, FILL 30, INSIDE 13, BACKHEAD 0**; HOVER/CLAW/FACEPRESS 0 |
| `pipeline/clip_scan.py` (6) | 2 bad frames (889, 907) | **0** |
| `scripts/hand_audit.py` (3) | 0 | **0** |
| `scripts/audit.py` (3) | fingers in cloth to −6 cm | feet 0, seat 0, bullet 0, fingers ≤ 9 mm; camera: f283 GypChunk (debris passing the lens in the wall cavity, as v007) |

**limb_check ARMBODY 373.** Every flag is the shoulder joint itself. The count went up from v007 only because more frames now show
both people. I re-ran the same test and logged which bone points are inside: in every flag, the only inside points are k = 0–2 on `upperarm01`, i.e. within 4 cm of the joint centre. That part of the
deltoid is skinned to `shoulder01`/`clavicle`, which limb_check classes as torso. No point on `upperarm02`, the forearm or the
wrist is inside the character's own torso or the other character, in any frame. These are not visible faults, so I left them.
Per-point log: `review/limb_points_v007b.json`. The arms that were really wrong (the straight reach, the detached sleeve) are fixed above.

**qa_check: new flags vs v007.** One new frame: EMPTY at f985, the impact macro of the bullet hitting the cup. In v007 his hand sat
behind the cup there; it has moved back (fault 2). Every other EMPTY/FILL/INSIDE flag is one of v007's bullet-flight and
wall-cavity shots. The end two-shot (f1417–1530) has no flags.
