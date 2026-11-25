// ===================== LAOS 5: Atta's garden, the school, other measurements (cues 107-133) =====================
import * as L from './lib3.js';
import * as M from './maps.js';
import * as X from './lao.js';
import * as LM from './laomaps.js';
import * as Z from './laosets.js';
const { THREE, cam, U, V3, at, lerp, clamp, ease, look, show, fx, overlay, OV, pose, facing, SETS } = L;
const { ct, wp, light, hide } = Z;
export const RANGE = { from: 107, to: 133, fadeOut: 2.4 };
export const SHOTS = {};
const fade = (lt, d, a = .4) => clamp(lt / a) * (1 - clamp((lt - d + a) / a));
const headPos = m => { const p = V3(); m.updateMatrixWorld(true); m.userData.rig.head.getWorldPosition(p); return p; };
// memory frames from the already-rendered sections
const MEM = {}; async function memLoad(key, ranges) { MEM[key] = []; for (const [f0, f1] of ranges) for (let f = f0; f < f1; f += 2) { const im = new Image(); im.src = `out_laos/${String(f).padStart(5, '0')}.jpg`; MEM[key].push(im); } await Promise.all(MEM[key].map(im => im.decode().catch(() => 0))); }
function memory(c, key, lt, d, sepia, cap) { const a = MEM[key], i = Math.min(a.length - 1, Math.floor(lt / d * a.length)), im = a[i]; c.fillStyle = '#100c08'; c.fillRect(0, 0, L.W, L.H); if (sepia) c.filter = 'sepia(.85) contrast(1.1) brightness(.9)'; if (im && im.naturalWidth) c.drawImage(im, -30 + lt * 8, -17, L.W + 60, L.H + 34); c.filter = 'none'; if (cap) lblB(c, cap, L.H - 90, 40, fade(lt, d)); }
const TLs = []; const fr = (i, a = .1, b = .9) => { const s = TLs[i]; return [Math.round((s.start + (s.end - s.start) * a) * 24), Math.round((s.start + (s.end - s.start) * b) * 24)]; };
export async function build(CUES) { Z.skies(); Z.gardenSet(); Z.schoolSet(); Z.caveSet(); Z.villageSet(); Z.cliffSet(); Z.skySet(); TLs.push(...CUES);
  await memLoad('past', [fr(55), fr(56), fr(63), fr(76)]); await memLoad('now', [fr(89), fr(92), fr(96), fr(99)]);
  U.gTrowel = L.mesh(new THREE.BoxGeometry(.18, .02, .08), L.mat(0x8a8a8a, .4, .6)); SETS.garden.add(U.gTrowel);
  // school windows: show a dim interior instead of black voids
  U.sch.traverse(m => { if (m.isMesh && m.material && m.material.color && m.material.color.getHex() === 0x1a1a1e) { m.material = m.material.clone(); m.material.color.set(0x5a4e42); } });
}
function gardenLook(sky = 'day', after = false) { show('garden'); look(sky, [0xd8e0d8, .002], 1.5, 2.4, 0xfff0dc, [-60, 70, 40], [12000, 0, 6000]);
  U.beds.position.y = after ? 0 : -60; U.saplings.position.y = after ? 0 : -60; U.store.position.y = after ? 0 : -60; U.pegs.position.y = after ? 0 : -60;
  hide(U.gTeam, U.pickup, U.gStakes, U.attaWife); U.gMound.position.y = -60; U.gb.position.y = -60; U.gHoe.position.y = -60; U.gBlast.userData.update(-1); U.demo.position.y = -60; U.gTrowel.position.y = -60; }
function kidsGarden(t, cx = 4, cz = 4) { U.attaKids.forEach((k, i) => { const a = t * .7 + i * 3; at(k, cx + Math.cos(a) * 2.2, 0, cz + Math.sin(a) * 1.6, facing([-Math.sin(a), Math.cos(a)])); pose(k, t + i, { walk: true, run: true, speed: 9 }); }); }
const SPOT = [-2, 0, 6];
// 107 atta_find
SHOTS[107] = (t, lt, d) => { gardenLook(); kidsGarden(t, 4, 1); const A = U.atta; at(A, SPOT[0] + .7, 0, SPOT[2] + .3, facing([-1, -.2])); pose(A, t, {}); if (lt < 3.2) X.act(A, t, 'dig', { rate: 3 }); else X.act(A, t, 'crouch'); at(U.gb, ...SPOT); U.gb.scale.setScalar(1.8); U.gb.position.y = .05;
  ct('garden', lt, d, [4, 1.8, 12, 0, .8, 4], [2, 1.2, 9.4, -1, .4, 5.6], [40, 36]); overlay(c => L.caption(c, 'PHON VILLAGE', 'METRES FROM WHERE HIS CHILDREN PLAYED', fade(lt, d))); };
// 108 atta_think
SHOTS[108] = (t, lt, d) => { gardenLook(); kidsGarden(t, 4, 1); const A = U.atta; at(A, SPOT[0] + .7, 0, SPOT[2] + .3, facing([-1, -.2])); pose(A, t, { look: Math.sin(lt * 2.4) * .6 }); X.act(A, t, 'crouch');
  const h = headPos(A); cam.position.set(h.x - 1.1, h.y + .05, h.z - .4); cam.lookAt(h.x, h.y, h.z); cam.fov = 34; cam.updateProjectionMatrix(); };
// 109 atta_bury
SHOTS[109] = (t, lt, d) => { gardenLook(); const A = U.atta; at(A, SPOT[0] + .8, 0, SPOT[2] + .2, facing([-1, -.2])); pose(A, t, {}); X.act(A, t * 1.4, 'dig', { rate: 4 }); const k = clamp(lt / d); U.gb.position.set(SPOT[0], .05 - k * .3, SPOT[2]); U.gMound.position.set(...SPOT); U.gMound.scale.set(.6 + k * .4, .1 + k * .3, .6 + k * .4); U.attaKids.forEach(m => m.position.y = -60);
  ct('garden', lt, d, [-.2, 1.1, 8.2, -1.8, .3, 6], [-.4, 1.0, 8.0, -1.8, .3, 6], [38, 36]); };
