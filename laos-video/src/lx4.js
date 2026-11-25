// ===================== LAOS 4: cluster bombs and the danger that stayed (cues 79-106) =====================
import * as L from './lib3.js';
import * as M from './maps.js';
import * as X from './lao.js';
import * as LM from './laomaps.js';
import * as Z from './laosets.js';
const { THREE, cam, U, V3, at, lerp, clamp, ease, look, show, fx, overlay, OV, pose, facing, SETS } = L;
const { ct, wp, light, hide } = Z;
export const RANGE = { from: 79, to: 106 };
export const SHOTS = {};
const fade = (lt, d, a = .4) => clamp(lt / a) * (1 - clamp((lt - d + a) / a));
const headPos = m => { const p = V3(); m.updateMatrixWorld(true); m.userData.rig.head.getWorldPosition(p); return p; };
const D = new THREE.Object3D();
export async function build() { Z.skies(); Z.skySet(); Z.villageSet(); Z.cliffSet(); Z.schoolSet();
  U.vJet = X.jet(); SETS.village.add(U.vJet); U.cJets = [0, 1].map(() => { const j = X.jet({ bombs: false }); SETS.cliff.add(j); return j; });
  U.hand = L.hand(.5); U.hand.children[0].material = L.mat(0x3a4a5a, .9); U.hand.traverse(m => { if (m.isMesh && m !== U.hand.children[0]) m.material = L.mat(0xb8845a, .6); }); SETS.village.add(U.hand);
  U.casing = X.bombBody(1.8, 0x6a5a40); SETS.village.add(U.casing); U.soil = L.mesh(new THREE.SphereGeometry(.6, 14, 6, 0, Math.PI * 2, 0, Math.PI / 2), L.mat(0x6a5a40, 1)); U.soil.scale.y = .25; SETS.village.add(U.soil);
  U.tufts = [...Array(14)].map((_, i) => { const t = L.mesh(new THREE.ConeGeometry(.02, .18, 4), L.mat(0x6a9a3a, .9)); SETS.village.add(t); return t; });
  U.poster = L.plate(1.1, .8, X.TT(['DON\'T TOUCH', '', 'TELL AN ADULT'], { w: 512, h: 380, size: 52, bg: '#f2ead8', fg: '#a8241c', draw: (x) => { x.fillStyle = '#6a6a3a'; x.beginPath(); x.arc(256, 190, 40, 0, 7); x.fill(); x.strokeStyle = '#c8241c'; x.lineWidth = 10; x.beginPath(); x.arc(256, 190, 62, 0, 7); x.moveTo(212, 146); x.lineTo(300, 234); x.stroke(); } }), SETS.school, [0, -60, 0]);
  U.detMan = X.villager({ seed: 3001, shirt: 0x5a4a3a, lower: 0x2a2a28, detector: true, longSleeve: true }); SETS.village.add(U.detMan);
}
function villageLook(sky = 'day', fog = [0xd8e0d8, .002], hemi = 1.5, sun = 2.4, sunCol = 0xfff0dc, sunPos = [-60, 70, 40]) { show('village'); look(sky, fog, hemi, sun, sunCol, sunPos, [3000, 0, 0]);
  hide(U.ruin, U.newPosts, U.warn, U.plot, U.scale, U.scrap, U.vStakes, U.vBombies, U.craters, Object.values(U.fam), U.farmers, U.buckets, U.vJet, U.hand, U.casing, U.soil, U.tufts, U.detMan); U.vfire.position.y = -60; }
function skyLook(sky = 'day') { show('sky'); look(sky, [0xc8d8e0, .0006], 1.5, 2.4, 0xfff0d8, [-300, 300, 200], [12000, 0, 0]); hide(U.b52s, U.cans, U.sJets); U.fall.forEach(b => b.position.y = -60); U.bomblets.count = 0; U.contrails.forEach(c => c.position.y = -60); U.sBlasts.forEach(b => b.userData.update(-1)); }
// bomblet swarm from a canister opened at (x0,y0,z0) at time t0 (seconds); local to sky set
function swarm(lt, t0, o, n = 400, spread = 1) { const tt = lt - t0; if (tt < 0) { U.bomblets.count = 0; return; } U.bomblets.count = n;
  for (let i = 0; i < n; i++) { const r = L.rng(i + 7), a = r() * 6.28, sp = (2 + r() * 10) * spread, up = r() * 2; const x = o[0] + o[3] * tt + Math.cos(a) * sp * tt, y = o[1] + up * tt - 4.9 * tt * tt * .6, z = o[2] + Math.sin(a) * sp * tt;
    D.position.set(x, Math.max(.3, y), z); D.rotation.set(tt * 8 + i, tt * 5, 0); D.scale.setScalar(1); D.updateMatrix(); U.bomblets.setMatrixAt(i, D.matrix); } U.bomblets.instanceMatrix.needsUpdate = true; }
// 79 cluster_drop
SHOTS[79] = (t, lt, d) => { skyLook('day'); const j = U.sJets[0]; const x = -160 + lt * 70; at(j, x, 230, 0); j.rotation.set(0, 0, -.04);
  U.cans.forEach((c, i) => { const tt = lt - 3.2 - i * .6; if (tt < 0) { c.position.y = -60; return; } c.position.set(x - 2 - tt * 8 - i * 4, 228 - 4.9 * tt * tt * .5, (i - .5) * 4); c.rotation.set(0, 0, -Math.min(.8, tt * .3)); c.userData.halves.forEach(h => h.rotation.set(0, 0, 0)); });
  ct('sky', lt, d, [x - 40, 236, 26, x, 226, 0], [x - 30, 234, 22, x, 222, 0], [44, 44]); overlay(c => L.caption(c, 'CLUSTER BOMBS', '', fade(lt, d))); };
// 80 cluster_open
SHOTS[80] = (t, lt, d) => { skyLook('day'); const c = U.cans[0]; U.cans[1].position.y = -60; const y = 200 - lt * 3; c.position.set(0, y, 0); c.rotation.set(0, 0, -.6); const op = ease(clamp((lt - .8) / .8)); c.userData.halves[0].rotation.x = op * 1.4; c.userData.halves[1].rotation.x = -op * 1.4;
  swarm(lt, 1.1, [0, y, 0, -1.5], 360, .45);
  ct('sky', lt, d, [10, y + 3, 9, 0, y - 1, 0], [11, y + 1, 10, 0, y - 4, 0], [44, 48]); };
// 81 counter: the rain seen from the ground
SHOTS[81] = (t, lt, d) => { skyLook('day'); swarm(lt + 1.2, 0, [24, 40, 30, 0], 400, .5);
  ct('sky', lt, d, [30, 2, 60, 22, 26, 30], [30, 2, 60, 22, 20, 30], [50, 50]); overlay(c => LM.counter(c, lt, 270000000, 'SUBMUNITIONS DROPPED ON LAOS', '', { bg: false, size: 120, y: 280 })); };
