// ===================== LAOS 2: armies, the trail, the campaign, surviving the weeks after (cues 25-45) =====================
import * as L from './lib3.js';
import * as M from './maps.js';
import * as X from './lao.js';
import * as LM from './laomaps.js';
import * as Z from './laosets.js';
const { THREE, cam, U, V3, at, lerp, clamp, ease, look, show, fx, overlay, OV, pose, facing, SETS } = L;
const { ct, wp, light, hide } = Z;
export const RANGE = { from: 25, to: 45 };
export const SHOTS = {};
const fade = (lt, d, a = .4) => clamp(lt / a) * (1 - clamp((lt - d + a) / a));
// readable label: dark rounded backing behind Cinzel text
function tag(c, s, x, y, size, a = 1, col = '#f2e8d2', align = 'center') { if (a <= 0) return; c.save(); c.font = `700 ${size}px Cinzel, serif`; const w = c.measureText(s).width, x0 = align === 'left' ? x - 14 : x - w / 2 - 14; c.globalAlpha = a * .72; c.fillStyle = '#0e0a06'; c.fillRect(x0, y - size * .95, w + 28, size * 1.35); c.restore(); M.label(c, s, x, y, size, col, a, align); }
// callout: label placed at (lonL,latL) with a leader line to (lonT,latT)
function callout(c, pr, s, lonL, latL, lonT, latT, a, size = 26) { if (a <= 0) return; const [x0, y0] = pr(lonL, latL), [x1, y1] = pr(lonT, latT); c.save(); c.globalAlpha = a; c.strokeStyle = '#ffe0c0'; c.lineWidth = 3; c.beginPath(); c.moveTo(x0, y0 + 6); c.lineTo(x1, y1); c.stroke(); c.fillStyle = '#ffe0c0'; c.beginPath(); c.arc(x1, y1, 6, 0, 7); c.fill(); c.restore(); tag(c, s, x0, y0, size, a, '#ffe0c0'); }
export async function build() { Z.skies(); Z.trailSet(); Z.ridgeSet(); Z.skySet(); Z.jarsSet(); Z.opsSet(); Z.villageSet();
  U.vJet = X.jet(); SETS.village.add(U.vJet); U.vJet2 = X.jet(); SETS.village.add(U.vJet2);
  U.crates = [...Array(6)].map(() => { const c = L.mesh(new THREE.BoxGeometry(.8, .5, .5), L.mat(0x6a5a3a, .9)); SETS.ridge.add(c); return c; });
  U.plFlagT = L.flag(.9, .6, ['#c8241c'], { draw: X.plDraw }); SETS.trail.add(U.plFlagT);
  U.tsmoke = [0, 1, 2].map(() => fx(L.smoke(V3(), { n: 36, color: 0x3a3430, wind: [1, .3], rise: 16, size: 3, grow: 4, life: 6, opacity: .85 })));
  U.tFire = L.fire(12, 2.6); SETS.trail.add(U.tFire); U.tFire.position.y = -60;
  U.seedlings = new THREE.Group(); for (let k = 0; k < 5; k++) { const sd = L.mesh(new THREE.ConeGeometry(.025, .28, 4), L.mat(0x6aa83a, .9), [(k % 3 - 1) * .025, -.12, (k % 2 - .5) * .03], [Math.PI, 0, (k - 2) * .12], U.seedlings); } U.fam.mum.userData.rig.arms[1].hand.add(U.seedlings); U.seedlings.visible = false;
  fixBuild();
}
// ---- QA fixes: NVA pith helmets, believable ruin, rebuild tools, Plain of Jars without karst ----
function pithify(m) { m.traverse(o => { if (!o.isMesh || !o.geometry.parameters) return; const gp = o.geometry.parameters;
  if (o.geometry.type === 'SphereGeometry' && Math.abs(gp.radius - .15) < 1e-6 && Math.abs(gp.thetaLength - Math.PI * .5) < 1e-6) { o.scale.set(1.04, 1.3, 1.14); o.position.y = .065; }
  if (o.geometry.type === 'CylinderGeometry' && Math.abs(gp.radiusTop - .19) < 1e-6 && gp.height < .02) { o.geometry = new THREE.CylinderGeometry(.152, .2, .05, 22, 1, true); o.material = o.material.clone(); o.material.side = THREE.DoubleSide; o.position.y = .055; o.scale.set(1, 1, 1.1); } }); }
