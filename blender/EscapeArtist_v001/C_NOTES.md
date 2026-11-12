# Checkpoint C: polish notes

## Sheets
`stills/C_polish_beatNN.jpg`: 0.2 s stills (5 per second), one sheet per beat group.

## Audit (`scripts/audit.py`, every 30 frames, visible characters only)
Checks: foot hover/sink vs the floor or the ray-cast yard ground; hand/head penetration (nearest-surface + normal-side test, within 8 cm, against all set meshes); camera inside geometry.

Result before the last fixes: hover 0, sink 0, camera-inside 0, penetration flags 19 of 400 character-samples:
- Beat 1: fingers ~1 cm inside the bars they grip (56 verts). Fixed: grip targets moved 2.5 cm back.
- Beat 10: saw-hand fingers brushing the window reveal (80–210 verts). Fixed: stroke recentred, hands pulled 3 cm out.
- Beat 6: stepmother 13 verts (pointing hand near the brick wall), beat 11: 32 verts at the cell door. Minor.
Feet are planted by IK (anim_lib walk), and the yard uses ray-cast ground height. Fence climb frames (1600–1800) are excluded from the floor check: feet are on the mesh.

## Changed since B
- Night beats lit: caged cell bulb, moonlight through the window, face fill. No more black frames in solitary, saw or time-lapse.
- Orange prison overalls (hue-shifted MakeHuman denim); boy rebuilt younger (about 8), with darker hair; no printed shirts anywhere.
- Stepmother faces camera, phone at ear, pointing; boy reacts behind her.
- Saw beat shot from outside the window through the bars (blade, filings, notch, his face straining, glance at the door).
- Key-ring macro on the guard's hip at 1 s; glowing memory key no longer drifts to the floor.
- Brick prison exterior with real window openings, sills, roof edge, gutter and downpipes.
- Court→corridor whip now goes through a real doorway, so there's no blank wall. The path into cell 6 is re-routed through the gate bars and cell bars, not the divider wall.
- Old man stands from the bunk and walks to the window, rather than popping there.
- The prisoner is hidden while off-stage between beats 3 and 8, so no stray walk through walls.

## Found in the 0.2 s sheets, fixed for D (not in these sheets)
- 42.6 s: one black frame. The camera spline overshot into the far corridor wall; keys pulled back.
- 58.6 s: one black frame. The camera flew through the middle window bar; path offset between bars.
- Final window pose: the old man's hands were swapped (arms crossed); now each hand grips its own bar.

## Known, not fixed yet
- Beat 9: the solitary steel panel is behind camera most of the time, so "solitary" mostly reads through the slot light and the darker cell.
- Beat 1: the key-ring macro holds about 1.2 s on the guard's hip.
- Sheets 0–181 (beats 1–9) come from the film before the court-doorway / cell-6 path fix; 118–128 and 0–28 were re-rendered after it.
