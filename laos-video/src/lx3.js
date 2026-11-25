// ===================== LAOS 3: Viengxay, life inside the mountains (cues 46-78) =====================
import * as L from './lib3.js';
import * as M from './maps.js';
import * as X from './lao.js';
import * as LM from './laomaps.js';
import * as Z from './laosets.js';
import * as P from './props.js';
const { THREE, cam, U, V3, at, lerp, clamp, ease, look, show, fx, overlay, OV, pose, facing, SETS } = L;
const { ct, wp, light, hide } = Z;
export const RANGE = { from: 46, to: 78 };
export const SHOTS = {};
const fade = (lt, d, a = .4) => clamp(lt / a) * (1 - clamp((lt - d + a) / a));
const headPos = m => { const p = V3(); m.updateMatrixWorld(true); m.userData.rig.head.getWorldPosition(p); return p; };
export async function build() { Z.skies(); Z.cliffSet(); Z.caveSet(); Z.villageSet();
  U.cJet = X.jet(); SETS.cliff.add(U.cJet); U.cBlasts = [0, 1, 2].map(() => { const b = L.blast({ size: 10 }); SETS.cliff.add(b); return b; });
  U.dust = fx(L.smoke(V3(), { n: 40, color: 0xa89878, wind: [0, 0], rise: -2.6, size: .12, grow: 1.2, life: 1.4, opacity: .9 }));
  U.poles = [0, 1, 2].map(() => { const p = L.mesh(new THREE.CylinderGeometry(.05, .05, 4, 6), L.mat(0x9a8a50, .9)); p.rotation.z = Math.PI / 2; SETS.cave.add(p); return p; });
  U.water = L.mesh(new THREE.CylinderGeometry(.16, .12, .35, 12), L.mat(0x8a6a44, .8)); SETS.cliff.add(U.water);
  // fixes: bedroll in the family chamber, chairs in the office, extra patients in the ward
  U.bedroll = new THREE.Group(); L.mesh(new THREE.BoxGeometry(1.4, .07, .66), L.mat(0xc8b89a, .95), [0, .035, 0], [0, 0, 0], U.bedroll); L.mesh(new THREE.BoxGeometry(.3, .1, .4), L.mat(0xe8e0d0, .95), [-.5, .1, 0], [0, 0, 0], U.bedroll); L.mesh(new THREE.BoxGeometry(.75, .06, .62), L.mat(0x8a4a3a, .95), [.25, .1, 0], [0, 0, 0], U.bedroll);
  at(U.bedroll, 2.4, 0, .5); U.cRooms.family.add(U.bedroll);
  U.offChairs = [[-.4, 1.0], [.8, 1.0]].map(([x, z]) => { const c = P.chair(); at(c, x, 0, z, Math.PI / 2); U.cRooms.office.add(c); return c; });
  U.patients2 = [...Array(5)].map((_, i) => { const m = X.villager({ seed: 1240 + i, longSleeve: true, shirt: [0x6a7a6a, 0x8a6a5a, 0x5a6a7a][i % 3] }); U.cRooms.ward.add(m); return m; });
  U.wStool = P.chair(); U.cRooms.street.add(U.wStool);
  U.gapK = X.karst(175, 75, 731); at(U.gapK, 40, -3, 235, 2.2); SETS.cliff.add(U.gapK);
}
// readable text with a dark backing
function tag(c, s, x, y, size = 40, col = '#fff4e0', a = 1, align = 'center') { if (a <= 0) return; c.save(); c.font = `700 ${size}px Cinzel, serif`; const w = c.measureText(s).width; const x0 = align === 'center' ? x - w / 2 : align === 'right' ? x - w : x;
  c.globalAlpha = a * .62; c.fillStyle = '#0c0806'; c.fillRect(x0 - size * .5, y - size * 1.0, w + size, size * 1.45); c.restore(); M.label(c, s, x, y, size, col, a, align); }
function topTitle(c, s1, s2, a) { if (a <= 0) return; c.save(); c.globalAlpha = a * .6; c.fillStyle = '#0c0806'; c.fillRect(0, 40, 980, s2 ? 140 : 90); c.restore(); M.label(c, s1, 70, 100, 46, '#f2e8d2', a, 'left'); if (s2) M.label(c, s2, 72, 150, 28, '#e8d8b8', a, 'left'); }
// cave mouth silhouette overlay (looking out from inside)
function arch(c, a = 1, o = {}) { c.save(); c.globalAlpha = a; c.fillStyle = o.col || '#0c0806'; c.beginPath(); c.rect(0, 0, L.W, L.H); const cx = L.W / 2 + (o.dx || 0), w = o.w || 760, h = o.h || 820; c.moveTo(cx - w, L.H);
  for (let i = 0; i <= 40; i++) { const t = i / 40, a2 = Math.PI * (1 - t); const r = 1 + .06 * Math.sin(i * 1.7) + .04 * Math.sin(i * 3.3); c.lineTo(cx + Math.cos(a2) * w * r, L.H - Math.sin(a2) * h * r); } c.lineTo(cx + w, L.H); c.closePath(); c.fill('evenodd'); c.restore(); }
const roomZ = { street: 0, class: 40, ward: 80, office: 120, theatre: 160, family: 200 };
function caveLook(room, warm = 1) { show('cave'); look('night', null, .32 * warm, 0, 0xfff0dc, [0, 60, 0], [0, 0, 3000], [0x8a6a4a, 0x2a1a10]); const z = roomZ[room];
  light(0, 'cave', -6, 2.6, z, 14 * warm, 0xffb060, 14); light(1, 'cave', 2, 2.6, z, 14 * warm, 0xffb060, 14); light(2, 'cave', 8, 2.6, z, 12 * warm, 0xffa050, 14); U.poles.forEach(p => p.position.y = -60); }
const rz = (room, x, y, z) => [x, y, z + roomZ[room]];
function cliffLook(sky = 'morning', fogA = .002) { show('cliff'); look(sky, [0xc8d0d0, fogA], 1.4, 2.2, 0xfff0d8, [-80, 60, 80], [6000, 0, 0]); hide(U.cPeople, U.bearers, U.cJet); U.stretcher.position.y = -60; U.lamp.position.y = -60; U.water.position.y = -60; U.cBlasts.forEach(b => b.userData.update(-1)); }
function villageNight(sky = 'night') { show('village'); look(sky, [0x0a1020, .003], .9, 1.1, 0x9ab0e0, [60, 80, 60], [3000, 0, 0]); hide(U.ruin, U.newPosts, U.warn, U.plot, U.scale, U.scrap, U.vStakes, U.vBombies, U.craters, Object.values(U.fam), U.buckets); U.vfire.position.y = -60; }
function farmers(t, z0 = 30) { U.farmers.forEach((m, i) => { at(m, -14 + i * 5.2, .1, z0 - 2 + (i % 3) * 2.2, facing([0, 1])); pose(m, t + i, {}); X.act(m, t * .6 + i, 'dig', { rate: 2 }); }); }
// 46 viengxay_map
SHOTS[46] = (t, lt, d) => { OV.noGL = true; overlay(c => { const pr = LM.viewLerp([104, 18, 11], [104.0, 20.2, 4.2], ease(clamp(lt / 3))); LM.base(c, pr, { hl: [['Laos', '#d8c8a0']] });
  const [vx, vy] = pr(...LM.CITY.Viengxay); for (let i = 0; i < 26; i++) { const r = M.mulberry(i + 3), a = r() * 6.28, dd = 30 + r() * 160; const x = vx + Math.cos(a) * dd * 1.4, y = vy + Math.sin(a) * dd; c.fillStyle = `rgba(90,110,70,${clamp((lt - 2) / .8)})`; c.beginPath(); c.moveTo(x - 14, y + 10); c.quadraticCurveTo(x, y - 34, x + 14, y + 10); c.fill(); }
  LM.city(c, pr, 'Viengxay', { a: clamp((lt - 1.8) / .4), size: 34 }); M.title(c, 'VIENGXAY', 'HOUAPHAN PROVINCE · NORTHEASTERN LAOS', clamp(lt / .5)); M.vignette(c, .5); }); };