// 110 atta_fear
SHOTS[110] = (t, lt, d) => { gardenLook(); kidsGarden(t, 3, 3); U.gMound.position.set(...SPOT); U.gMound.scale.set(1, .4, 1); const A = U.atta; const x = 2 - lt * .4; at(A, x, 0, SPOT[2] + .4, facing([-1, 0])); pose(A, t, {}); X.act(A, t, 'dig', { rate: 1.6 });
  ct('garden', lt, d, [-3.4, .35, 7.4, 0, .9, 5], [-3.3, .4, 7.2, .4, .9, 5], [40, 40]); };
// 111 team_arrive
SHOTS[111] = (t, lt, d) => { gardenLook('morning'); U.gMound.position.set(...SPOT); U.gMound.scale.set(1, .4, 1); const p = ease(clamp(lt / 2)); at(U.pickup, lerp(30, 9, p), 0, 10, Math.PI);
  U.gTeam.forEach((m, i) => { const out = clamp((lt - 2.1 - i * .3) / .8); at(m, 8 + i * .8 - out * 2, 0, 11.5 + out * 1.2, facing([-1, 0])); pose(m, t + i, { walk: out > 0 && out < 1 }); if (out <= 0) m.position.y = -60; });
  const A = U.atta; at(A, 2.4, 0, 9.6, facing([1, .3])); pose(A, t, lt > 3.4 ? { point: true, pointUp: -.4 } : {}); U.attaKids.forEach(m => m.position.y = -60);
  ct('garden', lt, d, [-4, 1.7, 17, 5, 1.2, 9], [-3, 1.6, 16, 5, 1.2, 9], [40, 40]); overlay(c => L.caption(c, '2022', 'A CLEARANCE TEAM ARRIVES', fade(lt, d))); };
// 112 team_found
SHOTS[112] = (t, lt, d) => { gardenLook('morning'); U.gMound.position.set(...SPOT); U.gMound.scale.set(1, .4, 1); const m = U.gTeam[0]; at(m, SPOT[0] + 1.0, 0, SPOT[2] + .2, facing([-1, 0])); pose(m, t, {}); X.act(m, t, 'sweep'); const s = U.gStakes[0]; at(s, SPOT[0] + .3, 0, SPOT[2] + .4); s.scale.setScalar(1.6);
  ct('garden', lt, d, [SPOT[0] - .6, .7, SPOT[2] + 1.8, SPOT[0] + .4, .3, SPOT[2]], [SPOT[0] - .6, .7, SPOT[2] + 1.7, SPOT[0] + .4, .3, SPOT[2]], [40, 40]); };
// 113 team_destroy
SHOTS[113] = (t, lt, d) => { gardenLook('day'); U.demo.position.set(40, 0, 40); U.gBlast.position.set(40, 0, 40); U.gBlast.userData.update(lt - 1.2, wp('garden', 40, 0, 40)); at(U.pickup, 14, 0, 18, .6);
  U.gTeam.forEach((m, i) => { at(m, 12 + i * .9, 0, 15.6 - i * .3, facing([1, 1])); pose(m, t + i, {}); });
  ct('garden', lt, d, [6, 1.6, 10, 40, 2, 40], [6.3, 1.6, 10.2, 40, 3, 40], [40, 40], lt > 1.2 && lt < 1.9 ? .03 : 0); overlay(c => L.caption(c, 'DESTROYED', 'WITH OTHER EXPLOSIVES FOUND ON HIS LAND', fade(lt, d))); };
// 114-117 the garden after clearance
function afterScene(t) { kidsGarden(t, -6, 10); const A = U.atta; at(A, 5, 0, 1.2, facing([0, 1])); pose(A, t, {}); X.act(A, t, 'dig', { rate: 2 }); const W = U.attaWife; at(W, 8, 0, 3, facing([-.3, 1])); pose(W, t, {}); X.act(W, t + 1, 'dig', { rate: 2 }); }
SHOTS[114] = (t, lt, d) => { gardenLook('day', true); afterScene(t); ct('garden', lt, d, [24, 14, 34, 0, 0, 2], [16, 8, 26, 0, 0, 2], [42, 42]); };
SHOTS[115] = (t, lt, d) => { gardenLook('day', true); const A = U.atta; at(A, 1, 0, 9.6, facing([0, -1])); pose(A, t, {}); X.act(A, t, 'crouch'); U.attaKids.forEach(m => m.position.y = -60);
  ct('garden', lt, d, [2.2, .9, 11.2, 1, .7, 8.8], [2.0, .85, 11.0, 1, .7, 8.8], [38, 36]); };
SHOTS[116] = (t, lt, d) => { gardenLook('day', true); kidsGarden(t * 1.2, -6, 10); ct('garden', lt, d, [-1, .8, 16, -6, .7, 10], [-2, .8, 16, -6, .7, 10], [42, 42]); };
SHOTS[117] = (t, lt, d) => { gardenLook('dusk', true); look('dusk', [0xc8a080, .002], 1.1, 1.6, 0xffb080, [-100, 20, -60], [12000, 0, 6000]); const F = [U.atta, U.attaWife, ...U.attaKids]; F.forEach((m, i) => { at(m, -1 + i * .8, 0, 14 + (i % 2) * .3, facing([0, -1])); pose(m, t + i, {}); });
  ct('garden', lt, d, [-4, 1.3, 19, 2, 1.6, 4], [-3.5, 1.3, 18.4, 2, 1.8, 4], [42, 42]); };
