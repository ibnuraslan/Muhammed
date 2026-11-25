// ===================== SECTION 4: 1918, the route east and the revolt, cues 52-81 =====================
import * as L from './lib3.js';
import * as M from './maps.js';
import * as P from './props.js';
const { THREE, S, cam, U, SKY, V3, at, mesh, mat, pbr, model, clamp, lerp, ease, rng, pl1, pl2, pl3, look, camTo, show, fx, overlay, OV, pose, facing, man, SETS } = L;
export const RANGE = { from: 52, to: 81 };
let C; const ST = i => C[i].start;
const ct = (set, lt, d, a, b, fov = [35, 35], shake = 0) => { const o = SETS[set].position; camTo(lt, d, [a[0] + o.x, a[1] + o.y, a[2] + o.z, a[3] + o.x, a[4] + o.y, a[5] + o.z], [b[0] + o.x, b[1] + o.y, b[2] + o.z, b[3] + o.x, b[4] + o.y, b[5] + o.z], fov, shake); };
const camAt = (set, p, tg, fov) => { const o = SETS[set].position; cam.position.set(p[0] + o.x, p[1] + o.y, p[2] + o.z); cam.lookAt(tg[0] + o.x, tg[1] + o.y, tg[2] + o.z); cam.fov = fov; cam.updateProjectionMatrix(); };
const CZ = ['#f2f0ea', '#c8241c'], RUW = ['#f2f0ea', '#2a4ea0', '#c8241c'];
const RAIL = [[45.0, 53.2, 'PENZA'], [50.1, 53.2, 'SAMARA'], [56.0, 54.7, 'UFA'], [61.4, 55.16, 'CHELYABINSK'], [65.5, 57.15, ''], [73.4, 54.99, 'OMSK'], [82.9, 55.03, 'NOVONIKOLAEVSK'], [92.9, 56.0, 'KRASNOYARSK'], [104.3, 52.29, 'IRKUTSK'], [113.5, 52.03, 'CHITA'], [127.5, 50.3, ''], [131.9, 43.12, 'VLADIVOSTOK']];
const railAt = (pr, q) => { const pts = RAIL.map(([lo, la]) => pr(lo, la)); const k = q * (pts.length - 1), i = Math.min(pts.length - 2, Math.floor(k)), f = k - i; return [lerp(pts[i][0], pts[i + 1][0], f), lerp(pts[i][1], pts[i + 1][1], f)]; };
function drawRail(c, pr, w = 4) { c.strokeStyle = '#2a1a10'; c.lineWidth = w + 3; c.beginPath(); RAIL.forEach(([lo, la], i) => { const [x, y] = pr(lo, la); i ? c.lineTo(x, y) : c.moveTo(x, y); }); c.stroke(); c.strokeStyle = '#e8dcc0'; c.lineWidth = w; c.setLineDash([10, 8]); c.stroke(); c.setLineDash([]); }
const RU_PROJ = () => M.proj(28, 140, 36, 66);
function waterTower() { const g = new THREE.Group(), w = mat(0x5a4632, .9); for (const [x, z] of [[-1.2, -1.2], [1.2, -1.2], [-1.2, 1.2], [1.2, 1.2]]) mesh(new THREE.CylinderGeometry(.12, .15, 6, 6), w, [x, 3, z], [0, 0, 0], g); mesh(new THREE.CylinderGeometry(2, 2, 3, 16), pbr('brown_planks_05', [3, 1], { color: 0x7a5236 }), [0, 7.5, 0], [0, 0, 0], g); mesh(new THREE.ConeGeometry(2.3, 1.2, 16), mat(0x3a3a3a, .8), [0, 9.6, 0], [0, 0, 0], g); return g; }
function hill(r, h, col = 0x7a8a52) { const g = new THREE.SphereGeometry(1, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2); const m = new THREE.Mesh(g, mat(col, 1)); m.scale.set(r, h, r * .8); m.receiveShadow = true; return m; }
function mgNest() { const g = new THREE.Group(); for (let i = 0; i < 6; i++) { const s = L.sandbags(1.4, 2); const a = i / 6 * Math.PI * 1.4 - .2; s.position.set(Math.cos(a) * 1.3, 0, Math.sin(a) * 1.3); s.rotation.y = -a + Math.PI / 2; g.add(s); } const mg = new THREE.Group(); mesh(new THREE.CylinderGeometry(.08, .08, .9, 10), mat(0x2a2e2a, .5, .5), [.4, .55, 0], [0, 0, Math.PI / 2], mg); mesh(new THREE.BoxGeometry(.4, .25, .2), mat(0x2a2e2a, .5, .5), [0, .55, 0], [0, 0, 0], mg); mesh(new THREE.BoxGeometry(.5, .05, .5), mat(0x2a2e2a, .5, .5), [0, .4, 0], [0, 0, 0], mg); mesh(new THREE.BoxGeometry(.04, .4, .04), mat(0x2a2e2a, .5), [.1, .2, .15], [.3, 0, 0], mg); mesh(new THREE.BoxGeometry(.04, .4, .04), mat(0x2a2e2a, .5), [.1, .2, -.15], [-.3, 0, 0], mg); g.add(mg); g.userData.mg = mg; return g; }
export async function build(cues) {
  C = cues;
  SKY.dusk = L.paintSky('#3e4474', '#f2a868', '#ffd8a0', '#d89a8a', '#7a6a8a', 9, { sun: [700, 820] });
  SKY.day = L.paintSky('#7fa6d4', '#e2e4dc', '#fdf9f0', '#d9d9de', '#a3abbd', 5);
  SKY.grey = L.paintSky('#8e98a6', '#cfcec6', '#e8e6e0', '#bdbdc2', '#8d929e', 7);
  SKY.night = L.paintSky('#0a1228', '#28344e', '#4a5a7e', '#323e5c', '#1e263c', 11, { stars: true });
  SKY.snowdusk = L.paintSky('#4a5a86', '#e8b898', '#ffe0c8', '#d0b0b0', '#8a8aa8', 13, { sun: [1400, 800] });
  SKY.summer = L.paintSky('#5a8ad0', '#e8e0c8', '#fffaf0', '#e8e0d8', '#a8b0c4', 23, { sun: [1500, 300] });
  // flashback frames from section 1 (the iron bar)
  U.flash = []; for (const f of [...Array(21).keys()].map(k => 290 + k * 2).concat([...Array(17).keys()].map(k => 398 + k * 2))) { const im = new Image(); im.src = `out/${String(f).padStart(5, '0')}.jpg`; U.flash.push(im); } await Promise.all(U.flash.map(im => im.decode().catch(() => 0)));
  // ---------- TAIGA line (sunset / snow + burning village) ----------
  const tg = L.addSet('taiga', 0, 0); L.ground(tg, 'snow'); tg.add(L.track2(1400, -700)); tg.add(L.forest(500, -700, 700, -260, -18, 101, true)); tg.add(L.forest(400, -700, 700, 18, 260, 102, true));
  U.tTrain = L.train(10, {}); tg.add(U.tTrain); U.tSmoke = fx(L.smoke(V3(), { n: 80, color: 0x4a4a50, wind: [-6, .5], rise: 9, size: 1.6, grow: 5, life: 6, opacity: .9 }));
  U.village = new THREE.Group(); for (let i = 0; i < 6; i++) { const h = L.house(6, 4, 5, { color: 0x8a6a4a, roofTex: 'brown_planks_05', roof: 0x5a4a3a }); at(h, -40 + i * 9 + (i % 2) * 3, 0, -30 - (i % 3) * 6, (i - 2) * .3); U.village.add(h); } tg.add(U.village);
  U.vfires = [[-40, -30], [-22, -36], [-4, -30], [14, -42]].map(([x, z]) => { const f = L.fire(14, 5); f.position.set(x, 2, z); tg.add(f); return f; });
  U.vsmoke = fx(L.smoke(V3(), { n: 60, color: 0x2a2222, wind: [2, .4], rise: 35, size: 6, grow: 4, life: 8, opacity: .9 }));
  // ---------- HARBOUR (Vladivostok) ----------
  const hb = L.addSet('harbor', 900, 0); U.sea = P.sea(2400, 0x2a4a62); hb.add(U.sea); U.sea.position.y = -1;
  const quay = mesh(new THREE.BoxGeometry(400, 3, 40), pbr('gravel', [60, 8], { color: 0x8a847a }), [0, .5, -30], [0, 0, 0], hb); for (let i = 0; i < 5; i++) { const cr = P.crane(); at(cr, -60 + i * 30, 2, -16, Math.PI / 2); hb.add(cr); }
  for (let i = 0; i < 6; i++) { const w = L.barrack(18, 10); w.scale.set(1, 1.6, 1); at(w, -70 + i * 26, 2, -40); hb.add(w); }
  U.ships = [[-30, 2], [40, 2], [10, 60]].map(([x, z], i) => { const s = P.ship({ funnels: i === 1 ? [-6, -1, 4] : [-4, 2], hull: [0x1e2226, 0x2a2e34, 0x3a3e44][i] }); at(s, x, 0, z, i === 2 ? .3 : 0); hb.add(s); return s; });
  U.hills = []; for (let i = 0; i < 9; i++) { const h = hill(60 + (i % 3) * 30, 25 + (i % 4) * 12, 0x5a6a48); h.position.set(-300 + i * 80, 0, -120 - (i % 2) * 40); hb.add(h); }
  U.fsmoke = U.ships.slice(0, 2).map(() => fx(L.smoke(V3(), { n: 40, color: 0x3a3a3e, wind: [3, .5], rise: 14, size: 2.5, grow: 4, life: 6, opacity: .8 })));
  // ---------- OFFICE (agreement; commissar's telegraph) ----------
  const of = L.addSet('office', -900, 0); const orm = P.room(9, 6, 3.6, { wall: 0x8a7a62 }); of.add(orm); const ot = P.longTable(2.6, 1.2); of.add(ot); { const pp = P.papers(6, 21); of.add(pp); }
  const ol = P.deskLamp(); at(ol, .9, .84, -.3); of.add(ol); U.offLamp = ol;
  U.comm = man({ u: 'red', seed: 1500, rifle: false, hero: true }); at(U.comm, -.35, 0, -1.0, facing([0, 1])); of.add(U.comm); U.comm.userData.rig.head.traverse(o => { if (o.isMesh && o.geometry.type === 'CylinderGeometry' && o.geometry.parameters.height < .02) o.visible = false; }); const c1 = P.chair(); at(c1, -.35, 0, -1.08, facing([0, 1]) + Math.PI); of.add(c1);
  U.lofficer = man({ u: 'legionCap', seed: 1501, rifle: false, hero: true }); at(U.lofficer, .35, 0, 1.0, facing([0, -1])); of.add(U.lofficer); const c2 = P.chair(); at(c2, .35, 0, 1.08, facing([0, -1]) + Math.PI); of.add(c2);
  const wmap = (() => { const cv = document.createElement('canvas'); cv.width = 1024; cv.height = 512; const x = cv.getContext('2d'); const pr = L.mapProj(28, 140, 36, 66, 0, 0, 1024, 512); L.drawMap(x, pr, { sea: '#8aa0a8', ru: '#d8c8a0', land: '#e4d6b0', w: 1024, h: 512 }); x.strokeStyle = '#3a2a1a'; x.lineWidth = 3; x.beginPath(); RAIL.forEach(([lo, la], i) => { const [px, py] = pr(lo, la); i ? x.lineTo(px, py) : x.moveTo(px, py); }); x.stroke(); for (let i = 0; i < 40; i++) { const q = (i * 37 % 100) / 100; const pts = RAIL.map(([lo, la]) => pr(lo, la)); const k = q * (pts.length - 1), j = Math.floor(k), f = k - j; const px = lerp(pts[j][0], pts[j + 1][0], f), py = lerp(pts[j][1], pts[j + 1][1], f); x.fillStyle = '#c8241c'; x.beginPath(); x.arc(px, py, 6, 0, 7); x.fill(); } const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; return t; })();
  L.plate(4.6, 2.3, wmap, of, [0, 2.0, -2.9]); U.tape = new THREE.Group(); mesh(new THREE.BoxGeometry(.3, .18, .25), mat(0x2a2218, .5, .4), [0, .93, 0], [0, 0, 0], U.tape); mesh(new THREE.CylinderGeometry(.06, .06, .05, 12), mat(0xc9a24d, .3, .9), [0, 1.05, 0], [0, 0, 0], U.tape); at(U.tape, -.9, 0, -.2); of.add(U.tape);
  U.tapeStrip = mesh(new THREE.BoxGeometry(.6, .003, .025), mat(0xf0e8d0, .9), [0, 0, 0], [0, 0, 0], of);
  // ---------- PLATFORM (surrender, standoff, firefight) + boxcar slit ----------
  const pf = L.addSet('platform', 0, 900); L.ground(pf, 'dirt'); pf.add(L.track2(600, -300)); const pt2 = L.track2(600, -300); pt2.position.z = 7; pf.add(pt2);
  const stb = L.station('ПЕНЗА', { wallTint: 0xd8c4a0 }); at(stb, 0, .6, -15.5); pf.add(stb); mesh(new THREE.BoxGeometry(80, .6, 6.2), pbr('old_wood_floor', [24, 2], { color: 0x9a8a78 }), [0, .3, -4.6 - 3.1], [0, 0, 0], pf);
  for (const x of [-14, -2, 10]) { const l = await model('street_lamp_01'); at(l, x, .6, -5.2); pf.add(l); }
  U.pTrain = L.train(5, { openIdx: [0, 1, 2, 3, 4] }); at(U.pTrain, 18, 0, 0); pf.add(U.pTrain);
  U.handers = [...Array(8)].map((_, i) => { const m = man({ u: i % 3 === 1 ? 'legionCap' : 'legion', seed: 1510 + i }); pf.add(m); return m; });
  U.reds = [...Array(10)].map((_, i) => { const m = man({ u: 'red', seed: 1530 + i, RIFLE: L.lowRifle(true) }); pf.add(m); return m; });
  U.pile = new THREE.Group(); for (let i = 0; i < 26; i++) { const r = L.lowRifle(); r.position.set((i % 7) * .14 - .45, .05 + Math.floor(i / 7) * .07, (i % 3) * .08); r.rotation.set(Math.PI / 2, 0, (i % 5 - 2) * .15); U.pile.add(r); } at(U.pile, -3, .6, -8.8); pf.add(U.pile);
  U.stack = new THREE.Group(); for (let i = 0; i < 6; i++) { const r = L.lowRifle(); const a = i / 6 * Math.PI * 2; r.position.set(Math.cos(a) * .25, .62, Math.sin(a) * .25); r.rotation.set(0, -a, Math.PI / 2 - .25); r.rotateZ(0); U.stack.add(r); }
  U.clerk = man({ u: 'red', seed: 1550, rifle: false }); at(U.clerk, -4.5, .6, -9.4, facing([1, .3])); pf.add(U.clerk); U.roofGuard = [0, 1].map(i => { const m = man({ u: 'legion', seed: 1555 + i }); const c = U.pTrain.userData.cars[1 + i * 2]; at(m, 0, c.userData.by0 + 2.85, 0, facing([0, -1])); c.add(m); return m; });
  U.flashes = [...Array(14)].map(() => fx(new THREE.Sprite(new THREE.SpriteMaterial({ map: L.FIRE_T, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }))));
  U.gunsmoke = fx(L.smoke(V3(), { n: 50, color: 0xb8b4ac, wind: [.6, .8], rise: 2, size: 1.2, grow: 4, life: 3, opacity: .7 }));
  // boxcar interior at night, looking out through the door gap
  const bx = L.addSet('boxin', 900, 900); const pl = pbr('brown_planks_05', [3, 1], { color: 0x6a4228 });
  const Pp = (w, h, x, y, z, ry = 0, rx = 0) => mesh(new THREE.PlaneGeometry(w, h), Object.assign(pl.clone(), { side: THREE.DoubleSide }), [x, y, z], [rx, ry, 0], bx);
  Pp(7.4, 2.7, 0, 1.35, -1.37); Pp(2.6, 2.7, -2.4, 1.35, 1.37); Pp(2.6, 2.7, 2.4, 1.35, 1.37); Pp(7.4, .5, 0, 2.45, 1.37); Pp(2.75, 2.7, -3.7, 1.35, 0, Math.PI / 2); Pp(2.75, 2.7, 3.7, 1.35, 0, Math.PI / 2); Pp(7.4, 2.75, 0, 0, 0, 0, -Math.PI / 2); Pp(7.4, 2.75, 0, 2.7, 0, 0, Math.PI / 2);
  U.slideDoor = mesh(new THREE.BoxGeometry(2.0, 2.3, .06), pl, [.9, 1.15, 1.42], [0, 0, 0], bx);
  U.inside = [...Array(5)].map((_, i) => { const m = man({ u: i % 2 ? 'legionCap' : 'legion', seed: 1560 + i, rifle: false, hero: i === 0 }); at(m, -2.6 + i * 1.2, 0, -.5 + (i % 2) * .4, facing([0, 1]) + (i - 2) * .2); bx.add(m); return m; });
  L.ground(bx, 'dirt'); bx.children[bx.children.length - 1].position.y = -1.3;
  U.outReds = [0, 1, 2].map(i => { const m = man({ u: 'red', seed: 1570 + i, RIFLE: L.lowRifle(true) }); at(m, -3 + i * 3, -1.3 + .0, 5 + i, facing([0, -1])); bx.add(m); return m; });
  const lmp = await model('street_lamp_01'); at(lmp, 2, -1.3, 7); bx.add(lmp);
  U.floor = new THREE.Group(); const fb = mesh(new THREE.BoxGeometry(1.6, .05, .5), pl, [0, .03, 0], [0, 0, 0], U.floor); U.hidden = new THREE.Group(); for (let i = 0; i < 4; i++) { const r = L.lowRifle(); r.position.set(-.3 + i * .02, -.12, -.15 + i * .1); r.rotation.set(0, 0, 0); U.hidden.add(r); } for (let i = 0; i < 4; i++) { const gr = new THREE.Group(); mesh(new THREE.CylinderGeometry(.035, .035, .1, 10), mat(0x3a4030, .6, .3), [0, 0, 0], [0, 0, 0], gr); mesh(new THREE.CylinderGeometry(.012, .012, .25, 6), mat(0x6a4a2a, .7), [0, -.17, 0], [0, 0, 0], gr); gr.position.set(.45 + i * .09, -.1, .05); gr.rotation.z = Math.PI / 2; U.hidden.add(gr); }
  at(U.floor, 1.6, .26, .6); at(U.hidden, 1.6, .3, .6); bx.add(U.floor); bx.add(U.hidden); for (const [w, d2, x, z] of [[1.7, .04, 1.6, .33], [1.7, .04, 1.6, .87], [.04, .58, .75, .6], [.04, .58, 2.45, .6]]) mesh(new THREE.BoxGeometry(w, .26, d2), pl, [x, .13, z], [0, 0, 0], bx); mesh(new THREE.BoxGeometry(1.66, .02, .52), mat(0x1a120c, 1), [1.6, .02, .6], [0, 0, 0], bx);
  U.hay = []; for (let i = 0; i < 6; i++) { const h = mesh(new THREE.SphereGeometry(.35, 8, 6), mat(0xc8b060, 1), [1.0 + i * .25, .1, .2 + (i % 2) * .5], [0, 0, 0], bx); h.scale.set(1.4, .4, 1); U.hay.push(h); }
  // ---------- WINTER SIDING (lone sentry, night) ----------
  const ws = L.addSet('wsiding', -900, 900); L.ground(ws, 'snow'); ws.add(L.track2(600, -300)); ws.add(L.forest(220, -300, 300, -200, -18, 111, true)); ws.add(L.forest(220, -300, 300, 18, 200, 112, true));
  U.wTrain = L.train(4, {}); at(U.wTrain, 20, 0, 0); ws.add(U.wTrain); U.sentry = man({ u: 'legion', seed: 1580, hero: true }); at(U.sentry, 0, 0, 3.2, facing([-1, 0])); ws.add(U.sentry);
  U.campfire = L.fire(8, .9); U.campfire.position.set(-1.2, .15, 6.0); ws.add(U.campfire); U.fireLogs = new THREE.Group(); for (let i = 0; i < 4; i++) mesh(new THREE.CylinderGeometry(.06, .07, .8, 6), mat(0x3a2414, .9), [0, .08, 0], [Math.PI / 2, i * .8, 0], U.fireLogs); for (let i = 0; i < 9; i++) { const a = i / 9 * Math.PI * 2; mesh(new THREE.SphereGeometry(.09, 6, 5), mat(0x5a5a58, 1), [Math.cos(a) * .45, .04, Math.sin(a) * .45], [0, 0, 0], U.fireLogs); } at(U.fireLogs, -1.2, 0, 6.0); ws.add(U.fireLogs); U.signal = new THREE.Group(); mesh(new THREE.CylinderGeometry(.08, .1, 5, 8), mat(0x2a2a2a, .5, .5), [0, 2.5, 0], [0, 0, 0], U.signal); const lampR = mesh(new THREE.SphereGeometry(.15, 10, 8), new THREE.MeshBasicMaterial({ color: 0xff3020 }), [0, 4.8, .1], [0, 0, 0], U.signal); lampR.userData.noToon = true; at(U.signal, -30, 0, 2.6); ws.add(U.signal);
  U.wsnow = fx(L.snowfall(5000, [60, 25, 60], [-900, 0, 900]));
  // ---------- JUNCTION (station, approaches, bridge) ----------
  const jn = L.addSet('junction', 0, -900); L.ground(jn, 'grass', 8000); jn.add(L.track2(1600, -800)); const br = L.track2(140, 0); br.rotation.y = -.35; br.position.set(10, 0, 0); jn.add(br); const t3 = L.track2(200, -100); t3.position.z = 6; jn.add(t3);
  const js = L.station('ТАЙГА', { wallTint: 0xd8c4a0 }); at(js, 0, .6, -15.5); jn.add(js); mesh(new THREE.BoxGeometry(60, .6, 6.2), pbr('old_wood_floor', [18, 2], { color: 0x9a8a78 }), [0, .3, -7.7], [0, 0, 0], jn); const wt = waterTower(); at(wt, 22, 0, -10); jn.add(wt);
  U.jTrain = L.train(6, {}); at(U.jTrain, -6, 0, 0); jn.add(U.jTrain); U.jTrain2 = L.train(5, {}); at(U.jTrain2, 330, 0, 0, Math.PI); jn.add(U.jTrain2);
  U.nests = [[-35, -45], [40, -50], [-25, 40], [45, 42]].map(([x, z]) => { const n = mgNest(); at(n, x, 0, z, Math.atan2(x, z)); jn.add(n); const m = man({ u: 'legionCap', seed: 1600 + x }); at(m, x * .97, 0, z * .97, facing([x, z])); jn.add(m); m.userData.home = m.position.clone(); n.userData.man = m; return n; });
  const river = mesh(new THREE.PlaneGeometry(40, 3000), new THREE.MeshToonMaterial({ color: 0x3a6a8a, gradientMap: L.GRAD, polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4 }), [170, .3, 0], [-Math.PI / 2, 0, 0], jn); river.userData.noToon = true; const bg2 = L.trussBridge(46); at(bg2, 170, .2, 0); jn.add(bg2);
  U.jFlag = L.flag(1.6, 1.0, CZ); const jfp = L.poleWithFlag(4, U.jFlag); at(jfp, -4, .6, -9.6); jn.add(jfp); U.jFlagPole = jfp;
  U.stormers = [...Array(8)].map((_, i) => { const m = man({ u: i % 3 === 1 ? 'legionCap' : 'legion', seed: 1620 + i }); jn.add(m); return m; });
  U.labels = ['TRAIN', 'STATION', 'APPROACHES', 'THE TRACK BETWEEN'];
  U.armT = L.train(1, { kinds: ['flat'], front: 'armor', color: 0x3a4038 }); at(U.armT, -120, 0, 6); jn.add(U.armT); U.jblasts = [[-160, 14], [-130, -12], [-180, -6]].map(([x, z]) => { const b = L.blast({ size: 5 }); b.position.set(x, 0, z); jn.add(b); return b; });
  U.cflash = fx(new THREE.Sprite(new THREE.SpriteMaterial({ map: L.FIRE_T, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true })));
  // ---------- WHITE TOWN SQUARE ----------
  const ws2 = L.addSet('wsquare', 900, -900); L.ground(ws2, 'cobble'); for (let i = 0; i < 5; i++) { if (i === 2) continue; const h = L.house(10, 11 + (i % 2) * 3, 8, { color: [0xd8c8a8, 0xc8b08a, 0xe0d4b8, 0xb8a888, 0xd0b898][i] }); at(h, -22 + i * 11, 0, -12); ws2.add(h); }
  const hall = L.house(16, 14, 10, { color: 0xe8dcc0, flat: true }); at(hall, 0, 0, -18); hall.scale.set(1, 1, 1); ws2.add(hall);
  U.wFlag = L.flag(2.4, 1.5, RUW); const wfp = L.poleWithFlag(6, U.wFlag); at(wfp, 0, 14, -12.6); ws2.add(wfp); U.wfPole = wfp; U.wFlagCZ = L.flag(2.0, 1.25, CZ); const wcp = L.poleWithFlag(5, U.wFlagCZ); at(wcp, -6, 11, -7.6); ws2.add(wcp);
  U.whites = [...Array(6)].map((_, i) => { const m = man({ u: 'russian', seed: 1650 + i, kit: { hat: 'peaked', hatC: 0x7a7454, coat: 0x8a8460 } }); at(m, -5 + i * 2, 0, -6, facing([0, 1])); ws2.add(m); return m; });
  U.wcrowd = [...Array(14)].map((_, i) => { const m = man({ u: i % 4 === 0 ? 'woman' : 'civil', seed: 1670 + i, rifle: false }); at(m, -8 + (i % 7) * 2.6, 0, 1 + Math.floor(i / 7) * 1.6, facing([0, -1])); ws2.add(m); return m; });
  const proc = L.textTex([['КОМИТЕТ ЧЛЕНОВ', 44, 110], ['УЧРЕДИТЕЛЬНОГО', 44, 170], ['СОБРАНИЯ', 54, 240], ['ПРИКАЗ № 1', 40, 330], ['████ ██████ ███████', 24, 420], ['██████ ███ ████████', 24, 460], ['███ ██████ ████', 24, 500]], { w: 512, h: 640, bg: '#ece0c0' });
  L.plate(1.4, 1.75, proc, ws2, [8.2, 2.4, -7.85]);
}
// ---------- SHOTS ----------
export const SHOTS = {};
// 52 moving west meant crossing the Central Powers: arrow west blocked
SHOTS[52] = (t, lt, d) => { OV.noGL = true; overlay((c, tt) => { const pr = M.proj(-8, 52, 38, 62); M.paper(c); M.baseLand(c, pr, { land: '#b8a888' });
  ['Germany', 'Austria', 'Hungary', 'Czechia', 'Slovakia', 'Poland', 'Lithuania', 'Latvia', 'Belarus', 'Ukraine', 'Slovenia', 'Croatia', 'Bosnia and Herz.', 'Bulgaria', 'Serbia', 'Romania'].forEach((n, i) => { const f = M.byName(n); if (!f) return; M.pathFeature(c, pr, f); c.fillStyle = `rgba(40,36,34,${.55 * clamp((lt - i * .03) / .4)})`; c.fill(); });
  M.label(c, 'CENTRAL POWERS', ...pr(17, 50), 40, '#f2e8d2', clamp(lt / .6)); const fr = M.byName('France'); if (fr) { M.pathFeature(c, pr, fr); c.fillStyle = '#4a6ab0'; c.fill(); }
  const [ux, uy] = pr(37, 50), [fx, fy] = pr(2.4, 47.5), k = ease(clamp((lt - .4) / 1.6)), stop = .55, kk = Math.min(k, stop); c.strokeStyle = '#f2e8d2'; c.lineWidth = 12; c.setLineDash([24, 14]); c.beginPath(); c.moveTo(ux, uy); c.lineTo(lerp(ux, fx, kk), lerp(uy, fy, kk)); c.stroke(); c.setLineDash([]);
  if (k > stop) { const [bx, by] = [lerp(ux, fx, stop), lerp(uy, fy, stop)], s = ease(clamp((lt - 1.4) / .3)); c.strokeStyle = '#e03020'; c.lineWidth = 18; c.beginPath(); c.moveTo(bx - 50 * s, by - 50 * s); c.lineTo(bx + 50 * s, by + 50 * s); c.moveTo(bx + 50 * s, by - 50 * s); c.lineTo(bx - 50 * s, by + 50 * s); c.stroke(); }
  M.label(c, 'FRANCE', fx, fy + 10, 40, '#fff4e0'); M.label(c, 'THE LEGION', ux + 20, uy + 60, 30, '#fff4e0'); M.vignette(c); }); };
