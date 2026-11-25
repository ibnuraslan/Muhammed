// ===================== LAOS 1: the school, the scale, the neutrality that failed (cues 0-24) =====================
import * as L from './lib3.js';
import * as M from './maps.js';
import * as X from './lao.js';
import * as LM from './laomaps.js';
import * as Z from './laosets.js';
const { THREE, cam, U, V3, at, lerp, clamp, ease, look, show, fx, overlay, OV, pose, facing, SETS } = L;
const { ct, wp, light, hide } = Z;
export const RANGE = { from: 0, to: 24 };
export const SHOTS = {};
const fade = (lt, d, a = .4) => clamp(lt / a) * (1 - clamp((lt - d + a) / a));
const headPos = m => { const p = V3(); m.updateMatrixWorld(true); m.userData.rig.head.getWorldPosition(p); return p; };
// readable text: dark rounded backing behind a label
function tag(c, s, x, y, size = 30, col = '#f2e8d2', a = 1, align = 'center') { if (a <= 0) return; c.save(); c.globalAlpha = a * .62; c.font = `700 ${size}px Cinzel, serif`; const w = c.measureText(s).width, x0 = align === 'left' ? x : x - w / 2; c.fillStyle = '#100a06'; const r = size * .3, bx = x0 - size * .45, by = y - size * 1.02, bw = w + size * .9, bh = size * 1.42; c.beginPath(); c.moveTo(bx + r, by); c.arcTo(bx + bw, by, bx + bw, by + bh, r); c.arcTo(bx + bw, by + bh, bx, by + bh, r); c.arcTo(bx, by + bh, bx, by, r); c.arcTo(bx, by, bx + bw, by, r); c.fill(); c.restore(); M.label(c, s, x, y, size, col, a, align); }
function band(c, a = 1) { if (a <= 0) return; const g = c.createLinearGradient(0, L.H - 300, 0, L.H); g.addColorStop(0, 'rgba(8,5,3,0)'); g.addColorStop(1, `rgba(8,5,3,${.7 * a})`); c.fillStyle = g; c.fillRect(0, L.H - 300, L.W, 300); }
const arrowP = (c, a, b, p, col, w, o) => { if (p > .08) LM.arrow(c, a, b, p, col, w, o); };
function camAtWorld(p, q, fov) { cam.position.copy(p); cam.lookAt(q); cam.fov = fov; cam.updateProjectionMatrix(); }
export async function build() {
  Z.skies(); Z.schoolSet(); Z.villageSet(); Z.cliffSet(); Z.skySet(); Z.hallSet(); Z.trailSet();
  U.ghost = [0, 1, 2].map(() => { const j = X.jet({ bombs: false }); SETS.school.add(j); j.traverse(m => { if (m.isMesh) { m.material = m.material.clone(); m.material.transparent = true; } }); return j; });
  U.vBlasts = [0, 1, 2].map(() => { const b = L.blast({ size: 8 }); SETS.village.add(b); return b; });
  { const tx = L.textTex([['DECLARATION', 50, 150], ['ON THE NEUTRALITY', 31, 222], ['OF LAOS', 50, 292], ['Geneva, 23 July 1962', 30, 372], ['', 20, 420]], { w: 512, h: 700, bg: '#efe6d0', fg: '#2a1a10', draw: x => { x.strokeStyle = '#6a5a48'; x.lineWidth = 2; for (const yy of [460, 500, 540, 580]) { x.beginPath(); x.moveTo(70, yy); x.lineTo(442, yy); x.stroke(); } x.beginPath(); x.moveTo(80, 640); x.lineTo(300, 640); x.stroke(); } }); U.doc.material.map = tx; U.doc.material.needsUpdate = true; }
  L.mesh(new THREE.BoxGeometry(5.2, .7, .04), L.mat(0x2a5a8a, .7), [0, 2.6, 33.95], [0, 0, 0], SETS.school); // backing so the gate sign never reads mirrored from inside the yard
  // teacher reads clearly as a woman in her close-up: shoulder-length hair framing the face, a Lao sash (pha biang), soft lips
  { const hd = U.teacher.userData.rig.head, sp = U.teacher.userData.rig.spine, hm = L.mat(0x141010, .85), gold = L.mat(0xc8a040, .7);
    for (const s of [-1, 1]) L.mesh(new THREE.BoxGeometry(.09, .27, .045), hm, [-.02, -.06, s * .108], [0, 0, 0], hd);
    L.mesh(new THREE.BoxGeometry(.1, .3, .21), hm, [-.075, -.07, 0], [0, 0, 0], hd);
    L.mesh(new THREE.SphereGeometry(.03, 8, 6), L.mat(0xe8e0f0, .6), [-.06, .07, .1], [0, 0, 0], hd); // jasmine flower by the bun
    for (const x of [.176, -.176]) L.mesh(new THREE.BoxGeometry(.02, .64, .085), gold, [x, .27, .0], [.62 * Math.sign(x), 0, 0], sp); }
  // dinner on the floor: woven mat, low rattan table, sticky-rice basket and bowls (hidden outside shot 9)
  U.mealSet = new THREE.Group(); L.mesh(new THREE.CylinderGeometry(2.0, 2.0, .02, 28), L.mat(0x7a6440, .95), [0, .01, 0], [0, 0, 0], U.mealSet);
  L.mesh(new THREE.CylinderGeometry(.42, .36, .2, 20), L.mat(0x8a5a2a, .7), [0, .1, 0], [0, 0, 0], U.mealSet); L.mesh(new THREE.CylinderGeometry(.12, .09, .16, 12), L.mat(0xc8a868, .9), [.08, .28, .06], [0, 0, 0], U.mealSet);
  for (const [x, z] of [[-.2, .08], [.04, -.22], [-.08, .24]]) L.mesh(new THREE.CylinderGeometry(.08, .05, .05, 12), L.mat(0xe8e2d4, .6), [x, .225, z], [0, 0, 0], U.mealSet);
  SETS.village.add(U.mealSet); U.mealSet.visible = false;
  // geneva: solid pedestal under the long table, chairs turned so their backs are behind the delegates
  { const hall = SETS.hall; L.mesh(new THREE.BoxGeometry(15.2, .74, 1.0), L.mat(0x3a200e, .8), [0, .37, -1], [0, 0, 0], hall);
    hall.children.forEach(c => { if (c.isGroup && c.children.length === 6 && Math.abs(c.position.z + 2.6) < .01) c.rotation.y = -Math.PI / 2; if (c.isGroup && c.children.length === 6 && Math.abs(c.position.z - .6) < .01) c.rotation.y = Math.PI / 2; }); }
  // treaty on the trail: title sized to fit the paper
  U.treaty.material.map = L.textTex([['DECLARATION', 56, 170], ['ON THE', 44, 250], ['NEUTRALITY', 52, 325], ['OF LAOS', 56, 405], ['GENEVA · 1962', 34, 520]], { w: 512, h: 680, bg: '#ece2c8', fg: '#2a1a10' }); U.treaty.material.needsUpdate = true;
  // cave wall around the mouths: break up the smooth flattened patch into faceted dark rock
  { const wall = SETS.cliff.children.find(m => m.geometry && m.geometry.parameters && m.geometry.parameters.width === 260);
    if (wall) { const geo = wall.geometry, p = geo.attributes.position, cl = geo.attributes.color, h = i => { const v = Math.sin(i * 12.9898 + 78.233) * 43758.5453; return v - Math.floor(v); };
      for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i) - 1; for (const [mx, mr] of [[-30, 4.3], [8, 3.8], [55, 5.3]]) { const dx = Math.abs(x - mx) - (mr + 1.5), dy = y - (mr + 2.5), dd = Math.max(dx, dy, 0); if (dd > 6) continue; const w = 1 - dd / 6, r = Math.hypot(x - mx, y), n = h(i) * 2 - 1;
          if (r > mr + .9) p.setZ(i, p.getZ(i) + n * 1.1 * w); else p.setZ(i, p.getZ(i) - Math.abs(n) * .5 - .2);
          const k = (.62 + h(i + 7) * .25) * (1 - w) + (.5 + h(i + 3) * .22) * w; const o = 1 - w * .45; cl.setXYZ(i, cl.getX(i) * o + .5 * k * w * .45, cl.getY(i) * o + .47 * k * w * .45, cl.getZ(i) * o + .42 * k * w * .45); } }
      geo.computeVertexNormals(); p.needsUpdate = true; cl.needsUpdate = true; wall.material.flatShading = true; wall.material.needsUpdate = true; }
    U.caveMouths.forEach(m => { const rim = m.children[1], g2 = rim.geometry, q = g2.attributes.position; for (let i = 0; i < q.count; i++) { const v = Math.sin(i * 7.31 + 1.7) * 9137.13, n = v - Math.floor(v); q.setXYZ(i, q.getX(i) * (1 + (n - .5) * .12), q.getY(i) * (1 + (n - .5) * .12), q.getZ(i) + (n - .5) * .5); } g2.computeVertexNormals(); rim.material = rim.material.clone(); rim.material.color.set(0x5a544a); rim.material.flatShading = true; rim.material.needsUpdate = true; }); }
  U.splash = [...Array(6)].map(() => { const s = L.smoke(V3(), { n: 8, color: 0x8a7a5a, wind: [0, 0], rise: 1.2, size: .5, grow: 2, life: .8, opacity: .8 }); return fx(s); });
}
// ---- shared choreography ----
function kidsPlay(t, o = {}) { const K = U.kids;
  for (let i = 0; i < 6; i++) { const a = t * .55 + i * 1.05, r = 5.5 + (i % 2) * 1.2; at(K[i], Math.cos(a) * r - 2, 0, 9 + Math.sin(a) * r * .7, facing([-Math.sin(a), Math.cos(a) * .7])); pose(K[i], t + i, { walk: true, run: true, speed: 9 }); }
  const per = 1.6, ph = (t % per) / per, dir = Math.floor(t / per) % 2; const A = [10, 0, 5], B = [14.5, 0, 8.5];
  at(K[6], ...A, facing([B[0] - A[0], B[2] - A[2]])); at(K[7], ...B, facing([A[0] - B[0], A[2] - B[2]])); [6, 7].forEach(i => { pose(K[i], t, { armR: 1.2 + Math.sin(t * 4) * .3, elR: .5 }); });
  const s = dir ? 1 - ph : ph; U.ball.position.set(lerp(A[0], B[0], s), 1.0 + Math.sin(ph * Math.PI) * 2.2, lerp(A[2], B[2], s));
  for (let i = 8; i < 12; i++) { const a = (i - 8) / 4 * Math.PI * 2; at(K[i], -9 + Math.cos(a) * 1.5, 0, 14 + Math.sin(a) * 1.5, facing([-Math.cos(a), -Math.sin(a)])); pose(K[i], t + i, {}); X.act(K[i], t + i, 'cheer'); }
  for (let i = 12; i < 16; i++) { at(K[i], 3.6 + (i - 12) * 1.1, 0, 9.2 + (i % 2) * .7, facing([.4, 1])); pose(K[i], t, {}); X.act(K[i], t + i, 'crouch'); }
  if (o.noCrouch) for (let i = 12; i < 16; i++) K[i].position.y = -60; }
