# CrocodileFriend_v002b — B28 "His Best Friend Was A Crocodile", built to the client VO

- `CrocodileFriend_v002b_60fps.blend`: farm package (80.7 MB, everything packed), frames 1–1895
- `CrocodileFriend_v002b_VO.mp3` + `CrocodileFriend_v002b_VO.words.json` (faster-whisper word times)
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

## v002b changes (director notes on v002)
1. Real hair: MPFB short01 (dark, textured, with volume) fitted to the man; the flat short02 cap is gone.
2. Sleep (S09/S10): relaxed on his back, knees drawn up, right hand resting on his chest, left palm on the croc's back.
   Slow push-in; a soft blue moonlight fill on his face (keyed on only in the night shots).
3. S06: he stands at the pond bank calling the croc (waving arm), and it swims to him; house behind. S11: camera behind the
   leaving croc, so he faces camera, leaning and pointing to the wild, with a push-in.
4. Sky fill raised on all day and evening shots (shade on faces and the croc lifted); S18 camera raised so the croc's back is in the light.
5. S20: close waist-up on the singer, hand sweeping from his heart to the guests, other arm open; the guest in grey leggings is out of frame.

## Review (exact package, Nov 16)
- Full preview re-rendered from this package after the hair/fill change and watched start to finish; the later fixes
  (S06, S11, S13, S18, S20, sleep) were re-rendered from the final package and spliced. `review/preview.mp4` has the VO.
- `body_prop_cross`: **0 visible crossings**.
- `clip_scan`: S09/S10 739–757 and 781–889 = 29–45 shallow probes where his right palm rests on his chest (contact, reads clean);
  S11 997 = 1 sample of the pointing arm at the shirt.
- `limb_check`: ARMBODY 2-point shoulder false positives; 3 points on the arm resting on his chest (S09/S10) and on the
  hand-on-heart (S20); 3–5 points at the armpit of the waving arm (S16). All read clean in the preview.
- `qa_check`: CAMJUMP 16 = cuts; EMPTY = croc-only / portrait shots the VO names (S12, S19) and the wide framings S10/S13;
  FAN/CLAW S11 = pointing hand; PROPMOVE S07 = thrown meat in flight; BACKHEAD 1 sample in S05.
