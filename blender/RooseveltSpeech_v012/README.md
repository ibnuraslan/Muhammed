# RooseveltSpeech_v012: the from-scratch rebuild (batch 1, film 24)

**Status: ON HOLD. Not delivered.** After the two allowed fix rounds, my own watch and a fresh reviewer both rate the last preview FAIL. See `review/CHECK3.md` for the exact frames. The .blend is not pushed (no "Render check: PASS" yet). The film needs the director's OK for another round.

Built to the client's VO (v011 timing, frames 1-1307 at 60 fps), with one continuous camera and the set changes inside short flashes:
- **Street (f1-389):** a night street outside a hotel in 1912. The gunman fires from the foreground and the bullet flies in slow motion into Roosevelt's chest. He jolts, feels for the wound, then steadies. Onlookers stand around him. The DA KRAS FILMS hotel sign and the car door panel carry the logo.
- **Cutaway (f390-1027):** a real-scale cut block of the chest wall: coat, the folded inked speech, a steel glasses case with spectacles inside, then shirt, skin, fat, pectoral muscle, ribs, pleura and lung. One geometry-nodes cut per layer is driven by the keyed `TipCtl` empty. The bullet stops in the muscle.
- **Hall (f1028-1307):** he holds up the holed speech, then raises his fist. There are flags, bunting, a clock and a cheering audience, and the logo is on the lectern.

Scripts: `scripts/01_build.py` (characters, sets), `02_animate.py` (acting, bullet, camera, VO), `03_package.py` (pack). The assets are CC0 MakeHuman/MPFB plus CC-BY Sketchfab models (Ford Model T, facade scan, street lamp, clock), the same models credited in v011's CREDITS.md.
