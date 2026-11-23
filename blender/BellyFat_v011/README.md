# BellyFat_v011

This is a new build that replaces the rejected v010; v010 is left untouched. It has the same VO, timing and frame range: **frames 1–1273 at 60 fps**, with the VO (21.0 s) packed. It is built straight to the VO frames, with no retime, as 14 short shots joined by hard cuts on one camera.

## Files
- `BellyFat_v011_60fps.blend`: the render file, 74 MB, everything packed. `SETTINGS.md` has the render sheet.
- `review/preview.mp4`: the one small preview. It is every 5th frame at 270×480, 4 samples, with the VO, rendered with `pipeline/preview.py` from the exact package. `review/pages/` holds the contact pages of every preview frame.
- `review/clip_scan.json`, `qa_check.json`, `limb_check.json`, `body_prop_cross.json`, `audit_hands.txt`: the check results, from the package.
- `beats.json`: beat frames 1, 73, 181, 451, 715, 829, 1147.
- `CREDITS.md`: includes the CC-BY intestine credit.
- `scripts/`: the full rebuild, in order: `01_build_woman.py`, `02_build_scene.py`, `03_shots.py`, then `pipeline/anim_look.py`, `05_animated_look.py`, `shrink_textures.py`, `04_farm_settings.py` and `pipeline/package_for_farm.py`.

## The 18 items
Times are in the VO timeline.
1. **Origin and pose (0.0–0.6 s).** The opening is now a medium shot. She reads a box held on her left palm, with breathing, blinks, her head following the box and her basket on the floor. Shot B (37–72) shows where the bullet comes from: it cracks the shop window and flies down the aisle.
2. **Bullet in flight.** The camera rides 12 cm beside the bullet at f/22, so the bullet is sharp and visibly moving.
3. **Clear path.** The bullet path (y 0.43, z 1.0) passes 10 cm from the box and her forearm.
4. **Hit on the shirt.** Shot C is a close front-3/4 at f/11: the bullet in focus, the dimple and ripple on the shirt, then the hole mark.
5. **Layered cross-section.** It shows fabric, epidermis, dermis and fat as solid layers in contact. The skin sits at the top of a vertical frame and the bullet travels downward.
6. **Rings.** All the old rings are deleted. One flat shock-wave ring stays on the bullet and fades as the bullet loses energy.
7. **Defocused close-ups.** These are gone. Every macro shot is 2.7–4.4 units from the bullet at f/11, and the bullet is fully in frame and sharp on every preview frame.
8. **Progression.** The bullet travels steadily, with the depth curve slowing toward the stop at about frame 960. Its size and orientation stay constant: constant spin, no scaling, no tumbling.
9. **Bullet size.** There are no wide shots where the bullet is a few pixels. The bullet is at least about 12 % of frame height everywhere.
10. **Grey void.** The set extends behind every macro framing (muscle, peritoneum, bowel), so no grey void shows.
11. **Muscle layer.** The flat maroon slab is replaced by textured muscle fibres, and there is no foreground blocker.
12. **Fibres part at the tip.** The fibres part exactly where the tip is: each fibre opens as the tip reaches its depth.
13. **The stop.** It is clear and sharp above the bowel loops (frames 960–1146).
14. **Bullet pop-out.** The bullet no longer pops out: the macro bullet is a separate object on a static set, and the store bullet hides at the impact.
15. **The wound.** The shirt hole (dark core, frayed light ring, no blood) is shown with her in frame. She lifts her hand off it and looks down at it (shot O).
16. **Lens blocker.** There is no skin blob in front of the lens. There are no camera fly-throughs, only hard cuts.
17. **Face and hands.** She has a ponytail with the fringe off her face, fixed eyes with a catchlight on the camera, blinks, and a mouth that is closed or slightly parted. Her left hand is placed on the wound with `place_hand` and pushed out until it touches without going in. Her right hand hangs relaxed, away from the shelf.
18. **Payoff (shot P, 1207–1273).** She straightens, breathes out, looks up and pats her belly: she's fine.

Logo: DA KRAS FILMS appears dark on the box she holds (shot A) and on a box on the shelf behind her, flat to camera, at about 20 % of frame width. The shelf box shows in shots A, D, O and P, over 5 s in total. The logo also appears in white on the basket sides.

## Checks (on the package)
- `clip_scan`: no bad ranges.
- `audit_hands`: 1 frame (f1219, 5 hand vertices against her side as the hand returns to her belly). No hand-in-hand, no hand in another character, no wrist bends.
- `body_prop_cross`: only frames 1–35. Her left forearm grazes the underside of the held box by 2–3 points, which isn't visible from the shot-A camera. The basket, handle and other props have no crossings.
- `limb_check` ARMBODY: every flag is the first segment of `upperarm01`, at the shoulder joint, which sits inside the shoulder mass on this rig. I probed every flagged point; none is on the forearm or the rest of the upper arm.
- `qa_check`: every flag is by design:
  - CAMJUMP marks the hard cuts.
  - EMPTY marks the bullet-flight shot and the macro shots, which have no character.
  - FILL and ROLL come from the macro set: there is no horizon, and the skin layer is placed at the top of the frame.
  - PROPMOVE is the flying bullet.

## Known issues
- The window break in shot B is brief: the camera is on the bullet, so the cracked glass is seen only in the first frames.
- At the cut to H2 (frame 961) the framing widens, so the bullet is smaller than in H1. Within each shot its size is constant.
- In shot H3 the bowel loops behind the bullet are slightly soft (f/11, far behind the focus plane). The bullet is sharp.
- I did not render a full-resolution frame here (studio rule).
