# FakeDrainRescue v002 (B29): synced to the client's VO

She faked a child-in-the-drain emergency so the city would finally clear a storm drain choked with trash.
This is a vertical short at 1080×1920, 60 fps, Cycles, using hard cuts (one camera per shot, switched by markers).

- **Package:** `FakeDrainRescue_v002_60fps.blend`, frames **1–1752**, with all textures and the VO packed. The VO is also here as `FakeDrainRescue_v002_VO.mp3`.
- **Beats:** `beats.json` gives each shot's start frame at the VO word, `1 + round(s × 60)`.
- **Preview:** `review/preview.mp4` is every 5th frame at 270×480, Cycles 4 spp, with the VO. It was rendered from this exact package.
- **Build:** the scripts in `../FakeDrainRescue_v001/scripts/` rebuild everything:
  - `00` textures
  - `01` characters
  - `02` dress
  - `03` sets
  - `04` shots, from `shots.json`
  - `05` shrink

  The package itself comes from `pipeline/package_for_farm.py`.

## Timing (VO words → shots)
Every action runs at 1× (its provisional reference-pacing length) from its shot's VO frame, and the cut trims it. Nothing is time-stretched.
Two P1 shots (S04 pleading, S21 glance) were dropped because the client's VO has no room for them.
S05 (police) moved to the opening "She told police". The camera-only shots S14 and S25 are longer than their P1 versions.

## Director P1 notes, all done
1. **S20:** framed chest-up, with the phone at chest height.
2. **Clean-state water (S11, S24, S25):** murky green-grey with reflections, not pool cyan.
3. **Rescuers' hi-vis:** three separate vest meshes crumpled, so per LESSONS §2.15 their own fitted work suit is now fluorescent yellow (ResA) or orange (ResB) above the belt, with silver reflective bands (S06–S11, S22, S24).
4. **Clerk (S15, S16):** he sighs (slumps, drops his head, rises), and in S16 his palm slides a form across the desk. The form is keyed with the palm, so it moves only under his hand.
5. **Phone:** moved 4 mm further off the palm (P1 known issue).
6. **Fixes from watching the preview:**
   - S06: the wading arms sweep outward only.
   - S09, S14, S17: camera moves added (S17's drifting trash removed, because its path crossed the jammed bags).
   - S03: she stays planted at the edge with her hands clear of her hips.
   - S20: chest-up framing.

## Known issues
See `review/checks.md` for every check result and the known issues (phone back contact in S19 and S20; ankle cuffs and the hip colour line, visible at full resolution only).
