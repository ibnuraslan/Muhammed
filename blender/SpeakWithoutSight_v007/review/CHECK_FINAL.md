# SpeakWithoutSight v007: final check (after fix round 2 of 2): FAIL

Preview: `review/preview.mp4` (270x480, every 5th frame, with VO); contact pages `review/pages/p01-p07.jpg`. Film frames 1-1645.

## Script checks (on the packed file)
- clip_scan: 0 bad ranges (was 463-901 after round 1).
- qa_check: CLAW 2 (f1453, f1507 transitions); FAN 99 = the intended two-finger lip touch; PROPMOVE 157 = the pulse dots / ripples (FX, no prop).
- limb_check: ARMBODY 14: teacher arm.L 2 pts f381-425 (near the shoulder, likely the known false positive, not confirmed), girl arm.R f445-449.
- body_prop_cross: visible crossings remain: thighs into the settee seat, calves through the seat front / rail, the teacher's skirt into the seat, the girl's shins into the footstool. NOT clean.

## Fresh reviewer (harsh) verdict: FAIL, all 7 pages
Reject:
1. f1-56: the girl's shins sink into the footstool.
2. f1-146: wardrobe reads modern (teacher's knee skirt with bare legs and socks; the girl in jeans), not 1880s.
3. f126-346: the teacher's face leaves the left edge; only the girl is readable for about 3.5 s.
4. f501-596, f751-896: the girl's face is cut by the right edge.
5. f601-611: the girl's fingers hover in front of the throat (not touching).
6. f1176-1246: the girl's sleeve sweeps across the frame with no readable face for about 1 s.
7. f1251-1306: the teacher's face is cut out while the girl's arm reaches out of frame.
8. f1551-1641: the finale frames the teacher out on the left and cuts the girl at the right; no readable reaction; near-static end.
Minor: near-static girl close-up f191-311; hand floats f421-446; the extreme close-up crops the teacher's head (f651-706) with a gaping mouth; a splayed palm in transit f906-921; a static time-lapse wide f1351-1456 and the teacher's eyes reading white there; a raised claw-ish hand f1466; the throat glow on the girl f1521+ reads as a ring.

## What would fix it (not done: the 2-round limit is reached)
- Camera: re-frame the whole path so both faces sit inside the frame (a wider lens or framing on the pair midpoint) at f126-346, 501-896, 1176-1306 and 1497-1645, with a final push-in to both faces.
- Seating: a deeper/softer seat model, or raise both pelvises about 1.5 cm and move the knees 3 cm further past the seat front; lower the stool 1 cm.
- Wardrobe: period dresses need a real long-skirt garment (MPFB has none built in; fetch from the MakeHuman community library).

## Director-approved restage round (after the FAIL above): stopped at the stills stage, no preview
Evidence: `review/restage_stills_attempt2.jpg` (12 film-camera stills).
- Done in the scripts: a lower settee (seat 0.34), the rail set back, both in blouses, the camera re-framed on the pair (both faces in every still), fingertips 6-7 mm off the throat (bone axis, the pads touch).
- Not acceptable, so no preview was rendered and no .blend pushed:
  - the generated long skirts (the convex hull of the seated legs, remeshed) read as stiff solid blobs or pillows (the earlier rejected "rigid lap blob" fault);
  - the girl (about 1.22 m) cannot reach the floor from the seat: feet 95 mm short, so the solver perches her nearly standing (hip z 0.63).
- What it needs: a real cloth-simulated long skirt (a tube draped from the standing pose into the seat, colliding with legs and seat), or a downloaded period dress asset; and for the girl, a child-height seat (a low chair about 0.28 m) or her feet on a footstool, which the director's note ruled out.

## Director's final round (blouses + long trousers, the girl's feet on a footstool fitted to her soles): FAIL
Preview `review/preview.mp4` and pages `review/pages/` are from this round. The .blend is not pushed.
- Fixed since round 2: both faces in frame throughout (fresh reviewer: "faces stay in frame"); no sinking or floating on the settee/footstool visible; no clothing faults; no arms through torsos visible; the time-lapse is clean.
- Scripts: clip_scan bad 505-553, 577-601, 619-733, 835-895 (the girl's hand vs the teacher: the palm/heel at the collar); body_prop_cross still counts thigh edges under the seat-cushion surface (about 1 cm, soft-seat compression; the reviewer saw no sinking); limb ARMBODY: girl arm.R 449-909 (2-3 pts near the shoulder, likely the known false positive), teacher arm.L 381-425; CLAW single frames 1249, 1453, 1507.
- Fresh reviewer rejects: f1-146 near-static opening wide (about 2.4 s); f561-571 the hand slides off the throat onto the jaw/cheek; f606-616 the hand lifts off the throat on the ripple beat. Minors: the trapped-beat light drop at f166-176 / f326-341 reads as a pop; f456 hover; f916 an open hand in transit; possible fingertip-cheek graze f1001-1219; the teacher's eyes are bright; the girl's throat glow reads as a blotch.
- Remaining fixes (not done; the final round is used): key the throat hand every 2 frames with a palm-skin clearance test (the 6-frame keys let the IK drift between keys); add an action (the teacher turning to the girl and lifting her hand into frame) plus a faster push in f1-146; ramp the trapped-beat dim over 40 frames.