function fixBuild() { [...U.nva, ...U.porters].forEach(pithify);
  // Plain of Jars: open rolling grassland, no karst towers
  SETS.jars.children.forEach(ch => { if (ch.isGroup && !ch.userData.isJet && ch !== U.jJets[0] && ch !== U.jJets[1] && !U.jBlasts.includes(ch)) { let karst = false; ch.traverse(o => { if (o.isMesh && o.geometry.type === 'LatheGeometry' && o.geometry.parameters.points.length > 12) karst = true; }); if (karst) ch.visible = false; } });
  { const r = (k => () => (k = (k * 16807) % 2147483647) / 2147483647)(77); for (let i = 0; i < 16; i++) { const hl = L.mesh(new THREE.SphereGeometry(40 + r() * 50, 18, 8, 0, Math.PI * 2, 0, Math.PI / 2), L.mat(i % 2 ? 0x8a9a58 : 0x7a8c4c, 1), [(r() - .5) * 700, -6, -110 - r() * 260]); hl.scale.y = .16 + r() * .1; SETS.jars.add(hl); } }
  // ruin: deck tilted onto broken stilts, roof collapsed in two pieces, charred planks scattered
  const R = new THREE.Group(), W = 7, D = 5, tilt = Math.atan(1 / 7), ch = L.mat(0x3a2e24, 1), wd = L.mat(0x5a4632, .95), th = L.mat(0x4a3c2c, 1), postM = L.mat(0x4a3828, .9);
  const deck = new THREE.Group(); deck.position.set(0, 1.4, 0); deck.rotation.z = -tilt; R.add(deck);
  L.mesh(new THREE.BoxGeometry(W + .6, .15, D + .6), wd, [0, 0, 0], [0, 0, 0], deck);
  L.mesh(new THREE.BoxGeometry(W * .55, .9, .12), ch, [-1.4, .52, -D / 2 + .05], [0, 0, 0], deck); L.mesh(new THREE.BoxGeometry(.12, 1.3, D * .6), ch, [-W / 2 + .05, .72, -.4], [0, 0, 0], deck); L.mesh(new THREE.BoxGeometry(.12, .7, 1.2), ch, [-W / 2 + .05, .42, 1.6], [0, 0, 0], deck);
  L.mesh(new THREE.BoxGeometry(4.6, .18, 4.0), th, [1.1, .165, .35], [0, 0, 0], deck); L.mesh(new THREE.BoxGeometry(.1, .1, 4.3), ch, [-1.1, .3, .35], [.0, 0, 0], deck);
  for (let i = 0; i < 4; i++) L.mesh(new THREE.BoxGeometry(.1, .08, 1.4 + i * .3), ch, [-2.6 + i * .5, .12, -1.2 + (i % 2) * .8], [0, .3 + i * .5, 0], deck);
  { const x0 = (W / 2 + .3) * Math.cos(tilt), y0 = 1.4 - (W / 2 + .3) * Math.sin(tilt) + .08, x1 = x0 + 1.9, y1 = .04, ang = Math.atan2(y0 - y1, x1 - x0), len = Math.hypot(x1 - x0, y0 - y1);
    L.mesh(new THREE.BoxGeometry(len, .18, 3.8), th, [(x0 + x1) / 2 + .05, (y0 + y1) / 2 + .1, .35], [0, 0, -ang], R); }
  for (const x of [-W / 2 + .2, 0, W / 2 - .2]) for (const z of [-D / 2 + .2, D / 2 - .2]) { const h = 1.4 - x * Math.tan(tilt) - .08; L.mesh(new THREE.CylinderGeometry(.11, .13, h, 6), postM, [x, h / 2, z], [0, 0, 0], R); }
  L.mesh(new THREE.CylinderGeometry(.1, .13, .55, 6), postM, [W / 2 + .9, .27, -1.2], [0, 0, .5], R); L.mesh(new THREE.CylinderGeometry(.11, .13, 1.6, 6), postM, [-W / 2 - 1.3, .12, 1.4], [0, .4, Math.PI / 2 - .05], R);
  const pr = (k => () => (k = (k * 16807) % 2147483647) / 2147483647)(91); U.rPlanks = [];
  for (let i = 0; i < 9; i++) { const pl = L.mesh(new THREE.BoxGeometry(.22, .06, 1.2 + pr() * 1.4), i % 3 ? ch : wd, [-5 + pr() * 2.2 + (i % 2) * 8.6, .03 + (i % 3) * .002, -1.5 + pr() * 4.5], [0, pr() * 3, 0], R); U.rPlanks.push(pl); }
  U.rFire = L.fire(16, 1.7); U.rFire.position.set(.6, 1.55, .9); R.add(U.rFire); U.rFire2 = L.fire(12, 1.2); U.rFire2.position.set(-2.2, 1.8, -1.4); R.add(U.rFire2);
  at(R, 2, -60, -14, -.15); SETS.village.add(R); U.ruin2 = R;
  // rebuild: cleared site with a lashed cross-beam, plank stack and a mallet in the father's hand
  const RB = new THREE.Group(); L.mesh(new THREE.BoxGeometry(6.9, .14, .14), L.mat(0xa8865a, .9), [0, 1.75, 2.3 + .14], [0, 0, 0], RB);
  for (let i = 0; i < 5; i++) L.mesh(new THREE.BoxGeometry(2.6, .07, .24), L.mat(i % 2 ? 0xa8865a : 0x9a7a50, .9), [-5.6, .04 + i * .075, 1.2 + (i % 2) * .05], [0, (i - 2) * .04, 0], RB);
  at(RB, 2, -60, -11, -.15); SETS.village.add(RB); U.rebuild = RB;
  const mal = new THREE.Group(); L.mesh(new THREE.CylinderGeometry(.018, .018, .5, 8), L.mat(0x7a5a34, .8), [0, -.2, 0], [0, 0, 0], mal); L.mesh(new THREE.CylinderGeometry(.06, .06, .2, 10), L.mat(0x6a4a2a, .8), [0, -.45, 0], [0, 0, Math.PI / 2], mal); mal.position.set(0, -.02, 0); mal.rotation.set(0, 0, Math.PI / 2); U.fam.dad.userData.rig.arms[0].hand.add(mal); mal.visible = false; U.mallet = mal;
}