// 118-121 back to the school
function schoolLook(sky = 'morning') { show('school'); U.schFlag.parent.visible = true; look(sky, [0xd8e0e0, .0016], 1.5, 2.6, 0xfff0d8, [-60, 70, 50], [0, 0, 0], [0xdfe6f0, 0x8a7a5a]); hide(U.team, U.parents, U.moto); U.schStakes.forEach(s => s.position.y = -60); U.schBombie.position.y = -60; U.ball.position.y = -60; }
function kidsPlay(t) { const K = U.kids; for (let i = 0; i < 16; i++) { const a = t * .5 + i * .39, r = 4 + (i % 4) * 2.2; at(K[i], Math.cos(a) * r, 0, 10 + Math.sin(a) * r * .7, facing([-Math.sin(a), Math.cos(a) * .7])); pose(K[i], t + i, { walk: true, run: i % 2 === 0, speed: i % 2 ? 6 : 9 }); } }
function teacherOn(t) { at(U.teacher, -5.6, .5, -8.9, facing([.2, 1])); pose(U.teacher, t, { armL: .1, armR: .1, elL: 1.2, elR: 1.2 }); }
SHOTS[118] = (t, lt, d) => { schoolLook(); kidsPlay(t); teacherOn(t); ct('school', lt, d, [0, 10, 52, 0, 3, -4], [0, 8, 46, 0, 3, -4], [40, 40]); overlay(c => L.caption(c, 'NACHAT PRIMARY SCHOOL', '', fade(lt, d))); };
SHOTS[119] = (t, lt, d) => { schoolLook('day'); U.kids.forEach(k => k.position.y = -60); teacherOn(t); U.schStakes.forEach(s => s.position.copy(s.userData.home));
  ct('school', lt, d, [0, 24, 30, 0, 0, 12], [0, 22, 28, 0, 0, 12], [44, 44]); overlay(c => { M.label(c, '30', L.W - 200, 190, 120, '#f2c050', 1); M.label(c, 'IN ONE PLAYGROUND', L.W - 200, 240, 26, '#f2e8d2', 1); }); };
SHOTS[120] = (t, lt, d) => { schoolLook(); kidsPlay(t); teacherOn(t); const h = headPos(U.teacher); const k = ease(clamp(lt / d)); cam.position.set(h.x + .6, h.y + .02, h.z + 1.6 - k * .3); cam.lookAt(h.x - .05, h.y - .02, h.z); cam.fov = 32; cam.updateProjectionMatrix(); };
SHOTS[121] = (t, lt, d) => { schoolLook('morning'); teacherOn(t); U.kids.forEach((k, i) => { if (i > 7) { k.position.y = -60; return; } const p = clamp((lt - i * .35) / 3); at(k, (i % 2 ? .6 : -.6), 0, lerp(40, 28, p), facing([0, -1])); pose(k, t + i, { walk: p < 1 }); });
  U.parents.forEach((m, i) => { at(m, -4 + i * 2, 0, 37 + (i % 2), facing([0, -1])); pose(m, t + i, { armR: i % 2 ? -2.4 : 0 }); }); at(U.moto, 6, 0, 38, Math.PI / 2);
  ct('school', lt, d, [10, 2.2, 46, 0, 1.2, 32], [8, 2.0, 44, 0, 1.2, 32], [40, 40]); };
// 122 cave classroom (memory)
SHOTS[122] = (t, lt, d) => { show('cave'); look('night', null, .35, 0, 0xfff0dc, [0, 60, 0], [0, 0, 3000], [0x8a6a4a, 0x2a1a10]); light(0, 'cave', 4, 2.6, 40, 22, 0xffc070, 12); light(1, 'cave', -2, 2.6, 40, 14, 0xffb060, 12);
  U.clKids.forEach((k, i) => pose(k, t + i, { sit: true })); pose(U.clTeacher, t, {}); X.act(U.clTeacher, t, 'teach');
  ct('cave', lt, d, [-6, 1.7, 42.6, 6, 1.3, 39.6], [-4, 1.5, 42.2, 6, 1.3, 39.6], [44, 40]);
  overlay(c => { c.globalCompositeOperation = 'color'; c.fillStyle = 'rgba(150,120,80,.8)'; c.fillRect(0, 0, L.W, L.H); c.globalCompositeOperation = 'source-over'; L.caption(c, 'VIENGXAY, 1960s', 'CLASSROOMS INSIDE THE MOUNTAINS', fade(lt, d)); }); };
// 123 deminer
SHOTS[123] = (t, lt, d) => { gardenLook('day', true); const m = U.gTeam[1]; at(m, -20, 0, 20, facing([0, -1])); pose(m, t, { kneel: true, armR: .9, elR: .8 + Math.sin(t * 5) * .15, armL: .6, elL: 1 }); X.act(m, t, 'lookDown'); U.gb.position.set(-20.05, .04, 19.4); U.gb.scale.setScalar(1.8); U.gTrowel.position.set(-19.9, .08, 19.5);
  U.gStakes.forEach((s, i) => { at(s, -21.5 + (i % 4), 0, 18 + Math.floor(i / 4) * 2.6); s.scale.setScalar(1.4); });
  ct('garden', lt, d, [-17.6, 1.0, 21.4, -20, .35, 19.6], [-17.9, .9, 21.2, -20, .3, 19.6], [38, 34]); overlay(c => L.caption(c, 'CLEARANCE', 'ONE ITEM AT A TIME', fade(lt, d))); };
// 124-125 ledger
SHOTS[124] = (t, lt, d) => { OV.noGL = true; overlay(c => LM.ledger(c, lt, [['Missions', '580,000+'], ['Tonnage', '2,000,000+'], ['Targets', 'routes · positions']], { title: 'THE BOMBING' })); };
SHOTS[125] = (t, lt, d) => { OV.noGL = true; overlay(c => LM.ledger(c, lt, [], { title: 'ANOTHER SET OF MEASUREMENTS', paper: '#f0e6d0' })); };
// 126-129 measurements
SHOTS[126] = (t, lt, d) => { show('village'); look('day', [0xd8e0d8, .002], 1.5, 2.4, 0xfff0dc, [-60, 70, 40], [3000, 0, 0]); hide(U.ruin, U.newPosts, U.warn, U.plot, U.scale, U.scrap, U.vStakes, U.vBombies, U.craters, Object.values(U.fam), U.farmers, U.buckets); U.vfire.position.y = -60;
  ct('village', lt, d, [-4, 7, 18, -14, 0, 2], [-4, 7, 18, -14, 0, 2], [44, 44]); overlay(c => { c.strokeStyle = '#f2c050'; c.lineWidth = 5; c.setLineDash([16, 10]); c.beginPath(); c.moveTo(700, 420); c.lineTo(700 + (1180 - 700) * clamp(lt / .8), 420 + (640 - 420) * clamp(lt / .8)); c.stroke(); c.setLineDash([]); M.label(c, 'THE DISTANCE TO SHELTER', L.W / 2, L.H - 90, 42, '#fff4e0', fade(lt, d, .2)); }); };