function teacherOn(t, look = 0, nod = 0) { at(U.teacher, -5.6, .5, -8.9, facing([.2, 1])); pose(U.teacher, t, { look, nod, armL: .1, armR: .1, elL: 1.2, elR: 1.2 }); }
function schoolLook(sky = 'morning', sunI = 2.6) { show('school'); look(sky, [0xd8e0e0, .0016], 1.5, sunI, 0xfff0d8, [-60, 70, 50], [0, 0, 0], [0xdfe6f0, 0x8a7a5a]); hide(U.team, U.parents, U.moto, U.ghost); U.schStakes.forEach(s => s.position.y = -60); U.schBombie.position.set(8.4, 0, 11.4); U.ball.position.y = -60; U.schFlag.parent.visible = true; }
function villageLook(sky = 'day', fog = [0xd8e0d8, .002], hemi = 1.5, sun = 2.4, sunCol = 0xfff0dc, sunPos = [-60, 70, 40]) { show('village'); look(sky, fog, hemi, sun, sunCol, sunPos, [3000, 0, 0]);
  hide(U.ruin, U.newPosts, U.warn, U.plot, U.scale, U.scrap, U.vStakes, U.vBombies, U.craters, Object.values(U.fam), U.farmers, U.buckets); U.vfire.position.y = -60; U.houses[1].position.y = 0; U.vBlasts.forEach(b => b.userData.update(-1)); if (U.mealSet) U.mealSet.visible = false; }
