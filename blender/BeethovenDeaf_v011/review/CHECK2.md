# v011 check 2 (after fix round 1): FAIL (preview only, no .blend pushed)

`preview.mp4` is now the check-2 preview of the packed local build (every 5th frame, 270x480, with the VO). All 6 pages watched.

Fixed since check 1: the hair is mid-grey instead of white; the camera keeps his face in frame for most of the rod ride (267-400); the ear canal is beige, so the red pulse dying at the eardrum (818-900) reads; the ending (1300-1435) now orbits down to his right side with hands, keys, rod and face, so there is no static end hold; the logo reads 19.2-22.5 s.

Still failing (film frames):
1. **Hands, whole film (blocker):** the fingertip pads sit on the key tops (solver: within about 1 mm on 99 % of solved frames). But the middle and ring fingers' knuckles hook down into the black keys behind them. The mesh audit (`scripts/key_contact_check.py`) finds 2-15 mm intrusion on every sampled frame, and at preview size the hands read as fists. Five solver variants were tried this round (palm back or higher, knuckle-clearance cost, freed wrist limits, a free knuckle angle, automatic palm back-off). None kept the pads on the keys and the knuckles clear at the same time, so the check-1 solver was restored for this preview.
   Suggested re-stage: hands framed wider or out of the close shots (LESSONS 2.15), or a hand-keyed arched pianist pose library with the wrist above the key fronts, built and checked on one hand before the film.
2. **1-90 and every face shot:** the mouth around the rod reads as a dark open "O" (6 mm incisal gap; the lips part further than the teeth).
3. **151-196:** the camera is on the clamp and keys with no face in frame (about 0.8 s). **251-330:** his head is cut by the left frame edge.
4. **800-950 ear close-up:** hair cards and the pale skull fill most of the frame; the cochlea and ossicles inside the cutaway are small and low contrast.
5. **Minor:** pulse beads float below the jaw line (450-1000); the rug stripes read busy.

Fix rounds allowed by the brief: one used. Stopping here for the director's decision on the hand staging.
