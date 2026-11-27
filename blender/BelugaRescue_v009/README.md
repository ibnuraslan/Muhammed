# BelugaRescue_v009: the from-scratch rebuild (batch 1, film 22)

**Status: ON HOLD.** The .blend is pushed on the director's instruction after the render check passed. My watch and a fresh reviewer both mark the film FAIL after 2 fix rounds (see "Known faults"). Watch `review/preview.mp4` before anyone pays for a render.

One diver, one beluga, two spectators, one continuous camera. It is built to the client's VO (the v008 recording; word timings in `BelugaRescue_v009_VO.words.json`), frames **1–1736** at 60 fps, with no retime. The render sheet is `SETTINGS.md`, the credits are in `CREDITS.md`, and the scripts are in `scripts/` (00 tee texture, 01 build, 02 animate, 03 package).

## The film
- **Dive:** from deep in the arctic tank (ice-rock walls, blue mosaic floor, caustics, a rippling surface with ice floes), she dives in head-first with a cloud of air bubbles and glides down.
- **The cramp (f300–480):** she lands on the floor with feet planted, then her right knee jerks up, both hands clutch the calf, and a red pulse throbs on the leggings over it.
- **Can't swim back up / drowning (f480–683):** she pushes off and claws upward, then panics with bubbles escaping her mouth in close-up.
- **The beluga (f683–1100):** it notices her, then swims side-on past the viewing window where two spectators watch (the "smart and playful" vignette, with a bubble ring). An eye close-up follows, then it turns to her.
- **The rescue (f1100–1530):** it takes her pointed foot gently into its open mouth and pushes her up toward the light.
- **The surface (f1531–1736):** the camera rises through the surface. She surfaces in murky deep water, gasping, with the beluga's head beside her and the DA KRAS FILMS banner on the far rim.

## Known faults (after 2 fix rounds; preview frames)
- f1251–1460: the lift is a slow, mostly static wide. The whale's head fills the lower frame, and she is small with stiff arms. The foot-in-mouth can read as standing on the whale's head.
- f1536–1736: only her head is above the murky water. The gasp is weak, the head sits at the left edge, and the beluga is cut off at the right.
- f251–316 and f540–683: stiff upright floats with A-pose arms, which read as standing or calm rather than drowning.
- f1501–1526: a milky frame at the surface from below.
- f330–470: her fingertips press into the calf (clip_scan bad range 331–469).
- f1000–1040: whale-only close-up, with no human face.

## Checks on this package
- clip_scan: bad ranges 331–469 (the cramp hands' fingertips in the calf) and 1573–1579.
- qa_check: INSIDE when looking up at the water surface from below (the back-facing water sheet, a false positive), EMPTY in the whale-only frames f877–1039, and PROPMOVE for the swimming whale.
- limb_check ARMBODY: upper-arm points near the shoulder (the documented false positive), 908 samples.
- body_prop_cross: her right foot and lower leg inside the beluga's mouth at f1169–1540 (the intended "leg in its mouth" contact).

## Render check: PASS
On the exact file `BelugaRescue_v009_60fps.blend` (42 MB), opened with `blender --factory-startup -b`:
- No linked libraries, no unpacked images, and the VO sound is packed. No drivers or text blocks. No errors or warnings, apart from one Blender deprecation notice from the check script itself.
- Camera `CAM_Film`, 1080×1920 at 100 %, 60 fps, frames 1–1736, PNG to `//render/BelugaRescue_v009_####.png`, and the VO strip at frame 1.
- Test frames at full resolution, 64 adaptive samples, on a 4-core CPU with no GPU: f20 in 644 s, f900 in 547 s and f1700 in 297 s. None is black, empty or pink (mean RGB about 65/110/129).