// 82-84 the grid of millions
function grid(c, lt, hi, cleared = 0, msg = []) { c.fillStyle = '#1a1612'; c.fillRect(0, 0, L.W, L.H); const cols = 27, rows = 10, s = 52, x0 = (L.W - cols * s) / 2 + s / 2, y0 = 230;
  for (let i = 0; i < 270; i++) { const cx = x0 + (i % cols) * s, cy = y0 + Math.floor(i / cols) * s; const isHi = i % 27 < 8 && i < 270; const hiK = clamp((lt - .3 - (i % 27) * .02) / .4) * hi;
    let col = '#6a6458'; if (isHi) { const cl = cleared > 0 && ((i * 37) % 100) / 100 < cleared; col = cl ? '#9ab890' : `rgb(${lerp(106, 232, hiK) | 0},${lerp(100, 110, hiK) | 0},${lerp(88, 40, hiK) | 0})`; }
    c.fillStyle = col; c.beginPath(); c.arc(cx, cy, 17, 0, 7); c.fill(); }
  M.label(c, 'EACH DOT = 1 MILLION', L.W / 2, 170, 26, '#bfb4a0', 1); msg.forEach(([s, size, col], i) => M.label(c, s, L.W / 2, 860 + i * 60, size, col, clamp(lt / .4))); M.vignette(c, .4); }
SHOTS[82] = (t, lt, d) => { OV.noGL = true; overlay(c => grid(c, lt, 1, 0, [['80,000,000 FAILED TO DETONATE', 50, '#f2a050']])); };
SHOTS[83] = (t, lt, d) => { OV.noGL = true; overlay(c => grid(c, lt + 5, 1, 0, [['THE SCALE OF CONTAMINATION', 44, '#f2e8d2'], ['LEFT AFTER THE CAMPAIGN', 32, '#d8c8a8']])); };
SHOTS[84] = (t, lt, d) => { OV.noGL = true; overlay(c => grid(c, lt + 5, 1, clamp(lt / 2.4) * .5, [['NOT A COUNT OF WHAT REMAINS TODAY', 44, '#f2e8d2'], ['GREEN: CLEARED OR DESTROYED SINCE', 28, '#9ab890']])); };
// 85-87 the bombie stays
function bombieSoil(x, z, k = 1) { const b = U.vBombies[0]; at(b, x, .1, z); b.scale.setScalar(1.9); U.soil.position.set(x, .0, z); U.soil.scale.set(.45, .1, .45); U.tufts.forEach((tf, i) => { const a = i * 2.4; tf.position.set(x + Math.cos(a) * (.14 + (i % 3) * .05), .14, z + Math.sin(a) * (.14 + (i % 3) * .05)); tf.scale.setScalar(.3 + k * .9 * ((i % 4) / 4 + .5)); }); }
SHOTS[85] = (t, lt, d) => { const k = clamp(lt / d); villageLook(k < .5 ? 'day' : 'dusk', [0xd8e0d8, .003], 1.5 - k * .4, 2.4 - k, k < .5 ? 0xfff0dc : 0xffb080, [-60, 70 - k * 50, 40]); bombieSoil(-8, 8, k);
  ct('village', lt, d, [-7.2, .4, 8.9, -8, .1, 8], [-7.35, .35, 8.75, -8, .1, 8], [34, 30]); };
SHOTS[86] = (t, lt, d) => { villageLook('day'); bombieSoil(-8, 8, 1); at(U.farmers[0], 10, .1, 26, facing([0, 1])); pose(U.farmers[0], t, {}); X.act(U.farmers[0], t, 'dig', { rate: 2 });
  ct('village', lt, d, [-8.6, .35, 7.3, 2, .6, 26], [-8.6, .38, 7.2, 3, .6, 26], [40, 40]); };
SHOTS[87] = (t, lt, d) => { villageLook('day'); bombieSoil(-3.4, 14.4, 1); const F = U.fam; [F.dad, F.mum, F.girl].forEach((m, i) => { at(m, -12 + lt * 1.4 + i * 1.5, 0, 14 + (i % 2) * .5, facing([1, 0])); pose(m, t + i, { walk: true }); });
  const k = ease(clamp(lt / d)); ct('village', 0, 1, [-1, lerp(1.6, .3, k), 16.5, -3.4, lerp(1, .12, k), 14.4], [-1, lerp(1.6, .3, k), 16.5, -3.4, lerp(1, .12, k), 14.4], [40, 36]); };
// 88 sky_clear: 1973
SHOTS[88] = (t, lt, d) => { show('cliff'); look('day', [0xc8d0d0, .002], 1.5, 2.4, 0xfff0d8, [-80, 60, 80], [6000, 0, 0]); hide(U.bearers); U.stretcher.position.y = -60; U.lamp.position.y = -60;
  if (lt < 3.4) { U.cJets.forEach((j, i) => { at(j, 40 + lt * 60 + i * 12, 70 + lt * 8 + i * 4, -60 - lt * 30, -.4); }); U.cPeople.forEach(m => m.position.y = -60); ct('cliff', lt, 3.4, [8, 1.6, 30, 30, 50, -60], [8, 1.6, 30, 50, 60, -80], [46, 46]); }
  else { U.cJets.forEach(j => j.position.y = -60); const q = lt - 3.4; U.cPeople.forEach((m, i) => { const p = clamp((q - i * .25) / 3.2); at(m, 8 + (i % 3 - 1) * .7, 0, lerp(-24, -12, p) - (i % 4) * .4, facing([0, 1])); pose(m, t + i, { walk: p > 0 && p < 1 }); if (p <= 0) m.position.y = -60; });
    ct('cliff', q, d - 3.4, [14, 1.8, 0, 8, 1.6, -20], [13, 1.8, -2, 8, 1.6, -20], [42, 42]); }
  overlay(c => L.caption(c, '1973', 'THE BOMBING STOPS', fade(lt, d))); };
// 89 return_land
SHOTS[89] = (t, lt, d) => { villageLook('morning'); U.houses.forEach((h, i) => { if (i === 1 || i === 3) h.position.y = -60; }); U.ruin.position.set(2, 0, -14);
  const W = [...U.farmers.slice(0, 4), U.fam.mum, U.fam.boy]; W.forEach((m, i) => { at(m, -40 + lt * 1.6 + i * 1.6, .3, 25, facing([1, 0])); pose(m, t + i, { walk: true }); X.act(m, t, 'carry'); });
  ct('village', lt, d, [-20, 2, 40, -30, 1.2, 25], [-16, 2, 40, -26, 1.2, 25], [42, 42]); };
