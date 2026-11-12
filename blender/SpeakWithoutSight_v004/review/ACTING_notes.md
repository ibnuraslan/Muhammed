# SpeakWithoutSight: acting review of v002 (final), for v003

Source: `before_halfsec_*.jpg`, the half-second sheet of v002 (270×480, 8 samples, every 30 frames, 1–1980). Times are film seconds; frames = 1 + t·60. Story-beat frames (1, 163, 397, 595, 697, 895, 1063, 1261, 1453, 1723, 1843) stay where they are.

| # | Time (frames) | Problem in v002 | Fix in v003 |
|---|---|---|---|
| 1 | 14.0–16.5 s (840–990), **beat 6 at 14.9 s** | The girl, who is the actor on "how strong or soft it was", hangs her head while leaning in. The camera sees the top of her hair, so her reaction to loud and soft pulses can't be read. | Her head comes up and turns towards the teacher's voice from 8.5 s while her hand is on the throat. Her brows and mouth react (keys already in). The 14.9–16 s framings sit at her face height. |
| 2 | 8.5–11.5 s, 17–23 s (510–690, 1020–1380) | The girl's fingers on the teacher's throat and lips are splayed apart like a claw. Real Tadoma fingers are together, slightly curved and soft. | Fingers together (no spread), a gentle 14–18° curl, and the thumb relaxed alongside. |
| 3 | 8.0 s (481) | The teacher's outstretched sleeve fills the lower half of the frame while she guides the hand. | The framing moves up and to the girl's side, so both faces and the guided hand are in view. |
| 4 | 26.0–26.5 s (1561–1591), beat 9 | The girl practises the shapes on her own face, but the camera sits behind and above her head and sees hair and the teacher's face. | The framing is at the front-left of the girl at mouth height, so her hand on her own lips reads. |
| 5 | 29.5–30.2 s (1771–1813) | The time-lapse orbit swings behind the teacher; her back fills the frame just before the "finally able to speak" beat. | The orbit stays on the girl's open side (65°→15°), with a waypoint in front before the push-in to the girl. |
| 6 | 10–17 s, 22–28 s | The teacher holds a frozen kneel. Only her head and mouth move, and nothing breathes. | Breathing and weight shift on her spine every 1 s (±1.5° flex, ±2° twist), plus small nods on her stressed words. |
| 7 | 2–6 s (120–360) | The girl is very still. That's motivated (she's trapped and unaware), but her chest doesn't move. | A visible breathing cycle (±2°) and a slow sway. Her head stays lowered because the story asks for it: she's withdrawn. |
| 8 | 2–33 s | The dog stands on the same spot with only its head and tail moving after its bark. | It breathes, turns its head to whoever is talking, and lies down at 12 s (front legs folding first), then lifts its head at the first word. |
| 9 | 6.8–7.3 s (408–440) | The teacher's kneel-down: the back foot lands far behind, so it reads as a lunge. | A shorter step back with the knee lowering under the hip, and a two-stage kneel (one knee, then both). |
| 10 | 30.5–31.0 s | The girl's raised left hand sits close to the camera. | The camera is 15 cm further back (clearance). |

The hands rules in `STYLE_ANIMATED.md` still apply: the Limit Rotation constraints and the hand audit stay.

## Status at submission (16:22 UTC)
- clip_scan (step 6, 2 cm): **1 bad scan frame, 1057 (17.6 s)**. Every other range is clean (it was 7–21 ranges before).
- Throat/x-ray beat (690–1063): the pad now stays on the skin, with de-intersection allowed up to 1.3 cm. Earlier pushes had floated the hand off the throat.
- Dog (item 8): it walks off to DOG_END2 (690–780) instead of lying down.
- Kneel (item 9): only partly done. The teacher kneels closer; her hands rest on the armrest and the girl's knee instead of sinking into her own thighs.
- qa_check (c6240b2): BACKHEAD 2, INSIDE 101, FILL 141, EMPTY 7, FACEPRESS 4, and 0 HOVER and 0 CLAW. Most INSIDE/FILL hits are the close two-shot framing inside the furnished room. Not addressed in this pass.
- hand_closeups.jpg was rendered from the 15:40 build. The throat contact changed after it (see after_a/b).

# v004 (director rejection of v003, 16:22)
Checks run on the final build:
- clip_scan (official, 3cfc53c, skin only): **BAD_RANGES []**
- qa_check (771d2da): BACKHEAD 0, FACEPRESS 0, HOVER 0, CLAW 0, EMPTY 0, CAMJUMP 0, ROLL 0. Still flagged: INSIDE 33 and FILL (hair) 114; see the exceptions below.

## Fixes
1. **Throat pad.** The girl's fingertip is on the teacher's larynx skin for the whole beat (530–1063): 8.3–9 cm from the neck centre, which is the skin surface. The pad uses `apply_pose(..., "shield")` from hand_poses.py: flat fingers, thumb tucked beside the index. I chose shield over flat_palm because flat_palm's thumb sticks into the neck. `place_hand` keys IK_hand in a frame that doesn't match this rig's controls (it left the hand 25 cm short), so placement uses the reach-checked `g_hand_on`.
2. **Root cause of the v003 floating hand.** My de-intersect pass treated the hidden MPFB helper shells as skin. The pass now ignores helper and joint polygons, which is the same fix as the director's clip_scan 3cfc53c.
3. **FACEPRESS 4 → 0.**
   - The girl's left hand on her own throat now points sideways and sits 2 cm lower, so her fingertips stay off her jaw.
   - Her right hand's reach arcs out toward the teacher, clear of her own face (frame 511).
4. **BACKHEAD 2 → 0.**
   - Frame 1: the wide shot moved to the side the mother faces.
   - Frame 1453: the camera is on the girl's right, so the girl's face shows and the teacher is in three-quarter profile.
5. **X-ray, 12.5–14.5 s.** Shots 760 and 830 are pulled back to 30–32 mm. The teacher's throat porthole and the girl's x-ray hand and forearm now read in one frame.
6. **Clip fixes.**
   - 1057: the girl's own-body pass is extended.
   - 1333/1339: her fingers on the teacher's lips are de-intersected with an escape direction away from the teacher's head.
   - 1621: densified keys.
   - 1633–1645: the teacher's knee-rest hand has densified keys.
   - 1909–1921: a teacher hand path is added in front of her own chest, between the gasp and the heart.
7. **EMPTY / INSIDE.** DarkBubble (always hidden from render) and ExplainerDome (outside 698–1102) are now also hidden in the viewport, so QA ray casts no longer hit them.
8. **Girl face close-ups** are shot from just below eye level.
9. **Hand close-ups** were re-rendered from this final build, and the camera now rotates around each hand to find a clear line of sight.

## Intended exceptions
- **INSIDE 33, frames 721–1093.** These are all inside ExplainerDome, the blue x-ray backdrop sphere that is supposed to surround the pair for the explainer beat. The walls stay outside it and it has no visible edge.
- **FILL "hair" (25–45%), 114 frames.** These are face close-ups of the girl (black bob) and the teacher. The hair framing the face covers more than 25% of the ray grid, and the frames are faces, not the tops of heads. Not fixed in this round.

## Still open
- 22.0–23.0 s: the macro on the girl's fingers at the teacher's nose is soft from depth of field and very tight.
- In close-ups 06 (f1215, nose) and 07 (f1350, lips), the girl's own hair is still in front of the hand.
