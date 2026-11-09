// animation.js - bus 2008, v2: illustrated people + ink outlines, 39 scenes, no gore.
// The attacker is only ever a figure in shadow (inShadow) with an eye glint.
import { THREE, ease, seg, lerp, clamp, rng, toon, basic, box, cyl, sphere, mesh, textPlane, canvasTex } from '/animator/engine.js';
import { Person, SKIN } from '/animator/people.js';
import { office, impactBurst } from '/animator/props.js';
import { nightSky, flicker, lightBeam } from '/animator/kits/night.js';
import { evidenceBoard, censorBadge, courtroom } from '/animator/kits/investigation.js';
import { duskSky, prairie, makeBus, busInterior, policeCar, semiTruck, glassShards } from '/animator/kits/road.js';

// ---------------------------------------------------------------- people
const TIM = { skin: SKIN.fair, hair: 'spiky', hairColor: '#e3c46a', top: 'tshirt', topColor: '#5f9e55', pants: '#7a5a3a', shoes: '#b3261e', headphones: true };
const MAN = { skin: SKIN.fair, hair: 'short', hairColor: '#151515', top: 'tshirt', topColor: '#bfc3c7', pants: '#1c1f26', build: 1.1 };
const DRIVER = { skin: SKIN.light, hair: 'side', hairColor: '#7a7a7a', top: 'long', topColor: '#30405e', top2: '#e8edf2', pants: '#2a2f3a', age: 0.5 };
const TRUCKER = { skin: SKIN.fair, hair: 'short', hairColor: '#5a3a22', hat: 'cap', hatColor: '#2f6fb3', top: 'long', topColor: '#8c2f2a', top2: '#e0d7c8', pants: '#3a4a6a', build: 1.25, beard: true };
const COP = (i = 0) => ({ skin: [SKIN.fair, SKIN.tan, SKIN.light, SKIN.brown][i % 4], hair: 'short', hairColor: ['#2a1c14', '#111', '#6b4a2a', '#151515'][i % 4], hat: 'police', hatColor: '#1b2333', top: 'uniform', topColor: '#1f2a3d', top2: '#cfd6e0', pants: '#1b2333', stubble: i % 2 === 0 });
const PAX = (i) => ({ skin: [SKIN.light, SKIN.brown, SKIN.fair, SKIN.dark, SKIN.tan, SKIN.fair][i % 6], hair: ['bob', 'short', 'buzz', 'bun', 'long', 'side'][i % 6],
  hairColor: ['#5a3a22', '#222', '#8a6a3a', '#111', '#a0522d', '#333'][i % 6], top: ['hoodie', 'jacket', 'tshirt', 'long', 'tshirt', 'jacket'][i % 6],
  topColor: ['#5b4a8a', '#3a5a3a', '#a33', '#2f5f8f', '#c98a2b', '#555'][i % 6], top2: '#e8e1d4', pants: ['#2a2a35', '#3a3226', '#20304a'][i % 3], age: i === 4 ? 0.5 : 0 });
const MOTHER = { skin: SKIN.fair, hair: 'bob', hairColor: '#7a5a3a', top: 'jacket', topColor: '#4a5a72', top2: '#efe6d6', pants: '#2a2a35', age: 0.6 };
const JUDGE = { skin: SKIN.light, hair: 'side', hairColor: '#d0d0d0', top: 'robe', topColor: '#111', top2: '#eee', pants: '#111', age: 0.7, glasses: true };
const DOCTOR = { skin: SKIN.tan, hair: 'short', hairColor: '#333', top: 'suit', topColor: '#3d4652', top2: '#f2f2f2', tie: '#2b4e8c', pants: '#2b2f36', glasses: true };

const ROW = (i) => -5.4 + i * 0.95;
const SEAT = (row, z) => [ROW(row) + 0.15, -0.12, z];
const TIM_SEAT = SEAT(1, 0.95), MAN_SEAT = SEAT(1, 0.45);
const BUS_Z = 1.8;

// ---------------------------------------------------------------- looks
const finish = (S, v = 0.72) => { S.ink(); S.grade({ vignette: v, grain: 0.06 }); };
const dusk = (S, o = {}) => duskSky(S, { top: '#20264f', horizon: '#d77a46', hemi: 0.85, ...o });
function cabin(S, { flick = 0.5, seed = 3, night = false } = {}) {
  S.sky({ top: '#0b1430', horizon: '#26375e', bottom: '#0b1020', hemi: 0.85, sunI: 0.45, fog: null, sun: [10, 30, 20] });
  const b = busInterior(S, { dark: true, night });
  if (flick) flicker(S, b.userData.light, { amount: flick, seed });
  return b;
}
function sleepers(S, rows, seed = 1) {
  return rows.map(([r, z], i) => { const p = new Person(S, PAX(i + seed), { pos: SEAT(r, z), seed: 40 + seed + i, shadow: false }); p.set({ seat: 1, expr: 'asleep', tilt: (i % 2 ? -1 : 1) * 0.12 }); return p; });
}
const shadowMan = (S, pos, o = {}) => new Person(S, MAN, { pos, seed: 5, shadow: o.shadow ?? true });
function clockText(S, d = 2) {
  const tex = canvasTex(512, 128, () => {}); const m = new THREE.Mesh(new THREE.PlaneGeometry(0.7, 0.175), new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthTest: false, toneMapped: false }));
  m.renderOrder = 20000; const { h } = S.hud(new THREE.Group(), d); m.position.set(0, h * 0.3, -d); S.camera.add(m);
  m.userData.set = (txt) => { const g = tex.userData.ctx; g.clearRect(0, 0, 512, 128); g.font = '900 88px Display, sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.lineWidth = 10; g.strokeStyle = '#000'; g.strokeText(txt, 256, 64); g.fillStyle = '#f1e9d6'; g.fillText(txt, 256, 64); tex.needsUpdate = true; };
  return m;
}

