# TenDimes v002c: checks on the packed file (`TenDimes_v002c_60fps.blend`, frames 1–1868)

v002c changes only materials and the static dime meshes (no animation, cameras or rigs changed), so the v002b
clip_scan / limb_check / qa_check results below still hold for this file.
New for v002c:

| Check | Result | Notes |
|---|---|---|
| body_prop_cross: DimePile10, DimePile2, DimePileD × all four rigs, f1–1868 step 2 | **0 crossings** | `C_bpc_dimes.json` |
| unchanged-shot noise check (S05 f501 vs v002b preview) | RMSE 0.82 | render noise only, so the splice is consistent |
| package size | 50 MB | under the 95 MB limit |
| watched | all 8 pages + preview.mp4 | dimes f81–201, f1501–1597, f1771–1868 and close-ups f211–371, f781–821, f1201–1391 |

---

## (v002b) checks on the packed file (`TenDimes_v002b_60fps.blend`, frames 1–1868)

Run through `scripts/with_marker_cams.py` with the `*_markers.py` copies (the camera follows the shot markers on every frame;
see the v002 CHECKS.md for why). Full-film runs: `B_*.json`. Final S18 re-staging re-checked on 1393–1492: `B18_*.json`.
Between the full-film runs and the final package, only S18 changed.

| Check | Result | Notes |
|---|---|---|
| clip_scan | **0 bad ranges** | Full film (step 6). S18 re-checked at **step 1**: [] |
| body_prop_cross (all props × all rigs) | **0 crossings** (visible and off-camera) | |
| limb_check | ARMBODY S01/S05/S14/S18 | Only `upperarm01:0,1(,2)`: the known shoulder false positive (LESSONS §4). |
| limb_check | PROPHEAD S09/S11 | Earpiece cup over the outer ear: an intended contact (nearest handset vertex 6.6 mm from the skin). |
| qa_check | EMPTY/FILL S02, EMPTY S07/S10 | Insert shots of the dimes (S02 is now a push-in onto the table), the payphone and the ledge coins. |
| qa_check | FAN/CLAW S05, S11 | The kidnapper's point; the hand closed on the handset. |
| qa_check | BACKHEAD S05 f607, CAMJUMP ×19 | The son walking to the door; the hard cuts. |

Re-staged during v002b (found by the checks):
- S18 first try was the left hand slid into the trouser pocket: it was hidden behind him and its fingers went inside the
  thigh (clip_scan 1423–1489). Now the camera-side right hand comes round from the side and rests flat on the
  trouser pocket. Its contact point is ray-cast onto the cloth.
