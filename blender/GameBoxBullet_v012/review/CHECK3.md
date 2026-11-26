# v012 check 3 (round-2 build; fresh harsh reviewer + my watch): FAIL. Both allowed fix rounds are used, so I stopped.
`review/preview.mp4` and `review/page_p01-p06.jpg` are this check: every 5th frame of the packed local build, 270x480, with the VO.

## Remaining faults (film frames)
1. **Bullet continuity, f236-481.** As the camera rises to his face, the slow-motion bullet drops down the frame past his knees and feet (f241-251). It is then off-screen until it re-enters at chest height (about f476). It reads as missing him and then teleporting.
   *Fix:* keep the bullet in frame on its way to his face. Frame the front medium from the wall side of the bullet path, so the bullet stays in the lower foreground, or cut the medium to about 1 s.
2. **Shooter, f1-11.** His eyes still read as glowing white slits at preview size. The orange muzzle flash at f11 reads as a floating beige mesh.
   *Fix:* the eye material on the dark skin needs the scleras toned down and a lit face. The flash should be a thin cone of emissive streaks, not a faceted blob.
3. **Faceless stretches.**
   - f11-111, about 1.7 s: the bullet over the lawn (it fills the frame, but no person is in shot).
   - f141-171, about 0.5 s.
   - f666-856, about 3.2 s: macro of the box top.
   - f921-1051, about 2.2 s: macro of the box top.

   There are near-static stretches on the box top at f751-776 and f951-996.
   *Fix:* cut each macro to 1 s or less and return to his face in between.
4. **Debris reads as floating, f651-701 and f801-906.** The burst chunks rise slowly in slow motion.
   *Fix:* small fast shards that leave the frame within 10 frames, no large blocks.
5. **Hands.**
   - f461-546: his right hand is fanned flat on the box side in the low profile.
   - f686-746: in the top views his fingers show past the box wall with no arm in frame.
6. **Face.**
   - f916-921 and f1046-1056: the head is cut by the frame edge (transitions).
   - f1061-1131: the face is mostly hidden by the bowed head.
   - f1186-1291: several eye closures read as squints or a twitch.
   - The ending face is neutral: the rig smile read as a frown or bared teeth, so it was removed, and there is no emotional beat.
7. **Bullet macros are small** compared with the client-praised BellyFat v018. There the bullet fills about 1/3 of the frame. Here, in the stopped-halfway shot, the bullet is a small speck (f1001-1031).

## Reviewer items I checked and do not count as faults
- "The box changes from a closed top to an open tray": the box is always open-topped. The profile and front shots are below the rim. A wider top reveal before the hit would remove the misread.
- "A one-eyed wink at f1251": a close render shows both lids closed symmetrically. At 3/4 and preview size it reads as a wink, so the item stands as a read problem (6).

## Clean in check 3
- The one bullet and the one box: no swaps or size pops in the objects themselves.
- He sits ON the sofa.
- The garments are real CC0 MakeHuman t-shirt and cargo pants: no crotch hole, no skin through the cloth (close renders).
- The crack spreads from the hole.
- The logo is readable for more than 1.5 s: on the box f121-446, and on the poster f1151-1311.
- The colour is saturated, not grey.
