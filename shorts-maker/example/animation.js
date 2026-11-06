// animation.js - the animated shots for example/script.txt ("The Round Windows", part 1)
// Each shot id matches a [NN] marker in the script. A shot gets the stage S and
// returns update(t, u): t = seconds into the shot, u = 0..1 progress through it.
import { THREE, ease, seg, lerp, clamp, lerp3, rng, toon, basic, box, mesh } from '/animator/engine.js';
import { Char } from '/animator/cast.js';
import { makeJet, airfield, hangar, scaffold, hangarFront, desk, impactBurst, office, draftTable, terminal, counter, cabin, newspaper, confetti, tumbleweed, crackOverlay } from '/animator/props.js';

const HERO = { windows: 'round', stripe: '#169e8f', name: 'SKYWARD' };
const RIVAL = { windows: 'square', stripe: '#c8302e', name: 'JETLUX' };

// ---------------------------------------------------------------- shared sets
function hangarSet(S, team = HERO, o = {}) {
  S.sky({ top: '#4a86e0', horizon: '#ffe2b8', fog: [90, 500], sun: [30, 70, 60], hemi: 1.5, shadow: 45 });
  hangar(S);
  const jet = makeJet(team);
  jet.position.set(0, jet.userData.groundY, -10);
  S.add(jet);
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
  // FIX: real scaffold (no "table"), hero big, window visibly pressed into an empty frame + pop
  '01': (S) => {
    const jet = hangarSet(S, HERO);
    const slot = jet.userData.windows[13];                 // x ≈ 7.66, empty until he fits it
    const glass = slot.children[1]; glass.visible = false;
    scaffold(S, 7.0, -7.0, 2.2, { w: 2.8, d: 1.6 });
    const hero = new Char(S, 'hero', { pos: [7.15, 2.26, -7.25] });
    hero.set({ hold: 'window', facing: 1 });
    const pop = impactBurst(S, { text: null, size: 0.9, color: '#bfefff' }); pop.position.set(7.66, 3.65, -8.2);
    return (t, u) => {
      const placed = u > 0.4;
      hero.set({ armR: placed ? lerp(1.9, 0.5, ease.out(seg(u, 0.45, 0.7))) : lerp(0.5, 1.9, ease.out(seg(u, 0.0, 0.35))),
                 hold: placed ? null : 'window', eyes: placed ? 'happy' : 'half', mouth: placed ? 'grin' : 'smile',
                 hop: placed && u < 0.55 ? 0.2 : 0 });
      glass.visible = placed;
      slot.scale.setScalar(placed ? 1 + 0.35 * Math.sin(seg(u, 0.4, 0.55) * Math.PI) : 1);
      pop.show(placed ? (u - 0.4) * S.duration : -1);
      S.camMove(u, [[6.5, 3.5, -3.8], [7.2, 3.4, -8.2]], [[5.0, 3.8, 0.0], [6.3, 3.3, -8.4]], ease.io, [44, 50]);
    };
  },
  // when everyone wanted big square ones.
  // FIX: jet out in the open with sky behind (no sliding orange building), shoot the nose section (no wing slab), crowd framed from frame 1
  '02': (S) => {
    outdoorSky(S); airfield(S, { runway: false });
    const jet = makeJet(RIVAL); jet.position.set(0, jet.userData.groundY, 14); S.add(jet);
    const fans = crowd(S, 7, [4, 10], [4.5, 6.5], { seed: 2 });
    S.shadowFocus(6, 0, 10);
    return (t, u) => {
      fans.forEach(c => c.set({ eyes: 'happy', mouth: 'grin', armR: 2.3 + Math.sin(t * 8 + c.r * 9) * 0.3, armL: c.r < 0.5 ? 0.3 : 2.0,
                                hop: Math.max(0, Math.sin(t * 9 + c.r * 7)) * 0.2, look: 0.4 }));
      S.camMove(u, [[4.5, 1.3, -1], [7, 3.3, 14]], [[9, 1.6, 0], [10, 3.5, 14]], ease.io, [56, 54]);
    };
  },
  // You see, two companies are racing
  // FIX: split screen - SKYWARD yard on top, JETLUX yard below, cameras racing in opposite directions
  '03': (S) => {
    outdoorSky(S, { shadow: 110 }); airfield(S, { runway: false });
    const [A, B] = S.splitScreen();
    const crews = [];
    for (const [cx, team, seed] of [[-80, HERO, 32], [80, RIVAL, 31]]) {
      hangarFront(S, cx, -22, { name: team.name, color: team.stripe });
      const jet = makeJet(team); jet.position.set(cx, jet.userData.groundY, -3); S.add(jet);
      const crew = crowd(S, 4, [cx - 6, cx + 8], [6, 8], { seed, hat: 'hardhat' });
      crew.forEach(c => { c.set({ hold: 'hammer' }); crews.push(c); });
    }
    S.shadowFocus(0, 0, 0);
    return (t, u) => {
      crews.forEach(c => c.set({ armR: 1.5 + Math.cos(t * 13 + c.r * 6) * 0.9, walking: 0.6, walk: t * 10 + c.r * 5 }));
      S.camMoveOn(A, u, [[-92, 8, 22], [-80, 3.5, -4]], [[-72, 7.5, 20], [-76, 3.5, -4]], ease.io, [42, 42]);
      S.camMoveOn(B, u, [[92, 8, 22], [80, 3.5, -4]], [[72, 7.5, 20], [76, 3.5, -4]], ease.io, [42, 42]);
    };
  },
  // to build the world's first jet airliner,
  // FIX: workers big on scaffolds, hammers actually hit the fuselage with sparks, closer orbit
  '04': (S) => {
    const jet = hangarSet(S, HERO);
    scaffold(S, 7.2, -7.0, 2.2, { w: 2.6, d: 1.6 }); scaffold(S, 10.3, -7.0, 2.2, { w: 2.6, d: 1.6 });
    const w1 = new Char(S, 'extra', { seed: 41, hat: 'hardhat', pos: [7.2, 2.26, -7.25] });
    const w2 = new Char(S, 'extra', { seed: 42, hat: 'hardhat', pos: [10.3, 2.26, -7.25] });
    const boss = new Char(S, 'extra', { seed: 43, hat: 'cap', pos: [8.8, 0, -4.6] });
    w1.set({ hold: 'hammer', facing: 1 }); w2.set({ hold: 'hammer', facing: -1 }); boss.set({ hold: 'blueprint', armR: 1.2 });
    const sp = [impactBurst(S, { text: null, size: 0.6, color: '#ffe066' }), impactBurst(S, { text: null, size: 0.6, color: '#ffe066' })];
    sp[0].position.set(7.75, 3.45, -8.25); sp[1].position.set(9.75, 3.45, -8.25);
    return (t, u) => {
      [[w1, 0], [w2, 1.7]].forEach(([w, off], i) => {
        const ph = t * 8 + off;
        w.set({ armR: 1.5 + Math.cos(ph) * 0.95, eyes: 'half', mouth: Math.cos(ph) < -0.8 ? 'grin' : 'flat' });
        const since = (((ph - Math.PI) % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI) / 8;   // s since the hammer hit
        sp[i].show(since < 0.18 ? since : -1);
      });
      boss.set({ armL: 2.2 + Math.sin(t * 6) * 0.2, talk: 0.8, look: 0.5 });
      S.camOrbit(u, [8.7, 2.6, -7.4], 7.2, 0.7, 0.1, 0.5, ease.io, 54);
    };
  },
  // and whoever flies first
  // FIX: the jet actually lifts off and roars over the camera
  '05': (S) => {
    outdoorSky(S); airfield(S);
    const jet = makeJet({ windows: 'round', stripe: '#d9a21b', name: '' }); S.add(jet);
    return (t, u) => {
      const x = lerp(-55, 30, ease.in(u) * 0.4 + u * 0.6);
      const climb = Math.max(0, x + 35) * 0.22;
      jet.position.set(x, jet.userData.groundY + climb, 0); jet.rotation.z = Math.min(0.2, climb * 0.03);
      jet.userData.gear.visible = climb < 9;
      S.shadowFocus(x, 0, 0);
      S.camAt([22, 0.8, 6], [x, 3 + climb * 0.9, 0], 58);
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
  // FIX: board faces the camera, hero visibly drawing on it
  '07': (S) => {
    S.sky({ hemi: 1.5, fog: null, sun: [-20, 30, 40], shadow: 15 }); office(S);
    draftTable(S, 0.3, -1.2, { tilt: -1.0 });
    const hero = new Char(S, 'hero', { pos: [-1.0, 0, -0.5] });
    hero.set({ hold: 'pencil', facing: 1 });
    return (t, u) => {
      hero.set({ armR: 1.45 + Math.sin(t * 16) * 0.12, eyes: u < 0.6 ? 'half' : 'happy', mouth: 'smile', look: 0.5 });
      S.camMove(u, [[-0.2, 2.1, 4.6], [-0.3, 1.9, -0.9]], [[-0.6, 2.0, 3.2], [-0.5, 1.9, -0.9]], ease.io, [46, 44]);
    };
  },
  // on the team.
  // FIX: the older team stands in a visible row, arms crossed, turning to look at the young hero who waves
  '08': (S) => {
    S.sky({ hemi: 1.5, fog: null, sun: [-20, 30, 40], shadow: 20 }); office(S);
    [-5, -1.5, 2].forEach(x => draftTable(S, x, -4.5, { tilt: -0.5 }));
    const elders = [[-4.2, 0.2], [-2.6, 0.5], [-1.0, 0.2], [0.6, 0.5]].map(([x, z], i) => {
      const c = new Char(S, 'extra', { seed: 80 + i, pos: [x, 0, z] });
      Object.assign(c.d, { hairColor: '#a8a8a8', hat: i % 2 ? 'hair' : 'none', bald: i === 0, mustache: i === 0 ? 'walrus' : i === 2 ? 'pencil' : null, glasses: i % 2 ? 'round' : null });
      c.set({ armsCrossed: true, eyes: 'half', mouth: 'frown', brow: 0.3 }); return c;
    });
    const hero = new Char(S, 'hero', { pos: [2.5, 0, 1.2] });
    return (t, u) => {
      elders.forEach(c => c.set({ look: u > 0.3 ? 0.7 : 0 }));
      hero.set({ eyes: 'happy', mouth: 'grin', armR: 2.4 + Math.sin(t * 10) * 0.25 });
      S.camMove(u, [[2.0, 1.8, 5.2], [2.2, 1.5, 1]], [[-0.8, 2.8, 13.5], [-0.8, 1.3, 0.5]], ease.out, [48, 52]);
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
  // FIX: boss BEHIND a real desk facing camera; wind-up, fists come down ON the desk top,
  // everything on the desk jumps, BAM burst, camera shake, hero flinches in the background
  '11': (S) => {
    S.sky({ hemi: 1.5, fog: null, sun: [-20, 30, 40], shadow: 15 }); office(S);
    const dk = desk(S, 0, 0, { top: 0.8 });
    const boss = new Char(S, 'boss', { pos: [0, 0, -0.95], h: 2.15 });
    const hero = new Char(S, 'hero', { pos: [2.4, 0, -3.5] });
    const bam = impactBurst(S, { text: 'BAM!', size: 1.2 }); bam.position.set(0.55, 0.95, -0.6);
    const HIT = 0.42;
    return (t, u) => {
      const k = (u - HIT) * S.duration;                     // seconds since the fists land
      const arms = u < 0.3 ? lerp(0.3, 2.9, ease.out(seg(u, 0.02, 0.3)))
                 : u < HIT ? lerp(2.9, 0.75, ease.in(seg(u, 0.3, HIT))) : 0.75;
      boss.set({ anger: lerp(0.15, 0.85, ease.io(seg(u, 0, HIT))), brow: 1, eyes: 'angry', mouth: k > 0 ? 'shout' : 'frown',
                 armL: arms, armR: arms, squash: k > 0 && k < 0.12 ? 0.08 : 0 });
      hero.set({ eyes: k > 0 ? 'wide' : 'half', mouth: k > 0 ? 'o' : 'smile', sweat: k > 0 ? 1 : 0,
                 hop: k > 0 && k < 0.3 ? Math.sin(k / 0.3 * Math.PI) * 0.5 : 0, facing: -1 });
      dk.userData.jolt(k);
      bam.show(k);
      S.shake = k > 0 && k < 0.35 ? 0.09 * (1 - k / 0.35) : 0;
      S.camMove(u, [[0.3, 1.55, 4.2], [0, 1.3, -0.9]], [[0.15, 1.5, 3.4], [0, 1.3, -0.9]], ease.out, [48, 48]);
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
  // FIX: low "power" angle on the rival, arms spreading, the giant jet towering behind (no tables)
  '15': (S) => {
    const jet = hangarSet(S, RIVAL);
    scaffold(S, 7.2, -7.0, 2.2, { w: 2.6, d: 1.6 }); scaffold(S, 10.4, -7.0, 2.2, { w: 2.6, d: 1.6 });
    const rival = new Char(S, 'rival', { pos: [6, 0, -3.2], h: 2.2 });
    const crew = [41, 42].map((sd, i) => { const c = new Char(S, 'extra', { seed: 150 + i, hat: 'hardhat', pos: [i ? 10.4 : 7.2, 2.26, -7.25] }); c.set({ hold: 'hammer', facing: i ? -1 : 1 }); c.r = i; return c; });
    return (t, u) => {
      const spread = ease.back(seg(u, 0.1, 0.45));
      rival.set({ armL: lerp(0.3, 2.2, spread), armR: lerp(0.3, 2.2, spread), mouth: 'smirk', look: 0.2 });
      crew.forEach(c => c.set({ armR: 1.5 + Math.cos(t * 7 + c.r * 1.6) * 0.9 }));
      S.camMove(u, [[6.6, 0.45, 0.6], [6, 2.4, -3.2]], [[7.4, 0.6, 2.2], [7, 3.4, -8]], ease.io, [56, 62]);
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
    const fans = crowd(S, 10, [-4, 4], [33, 35], { seed: 17 });
    confetti(S, 350, [16, 12, 6], [0, 0, 31]);
    return (t, u) => {
      const x = lerp(-30, 55, ease.in(u) * 0.4 + u * 0.6), climb = Math.max(0, x + 5) * 0.2;
      jet.position.set(x, jet.userData.groundY + climb, 0); jet.rotation.z = Math.min(0.22, climb * 0.025);
      jet.userData.gear.visible = climb < 6;
      S.shadowFocus(x, 0, 0);
      fans.forEach(c => cheer(c, t));
      S.camAt([lerp(-1.5, 1.5, u), 2.2, 41], [x * 0.18, lerp(2.4, 3.6, ease.io(u)), 0], 56);
    };
  },
  // Their passengers love it.
  '18': (S) => {
    S.sky({ hemi: 1.1, fog: null, sun: [0, 40, 20], shadow: 15 });
    cabin(S, { windows: 'square' });
    const pax = [];
    for (let i = 0; i < 9; i++) {
      const x = -14 + i * 2.4 + 0.15;
      const c = new Char(S, 'extra', { seed: 180 + i, pos: [x, 0.2, -1.55], h: 1.7, shadow: false });
      c.set({ sit: true, facing: -1, look: -0.6 }); c.r = i; pax.push(c);
    }
    return (t, u) => {
      pax.forEach(c => c.set({ eyes: 'happy', mouth: 'grin', armL: c.r % 3 === 0 ? 2.4 + Math.sin(t * 9 + c.r) * 0.3 : 0.3, armR: c.r % 3 === 1 ? 1.9 : 0.3 }));
      S.camMove(u, [[7, 2.7, 0.25], [-1, 1.45, -1.7]], [[2.5, 2.6, 0.25], [-6, 1.45, -1.7]], ease.io, [60, 60]);
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
    const hero = new Char(S, 'hero', { pos: [-4.5, 0, -5.9] }); hero.set({ eyes: 'dot', mouth: 'flat', brow: -0.6, armL: 0.6, armR: 0.6 });
    const tw = tumbleweed(S); tw.scale.setScalar(1.6);
    S.shadowFocus(0, 0, -2);
    return (t, u) => {
      line.forEach((c, i) => c.set({ walking: Math.sin(t * 3 + i) > 0.6 ? 0.5 : 0, walk: t * 8 }));
      tw.position.set(lerp(1, -9, u), 1.0 + Math.abs(Math.sin(t * 6)) * 0.5, -4.6); tw.rotation.z = t * 5;
      S.camMove(u, [[7.5, 4.0, 13], [4.5, 1.8, -2]], [[-3.2, 2.3, 2.0], [-4.5, 1.4, -6.0]], ease.io, [54, 54]);
    };
  },
  // Then, one day at thirty thousand feet,
  '23': (S) => {
    S.sky({ top: '#1f5fd6', horizon: '#cfe6ff', bottom: '#8fbbe8', sun: [-60, 60, 30], sunColor: 0xffffff, fog: [300, 1200], hemi: 1.2, shadow: 40, ground: 0xbcd4ee });
    const jet = makeJet({ ...RIVAL, gear: false }); S.add(jet);
    const R = rng(23), clouds = [];
    for (let i = 0; i < 40; i++) clouds.push([S.cloud([(R() - .5) * 600, -30 - R() * 25, (R() - .5) * 500], 2 + R() * 3, 230 + i), R()]);
    for (let i = 0; i < 8; i++) clouds.push([S.cloud([(R() - .5) * 300, -4 + R() * 10, -40 - R() * 60], 1 + R(), 300 + i), R()]);
    return (t, u) => {
      clouds.forEach(([c, r]) => { c.position.x -= 1.4 + r * 0.6; if (c.position.x < -320) c.position.x += 640; });
      jet.position.y = Math.sin(t * 1.3) * 0.3; jet.rotation.x = Math.sin(t * 0.9) * 0.03;
      S.shadowFocus(0, 0, 0);
      S.camOrbit(u, [3, -1, 0], 19, 0.5, -0.1, 2.0, ease.io, 50);
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