SHOTS[127] = (t, lt, d) => { show('village'); look('night', [0x0a1020, .003], .9, 1.1, 0x9ab0e0, [60, 80, 60], [3000, 0, 0]); hide(U.ruin, U.newPosts, U.warn, U.plot, U.scale, U.scrap, U.vStakes, U.vBombies, U.craters, Object.values(U.fam), U.buckets);
  U.farmers.forEach((m, i) => { at(m, -14 + i * 5.2, .1, 28 + (i % 3) * 2.2, facing([0, 1])); pose(m, t + i, {}); X.act(m, t * .6 + i, 'dig', { rate: 2 }); }); ct('village', lt, d, [-4, 2.6, 50, 0, 1, 30], [-3.6, 2.5, 49, 0, 1, 30], [40, 40]);
  overlay(c => M.label(c, 'THE HOURS TO WORK A FIELD', L.W / 2, L.H - 90, 42, '#dfe8ff', fade(lt, d, .2))); };
SHOTS[128] = (t, lt, d) => { show('cliff'); look('night', [0x0a1020, .004], .8, 1.0, 0x9ab0e0, [60, 80, 60], [6000, 0, 0]); hide(U.cPeople); const x = -26 + lt * 1.5; U.stretcher.position.set(x, 1.05, 26); U.stretcher.rotation.y = 0;
  U.bearers.forEach((m, i) => { at(m, x + (i === 0 ? 1.45 : i === 1 ? -1.45 : .2), 0, 26 + (i === 2 ? .9 : 0), facing([1, 0])); pose(m, t + i, { walk: true, speed: 6, armL: .4, armR: .4, elL: .5, elR: .5 }); }); at(U.lamp, x + 2.2, 1.1, 26.4); light(0, 'cliff', x + 2.2, 1.3, 26.6, 10, 0xffb060, 8);
  ct('cliff', lt, d, [x - 6, 2, 36, x, 1.2, 26], [x - 5, 2, 36, x + 1, 1.2, 26], [42, 42]); overlay(c => M.label(c, 'THE JOURNEY AFTER DARK', L.W / 2, L.H - 90, 42, '#dfe8ff', fade(lt, d, .2))); };
SHOTS[129] = (t, lt, d) => { show('village'); look('day', [0xd8e0d8, .002], 1.5, 2.4, 0xfff0dc, [-60, 70, 40], [3000, 0, 0]); hide(U.ruin, U.newPosts, U.plot, U.scale, U.scrap, U.vBombies, U.craters, Object.values(U.fam), U.farmers, U.buckets);
  U.vStakes.forEach((s, i) => { at(s, -20 + i * 1.4, 0, 18 + Math.sin(i * 1.3) * .3); s.scale.setScalar(1.6); }); U.warn.position.set(-22, 0, 18);
  const F = U.fam; at(F.girl, -12 + clamp(lt / 1) * 1.2, 0, 15.6, facing([0, 1])); pose(F.girl, t, { walk: lt < 1 }); at(F.mum, -12.8, 0, 15.2, facing([.5, 1])); pose(F.mum, t, { armR: 1.4, elR: .2 });
  ct('village', lt, d, [-9, 1.4, 11.6, -12.6, .9, 16.4], [-9.3, 1.4, 11.9, -12.6, .9, 16.4], [40, 40]); overlay(c => M.label(c, 'THE GROUND A PARENT WILL NOT LET A CHILD ENTER', L.W / 2, L.H - 90, 36, '#fff4e0', fade(lt, d, .2))); };
// 130-131 montages
SHOTS[130] = (t, lt, d) => { OV.noGL = true; overlay(c => memory(c, 'past', lt, d, true, 'TEACHING · HEALING · GROWING FOOD')); };
SHOTS[131] = (t, lt, d) => { OV.noGL = true; overlay(c => memory(c, 'now', lt, d, false, 'REBUILDING AROUND WHAT WAS LEFT')); };
// 132 last_plane
SHOTS[132] = (t, lt, d) => { show('sky'); look('dusk', [0xc8a088, .0006], 1.3, 2.0, 0xffc890, [300, 120, -200], [12000, 0, 0]); hide(U.b52s, U.cans); U.fall.forEach(b => b.position.y = -60); U.bomblets.count = 0; U.contrails.forEach(c => c.position.y = -60); U.sBlasts.forEach(b => b.userData.update(-1));
  U.sJets.forEach((j, i) => { if (i) { j.position.y = -60; return; } at(j, 30 + lt * 50, 300 + lt * 6, -lt * 40, -.5); });
  ct('sky', lt, d, [-20, 290, 30, 60, 310, -40], [-20, 290, 30, 100, 316, -70], [40, 40]); overlay(c => L.caption(c, '1973', 'THE LAST AIRCRAFT', fade(lt, d))); };
// 133 finale: one playground at a time
SHOTS[133] = (t, lt, d) => { schoolLook('day'); kidsPlay(t); teacherOn(t); const k = ease(clamp(lt / (d - 1)));
  ct('school', 0, 1, [lerp(6, 0, k), lerp(1.2, 70, k), lerp(20, 120, k), lerp(0, 0, k), lerp(1, 20, k), lerp(8, -200, k)], [lerp(6, 0, k), lerp(1.2, 70, k), lerp(20, 120, k), 0, lerp(1, 20, k), lerp(8, -200, k)], [lerp(44, 50, k), lerp(44, 50, k)]); };

