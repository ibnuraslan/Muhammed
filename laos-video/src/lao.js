// ===================== lao.js: characters, sets and props for the Laos film =====================
import * as L from './lib3.js';
import { buildFace } from './face.js';
import { mergeGeometries } from './jsm/utils/BufferGeometryUtils.js';
const { THREE, mesh, mat, rng, lerp, clamp, GRAD } = L;
const V3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
export const TT = (lines, o = {}) => { const sz = o.size || 64, h = o.h || 256; return L.textTex(lines.map((s, i) => [s, sz, h / 2 + (i - (lines.length - 1) / 2) * sz * 1.15 + sz * .35, o.font]), o); };
const toon = (c, o = {}) => new THREE.MeshToonMaterial({ color: c, gradientMap: GRAD, ...o });

// ---------- people ----------
const SKIN = [0xc89468, 0xb8845a, 0xd0a074, 0xa87650, 0xc08a5e];
export function villager(o = {}) {
  const r = rng((o.seed || 1) * 17 + 3), g = new THREE.Group();
  const skinC = o.skin ?? SKIN[Math.floor(r() * SKIN.length)], skin = mat(skinC, .62), hairC = o.hairC ?? [0x141010, 0x1e1612, 0x2a1e16][Math.floor(r() * 3)];
  const shirtC = o.shirt ?? [0xe8e2d4, 0x3a5a7a, 0x7a4a3a, 0x5a6a4a, 0xb89a6a, 0x2a3a4a][Math.floor(r() * 6)];
  const lowC = o.lower ?? (o.skirt ? [0x6a2a3a, 0x3a2a5a, 0x2a4a5a, 0x5a3a2a][Math.floor(r() * 4)] : [0x2a2a30, 0x3a3428, 0x1e2a3a, 0x4a4030][Math.floor(r() * 4)]);
  const shirt = mat(shirtC, .9), shirtDk = mat(new THREE.Color(shirtC).multiplyScalar(.78), .9), low = mat(lowC, .9), shoe = mat(0x1e1610, .7);
  // legs
  const pelvis = new THREE.Group(); pelvis.position.y = .95; g.add(pelvis);
  const legs = [-1, 1].map(s => { const hip = new THREE.Group(); hip.position.set(0, 0, s * .095); pelvis.add(hip);
    mesh(new THREE.CylinderGeometry(.08, .066, .46, 12), o.shorts ? low : (o.skirt ? skin : low), [0, -.23, 0], [0, 0, 0], hip);
    const knee = new THREE.Group(); knee.position.y = -.46; hip.add(knee);
    mesh(new THREE.CylinderGeometry(.062, .05, .42, 12), (o.shorts || o.skirt) ? skin : low, [0, -.21, 0], [0, 0, 0], knee);
    mesh(new THREE.BoxGeometry(.24, .06, .1), o.boots ? mat(0x1a1410, .5) : (o.barefoot ? skin : shoe), [.05, -.44, 0], [0, 0, 0], knee);
    if (o.boots) mesh(new THREE.CylinderGeometry(.066, .062, .2, 12), mat(0x1a1410, .5), [0, -.33, 0], [0, 0, 0], knee);
    return { hip, knee }; });
  // torso (shirt) and optional sinh skirt
  const spine = new THREE.Group(); spine.position.y = .95; g.add(spine);
  const prof = [[0, -.08], [.2, -.08], [.205, .05], [.2, .25], [.215, .42], [.19, .5], [.1, .535], [0, .54]];
  const tor = mesh(new THREE.LatheGeometry(prof.map(p => new THREE.Vector2(p[0], p[1])), 20), shirt, [0, 0, 0], [0, 0, 0], spine); tor.scale.set(.78, 1, 1);
  if (o.vest) { const v = mesh(new THREE.CylinderGeometry(.19, .2, .42, 16, 1, true), mat(o.vest, .8), [0, .26, 0], [0, 0, 0], spine); v.scale.set(.86, 1, 1.08); v.material.side = THREE.DoubleSide; }
  if (o.skirt) { const sk = mesh(new THREE.CylinderGeometry(.19, .25, .84, 18, 1, true), low, [0, -.4, 0], [0, 0, 0], pelvis); sk.material.side = THREE.DoubleSide; sk.scale.set(.85, 1, 1);
    const band = mesh(new THREE.CylinderGeometry(.243, .25, .12, 18, 1, true), mat(o.bandC ?? 0xc8a040, .7), [0, -.76, 0], [0, 0, 0], pelvis); band.scale.set(.86, 1, 1.01); band.material.side = THREE.DoubleSide;
    const lap = mesh(new THREE.BoxGeometry(.5, .17, .36), low, [.22, -.04, 0], [0, 0, 0], pelvis); lap.visible = false; g.userData.sk = sk; g.userData.band = band; g.userData.lap = lap; }
  else if (!o.shorts) mesh(new THREE.CylinderGeometry(.17, .18, .14, 16), low, [0, -.02, 0], [0, 0, 0], pelvis).scale.set(.8, 1, 1.1);
  else mesh(new THREE.CylinderGeometry(.17, .19, .2, 16), low, [0, -.06, 0], [0, 0, 0], pelvis).scale.set(.8, 1, 1.15);
  // arms
  const arms = [-1, 1].map(s => { const sh = new THREE.Group(); sh.position.set(0, .46, s * .2); spine.add(sh);
    mesh(new THREE.SphereGeometry(.068, 10, 8), shirt, [0, 0, 0], [0, 0, 0], sh);
    mesh(new THREE.CylinderGeometry(.062, .055, .3, 10), o.longSleeve === false ? skin : shirt, [0, -.16, 0], [0, 0, 0], sh);
    if (o.longSleeve === false) mesh(new THREE.CylinderGeometry(.07, .068, .13, 10), shirt, [0, -.06, 0], [0, 0, 0], sh);
    const el = new THREE.Group(); el.position.y = -.31; sh.add(el);
    mesh(new THREE.CylinderGeometry(.05, .045, .27, 10), o.longSleeve ? shirtDk : skin, [0, -.13, 0], [0, 0, 0], el);
    const hand = mesh(new THREE.CapsuleGeometry(.03, .05, 4, 8), skin, [.005, -.3, 0], [0, 0, 0], el); hand.scale.set(1.1, 1, .7);
    return { sh, el, hand }; });
  // head
  const neck = new THREE.Group(); neck.position.y = .56; spine.add(neck);
  mesh(new THREE.CylinderGeometry(.05, .055, .1, 10), skin, [0, .02, 0], [0, 0, 0], neck);
  const head = new THREE.Group(); head.position.y = .115; neck.add(head);
  buildFace(head, { seed: o.seed || 1, skin: skinC, hair: hairC, eye: '#2a1e14', beard: 0, noMustache: o.mustache ? false : true, y0: .02 });
  const hairM = mat(hairC, .85);
  const cap = mesh(new THREE.SphereGeometry(.112, 16, 10, 0, Math.PI * 2, 0, Math.PI * .5), hairM, [-.012, .055, 0], [0, 0, -.12], head); cap.scale.set(1.04, .8, 1);
  if (o.bun) mesh(new THREE.SphereGeometry(.055, 12, 8), hairM, [-.11, .1, 0], [0, 0, 0], head);
  if (o.longHair) { const lh = mesh(new THREE.BoxGeometry(.06, .2, .2), hairM, [-.09, -.04, 0], [0, 0, 0], head); }
  const hat = o.hat || 'none';
  if (hat === 'conical') { const c = mesh(new THREE.ConeGeometry(.3, .16, 24, 1, true), mat(0xd8c090, .9), [0, .2, 0], [0, 0, 0], head); c.material.side = THREE.DoubleSide; }
  if (hat === 'pith') { mesh(new THREE.SphereGeometry(.15, 18, 10, 0, Math.PI * 2, 0, Math.PI * .5), mat(o.hatC ?? 0x5a6a3a, .8), [0, .07, 0], [0, 0, 0], head).scale.set(1.1, .9, 1); mesh(new THREE.CylinderGeometry(.19, .19, .012, 20), mat(o.hatC ?? 0x5a6a3a, .8), [0, .075, 0], [0, 0, 0], head); }
  if (hat === 'bush') { mesh(new THREE.CylinderGeometry(.11, .118, .08, 18), mat(o.hatC ?? 0x4a5a3a, .9), [-.005, .12, 0], [0, 0, 0], head); mesh(new THREE.CylinderGeometry(.18, .18, .01, 20), mat(o.hatC ?? 0x4a5a3a, .9), [0, .085, 0], [0, 0, -.06], head); }
  if (hat === 'helmet') { mesh(new THREE.SphereGeometry(.135, 18, 10, 0, Math.PI * 2, 0, Math.PI * .5), mat(o.hatC ?? 0x2a4a8a, .5), [-.005, .06, 0], [0, 0, 0], head).scale.set(1.05, .95, 1);
    const vis = mesh(new THREE.SphereGeometry(.15, 18, 10, -Math.PI * .45, Math.PI * .9, Math.PI * .35, Math.PI * .4), new THREE.MeshStandardMaterial({ color: 0xa8c8d8, transparent: true, opacity: .35, roughness: .1 }), [.0, .01, 0], [0, 0, 0], head); vis.userData.noOutline = true; vis.userData.noToon = true; }
  if (hat === 'beret') mesh(new THREE.CylinderGeometry(.12, .115, .04, 18), mat(o.hatC ?? 0x2a3a2a, .9), [-.01, .14, 0], [0, 0, .15], head);
  if (hat === 'cap') { mesh(new THREE.SphereGeometry(.118, 16, 8, 0, Math.PI * 2, 0, Math.PI * .5), mat(o.hatC ?? 0x2a3a5a, .9), [-.005, .07, 0], [0, 0, 0], head); mesh(new THREE.CylinderGeometry(.1, .1, .01, 16, 1, false, 0, Math.PI), mat(o.hatC ?? 0x2a3a5a, .9), [.06, .075, 0], [0, 0, -.1], head); }
  // carried props
  if (o.detector) { const d = detector(); d.position.set(.05, -.3, 0); arms[1].el.add(d); g.userData.detector = d; }
  if (o.hoe) { const h = hoe(); h.position.set(0, -.3, 0); arms[1].el.add(h); g.userData.hoe = h; }
  if (o.basket) { const b = mesh(new THREE.CylinderGeometry(.16, .12, .3, 14, 1, true), mat(0xa88a50, .9), [-.22, .25, 0], [0, 0, 0], spine); b.material.side = THREE.DoubleSide; }
  if (o.gun) { const gun = L.lowRifle(false); gun.scale.setScalar(.85); const hd = new THREE.Group(); hd.add(gun); hd.quaternion.setFromUnitVectors(V3(1, 0, 0), V3(-.12, .86, .5).normalize()); hd.position.set(-.24, .08, 0); spine.add(hd); g.userData.rifle = hd; }
  g.userData.rig = { legs, arms, spine, head, neck, pelvis };
  g.userData.pose = (t, p = {}) => {
    if (g.userData.sk) { g.userData.sk.scale.set(.85, 1, 1); g.userData.sk.position.y = -.4; g.userData.band.visible = true; g.userData.lap.visible = false; }
    const sp = p.speed ?? 6.5, ph = t * sp + (o.seed || 0), w = p.walk ? Math.sin(ph) : 0, w2 = p.walk ? Math.sin(ph + Math.PI) : 0, amp = p.run ? .85 : .5;
    legs[0].hip.rotation.z = w * amp; legs[1].hip.rotation.z = w2 * amp;
    legs[0].knee.rotation.z = p.walk ? -Math.max(0, -Math.cos(ph)) * (p.run ? 1.3 : .8) : 0; legs[1].knee.rotation.z = p.walk ? -Math.max(0, Math.cos(ph)) * (p.run ? 1.3 : .8) : 0;
    const swing = p.walk ? (p.run ? .8 : .38) : 0;
    arms[0].sh.rotation.z = (p.armL ?? 0) - w * swing; arms[1].sh.rotation.z = (p.armR ?? 0) + w * swing;
    arms[0].sh.rotation.x = p.armLx ?? .1; arms[1].sh.rotation.x = -(p.armRx ?? .1);
    arms[0].el.rotation.z = (p.elL ?? 0) + (p.walk ? (p.run ? 1.1 : .25) : .1); arms[1].el.rotation.z = (p.elR ?? 0) + (p.walk ? (p.run ? 1.1 : .25) : .1);
    const bob = p.walk ? Math.abs(Math.cos(ph)) * (p.run ? .07 : .03) : Math.sin(t * 1.7 + (o.seed || 0)) * .004;
    pelvis.position.y = .95 + bob; spine.position.y = .95 + bob; spine.rotation.z = (p.lean ?? 0) + (p.walk ? (p.run ? .18 : .04) : 0); spine.rotation.x = 0;
    head.rotation.y = (p.look ?? 0) + Math.sin(t * .45 + (o.seed || 0) * 3) * .06; head.rotation.z = p.nod ?? 0;
  };
  g.userData.pose(0);
  const sc = o.child ? (o.height || (.56 + r() * .1)) : (o.height || ((o.skirt || o.bun ? .93 : .97) + r() * .05));
  g.scale.setScalar(sc); if (o.child) head.scale.setScalar(1.28);
  g.traverse(m => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } });
  return g;
}
// extra poses for villagers (on top of L.pose)
export function act(m, t, k, p = {}) { const r = m.userData.rig, u = m.userData;
  // kneel-sit on the floor/mat (seiza): thighs forward, shins folded under; skirts drape over the lap
  if (k === 'floorSit') { for (const l of r.legs) { l.hip.rotation.z = 1.5; l.knee.rotation.z = -2.85; } r.pelvis.position.y = .3 + (p.h || 0); r.spine.position.y = .3 + (p.h || 0); r.spine.rotation.z = .04;
    if (u.sk) { u.lap.visible = true; u.sk.scale.set(.95, .3, 1.15); u.sk.position.y = -.16; u.band.visible = false; } }
  // after L.pose(..., {sit:true}) on a bench/chair: cover the thighs with the skirt
  if (k === 'lap') { if (u.sk) u.lap.visible = true; }
  if (k === 'dig') { const s = Math.sin(t * p.rate || t * 3); r.spine.rotation.z = -.45 - s * .12; r.arms[0].sh.rotation.z = 1.0 + s * .5; r.arms[1].sh.rotation.z = 1.1 + s * .5; r.arms[0].el.rotation.z = .4; r.arms[1].el.rotation.z = .4; r.head.rotation.z = -.4; }
  if (k === 'sweep') { const s = Math.sin(t * 2.2); r.arms[1].sh.rotation.z = .7; r.arms[1].el.rotation.z = .3; r.arms[1].sh.rotation.x = -.2 - s * .45; r.arms[0].sh.rotation.z = .3; r.arms[0].el.rotation.z = .9; r.spine.rotation.z = -.12; r.head.rotation.z = -.45; }
  if (k === 'crouch') { r.legs[0].hip.rotation.z = 1.9; r.legs[1].hip.rotation.z = 1.7; r.legs[0].knee.rotation.z = -2.3; r.legs[1].knee.rotation.z = -2.3; r.pelvis.position.y = .4; r.spine.position.y = .4; r.spine.rotation.z = -.35; r.head.rotation.z = -.35;
    r.arms[1].sh.rotation.z = 1.2; r.arms[1].el.rotation.z = .3; r.arms[0].sh.rotation.z = .9; r.arms[0].el.rotation.z = .6; }
  if (k === 'carry') { r.arms[0].sh.rotation.z = .5; r.arms[0].el.rotation.z = 1.2; r.arms[1].sh.rotation.z = .5; r.arms[1].el.rotation.z = 1.2; }
  if (k === 'lie') { /* caller rotates body */ r.arms[0].sh.rotation.z = .1; r.arms[1].sh.rotation.z = .1; }
  if (k === 'cheer') { r.arms[0].sh.rotation.z = -2.6 + Math.sin(t * 6) * .3; r.arms[1].sh.rotation.z = -2.6 - Math.sin(t * 6) * .3; r.arms[0].sh.rotation.x = .4; r.arms[1].sh.rotation.x = -.4; }
  if (k === 'lookUp') { r.head.rotation.z = .55; r.neck.rotation.z = .15; }
  if (k === 'lookDown') { r.head.rotation.z = -.55; r.spine.rotation.z = -.15; }
  if (k === 'teach') { r.arms[1].sh.rotation.z = 1.3 + Math.sin(t * 1.5) * .15; r.arms[1].el.rotation.z = .3; r.arms[1].sh.rotation.x = -.3; }
  if (k === 'handsHips') { r.arms[0].sh.rotation.x = .5; r.arms[1].sh.rotation.x = -.5; r.arms[0].el.rotation.z = 1.6; r.arms[1].el.rotation.z = 1.6; r.arms[0].sh.rotation.z = -.2; r.arms[1].sh.rotation.z = -.2; }
}

