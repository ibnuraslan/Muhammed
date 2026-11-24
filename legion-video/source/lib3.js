// ===================== lib3: shared cel-shaded film library =====================
import { THREE, R, W, H, RS, model, pbr, mat, mesh, rng, lerp, clamp, ease, station, forest, smoke, snowfall, TEXP } from './engine.js';
import { track2, locomotive2, boxcar2, person2, GAUGE, RAIL_TOP } from './engine2.js';
export { THREE, R, W, H, model, pbr, mat, mesh, rng, lerp, clamp, ease, station, forest, smoke, snowfall, TEXP, track2, locomotive2, boxcar2, person2, GAUGE, RAIL_TOP };
export const FPS = 24;
export const S = new THREE.Scene(), cam = new THREE.PerspectiveCamera(35, W / H, .05, 4000);
export const hemi = new THREE.HemisphereLight(0xdfe6f0, 0x6a5a48, 1.3); S.add(hemi);
export const sun = new THREE.DirectionalLight(0xfff0dc, 2.4); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); sun.shadow.bias = -.0005; Object.assign(sun.shadow.camera, { left: -45, right: 45, top: 45, bottom: -45, near: 1, far: 300 }); S.add(sun); S.add(sun.target);
export const pl1 = new THREE.PointLight(0xffb060, 0, 14, 1.6), pl2 = new THREE.PointLight(0xff9040, 0, 30, 1.4), pl3 = new THREE.PointLight(0xffd090, 0, 10, 1.6); [pl1, pl2, pl3].forEach(l => S.add(l));
export const U = {}, SETS = {}; export let RIFLE; export const setRifle = r => RIFLE = r;
export const comp = document.createElement('canvas'); comp.width = W; comp.height = H; const cx = comp.getContext('2d', { willReadFrequently: /cpu2d/.test(location.search) });
export const V3 = (x, y, z) => new THREE.Vector3(x, y, z), at = (o, x, y, z, ry = 0) => { o.position.set(x, y, z); o.rotation.y = ry; return o; };
export const GRAD = (() => { const t = new THREE.DataTexture(new Uint8Array([85, 165, 255]), 3, 1, THREE.RedFormat); t.needsUpdate = true; t.minFilter = t.magFilter = THREE.NearestFilter; return t; })();
// ---------- painted sky backdrops ----------
export function paintSky(top, bot, lit, mid, shd, seed, o = {}) {
  const cv = document.createElement('canvas'); cv.width = 1920; cv.height = 1080; const x = cv.getContext('2d'), r = rng(seed);
  const g = x.createLinearGradient(0, 0, 0, 1080); g.addColorStop(0, top); g.addColorStop(.75, bot); g.addColorStop(1, bot); x.fillStyle = g; x.fillRect(0, 0, 1920, 1080);
  if (o.sun) { const sg = x.createRadialGradient(o.sun[0], o.sun[1], 0, o.sun[0], o.sun[1], 600); sg.addColorStop(0, 'rgba(255,240,200,.95)'); sg.addColorStop(.1, 'rgba(255,215,160,.6)'); sg.addColorStop(1, 'rgba(255,200,150,0)'); x.fillStyle = sg; x.fillRect(0, 0, 1920, 1080); }
  if (o.stars) { x.fillStyle = '#fff'; for (let i = 0; i < 300; i++) { x.globalAlpha = r() * .8; x.fillRect(r() * 1920, r() * 700, 2, 2); } x.globalAlpha = 1; }
  const banks = o.banks || [[350, 520, 600, 240, 70], [1100, 470, 700, 220, 70], [1650, 560, 500, 260, 60]];
  banks.forEach(([cx0, cy0, bw, bh, n]) => { const P = []; for (let k = 0; k < n; k++) { const a = r() * Math.PI, rr = Math.sqrt(r()); P.push([cx0 + Math.cos(a) * bw * rr * (r() < .5 ? -1 : 1) * .5 + (r() - .5) * bw * .4, cy0 - Math.sin(a) * bh * rr + bh * .1, (.1 + r() * .2) * Math.min(bw, bh * 2)]); } P.sort((a, b) => b[1] - a[1]);
    P.forEach(([px, py, rad]) => { x.fillStyle = shd; x.beginPath(); x.arc(px + rad * .08, py + rad * .1, rad, 0, 7); x.fill(); }); P.forEach(([px, py, rad]) => { x.fillStyle = mid; x.beginPath(); x.arc(px - rad * .1, py - rad * .12, rad * .86, 0, 7); x.fill(); }); P.forEach(([px, py, rad]) => { x.fillStyle = lit; x.beginPath(); x.arc(px - rad * .26, py - rad * .3, rad * .6, 0, 7); x.fill(); }); });
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; return t;
}
export const SKY = {};
// ---------- helpers: fire, sparks, flags, props ----------
export function glowTex(stops) { const cv = document.createElement('canvas'); cv.width = cv.height = 64; const x = cv.getContext('2d'), g = x.createRadialGradient(32, 32, 0, 32, 32, 32); stops.forEach(([o, c]) => g.addColorStop(o, c)); x.fillStyle = g; x.fillRect(0, 0, 64, 64); return new THREE.CanvasTexture(cv); }
export const FIRE_T = glowTex([[0, 'rgba(255,255,220,1)'], [.25, 'rgba(255,200,80,.9)'], [.6, 'rgba(255,90,20,.5)'], [1, 'rgba(255,40,0,0)']]);
export const SPARK_T = glowTex([[0, 'rgba(255,255,230,1)'], [.3, 'rgba(255,200,90,.8)'], [1, 'rgba(255,120,30,0)']]);
export function fire(n = 14, size = 3) { const g = new THREE.Group(), sp = []; for (let i = 0; i < n; i++) { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: FIRE_T, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, fog: false })); g.add(s); sp.push(s); }
  g.userData.update = t => sp.forEach((s, i) => { const r = rng(i + 3), ph = (t * (1.2 + r()) + r()) % 1; s.position.set((r() - .5) * size * .9, ph * size * 1.4, (r() - .5) * size * .5); const sc = size * (1 - ph * .7) * (.7 + r() * .6); s.scale.set(sc, sc * 1.3, 1); s.material.opacity = (1 - ph) * .9; }); return g; }
