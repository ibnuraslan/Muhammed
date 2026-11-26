# v009 check 3: PASS (round 3, approved by the director)
`review/preview.mp4` = the full moving preview of the round-3 build (every 5th frame, 270x480, VO, 28.45 s). I watched all 15 time-stamped pages (24 tiles each), start to finish.

The director approved one extra round, limited to the camera, the time skip and small pose fixes. Each check-2 fault is now fixed:
- **Time skip hidden (f1566-1596):** the camera follows the teen's legs out of the well, then whip-tilts up past the pulley into the sky (f1572-1596). The switch at f1586 happens with only sky and the pulley cap in frame. It then tilts down on all three standing together (from f1606). No pop is visible.
- **Forearm clear of the rim (f1112-1300):** the teen's arms are tucked closer to his head while he goes in head-first. body_prop_cross now reports no teen-to-casing contact.
- **Face at the frame edge (f951-986):** the nod close-up is framed on the rescuer alone. The teen only crosses the frame edge for a few frames as the camera pans in and out.
- **Grab hold (f1352-1440):** the camera now drifts in, across and back during the hold.

## Script checks (round-3 build)
- clip_scan: 0 bad ranges.
- body_prop_cross: the only body-to-prop contact left is the toddler's root on SET_Casing at f100, as he steps over the rim. All the rest is rope-to-rope (ring, knot and rope, intended) or the teen's fingers on the rope while he ties the knot (intended contact).
- limb_check: ARMBODY 595, mostly the shoulder-point false positive and raised cheer arms. Checked by eye, no visible arm-through-body.
- qa_check: EMPTY 238. These are the cut-away shaft and strata frames (characters small against the soil face, by design) plus the short sky whip at f1572-1600 that hides the time skip. PROPMOVE 16 and ATTACH 35 are the hooked rope points and the head-torch parts.

No fresh reviewer was run on this extra round: the director limited it to one preview.