// 47 karst
SHOTS[47] = (t, lt, d) => { cliffLook('morning', .004); ct('cliff', lt, d, [14, 5, 56, 5, 14, -26], [10, 4.4, 46, 5, 12, -26], [44, 42]); };
// 48 cave_enter
SHOTS[48] = (t, lt, d) => { cliffLook('morning'); const goal = V3(8, 0, -25.4);
  U.cPeople.forEach((m, i) => { const p = clamp((lt + 3.5 - i * .55) / 5.5); const x = lerp(12 + i * .4, goal.x, p), z = lerp(14, goal.z, p); at(m, x, 0, z, facing([goal.x - x, goal.z - z])); pose(m, t + i, { walk: true }); if (p >= 1) m.position.y = -60; });
  ct('cliff', lt, d, [16, 2.2, 12, 8, 2.4, -24], [12, 2, 2, 8, 2.4, -25], [40, 40]); overlay(c => L.caption(c, 'THE CAVES OF VIENGXAY', 'PATHET LAO HEADQUARTERS', fade(lt, d))); };
// 49 cave_city
SHOTS[49] = (t, lt, d) => { OV.noGL = true; overlay(c => { LM.cutaway(c, lt, { gap: .5 }); M.label(c, 'AN UNDERGROUND SETTLEMENT', L.W / 2, 90, 40, '#f2e8d2', clamp(lt / .5)); }); };
// 50 cave_rooms: dolly along the cave street
function streetPeople(t) { const P = U.stPeople; const spots = [[-24, -2.4, 'write'], [-12, -2.6, 'carry'], [0, -1.9, 'carry'], [10.5, -3, 'teach'], [24, -1.8, '']];
  P.forEach((m, i) => { if (i < 5) { const [x, z, k] = spots[i]; at(m, x + .6, 0, z, facing([0, -1])); pose(m, t + i, { write: k === 'write' }); if (k && k !== 'write') X.act(m, t + i, k); } else if (i < 8) { const x = -30 + ((t * 1.1 + i * 13) % 60); at(m, x, 0, -.2 + (i % 2) * .6, facing([1, 0])); pose(m, t + i, { walk: true }); } else { at(m, 12 + (i - 8) * .5 - 1, 0, -1.6 + (i % 2) * .8, facing([0, -1])); pose(m, t + i, { sit: true }); } }); }
SHOTS[50] = (t, lt, d) => { caveLook('street'); streetPeople(t); const x = lerp(-28, 26, ease(clamp(lt / d)));
  light(0, 'cave', x - 6, 2.8, -1, 16, 0xffb060, 14); light(1, 'cave', x + 2, 2.8, -1, 16, 0xffb060, 14); light(2, 'cave', x + 8, 2.8, -1, 14, 0xffa050, 14);
  ct('cave', 0, 1, [x - 2, 1.8, 4.6, x + 1, 1.2, -3.5], [x - 2, 1.8, 4.6, x + 1, 1.2, -3.5], [48, 48]);
  overlay(c => { const lbl = [['OFFICES', -24], ['SHOPS', -12], ['A BAKERY', 0], ['A SCHOOL', 12], ['A HOSPITAL', 24]]; lbl.forEach(([s, px]) => { const a = clamp(1 - Math.abs(x + 1 - px) / 5); if (a > 0) M.label(c, s, L.W / 2, L.H - 100, 48, '#ffe8c0', a); }); }); };
// 51 cave_theatre
SHOTS[51] = (t, lt, d) => { caveLook('theatre', 1.1); light(0, 'cave', 8, 3.4, 160, 30, 0xfff0d0, 10); U.actors.forEach((m, i) => { pose(m, t + i, { armR: 1.0 + Math.sin(t * 2 + i) * .5, elR: .3 }); }); U.audience.forEach((m, i) => pose(m, t + i, { sit: true }));
  ct('cave', lt, d, rz('theatre', -6, 2.4, 2.5).concat(rz('theatre', 9, 1.8, 0)), rz('theatre', -5, 2.3, 2.2).concat(rz('theatre', 9, 1.8, 0)), [44, 42]); overlay(c => M.label(c, 'EVEN A THEATRE', L.W / 2, L.H - 100, 44, '#ffe8c0', fade(lt, d, .3))); };
// 52 cave_office
function officeScene(t) { U.officials.forEach((m, i) => { const p = [[-.4, .9], [.8, .9], [1.8, -2.6]][i]; at(m, p[0], 0, p[1] + 120 * 0, facing(i === 2 ? [-.3, -1] : [0, -1])); pose(m, t + i, { sit: i < 2, write: i === 0, point: i === 2, pointUp: .2 }); }); }
SHOTS[52] = (t, lt, d) => { caveLook('office'); light(0, 'cave', 0, 2.4, 121, 22, 0xffc070, 10); officeScene(t);
  ct('cave', lt, d, rz('office', 2.6, 1.7, 4.4).concat(rz('office', 0, 1.4, -2.5)), rz('office', 1.8, 1.6, 3.8).concat(rz('office', 0, 1.5, -2.5)), [42, 40]); };
// 53 cave_office:2 split
function famScene(t, k = 'sit') { const F = U.cFam; [[-.8, .4], [.8, .4], [-.3, 1.1], [.4, 1.2]].forEach(([x, z], i) => { at(F[i], x, 0, z, facing([-x, -z + .4])); pose(F[i], t + i, { sit: true }); }); }
SHOTS[53] = (t, lt, d) => { caveLook('office'); officeScene(t); famScene(t); light(0, 'cave', 0, 2.4, 121, 22, 0xffc070, 10); light(1, 'cave', .5, 1.2, 199.6, 14, 0xffa050, 8);
  OV.split = [() => ct('cave', lt, d, rz('office', 2.2, 1.6, 4).concat(rz('office', 0, 1.4, -2)), rz('office', 2, 1.6, 3.8).concat(rz('office', 0, 1.4, -2)), [44, 44]), () => ct('cave', lt, d, rz('family', 0, 1.4, 4).concat(rz('family', 0, .6, .4)), rz('family', 0, 1.3, 3.6).concat(rz('family', 0, .6, .4)), [44, 44])];
  overlay(c => { M.label(c, 'REVOLUTION', L.W / 4, L.H - 80, 38, '#ffe8c0', fade(lt, d)); M.label(c, 'SURVIVAL', L.W * 3 / 4, L.H - 80, 38, '#ffe8c0', fade(lt, d)); }); };
// 54 karst_jets: from inside a cave mouth
SHOTS[54] = (t, lt, d) => { cliffLook('day'); at(U.cJet, -200 + lt * 90, 60, 60, 0); U.cJet.rotation.z = -.15;
  U.cBlasts.forEach((b, i) => { b.position.set(-40 + i * 40, 30 + i * 6, 120 + i * 6); b.userData.update(lt - 1.8 - i * .5, wp('cliff', -40 + i * 40, 30, 120)); });
  ct('cliff', lt, d, [8, 1.8, -27.6, 6, 6, 40], [8, 1.8, -27.6, 4, 7, 40], [52, 52], lt > 1.8 && lt < 3.4 ? .03 : 0);
  overlay(c => { arch(c, 1, { w: 820, h: 860 }); if (lt > 1.8 && lt < 3.6) { c.fillStyle = `rgba(255,220,180,${.12 * Math.sin((lt - 1.8) * 6) ** 2})`; c.fillRect(0, 0, L.W, L.H); } }); };