// ===================== QA fixes (section 5) =====================
const back = (c, x, y, w, h, a = .62) => { c.save(); c.fillStyle = `rgba(10,8,6,${a})`; c.fillRect(x, y, w, h); c.restore(); };
const capB = (c, s1, s2, a) => { if (a <= 0) return; back(c, 0, L.H - 170, 1100, 130, .55 * a); L.caption(c, s1, s2, a); };
const lblB = (c, s, y, size, a, col = '#fff4e0') => { if (a <= 0) return; c.save(); c.font = `700 ${size}px Cinzel, serif`; const w = c.measureText(s).width + 60; c.restore(); back(c, L.W / 2 - w / 2, y - size - 12, w, size + 34, .6 * a); M.label(c, s, L.W / 2, y, size, col, a); };
function kidsGarden2(t, cx = 5, cz = -2) { const P = [[cx, cz, 2.4, 1.6], [cx + 4.2, cz + 1.2, 1.5, 1.1]]; U.attaKids.forEach((k, i) => { const [x0, z0, rx, rz] = P[i], a = t * (.65 + i * .15) + i * 1.7; at(k, x0 + Math.cos(a) * rx, 0, z0 + Math.sin(a) * rz, facing([-Math.sin(a) * rx, Math.cos(a) * rz])); pose(k, t + i * 1.3, { walk: true, run: true, speed: 9 }); }); }
function bomb(y = .02, sc = 2.2) { U.gb.position.set(SPOT[0], y, SPOT[2]); U.gb.scale.setScalar(sc); }
function headUp(m) { m.userData.rig.head.rotation.z = -.08; }
// 107 atta_find
SHOTS[107] = (t, lt, d) => { gardenLook(); kidsGarden2(t, 6, -3); const A = U.atta; at(A, SPOT[0] + .75, 0, SPOT[2] + .1, facing([-1, -.1])); pose(A, t, {});
  if (lt < 3.2) X.act(A, t, 'dig', { rate: 3 }); else { X.act(A, t, 'crouch'); headUp(A); A.userData.rig.head.rotation.z = -.3; } bomb(.04, 3.4);
  ct('garden', lt, d, [4, 1.8, 12, 0, .8, 4], [.9, .85, 8.2, -1.6, .25, 6], [40, 34]); overlay(c => capB(c, 'PHON VILLAGE', 'METRES FROM WHERE HIS CHILDREN PLAYED', fade(lt, d))); };
// 108 atta_think
SHOTS[108] = (t, lt, d) => { gardenLook(); kidsGarden2(t, 6, -3); const A = U.atta; at(A, SPOT[0] + .75, 0, SPOT[2] + .1, facing([-1, -.1])); pose(A, t, { look: Math.sin(lt * 2.4) * .6 }); X.act(A, t, 'crouch'); headUp(A); A.userData.rig.head.rotation.y = Math.sin(lt * 2.4) * .6; bomb(.04, 3.4);
  const h = headPos(A); cam.position.set(h.x - .9, h.y + .02, h.z + .75); cam.lookAt(h.x, h.y - .05, h.z); cam.fov = 36; cam.updateProjectionMatrix(); };
// 109 atta_bury: crouched, sweeping soil over it with his hands, mound grows
SHOTS[109] = (t, lt, d) => { gardenLook(); U.attaKids.forEach(m => m.position.y = -60); const A = U.atta; at(A, SPOT[0] + .62, 0, SPOT[2] + .05, facing([-1, 0])); pose(A, t, {}); X.act(A, t, 'crouch');
  const r = A.userData.rig, sw = Math.sin(t * 5); r.spine.rotation.z = -.75; r.arms[0].sh.rotation.z = .55 + sw * .25; r.arms[1].sh.rotation.z = .55 - sw * .25; r.arms[0].el.rotation.z = .1; r.arms[1].el.rotation.z = .1; r.head.rotation.z = -.2;
  const k = clamp(lt / (d - .3)); U.gb.position.set(SPOT[0], .04 - k * .16, SPOT[2]); U.gb.scale.setScalar(3.4); U.gMound.position.set(...SPOT); U.gMound.scale.set(.45 + k * .55, .06 + k * .3, .45 + k * .55);
  ct('garden', lt, d, [-.2, 1.25, 8.8, -1.6, .35, 6], [-.4, 1.15, 8.5, -1.6, .35, 6], [40, 38]); };
// 110 atta_fear
SHOTS[110] = (t, lt, d) => { gardenLook(); kidsGarden2(t, 2, 1.5); U.gMound.position.set(...SPOT); U.gMound.scale.set(1, .36, 1); const A = U.atta; const x = 2.2 - lt * .4; at(A, x, 0, SPOT[2] + .6, facing([-1, 0])); pose(A, t, {}); X.act(A, t, 'dig', { rate: 1.6 });
  ct('garden', lt, d, [-3.4, .35, 7.6, 0, .9, 4.5], [-3.3, .4, 7.4, .4, .9, 4.5], [42, 42]); };
// 111 team_arrive: pickup stops, team steps out from its near side, spaced
SHOTS[111] = (t, lt, d) => { gardenLook('morning'); U.gMound.position.set(...SPOT); U.gMound.scale.set(1, .36, 1); const p = ease(clamp(lt / 2)); at(U.pickup, lerp(30, 9, p), 0, 10, Math.PI);
  U.gTeam.forEach((m, i) => { const out = clamp((lt - 2.1 - i * .3) / .9); at(m, 6.6 + i * 1.3, 0, 11.4 + out * 1.6, facing([-.6, .4])); pose(m, t + i, { walk: out > 0 && out < 1 }); if (out <= 0) m.position.y = -60; });
  const A = U.atta; at(A, 2.4, 0, 12.4, facing([1, .1])); pose(A, t, lt > 3.4 ? { point: true, pointUp: -.4 } : {}); U.attaKids.forEach(m => m.position.y = -60);
  ct('garden', lt, d, [-4, 1.8, 19, 6, 1.2, 10.5], [-3, 1.7, 18, 6, 1.2, 10.5], [40, 40]); overlay(c => capB(c, '2022', 'A CLEARANCE TEAM ARRIVES', fade(lt, d))); };
