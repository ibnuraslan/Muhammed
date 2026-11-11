# Thumbnails

Image only: no words, logos or lettering (the person adds the title). 16:9, 3840×2160 plus a 1280×720 copy.

## House rules for thumbnails
- One bold idea, one or two subjects, big in frame, strong silhouettes.
- Leave about a third of the frame clean and dark (left or right) for the title.
- Punchier than the films: hard key, rim light, deep shadow, one saturated accent (red or green) in a cool, dark frame.
- Same CG world as the film (reuse its sets and `people.py`), Poly Haven assets for props and furniture.
- Faces: three-quarter, lit, with a guarded or worried look. No hand or skin macros.

## Tools (`nvidia/scenes/`)
- `thumb.py <name> [--variant V] [--pct P] [--samples S] [--out DIR]` renders `th_<name>.py` (full = `--pct 100 --samples 256`).
- `thumbkit.py` shared helpers: lights (`spot`, `soft`, `point`, `light_only`), posing (`stand`, `sit_on`, `look_at`,
  `gaze`), props (`phone`, `rain_curtains`, `glow_card`, `asset` for Poly Haven, `surface_z`), `strip_lettering()`
  (removes sign text from reused film sets).
- `contact.py` labelled review sheet with a phone-size inset per tile; `render_round.sh` renders all concepts + sheet.
- A thumbnail module returns `ctx` with `cam=(loc, target, lens)`, `focus`, `fstop` and optional `shift`.

```bash
cd projects/thumbnails/nvidia
PYTHONPATH=scenes:../../../nvidia_doc/scenes python scenes/thumb.py watched --pct 20 --samples 12 --out out/test
```

Timing on the 4-core cloud CPU: 20 %/12 samples ≈ 2–4 min; 50 %/64 ≈ 17 min; full 4K/256 ≈ 4–5 h per image.

## New film
Copy `nvidia/` to `<film>/`, put the film's scenes on `PYTHONPATH`, write new `th_*.py`. Renders go in `out/`
(git-ignored); only the chosen finals go in `<film>/final/`.
