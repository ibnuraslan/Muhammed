"""Natural weathering for painted wood (applied to every shot just before render, scene-level, no shared file edited).

The shared ship.paint 'chips' are a fine, hard-edged noise (scale 22, a 2% threshold band): at film distance they
read as white speckle / spatter. Here every such chip network is turned into worn paint: large soft patches where
the paint has thinned to the wood or primer (low-frequency noise, wide transition), at reduced strength."""
import bpy


def soften_chips():
    n = 0
    for m in bpy.data.materials:
        if not m.node_tree:
            continue
        for nd in m.node_tree.nodes:
            if nd.type == 'TEX_NOISE' and abs(nd.inputs['Scale'].default_value - 22.0) < 1e-3:
                nd.inputs['Scale'].default_value = 2.2; nd.inputs['Detail'].default_value = 6.0
                nd.inputs['Roughness'].default_value = 0.6
                for l in nd.outputs['Fac'].links:
                    mr = l.to_node
                    if mr.type == 'MAP_RANGE':
                        mr.inputs['From Min'].default_value = 0.56; mr.inputs['From Max'].default_value = 0.78
                        mr.inputs['To Max'].default_value = 0.55          # never fully bare: thinned paint
                n += 1
    return n
