# Thumbnails: Antwerp heist + Cladh Hallan mummy

Blender 5.2 Cycles scenes, no text in the images. They reuse each film's 3D library: set `ANTWERP3D` to a checkout
of `claude/antwerp-heist` (`antwerp_heist/3d`) and `MUMMY3D` to `claude/mummy-cladh-hallan` (`mummy/3d`)
(defaults: `../wt_antwerp/...` and `../wt_mummy/...` beside this folder's parent). Assets download on first use
(Poly Haven CC0, Sketchfab CC-BY via the film libraries).

| Concept | Scene | Idea |
|---|---|---|
| A1 | `scenes/antwerp_bag.py` | Black bin bag split open on a sunny autumn forest floor; diamond papers, loose diamonds, a VHS tape with its ribbon unspooled, the salami sandwich |
| A2 | `scenes/antwerp_vault.py` | Round vault door hanging open; an endless bright hall of forced boxes; a tiny figure with a torch; one diamond in the foreground |
| B1 | `scenes/mummy_skull.py VARIANT=b1` | Skull on a table, the wrong jaw set down beside it |
| A2 v2 | `scenes/antwerp_vault.py` + `scenes/crew.py` | Concrete vault wall, round door open, gold light; five crouched silhouettes sneaking out with loot bags |
| B1 v3 | `scenes/mummy_sand.py` | Skull half-buried in sand at dusk on the right third, the mismatched jaw lying apart |
| B1 alt | `scenes/mummy_hands.py` | Skull and torn-away jaw gripped by red hands in the dark (dropped) |
| B2 | `scenes/mummy_skull.py VARIANT=b2` | Skull and jaw assembled but plainly from two people (pale cranium, dark jaw, off-true fit) |

    PREVIEW=0.4 SPP=32 blender -b --python scenes/antwerp_vault.py      # 768x432 preview -> out/
    blender -b --python scenes/antwerp_vault.py                          # 1920x1080 master

Credits: Poly Haven (CC0) autumn_forest_04, kloofendal_48d_partly_cloudy_puresky, forest_leaves_02, wood_table_worn,
marble_01, trashbag, shrub_02, fern_02, dry_branches_medium_01, nettle_plant, dead_tree_trunk. Sketchfab (CC-BY 4.0):
cranium and mandible scans (jagake), "Sub Sandwich" (meerschaumdigital); see the film READMEs.

More credits: Sketchfab CC-BY "Eric Rigged 001" (renderpeople), "ZOMBIE HAND" (Colin.Greenall). Poly Haven CC0:
concrete_wall_008, concrete_floor_worn_001, coast_sand_01, qwantani_dusk_2_puresky.