// ===== 0 school_wide =====
SHOTS[0] = (t, lt, d) => { schoolLook(); kidsPlay(t); teacherOn(t, -.2);
  ct('school', lt, d, [0, 6.5, 46, 0, 2.5, -4], [-2, 4.5, 30, 0, 2.2, 0], [40, 38]); };
// ===== 1 teacher_close =====
SHOTS[1] = (t, lt, d) => { schoolLook(); kidsPlay(t); teacherOn(t, .25 - lt * .08, -.05 - clamp(lt / d) * .22);
  const h = headPos(U.teacher); const k = ease(clamp(lt / d)); camAtWorld(V3(h.x + .55 + k * .1, h.y + .04, h.z + 1.55 - k * .25), V3(h.x - .05, h.y - .02, h.z), 32); };
// ===== 2 teacher_memory =====
SHOTS[2] = (t, lt, d) => { schoolLook(); kidsPlay(t); teacherOn(t, 0, -.25);
  const K = U.kids; at(K[13], 5.6, 0, 10.6, facing([.3, -1])); X.act(K[13], t, 'crouch'); U.stick.position.y = -60;
  if (lt < 3.4) { at(U.teacher, -6.5, .5, -8.7, facing([.3, 1])); ct('school', lt, 3.4, [-5.4, 2.05, -9.0, 6, .6, 10], [-5.5, 2.0, -8.85, 7, .4, 10], [42, 36]); return; }
  const q = lt - 3.4; ct('school', q, d - 3.4, [11.2, 1.1, 14.4, 8.4, .1, 11.4], [9.2, .3, 12.4, 8.4, .05, 11.4], [34, 30]);
  overlay(c => { c.fillStyle = `rgba(20,10,0,${.12})`; c.fillRect(0, 0, L.W, L.H); }); };
