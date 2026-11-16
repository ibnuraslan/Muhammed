# TenDimes v002: checks on the packed file (`TenDimes_v002_60fps.blend`, frames 1–1868)

**Cameras:** this film cuts between shot cameras with timeline markers. The pipeline checks read `scene.camera` once
(the old one-camera rule), and background `frame_set` does not switch cameras at markers, so every shot would be judged
through the first camera. I ran each check through `scripts/with_marker_cams.py`, which switches the camera on every
frame. The `*_markers.py` copies of qa_check, limb_check and clip_scan are the pipeline scripts with `cam` re-read each
frame (limb_check also names which arm points it flags).

| Check | Result | Notes |
|---|---|---|
| clip_scan (step 6) | **BAD_RANGES []** | |
| body_prop_cross (step 3, all props × all rigs, helper verts excluded as in clip_scan) | **0 visible** | The last run flagged the handset cord through his right arm in S09–S11. The cord was re-routed in front of the forearm. Re-run on 752–1007: **0 crossings at all**. The rest of the film was unchanged: 0 visible. |
| limb_check (step 2) | ARMBODY S01/S05 | All are `upperarm01:0,1(,2)`: the shoulder-joint points. This is the known false positive (LESSONS §4: "hits on upperarm01 points 0–2 within 4 cm of the shoulder"). No forearm or wrist points. |
| limb_check | PROPHEAD S09/S11 | The handset's earpiece cup sits over the outer ear: an intended contact (limb_check doc: "intended contacts must be listed"). Against the rendered skin, the nearest handset vertex is 6.6–6.9 mm away. |
| qa_check (step 6) | EMPTY S02/S07/S10 | Insert shots of the object the VO names: dimes on the table, the payphone, the last two dimes on the ledge. |
| qa_check | FAN/CLAW S05, S11 | S05: the kidnapper's deliberate point (index out, others curled). S11: the singer's hand closed on the handset by `grip_object`. |
| qa_check | BACKHEAD S05 f607 | Last frame of S05: the son walks to the door (his face shows earlier in the shot; the kidnapper faces the camera). |
| qa_check | CAMJUMP ×19 | The 19 hard cuts. |

Fixed during the v002 preview review (all re-checked):
- S14: the hands-on-shoulders version put the father's fingers about 2 cm into the son (clip_scan, frames 1148–1199). It's now a no-contact nod.
- S19: the daughter's swinging hand clipped her thigh (frame 1663): her arms now swing wider.
