
def all_fcurves(idb):
    ad = getattr(idb, "animation_data", None)
    if not ad or not ad.action: return []
    out = []
    for layer in getattr(ad.action, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags: out.extend(cb.fcurves)
    return out
def hold_ends(f0, f1):
    """key every channel that moves inside [f0, f1] at f0 and f1 (evaluated now, before the next shot exists), so no shot's
    edge frame interpolates toward the next shot's pose"""
    ids = list(bpy.data.objects) + list(bpy.data.lights) + list(bpy.data.cameras)
    for idb in ids:
        for fc in all_fcurves(idb):
            ks = [kp.co.x for kp in fc.keyframe_points]
            if not any(f0 <= k <= f1 for k in ks): continue
            for f in (f0, f1):
                if not any(abs(k - f) < 0.01 for k in ks):
                    fc.keyframe_points.insert(f, fc.evaluate(f), options={'FAST'})
            fc.update()