// ===== 3 clearance_school =====
SHOTS[3] = (t, lt, d) => { schoolLook('day'); teacherOn(t, 0); U.kids.forEach(k => k.position.y = -60); U.schBombie.position.y = -60;
  U.team.forEach((m, i) => { const x = -18 + i * 5 + lt * 2.2, z = 22 - lt * 1.2; at(m, x, 0, z, facing([0, -1])); pose(m, t + i, { walk: true, speed: 3 }); if (i < 3) X.act(m, t + i, 'sweep'); });
  const n = Math.floor(clamp((lt - .3) / (d - 1.2)) * 30); U.schStakes.forEach((s, i) => { s.position.copy(s.userData.home); if (i >= n) s.position.y = -60; else { const k = clamp((lt - .3 - i * (d - 1.2) / 30) / .2); s.position.y = -.5 * (1 - k); } });
  ct('school', lt, d, [-4, 9, 36, 2, 0, 10], [-2, 7.5, 32, 2, 0, 10], [42, 42]);
  overlay(c => { const v = n; M.label(c, String(v), L.W - 220, 190, 120, '#f2c050', clamp(lt / .4)); M.label(c, 'UNEXPLODED BOMBS', L.W - 220, 240, 26, '#f2e8d2', clamp(lt / .4)); }); };
// ===== 4 planes_ghost =====
SHOTS[4] = (t, lt, d) => { schoolLook('day'); kidsPlay(t, { noCrouch: true }); teacherOn(t); U.schFlag.parent.visible = false;
  U.ghost.forEach((j, i) => { const x = -160 + lt * 110 + i * 14, a = clamp(Math.sin(clamp((lt - .1) / (d - .6)) * Math.PI)) * .55; at(j, x * .5, 34 + i * 4, -4 - i * 9); j.rotation.set(0, 0, -.05); j.traverse(m => { if (m.isMesh && m.material) m.material.opacity = a; }); });
  ct('school', lt, d, [2, 1.4, 24, -10, 30, -8], [2, 1.4, 24, 8, 32, -8], [50, 50]);
  overlay(c => { c.globalCompositeOperation = 'color'; c.fillStyle = `rgba(150,120,80,${.5 * clamp(Math.sin(clamp(lt / d) * Math.PI) * 1.4)})`; c.fillRect(0, 0, L.W, L.H); c.globalCompositeOperation = 'source-over'; }); };
// ===== 5 children_run =====
SHOTS[5] = (t, lt, d) => { schoolLook('day'); teacherOn(t); kidsPlay(t);
  [0, 1, 2, 3].forEach(i => { const k = U.kids[i]; const x = -10 + lt * 5.2 + i * 1.4 - (i % 2) * .8; at(k, x, 0, 16 + (i % 2) * 1.2 - i * .3, facing([1, 0])); pose(k, t + i * .4, { walk: true, run: true, speed: 11 }); });
  ct('school', lt, d, [-6, .9, 21.5, -3, .9, 16], [3, .9, 21.5, 6, .9, 16], [42, 42]); };
// ===== 6 bomb_ground =====
SHOTS[6] = (t, lt, d) => { schoolLook('day'); teacherOn(t);
  U.kids.forEach((k, i) => { if (i > 5) { k.position.y = -60; return; } const x = -4 + ((lt * 4.5 + i * 2.7) % 18); at(k, x, 0, 9.0 - (i % 3) * .8, facing([1, 0])); pose(k, t + i, { walk: true, run: true, speed: 11 }); });
  ct('school', lt, d, [9.02, .085, 11.95, 8.4, .03, 11.4], [8.85, .075, 11.8, 8.4, .035, 11.4], [30, 26]); };
// ===== 7 laos_map =====
SHOTS[7] = (t, lt, d) => { OV.noGL = true; overlay(c => { const k = ease(clamp(lt / 2.6)); const pr = LM.viewLerp([103, 15, 26], [104, 18.2, 10.5], k);
  LM.base(c, pr, { hl: [['Laos', '#c8a060', clamp((lt - .6) / .6)]] }); LM.outline(c, pr, 'Laos', '#f2d080', 4, 12 * clamp((lt - .6) / .6));
  LM.clipLaos(c, pr, () => LM.bombDots(c, pr, clamp((lt - 2.4) / 4.8)));
  M.vignette(c, .5); LM.name(c, pr, 'LAOS', 102.4, 19.6, 46, clamp((lt - .8) / .5)); tag(c, 'LAOS  ·  1964 – 1973', 70, 110, 40, '#f2e8d2', clamp(lt / .5), 'left');
  const tons = Math.round(2000000 * ease(clamp((lt - 2.4) / 4.8))), ta = clamp((lt - 2.4) / .4); tag(c, tons.toLocaleString('en-US') + '+ TONNES', L.W - 330, 200, 54, '#f2c050', ta); tag(c, 'OF ORDNANCE DROPPED', L.W - 330, 262, 26, '#f2e8d2', ta); }); };
