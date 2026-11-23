# v012 checks (run on the packed file)

The four checks ran on the package built just before the last change. That change only moved the lectern back from 23 cm to 15 cm, because at 23 cm the defendant's wrist flipped; frames 1241–1446 were re-rendered into the preview after it. The JSON files are in this folder.

| Check | Result | Reading |
|---|---|---|
| `clip_scan` (hands into bodies) | bad ranges 61–391, 421–427, 499, 979, 1063–1159 | Almost all are "other": a surgeon's hand inside the **patient's mesh**. In 61–277 and 1063–1159 the hands work inside the open-abdomen cavity, where her skin is cut away in the material but the mesh is still there. In 289–391 Surgeon 1's hands rest on the drape over her arm, which is hidden under the drape. On the preview the hands are above the skin or inside the opening. The earlier walking-arm hits (577, 643–703, 919–973) are fixed with a wider arm swing; 979 is one sample. |
| `limb_check` | ARMBODY 1297, PROPHEAD 483 | PROPHEAD: the neck towel and anaesthesia mask against the patient's face (they rest on it). ARMBODY: mostly 2-point hits, the elbows against the jacket and scrubs. v008g (approved) had 822 / 228. |
| `qa_check` | EMPTY 133, ATTACH 34, FAN 17, CAMJUMP 11, CLAW 11 | CAMJUMP = the 13 planned hard cuts. EMPTY = close shots where a hand, drape or prop fills more of the frame than a person (the branding and reveal close-ups, the calendar). ATTACH = masks about 2 cm off the skin (the pleated mask stands off the face). FAN / CLAW = the judge's and clerk's grip fingers. |
| `body_prop_cross` | crossings on desk, lectern, drape, pad, gavel handle, stamp | Gavel handle and stamp = the fingers wrapping them (grips). The table pad was fixed by lifting the patient 2.5 cm; the hair under her head is masked. The desk top was trimmed so it ends in front of the seated panel; what remains is resting fingertips sinking about 1 cm. The tool also reports toes, shoes and head "through" the desk and lectern tops, which cannot happen geometrically; on the rendered frames, bodies, arms and hands sit behind or on top of them. |

Every one of the 329 preview frames was watched after the final build.