export function sparks(n = 60) { const g = new THREE.Group(), sp = []; for (let i = 0; i < n; i++) { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: SPARK_T, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true })); s.scale.setScalar(.08); g.add(s); sp.push(s); }
  g.userData.update = (t, on = 1) => sp.forEach((s, i) => { const r = rng(i + 9), life = .5 + r() * .4, ph = ((t + r() * life) % life) / life, vx = (r() * 2 + 1) * 3, vy = 1 + r() * 3, vz = (r() - .5) * 2; s.position.set(vx * ph * life, vy * ph * life - 4.9 * Math.pow(ph * life, 2), vz * ph * life); s.material.opacity = on * (1 - ph); s.scale.setScalar(.05 + .07 * (1 - ph)); }); return g; }
export function flag(w, h, stripes, o = {}) { const cv = document.createElement('canvas'); cv.width = 256; cv.height = 160; const x = cv.getContext('2d'); x.scale(2, 2); stripes.forEach((c, i) => { x.fillStyle = c; if (o.vertical) x.fillRect(i * 128 / stripes.length, 0, 128 / stripes.length + 1, 80); else x.fillRect(0, i * 80 / stripes.length, 128, 80 / stripes.length + 1); }); if (o.draw) o.draw(x); const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace;
  const geo = new THREE.PlaneGeometry(w, h, 24, 10); geo.translate(w / 2, -h / 2, 0); const m = new THREE.Mesh(geo, new THREE.MeshToonMaterial({ map: t, side: THREE.DoubleSide, gradientMap: GRAD })); m.castShadow = true; const base = geo.attributes.position.array.slice();
  m.userData.update = (t, k = .2) => { const p = geo.attributes.position.array; for (let i = 0; i < p.length; i += 3) { const u = base[i] / w; p[i + 2] = Math.sin(base[i] * 2.4 - t * 6) * k * u + Math.sin(base[i + 1] * 3 + t * 4) * .05 * u; } geo.attributes.position.needsUpdate = true; geo.computeVertexNormals(); }; return m; }
export function poleWithFlag(h, f) { const g = new THREE.Group(); mesh(new THREE.CylinderGeometry(.05, .06, h, 10), mat(0x3a2a1e, .8), [0, h / 2, 0], [0, 0, 0], g); mesh(new THREE.SphereGeometry(.09, 10, 8), mat(0xc9a24d, .3, .9), [0, h + .05, 0], [0, 0, 0], g); g.add(f); f.position.y = h; return g; }
export function capMesh() { const g = new THREE.Group(); mesh(new THREE.CylinderGeometry(.135, .113, .07, 24), mat(0x5e5a3c, .9), [0, .035, 0], [0, 0, 0], g); mesh(new THREE.CylinderGeometry(.116, .116, .018, 24), mat(0xf2f0ea, .7), [0, .012, 0], [0, 0, 0], g); mesh(new THREE.CylinderGeometry(.116, .116, .018, 24), mat(0xc8241c, .7), [0, -.004, 0], [0, 0, 0], g); mesh(new THREE.CylinderGeometry(.115, .115, .012, 20, 1, false, 0, Math.PI), mat(0x0c0c0c, .3), [.04, -.01, 0], [0, 0, -.15], g); g.scale.setScalar(1.15); return g; }
export function hand(grip = .9) { const g = new THREE.Group(), sk = mat(0xc8906c, .6), sl = mat(0x5c5a40, .95); mesh(new THREE.CylinderGeometry(.06, .065, .4, 14), sl, [0, -.25, 0], [0, 0, 0], g); const palm = mesh(new THREE.BoxGeometry(.09, .1, .04), sk, [0, 0, 0], [0, 0, 0], g); for (let k = 0; k < 4; k++) { const f = new THREE.Group(); f.position.set(-.034 + k * .023, .05, .02); g.add(f); mesh(new THREE.CapsuleGeometry(.011, .045, 4, 8), sk, [0, .03, 0], [0, 0, 0], f); f.rotation.x = grip * 1.5; } const th = mesh(new THREE.CapsuleGeometry(.013, .04, 4, 8), sk, [.05, .0, .03], [0, 0, -.9], g); return g; }
export function armoredWagon() { const b = boxcar2({ stove: false }); const steel = mat(0x5a5e58, .6, .4), dk = mat(0x2e302c, .7, .3); b.traverse(m => { if (m.isMesh && m.material && m.material.map && m.position.y > 1.5) m.material = steel; });
  const by0 = b.userData.by0; mesh(new THREE.BoxGeometry(7.6, .5, 3.0), steel, [0, by0 + 2.75, 0], [0, 0, 0], b); const tur = new THREE.Group(); tur.position.set(1.5, by0 + 3.0, 0); b.add(tur); mesh(new THREE.CylinderGeometry(1.0, 1.15, .9, 20), steel, [0, .45, 0], [0, 0, 0], tur); const barrel = mesh(new THREE.CylinderGeometry(.09, .11, 2.6, 12), dk, [1.6, .55, 0], [0, 0, Math.PI / 2], tur);
  for (const z of [-1.42, 1.42]) for (const x of [-2.6, -1.2, 2.6]) mesh(new THREE.BoxGeometry(.4, .14, .06), mat(0x0c0c0c, 1), [x, by0 + 1.7, z], [0, 0, 0], b);
  b.userData.turret = tur; b.userData.muzzle = V3(2.95, .55, 0); return b; }
