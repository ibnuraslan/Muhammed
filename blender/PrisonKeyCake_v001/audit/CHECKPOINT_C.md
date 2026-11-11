# PrisonKeyCake checkpoint C: polish

**Sheets:** `stills/polish_C_0.jpg` … `polish_C_3.jpg`. These are one still every 0.2 s (158 stills, 270×480, 8 samples), and each sheet covers 8 s.

## Audit numbers (final film, `work/film_C.blend`)
| Check | Script | Result |
|---|---|---|
| Camera inside geometry | `audit_camera.py`, every frame | **0 frames inside.** 19 frames pass within 8 cm of a surface: the two window-bar fly-throughs, and macro moves skimming his sleeve or the door. |
| Feet hover/sink | `audit_contacts.py`, every 2nd frame | **0 sinks, 0 hovers** across all 7 IK characters |
| IK reach | `audit_contacts.py` | Gaps of 3–17 cm last only a few frames, during transitions: the window lift at 1197–1213 (14 cm), and the guard waving and hand-off at 545–589. The full list is in `contacts_C.txt`. |
| Penetration (BVH) | `audit_penetration.py`, every 6th frame, 4 mm threshold | **248 hand/foot frame-hits, 0 character overlaps, 271 head-item vertices through.** See the breakdown below. |

### What the penetration hits are
- **Most are grips:** fingertips 1–2 cm into what they hold, such as the crucible shank, the parcel box, the knife handle and the tins.
- **Fingertips on the table and wax:** while pressing the key, beats 1 and 7. Part of this count is a false positive, because the wax disc is an open mesh.
- **Wall contacts, at most 5 cm:**
  - the guard's waving hand by the gate wall
  - his left palm flat on the stone during the jam
- **Head items:** the 271 vertices are mostly hat brims grazing hair on the far crowd.

## Changed since B (director notes)
1. **His face:**
   - The beat 6 jam now alternates lock macro and face: frames 912 → 936 → 962 → 977 → 992 → 1018. You see his eyes dart to the door gap as a guard's lantern passes under the door, his jaw tighten, and his forehead go to the door.
   - Beat 8 ends on a face close-up as the key turns (relief: jaw opens, head lifts).
   - Beat 9 now uses a leading camera that looks back at his face through the corridor, at 1500, 1518, 1548 and 1582.
2. **Key and lock macros:**
   - 0–4 s: the key is in his fingers in a macro at 1 s. The fingertip press leaves the key visible between his hands.
   - Lock macros at 912, 962 and 1416 sit at key height along the door. They show the key's scrape and jam (it backs out and goes in again) and the jiggle, and later the 90° turn with the bolt sliding.
   - The keys are now bright worn iron.
3. **The cake:**
   - It is a procedural dark fruit cake: crumb with red and orange fruit specks, drippy white icing.
   - He makes two knife cuts, the slice comes out, crumbs scatter, and the key stands in the cut.
4. **1919 costume:**
   - Denim is now dark brown or grey wool, with fabric noise and no denim fade, on every character.
   - The prisoner's shirt is drab linen.
5. **Hands:** pore and knuckle bump detail on the prisoner's skin.
6. **Ending:**
   - The older him has grey hair, glasses and a darker suit.
   - Sun and HDRI light are warmer, and the facade is brighter.
   - Flags are 2.7 × 1.35 m with stronger wind.
   - The crowd wears bowlers and caps (some waved in the hand), and its clothing hue and value vary per person.
   - The end framing keeps the crowd at mid distance.
7. **Grit:**
   - The lantern of a guard pacing the corridor leaks under the cell door during the jam.
   - There is thin dust in the cell light.
   - Candle flicker, and the double gates swing with overshoot and settle.
8. **Fixes:** the lock, bolt and grille parenting; feet sole offsets; the cake key path; the guard's hands on the box; the corridor double gates and the guard's position; a blank white frame at 905, now routed over his head.
9. **Package:** 67 MB, a normal git file (no LFS). It now JPEG-encodes images, uses 1K textures (hero skin at 2K) and 1K HDRIs, bakes MPFB body shape keys, and purges orphans. Renders match the source film.

## Realism pass (client note, 21:00): primitives replaced with real models
| Shot | Was | Now |
|---|---|---|
| Keys, beats 1–8 (master, cast copies, glowing casting) | procedural ring/shaft/bit | **Old Key** by Meerschaum Digital (CC BY). The wax imprint is now ray-cast from this key's real silhouette. |
| Cell door lock, beats 6 and 8 | rusty box | **Pocket Door Lock** scan by IU Indianapolis University Library (CC BY), with a brass escutcheon keyhole on the door's inside face |
| Cakes, beats 5 and 8 | procedural iced cylinder | **Christmas Panettone** scan by alban (CC BY). Cake 2 is bisected from the scan into the main cake and the slice, with crumb on the cut faces. |
| Government building, beat 10 | box portico, cylinder columns, pediment | **Prefettura di Trieste** by Karpulya (CC BY), on a sandstone plinth at the top of the steps |
| Foundry crucible, beat 4 | noise cylinder | **Lead melting crucible** scan by City of Ballarat (CC BY) |
| Barrels, yard and foundry | wood-textured cylinders | Poly Haven **Wine Barrel 01** (CC0) |
| Cell bucket | metal cone | Poly Haven **Wooden Bucket 01** (CC0) |

Removed: the pigeon flock at the reveal. The CC-BY pigeon model broke when its rig was stripped, so only five small birds stay, circling high over the yard.
