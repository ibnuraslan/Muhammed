# NoPilotPlane_v008: motion-review fixes on the approved v007d

Same film, frames and story-beat frames as v007d: `beats.json` is unchanged and no VO is added. Every texture is packed, it is a normal git file (no LFS), and there is one camera, `CAM_Film`. The farm settings are in `SETTINGS.md`.

`review/preview.mp4` is the moving preview: every 5th frame at 270×480, 12 fps (real speed), made with `pipeline/preview.py` and `pipeline/watch_pages.sh` (director commit e0c925f). `review/pages/` holds the contact pages of every preview frame.

## Faults found by watching the v007d preview, and the fixes
| Time | Fault in motion | Fix |
|---|---|---|
| 0–1.6 s | Waking up: the hands float up to the face as flat, splayed palms in front of the seat. | The hands stay on YOU's own thighs and grip them. |
| 9.0–9.6 s | Standing up: the seat back ahead fills the frame. | The look goes over the seat ahead, not into it. |
| 11.7–12.4 s | After the door push the right hand hangs open and flat in the air. | The hand goes straight from the push onto the door frame. |
| 28.3–28.5 s, 32.4–33.4 s, 49.4 s | Black blobs: the 8 cm near clip cuts into YOU's own arm or body, and the camera sees the dark inside of the mesh. | Backfaces of all YOU's materials are transparent to camera rays (`06_pov_split.py`). A clipped limb shows the cockpit behind it. |
| 36.8–38 s | A floating mug becomes a giant white blob in the lens. | Loose items only lift a little and tumble near where they were. |
| 38.8–39.2 s | The hands hover palm-up on the way to the yoke. | The hands go straight onto the horns. |
| 39–72 s | Yoke: the hands cup the horns from below instead of gripping them. | `hand_poses.grip_object` on every yoke key: the palm faces the horn and the fingers and thumb wrap it. |
| 59.2–59.8 s | Throttle: the hand sits on the lever without gripping it. | `grip_object` on the throttle lever. |
| 57–64 s | The hand hesitating over the throttles is flat and splayed. | Loosely closed. |
| 52.4–53 s | The forearm fills the lens, with a black corner, in the side glance. | A narrower glance: 36° instead of 60°. |

## Still open
- 17.2 s (2 preview frames) and 26.8–27.0 s: a black panel at the right edge, behind the first officer's seat.
- 27.7–28.2 s: during the haul the 8 cm near clip cuts YOU's left forearm. With the backface fix it now shows as a flat beige sheet instead of a black blob, which is better but still visible.
- 43–44.5 s: in the preview the hands on the yoke horns still read loosely at 270×480; there is no close-up check yet.
- 50.4–52 s: in the side glance, one hand shows as a fist at the bottom edge, with the horn out of frame.
