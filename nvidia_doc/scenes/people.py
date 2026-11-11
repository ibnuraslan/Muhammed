"""The two recurring characters, built the same way in every scene (dramatization; no likeness is attempted).
  man()   : early 60s, grey hair, black leather jacket, dark jeans
  woman() : late 30s, long dark hair, dark fitted dress
"""
from human import Human, add_asset


def man(name="Man"):
    h = Human(name, gender=1.0, years=62, muscle=0.5, weight=0.5, height=0.42,
              skin="old_lightskinned_male_diffuse.png", eyebrows="eyebrow002", eyelashes="eyelashes01")
    jacket = add_asset(h, "clothes", "male_casualsuit05", hue=0.5, sat=0.15, val=0.12, rough=0.38, sheen=0.1)
    pb = jacket.data.materials[0].node_tree.nodes["Principled BSDF"]
    pb.inputs['Coat Weight'].default_value = 0.6; pb.inputs['Coat Roughness'].default_value = 0.25
    add_asset(h, "clothes", "shoes02", val=0.2, rough=0.35)
    add_asset(h, "hair", "short02", sat=0.0, val=0.75, rough=0.45)
    sk = h.skin_mat.node_tree.nodes["Principled BSDF"]
    sk.inputs['Subsurface Weight'].default_value = 0.1; sk.inputs['Subsurface Radius'].default_value = (0.5, 0.25, 0.15)
    return h


def woman(name="Woman"):
    h = Human(name, gender=0.0, years=38, muscle=0.45, weight=0.38, height=0.52,
              skin="middleage_lightskinned_female_diffuse.png", eyebrows="eyebrow001", eyelashes="eyelashes01")
    add_asset(h, "clothes", "female_elegantsuit01", hue=0.5, sat=0.2, val=0.18, rough=0.55, sheen=0.4)
    add_asset(h, "clothes", "shoes02", val=0.3, rough=0.3)
    add_asset(h, "hair", "long01", val=0.35, rough=0.4)
    sk = h.skin_mat.node_tree.nodes["Principled BSDF"]
    sk.inputs['Subsurface Weight'].default_value = 0.12; sk.inputs['Subsurface Radius'].default_value = (0.5, 0.25, 0.15)
    return h
