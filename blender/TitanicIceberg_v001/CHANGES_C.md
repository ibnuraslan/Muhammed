# Checkpoint C: changes since B, and audit

## Changes since B
- **Ghost liner** was rendering as a solid white body. It is now additive (transparent plus rim emission on the first surface only, with transparent bounces at 64), so it reads as a translucent cold-blue ghost.
- **Iceberg** facets were lumpy. They are now sharp Voronoi crackle (F2−F1) displacement. The scrape face is masked flat so the smear and the dive line stay clean.
- **Dive into the smear:** the crossing frame is raycast against the real displaced ice, so there is no black frame inside the ice. The iceberg and mist use `hide_render` while the camera is inside the berg.
- **Darkroom:**
  - The door-cutter helper was rendering as a red box (the blank red frames at 19–20 s). It is now hidden.
  - The door goes through both walls and is wider.
  - The trays are now hollow enamel trays. The liquid no longer blocks light, so the print is visible developing in the tray.
- **Office:**
  - Expert B holds the print within arm's reach (it was 0.5 m away).
  - Expert A is restaged at the desk, holding the magnifier.
  - The camera path now runs beside the lens into the print, so it no longer passes through Expert A.
- **Steward:** beat 1 now opens on his face (front-left, low) as he raises the camera, then swings over his shoulder.
- **Camera:** the look-target spline is now monotone (PCHIP per axis). That removes the swing to the bulkhead at 1.6 s. The explainer is reframed so the hull and photo share the frame, and the final orbit is wider ("alone in the fog").
- **Lights** are hidden from the camera (the scrape-glow sphere showed). The night is brighter, with the moon angled onto the scrape face and a contact glow.
- **Explainer:** the red band glows only near the waterline, not the whole lower hull.
- **Debris field:** 60 pieces, spread closer to the berg. Feet are raised 2.5 cm for the crouching actors (sink fix).
- **Package:** test-packed to 44 MB (see `stills/C_package_check_factory.jpg`, rendered from the packed file with `--factory-startup`).

## Audit (`stills/C_audit.txt`, from `scripts/audit.py`)
| Check | Count |
|---|---|
| Feet hovering > 2 cm | 0 |
| Feet sinking > 2 cm | 0 |
| Camera inside geometry (every 6 frames) | 0 |
| Hand float > 3 cm | 22: Expert B's right hand on the print edge, 4–5 cm (it reads as a pinch at the corner on screen) |
| Hand penetration (> 10 verts inside the prop) | 14: Expert A's fingers around the thin magnifier handle |
| Hat poke-through verts (steward's fedora) | 4 |

## Still open, being fixed for D
- The office window hotspot is blown out at 20.0–20.4 s.
- Stage floor reflections of the cyc key lights.
- The ghost scrape at night reads more like a pale bow shape than a full liner.
- The 26.0 s single still is mostly fog (the camera exiting the berg).
