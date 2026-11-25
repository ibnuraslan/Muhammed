// ===================== SECTION 2: 1914-1916, cues 13-31 =====================
import * as L from './lib3.js';
import * as M from './maps.js';
import * as P from './props.js';
const { THREE, S, cam, U, SKY, V3, at, mesh, mat, pbr, model, clamp, lerp, ease, rng, pl1, pl2, pl3, look, camTo, show, fx, overlay, OV, pose, facing, man, SETS } = L;
export const RANGE = { from: 13, to: 31 };
let C; const ST = i => C[i].start;
// camera helper in set-local coordinates
const ct = (set, lt, d, a, b, fov = [35, 35], shake = 0) => { const o = SETS[set].position; camTo(lt, d, [a[0] + o.x, a[1] + o.y, a[2] + o.z, a[3] + o.x, a[4] + o.y, a[5] + o.z], [b[0] + o.x, b[1] + o.y, b[2] + o.z, b[3] + o.x, b[4] + o.y, b[5] + o.z], fov, shake); };
const wpos = (set, x, y, z) => { const o = SETS[set].position; return V3(x + o.x, y + o.y, z + o.z); };
const HABS = ['#1a1a1a', '#e8c020'], CZ = ['#f2f0ea', '#c8241c'], RU = ['#f2f0ea', '#2a4ea0', '#c8241c'], FR = ['#2a4ea0', '#f2f0ea', '#c8241c'];
const ukDraw = x => { x.fillStyle = '#1e2c6a'; x.fillRect(0, 0, 128, 80); x.strokeStyle = '#f2f0ea'; x.lineWidth = 14; x.beginPath(); x.moveTo(0, 0); x.lineTo(128, 80); x.moveTo(128, 0); x.lineTo(0, 80); x.stroke(); x.strokeStyle = '#c8241c'; x.lineWidth = 5; x.stroke(); x.fillStyle = '#f2f0ea'; x.fillRect(52, 0, 24, 80); x.fillRect(0, 28, 128, 24); x.fillStyle = '#c8241c'; x.fillRect(57, 0, 14, 80); x.fillRect(0, 33, 128, 14); };
function prone(m) { const g = new THREE.Group(); m.rotation.set(0, 0, -Math.PI / 2); m.position.set(0, .22, 0); g.add(m); g.userData.m = m; return g; }
function crawl(g, t, k = 0) { const m = g.userData.m, r = m.userData.rig; m.userData.pose(t, {}); const s = Math.sin(t * 3 + k); r.arms[0].sh.rotation.z = 2.6 + s * .3; r.arms[1].sh.rotation.z = 2.6 - s * .3; r.arms[0].el.rotation.z = .6; r.arms[1].el.rotation.z = .6; r.legs[0].hip.rotation.z = .3 + s * .25; r.legs[1].hip.rotation.z = .3 - s * .25; r.legs[0].knee.rotation.z = -.6 - s * .3; r.legs[1].knee.rotation.z = -.6 + s * .3; r.head.rotation.z = .5; }
export async function build(cues) {
  C = cues;
  SKY.day = L.paintSky('#7fa6d4', '#e2e4dc', '#fdf9f0', '#d9d9de', '#a3abbd', 5);
  SKY.grey = L.paintSky('#8e98a6', '#cfcec6', '#e8e6e0', '#bdbdc2', '#8d929e', 7);
  SKY.dawn = L.paintSky('#6c8ac0', '#f2cfa0', '#fff2d8', '#f0c8b4', '#a898b4', 3, { sun: [1250, 760] });
  SKY.red = L.paintSky('#3a2a40', '#e87040', '#ffb070', '#c86a50', '#5a3a4a', 17, { sun: [960, 900] });
  SKY.night = L.paintSky('#0a1228', '#28344e', '#4a5a7e', '#323e5c', '#1e263c', 11, { stars: true });
  SKY.snow = L.paintSky('#9aa4b4', '#e4e4e6', '#f4f4f6', '#d4d6dc', '#a4aab8', 19);
  // ---------- SQUARE (Bohemian town 1914 / Kiev) ----------
  const sq = L.addSet('square', 0, 0); L.ground(sq, 'cobble');
  const tints = [0xd8c8a8, 0xc8b08a, 0xe0d4b8, 0xb8a888, 0xd0b898, 0xc4b4a0];
  for (let i = 0; i < 6; i++) { const h = L.house(9, 10 + (i % 3) * 2, 8, { color: tints[i], roof: 0x7a3a2a }); at(h, -27 + i * 10.4, 0, -15); sq.add(h); }
  for (let i = 0; i < 6; i++) { const h = L.house(9, 9 + (i % 2) * 3, 8, { color: tints[(i + 3) % 6] }); at(h, -27 + i * 10.4, 0, 17, Math.PI); sq.add(h); }
  for (const s of [-1, 1]) for (let i = 0; i < 3; i++) { const h = L.house(9, 11, 8, { color: tints[i + 1] }); at(h, s * 35, 0, -6 + i * 10, -s * Math.PI / 2); sq.add(h); }
  const tw = new THREE.Group(); mesh(new THREE.BoxGeometry(5, 22, 5), pbr('grey_plaster_02', [2, 4], { color: 0xd8ccb0 }), [0, 11, 0], [0, 0, 0], tw); mesh(new THREE.ConeGeometry(3.6, 9, 4), mat(0x3a5a4a, .6), [0, 26.5, 0], [0, Math.PI / 4, 0], tw); mesh(new THREE.CylinderGeometry(1.2, 1.2, .2, 20), mat(0xe8e0c0, .6), [0, 17, 2.55], [Math.PI / 2, 0, 0], tw); at(tw, 4, 0, -30); sq.add(tw);
  const pt = P.poster([['K. u. K.', 40, 90], ['MOBILISIERUNG', 46, 190], ['VŠEOBECNÁ', 50, 300], ['MOBILISACE', 50, 360], ['1914', 70, 480], ['Wir haben ...', 26, 560], ['█████ ███ ████ ██', 22, 610], ['██ ████ ███████ ██', 22, 650]], { draw: x => { x.fillStyle = '#1a1a1a'; x.beginPath(); x.arc(256, 46, 0, 0, 7); x.fill(); } });
  U.poster = L.plate(1.6, 2.25, pt, sq, [-6.2, 2.3, -10.92]); U.smallP = [-9.7, -8.3, -4.1, -2.7].map((x, i) => L.plate(1.1, 1.5, P.poster([['', 10, 10], ['█ ███ ██', 30, 200 + i * 30]], { bg: ['#d8c8a0', '#e0d0b0', '#c8b890', '#e4d8bc'][i] }), sq, [x, 2.1, -10.92]));
  const kp = P.poster([['ЧЕШСКАЯ', 52, 110], ['ДРУЖИНА', 52, 175], ['ČESKÁ DRUŽINA', 40, 280], ['DOBROVOLNÍCI!', 40, 350], ['VOLUNTEERS', 30, 420], ['KIEV 1914', 44, 520]], { bg: '#e8dcbc' }); U.kposters = [-6.2, -4.1].map(x => L.plate(1.5, 2.1, kp, sq, [x, 2.3, -10.91]));
  U.habs = new THREE.Group(); sq.add(U.habs); U.habsF = []; for (const x of [-22, -12, 10, 20]) { const f = L.flag(1.6, 1.0, HABS); const p = L.poleWithFlag(2.4, f); p.position.set(x, 7.2, -10.6); p.rotation.x = .7; U.habs.add(p); U.habsF.push(f); }
  U.crowd = [...Array(16)].map((_, i) => { const m = man({ u: i % 5 === 4 ? 'woman' : i % 3 ? 'civil' : 'suit', seed: 300 + i, rifle: false }); at(m, -9.5 + (i % 6) * 1.05 + (i > 5 ? .5 : 0), 0, -9.0 + Math.floor(i / 6) * 1.1, facing([0, -1]) + ((i * 37) % 10 - 5) * .04); sq.add(m); return m; });
  // Kiev recruiting table
  U.kiev = new THREE.Group(); sq.add(U.kiev); const kt = P.longTable(2.4, 1.0); at(kt, 8, 0, -7); U.kiev.add(kt); { const pp = P.papers(5, 3); pp.position.set(8, 0, -7); U.kiev.add(pp); }
  U.kievF = []; for (const [x, st] of [[6.2, CZ], [9.8, RU]]) { const f = P.flagStand(st, { w: 1.2, h: .8 }); at(f, x, 0, -8.2); U.kiev.add(f); U.kievF.push(f.userData.flag); }
  U.officer = man({ u: 'russian', seed: 330, rifle: false }); at(U.officer, 8.4, 0, -7.9, facing([0, 1])); U.kiev.add(U.officer); const ch = P.chair(); at(ch, 8.4, 0, -7.95, -Math.PI / 2); U.kiev.add(ch);
  U.signer = man({ u: 'civil', seed: 331, rifle: false }); at(U.signer, 7.6, 0, -6.15, facing([0, -1])); U.kiev.add(U.signer);
  U.queue = [...Array(9)].map((_, i) => { const m = man({ u: i % 3 ? 'civil' : 'suit', seed: 340 + i, rifle: false }); at(m, 6.6 - i * .9 - (i % 2) * .2, 0, -5.2 + i * .65, facing([1, -.6])); U.kiev.add(m); return m; });
  U.handRifle = L.lowRifle(); U.kiev.add(U.handRifle);
  // ---------- DEPOT (Prague station, troops leave) ----------
  const dp = L.addSet('depot', 400, 0); L.ground(dp, 'dirt'); dp.add(L.track2(600, -300)); const sb = L.station('PRAHA', { wallTint: 0xdcc8a4 }); at(sb, 0, .6, -15.5); dp.add(sb); mesh(new THREE.BoxGeometry(90, .6, 6.2), pbr('old_wood_floor', [26, 2], { color: 0x9a8a78 }), [0, .3, -4.6 - 3.1], [0, 0, 0], dp);
  dp.add(L.forest(80, -300, 300, 25, 120, 61, false));
  U.dtrain = L.train(6, { openIdx: [0, 1, 2, 3, 4, 5], color: 0x22282a }); at(U.dtrain, -30, 0, 0, Math.PI); dp.add(U.dtrain);
  U.dtrain.userData.cars.forEach((c, i) => { const tx = L.textTex([['40 MANN · 6 PFERDE', 58, 90, 'bold 58px DejaVu Sans, sans-serif']], { w: 1024, h: 160, bg: 'rgba(0,0,0,0)', fg: '#f4f0e4', border: false }); const p = L.plate(2.2, .34, tx, c, [-2.6, c.userData.by0 + 1.9, 1.42]); p.material.transparent = true;
    for (let k = 0; k < 9; k++) { const s = mesh(new THREE.SphereGeometry(.22, 8, 6), mat(k % 3 ? 0x3a6a2a : 0xd8b030, .9), [-3.4 + k * .85, c.userData.by0 + 2.65, 1.45], [0, 0, 0], c); } });
  U.dflags = []; for (const x of [-12, -4, 4, 12]) { const f = L.flag(1.4, .9, HABS); const p = L.poleWithFlag(3.2, f); at(p, x, 4.6, -10.2); dp.add(p); U.dflags.push(f); }
  U.column = [...Array(18)].map((_, i) => { const m = man({ u: 'austro', seed: 400 + i }); dp.add(m); return m; });
  U.women = [...Array(8)].map((_, i) => { const m = man({ u: i % 3 ? 'woman' : 'civil', seed: 430 + i, rifle: false }); at(m, -10 + i * 2.2, .6, -9.6 - (i % 2) * .6, facing([0, 1])); dp.add(m); return m; });
  U.young = man({ u: 'austro', seed: 455, rifle: false, beard: 0, noMustache: true, hero: true }); const c2 = U.dtrain.userData.cars[2]; at(U.young, 0, c2.userData.by0, 1.5, facing([0, 1])); c2.add(U.young);
  U.youngMates = [0, 1].map(k => { const m = man({ u: 'austro', seed: 460 + k, rifle: false }); at(m, -.7 + k * 1.4, c2.userData.by0, 1.1, facing([0, 1]) + (k ? -.4 : .4)); c2.add(m); return m; });
  U.dsmoke = fx(L.smoke(V3(), { n: 60, color: 0x5a5a60, wind: [.8, .3], rise: 12, size: 1.4, grow: 5, life: 6, opacity: .9 }));
  // ---------- CAFE (exiles in Paris, night) ----------
  const cf = L.addSet('cafe', -400, 0); const rm = P.room(7, 5, 3.4, { wall: 0x8a6a50 }); cf.add(rm);
  const wp = P.windowPane(2.2, 1.6, P.nightCity(5, { rain: true, tower: true })); at(wp, .4, 1.9, -2.42); cf.add(wp);
  const bs = P.bookshelf(2.2, 2.6); at(bs, -3.38, 0, -.4, Math.PI / 2); cf.add(bs);
  const tb = P.longTable(2.0, 1.1); at(tb, 0, 0, 0); cf.add(tb); const lamp = P.deskLamp(); at(lamp, -.6, .82, -.2); cf.add(lamp); U.cafeLamp = lamp;
  U.paperTex = L.textTex([['LE MATIN', 70, 90], ['LA GUERRE', 120, 230], ["L'AUTRICHE-HONGRIE", 50, 330], ['MOBILISE', 50, 390], ['██████ ███ ████ ████', 26, 470], ['███ ██████ █████ ███', 26, 510]], { w: 512, h: 640, bg: '#e8dcc0', border: false });
  U.cafePaper = L.plate(.42, .52, U.paperTex, cf, [.15, .846, .1], [-Math.PI / 2, 0, .2]);
  U.exiles = [['suit', 500, -.75, .7, 'sit', -Math.PI / 2 + .3], ['suit', 501, .9, .55, 'sit', facing([-1, -.3])], ['civil', 502, .4, -.95, 'stand', facing([0, 1])]].map(([u, sd, x, z, p, ry]) => { const m = man({ u, seed: sd, rifle: false, beard: sd === 501 ? .8 : undefined }); at(m, x, 0, z, ry); m.userData.p = p; cf.add(m); if (p === 'sit') { const c = P.chair(); at(c, x - Math.cos(ry) * .12, 0, z + Math.sin(ry) * .12, ry + Math.PI); cf.add(c); } return m; });
  // ---------- HALL (Allied diplomats) ----------
  const hl = L.addSet('hall', 0, 400); const hr = P.room(16, 10, 5.5, { wall: 0xc8b898, panel: 0x3a2412, floor: 0x6a4a30 }); hl.add(hr);
  const lt2 = P.longTable(8, 1.6); hl.add(lt2); { const pp = P.papers(10, 9); pp.position.set(0, 0, 0); hl.add(pp); }
  U.chand = [-3, 3].map(x => { const c = P.chandelier(); at(c, x, 5.4, 0); hl.add(c); return c; });
  U.hallFlags = []; [[FR, true], [null, false, ukDraw], [RU, false]].forEach(([st, v, dr], i) => { const f = P.flagStand(st || ['#1e2c6a'], { w: 1.2, h: .8 }); if (dr || v) { f.remove(f.userData.flag); const nf = L.flag(1.2, .8, st || ['#1e2c6a'], { vertical: v, draw: dr }); nf.position.set(0, 2.35, 0); f.add(nf); f.userData.flag = nf; } at(f, -7.6 + i * 1.5, 0, -3.8); hl.add(f); U.hallFlags.push(f.userData.flag); });
  const emap = (() => { const cv = document.createElement('canvas'); cv.width = 1024; cv.height = 640; const x = cv.getContext('2d'); const pr = L.mapProj(-10, 45, 35, 62, 0, 0, 1024, 640); L.drawMap(x, pr, { sea: '#8aa0a8', ru: '#d8c8a0', land: '#e4d6b0', w: 1024, h: 640 }); const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; return t; })();
  L.plate(4.2, 2.6, emap, hl, [2, 2.9, -4.9]); mesh(new THREE.BoxGeometry(4.4, 2.8, .05), mat(0x3a2412, .7), [2, 2.9, -4.95], [0, 0, 0], hl);
  U.dips = []; for (let i = 0; i < 8; i++) { const side = i % 2 ? 1 : -1, x = -3 + Math.floor(i / 2) * 1.9; const m = man({ u: i === 5 ? 'french' : 'suit', seed: 520 + i, rifle: false, hairC: i % 3 === 0 ? 0x9a9a9a : undefined }); at(m, x, 0, side * 1.25, facing([0, -side])); hl.add(m); const c = P.chair(0x5a2a16); at(c, x, 0, side * 1.32, facing([0, -side]) + Math.PI); hl.add(c); U.dips.push(m); }
  U.presenter = man({ u: 'suit', seed: 540, rifle: false, beard: 1, hairC: 0xd8d4cc, height: 1.05, hero: true }); at(U.presenter, 4.4, 0, -3.6, facing([-1, .4])); hl.add(U.presenter); U.ally = man({ u: 'suit', seed: 541, rifle: false, hairC: 0x5a4a3a }); hl.add(U.ally);
  // pince-nez on the professor
  { const h = U.presenter.userData.rig.head, gm = mat(0xc9a24d, .3, .9); for (const s of [-1, 1]) mesh(new THREE.TorusGeometry(.016, .002, 4, 12), gm, [.1, .035, s * .034], [0, Math.PI / 2, 0], h); }
  // ---------- FIELD (dawn): close-ups, parade, firing squad ----------
  const fd = L.addSet('field', 0, -400); L.ground(fd, 'grass'); fd.add(L.forest(300, -300, 300, -260, -60, 71, false)); fd.add(L.forest(200, -300, 300, 60, 260, 72, false));
  U.hero = man({ u: 'legion', seed: 7, height: 1.04, hero: true }); at(U.hero, 0, 0, 0, facing([0, 1])); fd.add(U.hero);
  U.parade = [...Array(15)].map((_, i) => { const m = man({ u: i % 4 === 1 ? 'legionCap' : 'legion', seed: 600 + i }); fd.add(m); return m; });
  U.pflag = L.flag(1.6, 1.0, CZ); U.pfp = L.poleWithFlag(2.6, U.pflag); fd.add(U.pfp);
  U.squad = [...Array(6)].map((_, i) => { const m = man({ u: 'austro', seed: 620 + i }); at(m, 40 + i * 1.1, 0, 0, facing([0, -1])); fd.add(m); return m; });
  U.squadFlash = [...Array(6)].map(() => fx(new THREE.Sprite(new THREE.SpriteMaterial({ map: L.FIRE_T, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }))));
  // ---------- FRONT (night, no man's land) ----------
  const fr = L.addSet('front', 800, 0); L.ground(fr, 'mud');
  for (const z of [0, -62]) { const s1 = L.sandbags(80, 4); s1.position.set(0, 0, z); fr.add(s1); }
  for (const z of [-18, -44]) { const w = L.wireFence(80, -40, { h: 1.2, strands: 4 }); w.position.z = z; fr.add(w); }
  const r = rng(77); for (let i = 0; i < 14; i++) { const c = P.crater(1.5 + r() * 2.5); at(c, -35 + r() * 70, .02, -8 - r() * 48); fr.add(c); } for (let i = 0; i < 9; i++) { const tr = P.deadTree(4 + r() * 5, i); at(tr, -40 + r() * 80, 0, -10 - r() * 60); fr.add(tr); }
  U.scouts = [0, 1, 2].map(i => { const g = prone(man({ u: 'legionCap', seed: 700 + i, rifle: false })); at(g, -2 + i * 1.6, 0, -6, facing([0, -1])); fr.add(g); return g; });
  U.glass = man({ u: 'legionCap', seed: 710, rifle: false, hero: true }); const gl = prone(U.glass); at(gl, 3, 0, -16, facing([0, -1])); fr.add(gl); U.glassG = gl;
  U.bino = new THREE.Group(); for (const s of [-1, 1]) mesh(new THREE.CylinderGeometry(.025, .03, .12, 10), mat(0x1a1a1a, .4, .3), [0, 0, s * .035], [0, 0, Math.PI / 2], U.bino); U.glass.userData.rig.arms[1].hand.add(U.bino); U.bino.position.set(0, -.05, -.1);
  U.sentries = [...Array(4)].map((_, i) => { const m = man({ u: 'austro', seed: 720 + i }); at(m, -12 + i * 8, .6, -63.5, facing([0, 1])); fr.add(m); return m; });
  U.flare = fx(new THREE.Sprite(new THREE.SpriteMaterial({ map: L.SPARK_T, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true })));
  // ---------- CAMP (POWs in snow) ----------
  const cp = L.addSet('camp', -800, 0); L.ground(cp, 'snow'); cp.add(L.forest(200, -300, 300, -250, -60, 81, true));
  for (const [z, x0, len, ry] of [[-22, -30, 60, 0], [22, -30, 26, 0], [22, 4, 26, 0]]) { const w = L.wireFence(len, x0, { h: 2.6 }); w.position.z = z; cp.add(w); }
  for (const s of [-1, 1]) { const w = L.wireFence(44, -22, { h: 2.6 }); w.rotation.y = Math.PI / 2; w.position.x = s * 30; cp.add(w); }
  for (const [x, z] of [[-30, -22], [30, -22], [-30, 22], [30, 22]]) { const t2 = L.tower(); at(t2, x, 0, z); cp.add(t2); }
  for (let i = 0; i < 4; i++) { const b = L.barrack(14, 6); at(b, -20 + (i % 2) * 22, 0, -14 + Math.floor(i / 2) * 0); cp.add(b); } const bb2 = L.barrack(14, 6); at(bb2, 18, 0, -14); cp.add(bb2);
  U.gate = P.gate(8, 3.2); at(U.gate, 0, 0, 22); cp.add(U.gate);
  U.pows = [...Array(24)].map((_, i) => { const m = man({ u: 'pow', seed: 800 + i, rifle: false }); at(m, -7 + (i % 8) * 1.4, 0, -2 + Math.floor(i / 8) * 1.4, facing([0, 1]) + ((i * 7) % 5 - 2) * .05); cp.add(m); return m; });
  U.recruiter = man({ u: 'legion', seed: 840, hero: true }); const crate = await model('wooden_crate_01'); at(crate, 0, 0, 6); cp.add(crate); at(U.recruiter, 0, .62, 6.2, facing([0, -1])); cp.add(U.recruiter);
  U.kepi = fx(new THREE.Group()); mesh(new THREE.CylinderGeometry(.125, .113, .13, 18), mat(0x6a6a64, .9), [0, .065, 0], [0, 0, -.1], U.kepi); mesh(new THREE.CylinderGeometry(.115, .115, .012, 16, 1, false, 0, Math.PI), mat(0x0c0c0c, .3), [.04, 0, 0], [0, 0, -.15], U.kepi);
  U.snowfall = fx(L.snowfall(5000, [70, 30, 70], [-800, 0, 0]));
  U.volunteer = U.pows[11];
  // ---------- TRIBUNAL (Austro-Hungarian court martial) ----------
  const tr = L.addSet('tribunal', 0, 800); const trm = P.room(10, 7, 4.2, { wall: 0x6a6258, panel: 0x2a1a10, floor: 0x4a3a2a }); tr.add(trm);
  const tt = P.longTable(4.4, 1.2); at(tt, 0, 0, -1.6); tr.add(tt); const bf = L.flag(3.2, 2.0, HABS); bf.position.set(-1.6, 3.9, -3.38); tr.add(bf); U.tribF = bf;
  U.judges = [-1.4, 0, 1.4].map((x, i) => { const m = man({ u: 'austro', seed: 900 + i, rifle: false, kit: { coat: 0x5a6268, hatC: 0x4a5258 }, beard: i === 1 ? 1 : undefined, hairC: i === 1 ? 0xb8b4ac : undefined }); at(m, x, 0, -2.5, facing([0, 1])); tr.add(m); const c = P.chair(0x3a1a0a); at(c, x, 0, -2.58, facing([0, 1]) + Math.PI); tr.add(c); return m; });
  const tl3 = P.deskLamp(); at(tl3, 1.9, .82, -1.4); tr.add(tl3); { const pp = P.papers(4, 12); pp.position.set(0, 0, -1.6); tr.add(pp); }
  U.accused = man({ u: 'legion', seed: 910, rifle: false }); at(U.accused, 0, 0, 1.6, facing([0, -1])); tr.add(U.accused); U.tguards = [-1, 1].map((s, i) => { const m = man({ u: 'austro', seed: 912 + i }); at(m, s * 1.0, 0, 2.2, facing([0, -1])); tr.add(m); return m; });
  // ---------- STUDY (Masaryk at work, night) ----------
  const sd = L.addSet('study', 0, -800); const srm = P.room(6, 5, 3.2, { wall: 0x7a6a52 }); sd.add(srm); const dk = P.desk(1.7, .85); at(dk, 0, 0, -1.2); sd.add(dk);
  const sl = P.deskLamp(); at(sl, .6, .79, -1.35); sd.add(sl); U.studyLamp = sl; { const pp = P.papers(8, 4); pp.position.set(-.1, 0, -1.2); sd.add(pp); }
  for (const x of [-2.0, 2.0]) { const b2 = P.bookshelf(1.6, 2.6); at(b2, x, 0, -2.33); sd.add(b2); }
  const sw = P.windowPane(1.2, 1.6, P.nightCity(9, { rain: false })); at(sw, -2.88, 1.8, -.6, Math.PI / 2); sd.add(sw);
  U.mas = man({ u: 'suit', seed: 950, rifle: false, beard: 1, hairC: 0xd8d4cc, height: 1.05, hero: true }); at(U.mas, 0, 0, -.55, facing([0, -1])); sd.add(U.mas); const mc = P.chair(0x4a2412); at(mc, 0, 0, -.45, facing([0, -1]) + Math.PI); sd.add(mc);
  { const h = U.mas.userData.rig.head, gm = mat(0xc9a24d, .3, .9); for (const s of [-1, 1]) mesh(new THREE.TorusGeometry(.016, .002, 4, 12), gm, [.1, .035, s * .034], [0, Math.PI / 2, 0], h); }
  U.pen = new THREE.Group(); mesh(new THREE.CylinderGeometry(.005, .004, .14, 6), mat(0x1a1a1a, .3), [0, 0, 0], [0, 0, 0], U.pen); U.mas.userData.rig.arms[1].hand.add(U.pen); U.pen.position.set(.02, -.03, 0); U.pen.rotation.set(0, 0, .6);
}
// ---------- SHOTS ----------
export const SHOTS = {};
const sq = (t, kiev) => { show('square'); if (kiev) look('day', [0xd8dce0, .006], 1.6, 2.4, 0xfff0dc, [-40, 60, 30], [0, 0, 0]); else look('grey', [0xc0c0bc, .008], 1.5, 1.6, 0xf0ece0, [-40, 60, 30], [0, 0, 0]);
  U.habs.visible = !kiev; U.kiev.visible = kiev; U.poster.visible = !kiev; U.smallP.forEach(p => p.visible = !kiev); U.kposters.forEach(p => p.visible = kiev); U.habsF.forEach(f => f.userData.update(t)); U.kievF.forEach(f => f.userData.update(t)); U.crowd.forEach((m, i) => { m.visible = !kiev; pose(m, t, { look: Math.sin(t * .4 + i) * .2 }); }); };
