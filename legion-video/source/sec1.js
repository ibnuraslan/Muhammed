// ===================== SECTION 1: Chelyabinsk, May 1918 (cues 0-12) =====================
import * as L from './lib3.js';
const { THREE, S, cam, U, SKY, V3, at, mesh, mat, pbr, model, clamp, lerp, ease, rng, pl1, pl2, pl3, look, camTo, smk, show, fx, overlay, OV, pose, facing, man } = L;
export const RANGE = { from: 0, to: 12, fadeIn: .5 };
let C; const T = i => C[i].start;
// ---- POW train motion: enters at t=1.7 at 14 m/s, brakes to a stop at t=17 ----
const V0 = 14, DEC = .915, TA = 1.7, X0 = 160, TSTOP = TA + V0 / DEC;
function powD(t) { if (t < TA) return -(TA - t) * V0; const tt = Math.min(t, TSTOP) - TA; return V0 * tt - .5 * DEC * tt * tt; }
const powX = t => X0 - powD(t);
const carX = (k, t) => { U.pow.position.x = powX(t); U.pow.updateMatrixWorld(true); const v = V3(); U.pow.userData.cars[k].getWorldPosition(v); return v; };
const T_THROW = 10.4, T_HIT = 12.45;
export async function build(cues) {
  C = cues;
  SKY.dawn = L.paintSky('#6c8ac0', '#f2cfa0', '#fff2d8', '#f0c8b4', '#a898b4', 3, { sun: [1250, 760] });
  SKY.grey = L.paintSky('#8e98a6', '#cfcec6', '#e8e6e0', '#bdbdc2', '#8d929e', 7);
  SKY.dusk = L.paintSky('#3e4474', '#f2a868', '#ffd8a0', '#d89a8a', '#7a6a8a', 9, { sun: [700, 820] });
  SKY.night = L.paintSky('#0a1228', '#28344e', '#4a5a7e', '#323e5c', '#1e263c', 11, { stars: true });
  SKY.snowdusk = L.paintSky('#4a5a86', '#e8b898', '#ffe0c8', '#d0b0b0', '#8a8aa8', 13, { sun: [1400, 800] });
  // ---------- STATION ----------
  const st = L.addSet('station', 0, 0); L.ground(st, 'dirt');
  for (const z of [6, 0, -5.5]) { const tr = L.track2(900, -450); tr.position.z = z; st.add(tr); }
  const bld = L.station('ЧЕЛЯБИНСК'); at(bld, 2, .6, -15.5); st.add(bld); for (const x of [-40, 44, 80]) { const b2 = L.station('', { wallTint: 0xd0c0a0 }); b2.scale.set(.6, .8, .7); at(b2, x, .6, -16); st.add(b2); }
  mesh(new THREE.BoxGeometry(150, .6, 6.2), pbr('old_wood_floor', [40, 2], { color: 0x9a8a78 }), [20, .3, -10.4], [0, 0, 0], st);
  st.add(L.forest(160, -450, 450, -160, -45, 3, false)); st.add(L.forest(160, -450, 450, 40, 180, 5, false));
  for (const x of [-22, -10, 2, 14, 26, 40, 54, 68]) { const l = await model('street_lamp_01'); at(l, x, .6, -7.9); st.add(l); }
  for (const [n, x, z, r2] of [['wooden_crate_01', 16, -9.1, .3], ['wooden_crate_02', 17.1, -9.6, -.2], ['wooden_barrels_01', -13, -11.8, .4], ['old_military_crate', -6, -9, .1], ['painted_wooden_bench', 6, -12.6, 0], ['wooden_crate_01', 47, -12.2, .6]]) { const m = await model(n); at(m, x, .6, z, r2); st.add(m); }
  U.ech1 = L.train(7, { openIdx: [1, 3, 5] }); at(U.ech1, -6, 0, 0); st.add(U.ech1);
  U.ech2 = L.train(8, { openIdx: [2] }); at(U.ech2, 20, 0, 6); st.add(U.ech2);
  const fl = L.flag(1.6, 1.0, ['#f2f0ea', '#c8241c']); const fp = L.poleWithFlag(2.2, fl); const c1 = U.ech1.userData.cars[1]; fp.position.set(c1.position.x + 2.6, c1.userData.by0 + 2.9, .9); U.ech1.add(fp); U.flags = [fl];
  U.pow = L.train(6, { openIdx: [0, 1, 2, 3, 4] }); U.pow.rotation.y = Math.PI; U.pow.position.z = -5.5; st.add(U.pow);
  U.powMen = []; U.pow.userData.cars.forEach((car, ci) => { for (let k = 0; k < 3; k++) { const m = man({ u: 'pow', seed: 100 + ci * 5 + k, rifle: false }); at(m, -.55 + k * .55, car.userData.by0, 1.58 - (k % 2) * .06, -Math.PI / 2 + (k - 1) * .25); m.userData.home = m.position.clone(); car.add(m); U.powMen.push(m); } });
  U.thrower = U.powMen[3 + 1];
  // where the iron lands: in front of car 1's door at the moment of impact
  const hit = carX(1, T_HIT); U.VX = hit.x - 2.2;
  const r = rng(4); U.men = []; for (let i = 0; i < 26; i++) { const x = -20 + i * 4.3 + r() * 1.2; if (Math.abs(x - U.VX) < 2.2) continue; const m = man({ u: i % 4 === 3 ? 'legionCap' : 'legion', seed: i + 1 }); at(m, x, .6, -8.8 - r() * 2.4, facing([0, 1]) + (r() - .5) * .8); st.add(m); U.men.push(m); }
  const cx3 = carX(3, 6.0).x; U.cluster = [0, 1, 2, 3].map(i => { const m = man({ u: i % 2 ? 'legionCap' : 'legion', seed: 70 + i }); at(m, cx3 - 3 + i * 1.3, .6, -9.0 - (i % 2) * .6, facing([0, 1])); st.add(m); return m; }); U.cx3 = cx3;
  U.victim = man({ u: 'legion', seed: 41 }); at(U.victim, U.VX, .6, -8.3, facing([0, 1])); st.add(U.victim);
  U.runners = [0, 1, 2, 3].map(i => { const m = man({ u: i % 2 ? 'legionCap' : 'legion', seed: 60 + i }); st.add(m); return m; });
  U.iron = fx(mesh(new THREE.BoxGeometry(.5, .07, .07), pbr('rusty_metal', [1, .2], { color: 0x8a6a5a })));
  U.cap = fx(L.capMesh()); U.cap2 = fx(L.capMesh());
  U.sparks = fx(L.sparks(80));
  U.smokeA = fx(L.smoke(V3(), { n: 60, color: 0x58585e, wind: [.4, .2], rise: 14, size: 1.4, grow: 5, life: 6, opacity: .9 }));
  U.smokeB = fx(L.smoke(V3(), { n: 50, color: 0x6a6a70, wind: [.3, .1], rise: 14, size: 1.3, grow: 5, life: 7, opacity: .85 }));
  U.steam = fx(L.smoke(V3(), { n: 60, color: 0xf4f4f6, wind: [.6, -1], rise: 2.5, size: 1.4, grow: 5, life: 3, opacity: .85 }));
  U.powSmoke = fx(L.smoke(V3(), { n: 70, color: 0x4a4a50, wind: [3, .3], rise: 10, size: 1.3, grow: 5, life: 5, opacity: .9 }));
  U.handRifle = fx(new THREE.Group()); const hr = L.RIFLE.clone(true); U.handRifle.add(hr); const h1 = L.hand(1.0); h1.position.set(-.05, .02, .05); h1.rotation.set(0, 0, Math.PI / 2 + .2); U.handRifle.add(h1); U.hand1 = h1;
  U.flash = fx(new THREE.Sprite(new THREE.SpriteMaterial({ map: L.FIRE_T, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true })));
  // ---------- TOWN SQUARE + SOVIET HQ ----------
  const town = L.addSet('town', 0, 500); L.ground(town, 'cobble');
  const hq = L.station('СОВЕТ', { wallTint: 0xc8b89a }); at(hq, 0, 0, -10); town.add(hq);           // facade at z=-6, door at x=0
  U.banners = [-6, 6].map(x => { const b = L.flag(1.6, 3.0, ['#b81a14']); b.position.set(x - .8, 5.7, -5.7); town.add(b); return b; });  // hangs flat on the wall between windows
  for (const [x, s2] of [[-26, 'ЛАВКА'], [26, 'ПОЧТА'], [-50, ''], [50, '']]) { const b = L.station(s2, { wallTint: 0xd8c8a8 }); b.scale.set(.6, .8, .7); at(b, x, 0, -12); town.add(b); }
  for (const [x, z] of [[-34, 14], [-14, 16], [8, 15], [30, 14]]) { const h = L.house(10, 7, 8, { color: [0xcab89a, 0xb8a888, 0xd2c2a2, 0xc0b090][(x + 40) % 4 | 0] }); at(h, x, 0, z, Math.PI); town.add(h); }
  // real hinged door (hinge on the left edge)
  U.door = new THREE.Group(); U.door.position.set(-1.0, 0, -5.9); town.add(U.door);
  U.doorPanel = mesh(new THREE.BoxGeometry(2.0, 3.2, .12), pbr('brown_planks_05', [1, 2], { color: 0x6a3a22 }), [1.0, 1.6, 0], [0, 0, 0], U.door); mesh(new THREE.BoxGeometry(.18, .3, .04), mat(0xb8903a, .35, .9), [1.75, 1.3, .08], [0, 0, 0], U.door);
  for (const y of [.6, 2.6]) mesh(new THREE.BoxGeometry(2.0, .12, .05), mat(0x2a1a10, .6), [1.0, y, .07], [0, 0, 0], U.door);
  U.splinters = fx(new THREE.Group()); for (let i = 0; i < 14; i++) mesh(new THREE.BoxGeometry(.05 + (i % 3) * .04, .3 + (i % 4) * .1, .03), mat(0x7a4a2a, .8), [0, 0, 0], [0, 0, 0], U.splinters);
  U.guards = [...Array(6)].map((_, i) => man({ u: 'red', seed: 81 + i, RIFLE: L.lowRifle(true) })); U.guards.forEach(m => town.add(m));
  U.arrested = [0, 1, 2].map(i => man({ u: i === 1 ? 'legionCap' : 'legion', seed: 85 + i, rifle: false })); U.arrested.forEach(m => town.add(m));
  U.raid = [...Array(8)].map((_, i) => man({ u: i % 3 === 2 ? 'legionCap' : 'legion', seed: 90 + i })); U.raid.forEach(m => town.add(m));
  U.lanterns = [0, 1, 2].map(() => { const l = new THREE.PointLight(0xffb050, 0, 9, 1.6); town.add(l); const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: L.FIRE_T, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true })); s.scale.setScalar(.5); l.add(s); return l; });
  // ---------- WAR LINE: armored train + burning station ----------
  const war = L.addSet('war', 0, -600); L.ground(war, 'dirt');
  war.add(L.track2(900, -450)); war.add(L.forest(160, -450, 450, -200, -50, 21, false)); war.add(L.forest(120, -450, 450, 30, 200, 22, false));
  U.arm = L.train(2, { kinds: ['armor', 'flat'], front: 'armor', color: 0x3a4038 }); war.add(U.arm);   // armored wagon pushed ahead of the loco (real practice) + flatcar behind
  const flat = U.arm.userData.cars[1]; U.onTrain = [...Array(6)].map((_, i) => { const m = man({ u: i % 3 === 1 ? 'legionCap' : 'legion', seed: i === 3 ? 7 : 170 + i, height: i === 3 ? 1.04 : undefined, hero: i === 3 }); at(m, -2.8 + i * 1.1, flat.userData.deck, (i % 2 ? .45 : -.35), facing([0, 1]) + (i % 2 ? -.3 : .3)); flat.add(m); return m; });
  U.heroFlagCloth = L.flag(1.2, .75, ['#f2f0ea', '#c8241c']); U.heroFlag = L.poleWithFlag(2.4, U.heroFlagCloth); U.heroFlag.position.set(U.onTrain[3].position.x + .7, flat.userData.deck, -.9); flat.add(U.heroFlag);
  const bst = L.station('КУРГАН', { wallTint: 0xb8a888 }); at(bst, 40, 0, -14); war.add(bst);
  U.bfires = [[30, -10], [38, -12], [46, -10], [52, -13], [42, -16]].map(([x, z]) => { const f = L.fire(16, 4.5); f.position.set(x, 1, z); war.add(f); return f; });
  U.bsmoke = fx(L.smoke(V3(), { n: 60, color: 0x221c1c, wind: [1.5, .5], rise: 30, size: 5, grow: 4, life: 7, opacity: .95 }));
  U.cannonFlash = fx(new THREE.Sprite(new THREE.SpriteMaterial({ map: L.FIRE_T, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true })));
  U.cannonSmoke = fx(L.smoke(V3(), { n: 30, color: 0x9a9690, wind: [3, 0], rise: 2, size: 1.5, grow: 6, life: 2, opacity: .9 }));
  U.armSmoke = fx(L.smoke(V3(), { n: 60, color: 0x4a4a50, wind: [-4, .3], rise: 9, size: 1.3, grow: 5, life: 5, opacity: .9 }));
  // ---------- PLAIN (aerial) ----------
  const plain = L.addSet('plain', 0, -2600); L.ground(plain, 'grass', 8000);
  plain.add(L.track2(2400, -1200)); plain.add(L.forest(3000, -1200, 1200, -500, -25, 41, false)); plain.add(L.forest(3000, -1200, 1200, 25, 500, 42, false));
  U.plainTrain = L.train(12, {}); plain.add(U.plainTrain); U.smokeC = fx(L.smoke(V3(), { n: 90, color: 0x4a4a50, wind: [-8, .5], rise: 10, size: 2, grow: 6, life: 7, opacity: .85 }));
  // ---------- CITY (Samara) ----------
  const city = L.addSet('city', 600, 0); L.ground(city, 'dirt');
  city.add(L.track2(700, -350)); const cst = L.station('САМАРА', { wallTint: 0xd8c4a0 }); at(cst, 0, .6, -15.5); city.add(cst); mesh(new THREE.BoxGeometry(70, .6, 6.2), pbr('old_wood_floor', [20, 2], { color: 0x9a8a78 }), [0, .3, -10.4], [0, 0, 0], city);
  for (const [x, z] of [[-34, -28], [34, -26], [-52, -14], [54, -16]]) { const b = L.house(14, 12, 10, { color: 0xc8b898 }); at(b, x, 0, z, (x > 0 ? -1 : 1) * .4); city.add(b); }
  // flagpole on the platform in front of the station, with halyard
  const cp = new THREE.Group(); mesh(new THREE.CylinderGeometry(.06, .08, 9, 10), mat(0x3a2a1e, .8), [0, 4.5, 0], [0, 0, 0], cp); mesh(new THREE.SphereGeometry(.12, 10, 8), mat(0xc9a24d, .3, .9), [0, 9.05, 0], [0, 0, 0], cp); mesh(new THREE.CylinderGeometry(.008, .008, 9, 4), mat(0xd8d0c0, .8), [.09, 4.5, 0], [0, 0, 0], cp);
  U.redF = L.flag(2.2, 1.4, ['#b81a14']); U.czF = L.flag(2.2, 1.4, ['#f2f0ea', '#c8241c']); cp.add(U.redF); cp.add(U.czF); at(cp, 6, .6, -9.0); city.add(cp); U.cpole = cp;
  U.carm = L.train(2, { kinds: ['armor', 'flat'], color: 0x3a4038 }); U.carm.rotation.y = Math.PI; city.add(U.carm);   // loco leads westward
  U.chargers = [...Array(8)].map((_, i) => man({ u: i % 3 === 1 ? 'legionCap' : 'legion', seed: 120 + i })); U.chargers.forEach(m => city.add(m));
  U.hoister = man({ u: 'legion', seed: 133, rifle: false }); city.add(U.hoister);
  U.crowd = [...Array(16)].map((_, i) => { const m = man({ u: 'civil', seed: 140 + i, rifle: false }); at(m, -14 + i * 1.9, .6, -11.8 - (i % 3) * .8, facing([0, 1])); city.add(m); return m; });
  U.citySmoke = [[-40, -40], [30, -60], [70, -30]].map(([x, z]) => ({ s: fx(L.smoke(V3(), { n: 45, color: 0x2e2828, wind: [3, 1], rise: 35, size: 5, grow: 5, life: 8, opacity: .9 })), x: x + 600, z }));
  // ---------- BOXCAR INTERIOR (night) ----------
  const inn = L.addSet('inn', 0, 1500);
  const pl = pbr('brown_planks_05', [3, 1], { color: 0x8a5236 }), plD = pbr('old_wood_floor', [3, 1], { color: 0x6a4a34 });
  const P = (w, h, x, y, z, ry = 0, rx = 0, m = pl) => mesh(new THREE.PlaneGeometry(w, h), Object.assign(m.clone(), { side: THREE.DoubleSide }), [x, y, z], [rx, ry, 0], inn);
  P(7.4, 2.7, 0, 1.35, -1.37); P(7.4, 2.7, 0, 1.35, 1.37); P(2.75, 2.7, -3.7, 1.35, 0, Math.PI / 2); P(2.75, 2.7, 3.7, 1.35, 0, Math.PI / 2); P(7.4, 2.75, 0, 0, 0, 0, -Math.PI / 2, plD); P(7.4, 2.75, 0, 2.7, 0, 0, Math.PI / 2, plD);
  for (const x of [-2.6, 2.6]) for (const y of [.55, 1.6]) { mesh(new THREE.BoxGeometry(2.0, .08, 2.7), plD, [x, y, 0], [0, 0, 0], inn); mesh(new THREE.BoxGeometry(1.8, .12, 2.3), mat(0x6a6a5a, 1), [x, y + .1, 0], [0, 0, 0], inn); }
  const stove = await model('barrel_stove'); at(stove, 0, 0, -.9); inn.add(stove); U.stoveFire = L.fire(8, .5); U.stoveFire.position.set(0, .5, -.5); inn.add(U.stoveFire);
  const lamp = await model('vintage_oil_lamp'); U.lamp = new THREE.Group(); U.lamp.add(lamp); lamp.position.y = -.35; U.lamp.position.set(.8, 2.55, .2); inn.add(U.lamp);
  U.sleepers = [[-2.6, .75, .3, 0], [2.6, .75, -.2, Math.PI], [-2.6, 1.8, 0, 0]].map(([x, y, z, ry], i) => { const m = man({ u: 'legion', seed: 160 + i, rifle: false }); m.rotation.set(0, ry, -Math.PI / 2); m.position.set(x + (ry ? .8 : -.8), y + .15, z); inn.add(m); return m; });
  // hero sits on the lower bunk edge holding the map in both hands
  U.reader = man({ u: 'legion', seed: 7, height: 1.04, rifle: false, hero: true }); at(U.reader, 1.05, 0, .3, facing([-1, 0])); inn.add(U.reader); mesh(new THREE.BoxGeometry(.5, .5, .5), pbr('brown_planks_05', [1, 1], { color: 0x7a5a3a }), [1.15, .25, .3], [0, 0, 0], inn);
  U.mapTex = (() => { const cv = document.createElement('canvas'); cv.width = 1024; cv.height = 700; const x = cv.getContext('2d'); const pr = L.mapProj(0, 40, 40, 58, 0, 0, 1024, 700); L.drawMap(x, pr, { sea: '#9aa8a8', ru: '#e0d0a8', land: '#e0d0a8', w: 1024, h: 700, noBorders: true }); x.fillStyle = 'rgba(240,220,170,.35)'; x.fillRect(0, 0, 1024, 700);
    const [bx, by] = pr(15.5, 49.6); x.strokeStyle = '#7a1a14'; x.lineWidth = 5; x.setLineDash([12, 8]); x.beginPath(); x.ellipse(bx, by, 120, 60, -.1, 0, 7); x.stroke(); x.setLineDash([]); x.fillStyle = '#7a1a14'; x.font = 'bold 120px DejaVu Serif, serif'; x.textAlign = 'center'; x.fillText('?', bx, by + 42);
    const g = x.createRadialGradient(512, 350, 200, 512, 350, 620); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(90,60,30,.5)'); x.fillStyle = g; x.fillRect(0, 0, 1024, 700); const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; U.mapPin = [bx / 1024, by / 700]; return t; })();
  U.map = mesh(new THREE.PlaneGeometry(.62, .42, 8, 4), new THREE.MeshToonMaterial({ map: U.mapTex, side: THREE.DoubleSide, gradientMap: L.GRAD }), [0, 0, 0], [0, 0, 0], inn); U.map.userData.noToon = true;
  U.finger = fx(L.hand(.2));
  // ---------- SNOW DUSK (stranded) ----------
  const sn = L.addSet('snow', -1500, 0); L.ground(sn, 'snow'); sn.add(L.track2(800, -400)); sn.add(L.forest(300, -400, 400, -220, -30, 51, true)); sn.add(L.forest(300, -400, 400, 30, 220, 52, true));
  U.loner = man({ u: 'legion', seed: 7, height: 1.04, hero: true }); at(U.loner, 0, 0, -2.6, Math.PI / 2 + .2); sn.add(U.loner); U.snowS = fx(L.snowfall(6000, [70, 30, 60], [-1500, 0, 0]));
  for (let i = 0; i < 7; i++) { const c = L.cross(1.3 + (i % 3) * .1); at(c, -14 - i * 3.2, 0, -5.5 - (i % 2) * .4, (i % 3 - 1) * .08); c.rotation.z = (i % 4 - 1.5) * .04; sn.add(c); }
}
// ---------- shared station state ----------
function stationBase(t) { show('station'); look('dawn', [0xe8d2b8, .0022], 1.6, 2.3, 0xffe0b8, [60, 40, -30], [0, 0, -6]);
  U.pow.position.x = powX(t); U.pow.userData.update(powD(t)); U.ech1.userData.update(0); U.ech2.userData.update(0);
  U.smokeA.visible = U.smokeB.visible = U.steam.visible = U.powSmoke.visible = true; smk(U.smokeA, U.ech1.userData.loco, U.ech1.userData.loco.userData.chimney, t); smk(U.smokeB, U.ech2.userData.loco, U.ech2.userData.loco.userData.chimney, t); smk(U.steam, U.pow.userData.loco, U.pow.userData.loco.userData.cylinder, t); smk(U.powSmoke, U.pow.userData.loco, U.pow.userData.loco.userData.chimney, t);
  U.men.forEach((m, i) => pose(m, t, { look: Math.sin(t * .3 + i) * .4 })); U.powMen.forEach(m => { m.position.copy(m.userData.home); pose(m, t, { look: .4 }); }); pose(U.victim, t, {}); U.victim.rotation.set(0, facing([0, 1]), 0); U.victim.position.set(U.VX, .6, -8.3); U.flags.forEach(f => f.userData.update(t));
  U.runners.forEach((m, i) => { at(m, U.VX - 30 - i * 2, .6, -8.6, 0); pose(m, t, {}); }); }
const doorWorld = (k, t) => { const v = carX(k, t); v.z = -5.5 - 1.5; v.y = U.pow.userData.cars[k].userData.by0 + 1.3; return v; };
// ---------- SHOTS ----------
export const SHOTS = {};
// 0 extreme wide at dawn over the packed station
SHOTS[0] = (t, lt, d) => { stationBase(t); camTo(lt, d, [80, 46, 70, -10, 0, -8], [70, 38, 60, -6, 2, -8], [40, 38]); overlay(c => L.caption(c, 'MAY 1918', 'CHELYABINSK, RUSSIA', clamp((lt + .4) / .5))); };
// 1 the POW train: between the rails (kept as is) -> doors flick past -> legionaries stare -> hand on rifle
SHOTS[1] = (t, lt, d) => { stationBase(t);
  if (L.U.pow && lt < 2.8) { overlay(c => L.caption(c, 'MAY 1918', 'CHELYABINSK, RUSSIA', 1 - clamp((lt - 1.8) / .5))); U.pow.position.x = lerp(120, 0, lt / 2.8); U.pow.userData.update(lt * 30); cam.position.set(30, .52, -5.5); cam.lookAt(80, 2.2, -5.5); cam.fov = 50; cam.updateProjectionMatrix(); }
  else if (lt < 5.1) { const wp = carX(1, t); cam.position.set(wp.x + 2 - (lt - 2.8) * .4, 2.6, -11.0); cam.lookAt(wp.x, 2.9, -5.5); cam.fov = 38; cam.updateProjectionMatrix(); }
  else if (lt < 6.7) { const cxw = carX(3, t).x; U.cluster.forEach((m, i) => pose(m, t, { look: clamp((U.cx3 - cxw) * .08, -.9, .9) + (i - 1.5) * .05 })); camTo(lt - 5.1, 1.6, [U.cx3 + 1.5, 1.75, -12.4, cxw, 2.4, -5.5], [U.cx3 + 1.0, 1.7, -12.2, cxw - 2, 2.4, -5.5], [34, 32]); }
  else { const m = U.victim, hp = V3(); pose(m, t, { look: Math.sin(t * 2) * .05 - .2 }); m.userData.rig.head.getWorldPosition(hp); camTo(lt - 6.7, d - 6.7, [hp.x + .5, hp.y + .02, hp.z - 1.5, hp.x, hp.y, hp.z], [hp.x + .38, hp.y + .03, hp.z - 1.2, hp.x, hp.y + .02, hp.z], [30, 26]); } };
// 2 the throw: a hand in the dark doorway -> the iron bar tumbling in slow motion
const ironPath = q => { const a = doorWorld(1, T_THROW), b = V3(U.VX, 2.25, -8.25); return V3(lerp(a.x, b.x, q), lerp(a.y, b.y, q) + Math.sin(q * Math.PI) * .9, lerp(a.z, b.z, q)); };
SHOTS[2] = (t, lt, d) => { const tm = lt < .9 ? T_THROW - .9 + lt : T_THROW + (lt - .9) * .35; stationBase(tm); const th = U.thrower;
  if (lt < .9) { const q = clamp(lt / .7); pose(th, tm, { armR: -2.4 + q * 3.4, elR: .4 - q * .3, lean: q * .2 }); th.position.x = th.userData.home.x; th.position.z = th.userData.home.z + .3;
    const dw = doorWorld(1, tm); if (q > .85) { U.iron.visible = true; U.iron.position.copy(ironPath(0)); U.iron.position.x = dw.x - .2; }
    cam.position.set(dw.x - 2.2, 1.7, -9.6); cam.lookAt(dw.x, dw.y + .2, -6.8); cam.fov = 30; cam.updateProjectionMatrix(); return; }
  const q = (lt - .9) / (d - .9) * .8; U.iron.visible = true; U.iron.position.copy(ironPath(q)); U.iron.rotation.set(lt * 1.6, lt * .9, lt * 2.2);
  cam.position.set(U.iron.position.x + 1.3, U.iron.position.y + .1, U.iron.position.z - 1.0); cam.lookAt(U.iron.position); cam.fov = 30; cam.updateProjectionMatrix(); };
// 3 impact: the bar strikes -> cap spins, he falls -> boots run in
SHOTS[3] = (t, lt, d) => { stationBase(t); const v = U.victim;
  U.men.forEach(m => { if (Math.abs(m.position.x - U.VX) < 6) m.position.y = -50; });
  const hitQ = clamp(lt / .35), f = ease(clamp((lt - .35) / 1.3));
  if (hitQ < 1) { U.iron.visible = true; U.iron.position.copy(ironPath(.8 + hitQ * .2)); U.iron.rotation.set(lt * 5, lt * 3, lt * 7); }
  else { U.iron.visible = true; U.iron.position.set(U.VX - .5, .68, -7.9); U.iron.rotation.set(0, .5, 0); }
  if (lt > .33 && lt < .45) { pl3.intensity = 18; pl3.position.set(U.VX, 2.2, -8); OV.fade = 0; overlay(c => { c.fillStyle = 'rgba(255,245,230,.55)'; c.fillRect(0, 0, L.W, L.H); }); }
  v.position.set(U.VX - f * .5, .6, -8.3); v.rotation.set(0, facing([0, 1]), f * 1.48); pose(v, t, { armL: f * 1.3, armR: f * .9 }); v.rotation.set(-f * 1.45, facing([0, 1]), 0);
  if (lt > .35) { U.cap.visible = true; U.cap.position.set(U.VX + .2 + f * .8, 2.4 + Math.sin(f * Math.PI) * .7 - f * 1.7, -8.0 - f * .9); U.cap.rotation.set(f * 6, f * 3, f * 4); if (f >= 1) U.cap.position.y = .66; }
  if (lt < 1.7) { cam.position.set(U.VX + 2.6, 1.5, -10.6); cam.lookAt(U.VX, 1.5, -8.2); cam.fov = 34; cam.position.x += Math.sin(lt * 40) * .03 * (lt > .35 && lt < .7); }
  else { U.runners.forEach((m, i) => { const q = clamp((lt - 1.7 - i * .15) / 1.0); at(m, lerp(U.VX - 9 - i * 1.5, U.VX - 1.6 - i * .55, q), .6, -9.0 - (i % 2) * .7, 0); pose(m, t, { walk: q < 1, speed: 11 }); }); cam.position.set(U.VX + 1.4, .45, -7.4); cam.lookAt(U.VX - 4, .7, -8.9); cam.fov = 40; }
  cam.updateProjectionMatrix(); };
// 4 brakes scream -> legionaries climb into the wagon (prisoners back away inside) -> a shot flashes in the dark doorway -> aftermath
SHOTS[4] = (t, lt, d) => { stationBase(t); const v = U.victim; v.position.set(U.VX - .5, .6, -8.3); v.rotation.set(-1.45, facing([0, 1]), 0); U.cap.visible = true; U.cap.position.set(U.VX + 1, .66, -8.9); U.iron.visible = true; U.iron.position.set(U.VX - .5, .68, -7.9);
  if (lt < 1.5) { U.sparks.visible = true; const wh = V3(-1.6, .45, -.9); U.pow.userData.loco.localToWorld(wh); U.sparks.position.copy(wh); U.sparks.userData.update(t, 1); pl3.intensity = 6 + Math.sin(t * 40) * 3; pl3.position.copy(wh);
    U.men.forEach(m => { if (Math.abs(m.position.x - wh.x) < 7) m.position.y = -50; }); cam.position.set(wh.x + 3.2, .6, -.6); cam.lookAt(wh.x, .55, wh.z); cam.fov = 30; cam.updateProjectionMatrix(); return; }
  const car = U.pow.userData.cars[2], dw = doorWorld(2, t), q = lt - 1.5;
  // prisoners inside car 2 shrink back from the doorway
  U.powMen.slice(6, 9).forEach((m, k) => { const b = clamp(q / .8); m.position.set(m.userData.home.x + (k - 1) * .5 * b, m.userData.home.y, m.userData.home.z - b * 1.2); pose(m, t, { handsUp: k === 1 && b > .5, look: 0 }); m.rotation.y = -Math.PI / 2; });
  U.runners.forEach((m, i) => { const k = clamp((q - i * .3) / 1.0); const x = dw.x - .6 + i * .45, z0 = -8.8, z1 = -6.2; at(m, x, .6 + clamp((k - .55) / .45) * (car.userData.by0 - .6 + .02), lerp(z0, z1, k), facing([0, 1])); pose(m, t, { walk: k > 0 && k < 1, speed: 10, armR: k > .45 && k < .9 ? 2.2 : 0, armL: k > .45 && k < .9 ? 2.0 : 0 }); if (k >= 1) m.position.y = -50; });
  if (q < 2.2) { camTo(q, 2.2, [dw.x + 4.6, 1.7, -11.6, dw.x, 1.9, -6.8], [dw.x + 3.6, 1.8, -11.0, dw.x - .2, 2.0, -6.8], [34, 32], .015); return; }
  const q2 = q - 2.2; if (q2 < .5) { U.runners.forEach(m => m.position.y = -50); const fl = (q2 > .12 && q2 < .2) || (q2 > .3 && q2 < .36); if (fl) { U.flash.visible = true; U.flash.position.set(dw.x + .3, dw.y + .2, -6.5); U.flash.scale.setScalar(1.6); pl2.intensity = 40; pl2.position.set(dw.x, dw.y, -6.2); }
    camTo(q2, .5, [dw.x + 6.5, 1.5, -12.5, dw.x, 2.1, -6.5], [dw.x + 6.3, 1.5, -12.3, dw.x, 2.1, -6.5], [30, 30]); return; }
  U.runners.forEach(m => m.position.y = -50); const q3 = q2 - .5; camTo(q3, d - 4.2, [U.VX + 2.8, .85, -10.0, U.VX + .4, .8, -8.4], [U.VX + 2.5, .95, -10.3, U.VX, .9, -8.2], [34, 32]); };
// ----- town helpers -----
function townDay(t) { show('town'); look('grey', [0xc8c8c4, .006], 1.4, 1.8, 0xf2ece0, [-30, 60, 40], [0, 0, 500]); U.banners.forEach(b => b.userData.update(t, .03)); U.raid.forEach(m => m.position.y = -50); }
// 5 ARREST: Red Guards' bayonets close in around three legionaries -> hands up -> marched in, the door shuts
SHOTS[5] = (t, lt, d) => { townDay(t); const ctr = V3(-1, 0, 503);
  U.arrested.forEach((m, i) => { at(m, -1.6 + i * 1.0, 0, 4 + (i % 2) * .4, facing([0, -1]) + (i - 1) * .3); });
  if (lt < 1.9) { const q = ease(clamp(lt / 1.3)); U.door.rotation.y = 0;
    U.guards.forEach((m, i) => { const a = -2.6 + i * .95, r = lerp(5.5, 2.2, q); at(m, -.6 + Math.cos(a) * r, 0, 4.3 + Math.sin(a) * r * .8, Math.atan2(Math.sin(a), -Math.cos(a)) ); m.rotation.y = facing([-.6 - m.position.x, 4.3 - m.position.z]); pose(m, t, { aim: true, walk: q < 1, speed: 6 }); });
    U.arrested.forEach((m, i) => pose(m, t, { handsUp: lt > .9, look: (i - 1) * .3 }));
    camTo(lt, 1.9, [1.4, .35, 506.2, -.6, 1.9, 504], [1.0, .3, 505.8, -.6, 2.0, 504], [40, 36]); return; }
  const q = lt - 1.9; U.door.rotation.y = q < 1.0 ? -lerp(0, 1.4, clamp(q / .3)) : -lerp(1.4, 0, clamp((q - 1.0) / .25));
  const order = [...U.arrested, U.guards[0], U.guards[1]]; order.forEach((m, i) => { const k = clamp((q - i * .18) / 1.0); at(m, lerp(-1.2 + i * .5, 0, k), 0, lerp(2.5 + i * .9, -6.4, k), facing([0, -1])); pose(m, t, { walk: k < 1, speed: 6, handsUp: i < 3, aim: i >= 3 }); if (k >= 1) m.position.y = -50; });
  U.guards.slice(2).forEach((m, i) => { at(m, -4 + i * 2.6, 0, 1.4 + (i % 2), facing([0, -1])); pose(m, t, { port: true }); });
  camTo(q, d - 1.9, [6.5, 1.7, 508, -.5, 1.8, 494], [5.5, 1.7, 507, -.5, 1.8, 494], [34, 32]); };
// 6 FREE BY FORCE: night, lanterns pour down the street -> rifle butts smash the door in -> they storm inside
SHOTS[6] = (t, lt, d) => { show('town'); look('night', [0x141a28, .02], .35, .35, 0x8aa0d0, [-30, 60, 40], [0, 0, 500], [0x4a5a8a, 0x1a1a22]); U.banners.forEach(b => b.userData.update(t, .03));
  U.guards.concat(U.arrested).forEach(m => m.position.y = -50);
  if (lt < 1.2) { U.door.rotation.y = 0; U.raid.forEach((m, i) => { at(m, -24 + lt * 5 - i * 1.3, 0, 3 + (i % 3) * 1.1, facing([1, -.15])); pose(m, t, { walk: true, speed: 10, port: true }); }); U.lanterns.forEach((l, k) => { const m = U.raid[k * 3]; l.intensity = 10 + Math.sin(t * 20 + k) * 2; l.position.set(m.position.x + .4, 1.4, m.position.z + .3 + 500); l.position.z -= 500; });
    camTo(lt, 1.2, [-4, 1.2, 509, -20, 1.6, 502], [-6, 1.4, 508, -14, 1.6, 501], [36, 34]); return; }
  const q = lt - 1.2, hitT = .55; U.lanterns.forEach((l, k) => { l.intensity = 9; l.position.set(-2.5 + k * 1.8, 1.5, -3.5 + k * .3); });
  U.raid.forEach((m, i) => { if (i < 2) { at(m, -1.2 + i * 1.9, 0, -4.4, facing([0, -1]) + (i ? .5 : -.5)); const sw = Math.sin(clamp(q / hitT) * Math.PI); pose(m, t, { port: true, lean: -.3 * sw }); m.userData.rifle.position.x += .25 * sw; return; }
    const k = clamp((q - hitT - .1 - (i - 2) * .12) / .9); at(m, -1.5 + (i % 3) * .8, 0, lerp(-1 + (i - 2) * .9, -7, k), facing([0, -1])); pose(m, t, { walk: k < 1, speed: 11, port: true }); if (k >= 1) m.position.y = -50; });
  const br = clamp((q - hitT) / .2); U.door.rotation.y = -br * 1.7; U.door.position.z = -5.9 - br * .2; U.doorPanel.rotation.z = br * .15;
  if (q > hitT) { U.splinters.visible = true; const s = q - hitT; U.splinters.children.forEach((p, i) => { const r = rng(i + 30); p.position.set(-.2 + (r() - .5) * 1.5 + (r() - .5) * s * 3, Math.max(.05, 1.6 + (r() - .2) * 1.2 + s * (2 - 4.9 * s)), 494.1 - s * (1 + r() * 2) + (r() < .3 ? s * 3 : 0)); p.rotation.set(s * 9 * r(), s * 7, s * 5 * r()); }); }
  if (q > hitT && q < hitT + .12) { pl3.intensity = 25; pl3.position.set(0, 1.5, 495); }
  pl2.intensity = 8; pl2.position.set(.5, 2.2, 496);
  camTo(q, d - 1.2, [3.0, 1.5, 502.5, -.4, 1.8, 494], [2.6, 1.5, 501.8, -.4, 1.9, 494], [34, 34], q > hitT && q < hitT + .4 ? .04 : 0); };
// 7 RAIL WAR: animated map -> armored train fires -> station burns
SHOTS[7] = (t, lt, d) => {
  if (lt < 2.0) { OV.noGL = true; overlay((c, tt) => L.routeMap(c, lt, 2.0, tt)); cam.position.set(0, -500, 0); return; }
  show('war'); const warLook = x => look('dusk', [0x9a7060, .004], 1.0, 2.0, 0xffa060, [100, 30, -60], [x, 0, -600]);
  U.arm.position.x = 0; U.arm.userData.update(0); U.armSmoke.visible = true; smk(U.armSmoke, U.arm.userData.loco, U.arm.userData.loco.userData.chimney, t);
  if (lt < 3.1) { warLook(0); const q = lt - 2.0, tw = U.arm.userData.front, tur = tw.userData.turret; tur.rotation.y = .9;
    const mz = tw.userData.muzzle.clone(); tur.localToWorld(mz); const fl = q > .25 && q < .45; U.cannonFlash.visible = fl; U.cannonFlash.position.copy(mz); U.cannonFlash.scale.setScalar(4); pl2.intensity = fl ? 30 : 0; pl2.position.copy(mz); U.cannonSmoke.visible = q > .25; U.cannonSmoke.userData.update(q - .25, mz);
    const fx0 = tw.position.x + 4; camTo(q, 1.1, [fx0 + 2, 1.4, -588, fx0, 3.6, -600], [fx0 + 2.5, 1.5, -589, fx0, 3.7, -600], [32, 30], q > .25 && q < .7 ? .05 : 0); return; }
  warLook(40); const q = lt - 3.1; U.bfires.forEach(f => f.userData.update(t)); U.bsmoke.visible = true; U.bsmoke.userData.update(t, V3(40, 6, -612)); pl2.intensity = 25 + Math.sin(t * 17) * 5; pl2.position.set(40, 4, -608);
  camTo(q, d - 3.1, [22, 2, -588, 40, 4, -612], [25, 2.2, -589, 40, 4.5, -612], [36, 34]); };
// 8 LEGION CLOSE-UP: dolly along the men riding the flatcar -> ends on the hero's face, flag above him
SHOTS[8] = (t, lt, d) => { show('war'); look('dawn', [0xe8d2b8, .004], 1.3, 2.2, 0xffe0b8, [60, 40, -30], [0, 0, -600]);
  U.arm.position.x = 0; U.arm.userData.update(0); U.arm.userData.front.userData.turret.rotation.y = 0;
  U.onTrain.forEach((m, i) => pose(m, t, { look: .1 + (i % 2) * .2 })); U.heroFlagCloth.userData.update(t, .25);
  const hero = U.onTrain[3], hp = V3(); hero.userData.rig.head.getWorldPosition(hp);
  camTo(lt, d, [hp.x - 4.5, hp.y + .1, hp.z + 4.2, hp.x - 2.5, hp.y - .1, hp.z], [hp.x + .25, hp.y + .02, hp.z + 1.25, hp.x, hp.y, hp.z], [34, 28]); };
// 9 aerial: one tiny train across endless forest (+ inset map)
SHOTS[9] = (t, lt, d) => { show('plain'); look('dawn', [0xe8d2b8, .0012], 1.3, 2.2, 0xffd8a8, [200, 60, -100], [0, 0, -2600]);
  const x = -200 + lt * 14; U.plainTrain.position.set(x, 0, 0); U.plainTrain.userData.update(x); U.smokeC.visible = true; smk(U.smokeC, U.plainTrain.userData.loco, U.plainTrain.userData.loco.userData.chimney, t);
  camTo(lt, d, [x - 90, 55, -2600 + 70, x + 10, 0, -2600], [x - 60, 48, -2600 + 60, x + 25, 0, -2600], [38, 36]); overlay((c, tt) => L.insetMap(c, L.W - 560, L.H - 380, 500, 320, lt, tt)); };
// 10 CITY: armored train (loco first) rolls in -> men jump down and charge -> red flag lowered, white-red hoisted to the top
SHOTS[10] = (t, lt, d) => { show('city'); look('dusk', [0xa07a68, .005], 1.0, 2.0, 0xffa870, [60, 30, 40], [600, 0, 0]);
  U.citySmoke.forEach((c, i) => { c.s.visible = true; c.s.userData.update(t + i * 2, V3(c.x, 4, c.z)); });
  const ax = 30 - Math.min(lt, 2.0) * 12 + Math.max(0, lt - 2.0) * 0; U.carm.position.set(ax, 0, 0); U.carm.userData.update(-ax);
  const top = 8.6, bot = 1.0; const fd = ease(clamp((lt - 2.6) / 1.0)), fu = ease(clamp((lt - 3.5) / 1.1));
  U.redF.position.y = lerp(top, bot, fd); U.redF.visible = lt < 3.5; U.czF.position.y = lerp(bot, top, fu); U.czF.visible = lt >= 3.5; U.redF.userData.update(t); U.czF.userData.update(t);
  at(U.hoister, 6.4, .6, -8.6, facing([-1, 0])); pose(U.hoister, t, { armR: 2.6 - Math.abs(Math.sin(t * 5)) * .8, armL: 2.4 - Math.abs(Math.cos(t * 5)) * .8 });
  U.crowd.forEach((m, i) => pose(m, t, { armR: lt > 3.9 ? -2.6 + Math.sin(t * 6 + i) * .3 : 0, look: .3 }));
  const fx0 = U.carm.userData.cars[1].getWorldPosition(V3()).x - 600; U.chargers.forEach((m, i) => { const q = clamp((lt - 1.4 - i * .08) / 1.6), z = lerp(-1.4, -8.6 - (i % 2) * .8, q); at(m, fx0 - 3 + (i % 4) * 1.6 - q * 3, q < .2 ? lerp(1.85, 0, q / .2) : (z < -7.3 ? .6 : 0), z, facing([-.3, -1])); pose(m, t, { walk: q > 0 && q < 1, speed: 11, port: q < 1, armR: q >= 1 ? -2.8 : 0 }); });
  if (lt < 1.4) camTo(lt, 1.4, [578, 1.2, 8, 594, 2.5, 0], [584, 1.3, 7, 600, 2.6, 0], [36, 34]);
  else if (lt < 2.6) camTo(lt - 1.4, 1.2, [626, 1.3, 5, 614, 1.6, -5], [624, 1.4, 4.4, 612, 1.6, -8], [36, 32], .02);
  else camTo(lt - 2.6, d - 2.6, [617, 1.7, -3.6, 606, 7.2, -9], [616, 1.6, -4.0, 606, 8.2, -9], [40, 38]); };
// 11 "their own country does not yet exist": the boxcar at night; he unfolds a map; finger on a blank region with a question mark
SHOTS[11] = (t, lt, d) => { show('inn'); look('night', null, .7, 0, 0xffffff, [0, 60, 0], [0, 0, 1500], [0xb08860, 0x403020]); S.background = new THREE.Color(0x0a0604);
  pl1.intensity = 14 + Math.sin(t * 9) * 2 + Math.sin(t * 23) * 1.2; pl1.position.set(0, .9, 1499.4); const sw = Math.sin(t * 1.3) * .22; U.lamp.rotation.z = sw; pl3.intensity = 10; pl3.position.set(.8 + Math.sin(sw) * .35, 2.2, 1500.2); U.stoveFire.userData.update(t);
  U.sleepers.forEach(m => pose(m, t * .2, {})); pose(U.reader, t, { sit: true, armL: .9, armR: .9, elL: .9, elR: .9, nod: -.45 }); U.reader.position.y = .02;
  // map held in his hands, tilted toward his face
  const hl = V3(), hr = V3(), hd = V3(); U.reader.userData.rig.arms[0].hand.getWorldPosition(hl); U.reader.userData.rig.arms[1].hand.getWorldPosition(hr); U.reader.userData.rig.head.getWorldPosition(hd);
  const mw = hl.clone().add(hr).multiplyScalar(.5); mw.y += .04; const loc = L.SETS.inn.worldToLocal(mw.clone()); U.map.position.copy(loc); U.map.up.set(-1, 0, 0); U.map.lookAt(hd); U.map.updateMatrixWorld(true);
  if (lt < 1.2) { camTo(lt, 1.2, [-1.2, 1.7, 1501.0, 1.5, 1.0, 1500.2], [-1.0, 1.65, 1500.9, 1.5, 1.05, 1500.2], [40, 38]); return; }
  // close-up: only now his finger enters from below (his own sleeve)
  const q = lt - 1.2, fp = ease(clamp(q / .7)), pin = V3((U.mapPin[0] - .5) * .62, (.5 - U.mapPin[1]) * .42, .0); U.map.localToWorld(pin);
  U.finger.visible = true; const dir = pin.clone().sub(V3(hd.x, hd.y - .45, hd.z + .15)).normalize(); U.finger.quaternion.setFromUnitVectors(V3(0, 1, 0), dir); U.finger.position.copy(pin).addScaledVector(dir, -.07 - (1 - fp) * .12);
  const cpos = V3(hd.x + .3, hd.y + .38, hd.z + .3); camTo(q, d - 1.2, [cpos.x, cpos.y, cpos.z + .05, mw.x, mw.y, mw.z], [cpos.x + .12, cpos.y - .06, cpos.z + .02, pin.x, pin.y, pin.z], [32, 26]); };
// 12 alone in deep snow at dusk beside a row of crosses; camera rises; the 9,000 km arc
SHOTS[12] = (t, lt, d) => { show('snow'); look('snowdusk', [0xd8c0b8, .008], 1.1, 1.8, 0xffc8a0, [200, 20, -60], [-1500, 0, 0], [0xc8d0e8, 0x8a8aa0]); U.snowS.visible = true; U.snowS.userData.update(t);
  pose(U.loner, t, { look: .25 }); camTo(lt, d, [-1497.4, 1.6, -.2, -1500, 1.6, -2.6], [-1475, 26, 18, -1500, 0, -2.6], [32, 40]);
  overlay((c, tt) => L.arcMap(c, Math.max(0, lt - 2.2), tt, clamp((lt - 2.0) / .8) * .92)); };