// ===== 8 tonnage: B-52 formation =====
SHOTS[8] = (t, lt, d) => { show('sky'); look('dusk', [0xb8907a, .0011], 1.3, 2.2, 0xffc890, [300, 120, -200], [12000, 0, 0]);
  U.b52s.forEach((b, i) => { at(b, 260 - lt * 32 - i * 40, 420 + i * 6, -40 + i * 48, Math.PI); }); U.sJets.forEach(j => j.position.y = -60); U.cans.forEach(c => c.position.y = -60); U.bomblets.count = 0;
  U.fall.forEach((b, i) => { const bi = i % 3, k = Math.floor(i / 3), tt = lt - k * .32; const B = U.b52s[bi]; if (tt < 0) { b.position.y = -60; return; } const x0 = 260 - (lt - tt) * 32 - bi * 40; b.position.set(x0 - tt * 20, 418 + bi * 6 - 4.9 * tt * tt, -40 + bi * 48 + ((k % 2) - .5) * 3); b.rotation.set(0, Math.PI, -Math.min(1.3, tt * .7)); });
  U.sBlasts.forEach(b => b.userData.update(-1));
  ct('sky', lt, d, [150, 380, 140, 120, 388, 0], [110, 372, 150, 60, 383, 0], [44, 44]);
  overlay(c => { band(c, fade(lt, d)); L.caption(c, 'THE MOST HEAVILY BOMBED COUNTRY', 'PER PERSON, IN HISTORY', fade(lt, d)); }); };
// ===== 9 life_split: 1960s family meal, jet overhead =====
function famMeal(t, up) { const F = U.fam, c = [-11, 1.5]; U.mealSet.position.set(c[0], 0, c[1]); U.mealSet.visible = true;
  ['dad', 'mum', 'gran', 'boy', 'girl'].forEach((k, i) => { const a = i / 5 * Math.PI * 2 + 1.32, r = (k === 'boy' || k === 'girl') ? 1.0 : 1.2, x = c[0] + Math.cos(a) * r, z = c[1] + Math.sin(a) * r, m = F[k];
    at(m, x, 0, z, facing([-Math.cos(a), -Math.sin(a)])); pose(m, t + i, { armR: .55, elR: 1.0, armL: .3, elL: .8 }); X.act(m, t, 'floorSit'); if (up) X.act(m, t, 'lookUp'); }); }
SHOTS[9] = (t, lt, d) => { villageLook('day'); famMeal(t, lt > 3.1);
  const j = U.sJets[0]; // borrow: a jet in the village set
  if (!U.vJet) { U.vJet = X.jet(); SETS.village.add(U.vJet); } at(U.vJet, 200 - (lt - 2.6) * 140, 40, -60); U.vJet.rotation.set(0, Math.PI, .2); if (lt < 2.6) U.vJet.position.y = -60;
  ct('village', lt, d, [-2, 3.2, 9, -11, 1, 1.5], [-6.5, 1.3, 5.2, -11, .9, 1.5], [36, 36], lt > 3 && lt < 3.8 ? .02 : 0); };
// ===== 10 family_bunker =====
SHOTS[10] = (t, lt, d) => { villageLook('day', [0xd8d0c0, .003]); const F = U.fam, ent = V3(-14 + Math.sin(.3) * 2.2, 0, 10 + Math.cos(.3) * 2.2);
  ['gran', 'girl', 'mum', 'boy', 'dad'].forEach((k, i) => { const m = F[k], p = clamp((lt + 1.0 - i * .32) / 1.6); const x = lerp(ent.x + 3.2 + i * .9, ent.x, p), z = lerp(ent.z + 2.0 + (i % 2) * .3, ent.z, p); at(m, x, -clamp((p - .8) / .2) * 1.2, z, facing([ent.x - x, ent.z - z])); pose(m, t + i, { walk: true, speed: 9 }); });
  ct('village', lt, d, [-7, 1.6, 20, -13.2, 1, 11.5], [-8, 1.5, 19, -13.2, .9, 11.8], [38, 36]); };
// ===== 11 cave_hospital_teaser =====
SHOTS[11] = (t, lt, d) => { show('cliff'); look('dusk', [0x8a7a80, .002], 1.2, 1.4, 0xffb080, [-80, 30, 60], [6000, 0, 0]); hide(U.cPeople); U.plFlag.parent.visible = false;
  const p = clamp(lt / d), A = [9.8, -20.6], B = [8.3, -24.0], x = lerp(A[0], B[0], p), z = lerp(A[1], B[1], p), dx = B[0] - A[0], dz = B[1] - A[1], L0 = Math.hypot(dx, dz), ux = dx / L0, uz = dz / L0;
  U.stretcher.position.set(x, 1.05, z); U.stretcher.rotation.y = Math.atan2(-dz, dx);
  U.bearers.forEach((m, i) => { const off = i === 0 ? 1.45 : i === 1 ? -1.45 : -.4; const sx = i === 2 ? -uz * .95 : 0, sz = i === 2 ? ux * .95 : 0; at(m, x + ux * off + sx, 0, z + uz * off + sz, facing([dx, dz])); pose(m, t + i, i === 2 ? { walk: true, speed: 6, armR: .25, elR: .2 } : { walk: true, speed: 6, armL: .4, armR: .4, elL: .6, elR: .6 }); });
  const hp = V3(); U.bearers[2].updateMatrixWorld(true); U.bearers[2].userData.rig.arms[1].hand.getWorldPosition(hp); U.lamp.position.set(hp.x - 6000, hp.y - .16, hp.z);
  light(0, 'cliff', hp.x - 6000, hp.y, hp.z, 16, 0xffb060, 10); light(1, 'cliff', 8, 1.6, -23.9, 12, 0xffa050, 6);
  ct('cliff', lt, d, [14.5, 1.9, -13.5, 8.6, 1.4, -23.4], [13.4, 1.8, -15.2, 8.4, 1.4, -23.8], [40, 38]); };