// ---------- map overlay (2D) ----------
export let LAND = null; export const setLand = l => LAND = l;
export const CITIES = [['Penza', 45.0, 53.2], ['Samara', 50.1, 53.2], ['Ufa', 56.0, 54.7], ['Chelyabinsk', 61.4, 55.16], ['Omsk', 73.4, 54.99], ['Novonikolaevsk', 82.9, 55.03], ['Krasnoyarsk', 92.9, 56.0], ['Irkutsk', 104.3, 52.29], ['Chita', 113.5, 52.03], ['Vladivostok', 131.9, 43.12]];
export function mapProj(lon0, lon1, lat0, lat1, x0, y0, w, h) { const k = Math.cos((lat0 + lat1) / 2 * Math.PI / 180); return (lon, lat) => [x0 + (lon - lon0) / (lon1 - lon0) * w, y0 + (lat1 - lat) / (lat1 - lat0) * h]; }
export function drawMap(c, pr, o = {}) {
  c.fillStyle = o.sea || '#2e3d4c'; c.fillRect(o.x0 ?? 0, o.y0 ?? 0, o.w ?? W, o.h ?? H);
  c.save(); c.beginPath(); c.rect(o.x0 ?? 0, o.y0 ?? 0, o.w ?? W, o.h ?? H); c.clip();
  LAND.features.forEach(f => { const polys = f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates;
    c.beginPath(); polys.forEach(poly => poly.forEach(ring => { ring.forEach(([lon, lat], i) => { const [px, py] = pr(lon, lat); i ? c.lineTo(px, py) : c.moveTo(px, py); }); c.closePath(); }));
    const isRu = f.properties && /Russia/.test(f.properties.name); c.fillStyle = isRu ? (o.ru || '#c9b48a') : (o.land || '#a8987a'); c.fill(); if (!o.noBorders) { c.strokeStyle = 'rgba(40,30,20,.5)'; c.lineWidth = 1; c.stroke(); } });
  c.restore();
  const g = c.createRadialGradient(W / 2, H / 2, H * .3, W / 2, H / 2, W * .7); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(10,6,2,.6)'); c.fillStyle = g; c.fillRect(0, 0, W, H);
}
export function flameIcon(c, x, y, s, t) { c.save(); c.translate(x, y); c.scale(s, s); const f = 1 + Math.sin(t * 14 + x) * .12; c.globalCompositeOperation = 'lighter'; const g = c.createRadialGradient(0, -8, 0, 0, -8, 30 * f); g.addColorStop(0, 'rgba(255,240,180,1)'); g.addColorStop(.4, 'rgba(255,140,40,.8)'); g.addColorStop(1, 'rgba(255,60,0,0)'); c.fillStyle = g; c.beginPath(); c.arc(0, -8, 30 * f, 0, 7); c.fill(); c.restore(); }
export function routeMap(c, lt, d, t) { const pr = mapProj(25, 145, 38, 70, -40, 60, W + 80, H - 120); drawMap(c, pr);
  const pts = CITIES.map(([n, lon, lat]) => [n, ...pr(lon, lat)]), prog = clamp(lt / (d * .85)) * (pts.length - 1);
  c.strokeStyle = 'rgba(60,40,30,.6)'; c.lineWidth = 3; c.setLineDash([10, 8]); c.beginPath(); pts.forEach(([, x, y], i) => i ? c.lineTo(x, y) : c.moveTo(x, y)); c.stroke(); c.setLineDash([]);
  c.strokeStyle = '#c8241c'; c.lineWidth = 7; c.shadowColor = 'rgba(255,80,40,.8)'; c.shadowBlur = 14; c.beginPath(); for (let i = 0; i <= Math.floor(prog); i++) { const [, x, y] = pts[i]; i ? c.lineTo(x, y) : c.moveTo(x, y); } const fi = Math.floor(prog), fr = prog - fi; if (fi < pts.length - 1) { c.lineTo(lerp(pts[fi][1], pts[fi + 1][1], fr), lerp(pts[fi][2], pts[fi + 1][2], fr)); } c.stroke(); c.shadowBlur = 0;
  pts.forEach(([n, x, y], i) => { if (i <= prog) { flameIcon(c, x, y, .9, t); c.fillStyle = '#f2e8d2'; c.font = '600 22px Cinzel, serif'; c.textAlign = 'center'; c.fillText(n.toUpperCase(), x, y + 34); } });
  c.fillStyle = '#f2e8d2'; c.font = '700 40px Cinzel, serif'; c.textAlign = 'left'; c.globalAlpha = clamp(lt / .6); c.fillText('THE TRANS-SIBERIAN RAILWAY', 60, 90); c.font = '26px Cinzel, serif'; c.fillText('≈ 7,000 KM  ·  SUMMER 1918', 62, 130); c.globalAlpha = 1; }
export function insetMap(c, x0, y0, w, h, lt, t) { const pr = mapProj(30, 140, 38, 66, x0, y0, w, h); c.save(); c.shadowColor = 'rgba(0,0,0,.6)'; c.shadowBlur = 20; c.fillStyle = '#000'; c.fillRect(x0, y0, w, h); c.restore(); drawMap(c, pr, { x0, y0, w, h });
  c.strokeStyle = '#f2e8d2'; c.lineWidth = 3; c.strokeRect(x0, y0, w, h); const a = pr(61.4, 55.16), b = pr(131.9, 43.12), p = clamp(lt / 2.6);
  c.strokeStyle = '#c8241c'; c.lineWidth = 5; c.setLineDash([12, 8]); c.beginPath(); c.moveTo(...a); c.quadraticCurveTo((a[0] + b[0]) / 2, a[1] - 60, lerp(a[0], b[0], p), lerp(a[1], b[1], p) - Math.sin(p * Math.PI) * 30); c.stroke(); c.setLineDash([]);
  c.fillStyle = '#f2e8d2'; c.font = '600 18px Cinzel, serif'; c.textAlign = 'center'; c.fillText('CHELYABINSK', a[0], a[1] - 12); if (p > .9) c.fillText('VLADIVOSTOK →', b[0] - 30, b[1] + 26); }
