# NukedWell acting review (v003 → v004)

**Method.**
- I rendered a half-second sheet of the approved v003 (`ACTING_before_v003_halfsec.jpg`).
- I checked every frame against `briefs/ACTING_FIX_04-10.md`.
- I ran three automated scans:
  - `scripts/acting_scan.py`: on-screen teleports, sliding planted feet, and frozen poses held more than 1.5 s on screen.
  - The hand audit (every 2 frames).
  - `clip_scan.py`, both the director's version and `scripts/clip_scan_rootpos.py`. The second is the same scan, except that the distance to the camera is measured from the root bone. NukedWell rigs stay at the origin and move through IK targets, so the unmodified scan almost never sees them.

**Story-beat frames are unchanged:** 1, 193, 343, 541, 619, 895, 1111, 1381, 1585, 1681, 1897 (`beats.json`).

## Problems found in v003, and what v004 does

| # | v003 frames | Problem | v004 fix |
|---|---|---|---|
| 1 | 1311–1340 (21.8–22.3 s) | **A bug.** The beat 7 backward retreat (1236–1326) overlapped the beat 8 keys, which started at 1312. All six crew flickered between two places, 20–55 m apart, in a wide shot. | The retreat ends at 1290, followed by a short hold. A forward **time-lapse** (1300–1362) carries everyone to their beat 8 places, with the sun sweeping a full day in the sky. The story skips ahead to the test day. Each person then turns on the spot (1363–1367) to face the work. |
| 2 | 405 (6.7 s) | At the start of the rewind, the whole crew teleported 14–62 m to their 1963 positions, in view. | During the rewind, every person **zips backwards** along a straight line to their 1963 spot (404–535). That reads as time running back, matching the sun, the concrete and the fire. |
| 3 | 857 (14.3 s) | At dawn, the soldiers and engineers jumped 18–55 m to the hose positions. | When the gas erupts, the four soldiers **run from their 1963 spots straight to their hose positions** (597–747). The engineers walk a few metres in from where they watched the night. Nobody jumps. |
| 4 | 856–901 | The hose crews mimed holding hoses that weren't there yet; the hoses popped in at 901. | The hoses **lie flat on the sand** from beat 4 on. At 835–881 each crew **crouches, grips the hose (fingers curled) and lifts it** to the hip, then braces. When they retreat, they let go: the hands come down to their sides and the hose drops back to the sand. |
| 5 | 1211–1236 | When the hose crews let go to retreat, the hands swept straight through the torso (hand audit: 120 vertices). | Explicit let-go keys: hands to a low brace, then to the sides, before stepping back. |
| 6 | 1–343, 897–1300 | **The "radio" gesture:** a hand held to the ear with no radio in it. Miming. | Replaced everywhere with hands on hips. |
| 7 | 2041 (34.0 s) | During the cheer, SolC's raised hand went into his own head (root-bone clip scan: 119 vertices). | The "up" and "wave" hand targets moved out and forward. |
| 8 | 785 (13.1 s) | The night shielding pose put EngA's hand into his face. | The shield hand sits further forward, in front of the face. |
| 9 | 1357–1367 | At time-lapse speed the walk keyed the arm swing only every 12 frames, so the hands lagged metres behind the body. | Arms are keyed every 2 frames, like the feet. Arm swing is damped during the time-lapse zips. |
| 10 | 1581 | The crew moved to the bunker while still at the top edge of the underground frame. | The move now happens at 1587, inside the white detonation flash, where nothing is readable. |
| 11 | 1.5–4.5 s (91–271) | **Frame filled by a wall.** In the beat 1–2 section shots, the flat strata wall filled the frame and the device was small. | The camera stays about 7 m from the device all the way down the bore, so the device is the subject of every frame. The strata read behind it. |
| 12 | 23.5 s (1411) | Beat 8: the device filled the frame and the soldiers were cut off at the edge. | The framing pulls back to show the device with both soldiers' hands on it and their faces in profile. |
| 13 | 895 (beat 6, 14.9 s) | The story beat framed the hose crew from behind, so no face was readable. | It now opens on a three-quarter front angle of the front hose holder's face, then moves along the water. |

## Checks after the fixes (v004)
- `acting_scan.py`:
  - **0** sliding feet and **0** frozen poses.
  - Fast moves remain only inside the intended time-lapses (rewind 404–535, fast-forward 1300–1362) and the flash at 1587. The ground heave at 1593–1600 moves everyone with the ground.
- `clip_scan.py`, the director's script unchanged: **0 bad ranges.** The root-bone copy also gives **0 bad ranges.**
- Hand audit: see `v004_hand_audit.txt`.
- Hand-contact close-ups: `v004_hand_contact_closeups.jpg`.

## Not changed or open
- The crew are generic MPFB figures with simple faces. In wide shots their faces are small. Faces are readable on beats 6, 8 and 11, and are not a factor in the cross-section beats.
- The fire and cross-section looks are unchanged from v003 (approved).

## Round 2 (director review of v004, Nov 12 14:34)

| # | Note | Fix |
|---|---|---|
| 14 | 23.5–24.5 s: the soldiers' faces were pressed into the casing, as if hugging it. | They now steady the hanging casing **side-on**, as you would a load on a crane hook. One hand is flat on the casing at chest height, and the other rests on the hip or signals the crane operator. Backs are upright and heads are up, turned toward the crane. Measured at f1420: palm within 1 cm of the casing, head 31 cm off it, chest 36 cm off it. When they let go, the hand drops down beside the casing instead of pulling back through the body. |
| 15 | The hose pickup crouch had the head buried in the knee and shoulder. | The soldier now bends more at the knees, keeps his back less folded, and holds his **head up, looking at the hose**, with his fingers closing on it. |
| 16 | 33.0 s: a yellow object at the frame edge (the crane cab), with empty desert behind. | The camera route now passes east of the crane and frames the bunker crew from 1988 on. |
| 17 | 32.5 s: mostly empty sky with a blurred flame. | Beat 11 opens on the shaft and the wellhead with the dying flame (1925 framing at ground level). |