// ---------- hand tools ----------
export function detector() { const g = new THREE.Group(), blk = mat(0x1e1e22, .5), yel = mat(0xd8b020, .6);
  mesh(new THREE.CylinderGeometry(.012, .012, 1.0, 8), blk, [.38, -.25, 0], [0, 0, 1.0], g);
  mesh(new THREE.BoxGeometry(.1, .06, .05), yel, [.05, -.04, 0], [0, 0, 0], g);
  mesh(new THREE.CylinderGeometry(.13, .13, .025, 20), yel, [.8, -.52, 0], [0, 0, 0], g); return g; }
export function hoe() { const g = new THREE.Group(); mesh(new THREE.CylinderGeometry(.016, .016, 1.2, 8), mat(0x6a4a2a, .8), [0, -.1, 0], [0, 0, 0], g); mesh(new THREE.BoxGeometry(.2, .03, .14), mat(0x4a4a4e, .5, .6), [.1, -.7, 0], [0, 0, 0], g); return g; }

// ---------- vegetation & land ----------
export function karst(h = 120, rad = 50, seed = 1) {
  const r = rng(seed), prof = [], N = 14; for (let i = 0; i <= N; i++) { const t = i / N; const y = t * h; const k = t < .7 ? 1 - t * .18 : (1 - .7 * .18) * Math.max(0, Math.cos((t - .7) / .3 * Math.PI / 2)) ** .6; prof.push(new THREE.Vector2(Math.max(.01, rad * k), y)); }
  prof.push(new THREE.Vector2(0, h + .1)); const geo = new THREE.LatheGeometry(prof, 28); const pos = geo.attributes.position, col = [];
  const rock = new THREE.Color(0x9a948a), rockDk = new THREE.Color(0x6e6a62), green = new THREE.Color(0x4e6a34), green2 = new THREE.Color(0x3a5428);
  for (let i = 0; i < pos.count; i++) { const x = pos.getX(i), y = pos.getY(i), z = pos.getZ(i), a = Math.atan2(z, x); const n = 1 + .14 * Math.sin(a * 5 + seed) + .08 * Math.sin(a * 11 + y * .07 + seed * 2) + .05 * Math.sin(y * .15 + a * 3);
    pos.setX(i, x * n); pos.setZ(i, z * n); pos.setY(i, y * (1 + .1 * Math.sin(a * 3 + seed * 1.3))); }
  geo.computeVertexNormals(); const nrm = geo.attributes.normal;
  for (let i = 0; i < pos.count; i++) { const up = nrm.getY(i), y = pos.getY(i) / h, nn = (Math.sin(i * 12.9898 + seed) * 43758.5) % 1; let c = up > .45 || (y > .55 && up > .15) ? (Math.abs(nn) > .5 ? green : green2) : (Math.abs(nn) > .6 ? rockDk : rock); if (y < .08) c = green2; col.push(c.r, c.g, c.b); }
  geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  const m = new THREE.Mesh(geo, toon(0xffffff, { vertexColors: true })); m.userData.noToon = true; m.castShadow = true; m.receiveShadow = true; return m; }