// 113 team_destroy: controlled detonation in the distance, team behind the pickup
SHOTS[113] = (t, lt, d) => { gardenLook('day'); at(U.pickup, 1.5, 0, 15.5, .25); const DX = 22, DZ = 4;
  U.demo.position.set(DX, lt < 1.5 ? 0 : -60, DZ); U.gBlast.position.set(DX, 0, DZ); U.gBlast.userData.update(lt - 1.2, wp('garden', DX, 0, DZ));
  U.gTeam.forEach((m, i) => { at(m, 6.4 + i * 1.3, 0, 17.4 + (i % 2) * .4, facing([.7, -1])); pose(m, t + i, { look: .1 }); if (m.userData.detector) m.userData.detector.visible = true; });
  ct('garden', lt, d, [3, 2.6, 24, 17, 2.4, 4], [3.2, 2.65, 24.1, 17, 2.8, 4], [42, 42], lt > 1.2 && lt < 1.9 ? .03 : 0); overlay(c => capB(c, 'DESTROYED', 'WITH OTHER EXPLOSIVES FOUND ON HIS LAND', fade(lt, d))); };
// 118 school_return: from inside the yard, no duplicate title
SHOTS[118] = (t, lt, d) => { schoolLook(); kidsPlay(t); teacherOn(t); ct('school', lt, d, [0, 9, 31, 0, 2, -6], [0, 7.5, 27, 0, 2, -6], [42, 42]); };
// 119 school_bombs: high, clear view of the yard and its 30 stakes
SHOTS[119] = (t, lt, d) => { schoolLook('day'); U.kids.forEach(k => k.position.y = -60); teacherOn(t); U.schStakes.forEach(s => s.position.copy(s.userData.home)); U.schFlag.parent.visible = false;
  ct('school', lt, d, [-2, 30, 31, -2, 0, 14.5], [-2, 28.5, 30, -2, 0, 14.5], [44, 44]); overlay(c => { back(c, 40, 80, 360, 200, .6); M.label(c, '30', 220, 200, 120, '#f2c050', 1); M.label(c, 'IN ONE PLAYGROUND', 220, 250, 26, '#f2e8d2', 1); }); };
// 120 school_teacher: over her shoulder to the playing children, then her face
SHOTS[120] = (t, lt, d) => { schoolLook(); kidsPlay(t); teacherOn(t); const h = headPos(U.teacher);
  if (lt < 2.6) { const k = ease(clamp(lt / 2.6)); cam.position.set(h.x - .55, h.y + .15, h.z - .9 - k * .1); cam.lookAt(h.x + 2, h.y - 1, h.z + 12); cam.fov = 44; cam.updateProjectionMatrix(); return; }
  const k = ease(clamp((lt - 2.6) / (d - 2.6))); cam.position.set(h.x + .7, h.y + .02, h.z + 1.5 - k * .25); cam.lookAt(h.x - .05, h.y - .02, h.z); cam.fov = 32; cam.updateProjectionMatrix(); };
// 121 school_gate: parents clear of the posts, a rider on the motorbike
SHOTS[121] = (t, lt, d) => { schoolLook('morning'); teacherOn(t); U.kids.forEach((k, i) => { if (i > 7) { k.position.y = -60; return; } const p = clamp((lt - i * .35) / 3); at(k, (i % 2 ? .7 : -.7), 0, lerp(40, 28, p), facing([0, -1])); pose(k, t + i, { walk: p < 1 }); });
  U.parents.forEach((m, i) => { if (i === 4) return; const xs = [-5.2, -7, 5, 6.8]; at(m, xs[i], 0, 38.5 + (i % 2) * .8, facing([0, -1])); pose(m, t + i, { armR: i % 2 ? -2.4 : 0 }); });
  at(U.moto, 9.5, 0, 40, Math.PI / 2); const rd = U.parents[4]; at(rd, 9.5, .32, 40.15, facing([0, -1])); pose(rd, t, { sit: true, armL: 1.3, armR: 1.3, elL: .2, elR: .2 });
  ct('school', lt, d, [12, 2.2, 47, 0, 1.2, 32], [10, 2.0, 45, 0, 1.2, 32], [42, 42]); };
// 122 cave classroom memory: higher camera, no head in the lens
SHOTS[122] = (t, lt, d) => { show('cave'); look('night', null, .35, 0, 0xfff0dc, [0, 60, 0], [0, 0, 3000], [0x8a6a4a, 0x2a1a10]); light(0, 'cave', 4, 2.6, 40, 22, 0xffc070, 12); light(1, 'cave', -2, 2.6, 40, 14, 0xffb060, 12); L.S.background = new THREE.Color(0x050403);
  U.clKids.forEach((k, i) => pose(k, t + i, { sit: true })); pose(U.clTeacher, t, {}); X.act(U.clTeacher, t, 'teach');
  ct('cave', lt, d, [-6.8, 2.4, 41.4, 6, 1.0, 39.6], [-5.8, 2.3, 41.2, 6, 1.0, 39.6], [44, 42]);
  overlay(c => { c.globalCompositeOperation = 'color'; c.fillStyle = 'rgba(150,120,80,.8)'; c.fillRect(0, 0, L.W, L.H); c.globalCompositeOperation = 'source-over'; capB(c, 'VIENGXAY, 1960s', 'CLASSROOMS INSIDE THE MOUNTAINS', fade(lt, d)); }); };