export function arcMap(c, lt, t, a) { const pr = mapProj(5, 125, 35, 68, 0, 0, W, H); c.globalAlpha = a; drawMap(c, pr, { ru: '#c4b088', land: '#a8987a' });
  const A = pr(104.3, 52.29), B = pr(14.43, 50.08), p = clamp(lt / 2.5); c.strokeStyle = '#f2e8d2'; c.lineWidth = 5; c.setLineDash([16, 10]); c.beginPath(); for (let i = 0; i <= 60 * p; i++) { const q = i / 60, x = lerp(A[0], B[0], q), y = lerp(A[1], B[1], q) - Math.sin(q * Math.PI) * 220; i ? c.lineTo(x, y) : c.moveTo(x, y); } c.stroke(); c.setLineDash([]);
  [[A, 'SIBERIA'], [B, 'PRAGUE']].forEach(([[x, y], n], i) => { if (i === 0 || p > .95) { c.fillStyle = '#c8241c'; c.beginPath(); c.arc(x, y, 10, 0, 7); c.fill(); c.fillStyle = '#f2e8d2'; c.font = '700 30px Cinzel, serif'; c.textAlign = 'center'; c.fillText(n, x, y + 48); } });
  if (p > .6) { c.fillStyle = '#f2e8d2'; c.font = '700 54px Cinzel, serif'; c.textAlign = 'center'; c.globalAlpha = a * clamp((p - .6) / .3); c.fillText('≈ 9,000 KM', W / 2, 140); } c.globalAlpha = 1; }
export function look(sky, fog, hemiI = 1.6, sunI = 2.4, sunCol = 0xfff0dc, sunPos = [-40, 60, 30], target = [0, 0, 0], hemiCols = [0xdfe6f0, 0x6a5a48]) {
  S.background = SKY[sky]; S.fog = fog ? new THREE.FogExp2(fog[0], fog[1]) : null; hemi.intensity = hemiI; hemi.color.set(hemiCols[0]); hemi.groundColor.set(hemiCols[1]); sun.intensity = sunI; sun.color.set(sunCol);
  sun.target.position.set(...target); sun.position.set(target[0] + sunPos[0], target[1] + sunPos[1], target[2] + sunPos[2]); [pl1, pl2, pl3].forEach(l => l.intensity = 0); }
export function camTo(lt, d, a, b, fov = [35, 35], shake = 0) { const p = ease(clamp(lt / d)); cam.position.set(lerp(a[0], b[0], p) + Math.sin(lt * 17) * shake, lerp(a[1], b[1], p) + Math.cos(lt * 13) * shake, lerp(a[2], b[2], p)); cam.lookAt(lerp(a[3], b[3], p), lerp(a[4], b[4], p), lerp(a[5], b[5], p)); cam.fov = lerp(fov[0], fov[1], p); cam.updateProjectionMatrix(); }
export const smk = (s, obj, local, t) => { const v = local.clone(); obj.localToWorld(v); s.userData.update(t, v); };
export const grain = (() => { const cv = document.createElement('canvas'); cv.width = 480; cv.height = 270; const x = cv.getContext('2d'), id = x.createImageData(480, 270), r = rng(9); for (let i = 0; i < id.data.length; i += 4) { const v = 128 + (r() + r() - 1) * 90; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 255; } x.putImageData(id, 0, 0); return cv; })();
export function caption(c, s1, s2, a) { c.save(); c.globalAlpha = a; c.fillStyle = '#f2e8d2'; c.shadowColor = 'rgba(0,0,0,.7)'; c.shadowBlur = 12; c.textAlign = 'left'; c.font = '700 44px Cinzel, serif'; c.fillText(s1, 90, H - 150); c.font = '28px Cinzel, serif'; c.fillText(s2, 92, H - 105); c.fillRect(92, H - 92, 360 * a, 3); c.restore(); }
// ===================== lib3 additions =====================
export const FX = [];                       // objects hidden at the start of every frame
export const fx = o => { FX.push(o); S.add(o); o.visible = false; return o; };
export function show(...n) { Object.entries(SETS).forEach(([k, g]) => g.visible = n.includes(k)); }
export function addSet(name, x, z) { const g = new THREE.Group(); g.position.set(x, 0, z); S.add(g); SETS[name] = g; return g; }
// per-set ground (big enough that it never ends in frame)
const GM = {};
export function groundMat(kind) { if (GM[kind]) return GM[kind];
  const src = { dirt: ['dirt', 0xb8ab92], snow: ['snow_02', 0xf4f6fa], grass: ['dirt', 0x8a9a62], mud: ['dirt', 0x7a6a52], cobble: ['gravel', 0x9a948a], sand: ['dirt', 0xc8b48a] }[kind];
  const t = pbr(src[0], [400, 400]); return GM[kind] = new THREE.MeshToonMaterial({ map: t.map, color: src[1], gradientMap: GRAD }); }
export function ground(set, kind = 'dirt', size = 6000) { const g = new THREE.Mesh(new THREE.PlaneGeometry(size, size), groundMat(kind)); g.rotation.x = -Math.PI / 2; g.receiveShadow = true; g.userData.noToon = true; set.add(g); return g; }
// low-poly rifle (same frame as the Poly Haven model: butt at x=-.635, muzzle at x=+.596)
export function lowRifle(bayonet = false) { const g = new THREE.Group(), wood = mat(0x6a4024, .7), steel = mat(0x2a2a2c, .4, .7);
  const sh = new THREE.Shape(); sh.moveTo(-.635, -.105); sh.lineTo(-.6, .03); sh.lineTo(-.3, .035); sh.lineTo(-.2, .01); sh.lineTo(.38, .02); sh.lineTo(.38, -.01); sh.lineTo(-.2, -.03); sh.lineTo(-.36, -.04); sh.lineTo(-.635, -.105);
  const sg = new THREE.ExtrudeGeometry(sh, { depth: .04, bevelEnabled: false }); sg.translate(0, 0, -.02); mesh(sg, wood, [0, 0, 0], [0, 0, 0], g);
  mesh(new THREE.CylinderGeometry(.011, .011, .9, 6), steel, [.15, .035, 0], [0, 0, Math.PI / 2], g); mesh(new THREE.BoxGeometry(.16, .035, .03), steel, [-.2, .045, 0], [0, 0, 0], g); mesh(new THREE.SphereGeometry(.014, 6, 4), steel, [-.19, .05, .04], [0, 0, 0], g);
  if (bayonet) mesh(new THREE.ConeGeometry(.012, .45, 4), mat(0xc8ccd2, .2, .9), [.82, .035, 0], [0, 0, -Math.PI / 2], g); return g; }