export function karstRange(n, x0, x1, z0, z1, seed = 5, hs = [60, 180]) { const g = new THREE.Group(), r = rng(seed); for (let i = 0; i < n; i++) { const h = lerp(hs[0], hs[1], r()); const k = karst(h, h * lerp(.35, .55, r()), seed * 10 + i); k.position.set(lerp(x0, x1, r()), -2, lerp(z0, z1, r())); k.rotation.y = r() * 6; g.add(k); } return g; }
// instanced tropical trees: broadleaf, palm and banana
const LEAF = [0x3e6a2a, 0x4e7a32, 0x355a24, 0x5a8238];
export function jungle(n, x0, x1, z0, z1, seed = 7, o = {}) { const g = new THREE.Group(), r = rng(seed), d = new THREE.Object3D();
  const trunkG = new THREE.CylinderGeometry(.18, .3, 1, 6); trunkG.translate(0, .5, 0);
  const blobG = new THREE.IcosahedronGeometry(1, 1); const trunkM = toon(0x5a4632), blobM = toon(0xffffff);
  // same random sequence as before; instances are bucketed into 50 m tiles so off-screen / out-of-shadow tiles are culled
  const CH = 50, tiles = new Map(), c = new THREE.Color(); const tile = (x, z) => { const k = Math.floor(x / CH) + ',' + Math.floor(z / CH); if (!tiles.has(k)) tiles.set(k, { t: [], b: [] }); return tiles.get(k); };
  for (let i = 0; i < n; i++) { let x = lerp(x0, x1, r()), z = lerp(z0, z1, r()); const skip = !!(o.avoid && o.avoid(x, z));
    const h = lerp(o.hmin ?? 5, o.hmax ?? 14, r()); d.position.set(x, 0, z); d.scale.set(1 + h * .04, h * .75, 1 + h * .04); d.rotation.set(0, 0, (r() - .5) * .1); d.updateMatrix(); const T = skip ? null : tile(x, z); if (T) T.t.push(d.matrix.clone());
    for (let k = 0; k < 4; k++) { const sc = h * lerp(.22, .36, r()); d.position.set(x + (r() - .5) * h * .4, h * .72 + (r() - .2) * h * .25, z + (r() - .5) * h * .4); d.scale.set(sc, sc * .8, sc); d.rotation.set(r(), r(), r()); d.updateMatrix(); c.set(LEAF[Math.floor(r() * LEAF.length)]); if (T) T.b.push([d.matrix.clone(), c.clone()]); } }
  for (const { t, b } of tiles.values()) { if (!t.length) continue; const tm = new THREE.InstancedMesh(trunkG, trunkM, t.length), bm = new THREE.InstancedMesh(blobG, blobM, b.length);
    t.forEach((m, i) => tm.setMatrixAt(i, m)); b.forEach(([m, col], i) => { bm.setMatrixAt(i, m); bm.setColorAt(i, col); });
    [tm, bm].forEach(m => { m.castShadow = true; m.receiveShadow = true; m.userData.noToon = true; m.instanceMatrix.needsUpdate = true; if (m.instanceColor) m.instanceColor.needsUpdate = true; m.computeBoundingSphere(); g.add(m); }); }
  return g; }