// 13 mobilization poster in a Bohemian square
SHOTS[13] = (t, lt, d) => { sq(t, false); ct('square', lt, d, [-6.5, 1.75, -2.5, -6.2, 2.2, -11], [-6.3, 2.0, -7.3, -6.2, 2.3, -11], [38, 34]); overlay(c => L.caption(c, '1914', 'BOHEMIA, AUSTRIA-HUNGARY', clamp(lt / .5) * (1 - clamp((lt - d + .5) / .5)))); };
// 14-15 the empire map: Czech lands in the Austrian half, then Slovakia in the Hungarian half
SHOTS[14] = (t, lt, d) => { OV.noGL = true; const mode = t >= ST(15) ? 'slovak' : 'czech'; const l2 = t >= ST(15) ? t - ST(15) : lt; overlay((c, tt) => M.ahMap(c, mode === 'slovak' ? l2 : lt, d, mode, tt)); };
// 16 called to fight for the Habsburgs: column to the train -> chalked wagons -> a young Czech recruit in the door as it pulls out
SHOTS[16] = (t, lt, d) => { show('depot'); look('grey', [0xd0ccc4, .006], 1.5, 1.8, 0xf0e8d8, [-40, 60, 30], [400, 0, 0]); U.dflags.forEach(f => f.userData.update(t));
  const roll = Math.max(0, lt - 5.0); const tx = -30 - roll * roll * .6; U.dtrain.position.x = tx; U.dtrain.userData.update(-tx); U.dsmoke.visible = true; L.smk(U.dsmoke, U.dtrain.userData.loco, U.dtrain.userData.loco.userData.chimney, t);
  U.women.forEach((m, i) => pose(m, t, { armR: lt > 5 ? -2.6 + Math.sin(t * 7 + i) * .4 : -.2, look: .2 }));
  U.column.forEach((m, i) => { const row = Math.floor(i / 3), col = i % 3; const x = -14 + lt * 1.6 - row * 1.3; at(m, x, .6, -5.8 - col * .9, facing([1, 0])); pose(m, t, { walk: true, speed: 6.5 }); m.visible = lt < 5; });
  pose(U.young, t, { look: lt > 5.6 ? -.25 : 0 }); U.dtrain.updateMatrixWorld(true); if (lt > 5) { const hp0 = V3(); U.young.userData.rig.head.getWorldPosition(hp0); pl1.intensity = 5; pl1.position.set(hp0.x, hp0.y + .3, hp0.z - 1.2); } U.youngMates.forEach(m => pose(m, t, {}));
  if (lt < 2.6) { ct('depot', lt, 2.6, [-2, .9, -4.6, -14, 1.9, -7], [-3, .9, -4.8, -15, 1.9, -7], [36, 34]); overlay(c => L.caption(c, 'AUGUST 1914', 'CALLED TO FIGHT FOR THE EMPEROR', clamp(lt / .5) * (1 - clamp((lt - 2.1) / .5)))); return; }
  if (lt < 5.0) { const c3 = V3(); U.dtrain.userData.cars[1].getWorldPosition(c3); camTo(lt - 2.6, 2.4, [c3.x + 4, 2.6, -5.2, c3.x + 2.4, 2.9, 0], [c3.x + 2.5, 2.7, -4.6, c3.x + 2.4, 2.9, 0], [32, 30]); return; }
  const hp = V3(); U.young.userData.rig.head.getWorldPosition(hp); camTo(lt - 5.0, d - 5.0, [hp.x - 1.6, hp.y - .2, hp.z - 4.2, hp.x, hp.y - .35, hp.z], [hp.x - 1.2, hp.y - .15, hp.z - 3.4, hp.x, hp.y - .3, hp.z], [36, 32]); };