// 90 hoe_strike
SHOTS[90] = (t, lt, d) => { villageLook('day'); const m = U.farmers[0]; at(m, 8, .1, 22, facing([-1, 0])); pose(m, t, {}); X.act(m, t * 1.2, 'dig', { rate: 3 }); const b = U.vBombies[1]; at(b, 6.9, .1, 22); b.scale.setScalar(1.4);
  ct('village', lt, d, [6.2, .3, 23.2, 7.4, .5, 22], [6.4, .28, 23.0, 7.4, .5, 22], [44, 42]);
  overlay(c => { if (lt > d - .35) { c.fillStyle = '#000'; c.fillRect(0, 0, L.W, L.H); } }); };
// 91 child_find
SHOTS[91] = (t, lt, d) => { villageLook('day'); const k = U.fam.boy; at(k, -2, 0, 12, facing([0, 1])); pose(k, t, {}); X.act(k, t, 'crouch'); const b = U.vBombies[2]; b.scale.setScalar(1.6);
  const up = clamp((lt - .8) / 1); const hp = headPos(k); b.position.set(lerp(-1.7, hp.x - 3000 + .18, up), lerp(.05, hp.y - .3, up), lerp(12.35, hp.z + .05, up));
  ct('village', lt, d, [-.4, .8, 13.6, -1.9, .5, 12.1], [-.6, .75, 13.3, -1.9, .55, 12.1], [38, 36]); };
// 92 house_plan
SHOTS[92] = (t, lt, d) => { villageLook('day'); U.plot.position.set(30, 0, 18); const F = U.fam; at(F.dad, 28, 0, 15.6, facing([.2, 1])); pose(F.dad, t, {}); if (lt > 2) X.act(F.dad, t, 'lookDown'); at(F.mum, 32.5, 0, 16, facing([-.4, 1])); pose(F.mum, t, {}); at(F.girl, 33.2, 0, 15.2, facing([-.5, 1])); pose(F.girl, t, {});
  ct('village', lt, d, [24, 2.4, 26, 30, .6, 17], [25, 2.0, 24, 30, .6, 17], [40, 40]); };
// 93-95 sky to ground
SHOTS[93] = (t, lt, d) => { villageLook('day'); const k = ease(clamp(lt / d)); ct('village', 0, 1, [0, 1.6, 20, 0, lerp(40, -4, k), lerp(-20, 14, k)], [0, 1.6, 20, 0, lerp(40, -4, k), lerp(-20, 14, k)], [46, 46]); };
SHOTS[94] = (t, lt, d) => { villageLook('day'); const F = U.fam; ['dad', 'mum', 'gran', 'boy', 'girl'].forEach((n, i) => { at(F[n], -11 + i * .9, 0, 1 + (i % 2) * .6, facing([.2, 1])); pose(F[n], t + i, {}); X.act(F[n], t, 'lookUp'); });
  at(U.vJet, 120 - lt * 90, 36, -30, Math.PI); ct('village', lt, d, [-8, .8, 6, -9, 3, -2], [-8.4, .8, 5.6, -9, 3.4, -2], [44, 44]);
  overlay(c => { c.globalCompositeOperation = 'color'; c.fillStyle = 'rgba(150,120,80,.85)'; c.fillRect(0, 0, L.W, L.H); c.globalCompositeOperation = 'source-over'; M.label(c, 'THEN', 140, 120, 40, '#fff4e0', fade(lt, d, .2)); }); };
SHOTS[95] = (t, lt, d) => { villageLook('day'); const F = U.fam; ['dad', 'mum', 'girl'].forEach((n, i) => { at(F[n], -10 + lt * .8 + i * 1.3, 0, 14 + i * .4, facing([1, 0])); pose(F[n], t + i, { walk: true, speed: 4 }); X.act(F[n], t, 'lookDown'); });
  ct('village', lt, d, [-2, 1.2, 18, -7, .8, 14], [-1, 1.2, 18, -5.5, .8, 14], [40, 40]); overlay(c => M.label(c, 'NOW', 140, 120, 40, '#fff4e0', fade(lt, d, .2))); };
// 96-97 need land
function workPaddy(t) { U.farmers.forEach((m, i) => { at(m, -14 + i * 5.2, .1, 28 + (i % 3) * 2.2, facing([0, 1])); pose(m, t + i, {}); X.act(m, t * .7 + i, 'dig', { rate: 2.4 }); }); }
SHOTS[96] = (t, lt, d) => { villageLook('day'); workPaddy(t); ct('village', lt, d, [30, 8, 60, 0, 1, 30], [26, 7, 56, 0, 1, 30], [44, 44]); };
SHOTS[97] = (t, lt, d) => { villageLook('day'); workPaddy(t); const m = U.farmers[1]; const h = headPos(m); ct('village', lt, d, [h.x - 3000 + 2.2, 1.1, h.z + 1.6, h.x - 3000, .5, h.z + .2], [h.x - 3000 + 2.0, 1.05, h.z + 1.5, h.x - 3000, .5, h.z + .2], [38, 36]); };
// 98-99 poverty and risk
function stakeLine(x0, z0, n = 10) { U.vStakes.forEach((s, i) => { if (i >= n) { s.position.y = -60; return; } at(s, x0 + i * 1.6, 0, z0 + Math.sin(i) * .3); s.scale.setScalar(1.6); }); U.warn.position.set(x0 - 1, 0, z0); }
SHOTS[98] = (t, lt, d) => { villageLook('day'); stakeLine(-20, 18); const F = U.fam; ['dad', 'mum', 'boy'].forEach((n, i) => { at(F[n], 10 + i * .9, 0, -2 + (i % 2) * .5, facing([0, 1])); pose(F[n], t + i, {}); }); X.act(F.mum, t, 'carry');
  OV.split = [() => ct('village', lt, d, [-14, 1.4, 25, -14, .8, 18], [-13.6, 1.4, 24.6, -14, .8, 18], [40, 40]), () => ct('village', lt, d, [11, 1.5, 3.6, 11, 1.1, -1.6], [11, 1.5, 3.3, 11, 1.1, -1.6], [40, 40])];
  overlay(c => { M.label(c, 'DANGEROUS LAND', L.W / 4, L.H - 80, 38, '#ffe8c0', fade(lt, d)); M.label(c, 'NEEDED LAND', L.W * 3 / 4, L.H - 80, 38, '#ffe8c0', fade(lt, d)); }); };
SHOTS[99] = (t, lt, d) => { villageLook('day'); stakeLine(-20, 18); const m = U.fam.dad; const st = clamp((lt - 2.6) / 1.6); at(m, -12, 0, 16 - st * 3.2, facing([0, 1])); pose(m, t, { walk: st > 0 && st < 1 }); if (lt < 2.6) X.act(m, t, 'lookDown');
  ct('village', lt, d, [-9.6, 1.3, 12.6, -12, 1, 17], [-9.9, 1.3, 12.9, -12, 1, 17], [40, 40]); };
