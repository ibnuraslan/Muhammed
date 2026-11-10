# Production rules (from client feedback)

## Camera: one continuous move, never cuts
- **New angle about every 1 s, but no cuts.** The viewer should feel one camera that keeps moving: it pushes in, orbits, cranes, pulls back, drops low, rises. The *angle* changes; the shot doesn't.
- Build each shot as **one camera on a smooth spline path** through keyframed framings, one per ~1 s beat. Velocity stays continuous through every framing, so the camera never stops or snaps.
- **No camera switching** (no multiple cameras with timeline markers) for angle changes. Cut5s_v001 did this, and even with whip-pans it read as "cut, cut, cut".
- Whip-pans and fly-throughs are occasional accents inside the move, not a way to hide a camera switch.
- Change shot size gradually (medium → close → macro over the move), not by jumping wide straight to macro.
- Keep the key action (grasp, contact, drink, impact) on screen while the camera travels.

## Carried over from the motion test
- 1080×1920, 60 fps, set before animating. Cycles 48 samples / 0.05 / OIDN baseline, verified per scene.
- Planted feet locked; whole-body coordination; anticipation, weight transfer, follow-through, settle.
- Grasp visible before an object moves; no hands through props or faces (check numerically and in close-up renders).
- Continuous preview reviewed before any farm job; technical checks are not artistic approval.
- Look: textured, grounded, muted natural colour. Pacing and visual grammar: see `reference_analysis/batch01_analysis.md`.