// 55 cave_class
SHOTS[55] = (t, lt, d) => { caveLook('class', 1.1); light(0, 'cave', 4, 2.6, 40, 22, 0xffc070, 12); U.clKids.forEach((k, i) => pose(k, t + i, { sit: true })); pose(U.clTeacher, t, {}); X.act(U.clTeacher, t, 'teach');
  ct('cave', lt, d, rz('class', -5, 1.6, 2.4).concat(rz('class', 6, 1.3, -.4)), rz('class', -4, 1.5, 2).concat(rz('class', 6, 1.3, -.4)), [44, 42]); };
// 56 cave_ward
function wardScene(t, o = {}) { U.wdBeds.forEach(b => b.position.y = 0); U.patients.forEach((m, i) => { m.position.set(-8 + i * 3.6, .78, -2.6); m.rotation.set(0, Math.PI / 2, -Math.PI / 2); }); U.tarp.position.y = 0; U.opT.position.y = 0; U.wdPoles.forEach(p => p.position.y = 1.6);
  at(U.nurse, o.nx ?? -2, 0, -1.2, facing([0, -1])); pose(U.nurse, t, { walk: !!o.walk, armR: .5, elR: 1.2 }); at(U.surgeon, 8.6, 0, 1.0, facing([0, -1])); pose(U.surgeon, t, { armR: .8, elR: .6, armL: .8, elL: .6, nod: -.3 }); U.wdLamps.forEach(l => l.visible = true); }
function emptyWard() { U.wdBeds.forEach(b => b.position.y = -60); U.patients.forEach(m => m.position.y = -60); U.tarp.position.y = -60; U.opT.position.y = -60; U.wdPoles.forEach(p => p.position.y = -60); U.nurse.position.y = -60; U.surgeon.position.y = -60; U.wdLamps.forEach(l => l.visible = false); }
SHOTS[56] = (t, lt, d) => { caveLook('ward'); const nx = -7 + lt * 1.4; wardScene(t, { nx, walk: true }); light(0, 'cave', nx, 1.8, 79, 16, 0xffb060, 10);
  ct('cave', lt, d, rz('ward', -9.5, 1.7, .4).concat(rz('ward', -2, 1, -1.5)), rz('ward', -9, 1.6, .3).concat(rz('ward', -1, 1, -1.5)), [44, 44]); };
// 57 cave_work
SHOTS[57] = (t, lt, d) => { caveLook('street'); streetPeople(t); light(0, 'cave', -24, 2.6, -1, 18, 0xffb060, 10); U.dust.visible = true; U.dust.userData.update(t, wp('cave', -23.6, 4.4, -2.6));
  const sh = lt > .6 && lt < 1.4 ? .03 : 0; ct('cave', lt, d, [-21.6, 1.5, -.4, -23.6, 1.0, -3], [-21.9, 1.5, -.6, -23.6, 1.0, -3], [40, 38], sh); };
// 58 cave_mouth: looking out to the fields
SHOTS[58] = (t, lt, d) => { cliffLook('day'); at(U.cPeople[0], 8, 0, -24.4, facing([0, 1])); pose(U.cPeople[0], t, {});
  ct('cliff', lt, d, [8.4, 1.6, -28, 8, 1.4, 30], [8.4, 1.6, -27.4, 8, 1.4, 30], [50, 50]); overlay(c => arch(c, 1, { w: 860, h: 900 })); };
// 59 fields_day
SHOTS[59] = (t, lt, d) => { cliffLook('day'); ct('cliff', lt, d, [-20, 3, 70, 0, .5, 40], [-18, 3, 68, 0, .5, 40], [40, 40]); overlay(c => M.label(c, 'THE FIELDS', L.W / 2, L.H - 100, 50, '#fff4e0', fade(lt, d, .25))); };
// 60-61 hunger
SHOTS[60] = (t, lt, d) => { caveLook('family'); famScene(t); light(0, 'cave', .5, 1, 200.2, 16, 0xffa050, 6); ct('cave', lt, d, rz('family', 0, .7, 1.0).concat(rz('family', 0, .1, .3)), rz('family', 0, .62, .9).concat(rz('family', 0, .1, .3)), [36, 32]); };
SHOTS[61] = (t, lt, d) => { caveLook('family'); famScene(t); light(0, 'cave', .5, 1, 200.2, 16, 0xffa050, 6); const F = U.cFam; if (lt > 2.5) { F[0].userData.rig.head.rotation.y = .9; }
  ct('cave', lt, d, rz('family', 2.6, 1.3, 2.6).concat(rz('family', 0, .7, .5)), rz('family', 2.2, 1.2, 2.2).concat(rz('family', 0, .7, .5)), [42, 40]); };
// 62 night_farm
SHOTS[62] = (t, lt, d) => { villageNight(); farmers(t); ct('village', lt, d, [-36, 6, 64, 0, 1, 28], [-30, 5, 60, 0, 1, 28], [40, 40]); overlay(c => L.caption(c, 'WORKING AT NIGHT', '', fade(lt, d))); };
// 63 night_breath
SHOTS[63] = (t, lt, d) => { villageNight(); farmers(t); const m = U.fam.mum; at(m, 2, .1, 36, facing([.2, 1])); pose(m, t, { lean: .1 }); if (lt > 2) X.act(m, t, 'lookUp');
  const h = headPos(m); const k = ease(clamp(lt / d)); cam.position.set(h.x + 1.9 - k * .3, h.y - .2, h.z + .5); cam.lookAt(h.x, h.y + .15 + k * .35, h.z); cam.fov = 40; cam.updateProjectionMatrix(); };
// 64 cave_drip
SHOTS[64] = (t, lt, d) => { caveLook('family', .9); const F = U.cFam; famScene(t); F[3].position.set(.4, .12, 200.9 - 200); F[3].rotation.set(0, 0, -Math.PI / 2); light(0, 'cave', .5, 1, 200.2, 14, 0xffa050, 6);
  U.drips.forEach((dr, i) => { const ph = ((t * .9 + i * .37) % 1); dr.position.set(.3 + i * .04, 3 - ph * 2.9, 120.9); dr.visible = true; });
  ct('cave', lt, d, rz('family', 1.8, .9, 2.2).concat(rz('family', .4, .5, .9)), rz('family', 1.6, .8, 2.0).concat(rz('family', .4, .4, .9)), [40, 38]); };
// 65-67 day / night / dawn
const DN = [[-4, 2.6, 50, 0, 1, 30], [-3.6, 2.5, 49, 0, 1, 30]];
SHOTS[65] = (t, lt, d) => { show('village'); look('day', [0xd8e0d8, .002], 1.5, 2.4, 0xfff0dc, [-60, 70, 40], [3000, 0, 0]); hide(U.ruin, U.newPosts, U.warn, U.plot, U.scale, U.scrap, U.vStakes, U.vBombies, U.craters, Object.values(U.fam), U.farmers, U.buckets); ct('village', lt, d, ...DN, [40, 40]); overlay(c => M.label(c, 'DAY', 140, 120, 40, '#fff4e0', fade(lt, d, .2))); };
SHOTS[66] = (t, lt, d) => { villageNight(); farmers(t); ct('village', lt, d, ...DN, [40, 40]); overlay(c => M.label(c, 'NIGHT', 140, 120, 40, '#dfe8ff', fade(lt, d, .2))); };
SHOTS[67] = (t, lt, d) => { cliffLook('dawn'); U.cPeople.forEach((m, i) => { const p = clamp((lt + 1 - i * .25) / 3); const x = lerp(14 + i, 8, p), z = lerp(14 + i * .6, -25.4, p); at(m, x, 0, z, facing([8 - x, -25.4 - z])); pose(m, t + i, { walk: true }); if (p >= 1) m.position.y = -60; });
  ct('cliff', lt, d, [22, 3, 26, 8, 2, -20], [20, 3, 22, 8, 2, -20], [40, 40]); };