function trailLook(sky = 'day', dim = 1) { show('trail'); look(sky, [0x7a8a70, .006], 1.4 * dim, 1.6 * dim, 0xfff0d8, [-40, 70, 30], [9000, 0, 0]); hide(U.trucks, U.bikes, U.porters, U.nva, U.tJets); U.treaty.position.y = -60; U.tBlasts.forEach(b => b.userData.update(-1)); U.plFlagT.position.y = -60; }
function walkRoad(m, x, side, t, o = {}) { const p = Z.roadAt(x), q = Z.roadAt(x + .5); at(m, p.x, 0, p.z + side, facing([q.x - p.x, q.z - p.z])); pose(m, t, { walk: true, ...o }); }
function villageLook(sky = 'day', fog = [0xd8e0d8, .002], hemi = 1.5, sun = 2.4, sunCol = 0xfff0dc, sunPos = [-60, 70, 40]) { show('village'); look(sky, fog, hemi, sun, sunCol, sunPos, [3000, 0, 0]);
  hide(U.ruin, U.newPosts, U.warn, U.plot, U.scale, U.scrap, U.vStakes, U.vBombies, U.craters, Object.values(U.fam), U.farmers, U.buckets, U.vJet, U.vJet2); U.vfire.position.y = -60; U.houses[1].position.y = 0; if (U.vCol) hide(U.vCol); if (U.seedlings) U.seedlings.visible = false; U.ruin.position.y = -60; U.newPosts.position.y = -60; if (U.ruin2) { U.ruin2.position.y = -60; U.rebuild.position.y = -60; U.mallet.visible = false; } }
// 25 nva_march
SHOTS[25] = (t, lt, d) => { trailLook(); U.nva.forEach((m, i) => walkRoad(m, -6 + lt * 1.3 - i * 2.3, (i % 2 ? 1.0 : -1.0), t + i * .3));
  const fl = U.plFlagT, m3 = U.nva[3]; const hp = V3(); m3.getWorldPosition(hp); fl.position.y = -60;
  const p = Z.roadAt(-10 + lt * 1.3); light(0, 'trail', p.x, 4, p.z + 2, 30, 0xfff0d8, 30);
  ct('trail', lt, d, [p.x - 2, 1.6, p.z + 5.5, p.x + 3, 1.3, p.z], [p.x - 1, 1.5, p.z + 5, p.x + 4, 1.3, p.z], [40, 40]); };
// 26 hmong
SHOTS[26] = (t, lt, d) => { show('ridge'); look('morning', [0xc8d0d8, .002], 1.5, 2.4, 0xfff0d8, [-60, 50, 80], [9000, 0, 6000]);
  at(U.plane, 24, 0, 0, Math.PI); (U.plane.userData.props || []).forEach(p => p.rotation.x = t * 20);
  U.hmong.forEach((m, i) => { if (i < 5) { at(m, -14 + lt * 1.1 + i * 2.8, 0, 3 + (i % 2) * 2.6, facing([1, 0])); pose(m, t + i, { walk: true }); } else { at(m, 15.5 + (i - 5) * 1.5, 0, 4.4 + (i % 2) * .9, facing([0, 1])); pose(m, t + i, {}); X.act(m, t, 'carry'); } });
  U.crates.forEach((c, i) => at(c, 15 + (i % 3) * 1, .25 + Math.floor(i / 3) * .5, 2.6));
  ct('ridge', lt, d, [-22, 3, 18, 4, 1.5, 0], [-14, 2.2, 14, 6, 1.5, 0], [40, 38]); overlay(c => L.caption(c, 'A CIA-SUPPORTED ARMY', 'MANY OF ITS FIGHTERS WERE HMONG', fade(lt, d))); };
