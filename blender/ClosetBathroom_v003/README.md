# ClosetBathroom_v003: "Closet turned into a bathroom" (B19), built to the client VO

**ConnectB19** · branch `claude/connectB19-closet-bathroom` · Phase 2 package (for director review, not yet delivered).

- **Package:** `ClosetBathroom_v003_60fps.blend` (75 MB, everything packed) plus `ClosetBathroom_v003_VO.mp3`.
- **Frames:** 1–1881 at 60 fps (31.35 s). Each shot starts on its VO word: frame = `1 + round(seconds × 60)` from `review/VO.words.json`, the faster-whisper transcript. The shot list is in `beats.json` and `shots.json`.
- **Preview:** `review/preview.mp4`, every 5th frame at 270×480 with the VO. It was rendered from this exact package and watched start to finish, page by page.
  - S14 (frames 966–1069) was re-staged after watching. That range was re-rendered from the final package and spliced in; no other frames changed.

**Shots (VO words):**

| Shot | Frames | VO words | What's on screen |
|---|---|---|---|
| S01 | 1 | He opened what he remembered as | The door swings open (back view, no hand contact) |
| S02 | 104 | his closet, | Over the shoulder into the doorway |
| S03 | 164 | but found a bathroom instead. | Push-in on the bathroom |
| S04 | 283 | Confused, | Close-up |
| S05 | 343 | he asked his roommates | Palms up |
| S06 | 398 | what happened. | Arm sweeps back to the doorway |
| S07 | 464 | They stared at him and | Ray shrugs; Ken steps in and shrugs |
| S08 | 529 | insisted it had | Ray waves it off |
| S09 | 601 | always been a bathroom. | Two-shot at the door |
| S10 | 686 | At first, he assumed | Close-up, suspicious |
| S11 | 771 | they were pulling some elaborate prank. | Imagined half-converted closet; **logo** on the toilet box |
| S13 | 885 | But as days passed, | He walks back to the door |
| S14 | 966 | he became terrified because | He turns from the doorway, panicked, open hands raised |
| S15 | 1070 | he couldn't even remember what the closet had looked like anymore. | Thought-cloud of the closet breaks apart |
| S16 | 1277 | Thinking he was losing his mind, | Close-up, head shake |
| S17 | 1386 | he finally went to a doctor. | Seated in the clinic |
| S18 | 1514 | Tests revealed a brain tumor, | Doctor points at the scan |
| S19 | 1601 | causing memory loss and hallucinations. | Push-in on the scan |
| S20 | 1701 | The closet | Tom at the doorway turns back |
| S21 | 1779 | had never existed. | Bathroom push-in |

S12 (Ray and Ken nod) is not in this VO cut. It is parked after the film's end.

**Checks on this package (`review/`):**

| Check | Result |
|---|---|
| `clip_scan` | 0 bad ranges |
| `body_prop_cross` | 0 visible crossings over the whole film, 12 props. MPFB helper vertices are skipped (`scripts/body_prop_cross_nohelper.py`). |
| `limb_check` | 355 ARMBODY flags. All are upper-arm axis points 0–3, within 5.2 cm of the shoulder joint: the known false-positive class (Ray and Ken idle, the doctor's raised pointing arm). |
| `qa_check` | Every flag is expected: see below |

**`qa_check` flags explained:**
- **CAMJUMP 18:** the hard cuts.
- **EMPTY:** the bathroom-only shots S03 and S21 and the scan close-up S19, which show what the VO names. Wide shots score low character coverage.
- **PROPMOVE:** the thought-cloud tiles.
- **ATTACH:** a set piece misread as a worn item.
- **BACKHEAD 4:** S01 and S02 are the reference's back view; S14 opens on his back, then he turns.
- **CLAW and FAN on Doc's right hand, 1543–1597:** her pointing hand (index straight, other fingers curled).

**Director notes applied:**
- S07: the roommates act (shrug, glance, step).
- S12: the logo box is no longer cut by the frame edge (the shot is not in this VO cut).
- S17: hips on the seat, knees about 90°, feet flat.

**Rebuild:** `scripts/01_chars.py` → `02_sets.py` → `03_shots.py` → `04_bake.py` → `pipeline/package_for_farm.py`. The CC-BY models are listed in `CREDITS.md`; the GLBs themselves are not committed.
