# Tsunami2004_v013: the from-scratch rebuild (batch 1, film 25)

**Status: for director review (round 3, approved by the director with the client's authority).** Watch `review/preview.mp4`, the full moving preview of this exact file, before it goes to the client. My round-3 notes are in `review/CHECK4.md`.

One family, one beach town, one continuous camera with no cuts. Built to the client's VO (the v012 timing), frames **1–2066** at 60 fps. The render sheet is `SETTINGS.md` and attribution is in `CREDITS.md`. The scripts are in `scripts/`: 00 garment textures, 01 build, 02 animate, 03 package, plus the shared libs.

## The film
- **The sea pulls back (f1–259):** the water drains from the family's feet, and the camera rides low over the retreating sea to the bare floor (stranded fish flopping, coral, a boat on its side). The family walks out, puzzled, and the boy points at a fish.
- **They see it (f395–648):** Dad points and shouts, and the family turns and runs. The camera sets off over the sea floor and the water toward the white line of the wave.
- **A massive tsunami (f648–1025):** the camera skims the water up to the wave face, rises beside the crest and backs off in front of it as it grows. The earthquake cut-away was cut, as the director chose.
- **Up to 100 feet (f1025–1217):** the camera flies back over the family as they run up the road, faces to camera, with the wall towering over the palms and the hotel. They leave the bottom of the frame at f1224, before the impact. Nobody is ever shown being hit.
- **It hits the coast, the town goes (f1217–1621):** the palms snap, boats and cars are carried off, the camera rides up the road ahead of the surge, and the houses tilt and go under.
- **Nothing but rubble (f1621–2066):** the brown water drains to rubble and the standing mosque. At golden hour the family stands on the high ground, faces to camera, with the ruins and the mosque behind them, as the camera slowly cranes back.

## The client's extra lessons
- **One model per character:** four MPFB/MakeHuman people with real CC0 garments (shirts, tees, jeans, shorts, shoes), given solidify thickness, and real hair.
- **Arms:** relaxed with bent elbows. In the run the elbow bends on its real hinge, so the forearms pump forward and never wing out.
- **Feet:** planted on the real ground with IK.
- **Props:** nobody holds a prop. Debris moves only with the water.
- **Logo:** DA KRAS FILMS is printed on the boy's tee (in close-up at f1–60 and f1741–1860) and on the hotel's roof sign.

## Render check: PASS
On the exact file `Tsunami2004_v013_60fps.blend` (90 MB), opened with `blender --factory-startup -b`:
- No linked libraries, no unpacked images, and the VO sound is packed.
- No drivers, no Python, and no errors or warnings, apart from the no-GPU CUEW notice and one Blender deprecation notice from the check script itself.
- Camera `CAM_Film`, 1080×1920 at 100 %, 60 fps, frames 1–2066, PNG to `//render/Tsunami2004_v013_####.png`, and the VO strip at frame 1.
- Test frames at full resolution (adaptive, max 28 samples, OIDN) on a 4-core CPU with no GPU:
  - f20 in 94.2 s
  - f1062 in 85.8 s
  - f1840 in 79.3 s

  All are under 120 s, and none is black, empty or pink.
- Checks on the packed file before round 3 (the round-3 changes are camera, sun, materials and removing the cut-away):
  - clip_scan: 0 bad ranges.
  - limb_check: 0 ARMBODY, ARMBACK or PROPHEAD.
  - qa_check: EMPTY on the people-free sea and flood frames, and PROPMOVE for the debris carried by the water. Details are in `review/CHECK3.md`.