// ===== 12 night_farm_teaser =====
function farmersPaddy(t, set = 'village', baseZ = 30) { U.farmers.forEach((m, i) => { at(m, -14 + i * 5.2, .1, baseZ - 2 + (i % 3) * 2.2, facing([0, 1])); pose(m, t + i, {}); X.act(m, t * .6 + i, 'dig', { rate: 2 }); }); }
SHOTS[12] = (t, lt, d) => { villageLook('night', [0x0a1020, .003], .9, 1.1, 0x9ab0e0, [60, 80, 60]); farmersPaddy(t);
  ct('village', lt, d, [-6, 1.6, 42, 0, 1.0, 30], [-2, 1.4, 39, 0, .9, 30], [40, 38]); };
// ===== 13 aftermath_field =====
SHOTS[13] = (t, lt, d) => { villageLook('dawn', [0xc8b0a0, .004], 1.1, 1.5, 0xffc898, [-120, 30, -60]); U.craters.forEach(c => c.position.copy(c.userData.home));
  U.vsmoke.forEach((s, i) => { const c = U.craters[i]; s.visible = true; s.userData.update(t + i, V3(3000 + c.position.x, .5, c.position.z)); });
  at(U.fam.dad, -8, 0, 24, facing([1, .8])); pose(U.fam.dad, t, {});
  ct('village', lt, d, [-30, 2.4, 64, 2, 1, 30], [-26, 2.2, 60, 2, 1, 30], [38, 38]); };
// ===== 14 duds_rain =====
SHOTS[14] = (t, lt, d) => { villageLook('grey', [0x9a9a98, .004], 1.2, 1.2); U.craters.forEach(c => c.position.copy(c.userData.home));
  const P0 = [[-1, 33.5], [1.3, 34.6], [.2, 35.4], [-2.2, 35.1], [2.6, 33.2], [-.6, 32.6]]; const sl = .45;
  U.vBombies.forEach((b, i) => { const tl = lt * sl * 2.2 - i * .12; const y = Math.max(.08, 8 - 9.8 * tl * tl * .8); at(b, P0[i][0], y, P0[i][1]); b.rotation.set(tl * 6, tl * 4, 0); b.scale.setScalar(3.6);
    const sp = U.splash[i]; if (y <= .09 && tl > 0) { sp.visible = true; sp.userData.update(clamp(tl - Math.sqrt(8 / 7.84)) * 1.2, V3(3000 + P0[i][0], .15, P0[i][1])); } });
  U.vBlasts.forEach((b, i) => { b.position.set(-40 + i * 40, 0, -60 - i * 20); b.userData.update(lt - .4 - i * .7, V3(3000 - 40 + i * 40, 0, -60)); });
  ct('village', lt, d, [1.6, 1.6, 38.6, 0, .6, 33.8], [1.2, 1.3, 37.8, 0, .4, 34], [40, 36]); };
// ===== 15-19 maps =====
SHOTS[15] = (t, lt, d) => { OV.noGL = true; overlay(c => { const pr = LM.viewLerp([106, 16, 17], [105.4, 16.4, 15], ease(clamp(lt / d))); LM.base(c, pr, { hl: [['Vietnam', '#b86a4a', clamp(lt / .6)]] }); LM.name(c, pr, 'VIETNAM', 108.6, 14.6, 44, clamp((lt - .3) / .5)); LM.city(c, pr, 'Hanoi', { a: clamp((lt - .8) / .4) }); LM.city(c, pr, 'Saigon', { a: clamp((lt - 1.1) / .4) }); M.vignette(c, .5); }); };
SHOTS[16] = (t, lt, d) => { OV.noGL = true; overlay(c => { const pr = LM.viewLerp([105.4, 16.4, 15], [104.2, 17.4, 13], ease(clamp(lt / 2))); LM.base(c, pr, { hl: [['Vietnam', '#b86a4a', .7], ['Laos', '#d8b060', clamp((lt - .5) / .6)]] });
  const f = M.byName('Laos'); c.save(); M.pathFeature(c, pr, f); c.setLineDash([2400 * clamp((lt - .8) / 2.6), 99999]); c.strokeStyle = '#ffe090'; c.lineWidth = 5; c.shadowColor = '#ffd060'; c.shadowBlur = 14; c.stroke(); c.restore();
  M.vignette(c, .5); const N = (s2, lo, la, sz, a) => { const [x, y] = pr(lo, la); tag(c, s2, x, y, sz, '#f2e8d2', a); }; N('LAOS', 102.6, 19.4, 50, clamp((lt - .6) / .5)); N('VIETNAM', 108.4, 14.4, 34, 1); N('THAILAND', 100.4, 15.6, 32, 1); N('CHINA', 101.6, 22.4, 32, 1); N('CAMBODIA', 104.6, 12.8, 32, 1); }); };
