// animation.js - "The bus, 2008" (vertical short). No gore is ever shown: reactions, silhouettes,
// sound and the censor badge carry the horror. Li is only ever a silhouette (no face).
import { THREE, ease, seg, lerp, clamp, rng, toon, basic, box, cyl, sphere, mesh, textPlane, canvasTex } from '/animator/engine.js';
import { Char } from '/animator/cast.js';
import { office, impactBurst, desk } from '/animator/props.js';
import { nightSky, flicker, lightBeam } from '/animator/kits/night.js';
import { evidenceBoard, censorBadge, courtroom, titleCard } from '/animator/kits/investigation.js';
import { duskSky, prairie, makeBus, busInterior, policeCar, semiTruck, glassShards } from '/animator/kits/road.js';

// ---------------------------------------------------------------- cast (real people: simple, respectful designs)
const TIM = { body: 'plain', color: '#4a6f9a', shirt: '#e6e6e6', bodyW: 150, headR: 146, hat: 'hair', hairColor: '#7a5230', headphones: true, eyes: 'dot', mouth: 'smile' };
const SHADOW = { body: 'plain', color: '#17171c', shirt: '#17171c', bodyW: 152, headR: 146, silhouette: true, eyes: 'dot', mouth: 'flat' };
const DRIVER = { body: 'suit', color: '#26324d', shirt: '#dfe6ef', tie: '#1b2433', bodyW: 168, headR: 148, hat: 'pilot', eyes: 'dot', mouth: 'flat' };
const TRUCKER = { body: 'plain', color: '#8c2f2a', shirt: '#e0d7c8', bodyW: 185, headR: 150, hat: 'cap', hairColor: '#4a3020', eyes: 'dot', mouth: 'flat' };
const COP = { body: 'suit', color: '#1d2333', shirt: '#c9d2e0', tie: '#0f1420', bodyW: 165, headR: 146, hat: 'pilot', eyes: 'half', mouth: 'flat' };

const ROW = (i) => -5.4 + i * 0.95;          // bus seat rows (x); seat cushion top y = 0.54
const SEAT_Y = 0.22;                          // character base so a seated figure sits on the cushion
const TIM_SEAT = [ROW(1) + 0.12, SEAT_Y, 0.95], LI_SEAT = [ROW(1) + 0.12, SEAT_Y, 0.5];
const BUS_Z = 1.8;                            // bus lane

function passengers(S, n, seed = 5, rows = [3, 4, 5, 6, 7, 8, 9], only = 0) {
  const R = rng(seed), out = [];
  for (let i = 0; i < n; i++) {
    const r = rows[i % rows.length], side = only || (R() < 0.5 ? 1 : -1), z = side * (R() < 0.5 ? 0.95 : 0.5);
    const c = new Char(S, 'extra', { seed: seed * 50 + i, h: 1.9, shadow: false }); c.pos(ROW(r) + 0.12, SEAT_Y, z);
    c.set({ seat: 1, facing: R() < .5 ? 1 : -1, eyes: R() < 0.5 ? 'closed' : 'half', mouth: 'flat', blink: false }); c.r = R(); out.push(c);
  }
  return out;
}
const grade = (S, v = 0.7) => S.grade({ vignette: v, grain: 0.07 });
const darkVoid = (S, c = '#07080b') => { S.dome.visible = false; S.scene.background = new THREE.Color(c); };
function lightsFlicker(S, inside, amount = 0.8, seed = 4) {
  flicker(S, inside.userData.light, { amount, seed });
  const base = inside.userData.strip.color.clone();
  S.onUpdate((t) => { const k = inside.userData.light.intensity / 14; inside.userData.strip.color.copy(base).multiplyScalar(clamp(0.25 + k, 0.2, 1)); });
}