// 123 deminer: 3/4 front, face visible, trowel at a clear bomb, stakes clear of him
SHOTS[123] = (t, lt, d) => { gardenLook('day', true); const m = U.gTeam[1]; at(m, -20, 0, 20, facing([0, -1])); pose(m, t, { kneel: true, armR: .9, elR: .8 + Math.sin(t * 5) * .15, armL: .6, elL: 1 }); m.userData.rig.head.rotation.z = -.35; if (m.userData.detector) m.userData.detector.visible = false;
  U.gb.position.set(-20.1, .045, 19.3); U.gb.scale.setScalar(3.2); U.gTrowel.position.set(-19.85, .08, 19.45);
  U.gStakes.forEach((s, i) => { at(s, -24.5 + (i % 4) * 1.1, 0, 15.5 + Math.floor(i / 4) * 1.4); s.scale.setScalar(1.4); });
  ct('garden', lt, d, [-17.9, 1.35, 17.3, -20, .62, 19.8], [-18.1, 1.3, 17.5, -20, .6, 19.8], [44, 42]); overlay(c => capB(c, 'CLEARANCE', 'ONE ITEM AT A TIME', fade(lt, d))); };
// 127 measure_hours: properly dark moonlit night
SHOTS[127] = (t, lt, d) => { show('village'); look('night', [0x0a1020, .006], .45, .5, 0x8aa0d0, [60, 80, 60], [3000, 0, 0]); hide(U.ruin, U.newPosts, U.warn, U.plot, U.scale, U.scrap, U.vStakes, U.vBombies, U.craters, Object.values(U.fam), U.buckets);
  U.farmers.forEach((m, i) => { at(m, -14 + i * 5.2, .1, 28 + (i % 3) * 2.2, facing([0, 1])); pose(m, t + i, {}); X.act(m, t * .6 + i, 'dig', { rate: 2 }); }); ct('village', lt, d, [-4, 2.6, 50, 0, 1, 30], [-3.6, 2.5, 49, 0, 1, 30], [40, 40]);
  overlay(c => { c.globalCompositeOperation = 'multiply'; c.fillStyle = 'rgb(120,140,190)'; c.fillRect(0, 0, L.W, L.H); c.globalCompositeOperation = 'source-over'; lblB(c, 'THE HOURS TO WORK A FIELD', L.H - 90, 42, fade(lt, d, .2), '#dfe8ff'); }); };
// 129 measure_ground: side view, the mother's arm holds the child back from the staked patch
SHOTS[129] = (t, lt, d) => { show('village'); look('day', [0xd8e0d8, .002], 1.5, 2.4, 0xfff0dc, [-60, 70, 40], [3000, 0, 0]); hide(U.ruin, U.newPosts, U.plot, U.scale, U.scrap, U.vBombies, U.craters, Object.values(U.fam), U.farmers, U.buckets);
  U.vStakes.forEach((s, i) => { at(s, -20 + i * 1.4, 0, 18 + Math.sin(i * 1.3) * .3); s.scale.setScalar(1.6); }); U.warn.position.set(-22, 0, 18);
  const F = U.fam; at(F.girl, -12 + clamp(lt / 1) * .9, 0, 16.1, facing([0, 1])); pose(F.girl, t, { walk: lt < 1 }); at(F.mum, -12.7, 0, 15.5, facing([.5, 1])); pose(F.mum, t, { armR: 1.4, elR: .2 });
  ct('village', lt, d, [-7.6, 1.25, 16.4, -12.2, .85, 16.6], [-7.8, 1.25, 16.5, -12.2, .85, 16.6], [42, 42]); overlay(c => lblB(c, 'THE GROUND A PARENT WILL NOT LET A CHILD ENTER', L.H - 90, 34, fade(lt, d, .2))); };
// 117 garden:4: a little brighter
const S117 = SHOTS[117]; SHOTS[117] = (t, lt, d) => { S117(t, lt, d); look('dusk', [0xc8a080, .0016], 1.5, 2.0, 0xffb080, [-100, 20, -60], [12000, 0, 6000]); };
// 133 finale: rise only partway, keep the yard and children readable, karst on the horizon
SHOTS[133] = (t, lt, d) => { schoolLook('day'); L.S.fog = new THREE.FogExp2(0xd8e0e0, .0007); kidsPlay(t); teacherOn(t); const k = ease(clamp(lt / (d - 1.2)));
  ct('school', 0, 1, [lerp(6, 0, k), lerp(1.2, 14, k), lerp(20, 42, k), 0, lerp(1, 0, k), lerp(8, 5, k)], [lerp(6, 0, k), lerp(1.2, 14, k), lerp(20, 42, k), 0, lerp(1, 0, k), lerp(8, 5, k)], [lerp(44, 50, k), lerp(44, 50, k)]); };

// ===================== QA fixes round 3 (section 5) =====================
const Q5 = {};
function initQ5() { if (Q5.done) return; Q5.done = true;
  // dust/smoke plume for the controlled detonation
  Q5.plume = new THREE.Group(); Q5.puffs = [...Array(14)].map((_, i) => { const m = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 1), new THREE.MeshToonMaterial({ color: i % 3 ? 0x9a8a72 : 0x7a6a58, transparent: true, opacity: .9, gradientMap: L.GRAD })); m.userData.noOutline = true; m.castShadow = false; Q5.plume.add(m); return m; });
  SETS.garden.add(Q5.plume); Q5.plume.position.y = -60;
  // probe held by the deminer: handle + rod, spans 0..1 along +y, scaled to length
  Q5.probe = new THREE.Group(); L.mesh(new THREE.CylinderGeometry(.012, .012, 1, 6), L.mat(0xb0b0b0, .3, .7), [0, .5, 0], [0, 0, 0], Q5.probe); Q5.probe.children[0].geometry.translate(0, 0, 0);
  const hd = L.mesh(new THREE.CylinderGeometry(.03, .03, .16, 8), L.mat(0xd8a020, .6), [0, .92, 0], [0, 0, 0], Q5.probe); SETS.garden.add(Q5.probe); Q5.probe.position.y = -60;
}
function plume(tt, x, z) { if (tt < 0 || tt > 6) { Q5.plume.position.y = -60; return; } Q5.plume.position.set(x, 0, z);
  Q5.puffs.forEach((m, i) => { const r = L.rng(i + 31), f = i / (Q5.puffs.length - 1), k = 1 - Math.pow(1 - clamp(tt / (.9 + f * 1.4)), 2), a = r() * 6.28, sp = (.2 + f * .8) * (.5 + r() * .5);
    m.position.set(Math.cos(a) * sp * (.5 + 1.6 * k) + tt * .25 * f, .4 + f * k * 9, Math.sin(a) * sp * (.5 + 1.6 * k)); m.scale.setScalar((.35 + f * .5 + r() * .25) * (.5 + 1.8 * k)); m.material.opacity = .78 * clamp(tt / .15) * (1 - clamp((tt - 2.2) / 3.5)); }); }
