# IronRodHead_v003: Phase 2 (built to the client VO)

B12 "Iron Rod Through The Head" (Phineas Gage, 1848). Built straight to the VO word frames (`beats.json`,
`review/vo.words.json` from `pipeline/transcribe.py`), with nothing time-stretched. Source version `IronRodHead_v001` (P1) is untouched.

- `IronRodHead_v003_60fps.blend`: frames 1–1909, 1080×1920, 60 fps (see SETTINGS.md)
- `IronRodHead_v003_VO.mp3`: client VO
- `beats.json`: shot start frames = 1 + round(word seconds × 60)
- `review/preview.mp4`: every 5th frame, 270×480, Cycles 4 samples, with the VO
- `review/*.json`: clip_scan, qa_check, limb_check, body_prop_cross on this exact file
- `scripts/`: rebuild (`01_chars.py` → `02_sets.py` → `03_anim.py`; timing in `timing.py`)

Shots (VO words): S01 "In 1848" · S02 "a huge iron rod" · S03 "blasted" · S04 "(man's) face and skull" ·
S05 "while he was working on a railroad" · S06 "It entered below his left eye" · S08 "shot out through the top of his head" ·
S09 "Somehow, he stayed conscious" · S11 "and survived. But afterward," · S12 "wasn't really the same person anymore" ·
S13 "You see, the rod destroyed part of" · S14 "frontal lobe" · S15 "controls things like judgment" · S16 "and self-control" ·
S18 "After the accident, his personality" · S19 "completely changed" · S20 "He became impulsive" ·
S21 "unpredictable, and difficult to" · S22 "control".
(S07, S10 and S17 from P1 were dropped: the final VO has no "behind his eye", "removed" or "damaged" beat.)

Logo: DA KRAS FILMS on the supply crate, S01 only (whole, flat-on at the end of the crane). It is framed out of S12 and S11.
