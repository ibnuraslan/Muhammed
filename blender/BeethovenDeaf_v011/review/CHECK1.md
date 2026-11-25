# v011 check 1: FAIL (preview only, no .blend pushed)

`preview.mp4`: every 5th frame, 270x480, with the VO, rendered from the packed local build. All 6 pages watched.

Working: rod clamped between the incisors and running through the brass collar on the case; rings travel up the rod at one size and speed; x-ray window (skull fitted to the head, rod in the skull's teeth, pulses teeth -> jaw -> ear, skull glow wave); logo readable 19.2-23.9 s; one continuous camera.

Faults (film frames):
- Hands, whole film: the middle-finger knuckles hook down into the black keys (mesh audit: 2-15 mm inside keys); in the small preview the hands read as fists. Cause: palm placed over the keys, so the fingers curl back toward the player.
- 96-111: near-empty frames (wall and rod). 251-346: no face in frame (hands and rod only).
- 1-90: the mouth reads as a dark open "O" around the rod.
- Hair renders near-white and papery.
- 800-950: ear close-up dominated by the red ear canal and by hair.
- 1250-1435: almost the same high framing for 3 s (near-static hold).

Fix round 1: palm moved back in front of the keys plus a knuckle-clearance term in the finger solver, smaller incisal gap and thinner rod, darker grey hair, beige ear canal, camera keys re-aimed so the face stays in frame on the rod ride, ear shots pulled back, ending orbits round to his right side.
