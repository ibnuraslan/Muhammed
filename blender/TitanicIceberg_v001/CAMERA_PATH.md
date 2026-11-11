# Camera path (Checkpoint B)
One camera (`Camera_Main`) on a Catmull-Rom spline through the keyed framings in `scripts/03_animate.py` (`CK` list). Positions and look targets are both splined, and lens and f-stop use PCHIP. It is keyed every 2 frames, with no cuts and no camera switching.

| frames | move |
|---|---|
| 0–118 | Low over the deck boards past the steward's shoes, rising to over his shoulder as he raises the bellows camera. |
| 118–350 | Rack focus from the camera to the berg, push out over the rail, track the ghost liner passing, drift down to the waterline. |
| 350–625 | Macro skim along the red smear at the waterline (35→50 mm, f/2), tilt up the smear, ease back. |
| 625–915 | Crane-up aerial over the debris field, arc to the steamship, orbit back to the berg. |
| 915–1084 | Night ghost replay: low alongside the scrape, racing along the sparks, push into the smear. The ice skin is crossed at frame 1084 (raycast-detected). |
| 1084–1200 | Inside the darkroom (hidden inside the berg): descend over the developer trays, pull back to the door. |
| 1200–1329 | Fly through the doorway into the office, orbit over the experts' shoulders, push through the magnifier lens into the held print (crossed at 1329). |
| 1329–1561 | Explainer cyc (deep teal→navy): the giant print, the ghost hull slides in, the red band and match line. Fly into the giant print (crossed at 1561). |
| 1561–1830 | Exit the berg into the fog, turn back, slow orbit around the drifting berg, settle. |

Fly-through surfaces are hidden from the camera only after the camera has passed them (keyed `visible_camera` / `hide_render`, constant interpolation).
