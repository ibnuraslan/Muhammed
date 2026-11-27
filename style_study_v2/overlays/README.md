# Overlay study: on-screen text and graphics only

- `OVERLAYS.pdf`: one section per category with the best examples and design notes (font, colour, frame, position, and how it animates in and out, with timings).
- `sheet_<video>_<n>.jpg`: per-video contact sheets. Every distinct overlay instance is labelled with its timecode and category (Amy 91, Caylee 85, Noida 74).
- `<category>/`: full-resolution frames (854x480, the source resolution). Files are named `<video>_<MM-SS>_<instance>.jpg`.
- `index.json`: every instance with its time, category and seconds on screen.
- `scripts/`: the detection pipeline. Frames are taken at 2 fps, scored for sharp white and red pixels, then grouped into instances. A Tesseract OCR pass (`ovocr.py`) timed out and was not used. Categories were checked by hand (`categories.py`). In/out timing was measured at 30 fps.
