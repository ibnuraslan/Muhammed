# ToddlerWell v010 — check 4 (client fix: toddler legs in the well)

Fix: the toddler's foot IK targets were planted at field level (z = 0) while she stood on the well floor (z = -9),
so the leg IK pulled both legs up and backward on every well frame. v010 plants them on the well floor (`gz=Z_BOT`)
and adds IK rotation limits on her knees (lowerleg01 X -20..150°) and hips (upperleg01 X -120..20°, Y ±60°, Z ±45°).
Nothing else changed.

Result: **PASS** — watched the full moving preview (`preview.mp4`, every 5th frame, VO synced) start to finish.

- Backward-leg detector (knee bending against the body's forward direction, or hip hyperextension), every 2nd frame 1-1728:
  v009 flags 85 samples, v010 flags 0. Largest foot-to-target gap 1.4 cm.
- Watched well frames f186-1560: standing legs straight down, natural kneel on landing (f186-216),
  knees slightly forward while dangling during the lift (f1440-1560). No backward knees anywhere.
- clip_scan BAD_RANGES [], qa_check EMPTY 238 / PROPMOVE 16 / ATTACH 35, limb_check ARMBODY 595,
  body_prop_cross SET_Casing VIS 5 — identical to the v009 check 3 PASS (same causes, see v009 CHECK3.md).