export function palm(h = 8, seed = 1) { const g = new THREE.Group(), r = rng(seed), tr = toon(0x7a6448), lf = toon(0x4e8034, { side: THREE.DoubleSide });
  const curve = new THREE.QuadraticBezierCurve3(V3(0, 0, 0), V3(h * .15, h * .5, 0), V3(h * .08, h, 0)); mesh(new THREE.TubeGeometry(curve, 8, .16, 6), tr, [0, 0, 0], [0, 0, 0], g);
  for (let i = 0; i < 9; i++) { const a = i / 9 * Math.PI * 2 + r(); const lg = new THREE.PlaneGeometry(3.2, .55, 6, 1); lg.translate(1.6, 0, 0); const p = lg.attributes.position; for (let k = 0; k < p.count; k++) { const x = p.getX(k); p.setY(k, p.getY(k) * (1 - x / 3.6) - x * x * .09); } lg.computeVertexNormals();
    const leaf = mesh(lg, lf, [h * .08, h, 0], [0, -a, .25], g); leaf.rotation.order = 'YXZ'; leaf.rotation.x = -Math.PI / 2 + .2; leaf.userData.noOutline = true; }
  g.rotation.y = r() * 6; g.traverse(m => m.isMesh && (m.userData.noToon = true)); return g; }
export function banana(seed = 1) { const g = new THREE.Group(), r = rng(seed), lf = toon(0x5e9a3a, { side: THREE.DoubleSide }); mesh(new THREE.CylinderGeometry(.1, .14, 1.6, 6), toon(0x7a8a4a), [0, .8, 0], [0, 0, 0], g);
  for (let i = 0; i < 6; i++) { const a = i / 6 * Math.PI * 2 + r(); const lg = new THREE.PlaneGeometry(1.8, .5, 4, 1); lg.translate(.9, 0, 0); const p = lg.attributes.position; for (let k = 0; k < p.count; k++) { const x = p.getX(k); p.setZ(k, -x * x * .12); } lg.computeVertexNormals(); const l = mesh(lg, lf, [0, 1.5, 0], [0, 0, 0], g); l.rotation.order = 'YZX'; l.rotation.y = a; l.rotation.z = .5; l.userData.noOutline = true; }
  g.traverse(m => m.isMesh && (m.userData.noToon = true)); return g; }
// rice paddies: raised water (no z-fighting), dikes and rice tufts
export function paddies(cols, rows, cw = 14, cd = 10, o = {}) { const g = new THREE.Group(), r = rng(o.seed || 3), dike = toon(0x7a6a48), tufts = [];
  const water = toon(o.water ?? 0x6a8a84, { transparent: false }); water.polygonOffset = true; water.polygonOffsetFactor = -2;
  for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) { const x = (i - cols / 2 + .5) * cw, z = (j - rows / 2 + .5) * cd, h = (o.terrace ? j * .5 : 0);
    const w = mesh(new THREE.PlaneGeometry(cw - .6, cd - .6), water, [x, .12 + h, z], [-Math.PI / 2, 0, 0], g); w.userData.noToon = true; w.castShadow = false;
    if (h) mesh(new THREE.BoxGeometry(cw, h, cd), toon(0x6a5a3e), [x, h / 2, z], [0, 0, 0], g).userData.noToon = true;
    for (const [dx, dz, sx, sz] of [[0, cd / 2, cw, .5], [0, -cd / 2, cw, .5], [cw / 2, 0, .5, cd], [-cw / 2, 0, .5, cd]]) { const dm = mesh(new THREE.BoxGeometry(sx, .3, sz), dike, [x + dx, .15 + h, z + dz], [0, 0, 0], g); dm.userData.noToon = true; }
    if (o.rice !== false) for (let k = 0; k < (o.density ?? 40); k++) tufts.push([x + (r() - .5) * (cw - 1.2), .12 + h, z + (r() - .5) * (cd - 1.2)]); }
  if (tufts.length) { const tg = new THREE.ConeGeometry(.12, .5, 5); tg.translate(0, .25, 0); const im = new THREE.InstancedMesh(tg, toon(o.riceC ?? 0x7aa83a), tufts.length), d = new THREE.Object3D();
    tufts.forEach((p, i) => { d.position.set(...p); d.scale.setScalar(.7 + r() * .6); d.updateMatrix(); im.setMatrixAt(i, d.matrix); }); im.userData.noToon = true; g.add(im); g.userData.rice = im; }
  return g; }

