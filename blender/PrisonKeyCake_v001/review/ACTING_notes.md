# PrisonKeyCake: acting review of the approved v005 (half-second sheet `review/before_v005_halfsec.jpg`)

Frames are v005 frames (the same as the beat frames in `beats.json`; story-beat frames are unchanged in v007).

| # | Time | Frames | Problem | Fix in v007 |
|---|---|---|---|---|
| 1 | 0.0 s (beat 1) | 1–30 | The beat opens on his back, so his face isn't readable | First framings moved to the window side: his face over the table as he glances at the door |
| 2 | 0.5–1.0 s | 30–70 | The frame is filled by his shirt, because the key macro sits too close to his chest | Camera clearance pass (see 13) plus the key macro pulled back |
| 3 | 2.5 s | ~151 | The frame is filled by his crotch: the camera swoops through his torso between the face and press framings | The path is routed above and in front of him |
| 4 | 3.0–4.5 s | 181–271 | A pressing hand fills the frame (a blob at 4.5 s) | Wider macro: the key, both fingertip hands and the tin all in frame |
| 5 | 6.5 s | ~391 | The visitor's coat and leg fill the frame at the pocket | Pocket framing pulled back: hip, hand and tin in frame |
| 6 | 9.5 s | ~571 | The ally's back fills the frame | Framing moved to the front-right of the pour |
| 7 | 15.0 s | ~901 | His back fills the frame on the dive to the lock | Clearance pass |
| 8 | 16.5–17.5 s | 991–1051 | His shirt and shoulder fill the frame (slap and slump) | Clearance pass |
| 9 | 19.0–19.5 s | 1141–1171 | His arm, then the top of his head, fill the frame | Clearance pass; he looks up at the window, face readable |
| 10 | 20.5–21.0 s | 1231–1261 | Frozen hunch on the stool, head hanging | Waiting has life: he breathes, rubs his hands, looks up at the window and the candle, shifts weight |
| 11 | 23.0–24.5 s | 1381–1471 | His shirt, his back and the back of his head fill the frame | Clearance pass |
| 12 | 28.0 s (beat 10 start) | 1681 | The beat starts on his back | Camera ahead in the yard looking back at his face as he steps out, then crane up over him |
| 13 | everywhere | — | The camera passes within ~0.2 m of bodies | Per-frame clearance: the camera is pushed out to at least 0.38 m from every body, head and leg bone (0.22 m from hands for macros), smoothed over ±12 frames |
| 14 | 5.6, 6.4–7.1 s | 337–427 | clip_scan: the visitor's hand goes into his hip at the coat pocket | Pocket target moved 4 cm out |
| 15 | 20.8–21.1 s | 1249–1267 | clip_scan: hands sunk into the thighs on the stool | Hands rest on top of the thighs, palms down |
| 16 | 24.0–25.0 s | 1441–1501 | clip_scan: the sleeping guard's hands are inside his thighs | Hands rest on top of the thighs |
| 17 | 17.3–17.7, 25.6–26.2 s | 1039–1063, 1537–1573 | clip_scan: walking hands brush the thighs | The arm swing hangs 3.5 cm wider |
| 18 | 19.4, 21.7, 23.0–23.3 s | 1165, 1303, 1381–1399 | clip_scan: the pocket, the cake and the step to the door | Re-checked after the fixes (see the after scan) |

## qa_check.py (c6240b2) flags left in v007, with reasons
- EMPTY, 97 sampled frames: all are deliberate hand/prop macros. The hands and the prop fill the frame and the character's body is under 15%. Ranges:
  - 307–355: the visitor's hand and the mould at the window;
  - 547–739: the pour, casting and mould top;
  - 769–781: the cake;
  - 865–907: key into the lock;
  - 961: the jam;
  - 1081–1093 and 1171–1225: the second press and the window tin;
  - 1261–1303: the candle and the knife;
  - 1411–1441: the lock turn and door push;
  - 1483–1495: the corridor gates;
  - 1681–1735: the crane over the wall.
  The close-ups sheet shows the hands in contact in each of these.
- FILL 331 (table) and 337 (wall): the move from the press to the window. These are not intended and were not fixed for the 16:20 deadline.
- BACKHEAD:
  - 511 (beat 4): the nearest character is the guard; the acting character, the ally, is facing the camera at the crucible.
  - 367 (beat 3, visitor) and 1057 (beat 7, prisoner): not intended and not fixed for the deadline.
- HOVER, CLAW, FACEPRESS and INSIDE: 0.

## v007b: props in hand (PROPMOVE / ATTACH, qa_check e7b25f7)
Cause: the v005 wrist rotation limits clamp the hand's orientation, so the fingers pointed away from the props they held (10–30 cm gap).
Fix (scripts/03e_attach.py, the last step of the animation build):
- Every carried prop is re-keyed from the hand's actual grasp point (thumb tip, index and middle finger), so it sits in the fingers on every carried frame. The interior gap is now 0 for:
  - Key_Master, Key_Copy1 and Key_Copy2;
  - WaxMold (visitor and prisoner), ParcelBox_Lid, Knife_Blade and Crucible.
