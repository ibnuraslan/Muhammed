// Bus 2008 v3: pure 2D, shot-by-shot mirror of the reference (see plan.md). No gore is ever drawn.
import { cam3, P, personScale, finish, censor2D, wash, blackout, INK } from '../../animator/flat/flat.js';
import { bust, LOOKS, fist, knife, arm, shadeOf } from '../../animator/flat/bust.js';
import { aisle, nightView, BUS } from '../../animator/flat/bus.js';
import { Person } from '../../animator/people.js';
import { ease as EZ, lerp, clamp } from '../../animator/engine.js';
const ease = EZ.io;

export const flat = true;
const STAGE = { add() {} };
const LI_P = { skin: '#cdb59b', hair: 'short', hairColor: '#151515', top: 'tshirt', topColor: '#b7babd', pants: '#22252c', shoes: '#1a1a1c', build: 1.18 };
const TIM_P = { skin: '#e0b88f', hair: 'spiky', hairColor: '#e2c25c', top: 'tshirt', topColor: '#4f9a45', pants: '#7a5a3a', shoes: '#b3261e' };
const LI = { ...LOOKS.li, build: 1.12 }, TIM = LOOKS.tim;
const seg = (t, a, b) => clamp((t - a) / (b - a));
const E = (t, a, b) => ease(seg(t, a, b));
const drawBust = (g, look, pose, x, y, k, lw = 7) => { g.save(); g.translate(x, y); g.scale(k, k); bust(g, look, pose, lw / k); g.restore(); };
const inLocal = (fn, x, y, k, lw = 7) => (g) => { g.save(); g.translate(x, y); g.scale(k, k); fn(g, lw / k); g.restore(); };
// screen point -> people.js canvas point, for a Person drawn with feet at (fx,fy) and scale s
const toPC = (fx, fy, s, sx, sy) => [(sx - fx) / s + 320, (sy - fy) / s + 1255];

// a night window seen from inside: dark glass, pines, the frame bars
function windowBg(g, x0, y0, x1, y1, t, { pale = false, speed = 0 } = {}) {
  if (pale) {
    const gr = g.createLinearGradient(x0, y0, x1, y1); gr.addColorStop(0, '#8d9fab'); gr.addColorStop(1, '#a9b8c1'); g.fillStyle = gr; g.fillRect(x0, y0, x1 - x0, y1 - y0);
    g.strokeStyle = 'rgba(235,242,246,0.35)'; g.lineWidth = 26; for (const o of [0, 260]) { g.beginPath(); g.moveTo(x0 + 300 + o, y0); g.lineTo(x0 - 300 + o, y1); g.stroke(); }
    return;
  }
  nightView(g, x0, y0, x1, y1, y0 + (y1 - y0) * 0.62, t, speed, 7);
}

