# NoPilotPlane_v009: third-person re-stage to the new VO beats

The director rejected v008b and asked for a simpler re-stage rather than more patches. v009 keeps the story, set, characters and ending, but changes how the film is shot and timed.

- `NoPilotPlane_v009_60fps.blend`: packed, plain git file (no LFS), one camera `CAM_Film`, frames 1–3481 (58.0 s at 60 fps).
- `beats.json`: the director's 19 VO beat seconds; beat N starts at frame 1 + round(s × 60). No VO is added.
- `review/preview.mp4` and `review/pages/`: the full preview of this exact package (every 5th frame, 270×480, 12 fps = real speed), rendered after the last change to the file.

## The director's list

| # | Note on v008b | What v009 does |
|---|---|---|
| 1 | 35 s of first-person cockpit POV: hands filling the frame, no face, static panel. | No head-cam. YOU is a visible third-person character for the whole film. The film is a cut list of 35 shots (`scripts/08_camera.py`), none longer than 2.5 s. In the cockpit it cuts between his face through the windscreen (lit by the panel), a front-left three-quarter with his hands on the yoke at normal size, the view out of the window, the radio and the doorway. |
| 2 | Pink/red glare blobs on the windscreen and sky. | They came from the two red alarm point lights (`L_alarm`, `L_alarm_cabin`) strobing at 70 and 150 W during the alarm beats and lighting the canopy and the sky. They now stay off. The small red warning lamps on the panel still flash. |
| 3 | Giant limbs in the lens. | Every camera is placed and checked so that YOU, the captain and the first officer stay at least 1.5 m from the lens when they are in frame (passengers at least 1.0 m). See the check below. |
| 4 | The FO sprawled in a twisted pose, seen from above. | Both pilots now lie on their backs, face up. The captain lies across the doorway; YOU crouches beside him to check him (from between the pilot seats), then steps over him. After the haul, the first officer ends on his back along the right side of the cockpit, face up, and is shown at medium distance (51.1–52.5 s). |
| 5 | Build to the VO beat seconds, no warp. | All action is authored in the old beat seconds and mapped piecewise-linearly onto the new ones in `03_animate.py` (`remap`/`F`), so every beat starts exactly on its new frame. The film ends at 58.0 s. |

The ending close-up of his face (55.72–58.0 s) is kept as it was.

## Build chain
`03_animate.py` → `pipeline/anim_look.py` → `05_look_tune.py` → `06_pov_split.py` (the head split now runs only with `pov`; v009 does not use it) → `04_package.py` → `08_camera.py` (cut list, re-keys `CAM_Film` on the packaged file).

## Checks on the packaged file
(pending: running on this package)

## Open
(pending)