// ---------- buildings ----------
function corrugatedTex(c1 = '#9a9a96', c2 = '#7a7a76', rust = .3) { const cv = document.createElement('canvas'); cv.width = 256; cv.height = 256; const x = cv.getContext('2d'); for (let i = 0; i < 32; i++) { x.fillStyle = i % 2 ? c1 : c2; x.fillRect(i * 8, 0, 8, 256); } const rr = rng(4); for (let i = 0; i < 60 * rust; i++) { x.fillStyle = `rgba(130,70,30,${rr() * .4})`; x.fillRect(rr() * 256, rr() * 256, 6 + rr() * 30, 4 + rr() * 14); } const t = new THREE.CanvasTexture(cv); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace; return t; }
export function roofPrism(w, d, h, m) { const sh = new THREE.Shape(); sh.moveTo(-d / 2, 0); sh.lineTo(0, h); sh.lineTo(d / 2, 0); sh.lineTo(-d / 2, 0); const geo = new THREE.ExtrudeGeometry(sh, { depth: w, bevelEnabled: false }); geo.translate(0, 0, -w / 2); geo.rotateY(Math.PI / 2); return new THREE.Mesh(geo, m); }
export function school(o = {}) { const g = new THREE.Group(), W = o.w || 22, D = 7, H = 3.2;
  const wall = L.pbr('grey_plaster_02', [W / 4, 1], { color: o.wall ?? 0xe8d8a0 }), base = mat(0x8a8478, .9), blue = mat(0x2a5a8a, .7), post = mat(0xd8d0c0, .8);
  mesh(new THREE.BoxGeometry(W + 2, .5, D + 3), base, [0, .25, .8], [0, 0, 0], g);
  mesh(new THREE.BoxGeometry(W, H, D), wall, [0, .5 + H / 2, 0], [0, 0, 0], g);
  const tex = corrugatedTex(); tex.repeat.set(W / 2, 1); const roofM = new THREE.MeshStandardMaterial({ map: tex, roughness: .5, metalness: .3, side: THREE.DoubleSide });
  for (const s of [-1, 1]) { const rf = mesh(new THREE.PlaneGeometry(W + 2.4, 6.4), roofM, [0, .5 + H + 1.15, s * 2.6 + .8 * 0], [s * -Math.PI / 2 + s * .36 * 0, 0, 0], g); rf.rotation.set(-Math.PI / 2 + s * (Math.PI / 2 - 1.22), 0, 0); rf.position.set(0, .5 + H + 1.0, s * 2.75 + (s > 0 ? 1.1 : 0)); }
  // gable ends
  for (const x of [-W / 2, W / 2]) { const gm = roofPrism(.2, D, 2.2, wall); gm.position.set(x, .5 + H, 0); g.add(gm); }
  // veranda posts + doors/windows facing +z
  for (let i = 0; i <= 6; i++) mesh(new THREE.BoxGeometry(.25, H + .5, .25), post, [-W / 2 + i * W / 6, .5 + (H + .5) / 2, D / 2 + 2.2], [0, 0, 0], g);
  for (let i = 0; i < 3; i++) { const x = -W / 2 + (i + .5) * W / 3; mesh(new THREE.BoxGeometry(1.2, 2.3, .1), blue, [x - 1.6, .5 + 1.15, D / 2 + .05], [0, 0, 0], g);
    for (const dx of [.6, 2.4]) { mesh(new THREE.BoxGeometry(1.3, 1.1, .1), mat(0x1a1a1e, .5), [x + dx - .6, .5 + 1.7, D / 2 + .05], [0, 0, 0], g); for (const s of [-1, 1]) mesh(new THREE.BoxGeometry(.65, 1.2, .06), blue, [x + dx - .6 + s * .98, .5 + 1.7, D / 2 + .1], [0, 0, 0], g); } }
  if (o.sign !== false) { const st = TT([o.sign || 'NACHAT PRIMARY SCHOOL'], { w: 1024, h: 128, bg: '#2a5a8a', fg: '#f2ead8', size: 64 }); L.plate(5.5, .7, st, g, [0, .5 + H + .05, D / 2 + .12]); }
  return g; }