export let LOWRIFLE = null; export const initLowRifle = () => LOWRIFLE = lowRifle();
// extra poses on top of person2's pose(): aim, port, handsUp, kneel, sit, salute, carry flag
const Z0 = new THREE.Quaternion();
export function pose(m, t, p = {}) { const u = m.userData, r = u.rig; u.pose(t, p);
  const rf = u.rifle; if (rf && !rf.userData.q0) { rf.userData.q0 = rf.quaternion.clone(); rf.userData.p0 = rf.position.clone(); }
  if (rf) { rf.quaternion.copy(rf.userData.q0); rf.position.copy(rf.userData.p0); }
  if (p.aim) { r.arms[1].sh.rotation.z = 1.25; r.arms[1].el.rotation.z = .9; r.arms[1].sh.rotation.x = -.5; r.arms[0].sh.rotation.z = 1.45; r.arms[0].el.rotation.z = .25; r.arms[0].sh.rotation.x = .25; r.head.rotation.z = -.12; r.head.rotation.y = -.15;
    if (rf) { rf.quaternion.copy(Z0); rf.position.set(.52, .4, .1); } }
  if (p.port) { r.arms[1].sh.rotation.z = .5; r.arms[1].el.rotation.z = 1.1; r.arms[0].sh.rotation.z = .9; r.arms[0].el.rotation.z = 1.0; if (rf) { rf.quaternion.setFromAxisAngle(new THREE.Vector3(0, 0, 1), .75); rf.position.set(.3, .2, 0); } }
  if (p.handsUp) { r.arms[0].sh.rotation.z = -2.9 + Math.sin(t * 2) * .05; r.arms[1].sh.rotation.z = -2.9; r.arms[0].sh.rotation.x = .3; r.arms[1].sh.rotation.x = -.3; r.arms[0].el.rotation.z = -.3; r.arms[1].el.rotation.z = -.3; }
  if (p.salute) { r.arms[1].sh.rotation.z = 1.3; r.arms[1].sh.rotation.x = -1.3; r.arms[1].el.rotation.z = 2.3; }
  if (p.kneel) { r.legs[0].hip.rotation.z = 1.45; r.legs[0].knee.rotation.z = -1.45; r.legs[1].hip.rotation.z = -.15; r.legs[1].knee.rotation.z = -1.45; r.pelvis.position.y = .95 - .43; r.spine.position.y = .95 - .43; }
  if (p.sit) { r.legs[0].hip.rotation.z = 1.5; r.legs[1].hip.rotation.z = 1.5; r.legs[0].knee.rotation.z = -1.5; r.legs[1].knee.rotation.z = -1.5; r.pelvis.position.y = .5; r.spine.position.y = .5; r.spine.rotation.z = -.05 + (p.lean ?? 0); }
  if (p.prone) { /* caller rotates whole body */ }
  if (p.write) { r.arms[1].sh.rotation.z = .75; r.arms[1].el.rotation.z = 1.2 + Math.sin(t * 9) * .08; r.arms[0].sh.rotation.z = .6; r.arms[0].el.rotation.z = 1.1; r.head.rotation.z = -.35; }
  if (p.flag) { r.arms[1].sh.rotation.z = .6; r.arms[1].el.rotation.z = 1.4; r.arms[0].sh.rotation.z = .3; r.arms[0].el.rotation.z = 1.2; }
  if (p.point) { r.arms[1].sh.rotation.z = 1.5 + (p.pointUp ?? 0); r.arms[1].el.rotation.z = .1; r.arms[1].sh.rotation.x = -.2; }
}
export const facing = dir => Math.atan2(-dir[1], dir[0]);   // ry so a person faces direction [dx, dz]
export const man = (o) => { const m = person2({ RIFLE: o.hero ? RIFLE : LOWRIFLE, ...o }); return m; };
// cel-shade everything (call after build)
export function toonify() {
  const outline = new THREE.MeshBasicMaterial({ color: 0x24170f, side: THREE.BackSide }), list = [];
  S.traverse(o => { if (o.isMesh && !o.isInstancedMesh && !o.userData.ol && !o.userData.noToon) list.push(o); });
  for (const m of list) { const old = m.material; if (!old || Array.isArray(old) || old.isMeshToonMaterial || old.isMeshBasicMaterial || old.isSpriteMaterial || old.isPointsMaterial) continue;
    m.material = new THREE.MeshToonMaterial({ color: old.color, map: old.map, gradientMap: GRAD, side: old.side, transparent: old.transparent, opacity: old.opacity, emissive: old.emissive || new THREE.Color(0), emissiveIntensity: old.emissiveIntensity ?? 1 });
    if (!m.geometry.boundingSphere) m.geometry.computeBoundingSphere(); const pc = m.geometry.attributes.position.count, big = m.geometry.boundingSphere.radius;
    if (pc < 30000 && big < 30 && big > .025 && m.geometry.type !== 'PlaneGeometry' && !m.userData.noOutline) { const ol = new THREE.Mesh(m.geometry, outline); ol.scale.setScalar(1 + Math.min(.06, .012 / Math.max(.05, big))); ol.castShadow = false; ol.userData.ol = true; m.add(ol); } }
}
// text plate (signs, banners, documents)
export function textTex(lines, o = {}) { const cv = document.createElement('canvas'); cv.width = o.w || 1024; cv.height = o.h || 256; const x = cv.getContext('2d'); x.fillStyle = o.bg || '#efe6d0'; x.fillRect(0, 0, cv.width, cv.height);
  if (o.border !== false) { x.strokeStyle = o.fg || '#2a1a12'; x.lineWidth = 8; x.strokeRect(8, 8, cv.width - 16, cv.height - 16); }
  x.fillStyle = o.fg || '#2a1a12'; x.textAlign = 'center'; lines.forEach(([s, size, y, font]) => { x.font = font || `bold ${size}px DejaVu Serif, serif`; x.fillText(s, cv.width / 2, y); }); if (o.draw) o.draw(x, cv);
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t; }
export const plate = (w, h, tex, parent, pos, rot = [0, 0, 0]) => { const m = mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshToonMaterial({ map: tex, gradientMap: GRAD, side: THREE.DoubleSide }), pos, rot, parent); m.userData.noToon = true; return m; };
// simple box building
export function house(w, h, d, o = {}) { const g = new THREE.Group(), wall = pbr('grey_plaster_02', [w / 6, h / 6], { color: o.color || 0xd8c8a8 }), roofM = pbr(o.roofTex || 'clay_roof_tiles', [w / 4, 2], { color: o.roof || 0x8a4a3a });
  mesh(new THREE.BoxGeometry(w, h, d), wall, [0, h / 2, 0], [0, 0, 0], g);
  if (o.flat) mesh(new THREE.BoxGeometry(w + .4, .5, d + .4), mat(0x6a5a4a, .9), [0, h + .25, 0], [0, 0, 0], g);
  else { const sh = new THREE.Shape(); sh.moveTo(-d / 2 - .4, 0); sh.lineTo(0, o.pitch || d * .4); sh.lineTo(d / 2 + .4, 0); const rg = new THREE.ExtrudeGeometry(sh, { depth: w + .4, bevelEnabled: false }); rg.translate(0, 0, -w / 2 - .2); mesh(rg, roofM, [0, h, 0], [0, Math.PI / 2, 0], g); }
  const win = mat(o.lit ? 0xffc870 : 0x1c2630, .2, .3, { emissive: o.lit ? 0xffa040 : 0, emissiveIntensity: 1.2 }), trim = mat(o.trim || 0xe8e0d0, .7);
  const floors = Math.max(1, Math.floor(h / 3.2)), cols = Math.max(1, Math.floor(w / 2.6));
  for (let f = 0; f < floors; f++) for (let c = 0; c < cols; c++) { const x = -w / 2 + (c + .5) * w / cols, y = 1.9 + f * 3.2; if (f === 0 && c === (cols >> 1) && o.door !== false) { mesh(new THREE.BoxGeometry(1.4, 2.6, .1), mat(0x3a2418, .8), [x, 1.3, d / 2 + .02], [0, 0, 0], g); continue; } mesh(new THREE.BoxGeometry(1.0, 1.6, .1), win, [x, y, d / 2 + .02], [0, 0, 0], g); mesh(new THREE.BoxGeometry(1.2, .14, .16), trim, [x, y - .85, d / 2 + .05], [0, 0, 0], g); }
  return g; }