- Keys in the lock and the key pressed into the wax are not moved; the hand is on them there.
- The mould on the sill is hidden at 1234, before the outside hand takes it.
- President_Glasses moved onto the nose: median gap 1.0 cm (was 1.9).
Intended PROPMOVE: Spark* (casting sparks), Crumb* (falling cake crumbs), Pigeon* (birds in flight), CrowdHat* (thrown in the celebration), Candle_Flame/Candle_Wick (flame flicker).
Intended ATTACH: CrowdHat* (thrown hats).
Not intended and not fixed for the deadline:
- Crucible: 10 sampled frames, 499–643. The fingers are on the shank but more than 3 cm from its bounding box at those samples.
- ParcelBox_Lid and Cake1 at 823–847: they ride inside or on the carried box, with the hands on the box, not on them.
- Key_Master at 145 and 1117: the wax-press phases, where the key is pressed into the wax and not re-keyed.

## v007c: the director's moving-preview review of v009 (2026-11-14)
Synced times are mapped back to v007 frames through the camera keys of v009.
1. Eyes looked like black holes: MPFB's procedural EnhancedEye (blended cornea) rendered black. Every character now has an opaque textured eye (MPFB grey_eye.png) with a clear coat (scripts/03f_eyes.py).
2. Crucible, 575–624: the ally now stands at the far end of the crucible's long handle, holding it with both hands, upright, facing the pot. His head stays at least 0.57 m from the crucible.
3. Key at the chest, 56–75: the key is held well in front of the shirt (K_HOLD moved forward 12 cm), and the camera frames the hand and the key.
4. Arm against the wall, about 1025: the left arm hangs during the forehead lean. The lean was eased so his head stops at the wall (it reached x 2.12, through the wall at x 2.0).
5. Back of a man, empty corridor, top of a head (about 830, 854, 1369–1402):
   - the hand-off is shot from the side;
   - the whip leaves through the tunnel and enters through the window gap;
   - beat 6 and the jam are shot from the door and lock side;
   - the walk to the door is framed from above and in front.
6. limb_check (9a0a692), with my fixes:
   - Crowd arms went through their torsos; they now cheer with the body, arms down.
   - The ally holds the pour clear of his body and leans less at the mould and the cake.
   - The visitor holds the mould to his side.
   - The prisoner's key holds are further out.
   - The glasses moved to 1.35 cm off the face, no longer inside it.
   - ARMBACK is 0.
   - Remaining flags:
     - ARMBODY with 3 or more points: the ally at 785–853 (box carry), and the prisoner at 1173, 1181, 1213, 1325, 1373, 1377 and 1457, each 3–7 points on single frames.
     - PROPHEAD at 1205: the mould passing his head.
   - Flags with 2 points are the shoulder joint itself: the same 2 points flag in the rest pose (tested).
Moving preview: review/preview_v007c_every5th.mp4 (every 5th frame, 270x480, Cycles 4 samples and denoise), watched frame by frame.
Still visible in the preview: beat 6 (871) shows him at the door from behind and the right. The whip into the cell passes one dark tunnel frame (856). The crane has one empty-yard frame (1736).

## v007d: rule 3 (camera never passes or brushes a body or a wall). Camera only; animation unchanged from v007c.
- 853–858: the whip runs down the centre of the tunnel (the only way out of the shop), with the view turned to the bright yard first. A fill light (L_TunnelFill) lights the passage. Then a straight move across the open yard to the cell window.
- 864–946: the camera comes in through the window gap and goes straight to the lock side. Beat 6 (871) shows his face. No pass over his head; the camera stays on the lock side through the jam.
- 1376–1440: the camera holds on the north side and only pans as he goes to the door and turns the key. The lock close-up is gone; the hand is seen from a distance.
- 1736: the crane stays on him one key longer, then pans across the sky to the government building.
- Closest approach of the camera to any head or torso: at least 0.50 m everywhere except 187 (a stationary close-up of the press, 0.36 m) and 1460–1461 (following him out through the doorway, 0.32 m; unchanged).

## v007e: director review of v007d (14 items). Simplify rule: steady framings and hard cuts instead of risky moves.
1-2. Wax press (f76-330): one steady 3/4 shot of his face and both hands. Only the right hand presses the key; the left rests flat on the table (the second press at 1122 is the same).
3. 511-541: watches the visitor reach the gate from inside the yard, then cuts into the shop. No gate crosses the lens.
4. Mould top: wider, steady shot; the ally stands closer so his elbows bend.
5. Cake: his free hand hangs at his side; no hovering claw.
6. The cake and lid shot is wider, from the front and right, so his face shows under the hat.
7. The whip is replaced by a hard cut (853) from the hand-off into the night cell, lock side, his face.
8. Jam: steady medium from the lock side; no hand fills the frame.
9. The lean is now a hand on the wall with the head bowed about 11 cm off it. His head stops at x 1.80; the wall is at x 2.0.
10. 1040-1080: the camera arcs behind him on the south and west sides, never past him, and ends on his face at the table.
11. Window lift and stool wait are now steady medium shots. No candle macro, no empty wall.
12-13. Knife and key-out are framed from the table side. At 1463 a cut goes from the door to ahead of him in the corridor.
14. At 1646 a cut goes to a fixed camera in the yard, off his path, which then cranes up as he crosses. No door edge, no tilted empty walls.
Cuts at 541, 853, 1463 and 1646 are hard cuts. No smoothing across them; constant keys before each cut.
Checks:
- Camera audit: 0 bad frames.
- Camera is at least 0.49 m from every head and torso on every frame.
- Moving preview watched frame by frame (review/preview_v007e_every5th.mp4).