// 27 domino
SHOTS[27] = (t, lt, d) => { OV.noGL = true; overlay(c => { const pr = LM.view(101, 14, 24); LM.base(c, pr, { hl: [['Laos', '#d8b060']] }); LM.outline(c, pr, 'Laos', '#ffe090', 3, 8);
  const order = [['LAOS', 103.5, 19.4], ['THAILAND', 101.0, 15.6], ['CAMBODIA', 104.8, 12.7], ['S. VIETNAM', 107.4, 14.2], ['BURMA', 96.6, 20.4], ['MALAYSIA', 102.0, 4.6]];
  order.forEach(([n, lon, lat], i) => { const [x, y] = pr(lon, lat); tag(c, n, x, y + 62, 22, 1, '#fff4e0'); const fall = ease(clamp((lt - .8 - i * .55) / .5)); c.save(); c.translate(x - 20, y + 20); c.rotate(-fall * 1.25); c.fillStyle = '#f2ead8'; c.strokeStyle = '#2a1a10'; c.lineWidth = 4; c.fillRect(-22, -90, 44, 90); c.strokeRect(-22, -90, 44, 90); c.fillStyle = '#2a1a10'; for (const dy of [-70, -25]) { c.beginPath(); c.arc(0, dy, 6, 0, 7); c.fill(); } c.fillRect(-22, -48, 44, 4); c.restore(); });
  M.vignette(c, .45); c.save(); c.fillStyle = 'rgba(12,9,6,.65)'; c.fillRect(0, 40, 760, 140); c.restore(); M.label(c, 'THE VIEW FROM WASHINGTON', 70, 100, 44, '#f2e8d2', clamp(lt / .5), 'left'); M.label(c, 'IF LAOS FELL, WOULD THE REGION FOLLOW?', 72, 150, 28, '#f2d8a0', clamp(lt / .5), 'left'); }); };

// 28 trail_map
SHOTS[28] = (t, lt, d) => { OV.noGL = true; overlay(c => { const pr = LM.view(105.5, 16, 14); LM.base(c, pr, { hl: [['Laos', '#d8b060'], ['Vietnam', '#b86a4a', .75]] }); LM.outline(c, pr, 'Laos', '#ffe090', 3, 8);
  const P = (lo, la) => pr(lo, la); c.save(); c.strokeStyle = '#c8241c'; c.lineWidth = 14; c.lineCap = 'round'; c.lineJoin = 'round'; c.setLineDash([30, 18]); c.shadowColor = 'rgba(0,0,0,.6)'; c.shadowBlur = 10; c.beginPath();
  const path = [[105.85, 21.0], [105.65, 19.9], [105.5, 19.0], [105.1, 18.35], [104.85, 17.85], [105.15, 17.35], [105.75, 16.95], [106.15, 16.55], [106.3, 15.75], [106.6, 14.85], [106.75, 14.0], [106.95, 13.1], [107.0, 12.2], [106.7, 11.2]].map(p => P(...p)); const n = clamp((lt - .5) / 3.6) * (path.length - 1);
  path.forEach((p, i) => { if (i <= n) i ? c.lineTo(...p) : c.moveTo(...p); }); const fi = Math.floor(n); if (fi < path.length - 1) c.lineTo(lerp(path[fi][0], path[fi + 1][0], n - fi), lerp(path[fi][1], path[fi + 1][1], n - fi)); c.stroke(); c.restore();
  LM.city(c, pr, 'Hanoi'); LM.city(c, pr, 'Saigon', { a: clamp((lt - 3.6) / .4) }); tag(c, 'NORTH VIETNAM', ...P(107.6, 20.6), 24, .95); tag(c, 'SOUTH VIETNAM', ...P(109.6, 13.6), 24, .95); tag(c, 'LAOS', ...P(102.8, 19.2), 38, 1, '#fff0c0');
  tag(c, 'THROUGH LAOTIAN TERRITORY', L.W / 2, L.H - 80, 34, clamp((lt - 1.6) / .5), '#ffe0a0'); }); };