// crosses / graves
export function cross(h = 1.4, col = 0x4a3424) { const g = new THREE.Group(), m = mat(col, .9); mesh(new THREE.BoxGeometry(.1, h, .1), m, [0, h / 2, 0], [0, 0, 0], g); mesh(new THREE.BoxGeometry(.1, .1, .6), m, [0, h * .72, 0], [0, 0, 0], g); return g; }
// barbed wire fence line along x
export function wireFence(len, x0 = 0, o = {}) { const g = new THREE.Group(), post = mat(0x4a3a2a, .9), wire = mat(0x3a3a3a, .6, .5); const n = Math.ceil(len / 3);
  for (let i = 0; i <= n; i++) mesh(new THREE.CylinderGeometry(.06, .07, o.h || 2.4, 6), post, [x0 + i * 3, (o.h || 2.4) / 2, 0], [0, 0, (i % 3 - 1) * .04], g);
  for (let k = 0; k < (o.strands || 5); k++) mesh(new THREE.BoxGeometry(len, .015, .015), wire, [x0 + len / 2, .3 + k * ((o.h || 2.4) - .4) / ((o.strands || 5) - 1), 0], [0, 0, 0], g); return g; }
// sandbag wall
export function sandbags(len, rows = 3) { const g = new THREE.Group(), m = mat(0xa89a74, .95), geo = new THREE.CapsuleGeometry(.16, .4, 2, 6); geo.rotateZ(Math.PI / 2); const n = Math.floor(len / .62);
  const im = new THREE.InstancedMesh(geo, m, n * rows), M = new THREE.Matrix4(); let k = 0; for (let r = 0; r < rows; r++) for (let i = 0; i < n; i++) { M.makeTranslation(i * .62 + (r % 2) * .31 - len / 2, .16 + r * .28, 0); im.setMatrixAt(k++, M); } im.castShadow = im.receiveShadow = true; g.add(im); return g; }
// truss bridge over a river
export function trussBridge(len = 60) { const g = new THREE.Group(), steel = mat(0x3c4038, .6, .6); const H2 = 6;
  for (const z of [-2.6, 2.6]) { mesh(new THREE.BoxGeometry(len, .4, .3), steel, [0, .8, z], [0, 0, 0], g); mesh(new THREE.BoxGeometry(len, .35, .3), steel, [0, H2, z], [0, 0, 0], g); const n = Math.floor(len / 5); for (let i = 0; i <= n; i++) { const x = -len / 2 + i * len / n; mesh(new THREE.BoxGeometry(.25, H2, .25), steel, [x, (H2 + .8) / 2, z], [0, 0, 0], g); if (i < n) { const dx = len / n, l = Math.hypot(dx, H2 - .8); mesh(new THREE.BoxGeometry(l, .18, .18), steel, [x + dx / 2, (H2 + .8) / 2, z], [0, 0, (i % 2 ? 1 : -1) * Math.atan2(H2 - .8, dx)], g); } } }
  for (let i = 0; i <= len / 5; i++) mesh(new THREE.BoxGeometry(.2, .2, 5.4), steel, [-len / 2 + i * 5, H2, 0], [0, 0, 0], g);
  mesh(new THREE.BoxGeometry(len, .5, 5.6), mat(0x4a4038, .8), [0, .5, 0], [0, 0, 0], g); return g; }