// 68 cave_threshold
SHOTS[68] = (t, lt, d) => { cliffLook('day'); const m = U.cPeople[3]; const step = clamp((lt - 4.4) / 2.6); at(m, 8, 0, -25.2 + step * 4, facing([0, 1])); pose(m, t, { walk: step > 0 && step < 1, armR: .3, elR: 1.2 }); if (lt < 4.4) X.act(m, t, 'lookUp'); U.water.position.set(8.25, .95 + 0, -25.2 + step * 4 + .1);
  ct('cliff', lt, d, [11.5, 1.5, -16, 8, 1.4, -25], [10.2, 1.5, -18, 8, 1.4, -24], [38, 36]); };
// 69 sick_bed
SHOTS[69] = (t, lt, d) => { caveLook('family', .9); const F = U.cFam; F[2].position.set(0, .12, .3); F[2].rotation.set(0, 0, -Math.PI / 2); at(F[1], .1, 0, -.5, facing([0, 1])); pose(F[1], t, { kneel: true, armR: .9, elR: .6 }); hide(F[0], F[3]); light(0, 'cave', .5, .9, 199.6, 14, 0xffa050, 6);
  ct('cave', lt, d, rz('family', 1.2, .9, 1.6).concat(rz('family', 0, .3, .2)), rz('family', 1.0, .85, 1.4).concat(rz('family', 0, .3, .2)), [40, 38]); };
// 70-71 stretcher journeys
function stretcherAt(t, x, z, dir) { U.stretcher.position.set(x, 1.05, z); U.stretcher.rotation.y = Math.atan2(-dir[1], dir[0]); U.bearers.forEach((m, i) => { const off = i === 0 ? 1.45 : i === 1 ? -1.45 : .2; at(m, x + dir[0] * off + (i === 2 ? -dir[1] * .9 : 0), 0, z + dir[1] * off + (i === 2 ? dir[0] * .9 : 0), facing(dir)); pose(m, t + i, { walk: true, speed: 6, armL: .4, armR: .4, elL: .5, elR: .5 }); }); }
SHOTS[70] = (t, lt, d) => { cliffLook('night', .004); look('night', [0x0a1020, .004], .8, 1.0, 0x9ab0e0, [60, 80, 60], [6000, 0, 0]); const x = -30 + lt * 1.5; stretcherAt(t, x, 26, [1, 0]); at(U.lamp, x + 2.2, 1.1, 26.4); light(0, 'cliff', x + 2.2, 1.3, 26.6, 10, 0xffb060, 8);
  ct('cliff', lt, d, [x - 2, 1.4, 31, x + 1, 1.2, 26], [x - 1, 1.4, 30.6, x + 2, 1.2, 26], [42, 42]); overlay(c => L.caption(c, 'TO THE HOSPITAL', 'BY NIGHT', fade(lt, d))); };
SHOTS[71] = (t, lt, d) => { cliffLook('day'); at(U.cJet, 120 - lt * 80, 22, 24, Math.PI); U.cJet.rotation.z = .2;
  ct('cliff', lt, d, [-26, 1.4, 31, -20, 3, 26], [-26, 1.4, 31, -14, 6, 26], [42, 44]); overlay(c => M.label(c, 'TOO DANGEROUS BY DAY', L.W / 2, L.H - 100, 40, '#fff4e0', fade(lt, d, .3))); };
// 72-76 cave hospital
SHOTS[72] = (t, lt, d) => { caveLook('ward', 1.1); wardScene(t); light(2, 'cave', 8.6, 2.2, 80, 26, 0xfff0d0, 8); ct('cave', lt, d, rz('ward', -9.6, 2.6, 1).concat(rz('ward', 4, 1.2, 0)), rz('ward', -9, 2.4, .8).concat(rz('ward', 5, 1.2, 0)), [46, 44]); overlay(c => L.caption(c, 'A CAVE HOSPITAL', 'WARDS AND OPERATING ROOMS', fade(lt, d))); };
SHOTS[73] = (t, lt, d) => { caveLook('ward', 1.1); wardScene(t); U.drips.forEach((dr, i) => { const ph = ((t * .8 + i * .21) % 1); dr.visible = true; dr.position.set(-3 + i * 1.1, 5.2 - ph * 1.9, (i % 2 ? .6 : -.8)); });
  ct('cave', lt, d, rz('ward', -5, 1.6, 2.6).concat(rz('ward', -1, 3.4, -.2)), rz('ward', -4.6, 1.6, 2.4).concat(rz('ward', -.6, 3.6, -.2)), [46, 46]); overlay(c => M.label(c, 'SHELTER FROM THE DRIPPING ROCK', L.W / 2, L.H - 100, 36, '#ffe8c0', fade(lt, d, .3))); };
SHOTS[74] = (t, lt, d) => { caveLook('ward'); emptyWard(); U.wdPoles.slice(0, 6).forEach(p => p.position.y = 1.6);
  const W2 = [U.nurse, U.surgeon, U.patients[0]]; U.poles.forEach((p, i) => { const x = -6 + lt * 1.3 + i * 3; p.position.set(x, 1.45, 80 + (i - 1) * 1.6); p.rotation.set(0, 0, Math.PI / 2); });
  if (!U.builders) { U.builders = [0, 1, 2, 3, 4, 5].map(i => { const m = X.villager({ seed: 2600 + i, longSleeve: i % 2 === 0, shirt: [0x3a4a5a, 0x5a4a3a, 0x2a2a30][i % 3] }); SETS.cave.add(m); return m; }); }
  U.builders.forEach((m, i) => { const pi = Math.floor(i / 2), x = -6 + lt * 1.3 + pi * 3 + (i % 2 ? 1.6 : -1.6); at(m, x, 0, 80 + (pi - 1) * 1.6 - .3, facing([1, 0])); pose(m, t + i, { walk: true, armR: -2.6, elR: -.2, armL: -2.6, elL: -.2 }); });
  ct('cave', lt, d, rz('ward', 4, 1.6, 4).concat(rz('ward', -2, 1.4, 0)), rz('ward', 3.4, 1.6, 3.6).concat(rz('ward', -1, 1.4, 0)), [46, 44]); };
SHOTS[75] = (t, lt, d) => { caveLook('ward', .5); emptyWard(); if (U.builders) U.builders.forEach(m => m.position.y = -60); const m = U.nurse; at(m, -9 + lt * 1.2, 0, 0, facing([1, 0])); pose(m, t, { walk: true, armR: .5, elR: 1.4 }); light(0, 'cave', -9 + lt * 1.2 + .4, 1.4, 80, 20, 0xffb060, 9); light(1, 'cave', 0, 2, 80, 0, 0xffb060, 1); light(2, 'cave', 0, 2, 80, 0, 0xffb060, 1);
  ct('cave', lt, d, rz('ward', 6, 1.6, 3).concat(rz('ward', -6, 1.4, 0)), rz('ward', 5.6, 1.6, 2.8).concat(rz('ward', -5, 1.4, 0)), [46, 46]); };
SHOTS[76] = (t, lt, d) => { caveLook('ward', 1.1); wardScene(t, { nx: 0 }); if (U.builders) U.builders.forEach(m => m.position.y = -60); ct('cave', lt, d, rz('ward', 6, 1.6, 3).concat(rz('ward', -6, 1.4, 0)), rz('ward', 5.2, 1.6, 2.6).concat(rz('ward', -5, 1.4, 0)), [46, 46]);
  overlay(c => { const a = 1 - clamp(lt / .8); if (a > 0) { c.fillStyle = `rgba(0,0,0,${a * .8})`; c.fillRect(0, 0, L.W, L.H); } }); };