// 53 the route ran east: map arc to Vladivostok -> a train through the taiga at sunset
SHOTS[53] = (t, lt, d) => { if (lt < 3.2) { OV.noGL = true; overlay((c, tt) => { const pr = RU_PROJ(); M.paper(c); M.baseLand(c, pr, { land: '#b8a888' }); drawRail(c, pr, 3); M.routeStops(c, pr, RAIL.map(r => [r[0], r[1], ['PENZA', 'CHELYABINSK', 'OMSK', 'IRKUTSK', 'VLADIVOSTOK'].includes(r[2]) ? r[2] : '']), ease(clamp(lt / 2.8)), tt, { head: true, size: 22 }); M.title(c, 'THE WAY OUT', 'EAST · 9,000 KM TO THE PACIFIC', clamp(lt / .5)); M.vignette(c); }); return; }
  show('taiga'); look('snowdusk', [0xd8c0b8, .004], 1.2, 2.0, 0xffc8a0, [200, 30, -60], [0, 0, 0], [0xc8d0e8, 0x8a8aa0]); U.village.visible = false; U.vfires.forEach(f => f.visible = false);
  const x = -80 + (lt - 3.2) * 12; U.tTrain.position.x = x; U.tTrain.userData.update(x); U.tSmoke.visible = true; L.smk(U.tSmoke, U.tTrain.userData.loco, U.tTrain.userData.loco.userData.chimney, t);
  ct('taiga', lt - 3.2, d - 3.2, [x + 30, 2, 22, x - 10, 3, 0], [x + 28, 3, 20, x - 6, 3, 0], [36, 34]); };
