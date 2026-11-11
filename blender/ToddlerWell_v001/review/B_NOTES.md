# Checkpoint B: blocking

- `B_blocking_1s.jpg`: one still per second (0–32 s), 270×480, 8 samples, timed to the beat targets (no VO yet).
- `camera_path.jpg`: the full path of the one camera, in top and side views, with beat starts marked.
  - The camera dives down the pipe in beat 1.
  - It rockets up and back down in beat 2.
  - It passes out through the pipe wall into the cross-section and rises to the surface in beat 3.
  - It sinks into the cross-section during the beat 4 time-lapse.
  - It goes back down the pipe with the teen in beats 8–9.
  - It passes out through the wall again and rises with the pair in beat 10.
  - It cranes up at the end.
- `../beats.json`: the start frame of each beat for `retime_to_vo.py`.

## Known issues, to fix in polish
- Knot close-up (19–21 s): the framing sees the teen's side, not the knot. Moving it to a front-diagonal.
- Hi-vis vest on ResB tears at the armpit when he bends. I'll increase the offset or use a proxy-fitted vest.
- Inside the shaft the light is functional rather than beautiful. More torch beam and dust is coming.
- The crowd is 5 MPFB people plus 3 instanced copies of the 4 villagers, so they share motion.
- The excavator dig cycle is simple rigid-part rotation. The bucket doesn't reach the pit floor yet.
