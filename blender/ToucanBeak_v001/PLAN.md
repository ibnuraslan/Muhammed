# ToucanBeak — Plan (Checkpoint A)

Connect28 · branch `claude/connect28-toucan-beak` · 1080×1920 @ 60 fps · frame_end 2250 (37.5 s) · Cycles CPU · AgX Medium High Contrast

## Beat table (one continuous camera; framing changes ≈ every 1 s)
| # | t (s) / frame | Line | On screen | Camera (no cuts) |
|---|---|---|---|---|
| 1 | 0.0 / 0 | A stick swung down and smashed | Jungle edge at dusk (Poly Haven forest HDRI + scanned bark/soil/leaf litter, monstera/tropical plants, hanging vines in wind, a 2nd toucan & insects in BG). Keel-billed toucan on scanned branch, preening. A dark, out-of-focus stick (scanned wood) swings down in slow motion. | Starts wide low under canopy (0–0.6 s), cranes up to branch, then **rides alongside the stick** on its arc (0.6–1.7 s). |
| 2 | 1.7 / 102 | right into the toucan's upper beak | Impact (time-ramp to ~15% speed): keratin shards (fractured beak-material chips, textured) fly, leaves shake off the branch, bird flinches/ducks, wings half-open. No blood, no injury detail. | Stick-ride snaps into a whip-orbit around the head at impact, slow-mo push to macro on flying chips, then pulls back as the bird recoils (1.7–4.7 s, 3 framings). |
| 3 | 4.7 / 282 | every time it tried to eat | Same branch, later light: bird lunges at a real fig (scanned fig model) hanging from a twig; fig rolls off the short stump and drops into leaves. Two tries, then frustrated head shakes, crest feathers ruffle. | Low macro dolly under the beak → side profile → top-down as fig falls past lens (≈1 s each). |
| 4 | 8.9 / 534 | rescuers scanned the broken stump | **Fly-through the leaves** into a wildlife rescue clinic (real room HDRI + modelled walls/cabinets with textures, steel table, towel). MPFB vet (scrubs, nitrile glove material on MPFB hands, mask) cradles the bird; 2nd vet holds a handheld 3D scanner; a red laser line sweeps over the stump. BG: assistant walking, monitor glow. | Push past the leaves → medium of the two vets → arc down to the scanner's POV on the stump. |
| 5 | 11.3 / 678 | compared it to another toucan's beak | Scan data floats beside the bird: the stump point cloud/mesh (cyan wire-on-solid shader) and a whole reference beak mesh (from the 2nd toucan model) drift together and align. Deep teal→navy gradient backdrop. | Camera pulls out of the scanner lens into the floating data, orbits 90° as meshes align. |
| 6 | 14.1 / 846 | rebuild the missing half on a computer | Monitor on the clinic desk shows the same 3D shapes (no text/UI). The missing half extrudes layer by layer into place. | Orbit reveals monitor in clinic, then **push through the screen** into the 3D model (≤6 frames of screen surface). |
| 7 | 17.7 / 1062 | couldn't be too heavy… pull the head forward | Ghost demo on the gradient: translucent toucan; a solid, heavy-looking beak attached tips the head/neck forward and down, a downward arrow-free weight cue (beak sags, perch wobbles). Then resets. | Side profile slow dolly, low angle as head tips, crane up as it resets. |
| 8 | 22.5 / 1350 | full-size, but almost hollow | Cutaway: printed beak sliced open showing honeycomb/gyroid lattice infill; the real 3D printer model's nozzle lays layers (PLA filament material, layer lines via displacement). | Dive into the beak cross-section, track along the lattice, rise to the nozzle. |
| 9 | 25.2 / 1512 | lined it up with the broken stump | Clinic macro: vet's gloved MPFB hands (articulated grip) hold the painted prosthetic (keel-billed colours: green/orange/red tip) up to the stump; bird held under a towel. | Macro rack-focus from the hands to the seam, slow orbit. |
| 10 | 28.4 / 1704 | glued the base… fixed the rest with a pin | Adhesive bead applied with a syringe tip; tweezers (real model) insert a small pin; second vet steadies the head. BG: assistant, lamp, monitor. | Macro on the glue → whip-pan to tweezers → pull back to the vets' careful hands and faces (concentrated brows). |
| 11 | 33.0 / 1980 | the toucan could pick up fruit again | Outdoor enclosure with plants (mesh fence, monstera, perches, a 2nd bird). Toucan picks up a fig, tosses it, catches and swallows (throat bulge). | Slow orbit, settle on a medium of the bird on the perch to 37.5 s. |

`beats.json` will hold these frames; `pipeline/retime_to_vo.py` does the VO warp later.

## Assets (downloaded into `assets/`, CC-BY via Objaverse/Sketchfab, credited in CREDITS.md)
- **Keel-billed Toucan — Ramphastos sulfuratus**, MooreLab (CC-BY): a real specimen scan, 0.47 m, 1K texture. This is the hero bird. I'll add my own armature (spine, neck, head, upper/lower mandible, wings, tail) with procedural weights.
- **Toucan**, Lary (CC-BY): the source for the "another toucan's beak" reference mesh, plus a background bird.
- **Fig (Ficus carica)**, DiNArDa (CC-BY): scanned fig.
- **Wood Stick 02 / 03**, 3dhdscan (CC-BY): the scanned stick (weapon) and the perch branch.
- **Tropical Plant** by alint, by Peter Nox, and the monstera by evolveduk (CC-BY): jungle and enclosure foliage.
- **3D Printer**, Gregsterius (CC-BY); **Computer Monitor**, Marco Zakaria (CC-BY; plain screen, no logo); **Tweezers**, 3Dec.o (CC-BY).
- **Poly Haven (CC0):** a forest HDRI, a clinic interior HDRI, forest ground, bark, plaster/tiles and brushed steel textures.
- **MPFB2 / MakeHuman (CC0):** two vets and one assistant, with scrubs, masks and gloves; shirt prints removed.

## Trickiest shots
1. **Rigging a static scan.** I'll build a custom armature and weight by bone distance with smoothing. The upper beak goes on its own bone. For the broken beak I'll make a bisected copy of the upper mandible, with the cut face displaced and textured as keratin. Fragments are a cell-fracture-style split of the cut-off tip (Voronoi boolean chunks) with rigid-body or keyed ballistic arcs, slowed down.
2. **The stick ride plus slow motion on one camera.** The camera spline is parented to follow the stick through the arc, then blends to an orbit. The slow motion is in the keyframe timing, not a cut.
3. **Jungle to clinic with no cut.** The camera flies through a foreground leaf cluster (under 6 frames of leaf macro) into the clinic set, which sits in the same scene, offset in space.
4. **Through the monitor screen.** The screen shows a render-to-texture still of the same 3D beak; the camera passes the screen plane into the full 3D version of that model.
5. **Gloved hands gripping a tiny prosthetic and tweezers.** IK hand targets plus MPFB finger poses. I'll check clipping in close-up stills and with a BVH overlap test.

## Notes and risks
- Following the brief's **Batch 2 rules**: the package must be under 95 MB with no LFS, even though the film brief mentions LFS. Textures will be 1K, the HDRI 1–2K, and the save compressed.
- The scan bird has no feather cards. Close-up macros will lean on its texture, plus a fine-feather normal/displace pass.
