// animation.js - <Title>. One function per [NN] shot in script.txt.
// Shot fn gets the stage S (build the set once) and returns update(t, u):
//   t = seconds into the shot, u = 0..1 progress through it (time actions with u + seg()).
import { THREE, ease, seg, lerp, clamp, lerp3, rng, toon, basic, box, cyl, sphere, mesh, textPlane, canvasTex, noiseTex } from '/animator/engine.js';
import { Char } from '/animator/cast.js';
import { airfield, hangar, office, terminal, counter, cabin, makeJet, newspaper, confetti, tumbleweed, crackOverlay } from '/animator/props.js';

// sides (style bible colour codes): rename companies per story
const HERO_SIDE = { color: '#169e8f', name: 'HEROCO' };
const RIVAL_SIDE = { color: '#c8302e', name: 'RIVALCO' };

const DAY = { top: '#2f6fd6', horizon: '#cfe6ff', sun: [-60, 70, 50], fog: [120, 900], shadow: 60 };
const INSIDE = { hemi: 1.5, fog: null, sun: [-20, 30, 40], shadow: 15 };

function crowd(S, n, [x0, x1], [z0, z1], seed = 9, o = {}) {
  const R = rng(seed);
  return Array.from({ length: n }, (_, i) => {
    const c = new Char(S, 'extra', { seed: seed * 100 + i, h: 1.85 + R() * 0.3, ...o });
    c.pos(lerp(x0, x1, R()), 0, lerp(z0, z1, R())); c.set({ facing: R() < .5 ? 1 : -1 }); c.r = R();
    return c;
  });
}

export const shots = {
  // "<words of shot 01>"
  '01': (S) => {
    S.sky(INSIDE); office(S);
    const hero = new Char(S, 'hero', { pos: [0, 0, 0] });
    return (t, u) => {
      hero.set({ armR: lerp(0.2, 2.5, ease.back(seg(u, 0.1, 0.4))), eyes: 'half', mouth: 'smile' });
      S.camMove(u, [[0, 1.8, 6], [0, 1.4, 0]], [[0.6, 1.7, 4], [0, 1.5, 0]], ease.io, [48, 44]);
    };
  },
};
