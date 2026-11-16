# Milgram_v002c: checks on the packed file (`Milgram_v002c_60fps.blend`)

| Check | Result | Notes |
|---|---|---|
| `body_prop_cross` (tables, chairs, generator body/base/top/levers/plates, cuffs, clipboard) | **0 visible crossings** | every 6th + mid + last frame of every shot; every frame of the lever shots 03, 07, 12, 23 |
| `clip_scan` (6, 2 cm) | 1 short range: 1081–1093 | start of 13b: the kneeling stranger's hand resting on his thigh; reads as a hand on the thigh in the preview |
| `qa_check` EMPTY | 02, 17, 20 (+ a few first-person frames) | intended object shots on their words: the red lamp ("incorrectly"), the unplugged plug ("weren't real"), the photo on the clipboard ("test subject"); first-person shots show the hand only |
| `qa_check` CAMJUMP | 21 | one per hard cut, baked into the single camera |
| `qa_check` FAN | 01, 07, 10, 23, 29 | the `point` preset (index straight, other fingers curled) |
| `qa_check` PROPMOVE | stranger shots | the electrode cuff moves with the forearm it is strapped to (Child Of the forearm bone) |
| `qa_check` BACKHEAD | 06 (2 frames) | the 3/4 back view of the subject at the generator (director: back view fine) |
| `limb_check` ARMBODY | 2–3 points per arm | the shoulder-root points of the upper arm (known false positive); no arm enters a body in the preview |

v002b changed only the two lab-table materials (procedural wood) and the f-stop of the first-person, wrist and clipboard
cameras (f/22). Character poses and camera positions were compared against v002 at 7 frames across the film: identical
(max difference 0.0), so the v002 contact checks above still hold.

v002c adds only the stranger's hair (a hair mesh deformed by his head, neck and spine bones). Poses and camera positions
were compared against v002b at 7 frames: identical (max difference 0.0). The stranger's shots 01, 08, 09, 13a, 13b and
18 were re-rendered and watched in the spliced preview: the hair stays on the scalp through the jolt, the lean over the
table, the collapse and the wave.