// 77 journeys
SHOTS[77] = (t, lt, d) => { OV.noGL = true; overlay(c => LM.journey(c, lt)); };
// 78 cave_exit
SHOTS[78] = (t, lt, d) => { cliffLook('day'); const m = U.cPeople[6]; const step = clamp((lt - 1.2) / 3.5); at(m, 8.2, 0, -24.6 + step * 6, facing([0, 1])); pose(m, t, { walk: step > 0 && step < 1 });
  ct('cliff', lt, d, [8.5, 1.6, -28.2, 8, 1.5, 30], [8.5, 1.6, -27.8, 8, 1.5, 30], [50, 50]); overlay(c => arch(c, 1, { w: 860, h: 900 })); };

// ===================== QA fixes (reviewer pass) =====================
function caveLook2(room, warm = 1) { caveLook(room, warm); L.S.background = new THREE.Color(0x070504); U.drips.forEach(d => d.visible = false); U.bedroll.visible = room === 'family'; U.patients2.forEach(m => m.position.y = -60); U.wStool.position.y = -60; }
function famFloor(t, o = {}) { const F = U.cFam; const P2 = [[-.85, .2], [.85, .25], [-.35, 1.05], [.45, 1.1]];
  P2.forEach(([x, z], i) => { if (o.skip && o.skip.includes(i)) return; at(F[i], x, 0, z, facing([-x, .35 - z])); F[i].rotation.x = 0; F[i].rotation.z = 0; pose(F[i], t + i, { armR: .6, elR: 1.1, armL: .5, elL: 1.0, nod: -.15 }); X.act(F[i], t, 'floorSit'); }); }
function childOnBedroll(m, t = 0) { m.rotation.set(0, 0, 0); pose(m, t, { armL: .05, armR: .05, elL: 0, elR: 0 }); m.userData.rig.head.rotation.set(0, 0, 0); m.rotation.set(0, 0, Math.PI / 2); m.position.set(2.4 + .55, .16, .5); }
// 46 map: clean title + label placement
SHOTS[46] = (t, lt, d) => { OV.noGL = true; overlay(c => { const pr = LM.viewLerp([104, 18, 11], [104.0, 20.2, 4.2], ease(clamp(lt / 3))); LM.base(c, pr, { hl: [['Laos', '#d8c8a0']] });
  const [vx, vy] = pr(...LM.CITY.Viengxay); for (let i = 0; i < 26; i++) { const r = M.mulberry(i + 3), a = r() * 6.28, dd = 90 + r() * 150; const x = vx + Math.cos(a) * dd * 1.4, y = vy + 40 + Math.abs(Math.sin(a)) * dd * .8; c.fillStyle = `rgba(90,110,70,${clamp((lt - 2) / .8)})`; c.beginPath(); c.moveTo(x - 14, y + 10); c.quadraticCurveTo(x, y - 34, x + 14, y + 10); c.fill(); }
  const ca = clamp((lt - 1.8) / .4); c.save(); c.globalAlpha = ca; c.fillStyle = '#f2e8d2'; c.strokeStyle = '#2a1a10'; c.lineWidth = 3; c.beginPath(); c.arc(vx, vy, 10, 0, 7); c.fill(); c.stroke(); c.restore(); tag(c, 'VIENGXAY', vx, vy - 34, 34, '#fff4e0', ca);
  topTitle(c, 'VIENGXAY', 'HOUAPHAN PROVINCE · NORTHEASTERN LAOS', clamp(lt / .5)); M.vignette(c, .45); }); };
// 48 cave_enter: title at the top so walkers never cover it
SHOTS[48] = (t, lt, d) => { cliffLook('morning'); const goal = V3(8, 0, -24.9);
  U.cPeople.forEach((m, i) => { const p = clamp((lt + 3.5 - i * .55) / 5.5); const x = lerp(12 + i * .4, goal.x, p), z = lerp(14, goal.z, p); at(m, x, 0, z, facing([goal.x - x, goal.z - z])); pose(m, t + i, { walk: true }); if (p >= 1) m.position.y = -60; });
  ct('cliff', lt, d, [16, 2.2, 12, 8, 2.4, -24], [12, 2, 2, 8, 2.4, -25], [40, 40]); overlay(c => topTitle(c, 'THE CAVES OF VIENGXAY', 'PATHET LAO HEADQUARTERS', fade(lt, d))); };
// 50 street (keeps the earlier walker fix) + darker background behind gaps
const S50 = SHOTS[50]; SHOTS[50] = (t, lt, d) => { S50(t, lt, d); L.S.background = new THREE.Color(0x070504); U.drips.forEach(dd => dd.visible = false); U.patients2.forEach(m => m.position.y = -60); U.wStool.position.y = -60;
  U.stPeople.forEach((m, i) => { if (i >= 8) { at(m, 11 + (i - 8) * .7, 0, -1.3 + (i % 2) * .5, facing([0, -1])); pose(m, t + i, {}); X.act(m, t, 'floorSit'); } }); };
// 51 theatre: audience seated on the floor, caption at the top
SHOTS[51] = (t, lt, d) => { caveLook2('theatre', 1.1); light(0, 'cave', 8, 3.4, 160, 30, 0xfff0d0, 10); U.actors.forEach((m, i) => { pose(m, t + i, { armR: 1.0 + Math.sin(t * 2 + i) * .5, elR: .3 }); }); U.audience.forEach((m, i) => { pose(m, t + i, {}); X.act(m, t, 'floorSit'); });
  ct('cave', lt, d, rz('theatre', -6, 2.4, 2.5).concat(rz('theatre', 9, 1.8, 0)), rz('theatre', -5, 2.3, 2.2).concat(rz('theatre', 9, 1.8, 0)), [44, 42]); overlay(c => tag(c, 'EVEN A THEATRE', L.W / 2, 120, 44, '#ffe8c0', fade(lt, d, .3))); };
// 52-53 office: officials seated on chairs, seen from the wall side (faces visible)
function officeScene2(t) { U.officials.forEach((m, i) => { const p = [[-.4, 1.0], [.8, 1.0], [1.9, -2.4]][i]; at(m, p[0], 0, p[1], facing(i === 2 ? [-.6, 1] : [0, -1])); pose(m, t + i, { sit: i < 2, write: i === 0, point: i === 2, pointUp: .2 }); }); }
SHOTS[52] = (t, lt, d) => { caveLook2('office'); light(0, 'cave', 0, 2.4, 121.5, 22, 0xffc070, 10); light(1, 'cave', -.5, 1.6, 118, 10, 0xffc070, 8); officeScene2(t);
  ct('cave', lt, d, rz('office', -2.2, 1.7, -2.0).concat(rz('office', .3, 1.05, .8)), rz('office', -1.8, 1.6, -1.6).concat(rz('office', .3, 1.05, .8)), [44, 42]); };
const famScene2 = t => famFloor(t);
SHOTS[53] = (t, lt, d) => { caveLook2('office'); officeScene2(t); famFloor(t); U.bedroll.visible = true; [0, 1, 2, 3].forEach(i => U.cFam[i].position.y = U.cFam[i].position.y); light(0, 'cave', 0, 2.4, 121.5, 22, 0xffc070, 10); light(1, 'cave', .5, 1.2, 199.6, 14, 0xffa050, 8);
  OV.split = [() => ct('cave', lt, d, rz('office', -2.0, 1.6, -1.8).concat(rz('office', .3, 1.05, .8)), rz('office', -1.8, 1.6, -1.6).concat(rz('office', .3, 1.05, .8)), [46, 46]), () => ct('cave', lt, d, rz('family', 0, 1.5, 3.4).concat(rz('family', 0, .5, .5)), rz('family', 0, 1.4, 3.1).concat(rz('family', 0, .5, .5)), [46, 46])];
  overlay(c => { tag(c, 'REVOLUTION', L.W / 4, L.H - 80, 38, '#ffe8c0', fade(lt, d)); tag(c, 'SURVIVAL', L.W * 3 / 4, L.H - 80, 38, '#ffe8c0', fade(lt, d)); }); };