// 29 villagers_between
SHOTS[29] = (t, lt, d) => { villageLook('day'); U.farmers.forEach((m, i) => { at(m, -12 + i * 4.6, .1, 30 + (i % 2) * 2, facing([-.4, -1])); pose(m, t, {}); if (lt > 1.6) X.act(m, t, i % 2 ? 'lookUp' : 'lookDown'); else X.act(m, t + i, 'dig', { rate: 2 }); });
  if (!U.vCol) { U.vCol = [...Array(8)].map((_, i) => { const m = X.villager({ seed: 2500 + i, hat: 'pith', shirt: 0x5a6a3a, lower: 0x5a6a3a, gun: true, longSleeve: true }); pithify(m); SETS.village.add(m); return m; }); }
  U.vCol.forEach((m, i) => { at(m, -30 + lt * 1.4 + i * 1.6, .3, 25, facing([1, 0])); pose(m, t + i, { walk: true }); });
  at(U.vJet, 160 - (lt - 2.2) * 120, 36, 10, Math.PI); U.vJet.rotation.z = .15; if (lt < 2.2) U.vJet.position.y = -60;
  ct('village', lt, d, [10, 2.2, 52, -2, 2, 26], [6, 2.0, 49, -4, 2.4, 26], [42, 40]); };
// 30 trail_map:2
SHOTS[30] = (t, lt, d) => { OV.noGL = true; overlay(c => { const pr = LM.viewLerp([105.5, 16, 14], [106.2, 15.6, 9], ease(clamp(lt / 3))); LM.base(c, pr, { hl: [['Laos', '#d8b060'], ['Vietnam', '#b86a4a', .6], ['Cambodia', '#a89070', .5]] }); LM.trail(c, pr, clamp((lt - .4) / 4.2), { col: '#e8a030', w: 6 });
  M.label(c, 'THE HO CHI MINH TRAIL', L.W / 2, L.H - 90, 46, '#ffe0a0', clamp((lt - .8) / .5)); LM.city(c, pr, 'Tchepone', { a: clamp((lt - 2) / .4) }); LM.city(c, pr, 'Attapeu', { a: clamp((lt - 3) / .4) }); M.vignette(c, .5); }); };
// 31 trail_trucks (dusk)
SHOTS[31] = (t, lt, d) => { trailLook('dusk', .55); const xs = [-14, -26, -38];
  U.trucks.forEach((tr, i) => { const x = xs[i] + lt * 3.2; const p = Z.roadAt(x), q = Z.roadAt(x + 1); at(tr, p.x, 0, p.z, -Math.atan2(q.z - p.z, q.x - p.x)); tr.userData.update(x); });
  U.bikes.forEach((b, i) => { const x = -4 + lt * 1.2 - i * 3; const p = Z.roadAt(x), q = Z.roadAt(x + 1); at(b, p.x, 0, p.z + 2.75, -Math.atan2(q.z - p.z, q.x - p.x)); const m = U.porters[i]; at(m, p.x + .15, 0, p.z + 3.5, facing([1, 0])); pose(m, t + i, { walk: true, speed: 4, armL: 1.05, elL: .15, armLx: -.35, armR: .2, elR: .3 }); });
  U.nva.forEach((m, i) => { if (i > 5) { m.position.y = -60; return; } walkRoad(m, -8 + lt * 1.3 - i * 1.5, -2.4, t + i); });
  const lp = Z.roadAt(xs[0] + lt * 3.2); light(0, 'trail', lp.x + 5, 1.4, lp.z, 18, 0xfff0b0, 16); light(1, 'trail', 6, 6, 4, 14, 0xffa070, 40);
  const p0 = Z.roadAt(4); ct('trail', lt, d, [p0.x + 2, .9, p0.z + 6, p0.x - 14, 1.6, p0.z], [p0.x + 1, .9, p0.z + 5.5, p0.x - 10, 1.6, p0.z], [40, 40]); };
// 32 jets_trail
SHOTS[32] = (t, lt, d) => { trailLook('day'); const p0 = Z.roadAt(0);
  U.trucks.forEach((tr, i) => { if (i) { tr.position.y = -60; return; } const p = Z.roadAt(-6), q = Z.roadAt(-5); at(tr, p.x, 0, p.z, -Math.atan2(q.z - p.z, q.x - p.x)); });
  U.tJets.forEach((j, i) => { const tt = lt + .4 - i * .45, x = -95 + tt * 48; const p = Z.roadAt(clamp(x, -290, 290)); at(j, x, 17 + i * 4 - Math.sin(clamp(tt / 2.8) * Math.PI) * 5, p.z + (i ? 4 : -2)); j.rotation.set(0, 0, -.12 + clamp(tt / 2.8) * .2); });
  const BX = [-16, -9.5, -5.2]; U.tBlasts.forEach((b, i) => { const p = Z.roadAt(BX[i]); b.position.set(p.x, 1.2, p.z + (i === 2 ? 2.2 : (i ? -2.6 : 2.4))); b.userData.update(lt - 1.5 - i * .32, wp('trail', p.x, 1.2, p.z)); });
  const tp = Z.roadAt(-6); if (lt > 2.2) { U.tFire.position.set(tp.x, 1.6, tp.z); U.tFire.userData.update(t); U.tsmoke[0].visible = true; U.tsmoke[0].userData.update(t, wp('trail', tp.x, 2.4, tp.z)); } else U.tFire.position.y = -60;
  light(0, 'trail', p0.x, 6, p0.z + 4, 25, 0xfff0d8, 40); if (lt > 1.5) light(1, 'trail', tp.x, 2, tp.z + 2, 40 * clamp(1 - (lt - 1.5) / 2), 0xffa050, 20);
  ct('trail', lt, d, [p0.x + 12, 1.6, p0.z + 7, p0.x - 12, 7, p0.z], [p0.x + 11.5, 1.6, p0.z + 7, p0.x - 12, 6, p0.z], [50, 50], lt > 1.5 && lt < 2.8 ? .05 : 0); };

