# KidHacker_v002b (B32: The 10-Year-Old Who Hacked The FBI)

Vertical 1080×1920, 60 fps, Cycles, 37.2 s (frames 1–2234), timed to the client VO (`KidHacker_v002b_VO.mp3`).
Built from the P1 clips in `KidHacker_v001/` (PLAN.md, scripts) by `KidHacker_v001/scripts/06_vo_build.py`:
every shot starts on its VO word frame (`beats.json`, frame = 1 + round(s × 60)); clips are trimmed, never time-stretched.

The VO ends at "…the hacker was only a child", so the P1 interrogation / mother / ban shots (S25–S33) are not in the film.
S02 (face) was folded into S01 and S15 dropped, because the VO gave them under 1 s.

| Shot | Frames | VO |
|---|---|---|
| S01 | 1–108 | She sat down at a library computer |
| S03 | 109–168 | that connected to the |
| S04 | 169–284 | internet through a phone line |
| S05 | 285–409 | Then she used it to automatically dial |
| S06 | 410–499 | hundreds of other computers |
| S07 | 500–642 | until one finally answered |
| S08 | 643–763 | Back then, if you had the password |
| S09 | 764–896 | you could sometimes access the files |
| S10 | 897–984 | So she randomly typed |
| S11 | 985–1104 | oh, oh, oh, oh |
| S12 | 1105–1172 | To her surprise |
| S13 | 1173–1244 | it opened an FBI |
| S14 | 1245–1316 | database |
| S16 | 1317–1456 | But because the password was so easy |
| S17 | 1457–1612 | she assumed it was just some kind of computer game |
| S18 | 1613–1686 | For two weeks |
| S19 | 1687–1775 | she explored secret information |
| S20 | 1776–1852 | while the FBI searched |
| S21 | 1853–1924 | for the hacker |
| S22 | 1925–2034 | When agents finally traced it |
| S23 | 2035–2101 | they were shocked to discover |
| S24 | 2102–2234 | the hacker was only a child |

Logo: DA KRAS FILMS badge on the CRT bezel (screen close-ups S05–S07, S13–S14, OTS S10, S17, S19) and on an archive box in the FBI office (S20).
No on-screen text; screens are abstract shapes only. No FBI or NASA marks.

Review: `review/preview.mp4` (every 5th frame, 270×480, with the VO) and the check outputs in `review/`.

## v002b (director notes on v002)
1. The girl's face: eyeballs 13% smaller, larger iris (less white), upper lids lowered ~2.5 mm, thicker soft-brown brows, warmer and less waxy skin, opaque skin (no specks beside the nose). S16 (f1317-1456) is now a 3/4 angle.
2. Faceting: hair, blouse and brows now smooth-shaded with render subdivision 2. Proof at final settings (48 samples, no simplify): `review/test_f0701_540x960_final.png`, `review/test_f1401_540x960_final.png`. The preview pages still look faceted because preview.py renders with subdivision off.
3. S23 (f2035-2101): the agents walk in and slow to a stop with elbows bent; Agent C glances round the room, Agent B looks down at the child.
4. S21 (f1853-1924): the agent stands 3/4 toward the camera, glancing from the board.
Re-rendered preview ranges: f1-108, 641-896, 1101-1171, 1316-1611, 1686-1775, 1851-2234; everything else is the v002 preview, unchanged.
