# Delivery checklist (after the voiceover arrives)

1. Timings from the VO word times (edit/align); bake every shot (`tools/bake_chapter.py`), seconds from the VO cuts.
2. Last-frame check of heads/arms (`tools/lastframe.py`), hand crops (`tools/hands_all.sh`, `tools/hand_sheet.py`).
3. Day-brightness check: mean luminance of every DAY shot >= ~0.18 and not clearly below its plain render.
4. Title cards: shared `title_card.py` style (2-line wrap, soft scrim, one PNG per title; cherry-picks a5e97a4 b34ce08).
   Intro lead 2.5 s; every chapter >= 3.0 s of picture under its title before the voice.
5. CHAPTER-WISE delivery (the person, Nov 13; replaces the one-film file): one farm-ready .blend per part:
   - intro, with the Seldom sting at its end after a fade; then one per chapter (ch1, ch2, ch3);
   - each part's frame range starts at 1, with its own fade in and fade out;
   - each part has its own audio pair (with voice / without voice) matching its picture exactly;
   - output JPEG quality 92 (not PNG);
   - farm-ready: FilmCam, packed fonts, 32 samples adaptive 0.05 + denoise, film_transparent off.
   (`scenes/make_master_kih.py` is the per-part base; `scenes/make_film_kih.py` has the sting + fade code to reuse.)
6. Size (Banker lesson, 9.8 GB -> 2.2 GB): unpack textures into ONE shared deduped folder (<= 2K), share identical
   meshes across shot files, measure peak RAM opening the master, zip into <= 380 MB parts with one shared top folder
   plus a MERGE .bat.
7. Do not render the film.