// 54 Vladivostok harbour
SHOTS[54] = (t, lt, d) => { show('harbor'); look('day', [0xd8dce0, .0025], 1.5, 2.4, 0xfff0dc, [-60, 60, 40], [900, 0, 0]); U.sea.userData.update(t);
  U.ships.forEach((s, i) => { s.position.y = Math.sin(t * .8 + i) * .15; s.rotation.z = Math.sin(t * .6 + i) * .01; }); U.fsmoke.forEach((sm, i) => { sm.visible = true; L.smk(sm, U.ships[i], U.ships[i].userData.funnels[0], t); });
  ct('harbor', lt, d, [-70, 30, 120, 0, 5, 0], [-30, 22, 100, 10, 5, 0], [40, 38]); overlay(c => L.caption(c, 'VLADIVOSTOK', 'SHIPS TO FRANCE', clamp(lt / .5) * (1 - clamp((lt - d + .5) / .5)))); };
// 55 an army across a country sliding into civil war: the train passes a burning village at dusk
SHOTS[55] = (t, lt, d) => { show('taiga'); look('dusk', [0x9a7060, .004], 1.0, 1.8, 0xffa060, [100, 30, -60], [0, 0, 0], [0xc0a0a0, 0x4a3a40]); U.village.visible = true; U.vfires.forEach(f => { f.visible = true; f.userData.update(t); }); U.vsmoke.visible = true; U.vsmoke.userData.update(t, V3(-10, 6, -34)); pl2.intensity = 30; pl2.position.set(-10, 6, -30); pl2.distance = 80;
  const x = -6 + lt * 8; U.tTrain.position.x = x; U.tTrain.userData.update(x); U.tSmoke.visible = true; L.smk(U.tSmoke, U.tTrain.userData.loco, U.tTrain.userData.loco.userData.chimney, t);
  ct('taiga', lt, d, [-30, 1.2, 14, 0, 4, -20], [-24, 1.4, 13, 4, 4, -20], [38, 36]); };