// 100-103 scrap
SHOTS[100] = (t, lt, d) => { villageLook('day'); U.scrap.position.set(6, 0, 4); ct('village', lt, d, [9, 1.6, 7, 6, .5, 4], [8.4, 1.4, 6.6, 6, .5, 4], [40, 38]); overlay(c => L.caption(c, 'SCRAP METAL', '', fade(lt, d))); };
SHOTS[101] = (t, lt, d) => { villageLook('day'); U.scrap.position.set(6, 0, 4); U.scale.position.set(8, 0, 2.2); const F = U.fam; at(F.dad, 8, 0, 3.4, facing([0, -1])); pose(F.dad, t, {}); X.act(F.dad, t, 'carry'); at(U.farmers[1], 8.6, 0, 1.2, facing([-.3, 1])); pose(U.farmers[1], t, { armR: .9, elR: .4 });
  U.casing.position.set(8, .95, 2.2); U.casing.rotation.set(0, .4, 0); U.casing.scale.setScalar(.6); ct('village', lt, d, [11, 1.6, 4.4, 8, .9, 2.4], [10.6, 1.5, 4.2, 8, .9, 2.4], [40, 38]); };
SHOTS[102] = (t, lt, d) => { villageLook('day'); const m = U.detMan; const x = 40 - lt * .9; at(m, x, 0, -22, facing([-1, 0])); pose(m, t, { walk: true, speed: 3 }); X.act(m, t, 'sweep');
  [U.fam.boy, U.fam.girl].forEach((k, i) => { at(k, x + 2.2 + i * 1.2, 0, -21.5 + i * .6, facing([-1, 0])); pose(k, t + i, { walk: true, speed: 4 }); });
  ct('village', lt, d, [x + 2, 1.5, -14, x - 1, 1, -22], [x + 1, 1.5, -14.5, x - 2, 1, -22], [40, 38]); };
SHOTS[103] = (t, lt, d) => { villageLook('day'); U.casing.scale.setScalar(1); U.casing.position.set(-5, .05, 8); U.casing.rotation.set(0, .5, .1); U.soil.position.set(-5, .02, 8); U.soil.scale.set(1.4, .2, .8);
  const k = ease(clamp(lt / (d - 1))); U.hand.position.set(-5 + .9 - k * .6, .55 - k * .35, 8.4 - k * .25); U.hand.rotation.set(0, 0, 2.3);
  ct('village', lt, d, [-3.8, .7, 9.6, -5, .2, 8], [-3.9, .6, 9.4, -5, .2, 8], [38, 34]); overlay(c => { const a = clamp((lt - d + 1.4) / 1.2); c.fillStyle = `rgba(0,0,0,${a})`; c.fillRect(0, 0, L.W, L.H); }); };
// 104-105 the next generation
SHOTS[104] = (t, lt, d) => { villageLook('morning'); const F = U.fam; at(F.gran, -4, 0, 4, facing([.3, 1])); pose(F.gran, t, {}); X.act(F.gran, t, 'lookUp'); at(F.girl, -3.2, 0, 4.4, facing([.3, 1])); pose(F.girl, t, {}); X.act(F.girl, t, 'lookDown');
  ct('village', lt, d, [-1.6, 1.1, 7.4, -3.6, 1, 4.2], [-1.9, 1.1, 7.1, -3.6, 1, 4.2], [40, 38]); };
SHOTS[105] = (t, lt, d) => { villageLook('day'); const K = [U.fam.boy, U.fam.girl]; if (!U.kidsV) { U.kidsV = [0, 1].map(i => { const k = X.villager({ seed: 3100 + i, child: true, shirt: [0x8ab0d0, 0xd8a040][i], lower: 0x2a2a3a, shorts: true, barefoot: true }); SETS.village.add(k); return k; }); }
  const all = K.concat(U.kidsV); const b = U.vBombies[3]; at(b, 14, .05, 8); b.scale.setScalar(1.4); all.forEach((k, i) => { const a = i / 4 * 6.28 + .4; const p = clamp((lt - .5 - i * .3) / 1.4); at(k, 14 + Math.cos(a) * lerp(4, .8, p), 0, 8 + Math.sin(a) * lerp(4, .8, p), facing([-Math.cos(a), -Math.sin(a)])); pose(k, t + i, { walk: p < 1, run: true }); if (p >= 1) X.act(k, t, 'crouch'); });
  ct('village', lt, d, [18, 2.4, 13, 14, .3, 8], [17.4, 2.0, 12.4, 14, .3, 8], [40, 40]); };
// 106 risk_class: outdoor lesson at a school
SHOTS[106] = (t, lt, d) => { show('school'); look('day', [0xd8e0e0, .0016], 1.5, 2.4, 0xfff0d8, [-60, 70, 50], [0, 0, 0]); hide(U.team, U.parents, U.moto); U.schStakes.forEach(s => s.position.y = -60); U.schBombie.position.y = -60; U.ball.position.y = -60;
  U.kids.forEach((k, i) => { if (i > 9) { k.position.y = -60; return; } at(k, -3 + (i % 5) * 1.2, 0, 6 + Math.floor(i / 5) * 1.2, facing([0, -1])); pose(k, t + i, { sit: true }); if (i === 3 && lt > 1.6) { k.userData.rig.arms[1].sh.rotation.z = -2.8; } });
  at(U.teacher, -.6, 0, 3, facing([0, 1])); pose(U.teacher, t, { armR: 1.2, elR: .6, armL: 1.2, elL: .6 }); U.poster.position.set(-.6, 1.35, 3.6);
  ct('school', lt, d, [3.4, 1.4, 10.8, -.6, 1.1, 3.6], [3, 1.4, 10.2, -.6, 1.1, 3.6], [40, 38]); overlay(c => L.caption(c, 'RISK EDUCATION', 'TEACHING CHILDREN ABOUT THE WAR', fade(lt, d))); };

