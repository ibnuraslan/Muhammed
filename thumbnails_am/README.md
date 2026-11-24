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
| B2 | `scenes/mummy_skull.py VARIANT=b2` | Skull and jaw assembled but plainly from two people (pale cranium, dark jaw, off-true fit) |

    PREVIEW=0.4 SPP=32 blender -b --python scenes/antwerp_vault.py      # 768x432 preview -> out/
    blender -b --python scenes/antwerp_vault.py                          # 1920x1080 master

Credits: Poly Haven (CC0) autumn_forest_04, kloofendal_48d_partly_cloudy_puresky, forest_leaves_02, wood_table_worn,
marble_01, trashbag, shrub_02, fern_02, dry_branches_medium_01, nettle_plant, dead_tree_trunk. Sketchfab (CC-BY 4.0):
cranium and mandible scans (jagake), "Sub Sandwich" (meerschaumdigital); see the film READMEs.