// 56 an agreement: commissar and legion officer across the table
SHOTS[56] = (t, lt, d) => { show('office'); look('night', null, .6, 0, 0xffffff, [0, 60, 0], [-900, 0, 0], [0xc0a080, 0x3a2a1a]); S.background = new THREE.Color(0x0a0806); U.tapeStrip.visible = false;
  pose(U.comm, t, { sit: true, armL: .8, armR: .9, elL: 1, elR: 1 }); pose(U.lofficer, t, { sit: true, armL: .8, armR: .9, elL: 1, elR: 1 }); U.comm.position.y = 0; U.lofficer.position.y = 0;
  ct('office', lt, d, [2.8, 1.5, .2, 0, 1.0, 0], [2.4, 1.4, .1, 0, 1.0, 0], [36, 32]); overlay(c => L.caption(c, 'PENZA, MARCH 1918', 'AGREEMENT WITH THE SOVIET GOVERNMENT', clamp(lt / .5) * (1 - clamp((lt - d + .5) / .5)))); };
// 57 surrendering most weapons: rifles handed over and piled, a few guards keep theirs on the roofs
SHOTS[57] = (t, lt, d) => { show('platform'); look('grey', [0xd0ccc4, .006], 1.5, 1.8, 0xf0e8d8, [-40, 60, 30], [0, 0, 900]); U.pTrain.userData.update(0);
  U.handers.forEach((m, i) => { const k = clamp((lt - i * .4) / 1.2); at(m, -8 + i * 1.3, .6, -6.4 - k * 1.2, facing([0, -1])); pose(m, t, { armR: k > .5 && k < .95 ? 1.2 : 0, elR: .3 }); if (k > .9) m.userData.rifle.visible = false; else m.userData.rifle.visible = true; });
  U.reds.forEach((m, i) => { at(m, -8 + i * 1.6, .6, -9.6 - (i % 2) * .6, facing([0, 1])); pose(m, t, { port: i % 2 === 0 }); }); pose(U.clerk, t, { write: true });
  U.roofGuard.forEach(m => pose(m, t, {})); U.pile.scale.setScalar(.6 + clamp(lt / d) * .5);
  if (lt < 3.4) ct('platform', lt, 3.4, [-12, 1.3, -3.6, -4, 1.0, -8.5], [-10, 1.4, -4.0, -3, 1.0, -8.6], [36, 34]); else { const cw = V3(); U.pTrain.userData.cars[3].getWorldPosition(cw); camTo(lt - 3.4, d - 3.4, [cw.x - 2, 1.6, 888, cw.x, 3.8, 900], [cw.x - 1.5, 1.7, 888.5, cw.x, 4.0, 900], [34, 32]); } };
