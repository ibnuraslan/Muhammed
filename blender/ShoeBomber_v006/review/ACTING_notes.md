# ShoeBomber acting review of v004 (half-second sheet: `BEFORE_v004_0p5s.jpg`)

Frames are on the v004 timeline (60 fps, frame = 1 + 60·t). The beat start frames stay where they are: 1, 199, 373, 481, 655, 769, 1069, 1249, 1393.

## Problems found
| # | v004 frames | Problem | Bar broken |
|---|---|---|---|
| 1 | 1–200 | The bomber is hunched over a foot pulled up against his own shin. Both hands are crammed against his legs: clip_scan flags 1–127 and 157–193, with hands into his own thighs and shins. | hands / contact |
| 2 | 30–130 | The camera is filled by his huge foreground hand. His face doesn't read on the beat 1 line. | camera / face |
| 3 | 30–200 | The lit match floats beside his fingertips instead of being pinched between thumb and index finger. | prop without hand |
| 4 | 140–200 | His face is pressed into the seatback in front: the hunch is too deep, so his head hangs into the seat. | frozen / head hanging |
| 5 | 170–318 | The attendant walks the trolley, but after she lets go at 372 the trolley later slides forward by itself (470–560). | prop moves by itself |
| 6 | 372–430 | The attendant goes from the trolley (y 2.85) to row 3 (y 0.55) with no steps, sliding 2.3 m. She also passes **through** the parked trolley, which is between her and row 3. | sliding feet / through prop |
| 7 | 440–575 | The steward runs only to y −1.6 (f530), then **teleports** about 2.9 m across the pile into his kneel at the bomber's arm (f575). | snap / teleport |
| 8 | 492–590 | The attendant slides from his seat row to a kneel at his head (about 1.5 m) with no steps, and drops from standing to kneeling in about 10 frames. | sliding / snap |
| 9 | 440–545 | PaxB slides sideways out of seat 2C into the aisle while standing up. | sliding feet |
| 10 | 768–830 | PaxA slides 0.7 m sideways from his kneel into the row-3 legroom. | sliding feet |
| 11 | 830–850 | The attendant drops from walking to a kneel in 10 frames. | snap |
| 12 | 690–740 (11.5–12.5 s) | Tops of heads (the steward's and attendant's hair) fill the frame. His face is not seen as he goes limp on "finally sedated". | camera / face |
| 13 | 860–1000 (14.3–16.5 s) | The camera looks down on the top of the attendant's head while she pulls the shoes off and holds them up. Her face is unreadable on "checked his shoes". | camera / face |
| 14 | 397–937 | clip_scan flags hands/fingers more than 2 cm inside other bodies in the tackle pile and the pin: grips on his wrist, arm, back and calves sit too deep. | hands |
| 15 | 1393–1560 (23.2–26 s) | The camera sees the traveller only from the ceiling or from behind while he bends and puts the shoe in the tray. His face only reads at the very end. | face on beat |
| 16 | 1440–1460 | The traveller hangs bent over the belt with his head down, watching his own feet, for about 0.5 s with nothing else happening. | frozen / head hanging |

## Not problems (checked)
- **Studio cutaway (1069–1248):** props float by design, an explainer insert with no hands.
- **Sky (1249–1392):** clean.
- **Sleepers:** they breathe and shift (keys every 30 frames).
- **Tray table and cup in the tackle:** both are knocked by his body. The impact is motivated.

## Fixes in v006 (beat start frames unchanged: 1, 199, 373, 481, 655, 769, 1069, 1249, 1393; no VO added)
| # | Fix |
|---|---|
| 1 | Beat 1 re-posed: a shallower hunch (lean ×0.3). The raised right foot is turned out with a knee pole, so the shoe faces the camera. The left hand holds the toe, the right strikes above the tongue, and neither hand touches his legs. |
| 2 | Beat 1 camera reframed (45/100/150): the face plus the flame. Wider lenses, so there's no foreground hand. |
| 3 | The match sits between the thumb and index fingertips (a Child Of to the wrist, solved from the finger tips at f30). |
| 4 | The hunch no longer puts his head into the seatback (lower lean, head pitch ×0.9). |
| 5 | The trolley is parked in the forward galley from f1, with no other keys. It can't move by itself. |
| 6 | The attendant walks (with steps and arm swing) from the galley to row 3 on a path that misses the trolley, then rests her left hand on the row-4 seat-back. |
| 7 | The steward walks the whole way (440–532), holds two rows back while the attendant steps up, walks round her on the +x side (586–616), stops (624) and lowers to a kneel (640). The syringe appears in his hand at 640. |
| 8 | The attendant grabs his wrist (492), lets go as he drops, walks to his head with steps and arm swing (540–582), crouches (597) and kneels (612). |
| 9 | PaxB stands up in his seat, then steps into the aisle (474–500). |
| 10 | PaxA rises (790) and walks 796–825 to the row-3 legroom. His hands rest on the row-4 seat-back. |
| 11 | The attendant walks 790–848, stops (856) and crouches (864) before kneeling (874). Her hands go to her knees, then to his heel. |
| 12 | Beat 5 reframed low on the aisle side. When sedated, his head rolls onto his cheek (head yaw 32→58 over 690–720), so his face reads at 736–756. |
| 13 | Beat 6 framings (866/920/965/1015) aim between the shoe/fuse and the attendant's face, with wider lenses, so her face reads under every shoe insert and no sole fills the frame. |
| 14 | Hand contacts: a contact pass (`scripts/03b_hand_pushout.py`) solves every 3rd frame. Any hand vertex deeper than 1.2 cm in another body, or in its own head/torso/legs, pushes the IK target back out to the surface (+1.8 cm). On top of that there are hand-placed fixes: the attendant's hands ride on top of his wrist, PaxD's book comes down to her lap when she twists, PaxC's hand goes on the armrest, the steward's syringe and steadying hands sit on the sleeve, and PaxA's grab is raised. |
| 15 | Airport: the traveller glances up from the squat (head −25/−30). The cameras at 1470/1490/1508 are in front of him, so his face reads while he picks up and lifts the shoe. |
| 16 | The squat no longer has his head hanging over his feet. |

## clip_scan.py notes (for the director)
Two things in the v004 file made `pipeline/clip_scan.py` report false hits. Both are fixed **in the film**, so the unmodified tool reads true:
- clip_scan disables every MASK modifier, which exposed the MPFB "hide helpers" geometry (HelperGeometry/JointCubes) inside every body as an 'other' target. v006 deletes those helper vertices from all 13 bodies. They were never rendered.
- The ShoeHide foot masks were toggled by a keyed `show_viewport`, so `frame_set` re-enabled them and the vertex indices shifted under the scan. They're now toggled by a keyed mask threshold.