SHOTS[17] = (t, lt, d) => { OV.noGL = true; overlay(c => { const pr = LM.view(104, 17.4, 15); LM.base(c, pr, { hl: [['Laos', '#d8b060']] }); const P = (lo, la) => pr(lo, la);
  M.vignette(c, .5); arrowP(c, P(104, 24.6), P(103.2, 20.4), ease(clamp((lt - .3) / 1)), '#c8241c', 16); arrowP(c, P(107.5, 21.5), P(105, 18.6), ease(clamp((lt - .8) / 1)), '#c8241c', 16, { bend: 40 });
  arrowP(c, P(98.4, 13), P(101.8, 16.8), ease(clamp((lt - 1.6) / 1)), '#2a5ab0', 16); arrowP(c, P(110.5, 13.5), P(106.2, 15.6), ease(clamp((lt - 2.1) / 1)), '#2a5ab0', 16, { bend: -40 });
  const T2 = (s2, lo, la, col, a) => { const [x, y] = P(lo, la); tag(c, s2, x, y, 32, col, a); }; T2('COMMUNIST POWERS', 109.6, 22.7, '#ff9a80', clamp((lt - 1) / .4)); T2('UNITED STATES & ALLIES', 102.8, 12.3, '#a8c8ff', clamp((lt - 2.4) / .4));
  T2('LAOS', 102.6, 19.2, '#f2e8d2', 1); tag(c, 'THE COLD WAR  ·  SOUTHEAST ASIA', 70, 110, 38, '#f2e8d2', clamp(lt / .5), 'left'); }); };
function factionZones(c, pr, a) { LM.clipLaos(c, pr, () => { c.globalAlpha = a[0]; c.fillStyle = '#4a72b8'; c.fillRect(0, 0, L.W, L.H);
  c.globalAlpha = a[2]; c.fillStyle = '#c8402a'; c.beginPath(); const q = [[103.6, 23], [108, 23], [108, 13], [106.2, 13], [105.6, 16.2], [104.4, 18.2], [103.6, 19.2]].map(p => pr(...p)); q.forEach((p, i) => i ? c.lineTo(...p) : c.moveTo(...p)); c.fill();
  c.globalAlpha = a[1]; c.fillStyle = '#e0b030'; const [x, y] = pr(103.1, 19.4), [x2] = pr(103.9, 19.4); c.beginPath(); c.ellipse(x, y, (x2 - x), (x2 - x) * .8, 0, 0, 7); c.fill(); }); }
SHOTS[18] = (t, lt, d) => { OV.noGL = true; overlay(c => { const pr = LM.view(104, 18, 11); LM.base(c, pr, { hl: [['Laos', '#c8b890']] }); c.fillStyle = 'rgba(10,8,6,.45)'; c.fillRect(0, 0, L.W, L.H); LM.base(c, pr, { hl: [] }); c.globalAlpha = 1; LM.clipLaos(c, pr, () => { c.fillStyle = '#d8c8a0'; c.fillRect(0, 0, L.W, L.H); }); LM.outline(c, pr, 'Laos', '#fff0c0', 4, 16); M.label(c, 'A STRUGGLE FOR POWER', L.W / 2, L.H - 90, 44, '#f2e8d2', clamp(lt / .5)); M.vignette(c, .55); }); };
SHOTS[19] = (t, lt, d) => { OV.noGL = true; overlay(c => { const pr = LM.view(104, 18, 11); M.paper(c); M.baseLand(c, pr, { land: '#7a705e' }); LM.clipLaos(c, pr, () => { c.fillStyle = '#d8c8a0'; c.fillRect(0, 0, L.W, L.H); });
  factionZones(c, pr, [clamp((lt - .2) / .5) * .8, clamp((lt - 1.4) / .5) * .9, clamp((lt - 2.6) / .5) * .85]); LM.outline(c, pr, 'Laos', '#fff0c0', 3, 8);
  M.vignette(c, .5); const P = (lo, la) => pr(lo, la); const lb = (s2, lo, la, a, col, sz = 32) => { const [x, y] = P(lo, la); tag(c, s2, x, y, sz, col, a); };
  lb('ROYALISTS', 101.8, 17.6, clamp((lt - .3) / .4), '#dfe8ff'); lb('NEUTRALISTS', 103.1, 19.55, clamp((lt - 1.5) / .4), '#fff0b0'); lb('PATHET LAO', 104.0, 20.75, clamp((lt - 2.7) / .4), '#ffd0c0');
  arrowP(c, P(98.5, 14.2), P(101.2, 16.8), ease(clamp((lt - 4.2) / .8)), '#2a5ab0', 14); lb('U.S.', 98.4, 13.5, clamp((lt - 4.4) / .4), '#a8c8ff', 36);
  arrowP(c, P(108.6, 21.2), P(105.6, 19.8), ease(clamp((lt - 5.0) / .8)), '#c8241c', 14); lb('N. VIETNAM · USSR', 108.4, 22.0, clamp((lt - 5.2) / .4), '#ff9a80', 34); }); };