// 33 jets_north: Plain of Jars
SHOTS[33] = (t, lt, d) => { show('jars'); look('day', [0xd0d8d0, .0015], 1.5, 2.4, 0xfff0d8, [-60, 70, 40], [6000, 0, 6000]);
  U.jJets.forEach((j, i) => { at(j, -90 + lt * 45 - i * 16, 20 + i * 5, -36 - i * 10); j.rotation.set(0, 0, -.08); }); U.jBlasts.forEach((b, i) => { const x = -26 + i * 15, z = -44 - (i % 2) * 10; b.position.set(x, 1, z); b.userData.update(lt - 1.2 - i * .45, wp('jars', x, 1, z)); });
  ct('jars', lt, d, [6, 1.6, 22, -4, 9, -40], [3, 1.7, 20, -6, 9, -40], [46, 46]); overlay(c => L.caption(c, 'THE PLAIN OF JARS', 'NORTHERN LAOS', fade(lt, d))); };

// 34 planner_map
SHOTS[34] = (t, lt, d) => { show('ops'); look('night', null, .6, .3, 0xfff0dc, [-10, 30, 10], [3000, 0, 6000]); light(0, 'ops', 0, 2.5, 0, 22, 0xfff0d0, 8); light(1, 'ops', 3, 2.6, 3, 6, 0x9ab0d0, 12);
  U.officers.forEach((m, i) => { const a = [[-2.5, .5], [2.5, .3], [-1.2, -1.75], [1.1, -1.75]][i]; at(m, a[0], 0, a[1], facing([-a[0], -a[1]])); pose(m, t + i, { armR: i === 2 ? .9 : .1, elR: i === 2 ? .4 : .1, nod: -.35 }); });
  const pr = U.opsMapPr, toTable = (lo, la) => { const [x, y] = pr(lo, la); return [(x / L.W - .5) * 4, (y / L.H - .5) * 2.25]; };
  const pts = [[106.2, 16.7], [105.9, 17.6], [106.8, 14.8], [103.2, 19.45], [104.2, 20.4], [106.5, 15.9], [102.6, 19.8], [105.6, 16.4], [103.8, 18.6], [107.1, 14.1]];
  U.pins.forEach((p, i) => { const [x, z] = toTable(...pts[i]); const k = clamp((lt - .5 - i * .35) / .2); p.position.set(x, .88 + (1 - k) * .3, z); if (k <= 0) p.position.y = -60; });
  ct('ops', lt, d, [1.0, 3.0, 4.6, 0, 1.05, -.6], [.6, 2.85, 4.2, 0, 1.05, -.6], [44, 44]);
  overlay(c => { const tags = [['SUPPLY ROUTES', 1.2], ['TROOP POSITIONS', 2.4], ['STRATEGIC TARGETS', 3.6]]; tags.forEach(([s, t0], i) => tag(c, s, 90, 150 + i * 64, 34, fade(lt - t0, d - t0, .3), '#f2e8d2', 'left')); }); };