export function laoFlagDraw(x) { x.fillStyle = '#c8241c'; x.fillRect(0, 0, 128, 80); x.fillStyle = '#1e3a8a'; x.fillRect(0, 20, 128, 40); x.fillStyle = '#f2f0ea'; x.beginPath(); x.arc(64, 40, 16, 0, 7); x.fill(); }
export function royalLaoDraw(x) { x.fillStyle = '#c8241c'; x.fillRect(0, 0, 128, 80); x.fillStyle = '#f2f0ea'; x.fillRect(44, 54, 40, 4); for (const dx of [-12, 0, 12]) { x.beginPath(); x.ellipse(64 + dx, 36, 9, 11, 0, 0, 7); x.fill(); } x.fillRect(48, 40, 32, 12); x.beginPath(); x.moveTo(52, 18); x.lineTo(64, 6); x.lineTo(76, 18); x.fill(); }
export function plDraw(x) { x.fillStyle = '#c8241c'; x.fillRect(0, 0, 128, 80); x.fillStyle = '#1e3a8a'; x.fillRect(0, 20, 128, 40); x.fillStyle = '#f2f0ea'; x.beginPath(); x.arc(64, 40, 16, 0, 7); x.fill(); }
export function stiltHouse(o = {}) { const g = new THREE.Group(), r = rng(o.seed || 1), W = o.w || 7, D = o.d || 5, H0 = o.h0 ?? 1.9, H = 2.4;
  const wood = L.pbr('brown_planks_05', [2, 1], { color: o.wood ?? 0x9a7a54 }), postM = mat(0x5a4430, .9), thatch = mat(o.roofC ?? 0x9a8458, 1);
  for (const x of [-W / 2 + .2, 0, W / 2 - .2]) for (const z of [-D / 2 + .2, D / 2 - .2]) mesh(new THREE.CylinderGeometry(.11, .13, H0 + .3, 6), o.casings ? mat(0x5a5e4a, .5, .6) : postM, [x, (H0 + .3) / 2, z], [0, 0, 0], g);
  mesh(new THREE.BoxGeometry(W + .6, .15, D + .6), wood, [0, H0, 0], [0, 0, 0], g);
  if (!o.ruined) { mesh(new THREE.BoxGeometry(W, H, D), wood, [0, H0 + H / 2, 0], [0, 0, 0], g); const rf = roofPrism(W + 1.4, D + 2.2, 2.6, thatch); rf.position.y = H0 + H; g.add(rf);
    mesh(new THREE.BoxGeometry(.9, 1.8, .06), mat(0x2a1e14, .9), [W / 4, H0 + .95, D / 2 + .02], [0, 0, 0], g); mesh(new THREE.BoxGeometry(.9, .7, .06), mat(0x2a1e14, .9), [-W / 4, H0 + 1.4, D / 2 + .02], [0, 0, 0], g);
    // ladder
    const lad = new THREE.Group(); for (const s of [-.3, .3]) mesh(new THREE.BoxGeometry(.07, 2.4, .07), postM, [s, 0, 0], [0, 0, 0], lad); for (let i = 0; i < 6; i++) mesh(new THREE.BoxGeometry(.6, .05, .06), postM, [0, -1 + i * .38, 0], [0, 0, 0], lad); lad.position.set(W / 4, H0 / 2, D / 2 + .7); lad.rotation.x = -.4; g.add(lad); }
  else { // ruin: broken walls, collapsed roof, charred
    const ch = mat(0x2a2420, 1); mesh(new THREE.BoxGeometry(W * .6, H * .5, .12), ch, [-W * .2, H0 + H * .25, -D / 2], [0, 0, .05], g); mesh(new THREE.BoxGeometry(.12, H * .7, D * .7), ch, [W / 2, H0 + H * .35, 0], [0, 0, -.1], g);
    const rf = roofPrism(W * .8, D + 1, 1.6, mat(0x3a3028, 1)); rf.position.set(-.4, H0 - .2, .4); rf.rotation.set(.3, .2, .35); g.add(rf);
    for (let i = 0; i < 10; i++) mesh(new THREE.BoxGeometry(.12, .1, 1 + r() * 2), ch, [(r() - .5) * W, H0 + .1 + r() * .2, (r() - .5) * D], [r(), r() * 3, r()], g); }
  return g; }
export function bunker() { const g = new THREE.Group(), logM = mat(0x5a4632, .9), earth = mat(0x6a5a42, 1);
  const mound = mesh(new THREE.SphereGeometry(3, 18, 8, 0, Math.PI * 2, 0, Math.PI / 2), earth, [0, -.3, 0], [0, 0, 0], g); mound.scale.set(1, .45, .8);
  mesh(new THREE.BoxGeometry(1.4, 1.3, .4), mat(0x0a0806, 1), [0, .5, 2.2], [0, 0, 0], g);
  for (let i = 0; i < 4; i++) mesh(new THREE.CylinderGeometry(.12, .12, 2.2, 6), logM, [-.75 + i * .5, 1.25, 2.3], [0, 0, Math.PI / 2], g).rotation.set(0, Math.PI / 2, Math.PI / 2);
  for (const s of [-1, 1]) mesh(new THREE.CylinderGeometry(.12, .12, 1.4, 6), logM, [s * .78, .6, 2.35], [0, 0, 0], g);
  return g; }
export function scrapPile(seed = 2) { const g = new THREE.Group(), r = rng(seed), ms = [mat(0x5a5e4a, .5, .6), mat(0x6a5a44, .6, .5), mat(0x4a4a44, .5, .6)];
  for (let i = 0; i < 26; i++) { const k = r(); const m = ms[Math.floor(r() * 3)];
    const o = k < .4 ? bombBody(lerp(.6, 1.4, r())) : k < .7 ? mesh(new THREE.CylinderGeometry(.08, .08, .5 + r() * .5, 10), m) : mesh(new THREE.BoxGeometry(.3 + r() * .6, .05, .2 + r() * .4), m);
    o.position.set((r() - .5) * 3, .1 + r() * .7, (r() - .5) * 2.4); o.rotation.set(r() * 3, r() * 3, r() * 3); g.add(o); } return g; }

// ---------- ordnance ----------
export function bombBody(len = 2.2, col = 0x5a6248) { const g = new THREE.Group(), m = mat(col, .55, .3), rr = len * .12;
  const prof = [[0, -len / 2], [rr * .5, -len / 2 + .02], [rr, -len * .3], [rr, len * .2], [rr * .7, len * .38], [rr * .25, len / 2], [0, len / 2]];
  const b = mesh(new THREE.LatheGeometry(prof.map(p => new THREE.Vector2(p[0], p[1])), 16), m, [0, 0, 0], [0, 0, -Math.PI / 2], g);
  mesh(new THREE.CylinderGeometry(rr * 1.01, rr * 1.01, len * .05, 16), mat(0xc8a020, .6), [len * .3, 0, 0], [0, 0, Math.PI / 2], g);
  for (let i = 0; i < 4; i++) { const f = mesh(new THREE.BoxGeometry(len * .2, rr * 1.6, .012), m, [-len * .45, 0, 0], [i * Math.PI / 2, 0, 0], g); f.geometry.translate(0, rr * .8, 0); }
  return g; }
export function bombie(col = 0x7a7a4a) { const g = new THREE.Group(), m = mat(col, .6, .3), r = .04;
  mesh(new THREE.SphereGeometry(r, 14, 10), m, [0, 0, 0], [0, 0, 0], g); mesh(new THREE.TorusGeometry(r, r * .12, 6, 16), mat(0x4a4a30, .6, .3), [0, 0, 0], [Math.PI / 2, 0, 0], g);
  for (let i = 0; i < 4; i++) mesh(new THREE.BoxGeometry(r * .5, r * .12, r * 1.2), m, [Math.cos(i * Math.PI / 2) * r * .9, 0, Math.sin(i * Math.PI / 2) * r * .9], [0, -i * Math.PI / 2, .3], g);
  return g; }
