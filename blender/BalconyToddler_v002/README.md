# BalconyToddler_v002: built to your voiceover (IN REVIEW, not yet approved)

ConnectB35, branch `claude/connectB35-balcony-toddler`. A toddler slips through the floor bars of a 2nd-floor balcony cage and his
head gets stuck; people stack chairs on a table, a man climbs up and holds the boy's legs to take the weight off his neck until his
grandmother pulls him back inside. Calm faces, no arrows or highlights.

- Built from the director-approved P1 (`BalconyToddler_v001`, commit ddad4d5), plus the Phase-2 note: grandma has short grey hair
  (no scarf) and stronger face fill.
- Every shot plays its own 1× animation from its start; the VO cut only trims shots (keys shifted, never scaled). Beat frames are
  `1 + round(word start × 60)` from `pipeline/transcribe.py` (`beats.json`).
- One logo placement: DA KRAS FILMS on the cafe sign across the street (shot 11).

Render: frames **1–1751** at 60 fps (29.2 s). Settings: `SETTINGS.md`. Credits: `CREDITS.md`. Preview: `review/preview.mp4`.
Rebuild: `scripts/01_lib.py` → `02_build.py` (exec's `03_shots.py`, `04_finish.py`) → `05_vo_cut.py` → `06_slim.py` → `pipeline/package_for_farm.py`.
