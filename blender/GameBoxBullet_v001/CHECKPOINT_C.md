# GameBoxBullet — checkpoint C

Polish sheets (0.2 s, 270×480, 8 spp): `polish_sheet_a.jpg` (0–8 s), `polish_sheet_b.jpg` (8–16 s), `polish_sheet_c.jpg` (16–25 s).
Audit: `audit.txt` (from `scripts/04_audit.py`, every 5 frames plus every frame through the wall pass 160–229).

## Audit summary
| Check | Result |
|---|---|
| Camera clearance (closest visible mesh) | min **+2.7 cm** (f116); never inside geometry, including the wall fly-through |
| Soles vs bedroom floor | left foot within 0.1 mm throughout; right foot lifts 4.7 cm only during the stagger step (f410–500), then replants |
| Fingertips inside the box | 0 sampled frames |
| Penetration count (body + shirt vertices inside the box volume, shrunk 2 mm) | 4367 vertex-hits over 356 sampled frames. Nearly all are 10–16 shirt vertices per frame where the box presses into the shirt fabric at the belly (≤1.5 cm, hidden behind the box). One spike, 107 vertices, at f1416 (fingers under the box while he tilts it to look at the hole); about 0.2 s, at the bottom edge |
| Box ↔ chest contact | the box rides with his chest through the shove (same offset as the root) |

## Changed since B
- Box: clean matte black with an embossed abstract emblem (rings, diamond, chevrons, frame), slight coat sheen. Cracks spread only from the impact point (radius 0 → 5 cm in 15 frames, then grows through beat 5). Dark bullet hole stays after the cross-section closes.
- Inside: discs are annuli with centre holes and rainbow thin-film data sides, sitting in a jewel-case tray (frame + back plate); disc 3 is in a clear jewel case; booklet pages are in two print colours. Shards keep the iridescence.
- Cross-section: the +X half of every part is split off as real geometry and fades away, leaving solid cut faces. Halves only exist while it's open (no seam on the closed box). A soft studio key lights the section.
- Acting: he turns the new box in his hands near his chest; he squares it up just before the hit; the impact shoves box and torso back together and his right foot steps back half a step; his jaw drops; at the end he looks down at the hole, then up to camera.
- Grip: palms under the box, fingers wrapping the front-bottom edge (the old side grip was palm-out). Box and bullet raised to true chest height.
- Eyes: fixed black eyes (cornea alpha now wired, MakeHuman eye texture).
- Exterior: the camera rides closer; a thin bright streak behind the bullet (the old shock cone was removed because it read as a solid cone); a neighbour walking on the sidewalk (MPFB); a rotating sprinkler with slow-mo droplet arcs; birds lifting off the tree; the wall stays intact until the bullet arrives.
- Wall pass: the camera crosses the wall in about 6 frames, with a cavity light on the studs and insulation; the dust is thinner.
- Room life: RGB LED colour cycling, monitor glow, ceiling fan (slow in slow-mo, speeds up at the end), a poster knocked crooked, dust shaken from the ceiling, 60 dim motes only in the window shaft.
- Realism pass: real CC-BY models replace the blocked-out furniture (PC setup + gaming chair, wooden bed) and the neighbour houses (Suburban House ×4); trees LOD1 decimated; our own facade got 3 trimmed windows, shutters, sills, a porch light and beds.
- Camera fix: the stop orbit (20.5–22.5 s) was aiming 17 cm above the bullet; it now orbits the buried bullet.

## Known issues
- No facial rig beyond jaw and eyes, so there is no grin before the hit; shock is jaw + head + body.
- The bullet is small in the first 1.5 s of the exterior; the streak carries it.
- Our own house front is procedural (the bullet has to cut its layers) but uses scanned siding.