// 17 exiles in Paris: rainy night, three men over a newspaper
SHOTS[17] = (t, lt, d) => { show('cafe'); look('night', null, .35, 0, 0xffffff, [0, 60, 0], [-400, 0, 0], [0x8a7060, 0x2a2018]); S.background = new THREE.Color(0x080604);
  U.exiles.forEach((m, i) => pose(m, t, m.userData.p === 'sit' ? { sit: true, armL: .7, armR: .8, elL: .9, elR: 1.0, nod: -.3 } : { lean: .35, nod: -.4, armL: .6, armR: .4 }));
  ct('cafe', lt, d, [2.6, 1.6, 2.6, 0, 1.0, 0], [1.4, 1.45, 1.8, .1, .9, 0], [36, 32]); overlay(c => L.caption(c, 'PARIS', 'CZECH & SLOVAK EXILES', clamp(lt / .5) * (1 - clamp((lt - d + .5) / .5)))); };
// 18 if the empire lost, it might break apart
SHOTS[18] = (t, lt, d) => { OV.noGL = true; overlay((c, tt) => M.ahBreak(c, lt, d, tt)); };
// 19 the victorious powers: Allied diplomats around the long table
SHOTS[19] = (t, lt, d) => { show('hall'); look('night', null, .6, 0, 0xffffff, [0, 60, 0], [0, 0, 400], [0xc0a080, 0x3a2a1a]); S.background = new THREE.Color(0x0a0806); U.hallFlags.forEach(f => f.userData.update(t, .03));
  U.dips.forEach((m, i) => pose(m, t, { sit: true, armL: .8, armR: .8, elL: .9, elR: .9, look: Math.sin(t * .5 + i) * .3 })); pose(U.presenter, t, { point: true, pointUp: .4 }); U.ally.position.y = -50;
  ct('hall', lt, d, [-7, 2.6, 4.2, 1, 1.2, 0], [-2, 1.8, 3.2, 3.5, 1.9, -3], [38, 34]); };