export const shots = {
  // 1. HOOK (ref 0:00-3.5): camera above him, huge grin; his hand brings something up to his mouth
  //    (the reference shows a heart: ours is fully covered by the CENSORED badge). Fade to black.
  '01': ({ W, H, dur }) => (g, t, u) => {
    const tt = t * 3.5 / dur;
    const gr = g.createLinearGradient(0, 0, 0, H); gr.addColorStop(0, '#34363b'); gr.addColorStop(1, '#4a4c51'); g.fillStyle = gr; g.fillRect(0, 0, W, H);
    const bite = E(tt, 1.5, 1.9) * (1 - E(tt, 2.4, 2.9)), k = lerp(2.85, 3.1, ease(u));
    drawBust(g, LI, { pitch: 1, mouth: 'grin', mouthK: lerp(0.85, 1, E(tt, 0, 1.2)), socket: 1, brow: 0.6, hdy: 8 * bite + Math.sin(tt * 2.5) * 4,
      tilt: -0.03 + 0.03 * Math.sin(tt * 1.3) }, 540, 640, k, 8);
    // the hand rises from the bottom to the mouth, then pushes in ("bite")
    const rise = E(tt, 0.25, 1.4), hx = lerp(300, 400, rise) + 20 * bite, hy = lerp(2250, 1480, rise) - 40 * bite;
    g.save(); g.translate(hx, hy); g.scale(3.4, 3.4); fist(g, [0, 0], -1.05, LI.skin, 8 / 3.4, true); g.restore();
    censor2D(g, hx + 150, hy - 200, 165, seg(tt, 0.35, 2.6) > 0 ? Math.max(0.16, seg(tt, 0.35, 0.6)) : 0);
    finish(g, W, H, t, { vig: 0.8, flick: 0.2, seed: 11 });
    wash(g, W, H, '#000', E(tt, 2.85, 3.45));
  },

  // 2. AISLE (ref 3.5-9.8): Tim asleep-ish in the WINDOW seat (left), head on his fist, the AISLE seat
  //    beside him EMPTY. The man walks down the aisle toward us and stops at Tim's row, hands on the seat back.
  '02': ({ W, H, dur }) => {
    const tim = new Person(STAGE, TIM_P, { seed: 2 }), li = new Person(STAGE, LI_P, { seed: 5 });
    return (g, t, u) => {
      const tt = t * 6.3 / dur;
      const c = cam3({ x: -0.38, y: 2.05, z: lerp(-0.3, -0.12, ease(u)), f: 1150, cx: 540, cy: 270 });
      const walk = seg(tt, 0, 4.9), zl = lerp(7.4, 1.98, ease(walk) * 0.25 + walk * 0.75), stop = E(tt, 4.7, 5.5);
      const fT = P(c, -1.0, 0, 1.72), sT = personScale(c, 1.72, 1.82);
      tim.set({ seat: 1, view: 'front', turn: 0.35, tilt: -0.2, expr: 'tired', blink: true, aimLc: toPC(fT[0], fT[1], sT, ...P(c, -1.15, 1.25, 1.8).slice(0, 2)),
        armR: [0.3, -0.5] });
      const fL = P(c, -0.12, 0, zl), sL = personScale(c, zl, 1.92);
      const hands = stop > 0 ? { aimLc: toPC(fL[0], fL[1], sL, ...P(c, -0.38, lerp(0.85, 1.22, stop), 2.06).slice(0, 2)) } : { aimLc: null, aimRc: null };
      li.set({ view: 'front', walking: 1 - stop, walk: tt * 5.2, expr: 'neutral', eyeShadow: 0.85, turn: -0.35 * stop, ...hands });
      aisle(g, c, t, { W, H, z0: 1.12, skip: (i, xc) => i === 0 && xc === -1.0, people: [
        { z: 1.86, draw: g2 => {
          tim.drawInto(g2, fT[0], fT[1], sT, t);
          const hp = P(c, -1.12, 1.24, 1.8);         // fist against his temple, drawn over the head
          g2.save(); g2.translate(hp[0], hp[1]); g2.scale(sT * 0.75, sT * 0.75); fist(g2, [0, 0], -1.9, TIM.skin, 4 / (sT * 0.75)); g2.restore();
        } },
        { z: zl - 0.2, draw: g2 => li.drawInto(g2, fL[0], fL[1], sL, t) },
      ], sil: [{ x: -0.56, z: 2.98 }, { x: 0.98, z: 4.8 }, { x: -1.0, z: 6.6 }, { x: 0.56, z: 8.4 }] });
      wash(g, W, H, '#0b0c10', 0.25);
      finish(g, W, H, t, { vig: 0.8, flick: 0.25, seed: 4 });
    };
  },

  // 3. Tim (ref 10.0-12.3): three-quarter to the left, chin on his fist, elbow on the sill, window behind.
  //    Half asleep -> yawns -> mouth closes, eyes stay shut: he nods off on his hand.
  '03': ({ W, H, dur }) => (g, t, u) => {
    const tt = t * 2.5 / dur;
    g.fillStyle = BUS.wall; g.fillRect(0, 0, W, H);
    nightView(g, 0, 0, 1000, 1300, 1100, t, 25, 7, 2.5);
    g.fillStyle = '#8e939b'; g.fillRect(960, 0, 40, 1300); g.strokeStyle = INK; g.lineWidth = 4; g.strokeRect(960, -5, 40, 1305);
    g.fillStyle = '#5d6168'; g.fillRect(0, 1300, W, 34); g.strokeRect(-5, 1300, W + 10, 34);     // sill
    g.fillStyle = '#2c2e33'; g.fillRect(0, 1334, W, H);
    wash(g, W, H, '#0b0c10', 0.2);
    const yawn = E(tt, 0.55, 1.0) * (1 - E(tt, 1.55, 1.95)), doze = E(tt, 1.7, 2.4), k = lerp(1.55, 1.68, ease(u));
    const nod = doze * 14 + Math.sin(tt * 2) * 3;
    drawBust(g, TIM, { tn: -0.62, tilt: 0.1 + 0.04 * doze, hdy: nod, hdx: -6 * doze, light: -1,
      mouth: yawn > 0.04 ? 'yawn' : 'neutral', mouthK: yawn, eyeMode: yawn > 0.3 ? 'squeeze' : (tt > 1.5 ? 'closed' : 'open'), eye: 0.42, browUp: 0.3 * yawn,
      armL: { front: true, sh: [-240, 410], el: [-470, 830], hd: [-112, 236 + nod] } }, 610, 470, k);
    finish(g, W, H, t, { vig: 0.7 });
  },

  // 4. (ref 12.5-14.3) low side angle: Tim fully asleep, head slumped on the seat back; slow pan right...
  '04': ({ W, H, dur }) => (g, t, u) => seatPan(g, W, H, t, lerp(0, 380, ease(u) * 0.8 + u * 0.2), 0),
  // 5. (ref 14.5-17.0) ...the pan reveals the man sitting next to him. He turns to us, grins, pulls a knife.
  '05': ({ W, H, dur }) => (g, t, u) => { const tt = t * 2.6 / dur; seatPan(g, W, H, t, lerp(380, 1060, E(tt, 0, 1.0)), tt); },

  // 6. (ref 17.0-19.8) Tim's side by the pale window: the man's arm comes in and raises the knife over him;
  //    Tim's eyes snap open -> hard cut to black + CENSORED badge (no wound, nothing shown).
  '06': ({ W, H, dur }) => (g, t, u) => {
    const tt = t * 2.8 / dur;
    if (tt > 2.05) { blackout(g, W, H); censor2D(g, W / 2, H * 0.45, 230, seg(tt, 2.08, 2.8) || 0.01); finish(g, W, H, t, { vig: 0.5 }); return; }
    windowBg(g, 0, 0, W, 1400, t, { pale: true });
    g.fillStyle = '#6d727a'; g.fillRect(0, 1400, W, 44); g.strokeStyle = INK; g.lineWidth = 4; g.strokeRect(-5, 1400, W + 10, 44);
    g.fillStyle = '#34363c'; g.fillRect(0, 1444, W, H);
    const wake = E(tt, 1.45, 1.6), k = lerp(1.5, 1.62, ease(u)) + 0.08 * wake;
    drawBust(g, TIM, { tn: -0.38, tilt: lerp(-0.22, -0.05, wake), hdy: -20 * wake, light: -1,
      eyeMode: wake > 0.3 ? 'open' : 'closed', eye: 1.15, look: -0.6, lookY: -0.8, mouth: wake > 0.3 ? 'scared' : 'neutral', mouthK: wake, brow: -0.6 * wake, browUp: wake,
      armL: { front: true, sh: [-240, 410], el: [-430, 900], hd: [lerp(-120, -170, wake), lerp(170, 300, wake)] } }, 700, 860, k);
    // the man's arm enters from the bottom left and raises the knife high
    const up = E(tt, 0.35, 1.2), down = E(tt, 1.75, 2.05);
    const hd = [lerp(-80, 330, up) + 120 * down, lerp(2100, 470, up) + 260 * down], el = [lerp(-260, 120, up), lerp(2300, 1250, up)];
    inLocal((g2, lw) => { const h2 = [hd[0] / 1.6, hd[1] / 1.6], e2 = [el[0] / 1.6, el[1] / 1.6]; arm(g2, { sh: [-260, 1600], el: e2, hd: h2, fist: true }, LI, lw); knife(g2, h2[0] + 6, h2[1] + 12, lerp(-0.6, 0.9, up) + 0.5 * down, 300, lw); fist(g2, h2, Math.atan2(h2[1] - e2[1], h2[0] - e2[0]), LI.skin, lw); }, 0, 0, 1.6)(g);
    finish(g, W, H, t, { vig: 0.65, desat: 0.4 });
    if (tt > 1.98) wash(g, W, H, '#fff', 0.25);
  },
};

