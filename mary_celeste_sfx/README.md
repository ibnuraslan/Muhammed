# Mary Celeste: SFX and ambience (no VO, no music)

## Deliverables (`audio/`)
| file | length | loudness |
|---|---|---|
| MaryCeleste_FULL_SFX.mp3 | 715.833 s = 17180 fr @ 24 fps (P1+P2+P3+P4+P5 butted, no gaps) | −20.0 LUFS integrated, −1.0 dBTP |
| MaryCeleste_P1_SFX.mp3 | 157.833 s (3788 fr) | −20 LUFS |
| MaryCeleste_P2_SFX.mp3 | 152.625 s (3663 fr) | −20 LUFS |
| MaryCeleste_P3_SFX.mp3 | 139.833 s (3356 fr) | −20 LUFS |
| MaryCeleste_P4_SFX.mp3 | 164.625 s (3951 fr) | −20 LUFS |
| MaryCeleste_P5_SFX.mp3 | 100.917 s (2422 fr) | −20 LUFS |

48 kHz stereo, 320 kbps MP3; the decoded sample counts are exact (34,360,000 for the full film). Second 0 of each file = MASTER frame 1 of that part.
Shots are placed from each part's `vo/vo_timings.json`, the same file each part's `build_master.py` uses to lay out its MASTER strips.
Cue sheets: `cues/` (bed layers per shot, silences, every spot effect with its time).

## How it is built
- Beds per scene (`locs.py`): looped CC0 field recordings (`r_*`) layered with synthesised layers, crossfaded 0.25 s at cuts.
- Spot effects per shot (`spec_pN.py`): CC0 one-shots sliced at transients plus synthesised bodies; tension hits (CC0 cinematic booms) and real silences before reveals.
- Sources and licences are in `CREDITS.txt`: every recording is Freesound CC0 1.0, verified on its page.

Rebuild: fetch the recordings (`tools/fetch.py tools/pick.json`, after `tools/batch.py` search results), then
`NO_MIX=1 python3 -I engine.py spec_p4.py <vo_timings.json> <VO.mp3> 3951 out/P4 P4` (drop NO_MIX to also get a VO-ducked check mix).