// 20 support would have to be earned: hero close-up at dawn
SHOTS[20] = (t, lt, d) => { show('field'); look('dawn', [0xe8d2b8, .004], 1.3, 2.4, 0xffe0b8, [60, 30, -40], [0, 0, -400]); U.parade.forEach(m => m.position.y = -50); U.squad.forEach(m => m.position.y = -50); U.pfp.position.y = -50;
  pose(U.hero, t, { look: -.1 }); const hp = V3(); U.hero.userData.rig.head.getWorldPosition(hp); camTo(lt, d, [hp.x + .4, hp.y - .25, hp.z + 1.3, hp.x, hp.y, hp.z], [hp.x + .25, hp.y - .2, hp.z + .95, hp.x, hp.y + .02, hp.z], [30, 26]); };
// 21 Kiev: Czech emigrants sign up
SHOTS[21] = (t, lt, d) => { sq(t, true); pose(U.officer, t, { sit: true, armL: .8, armR: .8, elL: 1, elR: 1 }); U.officer.position.y = 0; pose(U.signer, t, { write: true, lean: .45 }); U.queue.forEach((m, i) => pose(m, t, { look: .3 }));
  U.handRifle.position.set(7.5, .86, -6.75); U.handRifle.rotation.set(Math.PI / 2, 0, .15);
  ct('square', lt, d, [12.5, 1.5, -2.5, 7, 1.2, -7], [11.2, 1.45, -3.6, 7.6, 1.1, -7], [36, 32]); overlay(c => L.caption(c, 'KIEV, 1914', 'THE CZECH COMPANY', clamp(lt / .5) * (1 - clamp((lt - d + .5) / .5)))); };
