# Acting fix: films 04–10 (client, Nov 12)

The client reviewed the films and rejected the acting: **"most of these are nonsense... very weird actions, not real actions. Everything has a problem."** Clipping-free is not enough. Every beat must look like what a real person physically does.

**Update 18:40 UTC:** the client stopped the 01–03 renders because of mistakes. Films **01 EarInArm, 02 MonkeyHeadTransplant and 03 LegoInNose now get the same full acting fix**, following every rule in this brief.

## What each chat does (04–10)
1. **Review every beat yourself.**
   - Render a half-second sheet of your approved final (270×480, 8 samples), every 30 frames from frame 1 to the end.
   - For each frame, ask: *would a real person move like this, here, for this reason?*
   - Write the list of every problem with its frames to `review/ACTING_notes.md`. List them all, not just the worst one.
2. **Fix every item.** Work in your own scripts on your approved version's timeline.
   - Keep every story-beat frame where it is. The voiceover sync uses those frames, and the director re-syncs your new version to the client's voiceover.
   - Do not add the VO yourself.
3. **Re-check.**
   - Render the same half-second sheet of the new version.
   - Render a 270×480 close-up of every hand contact.
   - Run `blender/pipeline/clip_scan.py` (on the director branch `claude/beautiful-ptolemy-c5vrcq`) and get 0 bad ranges on camera.
4. **Package the next version** (vNNN+1, under 95 MB, plain git) with before and after sheets in `review/`. Push it, and message the director with the path, the commit, and the list of fixes.

## The bar (reject any frame that breaks one)
- **Weight and contact:** feet on the floor or pile (no floating, no sliding), hands on what they touch, sitting on something.
- **No frozen poses:** no deep squat held for no reason, and no head hanging down for no reason. People breathe, shift and look at things.
- **Plausible transitions:** going from lying to sitting to kneeling to standing passes through real in-betweens. No snaps, no root spins, no limbs passing through each other.
- **Props never move by themselves.** A hand moves them, with visible contact. Example: a mask comes off because a hand pulls it.
- **Physics reads true:** falls land on the body's back, side or hands. Legs don't stay up a wall or in the air after landing.
- **Camera:**
  - never inside a body, wall or prop
  - no frame filled by a wall, hair, the top of a head or a shoe sole
  - the face of the character who is acting is readable on every story beat
- **Hands:** all rules in `blender/STYLE_ANIMATED.md` still apply (no backward joints, nothing through shirts, bodies or each other, real grips).

## Director notes per film
### 09 DonationBin (worst, start now)
The sheet of v004 retimed (as v005) is in `acting_review/09_DonationBin_v005_sheet.jpg`. Frame numbers on the sheet are v005 (VO) frames. Old (v004) frames are given here in brackets.

| v005 time | What is wrong |
|---|---|
| 2 s [~155–175] | The shover's hands are on her backside, and his head blocks the view. Push her **upper back / shoulder blades**. |
| 3 s [~205–215] | A shoe sole fills the frame as she goes through the chute. Move the camera back and up. |
| 4–6 s [~240–360] | Somersault ends on her back with **legs up the wall / in the air** for seconds. Land her on her back with **knees bent and feet down on the clothes** within ~0.3 s, then a dazed lie. |
| 7 s [~420–460] | Deep squat facing away, hands on the floor. Sit her up properly from lying, seated on the clothes, then turn to look at the flap. |
| 11 s [~650] | Crouch-to-stand transition is a snap. Use kneel, then one foot planted, then stand. |
| 14 s [~955] | **Camera passes through the bin wall / her body** (blue blur). Re-enter the bin while the x-ray walls are still see-through (before ~905). |
| 15–18 s [~990–1100] | Hunched at the left wall. The camera sees the top of her head or the wall only. Stand her **upright**, hands sliding on the smooth wall, looking up. The camera is at face height in a corner. |
| 19 s [~1180–1250] | Jump at the back wall: OK as an idea, but the camera only shows hair or wall. |
| 22 s [~1320–1340] | Her face is cut, the frame is mostly her shoulder. |
| 26–29 s [~1500–1840] | "Three days curled up": **her face is pressed into the wall**, the hands are claws, and the legs splay over the camera. Lay her curled on her side in the **middle** of the clothes, head on her arm, face toward camera, hands relaxed. |
| Rescue [~1910–2090] | She snaps back to the same squat. Instead: lifts her head at the knock, pushes up on one arm, sits. |

