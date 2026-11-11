# Split copy of the farm .blend

The Git LFS upload was refused ("verify: Forbidden"), so the packed file is stored here as plain-git parts, each under 100 MB.

To rebuild it, run this from `blender/ShoeBomber_v002/`:

```
cat parts/ShoeBomber_v002_60fps.blend.part* > ShoeBomber_v002_60fps.blend
sha256sum -c parts/SHA256SUMS
```