// 22 recon at night: crawling to the wire -> a flare bursts -> binoculars on the enemy line -> from above
SHOTS[22] = (t, lt, d) => { show('front'); const fl = clamp((lt - 1.6) / .3) * (1 - clamp((lt - 6.5) / 1.5)); look('night', [0x0c1220, .008], 1.5 + fl * .5, 1.1, 0x9ab0e8, [-30, 50, -40], [800, 0, 0], [0x8a9aca, 0x3a3a4a]);
  U.scouts.forEach((g, i) => { crawl(g, t * (fl > .5 ? .05 : 1), i); g.position.z = -6 - lt * .5 * (fl > .5 ? .2 : 1) - i * .3; }); crawl(U.glassG, 0, 0); U.glass.userData.rig.arms[1].sh.rotation.z = 2.1; U.glass.userData.rig.arms[1].el.rotation.z = 1.8; U.glass.userData.rig.arms[0].sh.rotation.z = 2.1; U.glass.userData.rig.arms[0].el.rotation.z = 1.8; U.glass.userData.rig.head.rotation.z = 1.2;
  U.sentries.forEach((m, i) => pose(m, t, { look: Math.sin(t * .6 + i) * .5 }));
  if (lt > 1.4) { U.flare.visible = true; const q = lt - 1.4; U.flare.position.set(803, Math.min(24, q * 22) - Math.max(0, q - 1.1) * 1.5, -22); U.flare.scale.setScalar(2.2); pl2.intensity = 90 * fl; pl2.distance = 120; pl2.color.set(0xe8f0d8); pl2.position.copy(U.flare.position); }
  if (lt < 3.2) { ct('front', lt, 3.2, [6, .5, -6.5, -.5, .3, -8.5], [5.5, .6, -8, -.5, .3, -9.5], [36, 34]); return; }
  if (lt < 5.6) { const q = lt - 3.2; ct('front', q, 2.4, [1.6, 2.0, -17.4, 0, 1.3, -62], [1.6, 2.0, -17.4, 0, 1.5, -62], [18, 12]); overlay(c => { if (!U.binoMask) { const m = document.createElement('canvas'); m.width = L.W; m.height = L.H; const x = m.getContext('2d'); x.fillStyle = '#000'; x.fillRect(0, 0, L.W, L.H); x.globalCompositeOperation = 'destination-out'; for (const dx of [-230, 230]) { x.beginPath(); x.arc(L.W / 2 + dx, L.H / 2, 330, 0, 7); x.fill(); } U.binoMask = m; } c.drawImage(U.binoMask, 0, 0); }); return; }
  look('night', [0x0c1220, .006], 2.2, 1.4, 0x9ab0e8, [-30, 50, -40], [800, 0, 0], [0x9aaad8, 0x4a4a5a]); ct('front', lt - 5.6, d - 5.6, [6, 3.2, -3, 0, .3, -9], [7, 4.5, -2.4, 0, .3, -10], [36, 38]); };