// 54 karst_jets: jets low enough to cross the cave mouth view
SHOTS[54] = (t, lt, d) => { cliffLook('morning', .0015); look('morning', [0xc8d0d0, .0015], 1.2, 1.8, 0xfff0d8, [-80, 60, 80], [6000, 0, 0]); U.cJet.position.y = 0; at(U.cJet, -150 + lt * 60, 20, 75, 0); U.cJet.rotation.z = -.1;
  U.cBlasts.forEach((b, i) => { b.position.set(-40 + i * 40, 22 + i * 6, 130 + i * 6); b.userData.update(lt - 2.2 - i * .5, wp('cliff', -40 + i * 40, 22, 130)); });
  ct('cliff', lt, d, [8, 1.8, -24.2, 6, 7, 40], [8, 1.8, -24.2, 5, 7.5, 40], [56, 56], lt > 2.2 && lt < 3.6 ? .03 : 0);
  overlay(c => { arch(c, 1, { w: 860, h: 900 }); if (lt > 2.2 && lt < 3.8) { c.fillStyle = `rgba(255,220,180,${.1 * Math.sin((lt - 2.2) * 6) ** 2})`; c.fillRect(0, 0, L.W, L.H); } }); };
// 55 class: kids seated on lowered benches
SHOTS[55] = (t, lt, d) => { caveLook2('class', 1.1); light(0, 'cave', 4, 2.6, 40, 22, 0xffc070, 12); U.clKids.forEach((k, i) => { pose(k, t + i, { sit: true }); X.act(k, t, 'lap'); }); pose(U.clTeacher, t, {}); X.act(U.clTeacher, t, 'teach');
  ct('cave', lt, d, rz('class', -5.6, 1.8, 2.0).concat(rz('class', 5, 1.1, -.2)), rz('class', -4.8, 1.7, 1.8).concat(rz('class', 5, 1.1, -.2)), [46, 44]); };
// 56/72/76 ward with patients in every bed
function wardScene2(t, o = {}) { wardScene(t, o); U.patients2.forEach((m, i) => { m.position.set(-8 + i * 3.6, .78, 2.6); m.rotation.set(0, -Math.PI / 2, -Math.PI / 2); }); }
SHOTS[56] = (t, lt, d) => { caveLook2('ward'); const nx = -6.5 + lt * 1.3; wardScene2(t, { nx, walk: true }); light(0, 'cave', nx, 1.8, 79, 16, 0xffb060, 10);
  ct('cave', lt, d, rz('ward', -9.2, 2.3, 0).concat(rz('ward', -1, .9, 0)), rz('ward', -8.8, 2.2, 0).concat(rz('ward', 0, .9, 0)), [46, 46]); };
// 57 cave_work: a clerk seated at the desk, typing, face lit
SHOTS[57] = (t, lt, d) => { caveLook2('street'); streetPeople(t); const m = U.stPeople[0]; U.wStool.position.set(-23.4, 0, -2.25); U.wStool.rotation.y = Math.PI / 2; at(m, -23.4, 0, -2.35, facing([0, -1])); pose(m, t, { sit: true, write: true }); m.userData.rig.arms[1].el.rotation.z = 1.3 + Math.sin(t * 14) * .12; m.userData.rig.arms[0].el.rotation.z = 1.2 + Math.cos(t * 13) * .12;
  light(0, 'cave', -23.6, 1.7, -3.0, 14, 0xffc070, 6); light(1, 'cave', -21, 2.6, -1, 10, 0xffb060, 12); U.dust.visible = true; U.dust.userData.update(t, wp('cave', -23.6, 4.4, -2.6));
  const sh = lt > .6 && lt < 1.4 ? .03 : 0; ct('cave', lt, d, [-21.4, 1.55, -1.5, -23.5, 1.15, -2.7], [-21.6, 1.5, -1.6, -23.5, 1.15, -2.7], [40, 38], sh); };
// 58 cave_mouth: silhouette at the side of the mouth looking out
SHOTS[58] = (t, lt, d) => { cliffLook('day'); at(U.cPeople[0], 6.6, 0, -20.2, facing([.2, 1])); pose(U.cPeople[0], t, {});
  ct('cliff', lt, d, [8.0, 1.6, -24.3, 8, 1.4, 30], [8.0, 1.6, -24.0, 8, 1.4, 30], [50, 50]); overlay(c => arch(c, 1, { w: 860, h: 900 })); };
// 60-61 hunger: 3/4 view of the family kneeling around a nearly empty bowl
SHOTS[60] = (t, lt, d) => { caveLook2('family'); famFloor(t); light(0, 'cave', .5, 1.2, 201, 16, 0xffa050, 7); ct('cave', lt, d, rz('family', 2.1, 1.7, 2.6).concat(rz('family', 0, .2, .45)), rz('family', 1.9, 1.6, 2.4).concat(rz('family', 0, .2, .45)), [36, 32]); };
SHOTS[61] = (t, lt, d) => { caveLook2('family'); famFloor(t); light(0, 'cave', .5, 1.2, 201, 16, 0xffa050, 7); const F = U.cFam; if (lt > 2.5) { F[0].userData.rig.head.rotation.y = .9; }
  ct('cave', lt, d, rz('family', 2.4, 1.5, 2.6).concat(rz('family', 0, .5, .5)), rz('family', 2.1, 1.4, 2.3).concat(rz('family', 0, .5, .5)), [42, 40]); };
// 63 night_breath: keep her profile in frame, gentle tilt to the stars
SHOTS[63] = (t, lt, d) => { villageNight(); farmers(t); const m = U.fam.mum; at(m, 2, .1, 36, facing([0, 1])); pose(m, t, { lean: .1 }); if (lt > 2) X.act(m, t, 'lookUp');
  const h = headPos(m); light(0, 'village', h.x - 3000 + .5, h.y + .2, h.z + 1.1, 7, 0xc8d0f0, 4); const k = ease(clamp(lt / d)); cam.position.set(h.x + .9, h.y - .15, h.z + 1.7); cam.lookAt(h.x, h.y + .1 + k * .3, h.z); cam.fov = 44; cam.updateProjectionMatrix(); };
// 64 cave_drip: the child asleep on a bedroll, drips falling beside him
SHOTS[64] = (t, lt, d) => { caveLook2('family', .9); famFloor(t, { skip: [3] }); childOnBedroll(U.cFam[3], t); light(0, 'cave', .5, 1.2, 201, 14, 0xffa050, 7);
  U.drips.forEach((dr, i) => { const ph = ((t * .9 + i * .37) % 1); dr.position.set(2.1 + i * .05, 3 - ph * 2.85, 120.75); dr.visible = true; });
  ct('cave', lt, d, rz('family', 3.6, 1.0, 2.0).concat(rz('family', 2.3, .3, .6)), rz('family', 3.4, .95, 1.8).concat(rz('family', 2.3, .3, .6)), [42, 40]); };