const S_gl = gardenLook; gardenLook = (...a) => { initQ5(); S_gl(...a); Q5.plume.position.y = -60; Q5.probe.position.y = -60; };
// 111 team_arrive: team members step out spaced across the view, no overlap
SHOTS[111] = (t, lt, d) => { gardenLook('morning'); U.gMound.position.set(...SPOT); U.gMound.scale.set(1, .36, 1); const p = ease(clamp(lt / 2)); at(U.pickup, lerp(30, 9, p), 0, 10, Math.PI);
  U.gTeam.forEach((m, i) => { const out = clamp((lt - 2.1 - i * .3) / .9); at(m, 6.0 + i * .95, 0, 11.6 + i * 1.0 + out * 1.4, facing([-.6, .4])); pose(m, t + i, { walk: out > 0 && out < 1 }); if (out <= 0) m.position.y = -60; });
  const A = U.atta; at(A, 2.4, 0, 12.4, facing([1, .1])); pose(A, t, lt > 3.4 ? { point: true, pointUp: -.4 } : {}); U.attaKids.forEach(m => m.position.y = -60);
  ct('garden', lt, d, [-4, 1.8, 19, 6, 1.2, 10.5], [-3, 1.7, 18, 6, 1.2, 10.5], [40, 40]); overlay(c => capB(c, '2022', 'A CLEARANCE TEAM ARRIVES', fade(lt, d))); };
// 113 team_destroy: charge on open ground, flash + dirt plume, team well back watching it
SHOTS[113] = (t, lt, d) => { gardenLook('day'); at(U.pickup, 1.5, 0, 15.5, .25); const DX = 15, DZ = 3;
  U.demo.position.set(DX, lt < 1.2 ? 0 : -60, DZ); U.gBlast.position.set(DX, 0, DZ); U.gBlast.userData.update(lt - 1.2, wp('garden', DX, 0, DZ)); plume(lt - 1.2, DX, DZ);
  U.gTeam.forEach((m, i) => { at(m, 4.6 + i * 1.3, 0, 17.4 + (i % 2) * .4, facing([DX - 4.6 - i * 1.3, DZ - 17.4])); pose(m, t + i, {}); if (m.userData.detector) m.userData.detector.visible = true; });
  ct('garden', lt, d, [3, 2.6, 24, 16, 2.6, 4], [3.2, 2.65, 24.1, 16, 3.0, 4], [42, 42], lt > 1.2 && lt < 1.9 ? .03 : 0);
  overlay(c => { if (lt > 1.2 && lt < 1.6) { c.fillStyle = `rgba(255,240,210,${.5 * (1 - (lt - 1.2) / .4)})`; c.fillRect(0, 0, L.W, L.H); } capB(c, 'DESTROYED', 'WITH OTHER EXPLOSIVES FOUND ON HIS LAND', fade(lt, d)); }); };
// 123 deminer: leaning in, probe from his hand to the soil beside the bomb, eyes on it
SHOTS[123] = (t, lt, d) => { gardenLook('day', true); const m = U.gTeam[1]; at(m, -20, 0, 20, facing([0, -1])); pose(m, t, { kneel: true }); if (m.userData.detector) m.userData.detector.visible = false;
  const r = m.userData.rig, w = Math.sin(t * 3) * .05; r.spine.rotation.z = -.55; r.arms[1].sh.rotation.z = .35 + w; r.arms[1].el.rotation.z = .5; r.arms[0].sh.rotation.z = .25; r.arms[0].el.rotation.z = .9; r.arms[0].sh.rotation.x = .2; r.head.rotation.z = -.45;
  U.gb.position.set(-20.1, .045, 19.3); U.gb.scale.setScalar(3.2); U.gTrowel.position.y = -60;
  m.updateMatrixWorld(true); const h = V3(); r.arms[1].hand.getWorldPosition(h); SETS.garden.worldToLocal(h); const tip = V3(-19.84, .02, 19.5 + w * .4);
  const dir = h.clone().sub(tip); const len = dir.length(); Q5.probe.position.copy(tip); Q5.probe.quaternion.setFromUnitVectors(V3(0, 1, 0), dir.normalize()); Q5.probe.scale.set(1, len + .06, 1);
  U.gStakes.forEach((s, i) => { at(s, -24.5 + (i % 4) * 1.1, 0, 15.5 + Math.floor(i / 4) * 1.4); s.scale.setScalar(1.4); });
  ct('garden', lt, d, [-17.9, 1.35, 17.3, -20, .62, 19.8], [-18.1, 1.3, 17.5, -20, .6, 19.8], [44, 42]); overlay(c => capB(c, 'CLEARANCE', 'ONE ITEM AT A TIME', fade(lt, d))); };
// 125 ledger:2: the new column of measurements written in
SHOTS[125] = (t, lt, d) => { OV.noGL = true; overlay(c => LM.ledger(c, lt, [['The distance to shelter', ''], ['The hours to work a field', ''], ['The journey to a hospital after dark', ''], ['The ground a child may not enter', '']], { title: 'ANOTHER SET OF MEASUREMENTS', paper: '#f0e6d0', gap: .55 })); };
