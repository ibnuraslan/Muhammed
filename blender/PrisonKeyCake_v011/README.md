# PrisonKeyCake_v011: from-scratch rebuild of batch 1 film 06 (client-approved round 4)

Render frames **1–1836** at 60 fps (30.6 s), timed to the voiceover `PrisonKeyCake_v011_VO.mp3`, the same recording as v010. The voiceover is packed in the file. Farm settings are in `SETTINGS.md`, credits in `CREDITS.md`, and the review history in `review/` (CHECK1–CHECK5).

The client approved this round-4 build as it is (relayed by the director). The packed file was made from exactly the build that rendered `review/preview.mp4`, with no changes.

## What it is
- **Camera:** one continuous move, with no cuts. Scene changes happen inside the move:
  - a push into the candle flame, which glows and opens on the prison gate's torch (frame 341)
  - a matched cake close-up that carries the cake from the workshop to the cell (800)
  - a press-camera flash that jumps to the government steps years later (1622)
- **People:** three MPFB characters (the prisoner, the visitor and the locksmith) with real MakeHuman garments:
  - prisoner: striped shirt and jeans; years later, a suit
  - visitor: blouse and skirt
  - locksmith: work overalls
- **Story, in voiceover order:**
  1. He presses the brass master key into red wax.
  2. The visitor carries the mould out through the prison gate with her basket.
  3. The allies pour orange molten metal into a sand mould, and the copy goes into a cake (a close-up, with the hand out of frame).
  4. The cut cake sits on his cell shelf, and he pulls the key out.
  5. The key jams in the lock (a close-up of his fingers on the key).
  6. He makes a second impression while the candle burns down.
  7. The second key turns.
  8. He opens the door, unlocks the corridor gate and walks out through the small door in the prison gate.
  9. Years later he waves from the government steps with both allies and the tricolour flags.
- **Logo:** DA KRAS FILMS on a large hanging sign over the lane (frames ~400–480) and on the board inside the workshop (~700–760).
- **Build:** `scripts/01_build.py` (sets, people, props, look), then `scripts/02_animate.py` with `02b_story.py` (acting and props) and `02c_camera.py` (camera, glows, sky, VO), then `pipeline/package_for_farm.py`. The camera audit is `scripts/camcheck.py`.

## Known limits (accepted by the client with this round; listed in review/CHECK5.md)
- The second key turn (1300–1326) and the gate unlock (1420–1450) are partly covered by his fist.
- Brief blockers or wall frames remain at 306–336, 650–690, 700–785, 890–920, 1046–1064 and 1346–1360.
- The finale is a near-locked wide shot with small faces. The flags are cropped at the edges.

## Render check: PASS
Run on the exact delivered file, `PrisonKeyCake_v011_60fps.blend` (67 MB), opened with `blender --factory-startup -b` (Blender 5.2.2, no add-ons):
- It opens with no errors or warnings.
- No linked libraries, no unpacked or missing images, no drivers.
- The VO sound is packed, and the VO strip is at frame 1.
- One camera, `CAM_Film`, with no camera markers.
- 1080 × 1920 at 100 %, 60 fps (fps_base 1.0), frames 1–1836.
- PNG output to `//render/PrisonKeyCake_v011_####.png`.
- Filmic, High Contrast. Cycles 64 adaptive samples, OIDN, persistent data on.
- Full-resolution test frames:

| Frame | Render time | Content |
|---|---|---|
| 1 | 234 s | the cell |
| 918 | 222 s | him with the cut cake |
| 1836 | 175 s | the finale on the steps |

  None is black, empty or pink. The times are measured on this CPU-only cloud machine (4 cores); a farm GPU or CPU node is much faster.
- Moving preview: `review/preview.mp4` (every 5th frame, 270×480, with the VO), watched start to finish.
