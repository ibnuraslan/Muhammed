// Bus 2008 v3: pure 2D, scene-by-scene mirror of the reference (see plan.md)
import { cam3, P, personScale, finish, censor2D, wash, blackout } from '../../animator/flat/flat.js';
import { bust, LOOKS } from '../../animator/flat/bust.js';
import { aisle, nightView, BUS } from '../../animator/flat/bus.js';
import { Person } from '../../animator/people.js';
import { ease as EZ, lerp, clamp } from '../../animator/engine.js';
const ease = EZ.io;

export const flat = true;
const STAGE = { add() {} };
const LI_P = { skin: '#cdb59b', hair: 'short', hairColor: '#151515', top: 'tshirt', topColor: '#b7babd', pants: '#22252c', shoes: '#1a1a1c', build: 1.1 };
const TIM_P = { skin: '#e0b88f', hair: 'spiky', hairColor: '#e2c25c', top: 'tshirt', topColor: '#4f9a45', pants: '#7a5a3a', shoes: '#b3261e', headphones: true };
const seg = (t, a, b) => clamp((t - a) / (b - a));
const E = (t, a, b) => ease(seg(t, a, b));
const drawBust = (g, look, pose, x, y, k, lw = 7) => { g.save(); g.translate(x, y); g.scale(k, k); bust(g, look, pose, lw / k); g.restore(); };

export const shots = {
  // 1. HOOK: ECU of his face in the dark bus, the grin spreads, the lights fail
  '01': ({ W, H }) => (g, t, u) => {
    const gr = g.createLinearGradient(0, 0, 0, H); gr.addColorStop(0, '#2a2c31'); gr.addColorStop(1, '#17181c'); g.fillStyle = gr; g.fillRect(0, 0, W, H);
    g.fillStyle = '#3a3d44'; g.fillRect(W * 0.86, 0, 60, H);                         // out-of-focus pole
    g.save(); g.beginPath(); g.rect(-40, 140, 380, 620); g.clip(); nightView(g, -40, 140, 340, 760, 520, t, 30); g.restore();
    wash(g, W, H, '#0c0d10', 0.35);
    const k = lerp(2.7, 3.05, ease(u)), br = Math.sin(t * 2.2) * 4;
    drawBust(g, LOOKS.li, { tn: 0.06 * Math.sin(t * 0.8), tilt: -0.04 * E(t, 0, 2.5), mouth: 'grin', mouthK: lerp(0.35, 1, E(t, 0.2, 1.6)),
      socket: 1, glint: 0.5 + 0.4 * Math.sin(t * 9), brow: 1, hdy: br, underLight: 1 }, 540, 900, k);
    finish(g, W, H, t, { vig: 0.85, flick: 0.75, seed: 11 });
  },

  // 2. the aisle: Tim slumped on the left, the man walks down the aisle toward us
  '02': ({ W, H, dur }) => {
    const tim = new Person(STAGE, { ...TIM_P, headphones: false }, { seed: 2 }), li = new Person(STAGE, LI_P, { seed: 5 });
    return (g, t, u) => {
      const c = cam3({ x: 0.02, y: 1.95, z: lerp(0, 0.22, ease(u)), f: 1000, cx: 560, cy: 330 });
      const zl = lerp(5.2, 2.8, seg(t, 0, dur));
      tim.set({ seat: 1, view: 'front', turn: 0.3, tilt: -0.14, expr: 'tired', blink: true, aimLc: [268, 352], armR: [0.25, -0.4] });
      li.set({ view: 'front', walking: 1, walk: t * 5.5, expr: 'neutral', eyeShadow: 0.7 });
      aisle(g, c, t, { W, H, z0: 1.05, people: [
        { z: 1.8, draw: g2 => { const f = P(c, -0.62, 0, 1.68); tim.drawInto(g2, f[0], f[1], personScale(c, 1.68), t); } },
        { z: zl, draw: g2 => { const f = P(c, 0.05, 0, zl); li.drawInto(g2, f[0], f[1], personScale(c, zl, 1.95), t); } },
      ], sil: [{ x: 0.95, z: 5.4 }, { x: -0.98, z: 6.3 }, { x: 0.56, z: 8.1 }, { x: -0.56, z: 9.0 }] });
      wash(g, W, H, '#0b0c10', 0.22);
      finish(g, W, H, t, { vig: 0.8, flick: 0.35, seed: 4 });
    };
  },

  // 3. Tim yawns by the window, headphones on, drifts off
  '03': ({ W, H }) => (g, t, u) => {
    g.fillStyle = BUS.wall; g.fillRect(0, 0, W, H);
    g.save(); g.beginPath(); g.rect(0, 80, 860, 1150); g.clip(); nightView(g, 0, 80, 860, 1230, 760, t, 55, 7); g.restore();
    g.strokeStyle = '#8e939b'; g.lineWidth = 14; g.strokeRect(-20, 80, 880, 1150); g.strokeStyle = '#151214'; g.lineWidth = 4; g.strokeRect(-27, 73, 894, 1164);
    g.fillStyle = '#2a2c31'; g.fillRect(900, 0, 180, H); g.fillStyle = '#6f737b'; g.fillRect(880, 0, 24, H);
    wash(g, W, H, '#0b0c10', 0.18);
    const k = lerp(1.62, 1.8, ease(u)), yawn = E(t, 0.1, 0.8) * (1 - E(t, 1.6, 2.2));
    const down = E(t, 1.6, 2.4), sleep = E(t, 2.2, 3.0);
    const arm = { front: down < 0.55, sh: [-250, 400], el: [lerp(-430, -330, down), lerp(720, 950, down)], hd: [lerp(-96, -260, down), lerp(150, 1350, down)] };
    drawBust(g, LOOKS.tim, { tn: 0.22, tilt: lerp(0.04, -0.12, sleep), hdx: lerp(0, -26, sleep), hdy: lerp(0, 18, sleep),
      mouth: yawn > 0.05 ? 'yawn' : 'neutral', mouthK: yawn, eyeMode: yawn > 0.2 ? 'squeeze' : sleep > 0.6 ? 'closed' : 'open', eye: 1 - sleep * 0.9,
      browUp: yawn * 0.8, armL: arm, headphones: true }, 620, 420, k);
    finish(g, W, H, t, { vig: 0.7 });
  },
};