// 35 village_reveal: from target grid to homes
SHOTS[35] = (t, lt, d) => { villageLook('day', [0xd8e0d8, .0015]); const F = U.fam; const k = ease(clamp(lt / (d - .8)));
  U.farmers.forEach((m, i) => { at(m, -30 + ((lt * 1.2 + i * 9) % 60), .2, 18 + (i % 3), facing([1, 0])); pose(m, t + i, { walk: true }); });
  [['dad', -10, 0], ['mum', -9, 1.2], ['boy', -8.2, .4], ['girl', 4, -6], ['gran', 5, -5.4]].forEach(([n, x, z], i) => { at(F[n], x, 0, z, facing([0, 1])); pose(F[n], t + i, {}); });
  ct('village', 0, 1, [lerp(0, 4, k), lerp(220, 4, k), lerp(2, 34, k), 0, 0, lerp(0, 0, k)], [lerp(0, 4, k), lerp(220, 4, k), lerp(2, 34, k), 0, 0, 0], [lerp(36, 46, k), lerp(36, 46, k)]);
  overlay(c => { const a = 1 - clamp((lt - 1.2) / 1.4); if (a <= 0) return; c.save(); c.globalAlpha = a; c.strokeStyle = 'rgba(30,20,10,.7)'; c.lineWidth = 2; for (let x = 0; x < L.W; x += 120) { c.beginPath(); c.moveTo(x, 0); c.lineTo(x, L.H); c.stroke(); } for (let y = 0; y < L.H; y += 120) { c.beginPath(); c.moveTo(0, y); c.lineTo(L.W, y); c.stroke(); }
    c.strokeStyle = '#c8241c'; c.lineWidth = 6; c.beginPath(); c.arc(L.W / 2, L.H / 2, 90, 0, 7); c.moveTo(L.W / 2 - 130, L.H / 2); c.lineTo(L.W / 2 + 130, L.H / 2); c.moveTo(L.W / 2, L.H / 2 - 130); c.lineTo(L.W / 2, L.H / 2 + 130); c.stroke(); M.label(c, 'TARGET AREA', L.W / 2, L.H / 2 - 150, 30, '#c8241c', 1); c.restore(); }); };
// 36 missions
SHOTS[36] = (t, lt, d) => { show('sky'); look('day', [0xc8d8e8, .0005], 1.5, 2.4, 0xfff0d8, [-300, 300, 200], [12000, 0, 0]); hide(U.b52s, U.cans); U.fall.forEach(b => b.position.y = -60); U.bomblets.count = 0; U.sBlasts.forEach(b => b.userData.update(-1));
  U.sJets.forEach((j, i) => { const x = -400 + lt * 160 - i * 30 + (i % 2) * 60; at(j, x, 560 + i * 20, -200 + i * 110); j.rotation.set(0, (i % 2 ? .3 : -.2), 0); const c = U.contrails[i]; const len = 400; c.scale.set(len, 1, 1); c.position.set(x - len / 2 - 7, 560 + i * 20, -200 + i * 110); c.rotation.set(0, (i % 2 ? .3 : -.2), Math.PI / 2); });
  U.contrails.forEach((c, i) => { if (i > 3) c.position.y = -60; });
  ct('sky', lt, d, [0, 20, 400, 0, 500, -100], [0, 20, 400, 30, 520, -100], [50, 50]);
  overlay(c => { const g = c.createLinearGradient(0, 640, 0, 1000); g.addColorStop(0, 'rgba(10,8,6,0)'); g.addColorStop(.3, `rgba(10,8,6,${.62 * clamp(lt / .35)})`); g.addColorStop(1, `rgba(10,8,6,${.62 * clamp(lt / .35)})`); c.fillStyle = g; c.fillRect(0, 640, L.W, 440); LM.counter(c, lt, 580000, 'BOMBING MISSIONS OVER LAOS', '1964 – 1973', { bg: false, suffix: '+', size: 130, y: 260 }); }); };
// 37 clock
SHOTS[37] = (t, lt, d) => { OV.noGL = true; overlay(c => LM.clock(c, lt, d)); };
// 38-40 averages vs concentration
SHOTS[38] = (t, lt, d) => { OV.noGL = true; overlay(c => { const pr = LM.view(104, 18, 10.5); LM.base(c, pr, { hl: [['Laos', '#d8c8a0']] }); LM.clipLaos(c, pr, () => LM.bombDots(c, pr, 1, { even: 1, col: 'rgba(120,110,100,.8)', r: 3 })); M.label(c, 'AN AVERAGE...', L.W / 2, L.H - 90, 44, '#f2e8d2', clamp(lt / .4)); M.vignette(c, .5); }); };
SHOTS[39] = (t, lt, d) => { OV.noGL = true; overlay(c => { const pr = LM.view(104, 18, 10.5); LM.base(c, pr, { hl: [['Laos', '#d8c8a0']] }); LM.clipLaos(c, pr, () => LM.bombDots(c, pr, 1, { even: 1, col: `rgba(120,110,100,${.8 - .4 * clamp(lt / d)})`, r: 3 })); M.label(c, 'NOT A STEADY RHYTHM', L.W / 2, L.H - 90, 44, '#f2e8d2', clamp(lt / .4)); M.vignette(c, .5); }); };
SHOTS[40] = (t, lt, d) => { OV.noGL = true; overlay(c => { const pr = LM.view(104, 18, 10.5); LM.base(c, pr, { hl: [['Laos', '#d8c8a0']] }); const e = 1 - ease(clamp(lt / 2.2)); LM.clipLaos(c, pr, () => LM.bombDots(c, pr, 1, { even: e, r: 3.4 }));
  const a = clamp((lt - 2.4) / .5); callout(c, pr, 'XIENG KHOUANG', 99.6, 18.6, 102.6, 19.3, a); callout(c, pr, 'THE TRAIL', 108.9, 17.4, 106.3, 16.3, a); callout(c, pr, 'HOUAPHAN', 101.6, 21.9, 103.8, 20.4, a); M.label(c, 'CONCENTRATED, AND DEVASTATING', L.W / 2, L.H - 90, 44, '#f2e8d2', clamp((lt - 2.2) / .4)); M.vignette(c, .5); }); };