export const shots = {
  // July 30th, 2008.
  '01': (S) => {
    dusk(S); prairie(S); const bus = makeBus({ lit: 0.5 }); S.add(bus); finish(S, 0.6);
    return (t, u) => { const bx = -30 + t * 13; bus.position.set(bx, 0, BUS_Z); S.shadowFocus(bx, 0, 0); S.camAt([bx + lerp(34, 26, u), lerp(24, 17, u), 36], [bx, 1, 0], 44); };
  },
  // A Greyhound bus
  '02': (S) => {
    dusk(S); prairie(S); const bus = makeBus({ lit: 0.5 }); S.add(bus); finish(S, 0.6);
    return (t, u) => { const bx = -2 + t * 13; bus.position.set(bx, 0, BUS_Z); S.shadowFocus(bx, 0, 0); S.camAt([bx + lerp(6, 1, u), 1.3, 7.8], [bx + lerp(-1, -4, u), 2.1, BUS_Z], 48); };
  },
  // is crossing the Canadian prairie.
  '03': (S) => {
    dusk(S, { fog: [120, 900] }); prairie(S); const bus = makeBus({ lit: 0.5 }); S.add(bus);
    S.add(box(9, 34, 9, toon(0x6e5e4c), [40, 17, -70])); S.add(box(10, 4, 10, toon(0x4a3e32), [40, 36, -70]));
    finish(S, 0.6);
    return (t, u) => { const bx = lerp(-10, 30, u); bus.position.set(bx, 0, BUS_Z); S.shadowFocus(bx, 0, 0); S.camAt([lerp(4, 14, u), 1.6, 26], [lerp(12, 24, u), 6, -30], 48); };
  },
  // Twenty-two-year-old Tim McLean
  '04': (S) => {
    cabin(S, { flick: 0 }); sleepers(S, [[3, -0.95], [5, 0.5]]);
    const tim = new Person(S, TIM, { pos: TIM_SEAT, seed: 2, shadow: false }); tim.set({ seat: 1, expr: 'smile', turn: -0.4, look: -0.6 });
    finish(S);
    return (t, u) => S.camMove(u, [[-2.6, 1.5, -0.2], [-4.3, 1.3, 0.85]], [[-3.25, 1.45, 0.05], [-4.3, 1.35, 0.9]], ease.io, [46, 40]);
  },
  // is heading home to Winnipeg.
  '05': (S) => {
    dusk(S); prairie(S); const bus = makeBus({ lit: 0.5 }); S.add(bus);
    const post = new THREE.Group(); post.add(cyl(0.08, 0.08, 3, toon(0x777b80), [-0.8, 1.5, 0], { seg: 8 })); post.add(cyl(0.08, 0.08, 3, toon(0x777b80), [0.8, 1.5, 0], { seg: 8 }));
    const sign = textPlane(['WINNIPEG', '→'], { w: 2.6, h: 1.3, bg: '#1d6b3a', fg: '#ffffff', border: '#ffffff', font: 'Display, sans-serif', size: 0.75, radius: 16 }); sign.position.set(0, 3.2, 0.06); post.add(sign);
    post.position.set(8, 0, 6.3); S.add(post); finish(S, 0.6);
    return (t, u) => { const bx = lerp(-30, 26, u); bus.position.set(bx, 0, BUS_Z); S.shadowFocus(4, 0, 4); S.camAt([lerp(12.5, 12, u), 2.4, 13], [7, 2.6, 4], 46); };
  },
  // He puts on his headphones
  '06': (S) => {
    cabin(S, { flick: 0 });
    const tim = new Person(S, { ...TIM }, { pos: TIM_SEAT, seed: 2, shadow: false });
    finish(S);
    return (t, u) => {
      const k = ease.out(seg(u, 0.05, 0.6));
      tim.set({ seat: 1, expr: 'neutral', turn: -0.2, armL: [lerp(0.15, 2.55, k), lerp(-0.15, -3.75, k)], armR: [lerp(0.15, 2.55, k), lerp(-0.15, -3.75, k)] });
      S.camMove(u, [[-3.35, 1.4, -0.15], [-4.3, 1.3, 0.9]], [[-3.55, 1.4, 0.05], [-4.3, 1.33, 0.9]], ease.lin, [40, 36]);
    };
  },
  // and falls asleep against the window.
  '07': (S) => {
    cabin(S, { flick: 0 });
    const tim = new Person(S, TIM, { pos: TIM_SEAT, seed: 2, shadow: false });
    finish(S, 0.76);
    return (t, u) => {
      const k = ease.io(seg(u, 0.2, 0.75));
      tim.set({ seat: 1, expr: k > 0.4 ? 'asleep' : 'tired', blink: false, turn: -0.2, tilt: lerp(0, 0.28, k), lean: lerp(0, 0.4, k) });
      S.camMove(u, [[-3.4, 1.38, 0.0], [-4.3, 1.32, 0.9]], [[-3.65, 1.35, 0.25], [-4.3, 1.32, 0.92]], ease.lin, [36, 32]);
    };
  },
  // After a rest stop in Brandon,
  '08': (S) => {
    dusk(S, { top: '#1a1f45', horizon: '#c86a40' }); prairie(S, { poles: false });
    const bus = makeBus({ lit: 0.45 }); bus.position.set(0, 0, 9); S.add(bus);
    S.add(box(12, 4, 7, toon(0xd8cbb3), [-6, 2, 18])); S.add(box(12.4, 0.5, 7.4, toon(0xb3261e), [-6, 4.2, 18]));
    S.add(cyl(0.15, 0.15, 7, toon(0x666666), [8, 3.5, 15]));
    const sign = textPlane('BRANDON', { w: 3.4, h: 0.9, bg: '#1d3557', fg: '#fff', font: 'Display, sans-serif', size: 0.7, radius: 12 }); sign.position.set(8, 7.2, 15.1); S.add(sign);
    S.add(box(10, 0.04, 16, toon(0x4f5156), [0, 0.02, 12], { cast: false }));
    const ppl = [0, 1, 2, 3].map(i => { const c = new Person(S, PAX(i), { pos: [-4 + i * 1.4, 0, 12.2 + (i % 2) * 0.8], seed: 60 + i }); c.set({ turn: i % 2 ? 0.5 : -0.4, expr: 'tired', armL: i === 1 ? [2.7, 0.2] : [0.15, -0.15], armR: i === 1 ? [2.7, 0.2] : [0.15, -0.15] }); return c; });
    const man = shadowMan(S, [5.0, 0, 11.8]); man.set({ inShadow: 1, turn: -0.4 });
    finish(S, 0.7);
    return (t, u) => { S.shadowFocus(0, 0, 12); S.camMove(u, [[10, 2.0, 24], [1, 1.8, 11]], [[7.2, 1.8, 20.5], [3.6, 1.7, 12]], ease.io, [44, 40]); };
  },
  // a quiet man
  '09': (S) => {
    cabin(S, { flick: 0.8, seed: 9 });
    const man = shadowMan(S, [-1.2, 0, 0.05], { shadow: false }); man.set({ inShadow: 1 });
    finish(S, 0.85);
    return (t, u) => S.camMove(u, [[0.6, 1.75, 0.05], [-1.2, 1.7, 0.05]], [[0.1, 1.72, 0.05], [-1.2, 1.72, 0.05]], ease.lin, [36, 32]);
  },
  // moves to the empty seat
  '10': (S) => {
    cabin(S, { flick: 0.7, seed: 4 }); sleepers(S, [[3, -0.95], [4, 0.95], [6, -0.5], [7, 0.5], [8, -0.95]], 2);
    const tim = new Person(S, TIM, { pos: TIM_SEAT, seed: 2, shadow: false }); tim.set({ seat: 1, expr: 'asleep', tilt: 0.28, turn: -0.2, lean: 0.4 });
    const man = shadowMan(S, [2, 0, 0.05], { shadow: false });
    finish(S, 0.78);
    return (t, u) => { man.pos(lerp(3.2, ROW(1) + 0.9, ease.io(u)), 0, 0.05); man.set({ view: 'back', walking: 1, walk: t * 6.5, inShadow: 1 }); S.camAt([4.8, 1.7, -0.15], [-3.5, 1.3, 0.25], 48); };
  },
  // beside him.
  '11': (S) => {
    cabin(S, { flick: 0.7, seed: 5 });
    const tim = new Person(S, TIM, { pos: TIM_SEAT, seed: 2, shadow: false }); tim.set({ seat: 1, expr: 'asleep', tilt: 0.28, turn: -0.2, lean: 0.4 });
    const man = shadowMan(S, MAN_SEAT, { shadow: false });
    finish(S, 0.8);
    return (t, u) => { const k = ease.io(seg(u, 0.05, 0.7)); man.pos(ROW(1) + 0.15 + (1 - k) * 0.5, lerp(0, -0.12, k), lerp(0.05, 0.45, k)); man.set({ seat: k, inShadow: 1, turn: 0.3 }); S.camAt([-2.7, 1.5, -0.4], [-4.2, 1.2, 0.6], 46); };
  },
  // His name is Vince Li.
  '12': (S) => {
    cabin(S, { flick: 0.85, seed: 6 });
    const tim = new Person(S, TIM, { pos: TIM_SEAT, seed: 2, shadow: false }); tim.set({ seat: 1, expr: 'asleep', tilt: 0.28, turn: -0.2, lean: 0.4 });
    const man = shadowMan(S, MAN_SEAT, { shadow: false }); man.set({ seat: 1, inShadow: 1, turn: 0.35, look: 0.8 });
    finish(S, 0.85);
    return (t, u) => S.camMove(u, [[-3.0, 1.5, -0.25], [-4.3, 1.38, 0.62]], [[-3.45, 1.45, 0.0], [-4.3, 1.4, 0.6]], ease.lin, [42, 36]);
  },
  // Nobody notices the knife.
  '13': (S) => {
    S.sky({ hemi: 0.35, fog: null, sunI: 0.3 }); S.dome.visible = false; S.scene.background = new THREE.Color('#07080b');
    const shape = new THREE.Shape(); shape.moveTo(0, 0); shape.lineTo(1.4, 0.05); shape.quadraticCurveTo(1.7, 0.12, 1.85, 0.3); shape.lineTo(0, 0.3); shape.closePath();
    const knife = new THREE.Group();
    knife.add(mesh(new THREE.ExtrudeGeometry(shape, { depth: 0.02, bevelEnabled: false }), new THREE.MeshPhongMaterial({ color: 0x6f7780, shininess: 160, specular: 0xffffff, emissive: 0x15181c }), [-0.9, -0.15, 0]));
    knife.add(box(0.75, 0.24, 0.1, toon(0x1a1410), [-1.3, 0, 0.01])); knife.rotation.set(0.2, -0.35, -0.12); S.add(knife);
    const glint = new THREE.PointLight(0xfff4dd, 0, 4, 1.5); S.add(glint);
    const spark = impactBurst(S, { text: null, size: 0.35, color: '#ffffff' });
    finish(S, 0.85);
    return (t, u) => { const k = seg(u, 0.3, 0.8); glint.position.set(lerp(-1.2, 1.2, k), 0.6, 0.8); glint.intensity = Math.sin(k * Math.PI) * 12; spark.position.set(lerp(-0.6, 0.7, k), 0.14, 0.05); spark.show(k > 0.45 && k < 0.65 ? (k - 0.45) * 2 : -1); S.camMove(u, [[0.1, 0.5, 4.6], [-0.2, 0, 0]], [[0.05, 0.35, 3.8], [-0.2, 0, 0]], ease.lin, [40, 38]); };
  },
  // Then the screaming
  '14': (S) => {
    cabin(S, { flick: 1.0, seed: 2 });
    const w = new Person(S, PAX(0), { pos: SEAT(4, 0.5), seed: 71, shadow: false });
    finish(S, 0.8);
    return (t, u) => { const k = seg(u, 0.12, 0.3); w.set({ seat: 1, expr: k > 0 ? 'scream' : 'asleep', blink: false, armL: k > 0 ? [2.5, -3.6] : [0.15, -0.15], armR: k > 0 ? [2.5, -3.6] : [0.15, -0.15], sweat: k > 0 ? 1 : 0, turn: 0.2 }); S.shake = k > 0 ? 0.012 : 0; S.camAt([ROW(4) + 1.1, 1.45, 0.05], [ROW(4) + 0.15, 1.32, 0.5], 40); };
  },
  // starts.
  '15': (S) => {
    cabin(S, { flick: 1.0, seed: 3 });
    const ppl = [[3, 0.5], [4, -0.5], [5, 0.55], [6, -0.55], [7, 0.5], [8, -0.5]].map(([r, z], i) => { const c = new Person(S, PAX(i + 1), { pos: [ROW(r) + 0.35, 0, z], seed: 80 + i, shadow: false }); c.r = i; return c; });
    const badge = censorBadge(S, { size: 1.0 }); badge.position.set(ROW(1) + 0.2, 1.3, 0.7);
    finish(S, 0.8);
    return (t, u) => {
      ppl.forEach((c, i) => c.set({ expr: i % 2 ? 'scream' : 'scared', turn: (i % 2 ? -1 : 1) * 0.5, view: i === 2 ? 'back' : 'front', armL: [lerp(0.2, 2.3, seg(u, 0, 0.3)), -0.6], armR: [lerp(0.2, 1.6, seg(u, 0, 0.3)), -1.2], sweat: 1 }));
      badge.userData.show((u - 0.2) * S.duration); S.shake = 0.02;
      S.camMove(u, [[5.2, 1.7, 0], [-2, 1.4, 0.1]], [[4.6, 1.65, 0], [-2.5, 1.4, 0.2]], ease.out, [54, 50]);
    };
  },
  // The driver pulls over,
  '16': (S) => {
    cabin(S, { flick: 0.4, seed: 8 });
    S.add(mesh(new THREE.PlaneGeometry(2.4, 1.4), new THREE.MeshBasicMaterial({ color: 0x1b2236 }), [6.4, 1.6, 0], { rot: [0, -Math.PI / 2, 0], cast: false }));
    const wheel = mesh(new THREE.TorusGeometry(0.28, 0.035, 10, 32), toon(0x1a1a1a), [6.25, 1.05, -0.7], { rot: [0, Math.PI / 2, 0.3] }); S.add(wheel);
    const drv = new Person(S, DRIVER, { pos: [5.85, -0.12, -0.7], seed: 91, shadow: false });
    const glow = new THREE.PointLight(0xff3020, 0, 6, 1.5); glow.position.set(6, 1.5, -0.7); S.add(glow);
    finish(S, 0.8);
    return (t, u) => {
      wheel.rotation.z = 0.3 + Math.sin(t * 4) * 0.4 * seg(u, 0.2, 1);
      drv.set({ seat: 1, expr: 'scared', sweat: 1, turn: 0.6, aimR: [6.25, 1.15, -0.45], aimL: [6.25, 1.0, -0.95] });
      glow.intensity = (Math.sin(t * 12) > 0 ? 6 : 0) * seg(u, 0.3, 1); S.shake = 0.015 * seg(u, 0.2, 1);
      S.camMove(u, [[4.5, 1.55, -0.2], [5.9, 1.25, -0.7]], [[4.8, 1.5, -0.25], [5.95, 1.25, -0.7]], ease.out, [46, 42]);
    };
  },
  // and the passengers run off the bus
  '17': (S) => {
    dusk(S, { top: '#191c40', horizon: '#b05f3a' }); prairie(S);
    const bus = makeBus({ lit: 0.45 }); bus.position.set(0, 0, 4.4); S.add(bus);
    const run = [0, 1, 2, 3, 4, 5].map(i => { const c = new Person(S, PAX(i), { seed: 120 + i }); c.r = i; return c; });
    finish(S, 0.72); S.shadowFocus(5, 0, 8);
    return (t, u) => {
      run.forEach((c, i) => { const st = i * 0.11, k = clamp((u - st) / 0.75); c.group.visible = u > st; c.pos(5.45 + (i % 2 ? -1 : 1) * k * 1.2, 0, 6.0 + k * 5.5); c.set({ run: 1, walk: t * 13 + i, expr: i % 2 ? 'scream' : 'scared', turn: (i % 2 ? -1 : 1) * 0.6 }); });
      S.camMove(u, [[9.5, 1.6, 15], [5, 1.6, 6]], [[8.8, 1.6, 14], [5, 1.6, 7]], ease.io, [46, 46]);
    };
  },
  // into the fields.
  '18': (S) => {
    dusk(S, { top: '#171a3a', horizon: '#9c5434' }); prairie(S);
    const bus = makeBus({ lit: 0.45 }); bus.position.set(0, 0, 4.4); S.add(bus);
    const run = [0, 1, 2, 3, 4].map(i => { const c = new Person(S, PAX(i + 2), { seed: 140 + i }); c.r = i; return c; });
    finish(S, 0.72); S.shadowFocus(4, 0, 16);
    return (t, u) => {
      run.forEach((c, i) => { c.pos(2 + i * 1.3 + Math.sin(i) * 0.6, 0, lerp(9 + i * 0.7, 19 + i * 0.4, u)); c.set({ run: 1, walk: t * 12 + i * 1.7, expr: 'scared', turn: (i % 2 ? 1 : -1) * 0.2, sweat: 1 }); });
      S.camAt([lerp(5, 5.5, u), 1.3, 26], [5, 1.3, 14], 46);
    };
  },
  // The driver and two men try to go back for Tim,
  '19': (S) => {
    dusk(S, { top: '#15183a', horizon: '#8f4e33' }); prairie(S);
    const bus = makeBus({ lit: 0.4 }); bus.position.set(0, 0, 4.4); S.add(bus);
    const men = [DRIVER, PAX(1), PAX(5)].map((d, i) => new Person(S, d, { seed: 160 + i }));
    finish(S, 0.74); S.shadowFocus(5, 0, 8);
    return (t, u) => { men.forEach((c, i) => { const k = ease.io(u); c.pos(lerp(4.4 + i * 1.0, 4.9 + i * 0.55, k), 0, lerp(11.5 + i * 0.4, 7.2 + i * 0.3, k)); c.set({ view: 'back', walking: 1, walk: t * 8 + i }); });
      S.camMove(u, [[5.6, 1.8, 16], [5.4, 1.6, 6]], [[5.6, 1.75, 13.5], [5.4, 1.6, 6]], ease.io, [46, 44]); };
  },
  // but they're driven off.
  '20': (S) => {
    dusk(S, { top: '#141737', horizon: '#86492f' }); prairie(S);
    const bus = makeBus({ lit: 0.35 }); bus.position.set(0, 0, 4.4); S.add(bus);
    const doorX = 5.5;
    const man = shadowMan(S, [doorX, 0.55, 5.85], { shadow: false }); man.set({ inShadow: 1, armR: [1.3, -0.3] });
    const men = [DRIVER, PAX(1), PAX(5)].map((d, i) => new Person(S, d, { seed: 160 + i }));
    const badge = censorBadge(S, { size: 0.55 }); badge.position.set(doorX + 0.45, 1.5, 6.0);
    finish(S, 0.78); S.shadowFocus(5, 0, 7);
    return (t, u) => {
      const back = ease.out(seg(u, 0.15, 0.85));
      men.forEach((c, i) => { const sx = [4.2, 6.8, 3.6][i]; c.pos(sx + back * (sx < doorX ? -1.0 : 1.0), 0, 7.4 + i * 0.4 + back * 2.4);
        c.set({ run: u > 0.15 ? 1 : 0, walk: t * 12 + i, expr: 'scream', turn: sx < doorX ? -0.6 : 0.6, armL: [2.3, 0.4], armR: [2.3, 0.4], kneel: i === 2 && u > 0.6 ? 1 : 0 }); });
      badge.userData.show((u - 0.1) * S.duration); S.shake = u > 0.15 && u < 0.35 ? 0.03 : 0;
      S.camAt([lerp(5.7, 5.5, u), 1.5, lerp(14.5, 13.6, u)], [doorX, 1.6, 6], 56);
    };
  },
  // So the driver disables the bus,
  '21': (S) => {
    S.sky({ hemi: 0.6, fog: null, sunI: 0.3 }); S.dome.visible = false; S.scene.background = new THREE.Color('#0b0d12');
    S.add(box(3, 1.2, 1.2, toon(0x23272e), [0, 0.6, 0]));
    const lamps = []; for (let i = 0; i < 5; i++) { const m = new THREE.MeshBasicMaterial({ color: [0x7fdc7f, 0xffc85a, 0x7fdc7f, 0x66b3ff, 0xff8a5a][i] }); lamps.push(m); S.add(mesh(new THREE.CircleGeometry(0.07, 16), m, [-1 + i * 0.35, 1.0, 0.61], { cast: false })); }
    S.add(mesh(new THREE.CircleGeometry(0.14, 24), new THREE.MeshBasicMaterial({ color: 0xff2a1a }), [0.9, 0.75, 0.61], { cast: false }));
    const lbl = textPlane('EMERGENCY STOP', { w: 0.9, h: 0.14, fg: '#ff8a7a', font: 'Display, sans-serif', size: 0.8 }); lbl.position.set(0.9, 0.52, 0.62); S.add(lbl);
    const drv = new Person(S, DRIVER, { pos: [0.35, -0.75, 1.4], seed: 91, shadow: false });
    finish(S, 0.75);
    return (t, u) => { const press = seg(u, 0.3, 0.5); drv.set({ aimR: [lerp(0.5, 0.9, press), 0.76, 0.62], expr: 'scared', sweat: 1, turn: 0.5 }); const off = u > 0.5; lamps.forEach(m => m.color.multiplyScalar(off ? 0.9 : 1)); S.camMove(u, [[0.45, 1.45, 4.2], [0.45, 0.9, 0.6]], [[0.6, 1.3, 3.4], [0.6, 0.85, 0.6]], ease.io, [48, 44]); };
  },
  // a trucker brings a hammer and a crowbar,
  '22': (S) => {
    dusk(S, { top: '#12152f', horizon: '#7d4430', sunI: 1.0 }); prairie(S);
    const bus = makeBus({ lit: 0.35 }); bus.position.set(0, 0, 4.4); S.add(bus); semiTruck(S, -22, BUS_Z);
    const tr = new Person(S, TRUCKER, { pos: [-12, 0, 6.6], seed: 170 }); tr.set({ hold: 'hammer', holdL: 'crowbar' });
    finish(S, 0.75); S.shadowFocus(-8, 0, 5);
    return (t, u) => { tr.pos(lerp(-14, -5, u), 0, 6.9); tr.set({ run: 1, walk: t * 11, expr: 'angry', turn: 0.7 }); S.camAt([lerp(-4, -1, u), 1.3, 12], [tr.group.position.x, 1.4, 6.6], 46); };
  },
  // and they keep him trapped inside.
  '23': (S) => {
    dusk(S, { top: '#101330', horizon: '#6e3c2c', sunI: 0.9 }); prairie(S);
    const bus = makeBus({ lit: 0.3 }); bus.position.set(0, 0, 4.4); S.add(bus);
    const doorX = 5.5, doorZ = 5.72;
    const man = shadowMan(S, [doorX, 0.55, 5.35], { shadow: false }); man.set({ inShadow: 1 });
    S.add(cyl(0.04, 0.04, 1.6, toon(0xb3261e), [doorX, 1.3, doorZ + 0.18], { rot: [0, 0, Math.PI / 2] }));
    const hold = [DRIVER, TRUCKER, PAX(1)].map((d, i) => new Person(S, d, { seed: 180 + i, pos: [doorX - 0.9 + i * 0.9, 0, 6.7 + (i % 2) * 0.25] }));
    finish(S, 0.8); S.shadowFocus(5, 0, 6);
    return (t, u) => { const shove = Math.max(0, Math.sin(t * 5)) * 0.06; hold.forEach((c, i) => c.set({ view: i === 1 ? 'front' : 'back', aimR: [doorX - 0.4 + i * 0.4, 1.3, doorZ + 0.18], aimL: [doorX - 0.6 + i * 0.4, 1.0, doorZ + 0.1], expr: 'angry', sweat: 1, lean: shove * 4 })); man.pos(doorX, 0.55, 5.35 + shove); S.camMove(u, [[doorX + 0.3, 1.5, 12.5], [doorX, 1.5, 5.8]], [[doorX + 0.15, 1.5, 10.8], [doorX, 1.55, 5.8]], ease.io, [44, 42]); };
  },
  // For almost five hours,
  '24': (S) => {
    duskSky(S); prairie(S, { night: true });
    const bus = makeBus({ lit: 0.3 }); bus.position.set(0, 0, 4.4); S.add(bus);
    const clock = clockText(S);
    const A = { top: new THREE.Color('#232a5c'), hor: new THREE.Color('#f19a58'), bot: new THREE.Color('#5a3f2c') }, B = { top: new THREE.Color('#030817'), hor: new THREE.Color('#2a4470'), bot: new THREE.Color('#0a1426') };
    const moon = new THREE.Mesh(new THREE.CircleGeometry(14, 40), new THREE.MeshBasicMaterial({ color: 0xf6f1d6, fog: false })); S.add(moon);
    finish(S, 0.75);
    return (t, u) => {
      const k = ease.io(u), un = S.dome.material.uniforms;
      un.top.value.lerpColors(A.top, B.top, k); un.hor.value.lerpColors(A.hor, B.hor, k); un.bot.value.lerpColors(A.bot, B.bot, k);
      S.scene.fog.color.copy(un.hor.value); S.sun.intensity = lerp(1.5, 0.6, k); S.sun.color.lerpColors(new THREE.Color(0xffa060), new THREE.Color(0xa9c3ff), k);
      moon.position.set(-200, lerp(-20, 120, k), -400); moon.lookAt(0, 0, 0);
      const mins = Math.round(lerp(20 * 60 + 30, 25 * 60 + 30, k)), hh = Math.floor(mins / 60) % 24, mm = mins % 60;
      clock.userData.set(`${((hh + 11) % 12) + 1}:${String(mm).padStart(2, '0')} ${hh >= 12 && hh < 24 ? 'PM' : 'AM'}`);
      S.camAt([lerp(16, 14, u), 2.2, 24], [0, 3, 2], 48);
    };
  },
  // he stays in there with Tim.
  '25': (S) => {
    nightSky(S, { fog: [60, 500], moonLight: 1.2, hemi: 0.85 }); prairie(S, { night: true });
    const bus = makeBus({ lit: 0.16 }); bus.position.set(0, 0, 4.4); S.add(bus);
    const man = shadowMan(S, [-3, 1.05, 4.4], { shadow: false }); man.set({ inShadow: 1 });
    const badge = censorBadge(S, { size: 1.2 }); badge.position.set(-4.4, 2.75, 6.0);
    finish(S, 0.85);
    return (t, u) => { man.pos(lerp(-1, -4.2, ease.io(u)), 1.05, 4.4); man.set({ walking: 0.6, walk: t * 5, turn: -0.5 }); badge.userData.show((u - 0.5) * S.duration); S.camMove(u, [[7, 1.2, 22], [-1, 2.2, 4.4]], [[3, 1.4, 16], [-3, 2.5, 4.4]], ease.lin, [44, 40]); };
  },
  // Police surround the bus.
  '26': (S) => {
    nightSky(S, { fog: [60, 500], moonLight: 1.0, hemi: 0.85 }); prairie(S, { night: true });
    const bus = makeBus({ lit: 0.16 }); bus.position.set(0, 0, 4.4); S.add(bus);
    const cars = [policeCar(S, 30, 9, { rotY: 2.8, seed: 1 }), policeCar(S, -30, 10.5, { rotY: 0.5, seed: 2 })];
    const cops = [[6.4, 11.4], [-4.4, 12.2], [1.2, 13.5]].map(([x, z], i) => { const c = new Person(S, COP(i), { pos: [x, 0, z], seed: 200 + i }); c.r = i; return c; });
    finish(S, 0.8); S.shadowFocus(2, 0, 8);
    return (t, u) => {
      const k = ease.out(seg(u, 0, 0.45));
      cars[0].position.set(lerp(30, 8.5, k), 0, 9.2); cars[1].position.set(lerp(-30, -6, k), 0, 10.4);
      cops.forEach((c, i) => { const go = seg(u, 0.45 + i * 0.08, 0.8 + i * 0.05); c.group.visible = go > 0; c.set({ kneel: go > 0.6 ? 1 : 0, run: go > 0 && go < 0.6 ? 1 : 0, walk: t * 12 + i, hold: 'flashlight', aimR: go > 0.6 ? [0, 2, 4.4] : null, expr: 'focused', turn: i === 1 ? 0.6 : -0.6 }); });
      S.camOrbit(u, [1.5, 1.4, 9.5], 12, 0.6, 0.2, 3.5, ease.io, 50);
    };
  },
  // At 1:30 in the morning,
  '27': (S) => {
    nightSky(S, { fog: [60, 500], moonLight: 0.9, hemi: 0.8 }); prairie(S, { night: true });
    const bus = makeBus({ lit: 0.16 }); bus.position.set(0, 0, 4.4); S.add(bus); policeCar(S, 4, 9.5, { rotY: 2.8, seed: 1 });
    const cop = new Person(S, COP(1), { pos: [1.5, 0, 9.2], seed: 211 }); cop.set({ kneel: 1, turn: -0.5, hold: 'flashlight', aimR: [-0.5, 1.0, 8.6], aimL: [-0.2, 0.95, 8.8], expr: 'focused', sweat: 1 });
    const clock = clockText(S); clock.userData.set('1:30 AM');
    finish(S, 0.85);
    return (t, u) => S.camMove(u, [[3.2, 1.2, 12.2], [1.4, 1.1, 9.2]], [[2.6, 1.15, 11.3], [1.4, 1.15, 9.2]], ease.lin, [42, 38]);
  },
  // he tries to escape through a window,
  '28': (S) => {
    nightSky(S, { fog: [60, 500], moonLight: 1.0, hemi: 0.85 }); prairie(S, { night: true });
    const bus = makeBus({ lit: 0.16 }); bus.position.set(0, 0, 4.4); S.add(bus); policeCar(S, 8, 12, { rotY: 2.6, seed: 1 });
    const win = bus.userData.windows[3];
    const man = shadowMan(S, [-1.64, 1.28, 5.8], { shadow: false }); man.set({ inShadow: 1, seatHideLegs: true }); man.group.visible = false;
    const shards = glassShards(S, [-1.64, 2.75, 5.72], { dir: [0, 0, 1] });
    finish(S, 0.82);
    const BREAK = 0.35;
    return (t, u) => { const k = (u - BREAK) * S.duration; win.visible = k < 0; shards.userData.burst(k); man.group.visible = k > 0.05; man.pos(-1.64, lerp(0.9, 1.28, clamp(k * 2)), 5.85); man.set({ armL: [1.7, -0.5], armR: [1.9, -0.3], lean: 0.2, tilt: -0.1 }); S.shake = k > 0 && k < 0.3 ? 0.06 : 0; S.camMove(u, [[1.4, 0.8, 11.5], [-1.6, 2.3, 5.6]], [[0.5, 0.9, 10], [-1.6, 2.4, 5.6]], ease.io, [44, 42]); };
  },
  // and police
  '29': (S) => {
    nightSky(S, { fog: [60, 500], moonLight: 1.0, hemi: 0.85 }); prairie(S, { night: true });
    const bus = makeBus({ lit: 0.16 }); bus.position.set(0, 0, 4.4); S.add(bus); bus.userData.windows[3].visible = false; policeCar(S, 6, 13, { rotY: 2.6, seed: 2 });
    const cops = [0, 1, 2].map(i => new Person(S, COP(i), { seed: 220 + i }));
    finish(S, 0.8); S.shadowFocus(0, 0, 9);
    return (t, u) => { cops.forEach((c, i) => { c.pos(-3 + i * 1.6, 0, lerp(13, 10, u) + (i % 2) * 0.5); c.set({ view: 'back', run: 1, walk: t * 13 + i, hold: 'flashlight' }); }); S.camAt([-1, 1.4, 16], [-1.6, 1.4, 6], 48); };
  },
  // finally take him down.
  '30': (S) => {
    nightSky(S, { fog: [60, 500], moonLight: 1.0, hemi: 0.9 }); prairie(S, { night: true });
    const bus = makeBus({ lit: 0.16 }); bus.position.set(0, 0, 4.4); S.add(bus); bus.userData.windows[3].visible = false;
    policeCar(S, 5, 13, { rotY: 2.6, seed: 1 }); policeCar(S, -7, 12, { rotY: 0.6, seed: 2 });
    const man = shadowMan(S, [-1.6, 0, 7.3]);
    const cops = [[-3.2, 7.9, 0.6], [0.0, 7.9, -0.6], [-1.6, 9.4, 0.1]].map(([x, z, tr], i) => { const c = new Person(S, COP(i), { pos: [x, 0, z], seed: 230 + i }); c.tr = tr; return c; });
    const zap = [0, 1].map(() => { const b = impactBurst(S, { text: null, size: 0.6, color: '#9fd8ff' }); b.position.set(-1.6, 1.25, 7.5); return b; });
    const beams = [lightBeam(S, [-3.0, 1.5, 8.0], { length: 3, radius: 0.5, spin: 0, opacity: 0.22 }), lightBeam(S, [0.0, 1.5, 8.0], { length: 3, radius: 0.5, spin: 0, opacity: 0.22 })];
    finish(S, 0.8); S.shadowFocus(-1.5, 0, 8);
    return (t, u) => {
      const down = u > 0.45;
      cops.forEach((c, i) => c.set({ turn: c.tr, expr: 'focused', hold: i === 1 ? 'taser' : 'flashlight', aimR: [-1.6, down ? 0.9 : 1.4, 7.3] }));
      zap[0].show((u - 0.3) * S.duration); zap[1].show((u - 0.42) * S.duration);
      man.set({ inShadow: 1, kneel: down ? 1 : 0, armL: down ? [2.7, 1.7] : [0.8, -0.2], armR: down ? [2.7, 1.7] : [0.9, -0.2], tilt: down ? 0.2 : 0 });
      beams.forEach(b => { b.lookAt(-1.6, down ? 0.9 : 1.3, 7.3); b.rotateY(Math.PI); });
      S.camMove(u, [[-0.6, 3.0, 14], [-1.6, 1.0, 7.3]], [[-1.0, 2.6, 12.0], [-1.6, 0.9, 7.3]], ease.io, [44, 42]);
    };
  },
  // In court, doctors said
  '31': (S) => {
    S.sky({ hemi: 0.75, fog: null, sun: [5, 20, 10], sunI: 0.6, shadow: 14 }); courtroom(S);
    const judge = new Person(S, JUDGE, { pos: [0, 0.55, -5.6], seed: 240 });
    const doc = new Person(S, DOCTOR, { pos: [1.2, 0, -2.6], seed: 241 }); doc.set({ hold: 'papers', talk: 0.8, turn: -0.4 });
    S.add(box(2.2, 0.9, 0.8, toon(0x6b4226), [-0.7, 0.45, 0.3]));
    const man = shadowMan(S, [-0.7, -0.12, 0.85], { shadow: false }); man.set({ seat: 1, view: 'back', inShadow: 1 });
    finish(S, 0.6);
    return (t, u) => S.camMove(u, [[-1.4, 1.9, 4.8], [0.3, 1.6, -3]], [[-0.9, 1.8, 3.7], [0.4, 1.6, -3]], ease.io, [48, 44]);
  },
  // he had untreated schizophrenia.
  '32': (S) => {
    S.sky({ hemi: 0.75, fog: null, sun: [5, 20, 10], sunI: 0.6, shadow: 14 }); courtroom(S);
    const doc = new Person(S, DOCTOR, { pos: [1.2, 0, -2.6], seed: 241 });
    finish(S, 0.6);
    return (t, u) => { doc.set({ hold: 'papers', talk: 0.9, turn: -0.3, armL: [1.1, -0.9] }); S.camMove(u, [[0.6, 1.7, -0.2], [1.2, 1.55, -2.6]], [[0.8, 1.68, -0.7], [1.2, 1.58, -2.6]], ease.lin, [40, 36]); };
  },
  // He believed God was telling him to do it.
  '33': (S) => {
    S.sky({ hemi: 0.1, fog: null, sunI: 0.05 }); S.dome.visible = false; S.scene.background = new THREE.Color('#050507');
    S.add(box(12, 0.1, 12, toon(0x222226), [0, -0.05, 0]));
    const spot = new THREE.SpotLight(0xfff6dd, 260, 14, 0.32, 0.6, 1.2); spot.position.set(0, 9, 0); spot.target.position.set(0, 0, 0); S.add(spot, spot.target);
    lightBeam(S, [0, 9, 0], { length: 9.5, radius: 1.4, spin: 0, opacity: 0.3, tilt: -Math.PI / 2 });
    const man = shadowMan(S, [0, 0, 0]); man.set({ inShadow: 0.92, kneel: 1, tilt: -0.25, armL: [0.5, -0.3], armR: [0.5, -0.3] });
    finish(S, 0.85);
    return (t, u) => S.camMove(u, [[0, 1.3, 6.5], [0, 1.4, 0]], [[0, 1.2, 4.6], [0, 1.4, 0]], ease.lin, [44, 40]);
  },
  // He was found not criminally responsible,
  '34': (S) => {
    S.sky({ hemi: 0.75, fog: null, sun: [5, 20, 10], sunI: 0.6, shadow: 14 }); courtroom(S);
    const judge = new Person(S, JUDGE, { pos: [0, 0.55, -5.6], seed: 240 });
    const thud = impactBurst(S, { text: null, size: 0.6, color: '#e9d7a8' }); thud.position.set(0.45, 1.95, -4.5);
    finish(S, 0.6);
    const HIT = 0.55;
    return (t, u) => { const k = (u - HIT) * S.duration; judge.set({ hold: 'gavel', expr: 'focused', armR: u < HIT ? [lerp(0.5, 2.6, ease.out(seg(u, 0.1, 0.4))) - Math.max(0, u - 0.42) * 14, -0.8] : [1.2, -0.9] }); thud.show(k); S.shake = k > 0 && k < 0.2 ? 0.03 : 0; S.camMove(u, [[0.2, 2.4, -1.4], [0, 2.4, -5.4]], [[0.15, 2.4, -2.2], [0, 2.4, -5.4]], ease.out, [44, 42]); };
  },
  // and in 2017,
  '35': (S) => {
    S.sky({ hemi: 0.4, fog: null, sunI: 0.2 }); S.dome.visible = false; S.scene.background = new THREE.Color('#07080b');
    const big = textPlane('2017', { w: 1.6, h: 0.6, fg: '#f1e9d6', font: 'Display, sans-serif', size: 0.9 }); big.position.set(0, 1.6, 0); S.add(big);
    finish(S, 0.85);
    return (t, u) => { big.scale.setScalar(lerp(0.9, 1.05, u)); big.material.opacity = seg(u, 0, 0.2); big.material.transparent = true; S.camAt([0, 1.6, 4], [0, 1.6, 0], 48); };
  },
  // he was set completely free.
  '36': (S) => {
    S.sky({ hemi: 0.4, fog: null, sunI: 0.2 }); S.dome.visible = false; S.scene.background = new THREE.Color('#07080b');
    S.add(box(4, 0.1, 14, toon(0x3a3a40), [0, -0.05, 0])); for (const sd of [-1, 1]) S.add(box(0.2, 4, 14, toon(0x4a4a52), [sd * 2, 2, 0]));
    S.add(box(4, 4, 0.2, toon(0x4a4a52), [0, 2, -7])); S.add(box(4.4, 0.2, 14.4, toon(0x3a3a42), [0, 4, 0]));
    S.add(mesh(new THREE.PlaneGeometry(1.6, 2.8), new THREE.MeshBasicMaterial({ color: 0xfffbea, toneMapped: false }), [0, 1.4, -6.89], { cast: false }));
    const pl = new THREE.PointLight(0xfff2d6, 30, 16, 1.2); pl.position.set(0, 1.8, -6.2); S.add(pl);
    const man = shadowMan(S, [0, 0, 2]);
    finish(S, 0.75);
    return (t, u) => { man.pos(0, 0, lerp(1.5, -6.4, ease.in(u))); man.set({ view: 'back', walking: 1, walk: t * 6, inShadow: 1 }); S.camAt([0.3, 1.5, 6], [0, 1.4, -4], 46); };
  },
  // Tim's mother said,
  '37': (S) => {
    S.sky({ hemi: 0.7, fog: null, sun: [-10, 20, 20], sunI: 0.5, shadow: 10 }); office(S);
    S.scene.traverse(o => { if (o.isPointLight) o.intensity = 10; });
    const mom = new Person(S, MOTHER, { pos: [0, 0, 0], seed: 250 }); mom.set({ expr: 'sad', tears: 1, hold: 'photo', armR: [0.5, -2.2], turn: 0.15 });
    finish(S, 0.75);
    return (t, u) => S.camMove(u, [[0.3, 1.6, 3.2], [0, 1.45, 0]], [[0.2, 1.6, 2.5], [0, 1.5, 0]], ease.lin, [44, 40]);
  },
  // "My son is still dead."
  '38': (S) => {
    S.sky({ top: '#05081a', horizon: '#18233f', hemi: 0.35, sunI: 0.2, fog: null });
    const inside = busInterior(S, { dark: true, night: true }); flicker(S, inside.userData.light, { amount: 0.5, seed: 6 });
    const hp = new THREE.Group(), band = basic(0x3c3c44), cupM = basic(0x26262c), red = basic(0xc0392b);
    hp.add(mesh(new THREE.TorusGeometry(0.15, 0.025, 10, 32, Math.PI), band, [0, 0, 0]));
    for (const sd of [-1, 1]) { hp.add(cyl(0.075, 0.075, 0.07, cupM, [sd * 0.15, -0.02, 0], { rot: [0, 0, Math.PI / 2] })); hp.add(box(0.074, 0.05, 0.02, red, [sd * 0.15, -0.02, 0.078], { cast: false })); }
    hp.rotation.set(0, 0.35, 0); hp.position.set(ROW(1) + 0.08, 0.64, 0.92); S.add(hp);
    const pool = new THREE.SpotLight(0xffe2b0, 16, 4, 0.45, 0.6, 1.2); pool.position.set(ROW(1) + 0.1, 2.3, 0.7); pool.target.position.set(ROW(1) + 0.08, 0.55, 0.92); S.add(pool, pool.target);
    finish(S, 0.85);
    return (t, u) => S.camMove(u, [[ROW(1) + 0.3, 1.35, -0.35], [ROW(1) + 0.06, 0.6, 0.92]], [[ROW(1) + 0.25, 1.2, 0.05], [ROW(1) + 0.06, 0.6, 0.92]], ease.lin, [44, 38]);
  },
  // Should he ever have been released?
  '39': (S) => {
    S.sky({ hemi: 0.4, fog: null, sun: [-20, 30, 40], sunI: 0.3, shadow: 15 }); office(S);
    S.scene.traverse(o => { if (o.isPointLight) o.intensity = 6; });
    for (const x of [-7, 0, 7]) { const m = new THREE.Mesh(new THREE.PlaneGeometry(4.6, 4.4), new THREE.MeshBasicMaterial({ color: 0x0b1630 })); m.position.set(x, 5.2, -7.76); S.add(m); }
    const lamp = new THREE.SpotLight(0xffd59a, 140, 16, 0.55, 0.5, 1.3); lamp.position.set(0.5, 7, -2.5); lamp.target.position.set(0, 3.4, -7.6); S.add(lamp, lamp.target);
    const items = [
      { type: 'note', text: 'JULY 30\n2008', at: [-1.9, 0.9] }, { type: 'note', text: 'NOT\nCRIMINALLY\nRESPONSIBLE', at: [0, 0.95], size: [0.8, 0.8], fontSize: 40 },
      { type: 'note', text: 'FREED\n2017', at: [1.9, 0.9], color: '#ff9f9f' }, { type: 'note', text: '?', at: [0, -0.9], color: '#ffffff', fontSize: 170, size: [0.75, 0.75] },
    ];
    const board = evidenceBoard(S, { pos: [0, 3.6, -7.55], items, links: [[0, 3], [1, 3], [2, 3]] });
    const inv = new Person(S, 'investigator', { pos: [1.3, 0, -4.4], seed: 260 });
    finish(S, 0.75);
    return (t, u) => { board.userData.setStrings(seg(u, 0.05, 0.6)); inv.set({ turn: u > 0.65 ? 0 : -0.6, aimR: u > 0.15 && u < 0.6 ? [0, 2.7, -7.5] : null, expr: 'focused' }); S.camMove(u, [[-0.6, 2.2, 2.5], [0.2, 2.6, -7.6]], [[0.7, 1.9, -0.8], [0.9, 2.0, -5]], ease.io, [48, 44]); };
  },
};