// 58 trust neither side possessed: split screen, eye to eye
SHOTS[58] = (t, lt, d) => { show('office'); look('night', null, .6, 0, 0xffffff, [0, 60, 0], [-900, 0, 0], [0xc0a080, 0x3a2a1a]); S.background = new THREE.Color(0x0a0806); U.tapeStrip.visible = false;
  pose(U.comm, t, { sit: true, armL: .8, armR: .9, elL: 1, elR: 1, look: 0 }); pose(U.lofficer, t, { sit: true, armL: .8, armR: .9, elL: 1, elR: 1 }); U.comm.position.y = 0; U.lofficer.position.y = 0; U.comm.updateMatrixWorld(true); U.lofficer.updateMatrixWorld(true);
  const a = V3(), b = V3(); U.comm.userData.rig.head.getWorldPosition(a); U.lofficer.userData.rig.head.getWorldPosition(b); pl1.intensity = 4; pl1.distance = 5; pl1.position.set(a.x + .2, a.y + .5, a.z + .9); pl2.intensity = 4; pl2.distance = 5; pl2.position.set(b.x - .2, b.y + .5, b.z - .9); const z = lerp(1.75, 1.5, lt / d);
  OV.split = [() => { cam.position.set(a.x, a.y + .02, a.z + z); cam.lookAt(a.x, a.y - .1, a.z); cam.fov = 24; cam.updateProjectionMatrix(); }, () => { cam.position.set(b.x, b.y + .02, b.z - z); cam.lookAt(b.x, b.y - .1, b.z); cam.fov = 24; cam.updateProjectionMatrix(); }]; };
// 59 Bolshevik fear: the telegraph clatters, the wall map is covered in red pins (Legion trains)
SHOTS[59] = (t, lt, d) => { show('office'); look('night', null, .6, 0, 0xffffff, [0, 60, 0], [-900, 0, 0], [0xc0a080, 0x3a2a1a]); S.background = new THREE.Color(0x0a0806);
  U.lofficer.position.y = -50; at(U.comm, -.6, 0, -1.4, facing([.3, 1])); pose(U.comm, t, { armR: 1.1, elR: 1.3, armL: 1.0, elL: 1.4, nod: -.25 }); U.tapeStrip.visible = true; { const hp = V3(); U.comm.updateMatrixWorld(true); U.comm.userData.rig.head.getWorldPosition(hp); U.tapeStrip.position.set(hp.x + 900 + .05, hp.y - .35, hp.z + .38); U.tapeStrip.rotation.set(-.5, .3, 0); U.tapeStrip.scale.set(1.2, 1, 3); }
  pl1.intensity = 6; pl1.position.set(-899.2, 2.2, .8); if (lt < 2.6) ct('office', lt, 2.6, [2.2, 1.6, 2.4, -.2, 1.5, -1.6], [1.9, 1.6, 2.1, -.2, 1.5, -1.6], [38, 36]); else ct('office', lt - 2.6, d - 2.6, [1.2, 1.7, 2.4, 0, 2.0, -2.9], [.4, 1.9, 1.4, 0, 2.0, -2.9], [36, 34]);
  if (lt < 2.6) overlay(c => L.caption(c, 'MOSCOW', 'AN ARMED FOREIGN FORCE ON SOVIET RAILWAYS', clamp(lt / .5) * (1 - clamp((lt - 2.1) / .5)))); };
// 60 the legionaries' fear: inside the boxcar at night; through the door gap, Red sentries with bayonets
SHOTS[60] = (t, lt, d) => { show('boxin'); look('night', [0x0a0e18, .03], .35, .2, 0x8aa0d0, [0, 60, 40], [900, 0, 900], [0x4a5a8a, 0x1a1a22]); S.background = SKY.night;
  pl1.intensity = 3; pl1.position.set(899, 1.6, 900.2); pl2.intensity = 12; pl2.distance = 14; pl2.position.set(902, 2.5, 907); U.floor.position.y = 0; U.hay.forEach(h => h.visible = true);
  U.inside.forEach((m, i) => { pose(m, t, { sit: i > 0, look: .5 - i * .1 }); if (i > 0) m.position.y = -.05; else m.position.y = 0; }); at(U.inside[0], -.9, 0, .95, facing([0, 1])); U.outReds.forEach((m, i) => { pose(m, t, { port: true, walk: i === 1, speed: 4 }); if (i === 1) m.position.x = -3 + Math.sin(t * .4) * 4; });
  if (lt < 2.6) ct('boxin', lt, 2.6, [3.3, 2.0, 1.0, -1.2, .8, -.3], [3.1, 1.95, .9, -1.2, .8, -.3], [44, 42]); else { const hp = V3(); U.inside[0].updateMatrixWorld(true); U.inside[0].userData.rig.head.getWorldPosition(hp); camTo(lt - 2.6, d - 2.6, [hp.x + .55, hp.y + .1, hp.z - 1.1, hp.x - .3, hp.y - .4, hp.z + 6], [hp.x + .5, hp.y + .08, hp.z - 1.0, hp.x - .3, hp.y - .45, hp.z + 6], [40, 38]); } };
