# B27 ChicagoRaised v002: review notes

## Preview
- `preview.mp4`: every 5th frame (385 frames), 270×480, Cycles 4 spp + OIDN, frame numbers burned in, with the VO, 32.1 s.
  - The full render was made from the final texture state of this package.
  - The last animation-only fixes were re-rendered from the delivered file and spliced in: frames 1–426, 1021–1076, 226–296 and 1306–1426.
- `pages/p01–p08.jpg`: contact pages of every preview frame (50 per page). I watched all of them.

## Director P1 notes, built into this version
1. **Crank grips.** Each palm rests on the grip bar, aligned with the forearm, and is pushed clear of the bar every frame. The shortest worker (W4) is off the crew, so jacks 3 and 4 are unmanned and their cranks stay still. `body_prop_cross` on S1–S7 gives 0 crossings (`bpc_crank.json`). S1 is framed on face and shoulders.
2. **1850s labourers.** Long-sleeve shirts and wool trousers in contrasting colours, with braces and flat caps (five of the seven). The S11 mason wears no cap, so his face reads while he looks down.
3. **S16 town.** A street grid of textured clapboard houses and brick blocks along mud streets, with a church spire.
4. **S18/S20 flood street.** Textured timber houses (doors and windows to the street) and brick shops. The small pink figure is gone; the woman in S20 walks toward camera.
5. **S22 skyline.** Darker teal river, stone-grey textured embankments and a darker ground, with a larger camera move.

## Checks on this package (step 6 unless noted)
- **`clip_scan`: 0 bad ranges.** The last two (Foreman f241, sick man f1315) were fixed and re-checked.
- **`body_prop_cross`:**
  - Crank S1–S7: 0 crossings.
  - S6: book and armchair are seated or resting contacts.
  - S8: fingertips on the pushed timber.
  - S11: fingertips on the wall top.
  - You accepted these as contact.
- **`qa_check`:**
  - EMPTY flags are the camera-only story shots (the building, the swamp, the town aerial, the raised block, the skyline).
  - CAMJUMP flags are the hard cuts.
  - ATTACH flags are a name false positive: the jack caps (`JackCap.*`) get treated as worn caps.
  - PROPMOVE flags the crank grips turning while the palms sit 1–2 cm clear of the bar (needed for 0 crossings), plus the mason's brick.
  - BACKHEAD flags W1 on the last frame of the wide S2 (tiny) and TownMan in profile wading behind the horse (S18).
- **`limb_check`:** W3's 2-point hits are upper-arm points next to the shoulder, the known false positive. Foreman/sick-man hits were fixed (see `limb_check.json`).

## Known issues
- The town and the skyline are simple, low-detail models.
- In S14 the crane over the roof shows the building's balcony side.
- The flood water is opaque muddy brown at specular 0.05 (no sky sheet), so in the wide S21 it reads very flat.