SHOTS[65] = (t, lt, d) => { show('village'); look('day', [0xd8e0d8, .002], 1.5, 2.4, 0xfff0dc, [-60, 70, 40], [3000, 0, 0]); hide(U.ruin, U.newPosts, U.warn, U.plot, U.scale, U.scrap, U.vStakes, U.vBombies, U.craters, Object.values(U.fam), U.farmers, U.buckets); ct('village', lt, d, ...DN, [40, 40]); overlay(c => tag(c, 'DAY', 140, 120, 40, '#fff4e0', fade(lt, d, .2), 'left')); };
SHOTS[66] = (t, lt, d) => { villageNight(); farmers(t); ct('village', lt, d, ...DN, [40, 40]); overlay(c => tag(c, 'NIGHT', 140, 120, 40, '#dfe8ff', fade(lt, d, .2), 'left')); };
// 68 cave_threshold: he stands at the threshold from the start, then steps out
SHOTS[68] = (t, lt, d) => { cliffLook('day'); const m = U.cPeople[3]; const step = clamp((lt - 4.4) / 2.6); at(m, 8, 0, -24.1 + step * 4, facing([0, 1])); pose(m, t, { walk: step > 0 && step < 1, armR: .3, elR: 1.2 }); if (lt < 4.4) X.act(m, t, 'lookUp'); U.water.position.set(8.25, .95, -24.1 + step * 4 + .12);
  ct('cliff', lt, d, [12.5, 1.6, -15, 8, 1.4, -24], [11, 1.6, -16.5, 8, 1.4, -23.5], [38, 36]); };
// 69 sick_bed: the child on the bedroll, mother kneeling beside, no drips
SHOTS[69] = (t, lt, d) => { caveLook2('family', .9); const F = U.cFam; childOnBedroll(F[2], t); at(F[1], 2.4, 0, -.3, facing([0, 1])); pose(F[1], t, { armR: 1.0 + Math.sin(t * 2) * .1, elR: .5, nod: -.35 }); X.act(F[1], t, 'floorSit'); hide(F[0], F[3]); light(0, 'cave', 2.0, 1.0, 199.8, 14, 0xffa050, 6);
  ct('cave', lt, d, rz('family', 4.0, 1.3, 1.3).concat(rz('family', 2.3, .35, .2)), rz('family', 3.8, 1.25, 1.2).concat(rz('family', 2.3, .35, .2)), [42, 40]); };
// 70 stretcher at night: darker, patient visible, lantern carried by the third bearer
SHOTS[70] = (t, lt, d) => { cliffLook('night', .004); look('night', [0x0a1020, .005], .42, .45, 0x8aa0d0, [60, 80, 60], [6000, 0, 0]); const x = -30 + lt * 1.5; stretcherAt(t, x, 26, [1, 0]);
  const b2 = U.bearers[2]; b2.position.z = 26 + 1.1; at(U.lamp, b2.position.x + .25, .95, 27.45); light(0, 'cliff', b2.position.x + .25, 1.1, 27.5, 12, 0xffb060, 9); light(1, 'cliff', x, 2.5, 28, 4, 0xffb060, 8);
  ct('cliff', lt, d, [x - 1.5, 1.6, 32, x + .5, 1.0, 26], [x - .5, 1.6, 31.6, x + 1.5, 1.0, 26], [42, 42]); overlay(c => topTitle(c, 'TO THE HOSPITAL', 'BY NIGHT', fade(lt, d))); };
SHOTS[71] = (t, lt, d) => { cliffLook('day'); at(U.cJet, 120 - lt * 80, 12, 24, Math.PI); U.cJet.rotation.z = .2;
  ct('cliff', lt, d, [-26, 1.4, 31, -20, 3, 26], [-26, 1.4, 31, -14, 5, 26], [44, 46]); overlay(c => tag(c, 'TOO DANGEROUS BY DAY', L.W / 2, L.H - 100, 40, '#fff4e0', fade(lt, d, .3))); };
SHOTS[72] = (t, lt, d) => { caveLook2('ward', 1.1); wardScene2(t); light(2, 'cave', 8.6, 2.2, 80, 26, 0xfff0d0, 8); ct('cave', lt, d, rz('ward', -9.4, 2.6, .6).concat(rz('ward', 4, 1.2, 0)), rz('ward', -9, 2.4, .5).concat(rz('ward', 5, 1.2, 0)), [46, 44]); overlay(c => topTitle(c, 'A CAVE HOSPITAL', 'WARDS AND OPERATING ROOMS', fade(lt, d))); };
// 73 tarp + patients both in frame
SHOTS[73] = (t, lt, d) => { caveLook2('ward', 1.1); wardScene2(t); U.drips.forEach((dr, i) => { const ph = ((t * .8 + i * .21) % 1); dr.visible = true; dr.position.set(-4 + i * 1.1, 5.2 - ph * 1.9, (i % 2 ? .6 : -.8)); });
  ct('cave', lt, d, rz('ward', -8.6, 1.2, 1.2).concat(rz('ward', -1.5, 2.4, -.8)), rz('ward', -8.3, 1.2, 1.1).concat(rz('ward', -1.2, 2.5, -.8)), [52, 52]); overlay(c => tag(c, 'SHELTER FROM THE DRIPPING ROCK', L.W / 2, L.H - 90, 36, '#ffe8c0', fade(lt, d, .3))); };
// 74 builders carry poles on their shoulders
SHOTS[74] = (t, lt, d) => { caveLook2('ward'); emptyWard(); U.wdPoles.slice(0, 6).forEach(p => p.position.y = 1.6);
  if (!U.builders) { U.builders = [0, 1, 2, 3, 4, 5].map(i => { const m = X.villager({ seed: 2600 + i, longSleeve: i % 2 === 0, shirt: [0x3a4a5a, 0x5a4a3a, 0x2a2a30][i % 3] }); SETS.cave.add(m); return m; }); }
  U.poles.forEach((p, i) => { const x = -7 + lt * 1.3 + i * 4.2, z = 80 + (i - 1) * 1.7; p.position.set(x, 1.47, z + .22); p.rotation.set(0, 0, Math.PI / 2); p.scale.set(1, .85, 1);
    [0, 1].forEach(k => { const m = U.builders[i * 2 + k]; at(m, x + (k ? 1.2 : -1.2), 0, z, facing([1, 0])); pose(m, t + i * 2 + k, { walk: true, armR: -1.9, elR: .9, armL: .2 }); }); });
  ct('cave', lt, d, rz('ward', 2, 1.8, 6.2).concat(rz('ward', -1, 1.2, 0)), rz('ward', 1.6, 1.8, 5.8).concat(rz('ward', -.5, 1.2, 0)), [50, 48]); };
// 75 empty chamber lit by a lantern (no sky through the rock)
SHOTS[75] = (t, lt, d) => { caveLook2('ward', .6); emptyWard(); if (U.builders) U.builders.forEach(m => m.position.y = -60); U.poles.forEach(p => p.position.y = -60); const m = U.nurse; at(m, -8 + lt * 1.2, 0, 0, facing([1, 0])); pose(m, t, { walk: true, armR: .5, elR: 1.4 });
  light(0, 'cave', -8 + lt * 1.2 + .4, 1.4, 80, 34, 0xffb060, 12); light(1, 'cave', 0, 2.5, 80, 3, 0xffb060, 14); light(2, 'cave', 0, 2, 80, 0, 0xffb060, 1);
  ct('cave', lt, d, rz('ward', 6, 1.8, 3).concat(rz('ward', -5, 1.4, 0)), rz('ward', 5.6, 1.8, 2.8).concat(rz('ward', -4, 1.4, 0)), [48, 48]); };
SHOTS[76] = (t, lt, d) => { caveLook2('ward', 1.1); wardScene2(t, { nx: 0 }); if (U.builders) U.builders.forEach(m => m.position.y = -60); U.poles.forEach(p => p.position.y = -60); ct('cave', lt, d, rz('ward', 6, 1.8, 3).concat(rz('ward', -6, 1.2, 0)), rz('ward', 5.2, 1.8, 2.6).concat(rz('ward', -5, 1.2, 0)), [48, 48]);
  overlay(c => { const a = 1 - clamp(lt / .8); if (a > 0) { c.fillStyle = `rgba(0,0,0,${a * .8})`; c.fillRect(0, 0, L.W, L.H); } }); };