// 61 hidden weapons: the floorboard lifts, rifles and grenades beneath the hay
SHOTS[61] = (t, lt, d) => { show('boxin'); look('night', null, .5, 0, 0xffffff, [0, 60, 0], [900, 0, 900], [0x8a7060, 0x2a2018]); S.background = new THREE.Color(0x050403); pl1.intensity = 6; pl1.position.set(901.2, 1.2, 901);
  U.inside.forEach(m => m.position.y = -50); const k = ease(clamp(lt / .9)); U.floor.position.set(1.6 + k * .3, .26 + k * .35, .6 + k * .2); U.floor.rotation.z = k * .6; U.hay.forEach((h, i) => h.position.x = 1.0 + i * .25 + k * (i % 2 ? .6 : -.6));
  ct('boxin', lt, d, [1.6, 1.55, 1.25, 1.6, .1, .5], [1.6, 1.25, 1.2, 1.6, .05, .55], [40, 36]); };
// 62 moving east, slowly: the train crawls across the steppe
SHOTS[62] = (t, lt, d) => { show('junction'); look('summer', [0xe0d8c8, .002], 1.5, 2.4, 0xfff0d8, [40, 50, -30], [0, 0, -900]); const x = -60 + lt * 3; U.jTrain.position.x = x; U.jTrain.userData.update(x); U.armT.position.y = -50;
  ct('junction', lt, d, [x + 30, 1.5, 12, x, 2.4, 0], [x + 29, 1.5, 12, x + 1, 2.4, 0], [34, 34]); };
// 63 separated across vast distances: echelons as dots strung along 7,000 km
SHOTS[63] = (t, lt, d) => { OV.noGL = true; overlay((c, tt) => { const pr = RU_PROJ(); M.paper(c); M.baseLand(c, pr, { land: '#b8a888' }); drawRail(c, pr, 4); const n = 60, k = clamp(lt / 1.4);
  for (let i = 0; i < n * k; i++) { const q = (i * 0.6180339 % 1); const [x, y] = railAt(pr, q * .98); c.fillStyle = '#f2f0ea'; c.strokeStyle = '#c8241c'; c.lineWidth = 3; c.beginPath(); c.arc(x, y, 7, 0, 7); c.fill(); c.stroke(); }
  M.title(c, 'SPRING 1918', 'SOME 60 LEGION TRAINS ALONG THE RAILWAY', clamp(lt / .5)); M.vignette(c); }); };
// 64 each delay left a group vulnerable: a lone sentry at a dark siding, a red signal far down the line
SHOTS[64] = (t, lt, d) => { show('wsiding'); look('night', [0x0c1220, .015], .7, .4, 0x8aa0d0, [-30, 50, -40], [-900, 0, 900], [0x6a7aaa, 0x2a2a36]); U.wsnow.visible = true; U.wsnow.userData.update(t); U.campfire.userData.update(t); pl1.intensity = 8 + Math.sin(t * 13) * 1.5; pl1.position.set(-901.2, 1, 906.0); U.wTrain.userData.update(0);
  pose(U.sentry, t, { look: -.2 + Math.sin(t * .4) * .2 }); U.sentry.updateMatrixWorld(true);
  if (lt < 3.6) ct('wsiding', lt, 3.6, [6, 1.7, 8, 0, 1.4, 3.2], [3.5, 1.65, 6.5, 0, 1.5, 3.2], [36, 32]); else { const hp = V3(); U.sentry.userData.rig.head.getWorldPosition(hp); camTo(lt - 3.6, d - 3.6, [hp.x + 1.6, hp.y + .1, hp.z + .9, hp.x - 30, hp.y - 1.2, hp.z - 2.5], [hp.x + 1.4, hp.y + .08, hp.z + .8, hp.x - 30, hp.y - 1.0, hp.z - 2.5], [36, 32]); } };
// 65 then came Chelyabinsk: sepia flashback of the iron bar
SHOTS[65] = (t, lt, d) => { OV.noGL = true; overlay((c, tt) => { const i = Math.min(U.flash.length - 1, Math.floor(lt / d * U.flash.length)), im = U.flash[i]; c.filter = 'sepia(.9) contrast(1.15) brightness(.85)'; if (im.complete && im.naturalWidth) c.drawImage(im, -40, -22, L.W + 80, L.H + 44); c.filter = 'none';
  for (let k = 0; k < 8; k++) { c.fillStyle = `rgba(30,20,10,${.15 + (k % 3) * .05})`; c.fillRect(((tt * 977 + k * 331) % 1) * L.W, 0, 2, L.H); } L.caption(c, 'CHELYABINSK', '14 MAY 1918', clamp(lt / .3)); }); };
// 66 the confrontation did not create the distrust: hero face, harsh lamp at night
SHOTS[66] = (t, lt, d) => { show('boxin'); look('night', [0x0a0e18, .03], .3, .2, 0x8aa0d0, [0, 60, 40], [900, 0, 900], [0x4a5a8a, 0x1a1a22]); S.background = SKY.night; U.inside.forEach((m, i) => { if (i) m.position.y = -50; });
  at(U.inside[0], -.9, 0, .95, facing([0, 1])); pose(U.inside[0], t, { look: 0 }); U.inside[0].updateMatrixWorld(true); const hp = V3(); U.inside[0].userData.rig.head.getWorldPosition(hp); pl1.intensity = 5; pl1.distance = 6; pl1.position.set(hp.x + .4, hp.y + .2, hp.z + .9);
  camTo(lt, d, [hp.x + .35, hp.y - .02, hp.z + .8, hp.x, hp.y, hp.z], [hp.x + .3, hp.y - .01, hp.z + .68, hp.x, hp.y, hp.z], [30, 26]); };
// 67 distrust becomes armed resistance: rifles come out, bolts work, they load
SHOTS[67] = (t, lt, d) => { show('boxin'); look('night', null, .5, 0, 0xffffff, [0, 60, 0], [900, 0, 900], [0x8a7060, 0x2a2018]); S.background = new THREE.Color(0x050403); pl1.intensity = 6; pl1.position.set(900.5, 1.6, 901);
  U.floor.position.set(1.9, .61, .8); U.floor.rotation.z = .6; U.inside.forEach((m, i) => { at(m, -2.2 + i * 1.0, 0, .6, facing([0, 1])); pose(m, t, { aim: i % 2 === 0, port: i % 2 === 1 }); m.userData.rifle && (m.userData.rifle.visible = true); });
  ct('boxin', lt, d, [3.0, 1.9, -1.05, -.6, 1.1, .9], [2.8, 1.85, -1.0, -.6, 1.1, .9], [46, 44]); };