// 23 POW camp: aerial over the wire -> a legionary recruits from a crate
SHOTS[23] = (t, lt, d) => { show('camp'); look('snow', [0xd8dce4, .008], 1.5, 1.6, 0xf0f0f4, [-40, 60, 30], [-800, 0, 0], [0xdde4f0, 0x8a8a96]); U.snowfall.visible = true; U.snowfall.userData.update(t);
  U.pows.forEach((m, i) => pose(m, t, { look: Math.sin(t * .4 + i) * .2 })); pose(U.recruiter, t, { point: true, pointUp: .2 + Math.sin(t * 2) * .1, look: Math.sin(t * .8) * .3 });
  if (lt < 2.6) { ct('camp', lt, 2.6, [0, 14, 40, 0, 2, 0], [0, 9, 26, 0, 1, 2], [40, 36]); overlay(c => L.caption(c, 'RUSSIA, 1915', 'CAMP FOR AUSTRO-HUNGARIAN PRISONERS', clamp(lt / .5) * (1 - clamp((lt - 2.1) / .5)))); return; }
  ct('camp', lt - 2.6, d - 2.6, [-4, 1.6, -4.5, 0, 2.2, 6], [-3.2, 1.5, -3.9, 0, 2.3, 6], [34, 30]); };
// 24 one prisoner steps forward; his Austrian cap drops into the snow
SHOTS[24] = (t, lt, d) => { show('camp'); look('snow', [0xd8dce4, .008], 1.5, 1.6, 0xf0f0f4, [-40, 60, 30], [-800, 0, 0], [0xdde4f0, 0x8a8a96]); U.snowfall.visible = true; U.snowfall.userData.update(t);
  U.pows.forEach((m, i) => { if (m !== U.volunteer) pose(m, t, { look: .2 }); }); pose(U.recruiter, t, {});
  const v = U.volunteer, k = clamp((lt - .4) / 1.6); at(v, -7 + 3 * 1.4, 0, -.6 + k * 2.4, facing([0, 1])); pose(v, t, { walk: k > 0 && k < 1, speed: 5, armR: lt > 2.4 ? lerp(0, 2.0, clamp((lt - 2.4) / .4)) : 0, elR: lt > 2.4 ? 1.2 : 0 });
  const vp = V3(); v.getWorldPosition(vp);
  if (lt < 2.4) { camTo(lt, 2.4, [vp.x - 2.6, 1.4, 7.0, vp.x, 1.6, vp.z], [vp.x - 2.0, 1.5, 6.0, vp.x, 1.6, vp.z], [34, 30]); return; }
  const q = lt - 2.4, fall = clamp((q - .5) / .7); U.kepi.visible = true; U.kepi.position.set(vp.x + .35 + fall * .15, lerp(1.45, .005, ease(fall)), vp.z + .3 + fall * .45); U.kepi.rotation.set(Math.sin(fall * Math.PI) * .9, fall * 1.3, Math.sin(fall * Math.PI) * .5);
  camTo(q, d - 2.4, [vp.x + 1.0, .3, vp.z + 1.2, vp.x + .35, .35, vp.z + .5], [vp.x + .9, .22, vp.z + 1.1, vp.x + .4, .15, vp.z + .6], [36, 34]); };
