// style test: illustrated people + ink outlines, night palette
import { THREE, ease, seg, lerp, clamp, rng, toon, basic, box, cyl, mesh } from '/animator/engine.js';
import { Person, SKIN } from '/animator/people.js';
import { nightSky, flicker, lightBeam } from '/animator/kits/night.js';
import { prairie, makeBus, busInterior, policeCar, glassShards } from '/animator/kits/road.js';

const TIM = { skin: SKIN.fair, hair: 'spiky', hairColor: '#e3c46a', top: 'tshirt', topColor: '#5f9e55', pants: '#7a5a3a', shoes: '#b3261e', headphones: true };
const STRANGER = { skin: SKIN.fair, hair: 'short', hairColor: '#151515', top: 'tshirt', topColor: '#bfc3c7', pants: '#1c1f26', build: 1.1 };
const COP = { skin: SKIN.fair, hair: 'short', hairColor: '#2a1c14', hat: 'police', hatColor: '#1b2333', top: 'uniform', topColor: '#1f2a3d', top2: '#cfd6e0', pants: '#1b2333', stubble: true };
const ROW = (i) => -5.4 + i * 0.95;
const nightBus = (S) => { S.sky({ top: '#0b1430', horizon: '#26375e', bottom: '#0b1020', hemi: 0.9, sunI: 0.5, fog: null, sun: [10, 30, 20] }); const b = busInterior(S, { night: true }); S.ink(); S.grade({ vignette: 0.7, grain: 0.05 }); return b; };

export const shots = {
  '01': (S) => {
    const inside = nightBus(S); flicker(S, inside.userData.light, { amount: 0.6 });
    const tim = new Person(S, TIM, { pos: [ROW(1) + 0.15, -0.12, 0.95], seed: 2, shadow: false });
    tim.set({ seat: 1, expr: 'asleep', tilt: 0.18, turn: -0.3 });
    const man = new Person(S, STRANGER, { pos: [2, 0, 0], seed: 5 });
    for (let i = 0; i < 4; i++) { const p = new Person(S, { skin: [SKIN.light, SKIN.brown, SKIN.fair, SKIN.dark][i], hair: ['bob', 'short', 'buzz', 'bun'][i], hairColor: ['#5a3a22', '#222', '#8a6a3a', '#111'][i], top: ['hoodie', 'jacket', 'tshirt', 'long'][i], topColor: ['#5b4a8a', '#3a5a3a', '#a33', '#2f5f8f'][i] }, { pos: [ROW(3 + i * 2) + 0.15, -0.12, i % 2 ? -0.95 : 0.5], seed: 10 + i, shadow: false }); p.set({ seat: 1, expr: 'asleep', tilt: 0.1 }); }
    return (t, u) => {
      man.pos(lerp(1.8, -2.6, ease.io(u)), 0, 0.05); man.set({ walking: 1, walk: t * 6, expr: 'neutral', inShadow: 1, view: 'front' });
      S.camAt([4.6, 1.7, -0.3], [-3.8, 1.2, 0.4], 50);
    };
  },
  '02': (S) => {
    const inside = nightBus(S); flicker(S, inside.userData.light, { amount: 0.8, seed: 7 });
    const tim = new Person(S, TIM, { pos: [ROW(1) + 0.15, -0.12, 0.95], seed: 2, shadow: false });
    tim.set({ seat: 1, expr: 'asleep', tilt: 0.22, turn: -0.3 });
    const man = new Person(S, STRANGER, { pos: [ROW(1) + 0.15, -0.12, 0.45], seed: 5, shadow: false });
    return (t, u) => { man.set({ seat: 1, turn: 0.45, expr: 'neutral', inShadow: 1, look: 0.8 }); S.camMove(u, [[-2.9, 1.55, -0.25], [-4.3, 1.4, 0.7]], [[-3.3, 1.5, -0.05], [-4.3, 1.45, 0.7]], ease.lin, [44, 40]); };
  },
  '03': (S) => {
    nightSky(S, { fog: [60, 420], moonLight: 1.3, hemi: 0.9 }); prairie(S, { night: true });
    const bus = makeBus({ lit: 0.55 }); S.add(bus); S.ink(); S.grade({ vignette: 0.7, grain: 0.05 });
    for (let x = -60; x < 80; x += 22) { S.add(cyl(0.08, 0.1, 6, toon(0x444a55), [x, 3, -6], { seg: 6 })); lightBeam(S, [x, 6, -5.6], { length: 6, radius: 1.6, spin: 0, opacity: 0.2, tilt: -Math.PI / 2 }); }
    return (t, u) => { const bx = -14 + t * 8; bus.position.set(bx, 0, 1.8); S.shadowFocus(bx, 0, 0); S.camAt([bx + 16, 7, 18], [bx, 1.5, 1.8], 44); };
  },
  '04': (S) => {
    nightSky(S, { fog: [60, 420], moonLight: 1.2, hemi: 0.9 }); prairie(S, { night: true });
    const bus = makeBus({ lit: 0.35 }); bus.position.set(0, 0, 4.4); S.add(bus); bus.userData.windows[3].visible = false;
    policeCar(S, 6, 12.5, { rotY: 2.6, seed: 1 });
    const cops = [[-3.2, 8.4, 0.6], [0.0, 8.6, -0.6], [-1.5, 9.8, 0.2]].map(([x, z, tr], i) => { const c = new Person(S, COP, { pos: [x, 0, z], seed: 30 + i }); c.set({ turn: tr, expr: 'focused', hold: i === 1 ? 'taser' : 'flashlight', aimR: [-1.64 + (i - 1) * 0.3, 1.7, 5.6] }); return c; });
    const man = new Person(S, STRANGER, { pos: [-1.64, 1.0, 5.35], seed: 5, shadow: false }); man.set({ inShadow: 1, armL: [2.4, 0.4], armR: [2.4, 0.4] });
    const shards = glassShards(S, [-1.64, 2.75, 5.72], { dir: [0, 0, 1] });
    S.ink(); S.grade({ vignette: 0.7, grain: 0.05 });
    return (t, u) => { shards.userData.burst(u * S.duration * 0.5); S.camMove(u, [[-0.4, 1.3, 14], [-1.6, 2.0, 6]], [[-0.8, 1.4, 12.5], [-1.6, 2.1, 6]], ease.io, [46, 44]); };
  },
};