// 68 orders to disarm collide with determination: Trotsky's telegram -> the standoff across the tracks
SHOTS[68] = (t, lt, d) => { if (lt < 3.0) { show('office'); look('night', null, .4, 0, 0xffffff, [0, 60, 0], [-900, 0, 0], [0xc0a080, 0x3a2a1a]); S.background = new THREE.Color(0x0a0806); ct('office', 0, 1, [0, 2.2, 2.5, 0, 1.2, 0], [0, 2.2, 2.5, 0, 1.2, 0], [36, 36]);
    overlay(c => { c.fillStyle = 'rgba(0,0,0,.6)'; c.fillRect(0, 0, L.W, L.H); M.documentPage(c, lt, [['TELEGRAM · 25 MAY 1918', 28, true], [''], ['ALL SOVIETS ARE ORDERED TO DISARM', 26], ['THE CZECHOSLOVAKS IMMEDIATELY.', 26], ['EVERY ARMED CZECHOSLOVAK FOUND ON', 26], ['THE RAILWAY IS TO BE SHOT ON THE SPOT.', 26], [''], ['                    — TROTSKY', 26, true]], { w: 1000, h: 560, cps: 55, bg: '#e4dcc4' }); }); return; }
  show('platform'); look('grey', [0xd0ccc4, .006], 1.4, 1.6, 0xf0e8d8, [-40, 60, 30], [0, 0, 900]); U.pTrain.userData.update(0); const q = lt - 3.0;
  U.reds.forEach((m, i) => { at(m, -6 + i * 1.4, .6, -9.6 - (i % 2) * .5, facing([0, 1])); pose(m, t, { aim: true }); }); U.handers.forEach((m, i) => { at(m, -6 + i * 1.6, 0, 3.4 + (i % 2) * .6, facing([0, -1])); pose(m, t, { aim: true }); m.userData.rifle.visible = true; }); U.clerk.position.y = -50; U.pile.visible = false;
  ct('platform', q, d - 3.0, [-12, 1.4, -3.2, 0, 1.4, -3.2], [-11, 1.4, -3.0, 1, 1.4, -3.2], [30, 28]); };
// 69 local clashes become a wider struggle: shooting across the tracks
SHOTS[69] = (t, lt, d) => { show('platform'); look('grey', [0xd0ccc4, .006], 1.4, 1.6, 0xf0e8d8, [-40, 60, 30], [0, 0, 900]); U.pTrain.userData.update(0); U.clerk.position.y = -50; U.pile.visible = false;
  U.reds.forEach((m, i) => { at(m, -6 + i * 1.4, .6, -9.6 - (i % 2) * .5, facing([0, 1])); pose(m, t, { aim: true }); if (lt > 1.2 && i % 3 === 0) { m.rotation.x = -clamp((lt - 1.2 - i * .05) / .5) * 1.4; } }); U.handers.forEach((m, i) => { at(m, -6 + i * 1.6, 0, 3.4 + (i % 2) * .6, facing([0, -1])); pose(m, t, { aim: true, kneel: i % 2 === 0 }); });
  [...U.reds, ...U.handers].forEach((m, i) => { const f = U.flashes[i % 14]; const on = ((t * 7 + i * 1.7) % 1) < .18; if (on && i < 14) { f.visible = true; const p = V3(.62, .04, 0); m.userData.rifle.localToWorld(p); f.position.copy(p); f.scale.setScalar(.7); } });
  U.gunsmoke.visible = true; U.gunsmoke.userData.update(t, V3(-1, 2.4, 897)); pl2.intensity = 10 + Math.sin(t * 50) * 5; pl2.position.set(0, 2, 897);
  ct('platform', lt, d, [10, 1.6, -1.5, -4, 1.4, -4], [9, 1.7, -2, -4, 1.4, -4], [38, 36], .02); };
// 70 scattered: each train ringed by enemies on the map
SHOTS[70] = (t, lt, d) => { OV.noGL = true; overlay((c, tt) => { const pr = RU_PROJ(); M.paper(c); M.baseLand(c, pr, { land: '#b8a888' }); drawRail(c, pr, 4);
  for (let i = 0; i < 9; i++) { const [x, y] = railAt(pr, .04 + i * .115); const r = 30 + Math.sin(tt * 4 + i) * 4; c.strokeStyle = `rgba(200,36,28,${clamp(lt / .6)})`; c.lineWidth = 5; c.setLineDash([8, 6]); c.beginPath(); c.arc(x, y, r, 0, 7); c.stroke(); c.setLineDash([]); c.fillStyle = '#f2f0ea'; c.beginPath(); c.arc(x, y, 8, 0, 7); c.fill(); }
  M.title(c, 'SCATTERED', 'ISOLATED GROUPS, SURROUNDED', clamp(lt / .5)); M.vignette(c); }); };
// 71 no position held the whole Legion: one train at a small station, alone in the steppe (aerial)
SHOTS[71] = (t, lt, d) => { show('junction'); U.nests.forEach(n => { n.visible = false; n.userData.man.visible = false; }); look('summer', [0xe0d8c8, .0018], 1.5, 2.4, 0xfff0d8, [40, 50, -30], [0, 0, -900]); U.jTrain.position.x = -6; U.jTrain.userData.update(0); U.armT.position.y = -50;
  ct('junction', lt, d, [-40, 60, 60, 0, 0, -4], [-20, 90, 70, 0, 0, -4], [40, 44]); };
// 72 attacked separately: an armored train shells a lone echelon
SHOTS[72] = (t, lt, d) => { show('junction'); look('dusk', [0x9a7060, .004], 1.0, 1.8, 0xffa060, [100, 30, -60], [0, 0, -900]); U.armT.position.y = 0; U.armT.position.x = -120; U.jTrain.position.x = -6; U.jTrain.userData.update(0);
  const tur = U.armT.userData.front.userData.turret; tur.rotation.y = 0; const fire = (lt % 1.2) < .1; if (fire) { const mz = U.armT.userData.front.userData.muzzle.clone(); tur.localToWorld(mz); U.cflash.visible = true; U.cflash.position.copy(mz); U.cflash.scale.setScalar(4); pl2.intensity = 30; pl2.position.copy(mz); }
  U.jblasts.forEach((b, i) => { b.position.set(-40 + i * 12, 0, (i - 1) * 7); b.userData.update(lt - .4 - i * .8); });
  ct('junction', lt, d, [-60, 2.2, 14, -20, 2, 0], [-56, 2.4, 13, -16, 2, 0], [36, 34], .02); };
// 73 junctions across an enormous network: map lights up -> aerial of the junction
SHOTS[73] = (t, lt, d) => { if (lt < 4.2) { OV.noGL = true; overlay((c, tt) => { const pr = RU_PROJ(); M.paper(c); M.baseLand(c, pr, { land: '#b8a888' }); drawRail(c, pr, 4);
    const br = [[[56.0, 54.7], [55.9, 58.0]], [[61.4, 55.16], [60.6, 56.8]], [[73.4, 54.99], [69.0, 57.2]], [[82.9, 55.03], [84.9, 56.5]], [[50.1, 53.2], [48.0, 55.8]], [[127.5, 50.3], [135.1, 48.5]]]; 
    RAIL.forEach(([lo, la, n], i) => { const k = clamp((lt - .3 - i * .25) / .3); if (k <= 0) return; const [x, y] = pr(lo, la); c.fillStyle = '#c8241c'; c.beginPath(); c.arc(x, y, 14 * k, 0, 7); c.fill(); c.fillStyle = '#f2f0ea'; c.beginPath(); c.arc(x, y, 7 * k, 0, 7); c.fill(); if (n) M.label(c, n, x, i % 2 ? y + 38 : y - 22, 20, '#fff4e0', k); });
    M.title(c, 'STATIONS & JUNCTIONS', 'THE KEYS TO THE RAILWAY', clamp(lt / .5)); M.vignette(c); }); return; }
  show('junction'); look('summer', [0xe0d8c8, .0018], 1.5, 2.4, 0xfff0d8, [40, 50, -30], [0, 0, -900]); U.armT.position.y = -50; U.jTrain.position.x = -6; U.jTrain.userData.update(0); U.nests.forEach(n => { n.visible = false; n.userData.man.visible = false; });
  ct('junction', lt - 4.2, d - 4.2, [-30, 45, 70, 20, 0, 0], [10, 35, 60, 20, 0, 0], [40, 40]); };