// ===================== REVIEW FIXES (overrides) =====================
const NEW = {};
function initFix() { if (NEW.done) return; NEW.done = true;
  U.bomblets.frustumCulled = false;
  NEW.civ = [...Array(7)].map((_, i) => { const m = X.villager({ seed: 3200 + i, skirt: i % 2 === 0, bun: i % 2 === 0, hat: i % 3 === 1 ? 'conical' : 'none', basket: i % 3 === 2, longSleeve: i % 2 === 1, child: i === 5 }); SETS.cliff.add(m); return m; });
  NEW.easel = new THREE.Group(); for (const s of [-1, 1]) L.mesh(new THREE.BoxGeometry(.05, 1.7, .05), L.mat(0x6a4a2a, .9), [s * .45, .85, 0], [-.12, 0, s * .1], NEW.easel); L.mesh(new THREE.BoxGeometry(.05, 1.6, .05), L.mat(0x6a4a2a, .9), [0, .8, -.35], [.3, 0, 0], NEW.easel); SETS.school.add(NEW.easel); NEW.easel.position.y = -60;
  NEW.scrapBit = X.bombBody(.9, 0x6a5a40); SETS.village.add(NEW.scrapBit); NEW.scrapBit.position.y = -60;
}
function vLook(...a) { initFix(); villageLook(...a); if (U.kidsV) U.kidsV.forEach(k => k.position.y = -60); NEW.scrapBit.position.y = -60; }
const handsMid = m => { m.updateMatrixWorld(true); const a = V3(), b = V3(); m.userData.rig.arms[0].hand.getWorldPosition(a); m.userData.rig.arms[1].hand.getWorldPosition(b); return a.add(b).multiplyScalar(.5); };
// swarm with explicit size scale
function swarm2(lt, t0, o, n, spread, sc) { swarm(lt, t0, o, n, spread); if (U.bomblets.count) { for (let i = 0; i < U.bomblets.count; i++) { U.bomblets.getMatrixAt(i, D.matrix); D.matrix.decompose(D.position, D.quaternion, D.scale); D.scale.setScalar(sc); D.updateMatrix(); U.bomblets.setMatrixAt(i, D.matrix); } U.bomblets.instanceMatrix.needsUpdate = true; } }
// 79: reset canister halves
const S79 = SHOTS[79]; SHOTS[79] = (t, lt, d) => { initFix(); U.cans.forEach(c => c.userData.halves.forEach(h => { h.position.set(0, 0, 0); h.rotation.set(0, 0, 0); })); S79(t, lt, d); };
// 80 cluster_open: the clamshell splits and bomblets pour out
SHOTS[80] = (t, lt, d) => { initFix(); skyLook('day'); const c = U.cans[0]; U.cans[1].position.y = -60; const y = 200 - lt * 2.2; c.position.set(0, y, 0); c.rotation.set(0, 0, -.35); const op = ease(clamp((lt - .7) / .9));
  c.userData.halves[0].position.set(0, op * .35, 0); c.userData.halves[0].rotation.set(op * .6, 0, 0); c.userData.halves[1].position.set(0, -op * .35, 0); c.userData.halves[1].rotation.set(-op * .6, 0, 0);
  { const tt = lt - 1.0; if (tt < 0) U.bomblets.count = 0; else { U.bomblets.count = 300; for (let i = 0; i < 300; i++) { const r = L.rng(i + 7), a = r() * 6.28, sp = .6 + r() * 2.6, along = (r() - .5) * 2.6; D.position.set(along - 1.2 * tt * .2, y - 2.0 * tt - .25 * tt * tt * (.5 + r()) , Math.sin(a) * sp * tt); D.position.y += Math.cos(a) * sp * tt * .5; D.rotation.set(tt * 6 + i, tt * 4, 0); D.scale.setScalar(.9); D.updateMatrix(); U.bomblets.setMatrixAt(i, D.matrix); } U.bomblets.instanceMatrix.needsUpdate = true; } }
  ct('sky', lt, d, [7, y + 1.5, 7, 0, y - .6, 0], [8, y + .2, 8, 0, y - 2.6, 0], [40, 46]); overlay(c2 => L.caption(c2, 'SUBMUNITIONS', 'HUNDREDS IN EACH CANISTER', fade(lt, d))); };
// 81 counter: readable band
SHOTS[81] = (t, lt, d) => { initFix(); skyLook('day'); swarm2(lt + 1.2, 0, [24, 40, 30, 0], 400, .5, 1.6);
  ct('sky', lt, d, [30, 2, 60, 22, 26, 30], [30, 2, 60, 22, 20, 30], [50, 50]);
  overlay(c => { const g = c.createLinearGradient(0, L.H - 380, 0, L.H); g.addColorStop(0, 'rgba(10,8,6,0)'); g.addColorStop(.35, 'rgba(10,8,6,.7)'); g.addColorStop(1, 'rgba(10,8,6,.85)'); c.fillStyle = g; c.fillRect(0, L.H - 380, L.W, 380); LM.counter(c, lt, 270000000, 'SUBMUNITIONS DROPPED ON LAOS', '', { bg: false, size: 120, y: 280 }); }); };
// 86: bombie clearly framed
SHOTS[86] = (t, lt, d) => { vLook('day'); bombieSoil(-8, 8, .6); at(U.farmers[0], 10, -.12, 26, facing([0, 1])); pose(U.farmers[0], t, {}); X.act(U.farmers[0], t, 'dig', { rate: 2 });
  ct('village', lt, d, [-8.9, .55, 6.9, -5, .2, 13], [-8.95, .58, 6.85, -4.6, .2, 13], [40, 40]); };
// 87 bombie_path: walkers' feet pass a visible bombie in the yard
SHOTS[87] = (t, lt, d) => { vLook('day'); bombieSoil(-3, 10, .5); U.vBombies[0].scale.setScalar(2.1); const F = U.fam; [F.dad, F.mum, F.girl].forEach((m, i) => { at(m, -12 + lt * 1.4 + i * 2.2, 0, 8.6 - (i % 2) * .6, facing([1, 0])); pose(m, t + i, { walk: true }); });
  const k = ease(clamp(lt / d)); ct('village', 0, 1, [-1, lerp(1.0, .35, k), 13.4, -3, lerp(.6, .1, k), 10], [-1, lerp(1.0, .35, k), 13.4, -3, lerp(.6, .1, k), 10], [lerp(44, 34, k), lerp(44, 34, k)]); };
// 88 sky_clear: the last jets leave; civilians step out into the light
SHOTS[88] = (t, lt, d) => { initFix(); show('cliff'); look('day', [0xc8d0d0, .002], 1.5, 2.4, 0xfff0d8, [-80, 60, 80], [6000, 0, 0]); hide(U.bearers, U.cPeople); U.stretcher.position.y = -60; U.lamp.position.y = -60; NEW.civ.forEach(m => m.position.y = -60);
  if (lt < 3.4) { U.cJets.forEach((j, i) => { at(j, 4 + i * 14, 55 + lt * 9 + i * 5, 10 + lt * 60 + i * 10, -Math.PI / 2); j.rotation.z = .08; }); ct('cliff', lt, 3.4, [8, 1.6, -6, 8, 30, 120], [8, 1.6, -6, 8, 36, 160], [50, 50]); }
  else { U.cJets.forEach(j => j.position.y = -60); const q = lt - 3.4; NEW.civ.forEach((m, i) => { const p = clamp((q - i * .3) / 3.2); at(m, 8 + (i % 3 - 1) * .8, 0, lerp(-24.2, -13, p) - (i % 4) * .5, facing([0, 1])); pose(m, t + i, { walk: p > 0 && p < 1 }); if (p <= 0) m.position.y = -60; });
    ct('cliff', q, d - 3.4, [14, 1.8, -8, 8, 1.6, -20], [13, 1.8, -10, 8, 1.6, -20], [42, 42]); }
  overlay(c => L.caption(c, '1973', 'THE BOMBING STOPS', fade(lt, d))); };