export function canister() { const g = new THREE.Group(), m = mat(0x5a6248, .55, .3), halves = [];
  for (const s of [0, 1]) { const h = new THREE.Group(); const sh = mesh(new THREE.CylinderGeometry(.22, .22, 2.4, 16, 1, true, s * Math.PI, Math.PI), m, [0, 0, 0], [0, 0, Math.PI / 2], h); sh.material.side = THREE.DoubleSide; g.add(h); halves.push(h); }
  const nose = mesh(new THREE.SphereGeometry(.22, 14, 8, 0, Math.PI * 2, 0, Math.PI / 2), m, [1.2, 0, 0], [0, 0, -Math.PI / 2], g); for (let i = 0; i < 4; i++) { const f = mesh(new THREE.BoxGeometry(.5, .5, .015), m, [-1.3, 0, 0], [i * Math.PI / 2, 0, 0], g); f.geometry.translate(0, .25, 0); }
  g.userData.halves = halves; g.userData.nose = nose; return g; }

// ---------- aircraft & vehicles ----------
export function jet(o = {}) { const g = new THREE.Group(), m = mat(o.col ?? 0x6a7258, .5, .3), dk = mat(0x2a2e26, .5, .3), gl = mat(0x2a3a4a, .1, .5);
  mesh(new THREE.CylinderGeometry(.55, .7, 11, 12), m, [0, 0, 0], [0, 0, Math.PI / 2], g); mesh(new THREE.ConeGeometry(.55, 3, 12), m, [7, 0, 0], [0, 0, -Math.PI / 2], g);
  mesh(new THREE.SphereGeometry(.5, 12, 8, 0, Math.PI * 2, 0, Math.PI / 2), gl, [3.6, .35, 0], [0, 0, 0], g).scale.set(2.4, 1, .9);
  const w = new THREE.Shape(); w.moveTo(1.5, 0); w.lineTo(-3.2, 5.6); w.lineTo(-4.6, 5.6); w.lineTo(-3.6, 0); const wg = new THREE.ExtrudeGeometry(w, { depth: .14, bevelEnabled: false }); wg.rotateX(Math.PI / 2);
  for (const s of [1, -1]) { const wm = mesh(wg, m, [0, -.2, 0], [0, 0, 0], g); wm.scale.z = s; }
  const t = new THREE.Shape(); t.moveTo(-3.2, 0); t.lineTo(-5.4, 3); t.lineTo(-6.2, 3); t.lineTo(-5.6, 0); mesh(new THREE.ExtrudeGeometry(t, { depth: .12, bevelEnabled: false }), m, [0, .3, -.06], [0, 0, 0], g);
  for (const s of [1, -1]) { const hs = mesh(new THREE.BoxGeometry(1.6, .08, 2.6), m, [-5, .1, s * 1.5], [s * .3, 0, 0], g); }
  mesh(new THREE.CylinderGeometry(.5, .5, .6, 12), dk, [-5.6, 0, 0], [0, 0, Math.PI / 2], g);
  if (o.bombs !== false) for (const s of [1, -1]) for (const k of [2.2, 3.4]) { const b = bombBody(1.6); b.position.set(-1.5, -.6, s * k); g.add(b); (g.userData.bombs = g.userData.bombs || []).push(b); }
  g.userData.flame = new THREE.Sprite(new THREE.SpriteMaterial({ map: L.FIRE_T, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true })); g.userData.flame.position.set(-6.2, 0, 0); g.userData.flame.scale.set(1.6, .9, 1); g.add(g.userData.flame);
  return g; }
export function bomber(o = {}) { const g = new THREE.Group(), m = mat(o.col ?? 0x8a8c80, .5, .3), dk = mat(0x3a3c36, .5, .3);
  mesh(new THREE.CylinderGeometry(1.5, 1.4, 44, 14), m, [0, 0, 0], [0, 0, Math.PI / 2], g); mesh(new THREE.SphereGeometry(1.5, 14, 10, 0, Math.PI * 2, 0, Math.PI / 2), m, [22, 0, 0], [0, 0, -Math.PI / 2], g).scale.set(1, 2.2, 1);
  const w = new THREE.Shape(); w.moveTo(6, 0); w.lineTo(-8, 28); w.lineTo(-11, 28); w.lineTo(-4, 0); const wg = new THREE.ExtrudeGeometry(w, { depth: .4, bevelEnabled: false }); wg.rotateX(Math.PI / 2);
  for (const s of [1, -1]) { const wm = mesh(wg, m, [0, 1.2, 0], [0, 0, 0], g); wm.scale.z = s; for (const k of [7, 15]) { mesh(new THREE.BoxGeometry(5, 1.1, 2.4), dk, [-k * .5 + 1, -.2, s * k], [0, 0, 0], g); } }
  const t = new THREE.Shape(); t.moveTo(-14, 0); t.lineTo(-20, 12); t.lineTo(-23, 12); t.lineTo(-22, 0); mesh(new THREE.ExtrudeGeometry(t, { depth: .3, bevelEnabled: false }), m, [0, 1, -.15], [0, 0, 0], g);
  for (const s of [1, -1]) mesh(new THREE.BoxGeometry(4, .2, 8), m, [-20, .6, s * 4], [0, 0, 0], g);
  return g; }
export function truck(o = {}) { const g = new THREE.Group(), m = mat(o.col ?? 0x4a5a38, .7), dk = mat(0x1a1a18, .6), can = mat(0x5a5a40, 1);
  mesh(new THREE.BoxGeometry(6.4, .3, 2.2), dk, [0, .9, 0], [0, 0, 0], g); mesh(new THREE.BoxGeometry(1.6, 1.4, 2.1), m, [2.2, 1.85, 0], [0, 0, 0], g); mesh(new THREE.BoxGeometry(1.4, 1, 1.8), m, [3.6, 1.55, 0], [0, 0, 0], g);
  mesh(new THREE.BoxGeometry(1.4, .5, 1.9), mat(0x2a3a4a, .2, .4), [2.9, 2.2, 0], [0, 0, -.2], g);
  mesh(new THREE.BoxGeometry(3.8, .8, 2.3), m, [-1, 1.45, 0], [0, 0, 0], g); const cv = mesh(new THREE.CylinderGeometry(1.15, 1.15, 3.8, 12, 1, false, 0, Math.PI), can, [-1, 1.85, 0], [0, 0, Math.PI / 2], g); cv.rotation.set(0, 0, Math.PI / 2); cv.rotation.x = 0;
  cv.rotation.set(Math.PI / 2, 0, Math.PI / 2); cv.rotation.set(0, Math.PI / 2, 0); cv.geometry.rotateZ(Math.PI / 2); cv.position.y = 1.85; cv.scale.set(1, .9, 1);
  const wheels = []; for (const x of [3.1, -.6, -2.3]) for (const s of [-1, 1]) { const w = mesh(new THREE.CylinderGeometry(.55, .55, .35, 14), dk, [x, .55, s * 1.05], [Math.PI / 2, 0, 0], g); wheels.push(w); }
  g.userData.wheels = wheels; g.userData.update = d => wheels.forEach(w => w.rotation.y = -d / .55); g.userData.lamp = V3(4.35, 1.5, 0);
  return g; }