// shots 4-5 share one wide picture, panned left -> right
function seatPan(g, W, H, t, ox, tt) {
  g.save(); g.translate(-ox, 0);
  const WW = W + 1100;
  g.fillStyle = '#383a40'; g.fillRect(0, 0, WW, H);
  // pale window band along the top with bars
  windowBg(g, 0, 0, WW, 360, t, { pale: true });
  g.fillStyle = '#5d6168'; for (let x = 60; x < WW; x += 300) { g.fillRect(x, 0, 30, 360); g.strokeStyle = INK; g.lineWidth = 3; g.strokeRect(x, -5, 30, 365); }
  g.fillRect(0, 352, WW, 24); g.strokeRect(-5, 352, WW + 10, 24);
  // seat backs of the rows ahead (two depths)
  const sb = (x, y, w, h, c = BUS.seat) => { g.beginPath(); g.moveTo(x, y + h); g.lineTo(x, y + w * 0.3); g.quadraticCurveTo(x, y, x + w * 0.3, y); g.lineTo(x + w * 0.7, y); g.quadraticCurveTo(x + w, y, x + w, y + w * 0.3); g.lineTo(x + w, y + h); g.closePath();
    g.fillStyle = c; g.fill(); g.strokeStyle = INK; g.lineWidth = 7; g.stroke(); g.strokeStyle = BUS.seatRim; g.lineWidth = 4; g.stroke(); };
  for (let x = -40; x < WW; x += 210) sb(x, 420, 170, 400);
  for (let x = 30; x < WW; x += 330) sb(x, 560, 280, 600, '#1a1e2c');
  wash(g, WW, H, '#0b0c10', 0.15);
  // Tim slumped against the seat back on the left, asleep
  drawBust(g, TIM, { tn: -0.25, tilt: 0.42, hdx: -10, hdy: 20 + Math.sin(t * 1.6) * 3, eyeMode: 'closed', eye: 0, mouth: 'neutral', light: 1, headphones: true }, 290, 1330, 1.35);
  // the man next to him
  const turn = E(tt, 0.9, 1.5), grin = E(tt, 1.2, 1.9), kn = E(tt, 1.5, 2.3);
  const hd = [lerp(170, 110, kn), lerp(1150, 560, kn)];
  drawBust(g, LI, { tn: lerp(-0.7, -0.15, turn), tilt: lerp(0.05, -0.06, turn), look: lerp(-1, 0.2, turn), eye: 1.1, socket: 0.25, brow: 0.5,
    mouth: grin > 0.05 ? 'grin' : 'neutral', mouthK: grin * 0.75, smirk: 0.6, sweat: 0,
    armR: kn > 0 ? { front: true, sh: [250, 400], el: [lerp(330, 330, kn), lerp(1000, 900, kn)], hd } : null }, 1560, 760, 1.32);
  if (kn > 0) {     // blade up out of the fist: knife first, then the fist again on top of the handle
    const el = [lerp(330, 330, kn), lerp(1000, 900, kn)];
    inLocal((g2, lw) => { knife(g2, hd[0], hd[1] + 20, -1.68, 380, lw); fist(g2, hd, Math.atan2(hd[1] - el[1], hd[0] - el[0]), LI.skin, lw); }, 1560, 760, 1.32)(g);
  }
  g.restore();
  finish(g, W, H, t, { vig: 0.75 });
}