// 90 hoe_strike: on dry ground, the hoe comes down beside the half-buried bombie
SHOTS[90] = (t, lt, d) => { vLook('day'); const m = U.farmers[0]; at(m, 10, 0, 56, facing([-1, 0])); pose(m, t, {}); const ph = Math.min(lt, d - .5); X.act(m, ph * 1.0, 'dig', { rate: 3.2 });
  const b = U.vBombies[1]; at(b, 8.7, .03, 56.1); b.scale.setScalar(2.2); U.soil.position.set(8.7, 0, 56.1); U.soil.scale.set(.5, .08, .5);
  ct('village', lt, d, [9.2, 1.1, 59.6, 9.3, .9, 56], [9.1, 1.05, 59.3, 9.3, .85, 56], [44, 42]); };
// 91 child_find: feet on the ground, object in the hands
SHOTS[91] = (t, lt, d) => { vLook('day'); const k = U.fam.boy; at(k, -2, 0, 54, facing([0, 1])); pose(k, t, {}); X.act(k, t, 'crouch'); const r = k.userData.rig; r.pelvis.position.y = .3; r.spine.position.y = .3; r.spine.rotation.z = -.25;
  const up = ease(clamp((lt - .9) / 1)); r.arms[0].sh.rotation.z = lerp(1.0, .9, up); r.arms[1].sh.rotation.z = lerp(1.0, .9, up); r.arms[0].el.rotation.z = lerp(.4, 1.3, up); r.arms[1].el.rotation.z = lerp(.4, 1.3, up); r.arms[0].sh.rotation.x = .25; r.arms[1].sh.rotation.x = -.25;
  const b = U.vBombies[2]; b.scale.setScalar(1.7); const hm = handsMid(k); const grd = V3(3000 - 2, .05, 54.42); const p = up > 0 ? hm.lerp(grd, 0) : grd; if (up <= 0) b.position.set(-2, .05, 54.42); else b.position.set(hm.x - 3000, hm.y, hm.z);
  ct('village', lt, d, [-.6, .75, 55.6, -2, .45, 54.2], [-.75, .72, 55.45, -2, .5, 54.2], [38, 36]); };
// 93 danger_moves: from the sky down to a bombie in the yard
SHOTS[93] = (t, lt, d) => { vLook('day'); bombieSoil(-3, 7, .6); const k = ease(clamp(lt / d)); ct('village', 0, 1, [-3, 1.5, 4.2, -3, lerp(40, .05, k), lerp(40, 7, k)], [-3, 1.5, 4.2, -3, lerp(40, .05, k), lerp(40, 7, k)], [46, 40]); };
// 94 look_up: faces lit from the camera side, heads up
SHOTS[94] = (t, lt, d) => { vLook('day', [0xd8e0d8, .002], 1.7, 2.6, 0xfff0dc, [-20, 60, 70]); const F = U.fam; ['dad', 'mum', 'gran', 'boy', 'girl'].forEach((n, i) => { at(F[n], -11.4 + i * 1.1, 0, 1 + (i % 2) * .7, facing([.15, 1])); pose(F[n], t + i, {}); F[n].userData.rig.head.rotation.z = .5; F[n].userData.rig.neck.rotation.z = .12; });
  at(U.vJet, 120 - lt * 90, 36, -30, Math.PI); ct('village', lt, d, [-8.2, 1.0, 6.4, -9, 2.2, 0], [-8.5, 1.0, 6.0, -9, 2.4, 0], [44, 44]);
  overlay(c => { c.globalCompositeOperation = 'color'; c.fillStyle = 'rgba(150,120,80,.85)'; c.fillRect(0, 0, L.W, L.H); c.globalCompositeOperation = 'source-over'; M.label(c, 'THEN', 140, 120, 40, '#fff4e0', fade(lt, d, .2)); }); };
// 95 look_down: spaced, clearly looking at the ground
SHOTS[95] = (t, lt, d) => { vLook('day'); const F = U.fam; ['dad', 'mum', 'girl'].forEach((n, i) => { at(F[n], -11 + lt * .7 + i * 2.4, 0, 11 + (i % 2) * .6, facing([1, 0])); pose(F[n], t + i, { walk: true, speed: 3.5 }); const r = F[n].userData.rig; r.head.rotation.z = -.75; r.spine.rotation.z = -.25; });
  ct('village', lt, d, [-5.5, 1.4, 17.5, -7.6, .8, 11.2], [-5, 1.4, 17.5, -6.8, .8, 11.2], [44, 44]); overlay(c => M.label(c, 'NOW', 140, 120, 40, '#fff4e0', fade(lt, d, .2))); };
// 96-97 farmers stand IN the paddy water
function workPaddy2(t) { U.farmers.forEach((m, i) => { at(m, -14 + i * 5.2, -.14, 28 + (i % 3) * 2.2, facing([0, 1])); pose(m, t + i, {}); X.act(m, t * .7 + i, 'dig', { rate: 2.4 }); }); }
SHOTS[96] = (t, lt, d) => { vLook('day'); workPaddy2(t); ct('village', lt, d, [30, 8, 60, 0, 1, 30], [26, 7, 56, 0, 1, 30], [44, 44]); };
SHOTS[97] = (t, lt, d) => { vLook('day'); workPaddy2(t); const m = U.farmers[1]; const h = headPos(m); const x = h.x - 3000, z = h.z; ct('village', lt, d, [x + 2.2, 1.7, z + 2.6, x + .1, .6, z + .3], [x + 2.05, 1.65, z + 2.45, x + .1, .6, z + .3], [42, 40]); };
// 98-99 danger on dry land beyond the paddies
function stakeLine2(z0, x0 = -16, n = 12) { U.vStakes.forEach((s, i) => { if (i >= n) { s.position.y = -60; return; } at(s, x0 + i * 1.5, 0, z0 + Math.sin(i * 1.7) * .25); s.scale.setScalar(1.6); }); U.warn.position.set(x0 - 1.2, 0, z0); }
SHOTS[98] = (t, lt, d) => { vLook('day'); stakeLine2(54); const F = U.fam; ['dad', 'mum', 'boy'].forEach((n, i) => { at(F[n], 10 + i * 1.1, 0, -2 + (i % 2) * .5, facing([0, 1])); pose(F[n], t + i, {}); }); X.act(F.mum, t, 'carry');
  OV.split = [() => ct('village', lt, d, [-6, 1.5, 62, -6, .8, 54], [-6.3, 1.5, 61.6, -6, .8, 54], [40, 40]), () => ct('village', lt, d, [11, 1.5, 3.6, 11, 1.1, -1.6], [11, 1.5, 3.3, 11, 1.1, -1.6], [40, 40])];
  overlay(c => { M.label(c, 'DANGEROUS LAND', L.W / 4, L.H - 80, 38, '#ffe8c0', fade(lt, d)); M.label(c, 'NEEDED LAND', L.W * 3 / 4, L.H - 80, 38, '#ffe8c0', fade(lt, d)); }); };
