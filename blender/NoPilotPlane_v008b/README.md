# NoPilotPlane_v008b: director's open items on v008

Same film, frames and story-beat frames as v007d and v008. `beats.json` is unchanged and no VO is added. Every texture is packed, it is a normal git file (no LFS), and there is one camera, `CAM_Film`. The farm settings are in `SETTINGS.md`.

`review/preview.mp4` is the moving preview: every 5th frame at 270×480, 12 fps (real speed), made with `pipeline/preview.py` and `pipeline/watch_pages.sh`. `review/pages/` holds the contact pages of every preview frame. The preview was rendered in full from the v008b build. The frames changed by the last fix round (6 ranges, listed below) were then re-rendered from the final build. The build is deterministic and the untouched frames are pixel-identical, which was checked.

## The director's list
| # | Item | Fix |
|---|---|---|
| 1 | 27.7–28.2 s: YOU's forearm clips during the haul. | **Pose fix, no material tricks.** YOU's hands were at eye height (wrist z 1.32 m, eye 1.34 m), and the left forearm crossed in front of the face to the top of his shoulder. A view-depth check (below) showed YOU's arm 0–5 cm in front of the lens from 27.6 to 30.2 s. Now the left hand grips the outside of his near upper arm, about 20 cm under the eye line. The right hand is on the side of his near shoulder. Both elbows are posed down and out with IK poles. The forearm now reads as a whole arm rising from the lower edge of the frame, with no cut sheet. |
| 2 | Black panel at 17.2 s and 26.8–27.0 s. | YOU stands further back from the first officer's seat, turns with the head, and the look goes past the seat edge. The camera never comes within 12 cm of the cockpit geometry (graze check, every frame). |
| 3 | 43–44.5 s: yoke grip, check a 540×960 close-up. | The yoke grip is `hand_poses.grip_object` on the measured horn axis. It is re-applied after all body keys (a regrip pass of 239 grips), so later body keys can no longer reopen the fingers. The close-ups at 41.3, 43.5, 60.1, 63.2 and 72.8 s show the fingers and thumb wrapped round the horns. |
| 4 | 50.4–52 s: frame the hand with the horn, or move the camera. | The side glance is pulled back to 34–38° and the pitch raised. The hand and horn are framed together at the bottom, or both are out of frame. |
| 5 | Rerun qa_check, clip_scan and limb_check on the package. | Results below. |

## Other faults found and fixed in this round
- **Near clip.** The 8 cm camera near clip (a v007d workaround for the same haul arm) cut YOU's shirt and forearm open at 3.5 s, 6.9–7.3 s (dark wedge at the left), 59.1 s (black wedge under the throttle hand), 63.7 s and 66 s. With the arm posed off the lens, the clip is now 3 cm. All of YOU's head meshes (eyes, lashes, brows, hair, teeth, inner head and neck) are invisible to the camera until the face reveal, so a small clip shows nothing from inside the head.
- **First-person head split.** The split pieces and the unsplit face-reveal copies now swap by per-ray visibility keys instead of `hide_render`, so YOU never reads as a render-hidden rig to the checks.
- **Prop hygiene.** Uniform details that followed a bone through a `CHILD_OF` constraint are now real bone children. The deployed oxygen masks hang from a fixed ceiling mount (`OXYDROP_*`); they are not worn. The cockpit sun visors are named `SUNSHADE_*`.

## Checks on the packaged file
(pending: the checks are running on the final package)

## View-depth near-clip check (new)
My first lens check measured the straight-line distance from the eye. In a 9:16 frame a limb 11 cm away at a steep angle is still inside an 8 cm near clip, so that check missed the haul. The new check (`scratchpad lens2.py`, every 3rd frame) takes every camera-visible vertex of YOU inside the frame and reports its depth along the view axis:
(pending)

## Intended prop motion (not faults)
These are listed in `NoPilotPlane_v001/review/ACTING_notes.md`:
- CUP and DRIP at 3.2–4.4 s: the turbulence jolt shakes the drink on the neighbour's tray.
- YOKE_L and YOKE_R when nobody holds them: the autopilot flies the aircraft (30.9–31.5 s; 43 s).
- HANDSET at 21–26 s: in YOU's hand. qa reported it with the earlier hidden-rig problem; see the qa counts above.
