# v013 check 3 (after fix round 2, the last allowed round): full moving preview of the exact packed file
`review/preview.mp4`: every 5th frame, 270x480, with the VO. I watched all 9 pages.

**Verdict: FAIL. ON HOLD. No .blend pushed.** Both fix rounds are used, so I stopped here as the brief asks.

## Fixed and holding in this preview
- Opening (f1-127): the water pulls away from the family's feet and the camera rides over the retreating sea.
- Running (f1061-1146): the arms pump forward with bent elbows. There is no T/A-pose wing (wrist sideways offset about 0).
- The wall (f1061-1246): it towers over the palms and the hotel, with foam running down its face. The family runs toward the camera and leaves the bottom of the frame at f1224. Nobody is shown hit.
- Flood (f1251-1500): the camera rides up the road, and the houses tilt and go under. The water drains to rubble and the standing mosque (f1621-1700).
- End (f1725-2066): the family faces the camera at golden hour with the ruins and the mosque behind them. The logo on the boy's tee reads at f1741-1800.

## Still failing (exact frames, film timeline)
1. f501-620: 'a wave heading for the shore' is a thin dark line on the horizon over empty sand. It is a near-static hold of about 2 s.
2. f626-746: the aerial over the sea shows the wave as a thin band, and a sun-glint blob sits at the bottom of the frame (f676-731).
3. f766-886: the cut-away still reads as a flat colour diagram. At f881-886 the block's end edge shows. It does not read as underwater.
4. f891-1011: the wave approaches as a band across the frame. The camera barely moves, so it holds for about 2 s.
5. f1806-1876: Dad is cut by the right frame edge.
6. f1901-2066: the family stands nearly still in the wide (only head and breathing motion).
7. Look limits: the flat blotchy ground and road materials, and the flood is a flat plane.

## What a next round would need (director's call)
- Re-stage beats 4-6 so the wave comes much closer, for example a low skim over the water toward the wave's face (f503-746 and f891-1011).
- Replace the cut-away with a sculpted, textured block with a water column, or cut it.
- Widen the end close-ups, and give the family a gesture such as Mom pulling the girl close.

## Script checks on the exact packed file
- clip_scan (step 6): **0 bad ranges**.
- limb_check (step 4): **0** ARMBODY, ARMBACK or PROPHEAD.
- qa_check (step 6, with beats.json):
  - EMPTY 200: the frames with no people (open sea, the cut-away, the flood). This confirms item 1-4 above.
  - PROPMOVE 153: the debris carried by the water, as intended.
  - FAN 46 (f43-451): the 'relaxed' finger spread on the hanging hands during the beach beats. I need to look at it in a close render.
  - CLAW 2 (f55, f433): Dad's hands. f433 is his point.
  - INSIDE 1 (f883): the camera passes the cut-away block's end (the same as item 3).
  - CAMJUMP 1 (f574): the fast swing from the horizon back to the faces.
- The render check (factory-startup open, 3 full-res test frames) was not run: the film is not PASS, so no .blend is delivered.
