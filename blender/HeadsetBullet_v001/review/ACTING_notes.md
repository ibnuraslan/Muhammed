# HeadsetBullet: acting review of v005 (client, Nov 12) and the fixes in v006
Sheets: `v006_BEFORE_0.5s_part1/2.jpg` (v005) and `v006_AFTER_0.5s_part1/2.jpg` (v006). Each is 270×480 at 8 samples, one still every 30 frames.
Story-beat frames are unchanged (1, 133, 241, 355, 571, 697, 835, 949, 1165, 1315), so `beats.json` is the same.

| # | Time (frames) | Problem in v005 | Fix in v006 |
|---|---|---|---|
| 1 | 9.5–11.5 s (f571–690) | The frame is filled by the back of his head and blurred hair for about 2 s. His face and the cup don't read while the line says "instead of piercing his skull". | The camera moves round to his left-front side at temple height. His profile, the ear cup and the incoming bullet are all in frame, and the camera stays clear of his hair. |
| 2 | 14–15.5 s (f835–930) | The cutaway is shot almost top-down, so the top of his head and his hair fill half the frame. | The camera is lowered to a three-quarter side view of the cut cup. The section shows the shell, foam, steel and bullet; less hair is in frame. |
| 3 | 18.8–19.2 s (f1130–1150) | After the thud he turns back to the monitor and his hands hover low over the keyboard, as if he's about to keep playing. That is a frozen, unmotivated pose. | He keeps looking at the hole after the thud. His hands pull up toward his chest in shock, shaking, then he turns back and reaches for the headset at the beat. |
| 4 | 11.9–12.3 s (f712–735) | The energy can tips over on its own; no hand or visible cause moves it. | The can stays put. A prop that moves without a hand is a reject. |
| 5 | 23.4–23.6 s (f1405–1420) | During the face → over-shoulder swing, the frame is filled by the chair back and his shoulder: his head had already turned away from the camera, and the aim curve overshot toward the hole. | He starts the slow turn toward the hole about 0.5 s later (f1405 → 1458). The camera aim uses a monotone curve, so it can't overshoot. His face stays readable through the swing, then the hole comes into view over his shoulder. |
| 6 | 20.4–21.0 s (f1225–1260) | The chair rolls back while his feet stay planted, so the right heel lifts about 2 cm (known issue). | The chair roll-back is shortened to 4 cm and the feet slide back with it, so both heels stay on the floor. |

Checked and OK (no change):
- The chase and window fly-through: there is no character in frame.
- Typing and the mouse: fingertips on the keys and a palm over the mouse (close-up `v005_hand_closeups.jpg`).
- The head jolt at the impact.
- The rip-off: hands close on the cups first, then the headset moves.
- The cradle and turning of the headset (thumbs opposing the fingers).
- The shock face on beat 10.
- The framed print swings because the bullet hits it.
- The chair swivel comes from his own startle in it.

## Re-check (v006)
- **Hand audit** (`v006_hand_audit.txt`, BVH every 2 frames, 1500 frames):
  - hand × hand 0
  - hand × own body 0
  - hand × shirt 0
- **Director clip scan** (`pipeline/clip_scan.py`, `v006_clip_scan.json`): **BAD_RANGES = []** (0 bad ranges).
- **Contact audit** (`v006_audit.txt`):
  - fingertips into keys: 2.8 mm max
  - grip on the ear cushion: 2.9 mm max
  - head into the worn headset: 0 mm
  - camera inside geometry: 0
- **Hand close-ups:** `v006_hand_closeups.jpg` covers typing, mouse, both shock poses with the hands toward the chest, the reach, closing on the cups, the rip, the cradle and the hold.
- **Unchanged:** the wrist limits are pinned to v005's approved natural range. The story-beat frames are as listed above, and `beats.json` is the same.