// 25 the camp gate opens: volunteers march out
SHOTS[25] = (t, lt, d) => { show('camp'); look('snow', [0xd8dce4, .008], 1.5, 1.6, 0xf0f0f4, [-40, 60, 30], [-800, 0, 0], [0xdde4f0, 0x8a8a96]); U.snowfall.visible = true; U.snowfall.userData.update(t);
  const op = ease(clamp(lt / 1.2)); U.gate.userData.leaves[0].rotation.y = -op * 1.6; U.gate.userData.leaves[1].rotation.y = op * 1.6;
  U.pows.forEach((m, i) => { const row = Math.floor(i / 3), col = i % 3, k = lt - .8 - row * .35; at(m, -1.2 + col * 1.2, 0, 16 + k * 1.4, facing([0, 1])); pose(m, t, { walk: k > 0, speed: 6 }); if (k < 0) m.position.z = 16; });
  U.recruiter.position.y = -50; ct('camp', lt, d, [3, .6, 32, 0, 2, 18], [2.4, .7, 30.5, 0, 2.2, 18], [36, 34]); };
// 26 court martial: treason
SHOTS[26] = (t, lt, d) => { show('tribunal'); look('night', null, .45, 0, 0xffffff, [0, 60, 0], [0, 0, 800], [0x9a8a70, 0x2a2018]); S.background = new THREE.Color(0x050403); U.tribF.userData.update(t, .02);
  U.judges.forEach((m, i) => pose(m, t, { sit: true, armL: .7, armR: .7, elL: 1, elR: 1, look: (i - 1) * -.2 })); pose(U.accused, t, { nod: .1 }); U.tguards.forEach(m => pose(m, t, {}));
  if (lt < 2.2) { ct('tribunal', lt, 2.2, [0, 1.7, 4.8, 0, 1.6, -2], [0, 1.6, 3.6, 0, 1.5, -2], [34, 30]); return; }
  ct('tribunal', 2.2, 2.2, [0, 1.6, 3.6, 0, 1.5, -2], [0, 1.6, 3.6, 0, 1.5, -2], [30, 30]); overlay(c => { c.fillStyle = 'rgba(0,0,0,.55)'; c.fillRect(0, 0, L.W, L.H); M.documentPage(c, lt - 2.2, [['K.u.K. FELDGERICHT', 34, true], [''], ['Angeklagter: Überläufer zum Feind', 28], ['Urteil: Tod durch den Strang', 28], [''], ['MILITARY COURT · DESERTER TO THE ENEMY', 22]], { stamp: [.9, 'HOCHVERRAT', 120, 170], cps: 60 }); }); };