// soldiers' tent / barracks
export function barrack(w = 14, d = 6) { const g = new THREE.Group(), wood = pbr('brown_planks_05', [w / 3, 1], { color: 0x8a6a4a }); mesh(new THREE.BoxGeometry(w, 2.6, d), wood, [0, 1.3, 0], [0, 0, 0], g);
  const sh = new THREE.Shape(); sh.moveTo(-d / 2 - .3, 0); sh.lineTo(0, 1.6); sh.lineTo(d / 2 + .3, 0); const rg = new THREE.ExtrudeGeometry(sh, { depth: w + .4, bevelEnabled: false }); rg.translate(0, 0, -w / 2 - .2); mesh(rg, mat(0x4a4a48, .9), [0, 2.6, 0], [0, Math.PI / 2, 0], g);
  for (let i = 0; i < 4; i++) mesh(new THREE.BoxGeometry(.9, .7, .1), mat(0x1c1a18, .8), [-w / 2 + (i + .5) * w / 4, 1.7, d / 2 + .02], [0, 0, 0], g); return g; }
export function tower() { const g = new THREE.Group(), w = mat(0x5a4632, .9); for (const [x, z] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) mesh(new THREE.CylinderGeometry(.1, .12, 7, 6), w, [x, 3.5, z], [0, 0, 0], g); mesh(new THREE.BoxGeometry(2.6, .2, 2.6), w, [0, 7, 0], [0, 0, 0], g); for (const [x, z, ry] of [[0, -1.3, 0], [0, 1.3, 0], [-1.3, 0, Math.PI / 2], [1.3, 0, Math.PI / 2]]) mesh(new THREE.BoxGeometry(2.6, 1, .08), w, [x, 7.6, z], [0, ry, 0], g);
  const sh = new THREE.ConeGeometry(2.2, 1.2, 4); mesh(sh, mat(0x3a3a38, .9), [0, 8.9, 0], [0, Math.PI / 4, 0], g); return g; }
// ===================== runner =====================
export const OV = { list: [] };              // 2D overlays registered by shots each frame
export const overlay = fn => OV.list.push(fn);
export function makeRunner(CUES, SHOTS, o = {}) {
  // CUES: timeline shots; SHOTS: { cueIndex: fn(t, lt, d) }. A shot lasts until the next defined index.
  const idx = Object.keys(SHOTS).map(Number).sort((a, b) => a - b), i0 = o.from, i1 = o.to;
  const T0 = CUES[i0].start, T1 = o.end ?? CUES[i1].end, f0 = Math.round(T0 * FPS), f1 = Math.round(T1 * FPS);
  const cuts = idx.map(i => CUES[i].start).concat(o.cuts || []);
  const cx = comp.getContext('2d');
  window.renderAt = f => {
    const t = f / FPS; let si = idx[0]; for (const i of idx) if (t >= CUES[i].start - 1e-6) si = i;
    const nxt = idx[idx.indexOf(si) + 1], st = CUES[si].start, en = nxt !== undefined ? CUES[nxt].start : T1, lt = t - st, d = en - st;
    FX.forEach(x => x.visible = false); [pl1, pl2, pl3].forEach(l => l.intensity = 0); OV.list.length = 0; OV.noGL = false; OV.fade = 0;
    SHOTS[si](t, lt, d);
    cx.globalAlpha = 1; cx.globalCompositeOperation = 'source-over';
    if (OV.split) { OV.split.forEach((setup, k) => { setup(); R.render(S, cam); const sw = R.domElement.width, sh = R.domElement.height; cx.drawImage(R.domElement, sw / 4, 0, sw / 2, sh, k * W / 2, 0, W / 2, H); }); cx.fillStyle = '#0a0806'; cx.fillRect(W / 2 - 4, 0, 8, H); OV.split = null; }
    else if (!OV.noGL) { R.render(S, cam); cx.drawImage(R.domElement, 0, 0, W, H); } else { cx.fillStyle = '#000'; cx.fillRect(0, 0, W, H); }
    OV.list.forEach(fn => { cx.save(); fn(cx, t); cx.restore(); });
    const g = cx.createRadialGradient(W / 2, H / 2, H * .35, W / 2, H / 2, W * .66); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(10,6,4,.55)'); cx.fillStyle = g; cx.fillRect(0, 0, W, H);
    cx.globalCompositeOperation = 'soft-light'; cx.fillStyle = 'rgba(255,200,150,.18)'; cx.fillRect(0, 0, W, H);
    cx.globalCompositeOperation = 'overlay'; cx.globalAlpha = .06; cx.drawImage(grain, (f * 37) % 40 - 40, (f * 23) % 30 - 30, W + 80, H + 60); cx.globalAlpha = 1; cx.globalCompositeOperation = 'source-over';
    for (const s0 of cuts) { const dd = Math.abs(t - s0); if (dd < .06 && s0 > T0 + .01) { cx.fillStyle = `rgba(0,0,0,${(1 - dd / .06) * .45})`; cx.fillRect(0, 0, W, H); } }
    if (OV.fade) { cx.fillStyle = `rgba(0,0,0,${OV.fade})`; cx.fillRect(0, 0, W, H); }
    if (o.fadeIn && t - T0 < o.fadeIn) { cx.fillStyle = `rgba(0,0,0,${1 - (t - T0) / o.fadeIn})`; cx.fillRect(0, 0, W, H); }
    if (o.fadeOut && T1 - t < o.fadeOut) { cx.fillStyle = `rgba(0,0,0,${1 - (T1 - t) / o.fadeOut})`; cx.fillRect(0, 0, W, H); }
    return comp.toDataURL('image/jpeg', .9);
  };
  return { f0, f1 };
}
// open flatcar with sandbag parapet (soldiers ride on it)
export function flatcar(o = {}) { const b = boxcar2({ stove: false }), by0 = b.userData.by0;
  const kill = []; b.children.forEach(c => { if (!c.isMesh) return; const p = c.geometry.parameters || {}; if (c.position.y > by0 + .3 || p.radiusTop === 3.6 || c === b.userData.doorDark || c === b.userData.doorPanel) kill.push(c); }); kill.forEach(c => b.remove(c));
  mesh(new THREE.BoxGeometry(7.6, .14, 2.8), pbr('old_wood_floor', [3, 1], { color: 0x7a6650 }), [0, by0 + .07, 0], [0, 0, 0], b);
  for (const z of [-1.35, 1.35]) { const sb = sandbags(7.2, 2); sb.position.set(0, by0 + .14, z); b.add(sb); }
  b.userData.deck = by0 + .14; return b; }
