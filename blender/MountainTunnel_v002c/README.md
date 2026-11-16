# MountainTunnel_v002c (B30): Why This Tunnel Exists

Built to the client VO (`MountainTunnel_v002c_VO.mp3`, 32.66 s of speech). Beat frames = `1 + round(word_seconds × 60)` (`beats.json`).
Each shot was built at 1× from the P1 clips (`MountainTunnel_v001`) and **trimmed** onto its VO window
(`MountainTunnel_v001/scripts/04_vo_layout.py`); character animation is never time-stretched. Only the three map/diagram
shots (6a, 7b, 10a) were built directly to their VO length.

| Shot | Frames | VO words |
|---|---|---|
| 1a | 1–148 | He swung a hammer into a chisel |
| 4c | 149–217 | slowly breaking pieces |
| 1b | 218–274 | the mountain |
| 2a | 275–379 | strike at a time |
| 3a | 380–462 | Villagers laughed at him |
| 4a | 463–574 | but he returned every single day |
| 4b | 575–720 | with the same simple tools |
| 5a | 721–816 | Years earlier, his wife |
| 5b | 817–893 | had fallen from a cliff |
| 5d | 894–985 | was badly injured |
| 6a | 986–1150 | The nearest hospital was on the other side of the mountain |
| 7a | 1151–1231 | and the only route around it |
| 7b | 1232–1378 | stretched more than 40 miles |
| 8a | 1379–1445 | She died before |
| 8b | 1446–1501 | help |
| 9a | 1502–1561 | So, he spent |
| 10a | 1562–1627 | 22 years |
| 10b | 1628–1678 | cutting straight through |
| 10c | 1679–1746 | the mountain himself |
| 11c | 1747–1824 | creating a shortcut |
| 13a | 1825–1888 | so nobody else |
| 13c | 1889–1991 | would suffer the same fate |

Logo: DA KRAS FILMS (white) on the wooden crate beside the laughing villagers (3a, 1.4 s). No logo in the sad beats.
Rebuild: `MountainTunnel_v001/scripts/01_chars.py` → `02_sets.py` → `03_shots.py -- build.blend shots_build.json` →
`04_vo_layout.py -- shots_build.json shots_vo.json out.blend VO.mp3 1991` → pack (`review/` has the preview).
