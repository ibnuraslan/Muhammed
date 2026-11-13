# Thumbnails

Built in Blender from each film's own sets, then finished in Python (grade + text).

```bash
bash pipeline/setup.sh && source ~/render_env/env.sh
# quick concept plate (25-35 %), or full quality (3840x2160, 384 samples, OIDN) without --pct/--samples
PYTHONPATH=nvidia_doc/scenes python thumbnails/tools/thumb.py thumbnails/nvidia/concepts.py chip --pct 35 --samples 32 --out thumbnails/nvidia/plates_quick
python thumbnails/nvidia/make.py sheet          # concept sheet with the 320x180 phone check
python thumbnails/nvidia/make.py final chip     # final, with and without text
```

Fonts in `assets/fonts` (Anton, Bebas Neue, Oswald) are from Google Fonts, SIL Open Font License.
Per film: `concepts.py` (cameras, lights), `make.py` (text), `PACKAGING.md` (texts, titles, description).