SHOTS[99] = (t, lt, d) => { vLook('day'); stakeLine2(54); const m = U.fam.dad; const st = clamp((lt - 2.6) / 1.8); at(m, -7.3, 0, 51.6 + st * 4.4, facing([0, 1])); pose(m, t, { walk: st > 0 && st < 1 }); if (lt < 2.6) { m.userData.rig.head.rotation.z = -.5; }
  ct('village', lt, d, [-2.2, 1.5, 48.2, -7.4, 1, 54], [-2.4, 1.5, 48.0, -7.4, 1, 54.6], [42, 42]); };
// 102 scrap_search: detector sweeping low, in the open field, metal ahead
SHOTS[102] = (t, lt, d) => { vLook('day'); const m = U.detMan; const x = 22 - lt * .8; at(m, x, 0, 60, facing([-1, 0])); pose(m, t, { walk: true, speed: 3 }); const r = m.userData.rig; r.arms[1].sh.rotation.z = .35; r.arms[1].el.rotation.z = .15; r.arms[1].sh.rotation.x = -.15 - Math.sin(t * 2.2) * .35; r.head.rotation.z = -.4;
  [U.fam.boy, U.fam.girl].forEach((k, i) => { at(k, x + 2.6 + i * 1.4, 0, 60.6 + i * .7, facing([-1, 0])); pose(k, t + i, { walk: true, speed: 4 }); });
  NEW.scrapBit.position.set(12.5, .06, 60.2); NEW.scrapBit.rotation.set(0, .6, .08);
  ct('village', lt, d, [x + 1.2, 1.4, 66, x - 1.4, .8, 60], [x + .4, 1.4, 66, x - 2.2, .8, 60], [44, 44]); };
// 103 scrap_hand: the hand stops just above the casing
SHOTS[103] = (t, lt, d) => { vLook('day'); U.casing.scale.setScalar(1); U.casing.position.set(-5, .05, 8); U.casing.rotation.set(0, .5, .1); U.soil.position.set(-5, .02, 8); U.soil.scale.set(1.4, .2, .8);
  const k = ease(clamp(lt / (d - 1.2))); U.hand.position.set(-5 + .9 - k * .7, .62 - k * .2, 8.4 - k * .25); U.hand.rotation.set(0, 0, 2.3);
  ct('village', lt, d, [-3.8, .75, 9.6, -5, .25, 8], [-3.9, .68, 9.4, -5, .25, 8], [38, 34]); overlay(c => { const a = clamp((lt - d + .9) / .9) * .85; c.fillStyle = `rgba(0,0,0,${a})`; c.fillRect(0, 0, L.W, L.H); }); };
// 104 generation: faces visible, separated
SHOTS[104] = (t, lt, d) => { vLook('morning'); const F = U.fam; at(F.gran, -4.4, 0, 4, facing([.55, 1])); pose(F.gran, t, {}); F.gran.userData.rig.head.rotation.z = .28; at(F.girl, -2.9, 0, 4.3, facing([.1, 1])); pose(F.girl, t, {}); X.act(F.girl, t, 'lookDown');
  ct('village', lt, d, [-1.6, 1.25, 7.6, -3.7, 1.05, 4.1], [-1.85, 1.25, 7.3, -3.7, 1.05, 4.1], [40, 38]); };
// 105 generation:2: children in a ring around a visible object
SHOTS[105] = (t, lt, d) => { vLook('day'); const K = [U.fam.boy, U.fam.girl]; if (!U.kidsV) { U.kidsV = [0, 1].map(i => { const k = X.villager({ seed: 3100 + i, child: true, shirt: [0x8ab0d0, 0xd8a040][i], lower: 0x2a2a3a, shorts: true, barefoot: true }); SETS.village.add(k); return k; }); }
  const all = K.concat(U.kidsV); const b = U.vBombies[3]; at(b, 14, .06, 8); b.scale.setScalar(2.6);
  all.forEach((k, i) => { const a = i / 4 * 6.28 + .4; const p = clamp((lt - .3 - i * .25) / 1.3); const rr = lerp(3.2, 1.15, p); at(k, 14 + Math.cos(a) * rr, 0, 8 + Math.sin(a) * rr, facing([-Math.cos(a), -Math.sin(a)])); pose(k, t + i, { walk: p < 1, run: true }); if (p >= 1) { X.act(k, t, 'crouch'); k.userData.rig.pelvis.position.y = .3; k.userData.rig.spine.position.y = .3; } });
  ct('village', lt, d, [18.6, 2.6, 13.6, 14, .3, 8], [18.2, 2.4, 13.2, 14, .3, 8], [44, 44]); };
// 106 risk_class: poster on an easel beside the teacher
SHOTS[106] = (t, lt, d) => { initFix(); show('school'); look('day', [0xd8e0e0, .0016], 1.5, 2.4, 0xfff0d8, [-60, 70, 50], [0, 0, 0]); hide(U.team, U.parents, U.moto); U.schStakes.forEach(s => s.position.y = -60); U.schBombie.position.y = -60; U.ball.position.y = -60;
  U.kids.forEach((k, i) => { if (i > 9) { k.position.y = -60; return; } at(k, -2.6 + (i % 5) * 1.25, 0, 6.2 + Math.floor(i / 5) * 1.3, facing([0, -1])); pose(k, t + i, {}); X.act(k, t + i, 'floorSit'); if (i === 3 && lt > 1.4) { k.userData.rig.arms[1].sh.rotation.z = -2.8; } });
  at(U.teacher, -1.3, 0, 3.4, facing([.3, 1])); pose(U.teacher, t, {}); X.act(U.teacher, t, 'teach'); NEW.easel.position.set(.4, 0, 3.0); NEW.easel.rotation.y = -.15; U.poster.position.set(.4, 1.45, 3.08); U.poster.rotation.set(-.12, -.15, 0);
  ct('school', lt, d, [1.2, 1.25, 9.6, -.3, 1.15, 3.2], [1.0, 1.25, 9.0, -.3, 1.15, 3.2], [40, 38]); overlay(c => L.caption(c, 'RISK EDUCATION', 'TEACHING CHILDREN ABOUT THE WAR', fade(lt, d))); };

