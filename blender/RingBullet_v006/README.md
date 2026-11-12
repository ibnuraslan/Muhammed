# RingBullet v006: farm package (acting pass)

| | |
|---|---|
| File | `RingBullet_v006_60fps.blend` (58 MB, packed, compressed; a normal git file, no LFS) |
| Format | 1080×1920, 60 fps, frames 1–1410 (23.5 s), Cycles CPU, 48 samples + OIDN, motion blur 0.5 |
| Camera | one camera (`Cam`) on one continuous move, no cuts, no markers |
| Output | `//render/RingBullet_v006_####.png` |
| Beats | `beats.json` (9 beats, start frames at the brief's target times) |
| Sources | `../RingBullet_v001/scripts/` (rebuild steps in `../RingBullet_v001/README.md`) |

## What changed from v005 (client acting review, Nov 12)
This is an acting pass on the approved v005. Every story-beat frame is unchanged (`beats.json` is identical), so the director can re-sync to the VO as before. The look, set and props are unchanged.

The full list of problems and fixes is in `../RingBullet_v001/review/ACTING_notes.md`. Before and after sheets: `../RingBullet_v001/review/v005_before_0p5s.jpg` and `v006_after_0p5s.jpg`. Hand close-ups: `v006_hand_closeups.jpg`.

1. **Wince (15 s):** the hit hand jerks back and down to the chest, curling, instead of pressing into his nose. The other hand comes up open beside it.
2. **Neck graze (16.5–17.5 s):** the right hand cups the side of the neck below the ear, from outside the collar. It arrives and leaves along a side path.
3. **Lowering the hand (18 s):** the hand comes off the neck down and forward, with no float-up beside the ear and the fingers leading outward.
4. **Walk-out:** the arm swing sits closer to the body (no held-out arms).
5. **Before the shot:** a small startle.
6. **Camera:**
   - the bullet-ride peel-off swings to his face (no blank wall frame at 3 s)
   - the macro bullet lock starts earlier (the bullet is in frame at 6.5 s)
   - the 15 s framing is lowered (no head-top fill)
   - the 18.5–19.5 s orbit is wider (no blurred-hand fill, and his face reads)

**Round 2** (director review of 40b7da8):
- shield hand about 16 cm in front of the face with the fingers together
- relaxed hands, the wince hand resting on his chest
- neck-cup contact
- focus follows to his face at 2.5–3 s
- re-aimed close-ups

Details are in `ACTING_notes.md`.

Checks:
- `pipeline/clip_scan.py`: **0 bad ranges**
- hand audit (every 2 frames): **0**
- contact audit: **0**

## Earlier: what changed from v004 (hands pass)
Only a hands pass. The look, camera, timing and everything else are the same as the approved v004, which is kept unchanged.
1. **Limit Rotation constraints (local space)** on every finger, thumb and wrist bone of all three characters (owner, robber, officer):
   - fingers: 0–90° curl, no backward bend, ±10° spread, ±5° twist
   - thumbs: a natural cone
   - wrists: ±70° flex, ±45° side

   The keyed finger poses are clamped to the same ranges, with a relaxed curl of at least 4°, so no flat or hyper-extended fingers.
2. **Re-keyed hands:**
   - raised hands spaced apart and more upright (no hand-through-hand)
   - the right hand cups the side of the neck from outside the collar, with an arc key leaving the neck
   - the right hand lowered clear of the jacket
   - the left hand's rise path in front of the lapel
   - the walk arm swing clear of the jacket and trousers, with an outward key while turning into the walk
3. **Hand audit** (`../RingBullet_v001/scripts/hand_audit.py`, BVH every 2 frames). It checks:
   - hand vs hand
   - hand vs own torso, neck and head skin
   - fingers vs own clothes
   - hand vs other characters

   **Result: 0 flagged frames** (`../RingBullet_v001/review/hand_audit_v005.txt`). It excludes only the shirt and jacket cuff resting on the back of the hand and on the thumb base, which is normal sleeve contact. The general contact audit also reports 0.
4. **Close-ups of every hand action:** `../RingBullet_v001/review/v005_hand_closeups.jpg` (gun grip, hands up, impact, wince, ring, neck grab, bandage, plaster, walk).

## Earlier: what changed from v003 (look change)
v004 has the same animation, camera path and beats as v003. Only the look changed, following `blender/STYLE_ANIMATED.md`: bright, clean 3D animation, never mistakable for live action. v003 is kept unchanged.

1. `RB_LOOK=anim` rebuild of the FX and camera stage (`scripts/03b_fx_camera.py`):
   - no handheld camera shake; short stylised bursts remain only on the muzzle flash, impact, split, wall hit and police flare
   - f-stop at least 8 outside true macro framings
   - no sweat sheen
2. `pipeline/anim_look.py`:
   - AgX Punchy, motion blur off
   - +25 % saturation, bump/normal ×0.35, roughness at least 0.35
   - volume density halved, lights ×1.25
   - sky-gradient camera background
3. `scripts/04_anim_fix.py` (hand fixes):
   - smooth CG skin with no pores
   - lighter, cleaner wood, floor and ceiling
   - the window backdrop recoloured to the sky-blue gradient (cyan to near-white)
   - high-key relight (key ×2.4, fill ×3, sconce ×2, and so on), exposure +0.6
   - the injuries are now small, clean, stylised red marks
   - the bullet and fragments are clean, polished metal
   - the bullet hitting the ring reads as a bright spark burst, with no wound

## Story beats as built
| # | Frame | Line | On screen |
|---|---|---|---|
| 1 | 1 | The robber fired the gun… | Over the robber's shoulder (he's only seen from behind), then the muzzle flash and smoke. The camera rides the bullet in slow motion, orbiting it. |
| 2 | 163 | …threw his hands up… | The camera peels off to the reverse as his hands snap up, the backs of his hands out and the gold ring facing the bullet, in a look of terror. |
| 3 | 409 | …instead of going through his skull | Macro from behind the bullet, with a rack focus from the bullet to the ring. |
| 4 | 541 | …hit his wedding ring | A rim glint, then impact with sparks, a flash, the hand jolting, the lamp flickering and a camera shake. |
| 5 | 661 | …split into two pieces | The bullet squashes, the ring dents and two fragments fly apart, with an orbit macro. |
| 6 | 865 | One piece lodged in his finger | Fragment A lodges in the middle finger, leaving a small dark nick with no blood. He winces with eyes squeezed and mouth open. |
| 7 | 979 | …the other went into his neck | A whip-pan with fragment B. It grazes his neck, leaving a small mark, and his hand flies to his neck. The fragment then hits the bookshelf behind him in a puff of dust and splinters. |
| 8 | 1075 | …minor injuries and a dented ring | He looks at the dented ring in disbelief (slow blink, brows up) as the camera orbits close and police light washes in. |
| 9 | 1249 | …walked away okay | Bandage and plaster on. He walks out (IK walk, planted feet) toward a red/blue strobe and an officer beckoning at the door, as the camera pushes into the doorway. |

