// animation.js - the animated shots for example/script.txt ("The Round Windows", part 1)
// Each shot id matches a [NN] marker in the script. A shot gets the stage S and
// returns update(t, u): t = seconds into the shot, u = 0..1 progress through it.
import { THREE, ease, seg, lerp, clamp, lerp3, rng, toon, basic, box, mesh } from '/animator/engine.js';
import { Char } from '/animator/cast.js';
import { makeJet, airfield, hangar, scaffold, office, draftTable, terminal, counter, cabin, newspaper, confetti, tumbleweed, crackOverlay } from '/animator/props.js';

const HERO = { windows: 'round', stripe: '#169e8f', name: 'SKYWARD' };
const RIVAL = { windows: 'square', stripe: '#c8302e', name: 'JETLUX' };

// ---------------------------------------------------------------- shared sets
function hangarSet(S, team = HERO, o = {}) {
  S.sky({ top: '#4a86e0', horizon: '#ffe2b8', fog: [90, 500], sun: [30, 70, 60], hemi: 1.5, shadow: 45 });
  hangar(S);
  const jet = makeJet(team);
  jet.position.set(0, jet.userData.groundY, -10);
  S.add(jet);
  if (o.scaffold !== false) { scaffold(S, 3, -6.4, 2); scaffold(S, -6, -6.4, 4); }
  S.shadowFocus(0, 0, -10);
  return jet;
}
function outdoorSky(S, o = {}) {
  S.sky({ top: '#2f6fd6', horizon: '#cfe6ff', bottom: '#e9cfa0', sun: [-60, 70, 50], fog: [120, 900], shadow: 60, ...o });
}
function crowd(S, n, [x0, x1], [z0, z1], o = {}) {
  const R = rng(o.seed || 9), out = [];
  for (let i = 0; i < n; i++) {
    const c = new Char(S, 'extra', { seed: (o.seed || 9) * 100 + i, h: 1.85 + R() * 0.3, hat: o.hat });
    c.pos(lerp(x0, x1, R()), 0, lerp(z0, z1, R()));
    c.set({ facing: R() < 0.5 ? 1 : -1, look: (R() - 0.5) * 0.6 });
    c.r = R(); out.push(c);
  }
  return out;
}
function cheer(c, t) {
  const k = Math.sin(t * 9 + c.r * 6);
  c.set({ eyes: 'happy', mouth: 'grin', armL: 2.6 + k * 0.25, armR: 2.6 - k * 0.25, hop: Math.max(0, k) * 0.35 });
}

