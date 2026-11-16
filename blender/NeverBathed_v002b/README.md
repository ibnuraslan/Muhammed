# NeverBathed_v002b (B31): the man who refused to bathe for 60 years

v002b = v002 + the director's notes of Nov 16 (clean tunics, matted crown hair, closer 5b, 10a action, clear final shot).
Built straight to the client VO (no retime). 20 shots, hard cuts, 1080×1920, 60 fps, frames 1–1728.
Generic characters only (no real likeness). The death stays off-screen.

- `NeverBathed_v002b_60fps.blend`: the package (textures and VO packed).
- `NeverBathed_v002b_VO.mp3`, `beats.json` (shot starts at `1 + round(word_s × 60)`), `review/VO_words.json`.
- `review/preview.mp4`: the full moving preview with VO (every 5th frame, 270×480, Cycles 4 samples + OIDN), rendered
  from this exact file. `review/pages/`: every preview frame, 50 per page.
- `review/CHECKS.md`: body_prop_cross, qa_check, clip_scan, limb_check results and the reasons for remaining flags.
- Build scripts: `../NeverBathed_v001/scripts/` (`build_all.sh <work> ../assets/models ../shots_vo.json` with `NB_VO=<mp3>`,
  then `pipeline/package_for_farm.py`).

## Shots (VO frame → shot)
| Frame | Words | Shot |
|---|---|---|
| 1 | He believed taking a bath | young hermit at the stone trough, finger stops above the water |
| 85 | would make him sick | he pulls back and turns away shaking his head |
| 158 | so for more than | young portrait in the lane, slow orbit |
| 223 | 60 years | age cut: the old hermit, same framing |
| 306 | refused to wash | old hermit at the trough turns away, shaking his head |
| 367 | because he thought the dirt | he strides toward camera and thumps his chest |
| 451 | was protecting him | villager by the crates (logo) shakes his head |
| 525 | He left his home | he walks out of his door |
| 597 | started sleeping in a | at the desert edge he scoops soil out of a shallow pit |
| 665 | shallow hole in the ground | he lies in the pit, camera cranes up |
| 756 | He survived on roadkill | he kneels by a dead hare on the road verge (no blood, no eating) |
| 846 | even smoked animal poop | insert: dark dried dung cakes beside his pipe |
| 932 | through a pipe | pipe pinched at his lips, then lowered |
| 1005 | Instead of cutting his hair | he lights a twig in his fire and lifts it to his beard |
| 1099 | he burned it over a fire | close: a small flame singes the beard ends at chest height, smoke |
| 1217 | Eventually, he became known as | he walks down the lane, flies circling over his head |
| 1323 | the dirtiest man in the world | he keeps walking, camera arcs round him |
| 1446 | Then someone finally convinced | villager points at the tin tub; the hermit shakes his head and steps back (camera pushes in) |
| 1547 | him to bathe, and | in the tub, villager's hands on his shoulders |
| 1622 | he died shortly afterward | dusk: one villager kneels at the empty pit, the other walks up; heads bowed (off-screen death) |

Logo: white DA KRAS FILMS decal on the crate in the 451 shot.