## Voiceover
No VO mp3 has been supplied yet, so this package contains no VO strip. To retime when it arrives:
1. Get the word timestamps with `pipeline/transcribe.py`.
2. Build an anchors file from `beats.json` (old frame → the second the beat's first word is spoken).
3. Run `blender -b RingBullet_v006_60fps.blend --python ../pipeline/retime_to_vo.py -- anchors.json vo.mp3 RingBullet_v006_60fps.blend`.

The world-time slow-motion curve (`TimeCtl["wt"]`) is keyframed, so it warps with everything else.

## Known issues
- In some macro frames (about 8–9 s and 13 s), skin fills most of the frame. It shows pore and normal detail, and the director has accepted these as macro.
- Around 3.0 s there's about one soft, dark frame as the camera peels off the bullet to the reverse.
- The bandaged hand mostly turns away from camera during the walk. The bandage reads at 20.8–21.2 s.
- Facial acting uses MPFB face bones (jaw, brows, lids, mouth corners) and no shape keys. It's readable, but not film-grade.
- The officer is a plain MPFB figure in a navy work uniform with no markings, and is only seen as a backlit figure through the door.
- The audit (`../RingBullet_v001/review/audit_C.txt`) reports 0 flags. It checks:
  - feet hover and sink
  - ring and body penetration depth
  - body against props
  - bandage and plaster gap
  - camera inside geometry
  - gun aimed at camera while in frame
  - robber face in view