export const shots = {
  // July 30th, 2008.
  '01': (S) => {
    duskSky(S); prairie(S);
    const bus = makeBus(); S.add(bus);
    grade(S, 0.6);
    return (t, u) => {
      const bx = -30 + t * 14; bus.position.set(bx, 0, BUS_Z); S.shadowFocus(bx, 0, 0);
      S.camAt([bx + lerp(30, 22, u), lerp(22, 16, u), 34], [bx, 1.5, 0], 46);
    };
  },
  // A Greyhound bus is crossing the Canadian prairie.
  '02': (S) => {
    duskSky(S); prairie(S);
    const bus = makeBus(); S.add(bus);
    grade(S, 0.6);
    return (t, u) => {
      const bx = lerp(-34, 30, u); bus.position.set(bx, 0, BUS_Z); S.shadowFocus(bx, 0, 0);
      S.camAt([26, 0.7, 7.5], [bx + 4, 1.8, BUS_Z], 50);
    };
  },
  // Twenty-two-year-old Tim McLean is heading home to Winnipeg.
  '03': (S) => {
    duskSky(S, { fog: null, hemi: 0.45 }); const inside = busInterior(S);
    passengers(S, 5, 5, [0, 2, 3, 4, 5], -1);
    const tim = new Char(S, TIM, { pos: TIM_SEAT, h: 1.9, shadow: false }); tim.set({ seat: 1, facing: -1, look: 0.6, eyes: 'half', mouth: 'smile' });
    grade(S, 0.6);
    return (t, u) => S.camMove(u, [[1.5, 1.75, 0.15], [-4.4, 1.3, 0.85]], [[-2.2, 1.6, 0.1], [-4.45, 1.3, 0.9]], ease.io, [48, 44]);
  },
  // He puts on his headphones and falls asleep against the window.
  '04': (S) => {
    duskSky(S, { fog: null, hemi: 0.45 }); const inside = busInterior(S);
    const tim = new Char(S, TIM, { pos: TIM_SEAT, h: 1.9, shadow: false });
    grade(S, 0.65);
    return (t, u) => {
      const asleep = u > 0.45;
      tim.set({ seat: 1, facing: -1, look: asleep ? 0.2 : 0.5, eyes: asleep ? 'closed' : 'half', blink: false, mouth: asleep ? 'flat' : 'smile', lean: asleep ? -0.4 * ease.io(seg(u, 0.45, 0.8)) : 0 });
      S.camMove(u, [[-3.0, 1.5, -0.15], [-4.45, 1.45, 0.9]], [[-3.45, 1.45, 0.1], [-4.45, 1.45, 0.95]], ease.out, [42, 38]);
    };
  },
  // After a rest stop in Brandon,
  '05': (S) => {
    duskSky(S, { top: '#1f234f', horizon: '#d9774a' }); prairie(S, { poles: false });
    const bus = makeBus(); bus.position.set(0, 0, 9); S.add(bus);
    S.add(box(12, 4, 7, toon(0xd8cbb3), [-4, 2, 18])); S.add(box(12.4, 0.5, 7.4, toon(0xb3261e), [-4, 4.2, 18]));
    S.add(cyl(0.15, 0.15, 7, toon(0x666666), [8, 3.5, 15]));
    const sign = textPlane('BRANDON', { w: 3.4, h: 0.9, bg: '#1d3557', fg: '#fff', font: 'Display, sans-serif', size: 0.7, radius: 12 }); sign.position.set(8, 7.2, 15.1); S.add(sign);
    S.add(box(8, 0.04, 16, toon(0x55575c), [0, 0.02, 12], { cast: false }));
    const people = [0, 1, 2, 3].map(i => { const c = new Char(S, 'extra', { seed: 60 + i, pos: [-3 + i * 1.6, 0, 12.4 + (i % 2) * 0.8] }); c.set({ armL: i % 2 ? 2.6 : 0.3, armR: i % 2 ? 2.6 : 0.3, eyes: 'closed' }); return c; });
    const li = new Char(S, SHADOW, { pos: [5.2, 0, 12.2] });
    grade(S, 0.65);
    return (t, u) => {
      people.forEach((c, i) => c.set({ armL: 0.3 + (i % 2) * (2.2 + Math.sin(t * 2 + i) * 0.2) }));
      S.shadowFocus(0, 0, 12);
      S.camMove(u, [[12, 2.2, 26], [2, 2.0, 11]], [[8.5, 1.9, 21.5], [4.5, 1.8, 12]], ease.io, [44, 40]);
    };
  },
  // a quiet man moves to the empty seat beside him.
  '06': (S) => {
    duskSky(S, { fog: null, hemi: 0.45 }); const inside = busInterior(S); lightsFlicker(S, inside, 0.7);
    passengers(S, 6, 7, [3, 5, 6, 8, 9]);
    const tim = new Char(S, TIM, { pos: TIM_SEAT, h: 1.9, shadow: false }); tim.set({ seat: 1, facing: -1, eyes: 'closed', blink: false, look: 0.2 });
    const li = new Char(S, SHADOW, { pos: [2, 0, 0], h: 1.95, shadow: false });
    grade(S, 0.72);
    return (t, u) => {
      const k = ease.io(seg(u, 0, 0.85));
      li.pos(lerp(1.6, ROW(1) + 0.5, k), 0, lerp(0, 0.25, k));
      li.set({ walking: u < 0.85 ? 0.7 : 0, walk: t * 7 });
      S.camAt([4.6, 1.75, -0.25], [lerp(0, -4.4, ease.io(u)), 1.3, 0.3], 48);
    };
  },
  // His name is Vince Li.
  '07': (S) => {
    duskSky(S, { fog: null, hemi: 0.5 }); const inside = busInterior(S); lightsFlicker(S, inside, 0.85, 9);
    const tim = new Char(S, TIM, { pos: TIM_SEAT, h: 1.9, shadow: false }); tim.set({ seat: 1, facing: -1, eyes: 'closed', blink: false, look: 0.2, lean: -0.3 });
    const li = new Char(S, SHADOW, { pos: LI_SEAT, h: 1.95, shadow: false }); li.set({ seat: 1, facing: -1, look: -0.1 });
    grade(S, 0.8);
    return (t, u) => S.camMove(u, [[-2.7, 1.55, -0.2], [-4.4, 1.45, 0.7]], [[-3.35, 1.5, 0.05], [-4.4, 1.5, 0.6]], ease.lin, [44, 38]);
  },
  // Nobody notices the knife.
  '08': (S) => {
    S.sky({ hemi: 0.35, fog: null, sunI: 0.3 }); darkVoid(S);
    const shape = new THREE.Shape(); shape.moveTo(0, 0); shape.lineTo(1.4, 0.05); shape.quadraticCurveTo(1.7, 0.12, 1.85, 0.3); shape.lineTo(0, 0.3); shape.closePath();
    const blade = mesh(new THREE.ExtrudeGeometry(shape, { depth: 0.02, bevelEnabled: false }), new THREE.MeshPhongMaterial({ color: 0x6f7780, shininess: 160, specular: 0xffffff, emissive: 0x15181c }), [-0.9, -0.15, 0]);
    const handle = box(0.75, 0.24, 0.1, toon(0x1a1410), [-1.3, 0, 0.01]);
    const knife = new THREE.Group(); knife.add(blade, handle); knife.rotation.set(0.2, -0.35, -0.12); S.add(knife);
    const glint = new THREE.PointLight(0xfff4dd, 0, 4, 1.5); S.add(glint);
    const spark = impactBurst(S, { text: null, size: 0.35, color: '#ffffff' });
    grade(S, 0.85);
    return (t, u) => {
      const k = seg(u, 0.3, 0.8); glint.position.set(lerp(-1.2, 1.2, k), 0.6, 0.8); glint.intensity = Math.sin(k * Math.PI) * 12;
      spark.position.set(lerp(-0.6, 0.7, k), 0.14, 0.05); spark.show(k > 0.45 && k < 0.65 ? (k - 0.45) * 2 : -1);
      S.camMove(u, [[0.1, 0.5, 4.6], [-0.2, 0, 0]], [[0.05, 0.35, 3.8], [-0.2, 0, 0]], ease.lin, [40, 38]);
    };
  },
  // Then the screaming starts.
  '09': (S) => {
    duskSky(S, { fog: null, hemi: 0.5 }); const inside = busInterior(S); lightsFlicker(S, inside, 1.0, 2);
    const faces = [[ROW(3), 0.5], [ROW(4), -0.5], [ROW(5), 0.55], [ROW(6), -0.55], [ROW(7), 0.5]].map(([x, z], i) => {
      const c = new Char(S, 'extra', { seed: 90 + i, h: 1.9, shadow: false }); c.pos(x + 0.3, 0, z); c.set({ facing: i % 2 ? 1 : -1 }); c.r = i; return c; });
    const badge = censorBadge(S, { size: 1.3 }); badge.position.set(ROW(1) + 0.2, 1.4, 0.75);
    grade(S, 0.8);
    return (t, u) => {
      const scared = u > 0.18;
      faces.forEach((c, i) => c.set({ eyes: scared ? 'wide' : 'closed', blink: false, mouth: scared ? (i % 2 ? 'open' : 'o') : 'flat', talk: scared && i % 2 ? 0.7 : 0, sweat: scared ? 1 : 0, look: scared ? -0.8 : 0, hop: scared && u < 0.35 ? 0.15 : 0 }));
      badge.userData.show(u > 0.25 ? (u - 0.25) * S.duration : -1);
      S.shake = scared ? 0.02 : 0;
      S.camMove(u, [[5.2, 1.7, 0], [-2, 1.4, 0.1]], [[4.6, 1.65, 0], [-2.5, 1.4, 0.2]], ease.out, [54, 50]);
    };
  },
  // The driver pulls over,
  '10': (S) => {
    duskSky(S, { top: '#1b1f45', horizon: '#c86a40' }); prairie(S);
    const bus = makeBus(); S.add(bus);
    grade(S, 0.7);
    return (t, u) => {
      const k = ease.out(u); const bx = lerp(-10, 6, k); bus.position.set(bx, 0, lerp(BUS_Z, 4.4, ease.io(u)));
      bus.rotation.y = Math.sin(u * Math.PI) * 0.08; bus.userData.tail.forEach(m => m.material.color.setHex(0xff6040));
      S.shadowFocus(bx, 0, 3);
      S.camAt([bx - 16, 1.4, 1.2], [bx, 1.8, 3.4], 50);
    };
  },
  // and the passengers run off the bus into the fields.
  '11': (S) => {
    duskSky(S, { top: '#1b1f45', horizon: '#c86a40' }); prairie(S);
    const bus = makeBus(); bus.position.set(0, 0, 4.4); S.add(bus);
    const run = [0, 1, 2, 3, 4, 5, 6, 7].map(i => { const c = new Char(S, 'extra', { seed: 120 + i }); c.r = i; return c; });
    grade(S, 0.7); S.shadowFocus(4, 0, 9);
    return (t, u) => {
      run.forEach((c, i) => {
        const start = i * 0.09, k = clamp((u - start) / 0.7);
        c.group.visible = u > start;
        c.pos(5.4 + (i % 3) * 0.4 - k * (i % 2 ? 2 : -1.5), 0, 5.9 + k * (6 + i * 0.6));
        c.set({ walking: 1, walk: t * 13 + i, eyes: 'wide', mouth: 'open', armL: 1.2 + Math.sin(t * 13 + i) * 0.6, armR: 1.2 - Math.sin(t * 13 + i) * 0.6, facing: i % 2 ? -1 : 1 });
      });
      S.camMove(u, [[14, 3, 22], [4, 1.5, 6]], [[11, 2.6, 19], [4, 1.5, 8]], ease.io, [44, 44]);
    };
  },
  // The driver and two men try to go back for Tim,
  '12': (S) => {
    duskSky(S, { top: '#191c40', horizon: '#b05f3a' }); prairie(S);
    const bus = makeBus({ lit: 0.35 }); bus.position.set(0, 0, 4.4); S.add(bus);
    const men = [DRIVER, 'extra', 'extra'].map((d, i) => { const c = new Char(S, d, { seed: 140 + i }); c.r = i; return c; });
    const shadow = new Char(S, SHADOW, { pos: [-2.6, 1.1, 4.4], h: 1.95, shadow: false });   // seen through the windows
    grade(S, 0.72); S.shadowFocus(4, 0, 7);
    return (t, u) => {
      men.forEach((c, i) => { const k = ease.io(u); c.pos(lerp(7 + i * 1.1, 5.6 + i * 0.6, k), 0, lerp(12 + i * 0.5, 7.2 + i * 0.4, k)); c.set({ walking: 0.8, walk: t * 8 + i, eyes: 'wide', mouth: 'flat', sweat: 1, facing: -1 }); });
      shadow.pos(lerp(-3, 1.5, u), 1.1, 4.4);
      S.camMove(u, [[9, 1.7, 19], [3, 2, 5]], [[7.6, 1.7, 16], [3.5, 2, 5]], ease.io, [46, 44]);
    };
  },
  // but they're driven off.
  '13': (S) => {
    duskSky(S, { top: '#171a3a', horizon: '#9c5434' }); prairie(S);
    const bus = makeBus({ lit: 0.3 }); bus.position.set(0, 0, 4.4); S.add(bus);
    const doorX = 5.5, doorZ = 5.72;
    const li = new Char(S, SHADOW, { pos: [doorX, 0.55, 5.85], h: 1.95, shadow: false });
    const men = [DRIVER, 'extra', 'extra'].map((d, i) => { const c = new Char(S, d, { seed: 140 + i }); c.r = i; return c; });
    const badge = censorBadge(S, { size: 0.6 }); badge.position.set(doorX + 0.55, 1.55, 6.0);
    grade(S, 0.78); S.shadowFocus(5, 0, 7);
    return (t, u) => {
      const back = ease.out(seg(u, 0.2, 0.9));
      men.forEach((c, i) => { const sx = [4.3, 6.7, 3.7][i]; c.pos(sx + back * (sx < doorX ? -1.0 : 1.0), 0, 7.6 + i * 0.4 + back * 2.2); c.set({ walking: u > 0.2 ? 1 : 0, walk: t * 12 + i, eyes: 'wide', mouth: 'open', armL: 2.4, armR: 2.4, sweat: 1, facing: sx < doorX ? -1 : 1, look: sx < doorX ? 0.5 : -0.5 }); });
      li.set({ look: 0.3 }); badge.userData.show(u > 0.15 ? (u - 0.15) * S.duration : -1);
      S.shake = u > 0.2 && u < 0.4 ? 0.03 : 0;
      S.camAt([lerp(5.7, 5.5, u), 1.5, lerp(14.5, 13.6, u)], [doorX, 1.6, 6], 56);
    };
  },
  // So the driver disables the bus,
  '14': (S) => {
    S.sky({ hemi: 0.5, fog: null, sunI: 0.3 }); darkVoid(S, '#0b0d12');
    S.add(box(3, 1.2, 1.2, toon(0x23272e), [0, 0.6, 0]));                   // dashboard
    const lamps = [];
    for (let i = 0; i < 5; i++) { const m = new THREE.MeshBasicMaterial({ color: [0x7fdc7f, 0xffc85a, 0x7fdc7f, 0x66b3ff, 0xff8a5a][i] }); lamps.push(m); S.add(mesh(new THREE.CircleGeometry(0.07, 16), m, [-1 + i * 0.35, 1.0, 0.61], { cast: false })); }
    const sw = new THREE.MeshBasicMaterial({ color: 0xff2a1a }); S.add(mesh(new THREE.CircleGeometry(0.14, 24), sw, [0.9, 0.75, 0.61], { cast: false }));
    const lbl = textPlane('EMERGENCY STOP', { w: 0.9, h: 0.14, fg: '#ff8a7a', font: 'Display, sans-serif', size: 0.8 }); lbl.position.set(0.9, 0.52, 0.62); S.add(lbl);
    const driver = new Char(S, DRIVER, { pos: [-0.25, -0.6, 1.55], h: 2.1, shadow: false });
    const glow = new THREE.PointLight(0x9fd0ff, 4, 4, 1.5); glow.position.set(0, 1.4, 1.5); S.add(glow);
    grade(S, 0.75);
    return (t, u) => {
      const press = seg(u, 0.35, 0.5);
      driver.set({ aimR: [lerp(0.4, 0.9, press), 0.75, 0.62], eyes: 'wide', mouth: 'flat', sweat: 1, look: 0.5, facing: 1 });
      const off = u > 0.5; lamps.forEach(m => m.color.multiplyScalar(off ? 0.92 : 1)); glow.intensity = off ? 1.2 : 4;
      S.camMove(u, [[0.45, 1.45, 4.2], [0.45, 0.9, 0.6]], [[0.6, 1.3, 3.4], [0.6, 0.85, 0.6]], ease.io, [48, 44]);
    };
  },
  // a trucker brings a hammer and a crowbar,
  '15': (S) => {
    duskSky(S, { top: '#15183a', horizon: '#8f4e33', sunI: 1.1 }); prairie(S);
    const bus = makeBus({ lit: 0.3 }); bus.position.set(0, 0, 4.4); S.add(bus);
    semiTruck(S, -22, BUS_Z);
    const trucker = new Char(S, TRUCKER, { pos: [-12, 0, 6.5] }); trucker.set({ hold: 'hammer', holdL: 'crowbar', facing: 1 });
    grade(S, 0.75); S.shadowFocus(-8, 0, 5);
    return (t, u) => {
      trucker.pos(lerp(-13, -4, u), 0, 6.8); trucker.set({ walking: 1, walk: t * 10, eyes: 'half', mouth: 'flat', brow: 0.6, armR: 0.5, armL: 0.5 });
      S.camAt([lerp(-3, 0, u), 1.2, 12], [trucker.group.position.x, 1.4, 6.5], 46);
    };
  },
  // and they keep him trapped inside.
  '16': (S) => {
    duskSky(S, { top: '#121531', horizon: '#7d4430', sunI: 1.0 }); prairie(S);
    const bus = makeBus({ lit: 0.3 }); bus.position.set(0, 0, 4.4); S.add(bus);
    const doorX = 5.5, doorZ = 5.72;
    const li = new Char(S, SHADOW, { pos: [doorX, 0.55, 5.3], h: 1.95, shadow: false });
    const bar = cyl(0.04, 0.04, 1.6, toon(0xb3261e), [doorX, 1.3, doorZ + 0.18], { rot: [0, 0, Math.PI / 2] }); S.add(bar);
    const hold = [DRIVER, TRUCKER, 'extra'].map((d, i) => new Char(S, d, { seed: 160 + i, pos: [doorX - 0.9 + i * 0.9, 0, 6.6 + (i % 2) * 0.25] }));
    grade(S, 0.8); S.shadowFocus(5, 0, 6);
    return (t, u) => {
      const shove = Math.max(0, Math.sin(t * 5)) * 0.06;
      hold.forEach((c, i) => c.set({ aimR: [doorX - 0.4 + i * 0.4, 1.3, doorZ + 0.18], aimL: [doorX - 0.6 + i * 0.4, 1.0, doorZ + 0.1], eyes: 'wide', mouth: 'flat', sweat: 1, brow: 0.8, lean: shove * 5 }));
      li.set({ look: Math.sin(t * 2) * 0.5 }); li.pos(doorX, 0.55, 5.3 + shove);
      S.camMove(u, [[doorX + 0.3, 1.5, 12.5], [doorX, 1.5, 5.8]], [[doorX + 0.15, 1.5, 10.8], [doorX, 1.55, 5.8]], ease.io, [44, 42]);
    };
  },
  // For almost five hours, he stays in there with Tim.
  '17': (S) => {
    nightSky(S, { fog: [60, 500], moonLight: 1.2 }); prairie(S, { night: true });
    const bus = makeBus({ lit: 0.18 }); bus.position.set(0, 0, 4.4); S.add(bus);
    const li = new Char(S, SHADOW, { pos: [-3, 1.15, 4.4], h: 1.95, shadow: false });
    const badge = censorBadge(S, { size: 1.4 }); badge.position.set(-4.4, 2.75, 6.0);
    grade(S, 0.85);
    return (t, u) => {
      li.pos(lerp(-1, -4.2, ease.io(u)), 1.15, 4.4);
      badge.userData.show(u > 0.55 ? (u - 0.55) * S.duration : -1);
      S.camMove(u, [[7, 1.2, 22], [-1, 2.2, 4.4]], [[3, 1.4, 16], [-3, 2.5, 4.4]], ease.lin, [44, 40]);
    };
  },
  // Police surround the bus.
  '18': (S) => {
    nightSky(S, { fog: [60, 500], moonLight: 1.0 }); prairie(S, { night: true });
    const bus = makeBus({ lit: 0.18 }); bus.position.set(0, 0, 4.4); S.add(bus);
    policeCar(S, 9, 9.5, { rotY: 2.4, seed: 1 }); policeCar(S, -6, 10.5, { rotY: 0.7, seed: 2 }); policeCar(S, 14, 3, { rotY: 1.6, seed: 3 });
    const cops = [[7.5, 11.8], [-4.5, 12.6], [12.2, 5.2]].map(([x, z], i) => { const c = new Char(S, COP, { seed: 180 + i, pos: [x, 0, z] }); c.set({ kneel: 1, hold: 'flashlight', aimR: [0, 1.8, 4.4], facing: i === 1 ? 1 : -1, look: 0.4 }); return c; });
    grade(S, 0.8); S.shadowFocus(2, 0, 8);
    return (t, u) => S.camOrbit(u, [2, 1.5, 6], 21, 0.55, 0.15, 7, ease.io, 46);
  },
  // At 1:30 in the morning, he tries to escape through a window,
  '19': (S) => {
    nightSky(S, { fog: [60, 500], moonLight: 1.0 }); prairie(S, { night: true });
    const bus = makeBus({ lit: 0.18 }); bus.position.set(0, 0, 4.4); S.add(bus);
    policeCar(S, 8, 12, { rotY: 2.6, seed: 1 });
    const winPos = [-1.64, 2.75, 5.72];
    const win = bus.userData.windows[3];
    const li = new Char(S, SHADOW, { pos: [-1.64, 1.15, 5.2], h: 1.95, shadow: false });
    const shards = glassShards(S, winPos, { dir: [0, 0, 1] });
    const clock = textPlane('1:30 AM', { w: 0.7, h: 0.18, fg: '#e9e1cf', font: 'Display, sans-serif', size: 0.8 });
    const hud = S.hud(new THREE.Group(), 2); clock.position.set(0, hud.h * 0.32, -2); clock.material.depthTest = false; clock.renderOrder = 20000; S.camera.add(clock);
    grade(S, 0.8);
    const BREAK = 0.45;
    return (t, u) => {
      const k = (u - BREAK) * S.duration;
      win.visible = k < 0; shards.userData.burst(k);
      li.pos(-1.64, 1.15, lerp(5.2, 5.6, clamp(k * 2))); li.set({ armR: k > 0 ? 2.6 : 1.4, armL: k > 0 ? 2.4 : 0.4 });
      S.shake = k > 0 && k < 0.3 ? 0.06 : 0;
      clock.material.opacity = 1 - seg(u, 0.3, 0.45); clock.material.transparent = true;
      S.camMove(u, [[1.5, 0.8, 12], [-1.6, 2.4, 5.6]], [[0.5, 0.9, 10.2], [-1.6, 2.5, 5.6]], ease.io, [44, 42]);
    };
  },
  // and police finally take him down.
  '20': (S) => {
    nightSky(S, { fog: [60, 500], moonLight: 1.0 }); prairie(S, { night: true });
    const bus = makeBus({ lit: 0.18 }); bus.position.set(0, 0, 4.4); S.add(bus); bus.userData.windows[3].visible = false;
    policeCar(S, 6, 13, { rotY: 2.6, seed: 1 }); policeCar(S, -6, 12, { rotY: 0.6, seed: 2 });
    const li = new Char(S, SHADOW, { pos: [-1.6, 0, 7.2], h: 1.95 });
    const cops = [0, 1, 2].map(i => new Char(S, COP, { seed: 200 + i }));
    const zap = [0, 1].map(() => { const b = impactBurst(S, { text: null, size: 0.6, color: '#9fd8ff' }); b.position.set(-1.6, 1.2, 7.4); return b; });
    const beams = [lightBeam(S, [2, 1.6, 11], { length: 10, radius: 1.2, spin: 0, opacity: 0.14 }), lightBeam(S, [-5, 1.6, 11], { length: 10, radius: 1.2, spin: 0, opacity: 0.14 })];
    grade(S, 0.8); S.shadowFocus(-1, 0, 8);
    return (t, u) => {
      const k = ease.io(seg(u, 0, 0.5));
      cops.forEach((c, i) => { const fx = [-3.1, -0.1, -1.6][i], fz = [7.6, 7.6, 6.3][i]; c.pos(lerp(fx + (i - 1) * 2, fx, k), 0, lerp(12, fz, k)); c.set({ walking: u < 0.5 ? 1 : 0, walk: t * 12 + i, hold: 'flashlight', aimR: [-1.6, 1.0, 7.2], eyes: 'half', brow: 0.6, facing: i < 1 ? 1 : -1 }); });
      zap[0].show(u > 0.45 ? (u - 0.45) * S.duration : -1); zap[1].show(u > 0.6 ? (u - 0.6) * S.duration : -1);
      li.set({ kneel: u > 0.55 ? 1 : 0, armL: u > 0.55 ? 2.7 : 0.4, armR: u > 0.55 ? 2.7 : 0.4 });
      beams.forEach(b => { b.lookAt(-1.6, 1.0, 7.2); b.rotateY(Math.PI); });
      S.camMove(u, [[-0.8, 3.4, 15], [-1.6, 0.9, 7.2]], [[-1.2, 3.0, 12.5], [-1.6, 0.8, 7.2]], ease.io, [44, 42]);
    };
  },
  // In court, doctors said he had untreated schizophrenia.
  '21': (S) => {
    S.sky({ hemi: 0.6, fog: null, sun: [5, 20, 10], sunI: 0.6, shadow: 14 }); courtroom(S);
    const judge = new Char(S, { body: 'suit', color: '#141414', shirt: '#f2f2f2', tie: '#141414', bodyW: 170, headR: 150, hat: 'hair', hairColor: '#cfcfcf', glasses: 'round', eyes: 'half', mouth: 'flat' }, { pos: [0, 0.75, -5.6] });
    const doctor = new Char(S, 'extra', { seed: 210, pos: [1.0, 0, -2.8] }); doctor.d.glasses = 'round'; doctor.set({ hold: 'folder', armL: 1.2, talk: 0.8, facing: -1 });
    S.add(box(2.2, 0.9, 0.8, toon(0x6b4226), [-0.7, 0.45, 0.3]));
    const li = new Char(S, SHADOW, { pos: [-0.7, 0.0, 0.85] }); li.set({ seat: 1, facing: 1 });
    grade(S, 0.65);
    return (t, u) => S.camMove(u, [[-1.6, 1.9, 5.2], [0.2, 1.6, -3]], [[-1.0, 1.8, 3.9], [0.3, 1.6, -3]], ease.io, [48, 44]);
  },
  // He believed God was telling him to do it.
  '22': (S) => {
    S.sky({ hemi: 0.08, fog: null, sunI: 0.05 }); darkVoid(S, '#050507');
    S.add(box(12, 0.1, 12, toon(0x222226), [0, -0.05, 0]));
    const spot = new THREE.SpotLight(0xfff6dd, 260, 14, 0.32, 0.6, 1.2); spot.position.set(0, 9, 0); spot.target.position.set(0, 0, 0); S.add(spot, spot.target);
    lightBeam(S, [0, 9, 0], { length: 9.5, radius: 1.4, spin: 0, opacity: 0.3, tilt: -Math.PI / 2 });
    const li = new Char(S, SHADOW, { pos: [0, 0, 0] }); li.set({ kneel: 1, look: 0, armL: 0.6, armR: 0.6 });
    grade(S, 0.85);
    return (t, u) => { li.set({ look: Math.sin(t * 0.8) * 0.15 }); S.camMove(u, [[0, 1.3, 6.5], [0, 1.4, 0]], [[0, 1.2, 4.6], [0, 1.4, 0]], ease.lin, [44, 40]); };
  },
  // He was found not criminally responsible,
  '23': (S) => {
    S.sky({ hemi: 0.6, fog: null, sun: [5, 20, 10], sunI: 0.6, shadow: 14 }); courtroom(S);
    const judge = new Char(S, { body: 'suit', color: '#141414', shirt: '#f2f2f2', tie: '#141414', bodyW: 170, headR: 150, hat: 'hair', hairColor: '#cfcfcf', glasses: 'round', eyes: 'half', mouth: 'flat' }, { pos: [0, 0.75, -5.6] });
    judge.set({ hold: 'gavel' });
    const thud = impactBurst(S, { text: null, size: 0.7, color: '#e9d7a8' }); thud.position.set(0.5, 2.0, -4.3);
    grade(S, 0.65);
    const HIT = 0.55;
    return (t, u) => {
      const k = (u - HIT) * S.duration;
      judge.set({ armR: u < HIT ? lerp(0.8, 2.8, ease.out(seg(u, 0.1, 0.4))) - (u > 0.42 ? (u - 0.42) * 18 : 0) : 1.3 });
      thud.show(k); S.shake = k > 0 && k < 0.2 ? 0.03 : 0;
      S.camMove(u, [[0.2, 2.5, -1.2], [0, 2.5, -5.4]], [[0.15, 2.5, -2.0], [0, 2.5, -5.4]], ease.out, [44, 42]);
    };
  },
  // and in 2017, he was set completely free.
  '24': (S) => {
    S.sky({ hemi: 0.3, fog: null, sunI: 0.2 });
    S.add(box(4, 0.1, 14, toon(0x3a3a40), [0, -0.05, 0]));
    for (const sd of [-1, 1]) S.add(box(0.2, 4, 14, toon(0x4a4a52), [sd * 2, 2, 0]));
    S.add(box(4, 4, 0.2, toon(0x4a4a52), [0, 2, -7])); S.add(box(4.4, 0.2, 14.4, toon(0x3a3a42), [0, 4, 0])); darkVoid(S);
    const doorLight = mesh(new THREE.PlaneGeometry(1.6, 2.8), new THREE.MeshBasicMaterial({ color: 0xfffbea, toneMapped: false }), [0, 1.4, -6.89], { cast: false }); S.add(doorLight);
    const pl = new THREE.PointLight(0xfff2d6, 30, 16, 1.2); pl.position.set(0, 1.8, -6.2); S.add(pl);
    const year = textPlane('2017', { w: 2, h: 0.6, fg: '#e9e1cf', font: 'Display, sans-serif', size: 0.8 }); year.position.set(0, 3.4, -6.8); S.add(year);
    const li = new Char(S, SHADOW, { pos: [0, 0, 2] });
    grade(S, 0.75);
    return (t, u) => { li.pos(0, 0, lerp(1.5, -6.4, ease.in(u))); li.set({ walking: 1, walk: t * 7 }); S.camAt([0.3, 1.5, 6], [0, 1.4, -4], 46); };
  },
  // Tim's mother said, "My son is still dead."
  '25': (S) => {
    nightSky(S, { moon: null, stars: false, fog: null, hemi: 0.25, moonLight: 0.3 });
    const inside = busInterior(S, { night: true }); lightsFlicker(S, inside, 0.5, 6);
    const hp = new THREE.Group(), band = basic(0x3c3c44), cupM = basic(0x26262c), red = basic(0xc0392b);
    hp.add(mesh(new THREE.TorusGeometry(0.15, 0.025, 10, 32, Math.PI), band, [0, 0, 0]));
    for (const sd of [-1, 1]) { hp.add(cyl(0.075, 0.075, 0.07, cupM, [sd * 0.15, -0.02, 0], { rot: [0, 0, Math.PI / 2] })); hp.add(box(0.074, 0.05, 0.02, red, [sd * 0.15, -0.02, 0.078], { cast: false })); }
    hp.rotation.set(0, 0.35, 0); hp.position.set(ROW(1) + 0.08, 0.64, 0.92); S.add(hp);
    const pool = new THREE.SpotLight(0xffe2b0, 16, 4, 0.45, 0.6, 1.2); pool.position.set(ROW(1) + 0.1, 2.3, 0.7); pool.target.position.set(ROW(1) + 0.08, 0.55, 0.92); S.add(pool, pool.target);
    grade(S, 0.85);
    return (t, u) => S.camMove(u, [[ROW(1) + 0.3, 1.35, -0.35], [ROW(1) + 0.06, 0.6, 0.92]], [[ROW(1) + 0.25, 1.2, 0.05], [ROW(1) + 0.06, 0.6, 0.92]], ease.lin, [44, 38]);
  },
  // Should he ever have been released?
  '26': (S) => {
    S.sky({ hemi: 0.25, fog: null, sun: [-20, 30, 40], sunI: 0.25, shadow: 15 }); office(S);
    S.scene.traverse(o => { if (o.isPointLight) o.intensity = 6; });
    for (const x of [-7, 0, 7]) { const m = new THREE.Mesh(new THREE.PlaneGeometry(4.6, 4.4), new THREE.MeshBasicMaterial({ color: 0x0b1630 })); m.position.set(x, 5.2, -7.76); S.add(m); }
    const lamp = new THREE.SpotLight(0xffd59a, 140, 16, 0.55, 0.5, 1.3); lamp.position.set(0.5, 7, -2.5); lamp.target.position.set(0, 3.4, -7.6); S.add(lamp, lamp.target);
    const items = [
      { type: 'note', text: 'JULY 30\n2008', at: [-1.9, 0.9] },
      { type: 'note', text: 'NOT\nCRIMINALLY\nRESPONSIBLE', at: [0, 0.95], size: [0.8, 0.8], fontSize: 40 },
      { type: 'note', text: 'FREED\n2017', at: [1.9, 0.9], color: '#ff9f9f' },
      { type: 'note', text: '?', at: [0, -0.9], color: '#ffffff', fontSize: 170, size: [0.75, 0.75] },
    ];
    const board = evidenceBoard(S, { pos: [0, 3.6, -7.55], items, links: [[0, 3], [1, 3], [2, 3]] });
    const det = new Char(S, 'detective', { pos: [1.2, 0, -4.2] });
    grade(S, 0.75);
    return (t, u) => {
      board.userData.setStrings(seg(u, 0.05, 0.6));
      det.set({ facing: -1, aimR: u > 0.15 && u < 0.6 ? [0, 2.7, -7.5] : null, armR: 0.25, eyes: 'half', brow: 0.4, mouth: 'flat', look: u > 0.6 ? 0 : -0.5 });
      S.camMove(u, [[-0.6, 2.4, 2.5], [0.2, 2.9, -7.6]], [[0.6, 2.0, -0.6], [0.8, 2.2, -5]], ease.io, [48, 44]);
    };
  },
};
