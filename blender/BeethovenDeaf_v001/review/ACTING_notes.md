# BeethovenDeaf: acting review of v007 (0.5 s sheet `review/ACTING_before_v007_0p5s.jpg`)

Frames are v007 timeline frames (frame = 1 + 60 × t). All story-beat start frames are unchanged in v009: 1, 235, 313, 517, 715, 985, 1105, 1207.

| # | t (s) / frames | Problem | Fix in v009 |
|---|---|---|---|
| 1 | 1.5–2.5 / 91–151 | The camera swings **behind his head**. Hair, ear and the back of the head fill the frame, and his face is lost while he bites the rod. | The profile framing moved to his front-left. The rod pull-back framing is in front of his face plane, not behind it. |
| 2 | 3.0–3.5 / 181–211 | The room wide is shot from high above, so only the top of his head shows and the **face is hidden** under the hair. | The camera is lower and more frontal (front-left over the piano corner), so the face reads under the hair. |
| 3 | 7.5–8.5 / 451–511 | The end of the rod ride is an extreme macro: **his nose fills the frame**, eyes cut, and the face is unreadable as the rings reach the jaw. | Pulled back about 6 cm and raised. Eyes, nose, teeth and rod are all in frame. |
| 4 | 19.0 / 1141 | The pull-back from the cochlea leaves a **near-empty frame**: backdrop plus a tiny cochlea at the edge. | The framing stays on the cochlea and temporal bone until the skin returns. |
| 5 | 20.0–20.5 / 1201–1231 | Beat 8 opens on the **top of his head**: hair fills about 70 % of the frame. | The pull-out framing is at face height, front-left, so the face (eyes closed, rod in teeth) reads on the beat. |
| 6 | 20.6–23.5 / 1237–1420 | **Manuscript pages fly off the music desk on their own.** No hand touches them, which breaks "props never move by themselves". At 21.0 s a page fills the frame. His hands can't reach the desk while his teeth are on the rod (about 0.65 m from the shoulder). | The flight was removed, and the pages stay on the desk. The floor already has 14 pages scattered from the start, so the "scattered manuscripts" overhead still reads. |

## Checked and fine (no change)
- **Rod in the teeth:** the mouth reaches the rod and clamps (the tip moves at most 1 mm per frame through the attach at f29–31). After that the tip-to-bite distance is 0 mm for the whole film.
- **Hands on the keys:**
  - All 256 strikes land on the key tops, and the struck keys go down 9 mm.
  - Joint limits are active and the v007 hand audit is 0.
  - The crash wind-up (3.9–4.3 s) lifts both hands and slams; the lift is natural and there are no backward joints.
- **Weight:** he sits on the bench (±3 mm), both feet are planted, and the right foot works the sustain pedal. There is no sliding.
- **Not frozen:** the body rocks and sways with the music in every beat, and the shoulders, spine and head move. The head is forward and down because his teeth are on the rod, which is the story, not a held pose.
- **Face on the beats:**
  - 0.0 s mouth open, then the bite at 0.5 s.
  - 3.9 s profile at the keys.
  - 18.4–20.1 s eyes close in bliss.
  - Beats 4–7 are inside the head by design: the x-ray dive.

## Round 2: director review of v009 (0ead4ad), all eight items fixed
| # | Director note | Fix |
|---|---|---|
| 1 | 0.0 s opened on a half-face crop of the nose and open mouth | Opens at eye height on a front-3/4 of the face: both eyes, the mouth opening for the rod, the rod in frame, and the bookcase behind him. |
| 2 | 1.5–2.5 s hair filled the top of the frame (camera close and above him) | The camera pulled back and dropped to eye level for the profile and pull-back. |
| 3 | 5.0 s hair blob on the right edge | The keys/rod framing is lower and farther left, clear of his head. |
| 4 | 7.0 s camera clips his hair; 8.0–9.0 s forehead and hair | The rod-ride end is lower, beside the rod. 8.0–9.0 s is a front-3/4 at eye height on the eyes, teeth and rod. |
| 5 | 19.5–20.5 s beat 8 opened on the top of his head | Face-height framings: front-3/4 at 20 s, then 3/4 from his left side, eyes visible (closed in bliss). |
| 6 | 21–23.5 s camera high over his head, and the lid filled the frame | A low orbit at his left side at body height (21–22.5 s), then the crane up to the overhead from 23 s. He stays readable, and the lid never fills the frame. |
| 7 | **Body acting:** hunched, head hanging over the keys | His spine is now **natural, leaning in** (spine flex 15° instead of 25°, root 5° instead of 8°), and his **head is up** (pitched −14° instead of −3°) so the eyes look forward. **Shoulders work** with the phrasing (clavicles rise and roll, L/R out of phase), and the sway is larger (±5° yaw, ±3 cm). The rod still follows his teeth (0 mm). |
| 8 | Hand close-ups showed a sleeve or knee; flat fingers | **Pianist hands:** the fingers curve (42–55° curl at the strike, 30–40° lifted, chords 44–52°) with the wrist level, and the fingertips strike. The close-up camera is now aimed at each hand's own knuckles from outside the hand (`v009_hand_closeups.jpg`). |
| + | Found while checking: **the eyes rendered as black holes** in frontal views (MPFB's procedural eye group goes black with this light-path setup) | A clean animated eye shader: sclera, brown iris and pupil from a baked forward-facing attribute on the eyeballs, with a glossy coat. |

**Re-checked:**
- Beat frames are unchanged.
- `clip_scan.py`: BAD_RANGES [] (`v009_clip_scan.json`).
- Hand audit: 0 overlaps and 0 joint violations.
- Strikes: 256 on keys that go down; worst 9 mm, 0 dips over 8 mm.
- Rod: 0 mm from the teeth.
- Seat: +0–5 mm on the cushion.
- Camera: never inside geometry.