// ---------------------------------------------------------------- the shots
export const shots = {
  // He put tiny round windows on his airplane
  '01': (S) => {
    const jet = hangarSet(S);
    const slot = jet.userData.windows[10]; slot.scale.setScalar(0.001);
    const hero = new Char(S, 'hero', { pos: [3.0, 2.08, -6.9] });
    hero.set({ hold: 'window', armR: 0.4, armL: 0.3, facing: -1 });
    return (t, u) => {
      const lift = ease.out(seg(u, 0.05, 0.4));
      const placed = u > 0.55;
      hero.set({ armR: placed ? lerp(2.4, 0.5, ease.out(seg(u, 0.55, 0.8))) : lerp(0.4, 2.4, lift), hold: placed ? null : 'window',
                 eyes: placed ? 'happy' : 'half', mouth: placed ? 'grin' : 'smile' });
      slot.scale.setScalar(placed ? ease.back(seg(u, 0.55, 0.7)) || 0.001 : 0.001);
      S.camMove(u, [[5.6, 3.3, -2.6], [3.2, 3.2, -8]], [[10.5, 4.6, 5.5], [1.0, 3.3, -8.5]], ease.io, [42, 48]);
    };
  },
  // when everyone wanted big square ones.
  '02': (S) => {
    outdoorSky(S); airfield(S);
    const jet = makeJet(RIVAL); jet.position.set(0, jet.userData.groundY, -62); S.add(jet);
    const fans = crowd(S, 7, [-9, 7], [-55.5, -54], { seed: 2 });
    S.shadowFocus(0, 0, -58);
    return (t, u) => {
      fans.forEach(c => { c.set({ eyes: 'happy', mouth: 'grin', armR: 2.2 + Math.sin(t * 8 + c.r * 9) * 0.4, armL: 0.3, look: -0.4 }); });
      S.camMove(u, [[-10, 2.6, -47], [-4, 3.6, -60.5]], [[6, 3.4, -46], [8, 3.6, -60.5]], ease.io, [40, 40]);
    };
  },
  // You see, two companies are racing
  '03': (S) => {
    outdoorSky(S); airfield(S);
    const a = makeJet({ ...HERO }); a.position.set(-24, a.userData.groundY, -62); S.add(a);
    const b = makeJet({ ...RIVAL }); b.position.set(24, b.userData.groundY, -62); S.add(b);
    scaffold(S, -24, -57, 4); scaffold(S, 24, -57, 4); scaffold(S, -14, -66, 6); scaffold(S, 34, -66, 6);
    crowd(S, 10, [-34, 34], [-52, -48], { seed: 3, hat: 'hardhat' });
    S.shadowFocus(0, 0, -60);
    return (t, u) => S.camMove(u, [[0, 46, 6], [0, 0, -62]], [[0, 12, -24], [0, 3, -62]], ease.io, [50, 54]);
  },
  // to build the world's first jet airliner,
  '04': (S) => {
    const jet = hangarSet(S, HERO);
    const workers = [];
    [[9, -6.9], [12.5, -7.2], [-2, -6.9], [-9, -7]].forEach(([x, z], i) => {
      const w = new Char(S, 'extra', { seed: 40 + i, hat: 'hardhat', pos: [x, 0, z] });
      w.set({ hold: 'hammer', facing: i % 2 ? 1 : -1 }); w.r = i; workers.push(w);
    });
    return (t, u) => {
      workers.forEach(w => { const k = Math.sin(t * 11 + w.r * 2); w.set({ armR: 1.6 + k * 0.9, eyes: 'half', mouth: k > 0.6 ? 'open' : 'flat' }); });
      S.camOrbit(u, [10, 3, -10], 17, 0.9, 0.15, 3.5, ease.io, 48);
    };
  },
  // and whoever flies first
  '05': (S) => {
    outdoorSky(S); airfield(S);
    const jet = makeJet({ windows: 'round', stripe: '#d9a21b', name: '' }); S.add(jet);
    S.shadowFocus(0, 0, 0);
    return (t, u) => {
      const k = ease.in(u) * 0.6 + u * 0.4;
      const x = lerp(-60, 45, k), climb = Math.max(0, x + 5) * 0.12;
      jet.position.set(x, jet.userData.groundY + climb, 0); jet.rotation.z = Math.min(0.18, climb * 0.02);
      jet.userData.gear.visible = true;
      S.shadowFocus(x, 0, 0);
      S.camAt([lerp(-6, 8, u), 1.0, 26], [x * 0.85, 3 + climb * 0.8, 0], 50);
    };
  },
  // gets every passenger in the country.
  '06': (S) => {
    S.sky({ hemi: 1.6, fog: [40, 200], sun: [10, 60, 40] }); terminal(S);
    const ppl = crowd(S, 16, [-5, 5], [-4, 9], { seed: 6 });
    ppl.forEach(c => c.set({ hold: c.r < 0.6 ? 'suitcase' : 'ticket', armR: 0.15 }));
    S.shadowFocus(0, 0, 4);
    return (t, u) => {
      ppl.forEach(c => { c.group.position.z += 0.05; c.set({ walking: 1, walk: t * 9 + c.r * 7, mouth: 'smile', facing: c.r < .5 ? 1 : -1 }); });
      S.camMove(u, [[0, 2.4, 15], [0, 1.6, 4]], [[0, 3.2, 19], [0, 1.4, 3]], ease.out, [52, 56]);
    };
  },
  // He's the youngest designer
  '07': (S) => {
    S.sky({ hemi: 1.5, fog: null, sun: [-20, 30, 40], shadow: 15 }); office(S);
    const tb = draftTable(S, 0, -1.5, { tilt: 0.55 });
    const hero = new Char(S, 'hero', { pos: [-1.9, 0, -0.6] });
    hero.set({ hold: 'pencil', facing: 1, look: 0.2 });
    return (t, u) => {
      hero.set({ armR: 1.25 + Math.sin(t * 14) * 0.15, eyes: 'half', mouth: 'smile' });
      S.camMove(u, [[-3.6, 2.5, 5.2], [-1.0, 1.9, -0.8]], [[-3.0, 2.2, 3.4], [-1.4, 1.9, -0.8]], ease.io, [46, 42]);
    };
  },
  // on the team.
  '08': (S) => {
    S.sky({ hemi: 1.5, fog: null, sun: [-20, 30, 40], shadow: 20 }); office(S);
    const elders = [];
    [[-6, -4], [0, -4], [6, -4], [-6, 2], [6, 2]].forEach(([x, z], i) => {
      draftTable(S, x, z, { tilt: 0.5 });
      const c = new Char(S, 'extra', { seed: 80 + i, hat: i % 2 ? 'hair' : 'none', pos: [x - 1.2, 0, z + 1.3] });
      c.d.hairColor = '#9a9a9a'; c.d.glasses = i % 2 ? 'round' : null; c.set({ hold: 'pencil', armR: 1.2, eyes: 'half', mouth: 'frown' }); elders.push(c);
    });
    draftTable(S, 0, 2, { tilt: 0.5 });
    const hero = new Char(S, 'hero', { pos: [-1.2, 0, 3.3] }); hero.set({ hold: 'pencil', armR: 1.2 });
    return (t, u) => {
      elders.forEach((c, i) => c.set({ armR: 1.2 + Math.sin(t * 10 + i) * 0.12 }));
      hero.set({ eyes: u > 0.5 ? 'happy' : 'half', mouth: 'grin', look: 0.3 });
      S.camMove(u, [[-0.8, 2.4, 7], [-1, 1.6, 3]], [[0, 5.5, 12.5], [0, 0.8, -1]], ease.out, [46, 52]);
    };
  },
  // And when his boss sees
  '09': (S) => {
    S.sky({ hemi: 1.5, fog: null, sun: [-20, 30, 40], shadow: 20 }); office(S);
    draftTable(S, -2, -2, { tilt: 0.5 });
    const boss = new Char(S, 'boss', { pos: [7, 0, 2], h: 2.15 });
    return (t, u) => {
      const k = ease.out(seg(u, 0, 0.8));
      boss.pos(lerp(7, 1.6, k), 0, lerp(2.5, 0.5, k));
      boss.set({ walking: u < 0.8 ? 1 : 0, walk: t * 10, facing: -1, eyes: u > 0.7 ? 'wide' : 'dot', brow: u > 0.7 ? 0.6 : 0, look: -0.35 });
      S.camAt([lerp(3.4, 2.4, u), 0.5, 6], [1.8, 2.0, 0.5], 48);
    };
  },
  // those little round windows on the blueprint,
  '10': (S) => {
    S.sky({ hemi: 1.5, fog: null, sun: [-20, 30, 40], shadow: 15 }); office(S);
    const tb = draftTable(S, 0, 0, { tilt: 0.0 });
    S.camera.up.set(0, 0, -1);
    return (t, u) => {
      // straight down onto the blueprint, pushing in on the windows
      S.camMove(u, [[0, 4.6, 0.6], [0, 2.3, 0]], [[0.25, 2.95, 0.12], [0.25, 2.3, 0.0]], ease.io, [50, 50]);
    };
  },
  // he slams the table.
  '11': (S) => {
    S.sky({ hemi: 1.5, fog: null, sun: [-20, 30, 40], shadow: 15 }); office(S);
    const tb = draftTable(S, 0, -0.4, { tilt: 0.25 });
    const boss = new Char(S, 'boss', { pos: [0.2, 0, 0.9], h: 2.15 });
    const hero = new Char(S, 'hero', { pos: [-2.6, 0, -1.6] });
    return (t, u) => {
      const anger = ease.io(seg(u, 0, 0.45));
      const slam = seg(u, 0.42, 0.5);
      const arms = u < 0.42 ? lerp(0.3, 2.9, ease.out(seg(u, 0.1, 0.42))) : lerp(2.9, 1.25, ease.in(slam));
      boss.set({ anger: anger * 0.8, brow: 1, eyes: 'angry', mouth: u > 0.45 ? 'shout' : 'frown', armL: arms, armR: arms, facing: -1, look: -0.2, squash: u > 0.5 ? Math.max(0, 0.08 - (u - 0.5)) : 0 });
      hero.set({ eyes: u > 0.5 ? 'wide' : 'half', sweat: u > 0.5 ? 1 : 0, mouth: u > 0.5 ? 'o' : 'smile', hop: u > 0.5 && u < 0.6 ? 0.4 : 0 });
      tb.userData.board.position.y = 2.25 + (u > 0.5 && u < 0.62 ? Math.sin((u - 0.5) * 50) * 0.08 : 0);
      S.shake = u > 0.5 && u < 0.72 ? 0.12 * (1 - seg(u, 0.5, 0.72)) : 0;
      S.camAt([lerp(-1.6, -1.2, u), 2.2, 5.6], [-0.3, 2.0, 0], 46);
    };
  },
  // Passengers want a view!
  '12': (S) => {
    S.sky({ hemi: 1.5, fog: null, sun: [-20, 30, 40], shadow: 15 }); office(S);
    const boss = new Char(S, 'boss', { pos: [0, 0, 0], h: 2.15 });
    return (t, u) => {
      boss.set({ anger: lerp(0.8, 1, seg(u, 0, 0.4)), brow: 1, eyes: 'angry', talk: u < 0.92 ? 1 : 0, steam: seg(u, 0.1, 0.3), armL: 1.6 + Math.sin(t * 12) * 0.2, armR: 0.9, look: 0 });
      S.shake = 0.025;
      S.camMove(u, [[0, 1.65, 2.6], [0, 1.65, 0]], [[0, 1.6, 1.75], [0, 1.65, 0]], ease.out, [48, 48]);
    };
  },
  // But he won't change
  '13': (S) => {
    S.sky({ hemi: 1.5, fog: null, sun: [-20, 30, 40], shadow: 15 }); office(S);
    const hero = new Char(S, 'hero', { pos: [0, 0, 0] });
    hero.set({ armsCrossed: true, eyes: 'half', mouth: 'smile', look: 0.1 });
    return (t, u) => S.camMove(u, [[0.6, 1.4, 2.6], [0, 1.5, 0]], [[0.2, 1.45, 2.1], [0, 1.5, 0]], ease.out, [46, 46]);
  },
  // a single one.
  '14': (S) => {
    const jet = hangarSet(S, HERO, { scaffold: false });
    return (t, u) => S.camMove(u, [[-8, 3.8, -6.2], [-4, 3.6, -8.6]], [[4, 3.7, -6.0], [8, 3.6, -8.6]], ease.lin, [38, 38]);
  },
  // The other company builds big,
  '15': (S) => {
    const jet = hangarSet(S, RIVAL);
    const rival = new Char(S, 'rival', { pos: [4, 0, -3.5], h: 2.2 });
    const crew = crowd(S, 4, [-8, 12], [-6.8, -6.4], { seed: 15, hat: 'hardhat' });
    crew.forEach(c => c.set({ hold: 'hammer' }));
    return (t, u) => {
      rival.set({ armL: lerp(0.3, 2.3, ease.back(seg(u, 0.1, 0.5))), armR: lerp(0.3, 2.3, ease.back(seg(u, 0.1, 0.5))), mouth: 'smirk', facing: 1 });
      crew.forEach(c => c.set({ armR: 1.6 + Math.sin(t * 11 + c.r * 5) * 0.9 }));
      S.camMove(u, [[5, 1.0, 4], [4, 2.0, -3.5]], [[6.5, 4.5, 8], [2, 3.4, -8]], ease.io, [46, 52]);
    };
  },
  // beautiful square windows,
  '16': (S) => {
    const jet = hangarSet(S, RIVAL, { scaffold: false });
    // a moving glint across each window
    const sheen = [];
    jet.userData.windows.slice(6, 12).forEach(w => {
      const s = new THREE.Mesh(new THREE.PlaneGeometry(0.16, 0.8), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.7, toneMapped: false }));
      s.rotation.z = -0.5; s.position.z = 0.02; w.add(s); sheen.push(s);
    });
    return (t, u) => {
      sheen.forEach((s, i) => { const k = ((u * 1.6 - i * 0.08) % 1); s.position.x = lerp(-0.6, 0.6, k); s.visible = k > 0 && k < 1; });
      S.camMove(u, [[-1.2, 3.75, -6.4], [0.5, 3.65, -8.5]], [[2.2, 3.7, -6.7], [3.5, 3.65, -8.5]], ease.io, [34, 32]);
    };
  },
  // and launches first.
  '17': (S) => {
    outdoorSky(S); airfield(S);
    const jet = makeJet(RIVAL); S.add(jet);
    const fans = crowd(S, 12, [-8, 8], [26, 30], { seed: 17 });
    confetti(S, 350, [24, 14, 10], [0, 0, 28]);
    return (t, u) => {
      const x = lerp(-50, 60, ease.in(u) * 0.5 + u * 0.5), climb = Math.max(0, x + 10) * 0.18;
      jet.position.set(x, jet.userData.groundY + climb, 0); jet.rotation.z = Math.min(0.22, climb * 0.025);
      jet.userData.gear.visible = climb < 6;
      S.shadowFocus(x, 0, 0);
      fans.forEach(c => cheer(c, t));
      S.camAt([lerp(-3, 3, u), 3.2, 38], [x * 0.6, 4 + climb * 0.5, 0], 52);
    };
  },
  // Their passengers love it.
  '18': (S) => {
    S.sky({ hemi: 1.7, fog: null, sun: [0, 40, 20], shadow: 15 });
    cabin(S, { windows: 'square' });
    const pax = [];
    for (let i = 0; i < 9; i++) {
      const x = -14 + i * 2.4 + 0.15;
      const c = new Char(S, 'extra', { seed: 180 + i, pos: [x, 0.2, -1.55], h: 1.7, shadow: false });
      c.set({ sit: true, facing: -1, look: -0.6 }); c.r = i; pax.push(c);
    }
    return (t, u) => {
      pax.forEach(c => c.set({ eyes: 'happy', mouth: 'grin', armL: c.r % 3 === 0 ? 2.4 + Math.sin(t * 9 + c.r) * 0.3 : 0.3 }));
      S.camMove(u, [[4, 1.9, 1.6], [1, 1.5, -2.2]], [[-6, 1.9, 1.6], [-8, 1.5, -2.2]], ease.io, [58, 58]);
    };
  },
  // While his plane gets a nickname
  '19': (S) => {
    const jet = hangarSet(S, HERO, { scaffold: false });
    const hero = new Char(S, 'hero', { pos: [2, 0, -2] });
    hero.set({ eyes: 'dot', mouth: 'flat', brow: -0.6, armL: 0.1, armR: 0.1, look: -0.2 });
    return (t, u) => S.camMove(u, [[9, 5, 12], [1.5, 2.2, -3]], [[3.5, 2.4, 3.2], [2, 1.6, -2]], ease.io, [48, 44]);
  },
  // in the papers:
  '20': (S) => {
    S.scene.background = new THREE.Color('#f2b134');
    const rays = new THREE.Mesh(new THREE.CircleGeometry(40, 24), new THREE.MeshBasicMaterial({ color: 0xffd36b, toneMapped: false }));
    rays.position.z = -10; S.add(rays);
    const burst = new THREE.Group();
    for (let i = 0; i < 12; i++) { const r = new THREE.Mesh(new THREE.PlaneGeometry(4, 60), new THREE.MeshBasicMaterial({ color: 0xf09a1e, toneMapped: false })); r.rotation.z = i * Math.PI / 6; r.position.z = -9; burst.add(r); }
    S.add(burst);
    const paper = newspaper(); S.add(paper);
    return (t, u) => {
      const k = ease.out(seg(u, 0, 0.75));
      paper.rotation.z = (1 - k) * Math.PI * 5; paper.scale.setScalar(lerp(0.05, 1, k));
      burst.rotation.z = t * 0.6;
      S.camAt([0, 0, 6.2], [0, 0, 0], 50);
    };
  },
  // the porthole plane.
  '21': (S) => {
    S.sky({ hemi: 1.5, fog: null, sun: [-20, 30, 40], shadow: 15 }); office(S);
    const paper = newspaper(); paper.position.set(0, 2.6, 0.5); S.add(paper);
    const laughers = [new Char(S, 'extra', { seed: 211, pos: [-2.3, 0, -1] }), new Char(S, 'extra', { seed: 212, pos: [2.4, 0, -1] })];
    return (t, u) => {
      laughers.forEach((c, i) => c.set({ eyes: 'happy', mouth: 'grin', armL: 0.4, armR: 1.4 + Math.sin(t * 14 + i) * 0.2, hop: Math.abs(Math.sin(t * 12 + i)) * 0.15, facing: i ? -1 : 1 }));
      paper.rotation.z = Math.sin(t * 3) * 0.03;
      S.camMove(u, [[0, 2.6, 6.4], [0, 2.6, 0.5]], [[0, 3.05, 3.4], [0, 3.1, 0.5]], ease.io, [48, 46]);
    };
  },
  // And everyone books the other airline.
  '22': (S) => {
    S.sky({ hemi: 1.6, fog: [40, 200], sun: [10, 60, 40] }); terminal(S);
    counter(S, 4.5, -8, { name: 'JETLUX', color: '#c8302e' });
    counter(S, -4.5, -8, { name: 'SKYWARD', color: '#169e8f' });
    const line = [];
    for (let i = 0; i < 9; i++) { const c = new Char(S, 'extra', { seed: 220 + i, pos: [4.5 + Math.sin(i) * 0.4, 0, -5.8 + i * 1.4] }); c.set({ hold: 'suitcase', facing: -1, mouth: 'smile', look: -0.3 }); line.push(c); }
    const hero = new Char(S, 'hero', { pos: [-4.5, 0, -9.6] }); hero.set({ eyes: 'dot', mouth: 'flat', brow: -0.6, armL: 0.6, armR: 0.6 });
    const tw = tumbleweed(S);
    S.shadowFocus(0, 0, -2);
    return (t, u) => {
      line.forEach((c, i) => c.set({ walking: Math.sin(t * 3 + i) > 0.6 ? 0.5 : 0, walk: t * 8 }));
      tw.position.set(lerp(2, -8, u), 0.7 + Math.abs(Math.sin(t * 6)) * 0.4, -5.5); tw.rotation.z = t * 5;
      S.camMove(u, [[5.5, 3.4, 9], [4.5, 2.4, -3]], [[-3.5, 3.0, 6], [-4.5, 2.6, -8]], ease.io, [56, 56]);
    };
  },
  // Then, one day at thirty thousand feet,
  '23': (S) => {
    S.sky({ top: '#1f4fa8', horizon: '#ffd2a8', bottom: '#f5e6d6', sun: [-80, 40, 20], sunColor: 0xffd9a8, fog: [150, 700], hemi: 1.3, shadow: 40 });
    const jet = makeJet({ ...RIVAL, gear: false }); S.add(jet);
    const R = rng(23), clouds = [];
    for (let i = 0; i < 40; i++) clouds.push([S.cloud([(R() - .5) * 600, -30 - R() * 25, (R() - .5) * 500], 2 + R() * 3, 230 + i), R()]);
    for (let i = 0; i < 8; i++) clouds.push([S.cloud([(R() - .5) * 300, -4 + R() * 10, -40 - R() * 60], 1 + R(), 300 + i), R()]);
    return (t, u) => {
      clouds.forEach(([c, r]) => { c.position.x -= 1.4 + r * 0.6; if (c.position.x < -320) c.position.x += 640; });
      jet.position.y = Math.sin(t * 1.3) * 0.3; jet.rotation.x = Math.sin(t * 0.9) * 0.03;
      S.shadowFocus(0, 0, 0);
      S.camOrbit(u, [3, 0, 0], 19, 0.5, -0.1, 2.5, ease.io, 50);
    };
  },
  // something weird happens.
  '24': (S) => {
    S.sky({ top: '#1f3f88', horizon: '#ffb78a', bottom: '#f5e6d6', sun: [-80, 40, 20], sunColor: 0xffc890, fog: [150, 700], hemi: 1.2 });
    const jet = makeJet({ ...RIVAL, gear: false }); S.add(jet);
    const win = jet.userData.windows[8];
    const crack = crackOverlay(0.76, 0.64); crack.position.z = 0.02; win.add(crack);
    const R = rng(24);
    for (let i = 0; i < 20; i++) S.cloud([(R() - .5) * 400, -30 - R() * 20, (R() - .5) * 300], 2 + R() * 2, 240 + i);
    jet.updateMatrixWorld(true);
    const wp = new THREE.Vector3(); win.getWorldPosition(wp);
    return (t, u) => {
      crack.userData.setProgress(ease.out(seg(u, 0.55, 0.85)));
      S.shake = u > 0.55 ? 0.006 : 0.002;
      const d = lerp(3.4, 1.15, ease.io(seg(u, 0, 0.9)));
      S.camAt([wp.x + 0.25, wp.y + 0.1, wp.z + d], [wp.x + 0.1, wp.y, wp.z], 40);
    };
  },
};