// a train: loco + n cars. dir = +1 loco faces +x (moves +x), -1 faces -x
export function train(n, o = {}) { const g = new THREE.Group(), loco = locomotive2(o); g.add(loco); const cars = []; let x = loco.userData.backX;
  for (let i = 0; i < n; i++) { const kind = (o.kinds || [])[i]; const b = kind === 'armor' ? armoredWagon() : kind === 'flat' ? flatcar() : boxcar2({ open: (o.openIdx || []).includes(i) ? .95 : 0, tint: [0xb06648, 0xa05a3e, 0x96603e, 0xa86a50][i % 4], stove: o.stove }); x -= b.userData.length / 2; b.position.x = x; x -= b.userData.length / 2; g.add(b); cars.push(b); }
  if (o.front) { const f = o.front === 'armor' ? armoredWagon() : flatcar(); f.position.x = loco.userData.frontX + f.userData.length / 2 + .3; g.add(f); g.userData.front = f; }
  g.userData.loco = loco; g.userData.cars = cars; g.userData.update = d => { loco.userData.update(d); cars.forEach(c => c.userData.update(d)); if (g.userData.front) g.userData.front.userData.update(d); }; return g; }
// explosion: flash + fireball + dirt chunks + smoke column; update(t since detonation)
export function blast(o = {}) { const g = new THREE.Group(), sz = o.size || 4;
  const fl = new THREE.Sprite(new THREE.SpriteMaterial({ map: FIRE_T, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true })); g.add(fl);
  const chunks = []; for (let i = 0; i < 18; i++) { const c = mesh(new THREE.BoxGeometry(.25, .2, .2), mat(0x3a2a1a, 1), [0, 0, 0], [0, 0, 0], g); c.castShadow = false; chunks.push(c); }
  const sm = smoke(new THREE.Vector3(), { n: 26, color: o.smokeCol || 0x3a3430, wind: [1, .2], rise: 14, size: sz * .7, grow: 3, life: 4, opacity: .9 }); g.add(sm);
  g.userData.update = (tt, wp) => { const on = tt >= 0; g.visible = on; if (!on) return; const k = clamp(tt / .35); fl.visible = tt < .5; fl.scale.setScalar(sz * 2.4 * (0.4 + k) * (1 - clamp((tt - .25) / .25))); fl.position.y = sz * .4;
    chunks.forEach((c, i) => { const r = rng(i + 5), vx = (r() - .5) * 14, vy = 6 + r() * 10, vz = (r() - .5) * 14, tc = Math.min(tt, 2.2); c.position.set(vx * tc * .5, Math.max(.1, vy * tc - 4.9 * tc * tc), vz * tc * .5); c.rotation.set(tt * 7 * r(), tt * 5, tt * 3); c.visible = tt < 2.2; });
    sm.userData.update(tt + 2, wp || new THREE.Vector3(g.position.x, g.position.y, g.position.z)); sm.position.set(-g.position.x, -g.position.y, -g.position.z); sm.children.forEach(s => s.material.opacity *= clamp(tt / .3)); };
  return g; }
// cheap instanced troop block (for distant formations): rows x cols figures, returns group with update(t, march)
export function troopBlock(rows, cols, o = {}) { const g = new THREE.Group(), n = rows * cols, sp = o.sp || 1.1;
  const parts = [[new THREE.CylinderGeometry(.2, .27, 1.25, 7), o.coat || 0x5c5a40, .62], [new THREE.CylinderGeometry(.08, .08, .7, 5), o.trou || 0x3a3226, .35], [new THREE.SphereGeometry(.12, 7, 5), 0xc8906c, 1.37], [new THREE.CylinderGeometry(.13, .13, .16, 7), o.hat || 0x2e241c, 1.52]];
  if (o.rifle !== false) parts.push([new THREE.BoxGeometry(.04, 1.2, .04), 0x4a3020, 1.0]);
  const ims = parts.map(([geo, col]) => { const im = new THREE.InstancedMesh(geo, new THREE.MeshToonMaterial({ color: col, gradientMap: GRAD }), n); im.castShadow = true; g.add(im); return im; });
  const M4 = new THREE.Matrix4(), Q = new THREE.Quaternion(), Sv = new THREE.Vector3(1, 1, 1), Pv = new THREE.Vector3();
  g.userData.update = (t, march = 0, face = 0) => { Q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), face); for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) { const i = r * cols + c, b = march ? Math.abs(Math.sin(t * 6.5 + r * .3)) * .04 : 0;
    parts.forEach(([, , y], k) => { Pv.set(c * sp - (cols - 1) * sp / 2 + (k === 4 ? .25 : 0), y + b, r * sp - (rows - 1) * sp / 2); Pv.applyQuaternion(Q); M4.compose(Pv, Q, Sv); ims[k].setMatrixAt(i, M4); }); }
    ims.forEach(im => im.instanceMatrix.needsUpdate = true); };
  g.userData.update(0); return g; }
