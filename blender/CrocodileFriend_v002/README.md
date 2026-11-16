# CrocodileFriend_v002 — B28 "His Best Friend Was A Crocodile", built to the client VO

- `CrocodileFriend_v002_60fps.blend`: farm package (80.7 MB, everything packed), frames 1–1895
- `CrocodileFriend_v002_VO.mp3` + `CrocodileFriend_v002_VO.words.json` (faster-whisper word times)
- `beats.json`: beat frames = 1 + round(word_s × 60)
- `review/preview.mp4`: full moving preview (every 5th frame, 270×480, Cycles 4 spp + OIDN) from this exact package, with the VO;
  `review/prev/pages/` contact pages; check outputs `review/*.json`

Built from `CrocodileFriend_v001` (scripts there): the P1 clips are **trimmed** at 1× to the VO word frames
(`scripts/06_to_vo.py`, no time-stretch), the 21 shot cameras are baked into one camera with hard cuts,
textures except the hero man / croc / eyes / logo / portrait are reduced to 512 px (`scripts/07_shrink.py`).
Shots S02, S15, S17, S21 are left out (they would have been under 0.8 s at the VO pace).

| Frames | Shot | VO |
|---|---|---|
| 1–138 | S01 river pull | He found a dying crocodile on the riverbank |
| 139–194 | S03 drag home | and brought it home |
| 195–299 | S04 treat (logo crate) | to treat its injuries |
| 300–427 | S05 pond, tracking | For six months, he secretly kept it |
| 428–541 | S06 croc swims | in a pond behind his house |
| 542–656 | S07 feed (bucket, meat on palm, toss) | feeding it around nine pounds of meat |
| 657–737 | S08 croc rises | every day |
| 738–815 | S09 night, sleeping beside it | He even slept beside it |
| 816–985 | S10 night close | because he believed affection would help it recover |
| 986–1156 | S11 points to the wild | When he finally tried releasing it back into the wild |
| 1157–1291 | S12 croc turns back | the crocodile refused to leave |
| 1292–1369 | S13 comes back, hand on its head | Instead, it stayed with him |
| 1370–1487 | S14 walking together | for more than 20 years |
| 1488–1592 | S16 show for tourists (logo sign) | They even performed shows together |
| 1593–1696 | S18 croc died, he kneels | and when the crocodile died |
| 1697–1784 | S19 portrait + flowers | the man held a public funeral |
| 1785–1895 | S20 he sings, guests | and sang for his friend |

## Review (exact package, Nov 16)
- Preview watched start to finish (all 379 frames, every page); changed ranges were re-rendered from the final package and spliced.
- `clip_scan`: 0 bad ranges.
- `qa_check`: CAMJUMP 16 = the 16 hard cuts. EMPTY = croc-only or portrait shots that the VO names (S12 "the crocodile refused", S19 "public funeral") plus wide shots where the man is small (S10, S13). FAN/CLAW S11 = the pointing hand (index straight by design). PROPMOVE S07 = the thrown meat in flight after release. BACKHEAD S05 = 1 sample in the walking track.
- `limb_check`: ARMBODY = 2-point upper-arm hits at the shoulder (the known false positive in LESSONS §4) everywhere, plus 3–5 points on the raised waving arm in S16 (armpit region; it reads clean in the preview). ARMBACK S09/S10 = his arm resting beside his head while lying on his back.
- `body_prop_cross` (step 3; croc body, bucket, meat, rail, crate, easel, sign, portrait; all characters): **0 visible crossings**.