// 74 they began taking those positions: men storm the station, the white-red goes up
SHOTS[74] = (t, lt, d) => { show('junction'); look('summer', [0xe0d8c8, .0018], 1.5, 2.4, 0xfff0d8, [40, 50, -30], [0, 0, -900]); U.armT.position.y = -50; U.jTrain.position.x = -6; U.jTrain.userData.update(0); U.jFlag.userData.update(t);
  U.stormers.forEach((m, i) => { const k = clamp((lt - i * .08) / 1.6); at(m, 8 + i * .8 - k * 6, k > .55 ? .6 : 0, 4 - k * 11, facing([-.4, -1])); pose(m, t, { walk: k < 1, speed: 11, port: true }); });
  const up = ease(clamp((lt - .6) / 1.2)); U.jFlag.position.y = lerp(.9, 4, up);
  ct('junction', lt, d, [10, .8, 8, -2, 3, -9], [8, 1.0, 7, -3, 3.4, -9], [38, 36]); };
// 75-77 one continuous pull-back: train -> station -> approaches -> the track between
SHOTS[75] = (t, lt, d) => { show('junction'); look('summer', [0xe0d8c8, .0015], 1.5, 2.4, 0xfff0d8, [40, 50, -30], [0, 0, -900]); U.armT.position.y = -50; U.jTrain.position.x = -6; U.jTrain.userData.update(0); U.jFlag.userData.update(t);
  U.stormers.forEach(m => m.position.y = -50); U.nests.forEach((n, i) => { n.visible = true; n.userData.man.visible = true; pose(n.userData.man, t, { aim: true }); });
  const T0 = ST(75), T1 = ST(76), T2 = ST(77), T3 = C[77].end; const q = t < T1 ? (t - T0) / (T1 - T0) * .25 : t < T2 ? .25 + (t - T1) / (T2 - T1) * .35 : .6 + (t - T2) / (T3 - T2) * .4;
  const P0 = [-4, 3, 10, -6, 2.5, 0], P1 = [-10, 14, 26, -2, 1, -6], P2 = [-30, 55, 75, 0, 0, -4], P3 = [60, 70, 110, 140, 0, 0];
  const seg = q < .25 ? [P0, P1, q / .25] : q < .6 ? [P1, P2, (q - .25) / .35] : [P2, P3, (q - .6) / .4]; const e = ease(seg[2]); const pv = seg[0].map((v, k) => lerp(v, seg[1][k], e)); camAt('junction', pv.slice(0, 3), pv.slice(3), 38 + q * 6);
  const lab = q < .25 ? 0 : q < .6 ? 1 : 2; const words = ['TO FREE A TRAIN: A STATION', 'TO HOLD THE STATION: THE APPROACHES', 'TO REACH THE NEXT UNIT: THE TRACK BETWEEN']; overlay(c => { M.label(c, words[lab], L.W / 2, L.H - 110, 40, '#fff4e0'); }); };
// 78 the escape route became a battlefield: armored train fires down the line at dusk
SHOTS[78] = (t, lt, d) => { show('junction'); look('dusk', [0x9a7060, .004], 1.0, 1.8, 0xffa060, [100, 30, -60], [0, 0, -900]); U.armT.position.y = 0; U.armT.position.x = -10; U.armT.rotation.y = Math.PI; U.jTrain.position.x = -200;
  const tur = U.armT.userData.front.userData.turret; tur.rotation.y = .3; const fire = lt > .3 && lt < .42 || lt > 1.5 && lt < 1.62; if (fire) { const mz = U.armT.userData.front.userData.muzzle.clone(); tur.localToWorld(mz); U.cflash.visible = true; U.cflash.position.copy(mz); U.cflash.scale.setScalar(5); pl2.intensity = 40; pl2.position.copy(mz); }
  ct('junction', lt, d, [-28, 1.0, 10, -18, 2.6, 6], [-29, 1.1, 9, -18, 2.8, 6], [32, 30], fire ? .05 : 0); U.armT.rotation.y = 0; };
// 79 by summer the Legion held the cities: map flips city after city
SHOTS[79] = (t, lt, d) => { OV.noGL = true; overlay((c, tt) => { const pr = RU_PROJ(); M.paper(c); M.baseLand(c, pr, { land: '#b8a888' }); drawRail(c, pr, 4);
  RAIL.filter(r => r[2]).forEach(([lo, la, n], i) => { const k = clamp((lt - .2 - i * .35) / .25), [x, y] = pr(lo, la); c.save(); c.translate(x, y); c.scale(1, 1); c.fillStyle = k > .5 ? '#f2f0ea' : '#b81a14'; c.fillRect(-14, -40, 28, 9); c.fillStyle = k > .5 ? '#c8241c' : '#b81a14'; c.fillRect(-14, -31, 28, 9); c.fillStyle = '#3a2a1a'; c.fillRect(-16, -40, 2, 40); c.restore(); c.fillStyle = '#2a1a10'; c.beginPath(); c.arc(x, y, 6, 0, 7); c.fill(); M.label(c, n, x, y + 30, 18, '#fff4e0'); });
  M.title(c, 'SUMMER 1918', 'THE RAILWAY CITIES FALL TO THE LEGION', clamp(lt / .5)); M.vignette(c); }); };
// 80 anti-Bolshevik governments fill the vacuum: white officers raise the tricolour; a proclamation goes up
SHOTS[80] = (t, lt, d) => { show('wsquare'); look('day', [0xd8dce0, .005], 1.6, 2.4, 0xfff0dc, [-40, 60, 30], [900, 0, -900]); U.wFlagCZ.userData.update(t); U.wFlag.userData.update(t);
  const up = ease(clamp((lt - .8) / 2.4)); U.wFlag.position.y = 6; U.whites.forEach((m, i) => pose(m, t, { salute: lt > 2 && i % 2 === 0 })); U.wcrowd.forEach((m, i) => pose(m, t, { armR: lt > 3 && i % 3 === 0 ? -2.6 : 0, look: .2 }));
  if (lt < 4.2) ct('wsquare', lt, 4.2, [3, 1.2, 8, 0, 10, -13], [2, 1.1, 6, 0, 14, -13], [38, 40]); else ct('wsquare', lt - 4.2, d - 4.2, [11.2, 1.8, -4, 8.2, 2.4, -7.9], [9.7, 2.1, -5.6, 8.2, 2.4, -7.9], [34, 30]);
  overlay(c => L.caption(c, 'SAMARA, JUNE 1918', 'ANTI-BOLSHEVIK GOVERNMENTS', clamp(lt / .5) * (1 - clamp((lt - 3.7) / .5)))); };
// 81 a struggle over who would govern Russia: red vs white on the map, the railway between
SHOTS[81] = (t, lt, d) => { OV.noGL = true; overlay((c, tt) => { const pr = RU_PROJ(); M.paper(c); M.baseLand(c, pr, { land: '#b8a888' }); const k = ease(clamp(lt / 2.2));
  const ru = M.byName('Russia'); if (ru) { c.save(); M.pathFeature(c, pr, ru); c.clip(); const [sx] = pr(54, 55); const gR = c.createLinearGradient(0, 150, 0, 300); gR.addColorStop(0, 'rgba(180,26,20,0)'); gR.addColorStop(1, 'rgba(180,26,20,.55)'); const gW = c.createLinearGradient(0, 150, 0, 300); gW.addColorStop(0, 'rgba(242,240,234,0)'); gW.addColorStop(1, 'rgba(242,240,234,.55)'); c.fillStyle = gR; c.fillRect(0, 150, sx * k, L.H); c.fillStyle = gW; c.fillRect(L.W - (L.W - sx) * k, 150, L.W, L.H); c.restore(); }
  drawRail(c, pr, 5); const [rx, ry] = pr(40, 58), [wx, wy] = pr(95, 57); M.label(c, 'RED', rx, ry, 56, '#b81a14', k); M.label(c, 'WHITE', wx, wy, 56, '#f8f4ea', k); M.title(c, 'THE RUSSIAN CIVIL WAR', 'THE RAILWAY AT ITS HEART', clamp(lt / .5)); M.vignette(c); }); };