`acting_review/09_DonationBin_director_draft_fix.py` is an **untested** director draft of this re-stage:
- It runs on v004.
- It re-keys the woman from 158 to 2094 with the same `Body.pose` helpers as `03_animate.py`.
- It re-keys the shover's hands on her back.
- It re-keys the camera inside the bin to the high corners.

Use it as a starting point if it helps. Verify everything in renders. Feet yaw, hand normals and IK reach are not checked.

### 05 SurgeonBrandsLivers
- Mask-off beat (v006 ~451–541): a single hand reaches up **in front of** the face, takes the mask and pulls it down. The elbow stays down and in front, the other arm stays low. No arm passes through or behind the head, and the mask never drops on its own.
- Then review every other beat to the bar above.

### 04 StanleyCup, 06 PrisonKeyCake, 07 ShoeBomber, 08 BeethovenDeaf, 10 BellyFat
- No director list yet. Do the full review in step 1. The client says every film has problems, so expect a real list, not "none".

## Self-check before you submit (mandatory, Nov 12 14:40 UTC)
Most first submissions came back with the same faults, so a chat may only submit when every box below is true. Look at the images yourself. The numeric audits do not catch these:
1. **Hands touch what they hold, every time.** In every hand close-up, the fingers are visibly wrapped on or pressed against the object, with no gap. No fist floating beside a nozzle, a box, a gavel, a stamp or a paper.
2. **No claws.** No stiff, bent, splayed fingers in the air, on a thigh or on a face. Idle hands are relaxed. Alarm hands are open and relaxed, or on the head.
3. **No face pushed into anything.** No palm pressed into a nose or eye, and no forehead against an object.
4. **No empty or unreadable frames.** No cell of the half-second sheet may be:
   - a bare wall, sky, floor or prop surface
   - a blur
   - black
   - hair or the back of the head on a story beat
5. **Close-ups show hands.** Every close-up is aimed at the hand and lit. Replace any close-up that shows feet, a blur or black.
6. **Use `blender/pipeline/hand_poses.py`** once it lands on this branch (pose presets plus `grip_object`). Don't hand-set finger angles.

In your submission message, list each of the 6 points with "checked".

## Automatic QA script (mandatory, Nov 12 15:00 UTC)
`blender/pipeline/qa_check.py` checks the scene geometry for exactly the faults that keep getting rejected. Run it on your packed file:
```
blender -b YourFilm_vNNN_60fps.blend --python blender/pipeline/qa_check.py -- review/qa_vNNN.json 6 beats.json
```
It flags:
- **EMPTY:** no character in view, or walls or props fill the frame while characters cover under 15 %.
- **FILL:** one prop or surface fills the frame, or hair or the top of a head covers over 25 %.
- **INSIDE:** the camera is inside geometry.
- **BACKHEAD:** the back of a head on a story beat.
- **HOVER:** a hand within 12 cm of a prop with no fingertip touching it.
- **CLAW:** fingers curled in the air touching nothing, or bent with a straight base joint.
- **FACEPRESS:** a hand on the face.
- **ROLL** (added 18:25 UTC): the horizon is tilted more than about 20°. This usually comes from a Damped Track aim. Use Track To with world up, or list a deliberate dutch angle.
- **CAMJUMP** (added 17:25 UTC): a hard cut, meaning a camera switch, or a teleport over 0.25 m in one frame (well above the neighbouring frames' speed), or a turn over 60° in one frame. A whip pan of up to 60° per frame is fine. The film is **one continuous camera**. Join framings with real eased moves (about 40 frames) through free space. Only a fully covered wipe (black or cloud frame) may hide a jump, and you list it.

Fix every flag. A flag may stay only if it is intended: a wide establishing shot, a fist that is meant, or contact you meant. List each one that stays, with its reason, in ACTING_notes.md. Attach the JSON with your submission. Submissions without it come straight back.
