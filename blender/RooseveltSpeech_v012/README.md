# RooseveltSpeech_v012: the from-scratch rebuild (batch 1, film 24)

**Status: delivered for the director's review (not yet marked READY).** This is the director-approved final round, and it passes the render check below. Watch `review/preview.mp4` before rendering. The known residuals are in `review/CHECK4.md`. The earlier rounds are in CHECK1 to CHECK3.

Built to the client's VO (the v011 timing), frames **1–1307** at 60 fps, with one continuous camera. The render sheet is `SETTINGS.md`, attribution is in `CREDITS.md`, and the scripts are in `scripts/` (01 build, 02 animate, 03 package).

## The film
- **Night street:** in 1912, outside a hotel with the DA KRAS FILMS sign, Roosevelt waves beside his car with onlookers around him. Over the gunman's shoulder, the nickel revolver fires with a big flash. The bullet flies in slow motion into his chest. He jolts, feels for the wound and steadies.
- **The cutaway:** the camera pushes onto the coat hole and lands in a real-scale cut of his chest wall. The bullet tears through the folded, inked speech and the steel glasses case (spectacles inside). It slows through shirt, skin and fat and stops in the chest muscle above the ribs and lung.
- **The hall:** he holds up the holed speech, then raises his fist. There are flags, bunting, a spinning clock and a cheering crowd, and the lectern carries the logo.

## Render check: PASS
On the exact file `RooseveltSpeech_v012_60fps.blend` (53 MB), opened with `blender --factory-startup -b`:
- No linked libraries, no unpacked images, and the VO sound is packed. No drivers and no Python. No errors or warnings: the six empty image nodes on the MakeHuman fedora materials were removed in packaging, and a recheck logs nothing.
- Camera `CAM_Film`, 1080×1920 at 100 %, 60 fps, frames 1–1307, PNG to `//render/RooseveltSpeech_v012_####.png`, with the VO strip at frame 1.
- Test frames at full resolution with 64 adaptive samples, on a 4-core CPU with no GPU: f20 in 177 s, f650 in 197 s and f1240 in 281 s. None is black, empty or pink.
