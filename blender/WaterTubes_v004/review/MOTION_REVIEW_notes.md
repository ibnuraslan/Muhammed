# WaterTubes v004: motion-review fixes on the approved v003 (2209ad0)

I watched every preview frame of v003 (402 frames, every 5th frame, `preview.py` + `watch_pages.sh`; pages in the session scratch). Faults are listed by film frame, then the fix. The story-beat frames are unchanged (`beats.json` is identical to v003). No VO is added.

| Frames | Fault seen in motion | Fix in v004 |
|---|---|---|
| 1301–1326, and the aerials 1371–1496 and 1886–2010 | **Gaps between the tube segments.** The barrier had visible holes the flood could pass through (a logic fault). | Each segment now overlaps its neighbours by 0.6 m, so the rounded ends press together and the ring is closed. Tube 0's start is unchanged, so the valve and hose staging stay the same. |
| 1–60, 171–196 | The empty flat tube dipped under the lawn noise and showed as dark patches and triangles poking through the grass. | The empty ribbon now lies 5.5 cm up, always on top of the lawn. |
| 621–706 | The surge front read as a smooth beige blob filling 2/3 of the frame. | The lip is lower (1.0 → 0.6), the foam is darker and muddier, and the camera sits higher and looks along the street (3.4 m, aim 26 m out). |
| 691–706 | A street lamp swept across the lens. | The 11.5 s camera key is moved off the lamp (over the flooded street at 3.2 m). |
| 711–716 | A whip at 1.5 m height passed close to the ground and fence. | Raised to 2.3 m. |
| 1221–1251 | The cutaway exit was a hazy half-faded shell plus a beige flood-section slab crossing the frame. | The flood section and arrows are hidden at 20.3 s. The shell fades in 6 frames (20.52–20.62 s) and the swaps end at the same moment. The 20.2 s key is raised so the exit isn't a blank sky. |
| 1256–1296 | A beige water "slab" floated above the tube at the slam. | The slam lip is lower (1.0 → 0.45). |
| 1856–1876 | Over the ring the tube top filled half the frame (blur), and the hero was tiny. | The 31.3 s key is now a wide view over the tube from outside, aimed at the hero on his lawn. |
| 301–321, 1241, 1316 | **A neighbour house rendered as a black silhouette or black stripes** (the SketchUp "2 Story House" model and house_b). | Those lots now use the clean house models (house_e, house_c, house_d). |

Also confirmed in motion: the hose is in his hands from the first frame (nozzle in the right fist, hose through the left hand), and carried round the ring in beat 2. His feet are on the ground and the porch. His beat 10 face reads, with hands resting on his head.

Checks on the packed v004 file:
- `clip_scan.py`: 0 bad ranges.
- `hand_audit`: 5 hits, Neighbour B at f371–375, off camera.
- `qa_check.py`: see `qa_v004.json`. The remaining EMPTY and INSIDE flags are the intended no-character shots and the tube-normal false positives explained in `../WaterTubes_v003/review/ACTING_notes.md`.

## Second watch: the v004 preview (`preview.mp4`, made from this exact packed file)
- The ring is closed in every aerial. No black houses, no lamp sweep, no haze at the cutaway exit. The hose is in his hands (nozzle in his fist, then carried round the ring), and his feet are on the lawn and the porch.
- Left as they are, with reasons:
  - The surge wave fills the lower frame for about 0.6 s at 10.4–11 s. It is the subject of the "floodwater began rushing" beat and is in focus.
  - The camera drops out of the cutaway past the tube section at 20.3–20.5 s (3 preview frames, about 0.25 s).
  - The tube passes under the lens on the rise behind him at 30.9–31.2 s (about 0.3 s).
