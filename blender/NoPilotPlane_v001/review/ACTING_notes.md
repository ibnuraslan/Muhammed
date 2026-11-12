# NoPilotPlane: acting review of v006 (client rejection of Nov 12)

Before sheet: `ACTING_before_v006_half_A_0-37s.jpg` and `ACTING_before_v006_half_B_37-73s.jpg`. They are 270×480 at 8 samples, one still every 30 frames. Frames are v006 frames, which are the same as v007: no story-beat frame moves (see `beats.json`).
The question asked of every still: would a real person move like this, here, for this reason?

| # | v006 time (frames) | Problem | Fix in v007 |
|---|---|---|---|
| 1 | 3.5–8.5 s (211–511) | YOU's left hand is pressed flat high on the wall above the window for about 4 s, and the arm passes over the neighbour's head. Nobody leans to look out like that. | The left hand rests on the window sill and frame bottom, below the window. The right hand stays on the armrest. YOU leans from the torso. |
| 2 | 13.0–16.5 s (781–991) | Beat 5, "one pilot has collapsed in the doorway": we only ever see the captain's legs and shoes. His face and body never read. | After stepping over him, YOU turns left and looks down at his face and chest (15.8–16.5 s). Then YOU turns to the first officer from 16.8 s; the beat frame is unchanged. |
| 3 | whole film | The captain, the first officer (after the haul) and all 49 passengers are frozen statues. Unconscious people still breathe. | Breathing on every unconscious character: chest and spine rise and fall, with a slight head nod, on a 4–5 s cycle with a random phase. Not during the dive, where the sway animation runs. |
| 4 | 33.7–44 s (2023–2641) | The captain lies perfectly still on the floor through a 30° nose-down dive and a 40° bank. | He slides about 10 cm forward and rolls slightly with the dive, then settles back as the aircraft levels. |
| 5 | 22.0–25.5 s (1321–1531) | The handset is held at arm's length in front of the panel while YOU "screams for help" into it. People hold a handset at the mouth. | The handset comes to the mouth: low in the frame, close, with a tight grip and a panic tremble. |
| 6 | 27.0–27.6 s (1621–1657) | Both forearms sweep across the lens, filling the frame, on the way to the first officer. One still has a black corner (the camera inside YOU's own arm). | The hands travel low, below the eye line, from the pedestal to his collar and shoulder. There is a mid key at 27.4 s, and the look stays on him. |
| 7 | 32.0–33.5 s (1921–2011) | "Pull the pilot out of his seat": the drag to the floor happens off camera. The first officer vanishes from frame and the hands touch nothing on screen. | The look follows him down to the floor (down-right, 32.4–33.2 s), so the hands at his collar and shoulder are seen dragging him. Then YOU whips up to the alarms at 33.7 s. |
| 8 | 50.4–52.0 s (3025–3121) | The look to the side window is a frame filled by a blank sidewall for about 1.5 s. | The side glance is narrower, at 34–40°, so the windscreen corner, side window and panel stay in frame. |
| 9 | 72.5–73.5 s (4351–4411) | The face reveal reads with black eyes in the review stills. The review script cut light bounces to 4; the farm file has 12, where the eyes render blue. | The review script now uses the farm light paths for the face frames. |

The rest was checked and kept:
- The wake-up (0–3 s), the stand-up and walk (9–11.6 s), the door push (11.6–12.2 s), the step over the captain (14–15.5 s) and the grab of the radio handset and its return to the cradle (19.7–26.6 s).
- The haul grip at the collar and shoulder (27.9–31.4 s), the yoke grips and the fight with the controls (38.8–56.5 s), the throttle hover and touch (56.8–64 s), the look-back (64.6–68 s) and the float-out (71.4 s).
- Loose items floating in the dive move by physics (negative g), not by themselves. They rise only while the aircraft pitches down and drop when it pulls out.