export function bicycle(o = {}) { const g = new THREE.Group(), m = mat(0x2a2a26, .5, .5), sack = mat(0xb8a878, 1);
  for (const x of [-.55, .55]) mesh(new THREE.TorusGeometry(.33, .025, 6, 20), m, [x, .35, 0], [0, 0, 0], g);
  mesh(new THREE.CylinderGeometry(.02, .02, 1.1, 6), m, [0, .62, 0], [0, 0, Math.PI / 2], g); mesh(new THREE.CylinderGeometry(.02, .02, .6, 6), m, [.25, .5, 0], [0, 0, .7], g); mesh(new THREE.CylinderGeometry(.02, .02, .6, 6), m, [-.25, .5, 0], [0, 0, -.7], g);
  mesh(new THREE.CylinderGeometry(.02, .02, .7, 6), m, [.6, .9, 0], [Math.PI / 2, 0, 0], g); mesh(new THREE.CylinderGeometry(.018, .018, 1.6, 6), m, [-.4, 1.05, .1], [0, 0, 1.2], g);
  for (const s of [-1, 1]) for (let k = 0; k < 2; k++) mesh(new THREE.BoxGeometry(.6, .4, .3), sack, [0, .75 + k * .38, s * .3], [0, 0, (k - .5) * .1], g);
  return g; }

// ---------- cave interior ----------
export function caveTunnel(len = 30, rad = 4, seed = 3, o = {}) { const geo = new THREE.CylinderGeometry(rad, rad, len, 26, 18, true); geo.rotateZ(Math.PI / 2); const p = geo.attributes.position, r = rng(seed), col = [];
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i), z = p.getZ(i), a = Math.atan2(y, z); const n = 1 + .12 * Math.sin(a * 4 + x * .4 + seed) + .07 * Math.sin(a * 9 + x * 1.1) + .05 * Math.sin(x * 2.3 + a * 2);
    let yy = y * n * (o.squash ?? .8); if (yy < -rad * .45) yy = -rad * .45 + (yy + rad * .45) * .05; p.setY(i, yy + rad * .45); p.setZ(i, z * n * (o.wide ?? 1.25)); }
  geo.computeVertexNormals(); const nr = geo.attributes.normal;
  for (let i = 0; i < p.count; i++) { const v = .55 + .1 * Math.sin(i * .7) + (nr.getY(i) < -.5 ? .1 : 0); const c = new THREE.Color(o.col ?? 0x8a8070).multiplyScalar(v); col.push(c.r, c.g, c.b); }
  geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  const m = new THREE.Mesh(geo, toon(0xffffff, { vertexColors: true, side: THREE.BackSide })); m.userData.noToon = true; m.receiveShadow = true;
  const g = new THREE.Group(); g.add(m); if (o.caps !== false) for (const s of [-1, 1]) { if (o.openEnd === s) continue; const cp = mesh(new THREE.SphereGeometry(rad * 1.5, 16, 12), toon(new THREE.Color(o.col ?? 0x8a8070).multiplyScalar(.5).getHex(), { side: THREE.BackSide }), [s * len / 2, rad * .45, 0], [0, 0, 0], g); cp.scale.set(.22, .8, 1.1); cp.userData.noToon = true; }
  const fl = mesh(new THREE.PlaneGeometry(len, rad * 2.4), toon(0x6a5e4e), [0, .02, 0], [-Math.PI / 2, 0, 0], g); fl.userData.noToon = true; return g; }
export function lantern() { const g = new THREE.Group(); mesh(new THREE.CylinderGeometry(.08, .1, .22, 10), mat(0xf0d090, .4, 0, { emissive: 0xffb050, emissiveIntensity: 1.4 }), [0, 0, 0], [0, 0, 0], g); mesh(new THREE.CylinderGeometry(.11, .11, .03, 10), mat(0x2a2a26, .5), [0, .13, 0], [0, 0, 0], g);
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: L.FIRE_T, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, opacity: .45 })); s.scale.setScalar(.9); g.add(s); return g; }
export function bed(o = {}) { const g = new THREE.Group(), fr = mat(o.frame ?? 0x5a6a6a, .5, .5), sh = mat(0xe8e4d8, .9);
  for (const x of [-.95, .95]) for (const z of [-.42, .42]) mesh(new THREE.CylinderGeometry(.025, .025, .55, 6), fr, [x, .27, z], [0, 0, 0], g);
  mesh(new THREE.BoxGeometry(2, .12, .9), sh, [0, .58, 0], [0, 0, 0], g); mesh(new THREE.BoxGeometry(.4, .1, .6), mat(0xf2f0ea, .9), [-.75, .68, 0], [0, 0, 0], g); return g; }
export function blackboard(lines = [], o = {}) { const g = new THREE.Group(); const t = TT(lines, { w: 1024, h: 512, bg: '#1e3a2a', fg: '#e8e8dc', size: o.size || 70 }); L.plate(2.6, 1.3, t, g, [0, 1.6, 0]); mesh(new THREE.BoxGeometry(2.8, .08, .1), mat(0x5a3a20, .8), [0, .92, .04], [0, 0, 0], g); return g; }
export function bench(len = 2) { const g = new THREE.Group(), m = mat(0x6a4a2a, .9); mesh(new THREE.BoxGeometry(len, .06, .35), m, [0, .42, 0], [0, 0, 0], g); for (const x of [-len / 2 + .15, len / 2 - .15]) mesh(new THREE.BoxGeometry(.06, .42, .3), m, [x, .21, 0], [0, 0, 0], g); return g; }
export function sign(lines, o = {}) { const g = new THREE.Group(); mesh(new THREE.BoxGeometry(.06, 1.2, .06), mat(0x5a4a3a, .9), [0, .6, 0], [0, 0, 0], g); const t = TT(lines, { w: 512, h: 384, bg: o.bg || '#c8241c', fg: '#f8f4ea', size: o.size || 80 }); L.plate(.7, .52, t, g, [0, 1.3, .04]); return g; }
export function stake(col = 0xc8241c) { const g = new THREE.Group(); mesh(new THREE.BoxGeometry(.04, .5, .04), mat(col, .7), [0, .25, 0], [0, 0, 0], g); mesh(new THREE.BoxGeometry(.045, .12, .045), mat(0xf2f0ea, .7), [0, .45, 0], [0, 0, 0], g); return g; }
export function tapeLine(a, b, col = 0xe8e8e0) { const d = Math.hypot(b[0] - a[0], b[1] - a[1]); const m = mesh(new THREE.BoxGeometry(d, .02, .05), mat(col, .7), [(a[0] + b[0]) / 2, .2, (a[1] + b[1]) / 2], [0, -Math.atan2(b[1] - a[1], b[0] - a[0]), 0]); return m; }