// 41 ruined_home
function famStand(t, x, z, dir = [0, 1]) { const F = U.fam; [['dad', 0, 0], ['mum', 1, .3], ['gran', -1.1, .5], ['boy', .5, 1], ['girl', 1.6, .9]].forEach(([n, dx, dz], i) => { at(F[n], x + dx, 0, z + dz, facing(dir)); pose(F[n], t + i, {}); }); }
SHOTS[41] = (t, lt, d) => { villageLook('smoke', [0x8a7a6a, .004], 1.1, 1.3, 0xffc898); U.houses[1].position.y = -60; U.ruin2.position.y = 0; U.rFire.userData.update(t); U.rFire2.userData.update(t + 1.3);
  U.vsmoke[0].visible = true; U.vsmoke[0].userData.update(t, V3(3002, 2, -14)); famStand(t, 0, -5, [0, -1]); X.act(U.fam.mum, t, 'carry'); light(0, 'village', 2.6, 2.4, -11.5, 30, 0xff8a40, 16);
  ct('village', lt, d, [6, 1.6, 3, 1, 1.6, -12], [5, 1.5, 1.8, 1, 1.6, -12], [40, 38]); };
// 42-45 rebuild
function hammer(m, t) { const r = m.userData.rig, k = Math.pow(Math.abs(Math.sin(t * 2.6)), .6); r.arms[0].sh.rotation.z = 1.0 + k * 1.3; r.arms[0].el.rotation.z = .25 + k * .5; r.arms[1].sh.rotation.z = 1.45; r.arms[1].el.rotation.z = .25; r.head.rotation.z = .1; }
SHOTS[42] = (t, lt, d) => { villageLook('day'); U.houses[1].position.y = -60; U.newPosts.position.set(2, 0, -11); U.rebuild.position.y = 0; const F = U.fam;
  at(F.dad, 2, 0, -7.95, facing([0, -1])); pose(F.dad, t, {}); U.mallet.visible = true; hammer(F.dad, t); ct('village', lt, d, [5.2, 1.5, -4.6, 2, 1.2, -8.6], [4.9, 1.5, -4.9, 2, 1.2, -8.6], [38, 36]); };
SHOTS[43] = (t, lt, d) => { villageLook('day'); U.craters.forEach(c => c.position.copy(c.userData.home)); const F = U.fam; at(F.mum, 9.5, .1, 23.5, facing([1, .2])); pose(F.mum, t, {}); X.act(F.mum, t, 'dig', { rate: 2.5 }); U.seedlings.visible = true;
  ct('village', lt, d, [7.4, 1.35, 27.8, 9.8, .55, 23.6], [7.8, 1.25, 27.3, 9.8, .5, 23.6], [38, 36]); };
SHOTS[44] = (t, lt, d) => { villageLook('day'); const F = U.fam; const x = -14 + lt * 1.4; at(F.girl, x, .3, 25, facing([1, 0])); pose(F.girl, t, { walk: true, speed: 5, armR: -.2, elR: 2.4, armL: -.2, elL: 2.4 }); U.buckets.position.set(x + .05, 1.25, 25); U.buckets.rotation.y = 0; if (!U.buckets.parent) SETS.village.add(U.buckets);
  at(F.gran, -4, 0, 18, facing([.3, 1])); pose(F.gran, t, {}); at(F.boy, -3.3, 0, 18.6, facing([-.5, 1])); pose(F.boy, t, {});
  ct('village', lt, d, [-6, 1.4, 34, -8, 1, 24], [-3, 1.4, 34, -5, 1, 24], [40, 40]); };
SHOTS[45] = (t, lt, d) => { villageLook('dusk', [0xb89080, .003], 1.5, 1.9, 0xffb080, [-100, 18, -60]); U.houses[1].position.y = -60; U.newPosts.position.set(2, 0, -11); U.rebuild.position.y = 0; famStand(t, 7.5, 7, [-.3, -1]);
  U.vsmoke.forEach((s, i) => { s.visible = true; s.userData.update(t + i * 2, V3(3000 - 120 + i * 120, 0, -260)); });
  light(0, 'village', 8, 3, 10, 18, 0xffc090, 16); ct('village', lt, d, [9.6, 1.5, 13.4, 6, 1.7, 0], [9.4, 1.55, 12.6, 6, 1.9, 0], [42, 42]); };