// 78 cave_exit: a man walks out from beside the camera into the light (back to us, clearly walking away)
SHOTS[78] = (t, lt, d) => { cliffLook('day'); const m = U.cPeople[4]; const step = clamp((lt - .4) / 4.6); at(m, 8.6, 0, -23.4 + step * 8, facing([0, 1])); pose(m, t, { walk: step > 0 && step < 1 });
  ct('cliff', lt, d, [8.0, 1.7, -24.4, 8, 1.4, 30], [8.0, 1.7, -24.2, 8, 1.4, 30], [50, 50]); overlay(c => arch(c, 1, { w: 860, h: 900 })); };

// ===================== QA pass 3 =====================
// patients lie on their backs, whole body on the mattress, head on the pillow (pillow is at bed z + .75)
const LIE_Q = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(V3(0, 1, 0), V3(0, 0, 1), V3(1, 0, 0)));
function layOnBed(m, bx, bz, t) { pose(m, t, { armL: .06, armR: .06, elL: .05, elR: .05 }); const r = m.userData.rig; r.head.rotation.set(0, 0, 0); r.spine.rotation.set(0, 0, 0);
  m.rotation.set(0, 0, 0); m.quaternion.copy(LIE_Q); m.position.set(bx, .81, bz + .78 - 1.64); }
function wardScene3(t, o = {}) { wardScene2(t, o); U.patients.forEach((m, i) => layOnBed(m, -8 + i * 3.6, -2.6, t + i)); U.patients2.forEach((m, i) => layOnBed(m, -8 + i * 3.6, 2.6, t + 5 + i));
  if (o.walk) { at(U.nurse, o.nx, 0, -.55, facing([1, 0])); pose(U.nurse, t, { walk: true }); } }
SHOTS[56] = (t, lt, d) => { caveLook2('ward'); const nx = -6.5 + lt * 1.3; wardScene3(t, { nx, walk: true }); light(0, 'cave', nx, 1.8, 79, 16, 0xffb060, 10);
  ct('cave', lt, d, rz('ward', -9.2, 2.3, 0).concat(rz('ward', -1, .9, 0)), rz('ward', -8.8, 2.2, 0).concat(rz('ward', 0, .9, 0)), [46, 46]); };
SHOTS[72] = (t, lt, d) => { caveLook2('ward', 1.1); wardScene3(t); light(2, 'cave', 8.6, 2.2, 80, 26, 0xfff0d0, 8); ct('cave', lt, d, rz('ward', -9.4, 2.6, .6).concat(rz('ward', 4, 1.2, 0)), rz('ward', -9, 2.4, .5).concat(rz('ward', 5, 1.2, 0)), [46, 44]); overlay(c => topTitle(c, 'A CAVE HOSPITAL', 'WARDS AND OPERATING ROOMS', fade(lt, d))); };
SHOTS[73] = (t, lt, d) => { caveLook2('ward', 1.1); wardScene3(t); U.drips.forEach((dr, i) => { const ph = ((t * .8 + i * .21) % 1); dr.visible = true; dr.position.set(-4 + i * 1.1, 5.2 - ph * 1.9, (i % 2 ? .6 : -.8)); });
  ct('cave', lt, d, rz('ward', -8.6, 1.2, 1.2).concat(rz('ward', -1.5, 2.4, -.8)), rz('ward', -8.3, 1.2, 1.1).concat(rz('ward', -1.2, 2.5, -.8)), [52, 52]); overlay(c => tag(c, 'SHELTER FROM THE DRIPPING ROCK', L.W / 2, L.H - 90, 36, '#ffe8c0', fade(lt, d, .3))); };
SHOTS[76] = (t, lt, d) => { caveLook2('ward', 1.1); wardScene3(t, { nx: 0 }); if (U.builders) U.builders.forEach(m => m.position.y = -60); U.poles.forEach(p => p.position.y = -60); ct('cave', lt, d, rz('ward', 6, 1.8, 3).concat(rz('ward', -6, 1.2, 0)), rz('ward', 5.2, 1.8, 2.6).concat(rz('ward', -5, 1.2, 0)), [48, 48]);
  overlay(c => { const a = 1 - clamp(lt / .8); if (a > 0) { c.fillStyle = `rgba(0,0,0,${a * .8})`; c.fillRect(0, 0, L.W, L.H); } }); };
// 74 builders: pole resting on top of the shoulder, one hand up steadying it
SHOTS[74] = (t, lt, d) => { caveLook2('ward'); emptyWard(); U.wdPoles.slice(0, 6).forEach(p => p.position.y = 1.6);
  if (!U.builders) { U.builders = [0, 1, 2, 3, 4, 5].map(i => { const m = X.villager({ seed: 2600 + i, longSleeve: i % 2 === 0, shirt: [0x3a4a5a, 0x5a4a3a, 0x2a2a30][i % 3] }); SETS.cave.add(m); return m; }); }
  U.poles.forEach((p, i) => { const x = -7 + lt * 1.3 + i * 4.2, z = 80 + (i - 1) * 1.7; p.position.set(x, 1.535, z + .2); p.rotation.set(0, 0, Math.PI / 2); p.scale.set(1, .85, 1);
    [0, 1].forEach(k => { const m = U.builders[i * 2 + k]; at(m, x + (k ? 1.2 : -1.2), 0, z, facing([1, 0])); pose(m, t + i * 2 + k, { walk: true }); const a = m.userData.rig.arms[1]; a.sh.rotation.set(0, 0, 1.3); a.el.rotation.set(0, 0, 1.9); }); });
  ct('cave', lt, d, rz('ward', 2, 1.8, 6.2).concat(rz('ward', -1, 1.2, 0)), rz('ward', 1.6, 1.8, 5.8).concat(rz('ward', -.5, 1.2, 0)), [50, 48]); };
// 50 street school: children sit on the floor in front of the blackboard; benches removed so nothing cuts through them
const S50b = SHOTS[50]; SHOTS[50] = (t, lt, d) => { S50b(t, lt, d); if (!U.stBenches) U.stBenches = U.cRooms.street.children.filter(o => o.isGroup && Math.abs(o.position.x - 12) < .5 && o.position.z > -3 && o.position.z < -.8 && o.children.length === 3); U.stBenches.forEach(b => b.visible = false); };
// short steps inside a sinh skirt so the legs never poke through it
function skirtWalk(m) { if (!m.userData.sk) return; m.userData.rig.legs.forEach(l => { l.hip.rotation.z *= .3; l.knee.rotation.z *= .4; }); }
// 67 dawn procession: walk on the dry ground in front of the paddies, wider skirts so legs stay inside while walking
SHOTS[67] = (t, lt, d) => { cliffLook('dawn'); U.cPeople.forEach((m, i) => { const p = clamp((lt + 1 - i * .25) / 3); const x = lerp(13 + i * .7, 8, p), z = lerp(8 + i * .5, -24.9, p); at(m, x, 0, z, facing([8 - x, -24.9 - z])); pose(m, t + i, { walk: true }); skirtWalk(m); if (p >= 1) m.position.y = -60; });
  ct('cliff', lt, d, [22, 3, 26, 8, 2, -20], [20, 3, 22, 8, 2, -20], [40, 40]); };
// 48 same procession: short steps for the women in sinh skirts
const S48c = SHOTS[48]; SHOTS[48] = (t, lt, d) => { S48c(t, lt, d); U.cPeople.forEach(skirtWalk); };
// a karst peak behind the bright gap in the ridge seen from the cave mouth (54, 58, 78)