// ===================== QA fixes round 3 (section 4) =====================
const back4 = (c, x, y, w, h, a = .55) => { c.save(); c.fillStyle = `rgba(10,8,6,${a})`; c.fillRect(x, y, w, h); c.restore(); };
const capB4 = (c, s1, s2, a) => { if (a <= 0) return; back4(c, 0, L.H - 170, 1100, 130, .55 * a); L.caption(c, s1, s2, a); };
const Q = {};
function initQ() { initFix(); if (Q.done) return; Q.done = true;
  // poster: icon between the two lines, nothing overlapping
  U.poster.material.map = L.textTex([['DON\'T TOUCH', 56, 78], ['TELL AN ADULT', 56, 350]], { w: 512, h: 380, bg: '#f2ead8', fg: '#a8241c', draw: (x) => { x.fillStyle = '#6a6a3a'; x.beginPath(); x.ellipse(256, 212, 46, 30, 0, 0, 7); x.fill(); x.strokeStyle = '#c8241c'; x.lineWidth = 11; x.beginPath(); x.arc(256, 212, 74, 0, 7); x.moveTo(204, 160); x.lineTo(308, 264); x.stroke(); } });
  U.poster.material.needsUpdate = true;
  // a settled scrap pile: tarp, bombs lying side by side, pipes and flat plates
  const g = new THREE.Group(), ms = [L.mat(0x5a5e4a, .5, .6), L.mat(0x6a5a44, .6, .5), L.mat(0x4a4a44, .5, .6)];
  L.mesh(new THREE.BoxGeometry(3.4, .02, 2.4), L.mat(0x4a3a2a, 1), [0, .01, 0], [0, 0, 0], g);
  const lay = (len, x, y, z, ry, axisAligned) => { const b = X.bombBody(len, [0x5a6248, 0x6a5a40, 0x4e5442][Math.floor(Math.abs(x * 7 + z * 3)) % 3]); b.position.set(x, y, z); b.rotation.set(axisAligned ? 0 : Math.PI / 4, ry, 0); g.add(b); return b; };
  // bottom row: 4 bombs (len 1.4, radius .168) lying parallel, fins diagonal so they rest on the tarp
  const len = 1.4, rr = len * .12, y0 = .02 + rr * 1.14;
  for (let i = 0; i < 4; i++) lay(len, (i % 2) * .25 - .3, y0, -.75 + i * .42, i % 2 ? Math.PI : 0, false);
  // second row nested in the grooves, fins axis aligned so the lower fin drops between the bombs
  for (let i = 0; i < 3; i++) lay(len, (i % 2) * .25 - .1, y0 + .28, -.54 + i * .42, i % 2 ? 0 : Math.PI, true);
  // pipes and plates flat on the tarp in front
  for (let i = 0; i < 4; i++) L.mesh(new THREE.CylinderGeometry(.07, .07, .9 + i * .12, 10), ms[i % 3], [1.25 + (i % 2) * .05, .09, -.7 + i * .2], [0, i * .15, Math.PI / 2], g).rotation.set(Math.PI / 2, 0, i * .15 + Math.PI / 2);
  for (let i = 0; i < 3; i++) L.mesh(new THREE.BoxGeometry(.7 - i * .12, .04, .5 - i * .06), ms[(i + 1) % 3], [-.2 + i * .05, .04 + i * .04, .95], [0, i * .3, 0], g);
  L.mesh(new THREE.BoxGeometry(.5, .04, .4), ms[2], [1.3, .04, .7], [0, .5, 0], g);
  g.traverse(m => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } });
  SETS.village.add(g); g.position.y = -60; Q.pile = g;
}
const vLookQ = (...a) => { initQ(); vLook(...a); Q.pile.position.y = -60; };
// level the conical hat in world space and lift the head so the face shows
function levelHat(m) { const h = m.userData.rig.head; h.children.forEach(c => { if (c.geometry && c.geometry.type === 'ConeGeometry') { m.updateMatrixWorld(true); const q = new THREE.Quaternion(); h.getWorldQuaternion(q); c.quaternion.copy(q.invert()); c.position.set(0, .16, 0); } }); }
// 88: empty, quiet sky - no aircraft under "the bombing stops"
const S88q = SHOTS[88]; SHOTS[88] = (t, lt, d) => { S88q(t, lt, d); U.cJets.forEach(j => j.position.y = -60); };
// 90: hat seated level, face visible
const S90q = SHOTS[90]; SHOTS[90] = (t, lt, d) => { initQ(); Q.pile.position.y = -60; S90q(t, lt, d); const m = U.farmers[0]; m.userData.rig.head.rotation.z = .38; levelHat(m); };
// 96/97: same hat fix for the paddy farmers
for (const k of [96, 97]) { const S = SHOTS[k]; SHOTS[k] = (t, lt, d) => { initQ(); Q.pile.position.y = -60; S(t, lt, d); U.farmers.forEach(m => { m.userData.rig.head.rotation.z = .3; levelHat(m); }); }; }
// 92: the house plot on dry ground beyond the paddies
SHOTS[92] = (t, lt, d) => { vLookQ('day'); U.plot.position.set(18, 0, 60); const F = U.fam; at(F.dad, 15.6, 0, 57.8, facing([.3, 1])); pose(F.dad, t, {}); if (lt > 2) X.act(F.dad, t, 'lookDown'); at(F.mum, 20.6, 0, 57.9, facing([-.4, 1])); pose(F.mum, t, {}); at(F.girl, 21.4, 0, 57.2, facing([-.5, 1])); pose(F.girl, t, {});
  ct('village', lt, d, [12, 2.4, 52, 18, .6, 59.5], [13, 2.0, 53.5, 18, .6, 59.5], [40, 40]); };
// 99: he walks up to the stake line and stops short of it
SHOTS[99] = (t, lt, d) => { vLookQ('day'); stakeLine2(54); const m = U.fam.dad; const st = ease(clamp((lt - 2.6) / 1.8)); at(m, -7.8, 0, 51.4 + st * 1.3, facing([0, 1])); pose(m, t, { walk: st > 0 && st < 1 }); if (lt < 2.6 || st >= 1) { m.userData.rig.head.rotation.z = -.5; }
  ct('village', lt, d, [-2.2, 1.5, 48.2, -7.4, 1, 54], [-2.4, 1.5, 48.0, -7.4, 1, 54.6], [42, 42]); };
// 100: settled scrap pile
SHOTS[100] = (t, lt, d) => { vLookQ('day'); U.scrap.position.y = -60; Q.pile.position.set(6, 0, 4); Q.pile.rotation.y = .3; ct('village', lt, d, [9, 1.6, 7, 6, .4, 4], [8.4, 1.4, 6.6, 6, .4, 4], [40, 38]); overlay(c => capB4(c, 'SCRAP METAL', '', fade(lt, d))); };
// 106: plated lower-third
const S106q = SHOTS[106]; SHOTS[106] = (t, lt, d) => { initQ(); S106q(t, lt, d); OV.list.pop(); overlay(c => capB4(c, 'RISK EDUCATION', 'TEACHING CHILDREN ABOUT THE WAR', fade(lt, d))); };
// any village shot hides the new pile unless it places it
{ const VL = villageLook; villageLook = (...a) => { VL(...a); if (Q.pile) Q.pile.position.y = -60; }; }
