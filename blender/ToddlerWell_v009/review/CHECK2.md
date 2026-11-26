# v009 check 2: FAIL (round-2 build): ON HOLD
`review/preview.mp4` = the full moving preview of the round-2 build (every 5th frame, 270x480, VO, 28.45 s). I watched all 15 time-stamped pages (24 tiles each). Both allowed fix rounds are used, so the film stays ON HOLD and no .blend is pushed.

Round-2 fixes confirmed in the preview: hi-vis rescuer, toddler drops with flailing arms and legs, no landing jump, no rope coil, bucket clear of the tripod, moving B4 time-lapse with evening light, teen arrives in time, nod close-up clear of the tripod leg, knot push-in, beam shortened at the grab, end crane up and to the left.

## Blocking fault
- **f1566-1590 (26.1-26.5 s): visible teleport.** The camera looks up at the pulley, but the teen's inverted legs and the knot stay in frame at the well mouth, and a toddler hand peeks in at f1586. At f1586-1591 (the time skip SW) both pop to their final standing spots in view. The time skip must happen fully off-frame.
  Fix: from about f1550, aim the pulley shot higher and tighter (look-at about z 2.6, lens 50 mm, with the well mouth below the frame), or keep the teen rising and pulled out by the rescuer, then hold SW until the camera has turned away.

## Minor (fix in the same pass)
- f1132-1147: the teen's right forearm crosses the casing rim as he goes in head-first (body_prop_cross: lowerarm01.R and clothes on SET_Casing). Tuck the arms closer for the first 40 frames of the inversion.
- f951-986: the nod close-up crops the teen's face at the left frame edge. Frame him fully or leave him out.
- f1352-1440: the grab reads as a near-static hold (about 1.5 s). Add a slow lift or a bigger kick.

## Script checks (round-2 build)
- clip_scan: 0 bad ranges.
- body_prop_cross: 229 visible frames, nearly all rope-to-rope (ring, knot and rope, intended). The teen's fingers touch ROPE_Teen at f1006-1090 while he ties the knot (intended contact). Toddler root on SET_Casing at f100, as he steps over the rim. Teen arm on the casing at f1132-1147 (see above).
- limb_check: ARMBODY 619, mostly the shoulder-point false positive and raised cheer arms. Checked by eye, no visible arm-through-body.
- qa_check: EMPTY 235. These are the cut-away shaft and strata frames, where the characters are small against the soil face by design. PROPMOVE 16 and ATTACH 36 are the hooked rope points and the head-torch parts.

No fresh reviewer was run on this check: my own watch already fails it, and both fix rounds are spent.