// ===== 20-22 Geneva =====
function hallLook() { show('hall'); look('day', null, 2.1, 1.8, 0xfff0dc, [-20, 30, 30], [0, 0, 6000], [0xf0e8dc, 0x6a5a48]); light(0, 'hall', -6, 5, 1, 70, 0xffe8c8, 26); light(1, 'hall', 6, 5, 1, 70, 0xffe8c8, 26); light(2, 'hall', 0, 4, 4, 40, 0xfff0e0, 20); U.dels.forEach((m, i) => pose(m, 0, { sit: true, write: i === 3 })); U.gHand.position.y = -60; }
SHOTS[20] = (t, lt, d) => { hallLook(); U.dels.forEach((m, i) => { pose(m, t + i, { sit: true, nod: Math.sin(t + i) * .05 }); m.position.y = .0; });
  ct('hall', lt, d, [11, 5.6, 8, 0, 1, -1], [9, 4.8, 6.5, 0, 1, -1], [40, 40]); overlay(c => L.caption(c, 'GENEVA, 1962', 'INTERNATIONAL CONFERENCE ON LAOS', fade(lt, d))); };
SHOTS[21] = (t, lt, d) => { hallLook(); const x = lerp(-6.4, 6.6, ease(clamp(lt / d))); ct('hall', 0, 1, [x - .6, 1.65, 1.4, x + .4, 1.55, -1], [x - .6, 1.65, 1.4, x + .4, 1.55, -1], [38, 38]);
  overlay(c => { tag(c, '14 COUNTRIES', L.W / 2, L.H - 70, 46, '#f2e8d2', fade(lt, d)); }); };
const SIG = k => [-.13 + k * .16, -.972 + Math.sin(k * 21) * .007 + Math.sin(k * 7) * .004];
SHOTS[22] = (t, lt, d) => { hallLook(); const k = clamp((lt - .4) / (d - .9)); const [sx, sz] = SIG(k); const lift = k <= 0 || k >= 1 ? .02 : 0;
  const e = new THREE.Euler(-.22, 0, .28); const off = V3(0, .075, 0).applyEuler(e); U.pen.rotation.copy(e); U.pen.position.set(sx + off.x, .862 + lift + off.y, sz + off.z);
  ct('hall', lt, d, [.32, 1.32, -.42, 0, .86, -1.16], [.26, 1.26, -.5, 0, .86, -1.12], [34, 30]);
  overlay(c => { c.save(); c.strokeStyle = 'rgba(20,24,60,.9)'; c.lineWidth = 3; c.lineCap = 'round'; c.beginPath(); const N = Math.floor(k * 60); for (let n = 0; n <= N; n++) { const [x, z] = SIG(n / 60); const v = V3(x, .8615, z + 6000).project(cam); const px = (v.x + 1) / 2 * L.W, py = (1 - v.y) / 2 * L.H; n ? c.lineTo(px, py) : c.moveTo(px, py); } c.stroke(); c.restore(); }); };
// ===== 23 treaty_paper =====
SHOTS[23] = (t, lt, d) => { OV.noGL = true; overlay(c => { c.fillStyle = '#2a1e14'; c.fillRect(0, 0, L.W, L.H); M.documentPage(c, lt + .4, [['DECLARATION ON THE NEUTRALITY OF LAOS', 30, true], ['', 22], ['The Governments of the fourteen states', 26], ['will respect the sovereignty, independence,', 26], ['neutrality, unity and territorial integrity', 26], ['of the Kingdom of Laos.', 26], ['', 22], ['Foreign troops shall be withdrawn.', 26]], { cps: 70, w: 1000, h: 640, stamp: [2.4, 'NEUTRAL', 200, 170] }); M.vignette(c, .5); }); };
// ===== 24 treaty_burn: the paper on the trail, boots march past =====
SHOTS[24] = (t, lt, d) => { show('trail'); look('day', [0xa8b8a0, .003], 1.6, 2.0, 0xfff0d8, [-40, 60, 30], [9000, 0, 0]); const r0 = Z.roadAt(0); U.treaty.position.set(r0.x + .4, .075, r0.z + .3);
  U.trucks.forEach(tr => tr.position.y = -60);
  U.nva.forEach((m, i) => { if (i > 5) { m.position.y = -60; return; } const x = -4 + lt * 1.5 - i * 1.7; const p = Z.roadAt(x); at(m, p.x, 0, p.z - 1.1 + (i % 2) * .35, facing([1, 0])); pose(m, t + i, { walk: true }); });
  hide(U.porters, U.bikes, U.tJets); U.tBlasts.forEach(b => b.userData.update(-1)); light(0, 'trail', r0.x, 3, r0.z + 1, 40, 0xfff0e0, 24);
  ct('trail', lt, d, [r0.x - 1.0, .75, r0.z + 2.3, r0.x + .3, .25, r0.z + .1], [r0.x - .8, .62, r0.z + 2.0, r0.x + .3, .25, r0.z + .1], [40, 36]); };