// 27 capture could mean execution: rifles rise against a red dawn
SHOTS[27] = (t, lt, d) => { show('field'); look('red', [0x8a4a3a, .01], .35, .6, 0xff9060, [0, 10, -80], [0, 0, -400], [0x6a4a5a, 0x1a1012]); U.parade.forEach(m => m.position.y = -50); U.hero.position.y = -50; U.pfp.position.y = -50;
  const aim = lt > .5; U.squad.forEach((m, i) => { at(m, -3 + i * 1.15, 0, 0, facing([0, -1])); pose(m, t, { aim }); });
  if (lt > 1.15 && lt < 1.27) { U.squad.forEach((m, i) => { const f = U.squadFlash[i]; f.visible = true; const mp = V3(); m.userData.rifle.localToWorld(mp.set(.6, .03, 0)); f.position.copy(mp); f.scale.setScalar(1.2); }); pl2.intensity = 30; pl2.position.set(0, 1.6, -401.5); }
  ct('field', lt, d, [5, .9, 5, -1, 1.5, -6], [4.6, .9, 4.6, -1, 1.5, -6], [34, 34]); if (lt > d - .35) OV.fade = (lt - d + .35) / .35; };
// 28 Masaryk at work by lamplight
SHOTS[28] = (t, lt, d) => { show('study'); look('night', null, .35, 0, 0xffffff, [0, 60, 0], [0, 0, -800], [0x8a7060, 0x2a2018]); S.background = new THREE.Color(0x060403);
  pose(U.mas, t, { sit: true, write: true, nod: -.35 }); U.mas.position.y = 0;
  ct('study', lt, d, [1.6, 1.5, 1.4, 0, 1.0, -1.1], [.8, 1.3, .6, 0, 1.0, -1.1], [36, 30]); overlay(c => L.caption(c, 'TOMÁŠ GARRIGUE MASARYK', 'LEADER OF THE INDEPENDENCE MOVEMENT', clamp((lt - .6) / .5) * (1 - clamp((lt - d + .5) / .5)))); };
// 29 his journeys to win the Allies -> the handshake
SHOTS[29] = (t, lt, d) => {
  if (lt < 3.8) { OV.noGL = true; overlay((c, tt) => { const pr = M.proj(-85, 150, 15, 68); M.paper(c); M.baseLand(c, pr, { land: '#b8a888' }); M.routeStops(c, pr, [[14.4, 50.1, 'PRAGUE'], [12.5, 41.9, 'ROME'], [6.1, 46.2, 'GENEVA'], [-0.1, 51.5, 'LONDON'], [30.3, 59.9, 'PETROGRAD'], [30.5, 50.4, 'KIEV'], [131.9, 43.1, 'VLADIVOSTOK'], [139.7, 35.7, 'TOKYO'], [-77.0, 38.9, 'WASHINGTON']], ease(clamp(lt / 3.4)), tt, { size: 20, head: true }); M.vignette(c); M.title(c, 'MASARYK ABROAD', '1914 - 1918', clamp(lt / .5)); }); return; }
  show('hall'); look('night', null, .6, 0, 0xffffff, [0, 60, 0], [0, 0, 400], [0xc0a080, 0x3a2a1a]); S.background = new THREE.Color(0x0a0806); U.hallFlags.forEach(f => f.userData.update(t, .03));
  const q = lt - 3.8, k = clamp(q / 1.0); U.dips.forEach((m, i) => pose(m, t, { sit: true, armL: .8, armR: .8, elL: .9, elR: .9 }));
  at(U.presenter, -5.05, 0, -2.2, facing([1, 0])); at(U.ally, -4.05, 0, -1.76, facing([-1, 0])); pose(U.presenter, t, { armR: lerp(0, 1.1, k), elR: .3 }); pose(U.ally, t, { armR: lerp(0, 1.1, k), elR: .3 }); const shake = q > 1 ? Math.sin(q * 12) * .06 : 0; U.presenter.userData.rig.arms[1].sh.rotation.z += shake; U.ally.userData.rig.arms[1].sh.rotation.z -= shake;
  ct('hall', q, d - 3.8, [-4.55, 1.3, -.4, -4.55, 1.2, -2.2], [-4.55, 1.35, -.9, -4.55, 1.25, -2.2], [40, 34]); };
// 30 an army on their side: legionaries march at the camera under the white-red flag
SHOTS[30] = (t, lt, d) => { show('field'); look('dawn', [0xe8d2b8, .004], 1.3, 2.4, 0xffe0b8, [60, 30, -40], [0, 0, -400]); U.hero.position.y = -50; U.squad.forEach(m => m.position.y = -50);
  U.parade.forEach((m, i) => { const row = Math.floor(i / 3), col = i % 3; at(m, -1.1 + col * 1.1, 0, -9.5 + lt * 1.5 - row * 1.4, facing([0, 1])); pose(m, t, { walk: true, speed: 6.5 }); });
  { const m0 = U.parade[0]; pose(m0, t, { walk: true, speed: 6.5, flag: true }); U.pfp.position.set(m0.position.x - .32, .55, m0.position.z + .22); } U.pflag.userData.update(t, .3);
  ct('field', lt, d, [1.2, .35, 0, -.5, 2.2, -12], [1.6, .3, -1, -.5, 2.6, -12], [36, 34]); };
// 31 every success made headlines
SHOTS[31] = (t, lt, d) => { show('study'); look('night', null, .35, 0, 0xffffff, [0, 60, 0], [0, 0, -800], [0x8a7060, 0x2a2018]); S.background = new THREE.Color(0x060403); pose(U.mas, t, { sit: true, armL: .7, armR: .7, elL: 1, elR: 1, nod: -.2 });
  ct('study', lt, d, [0, 2.4, .2, 0, .8, -1.2], [0, 2.3, -.2, 0, .8, -1.2], [36, 36]);
  overlay(c => { c.fillStyle = 'rgba(0,0,0,.45)'; c.fillRect(0, 0, L.W, L.H); const H3 = [[0, ['CZECH SCOUTS', 'PRAISED'], 'Volunteers serve with the Russian army', -330, -.08], [1.6, ['LES TCHÉCO-', 'SLOVAQUES'], 'combattent aux côtés des Alliés', 0, .05], [3.2, ['A NATION', 'IN ARMS'], 'Masaryk wins support in London', 330, -.03]];
    H3.forEach(([t0, h, s, dx, tilt]) => { if (lt > t0) M.newspaper(c, lt - t0, h, s, { dx, tilt, scale: .55, date: '1916', paper: ['THE TIMES', 'LE PETIT PARISIEN', 'DAILY CHRONICLE'][Math.round(t0 / 1.6)] }); }); }); };
