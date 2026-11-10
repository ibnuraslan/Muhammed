// Bus 2008 v3: pure 2D, shot-by-shot copy of the reference (see plan.md): same framing, staging, action, blood.
// Only the victim's body parts are never drawn (kept out of frame / covered).
import { cam3, P, personScale, finish, censor2D, wash, blackout, INK } from '../../animator/flat/flat.js';
import { bust, LOOKS, fist, knife, bloodyKnife, arm, grip, palm, backView, splat, smear, shadeOf } from '../../animator/flat/bust.js';
import { aisle, nightView, BUS } from '../../animator/flat/bus.js';
import { busExterior, city, nightSky, interrogation, lightCone, table, evidenceBag } from '../../animator/flat/scenes.js';
import { Person } from '../../animator/people.js';
import { ease as EZ, lerp, clamp } from '../../animator/engine.js';
const ease = EZ.io;

export const flat = true;
const STAGE = { add() {} };
const LI_P = { skin: '#cdb59b', hair: 'short', hairColor: '#151515', top: 'tshirt', topColor: '#b7babd', pants: '#22252c', shoes: '#1a1a1c', build: 1.18 };
const TIM_P = { skin: '#e0b88f', hair: 'spiky', hairColor: '#e2c25c', top: 'tshirt', topColor: '#4f9a45', pants: '#7a5a3a', shoes: '#b3261e' };
const LI = { ...LOOKS.li, build: 1.12 }, TIM = LOOKS.tim;
const DENIM = { skin: '#b98a63', hair: 'messy', hairColor: '#1e1a18', shirt: '#4a5f7c', collar: '#3c4d66', top: 'denim', eyes: '#3a2a20', lines: 0.6, jaw: 1.05 };
const HOODIE = { skin: '#e2b896', hair: 'messy', hairColor: '#8a5d36', shirt: '#2f3036', collar: '#2f3036', top: 'hoodie', eyes: '#5a4632', lines: 0 };
const BLONDE = { skin: '#ecc7a8', hair: 'bun', hairColor: '#e3c97f', shirt: '#a8302c', collar: '#a8302c', top: 'polo', eyes: '#4a6a8a', fem: true, jaw: 0.9, lines: 0 };
const COP = { skin: '#d6ab86', hair: 'flat', hairColor: '#2a2018', shirt: '#1d2a44', collar: '#1d2a44', top: 'uniform', hat: 'cap', eyes: '#3a2a20', jaw: 1.05, lines: 0.6 };
const seg = (t, a, b) => clamp((t - a) / (b - a));
const E = (t, a, b) => ease(seg(t, a, b));
const drawBust = (g, look, pose, x, y, k, lw = 7) => { g.save(); g.translate(x, y); g.scale(k, k); bust(g, look, pose, lw / k); g.restore(); };
const inLocal = (fn, x, y, k, lw = 7) => (g) => { g.save(); g.translate(x, y); g.scale(k, k); fn(g, lw / k); g.restore(); };
const toPC = (fx, fy, s, sx, sy) => [(sx - fx) / s + 320, (sy - fy) / s + 1255];
const N = (dur, nominal) => (t) => t * nominal / dur;           // shot time scaled to the reference timing

// bus interior seen at seat level: pale window band with bars, rows of seat backs
function seatsBg(g, W, H, t, { winY = 360, rows = true } = {}) {
  g.fillStyle = '#383a40'; g.fillRect(0, 0, W, H);
  paleWindow(g, W, winY);
  g.fillStyle = '#5d6168'; g.strokeStyle = INK; g.lineWidth = 3;
  for (let x = 60; x < W; x += 300) { g.fillRect(x, 0, 30, winY); g.strokeRect(x, -5, 30, winY + 5); }
  g.fillRect(0, winY - 8, W, 24); g.strokeRect(-5, winY - 8, W + 10, 24);
  if (rows) { for (let x = -40; x < W; x += 210) seatBack(g, x, winY + 60, 170, 400); for (let x = 30; x < W; x += 330) seatBack(g, x, winY + 200, 280, 600, '#1a1e2c'); }
}
function seatBack(g, x, y, w, h, c = BUS.seat) {
  g.beginPath(); g.moveTo(x, y + h); g.lineTo(x, y + w * 0.3); g.quadraticCurveTo(x, y, x + w * 0.3, y); g.lineTo(x + w * 0.7, y); g.quadraticCurveTo(x + w, y, x + w, y + w * 0.3); g.lineTo(x + w, y + h); g.closePath();
  g.fillStyle = c; g.fill(); g.strokeStyle = INK; g.lineWidth = 7; g.stroke(); g.strokeStyle = BUS.seatRim; g.lineWidth = 4; g.stroke();
}
function paleWindow(g, W, y1) {
  const gr = g.createLinearGradient(0, 0, W, y1); gr.addColorStop(0, '#8d9fab'); gr.addColorStop(1, '#a9b8c1'); g.fillStyle = gr; g.fillRect(0, 0, W, y1);
  g.strokeStyle = 'rgba(235,242,246,0.35)'; g.lineWidth = 26; for (const o of [0, 260]) { g.beginPath(); g.moveTo(300 + o, 0); g.lineTo(-300 + o, y1); g.stroke(); }
}

// ------------------------------------------------------------------------------------------------ shots
function hook({ W, H, dur }) {
  const T = N(dur, 3.5);
  return (g, t, u) => {
    const tt = T(t);
    const gr = g.createLinearGradient(0, 0, 0, H); gr.addColorStop(0, '#34363b'); gr.addColorStop(1, '#4a4c51'); g.fillStyle = gr; g.fillRect(0, 0, W, H);
    const bite = E(tt, 1.4, 1.8) * (1 - E(tt, 2.3, 2.8)), k = lerp(2.95, 3.2, ease(u));
    drawBust(g, LI, { pitch: 1, mouth: 'grin', mouthK: lerp(0.8, 1, E(tt, 0, 1.2)) - 0.25 * bite, socket: 1, brow: 0.6, blood: 1, hdy: 10 * bite + Math.sin(tt * 2.5) * 4,
      tilt: -0.03 + 0.03 * Math.sin(tt * 1.3) }, 540, 640, k, 8);
    // his hand comes up from the bottom gripping it, to his mouth (what he holds is covered)
    const rise = E(tt, 0.2, 1.3), hx = lerp(330, 430, rise) + 20 * bite, hy = lerp(2350, 1500, rise) - 50 * bite;
    smear(g, hx + 130, hy - 110, 120, 1, 21, 2.5);
    grip(g, hx, hy, -1.25, LI.skin, 8 / 2.6, 2.6);
    smear(g, hx + 30, hy - 160, 140, 0.9, 17, 1.6);
    censor2D(g, hx + 120, hy - 300, 175, seg(tt, 0.75, 2.9) > 0 ? Math.max(0.16, seg(tt, 0.75, 0.9)) : 0);
    finish(g, W, H, t, { vig: 0.8, flick: 0.2, seed: 11 });
    wash(g, W, H, '#000', E(tt, 2.95, 3.5));
  };
}

function seatPan(g, W, H, t, ox, tt) {
  g.save(); g.translate(-ox, 0);
  const WW = W + 1100;
  g.fillStyle = '#383a40'; g.fillRect(0, 0, WW, H);
  paleWindow(g, WW, 360);
  g.fillStyle = '#5d6168'; g.strokeStyle = INK; g.lineWidth = 3; for (let x = 60; x < WW; x += 300) { g.fillRect(x, 0, 30, 360); g.strokeRect(x, -5, 30, 365); }
  g.fillRect(0, 352, WW, 24); g.strokeRect(-5, 352, WW + 10, 24);
  for (let x = -40; x < WW; x += 210) seatBack(g, x, 420, 170, 400);
  for (let x = 30; x < WW; x += 330) seatBack(g, x, 560, 280, 600, '#1a1e2c');
  wash(g, WW, H, '#0b0c10', 0.15);
  drawBust(g, TIM, { tn: -0.25, tilt: 0.42, hdx: -10, hdy: 20 + Math.sin(t * 1.6) * 3, eyeMode: 'closed', eye: 0, mouth: 'neutral', light: 1, headphones: true }, 290, 1330, 1.35);
  const turn = E(tt, 0.9, 1.5), grin = E(tt, 1.2, 1.9), kn = E(tt, 1.5, 2.3);
  const hd = [lerp(170, 110, kn), lerp(1150, 560, kn)], el = [330, lerp(1000, 900, kn)];
  drawBust(g, LI, { tn: lerp(-0.7, -0.15, turn), tilt: lerp(0.05, -0.06, turn), look: lerp(-1, 0.2, turn), eye: 1.1, iris: 0.8, socket: 0.25, brow: 0.5,
    mouth: grin > 0.05 ? 'grin' : 'neutral', mouthK: grin * 0.75, smirk: 0.6,
    armR: kn > 0 ? { front: true, sh: [250, 400], el, hd } : null }, 1560, 760, 1.32);
  if (kn > 0) inLocal((g2, lw) => { knife(g2, hd[0], hd[1] + 20, -1.68, 380, lw); fist(g2, hd, Math.atan2(hd[1] - el[1], hd[0] - el[0]), LI.skin, lw); }, 1560, 760, 1.32)(g);
  g.restore();
  finish(g, W, H, t, { vig: 0.75 });
}

// passengers outside, city lights behind
function outside(g, W, H, t, u, { woman = 0 } = {}) {
  nightSky(g, W, H, H * 0.5, t);
  city(g, 0, H * 0.22, W, H * 0.62, 8);
  g.fillStyle = '#2a2a1e'; g.fillRect(0, H * 0.62, W, H);
  wash(g, W, H, '#05070f', 0.25);
  const k = lerp(1.25, 1.36, ease(u)), sh = Math.sin(t * 17) * 2;
  drawBust(g, HOODIE, { tn: 0.15, eye: 1.25, iris: 0.6, browUp: 1, mouth: 'scared', mouthK: 0.55, look: 0.1 }, 300 + sh, 1180, k);
  const hand = woman ? E(t, 0.4, 1.1) : 0;
  drawBust(g, BLONDE, { tn: -0.15, eye: 1.2, iris: 0.6, browUp: 1, brow: -0.4, mouth: 'scared', mouthK: 0.7 - 0.5 * hand, tears: woman ? E(t, 0.8, 2.5) : 0,
    armR: hand > 0 ? { front: true, sh: [250, 410], el: [300, 900], hd: [lerp(200, 30, hand), lerp(800, 190, hand)] } : null }, 790 - sh, 1250, k * 1.02);
  finish(g, W, H, t, { vig: 0.7 });
}

function hunchedBack(g, W, H, t, u, dark = 0) {
  paleWindow(g, W, 900); g.fillStyle = '#383a40'; g.fillRect(0, 900, W, H);
  seatBack(g, 140, 640, 800, 900, '#1a1e2c');
  splat(g, 330, 380, 170, 1, 3); splat(g, 720, 300, 140, 1, 5); smear(g, 560, 650, 380, 1, 9, 2.4); splat(g, 520, 560, 220, 0.9, 12);
  const k = lerp(1.55, 1.68, ease(u)), mv = Math.sin(t * 5) * 6;
  inLocal((g2, lw) => backView(g2, { ...LI, build: 1.2 }, { hunch: 1 }, lw), 540 + mv, 1180 + Math.abs(mv), k)(g);
  if (dark) wash(g, W, H, '#000', 0.25);
  finish(g, W, H, t, { vig: 0.8, flick: 0.4, seed: 21 });
}

export const shots = {
  // 1 (ref 0:00-3.5) camera above him, bloody grin, he brings it up to his mouth and bites. Fade to black.
  '01': hook,

  // 2 (ref 3.5-9.8) Tim in the WINDOW seat, head on his fist; the aisle seat beside him empty. The man walks
  //   down the aisle and stops right behind that empty seat, hands on its back.
  '02': ({ W, H, dur }) => {
    const tim = new Person(STAGE, TIM_P, { seed: 2 }), li = new Person(STAGE, LI_P, { seed: 5 }), T = N(dur, 6.3);
    return (g, t, u) => {
      const tt = T(t);
      const c = cam3({ x: -0.62, y: 1.72, z: lerp(0.0, 0.12, ease(u)), f: 1100, cx: 540, cy: 330 });
      const walk = seg(tt, 0, 4.8), zl = lerp(7.6, 2.32, ease(walk) * 0.3 + walk * 0.7), stop = E(tt, 4.6, 5.3);
      const fT = P(c, -1.0, 0, 1.72), sT = personScale(c, 1.72, 1.82);
      tim.set({ seat: 1, view: 'front', turn: 0.35, tilt: -0.2, expr: 'tired', blink: true, aimLc: toPC(fT[0], fT[1], sT, ...P(c, -1.15, 1.25, 1.78).slice(0, 2)), armR: [0.3, -0.5] });
      const fL = P(c, -0.14, 0, zl), sL = personScale(c, zl, 1.92);
      const hands = stop > 0 ? { aimLc: toPC(fL[0], fL[1], sL, ...P(c, -0.62, lerp(0.95, 1.27, stop), 2.0).slice(0, 2)), aimRc: toPC(fL[0], fL[1], sL, ...P(c, -0.38, lerp(0.95, 1.27, stop), 2.0).slice(0, 2)) } : { aimLc: null, aimRc: null };
      li.set({ view: 'front', walking: 1 - stop, walk: tt * 5.2, expr: 'neutral', eyeShadow: 0.85, turn: -0.3 * stop, tilt: 0.12 * stop, ...hands });
      aisle(g, c, t, { W, H, z0: 1.08, skip: (i, xc) => i === 0 && xc === -1.0, people: [
        { z: 1.86, draw: g2 => {
          tim.drawInto(g2, fT[0], fT[1], sT, t);
          const hp = P(c, -1.12, 1.24, 1.78);
          g2.save(); g2.translate(hp[0], hp[1]); g2.scale(sT * 0.75, sT * 0.75); fist(g2, [0, 0], -1.9, TIM.skin, 4 / (sT * 0.75)); g2.restore();
        } },
        { z: zl, draw: g2 => li.drawInto(g2, fL[0], fL[1], sL, t) },
      ], sil: [{ x: 0.98, z: 3.8 }, { x: -1.0, z: 4.8 }, { x: 0.56, z: 6.6 }, { x: -0.56, z: 8.4 }] });
      wash(g, W, H, '#0b0c10', 0.25);
      finish(g, W, H, t, { vig: 0.8, flick: 0.25, seed: 4 });
    };
  },

  // 3 (ref 10.0-12.3) Tim three-quarter, chin on his fist, elbow on the sill: half asleep -> yawn -> nods off
  '03': ({ W, H, dur }) => { const T = N(dur, 2.5); return (g, t, u) => {
    const tt = T(t);
    g.fillStyle = BUS.wall; g.fillRect(0, 0, W, H);
    nightView(g, 0, 0, 1000, 1300, 1100, t, 25, 7, 2.5);
    g.fillStyle = '#8e939b'; g.fillRect(960, 0, 40, 1300); g.strokeStyle = INK; g.lineWidth = 4; g.strokeRect(960, -5, 40, 1305);
    g.fillStyle = '#5d6168'; g.fillRect(0, 1300, W, 34); g.strokeRect(-5, 1300, W + 10, 34);
    g.fillStyle = '#2c2e33'; g.fillRect(0, 1334, W, H);
    wash(g, W, H, '#0b0c10', 0.2);
    const yawn = E(tt, 0.55, 1.0) * (1 - E(tt, 1.55, 1.95)), doze = E(tt, 1.7, 2.4), k = lerp(1.55, 1.68, ease(u));
    const nod = doze * 14 + Math.sin(tt * 2) * 3;
    drawBust(g, TIM, { tn: -0.62, tilt: 0.1 + 0.04 * doze, hdy: nod, hdx: -6 * doze, light: -1,
      mouth: yawn > 0.04 ? 'yawn' : 'neutral', mouthK: yawn, eyeMode: yawn > 0.3 ? 'squeeze' : (tt > 1.5 ? 'closed' : 'open'), eye: 0.42, browUp: 0.3 * yawn,
      armL: { front: true, sh: [-240, 410], el: [-470, 830], hd: [-112, 236 + nod] } }, 610, 470, k);
    finish(g, W, H, t, { vig: 0.7 });
  }; },

  // 4 (ref 12.5-14.3) Tim asleep, slumped on the seat back; slow pan right...
  '04': ({ W, H }) => (g, t, u) => seatPan(g, W, H, t, lerp(0, 380, ease(u) * 0.8 + u * 0.2), 0),
  // 5 (ref 14.5-17.0) ...the man sitting next to him turns to us, grins, pulls out a big knife
  '05': ({ W, H, dur }) => { const T = N(dur, 2.6); return (g, t, u) => { const tt = T(t); seatPan(g, W, H, t, lerp(380, 1060, E(tt, 0, 1.0)), tt); }; },

  // 6 (ref 17.0-19.8) by the pale window: his arm raises the knife over sleeping Tim, Tim's eyes snap open, the stab,
  //   blood sprays the window, Tim screams
  '06': ({ W, H, dur }) => { const T = N(dur, 2.8); return (g, t, u) => {
    const tt = T(t), hit = tt > 1.95;
    paleWindow(g, W, 1400);
    g.fillStyle = '#6d727a'; g.fillRect(0, 1400, W, 44); g.strokeStyle = INK; g.lineWidth = 4; g.strokeRect(-5, 1400, W + 10, 44);
    g.fillStyle = '#34363c'; g.fillRect(0, 1444, W, H);
    if (hit) { splat(g, 300, 520, 260, 1, 31); splat(g, 520, 300, 180, 1, 33); smear(g, 380, 700, 300, 1, 35, 2); splat(g, 200, 900, 160, 0.9, 37); }
    const wake = E(tt, 1.45, 1.6), k = lerp(1.45, 1.55, ease(u)) + 0.06 * wake, jolt = hit ? Math.sin(tt * 60) * 8 * (1 - seg(tt, 1.95, 2.4)) : 0;
    drawBust(g, TIM, { tn: -0.38, tilt: lerp(-0.22, -0.05, wake), hdy: -20 * wake, hdx: jolt, light: -1,
      eyeMode: wake > 0.3 ? 'open' : 'closed', eye: 1.2, iris: 0.6, look: -0.6, lookY: -0.8, mouth: wake > 0.3 ? 'scared' : 'neutral', mouthK: hit ? 1 : wake * 0.6, brow: -0.6 * wake, browUp: wake,
      shirtBlood: hit ? 1 : 0,
      armL: { front: true, sh: [-240, 410], el: [-430, 900], hd: [lerp(-120, -170, wake), lerp(170, 300, wake)] } }, 720 + jolt, 900, k);
    if (hit) inLocal((g2, lw) => { smear(g2, -60, 260, 90, 1, 41, 3); splat(g2, -40, 300, 120, 1, 43); }, 720, 900, k)(g);       // blood running down his neck
    // the man's big arm from the bottom left, knife high above Tim's head, then down
    const up = E(tt, 0.35, 1.2), down = E(tt, 1.75, 1.95), back = E(tt, 2.1, 2.6);
    const hd = [lerp(-80, 240, up) + 120 * down - 160 * back, lerp(2100, 380, up) + 560 * down - 360 * back], el = [lerp(-260, 20, up), lerp(2300, 1250, up) + 200 * down];
    inLocal((g2, lw) => { const h2 = [hd[0] / 1.6, hd[1] / 1.6], e2 = [el[0] / 1.6, el[1] / 1.6];
      arm(g2, { sh: [-160, 1500], el: e2, hd: h2, fist: true }, LI, lw); bloodyKnife(g2, h2[0] + 6, h2[1] + 12, lerp(-0.6, 0.35, up) + 0.9 * down, 300, lw, hit ? 1 : 0);
      fist(g2, h2, Math.atan2(h2[1] - e2[1], h2[0] - e2[0]), LI.skin, lw); }, 0, 0, 1.6)(g);
    finish(g, W, H, t, { vig: 0.65, desat: 0.4 });
    if (tt > 1.93 && tt < 2.02) wash(g, W, H, '#fff', 0.5);
  }; },

  // 7 (ref 20.0-22.3) exterior: the bus stopped on the shoulder at night, street lamps
  '07': ({ W, H }) => (g, t, u) => {
    busExterior(g, W, H, cam3({ x: 0.8 + u * 0.4, y: 7.5, z: 8 + u * 1.5, f: 900, cx: 540, cy: 620 }), t);
    finish(g, W, H, t, { vig: 0.75 });
  },

  // 8 (ref 22.5-25.2) inside: terrified passengers crowd and push for the door, pan right
  '08': ({ W, H }) => (g, t, u) => {
    const ox = lerp(0, 380, ease(u));
    g.fillStyle = '#383a40'; g.fillRect(0, 0, W, H); paleWindow(g, W, 700);
    g.save(); g.translate(-ox, 0);
    inLocal((g2, lw) => backView(g2, { skin: '#c9a080', hairColor: '#151515', shirt: '#2a2a30' }, {}, lw), 1150, 860, 1.25)(g);
    const sh = Math.sin(t * 15) * 4;
    drawBust(g, DENIM, { tn: 0.3, eye: 1.2, iris: 0.6, brow: 0.2, browUp: 0.8, mouth: 'scared', mouthK: 0.4, look: 0.8, sweat: 1 }, 240 + sh, 760, 1.25);
    drawBust(g, BLONDE, { tn: -0.2, eye: 1.25, iris: 0.6, browUp: 1, mouth: 'scared', mouthK: 0.8 }, 760 - sh, 720, 1.05);
    drawBust(g, HOODIE, { tn: 0.1, eye: 1.25, iris: 0.6, browUp: 1, mouth: 'scared', mouthK: 0.6, look: 0.2 }, 560 + sh, 820, 1.3);
    g.restore();
    finish(g, W, H, t, { vig: 0.7, flick: 0.3, seed: 8 });
  },

  // 9 (ref 25.3-28.2) him in the aisle, bloody knife raised high, other hand spread on a seat back, grinning
  '09': ({ W, H }) => (g, t, u) => {
    seatsBg(g, W, H, t, { winY: 420 });
    wash(g, W, H, '#0b0c10', 0.15);
    const k = lerp(1.25, 1.36, ease(u)), sway = Math.sin(t * 2.4) * 10;
    drawBust(g, LI, { tn: 0.05, eye: 1.15, iris: 0.6, brow: 0.8, mouth: 'grin', mouthK: 0.55, socket: 0.35, shirtBlood: 0.9, hdx: sway * 0.3,
      armL: { sh: [-260, 400], el: [-470, 120 + sway], hd: [-400, -200 + sway], blood: 0.6 },
      armR: { front: true, sh: [260, 400], el: [440, 720], hd: [380, 860], fist: false } }, 640, 860, k * 0.92);
    seatBack(g, 740, 1580, 520, 700);
    inLocal((g2, lw) => { bloodyKnife(g2, -400, -200 + sway, -1.9, 330, lw, 1); fist(g2, [-400, -200 + sway], Math.atan2(-320, 70), LI.skin, lw); palm(g2, 400, 820, -0.1, LI.skin, lw, 1.15, 1); smear(g2, 420, 880, 110, 0.8, 4, 1.5); }, 640, 860, k * 0.92)(g);
    finish(g, W, H, t, { vig: 0.75, flick: 0.35, seed: 9 });
  },

  // 10 (ref 28.3-31.6) he bends down over the seat, grinning, reaches down (what's below stays behind the seat back)
  '10': ({ W, H, dur }) => { const T = N(dur, 3.3); return (g, t, u) => {
    const tt = T(t);
    paleWindow(g, W, 1000); g.fillStyle = '#383a40'; g.fillRect(0, 1000, W, H);
    splat(g, 260, 820, 150, 1, 51);
    const bend = E(tt, 0, 1.2), up = E(tt, 2.2, 3.0);
    g.save(); g.translate(760, 1800); g.rotate(-lerp(0.05, 0.32, bend) + 0.08 * up);
    drawBust(g, LI, { tn: -0.55, pitch: 0.7 * (1 - up), tilt: -0.08 + 0.12 * up, look: lerp(-0.6, 0.6, up), lookY: lerp(1, 0, up), eye: 1.1, iris: 0.6, mouth: 'grin', mouthK: lerp(0.5, 0.8, up), socket: 0.3, shirtBlood: 1,
      armL: { front: true, sh: [-260, 400], el: [-420, 820], hd: [-500, 1150] } }, 0, -1000, 1.2);
    g.restore();
    seatBack(g, -60, 1240, 700, 900, '#1a1e2c');
    smear(g, 260, 1260, 260, 1, 53, 2.6);
    finish(g, W, H, t, { vig: 0.75, flick: 0.3, seed: 10 });
  }; },

  // 11 (ref 31.7-33.4) outside: two passengers staring in horror, city lights
  '11': ({ W, H }) => (g, t, u) => outside(g, W, H, t, u),
  // 12 (ref 33.5-36.5) from behind him, hunched over the seat
  '12': ({ W, H }) => (g, t, u) => hunchedBack(g, W, H, t, u),

  // 13 (ref 37.0-38.0) ECU of his bloody grinning mouth, chewing
  '13': ({ W, H }) => (g, t, u) => {
    g.fillStyle = '#3b3d42'; g.fillRect(0, 0, W, H);
    drawBust(g, LI, { mouth: 'grin', mouthK: 0.75 + 0.25 * Math.abs(Math.sin(t * 7)), blood: 1, socket: 1, brow: 0.6 }, 560, 40 + u * 30, 6.2, 10);
    finish(g, W, H, t, { vig: 0.7, flick: 0.3, seed: 13 });
  },

  // 14 (ref 38.0-41.0) outside again: the woman's hand goes to her mouth, tears
  '14': ({ W, H }) => (g, t, u) => outside(g, W, H, t, u, { woman: 1 }),

  // 15 (ref 41.5-43.0) him walking past the window, head down, grinning, bloody knife low in his hand
  '15': ({ W, H }) => (g, t, u) => {
    paleWindow(g, W, 1050); g.fillStyle = '#5d6168'; g.fillRect(0, 1040, W, 30); g.fillStyle = '#383a40'; g.fillRect(0, 1070, W, H);
    g.fillStyle = '#5d6168'; g.fillRect(lerp(220, 120, u), 0, 34, 1050);
    const x = lerp(760, 600, u), bob = Math.abs(Math.sin(t * 6)) * 14;
    drawBust(g, LI, { tn: -0.45, tilt: -0.28, look: 0.3, lookY: 1, eye: 0.7, mouth: 'grin', mouthK: 0.6, socket: 0.45, shirtBlood: 1, blood: 0.6,
      armL: { front: true, sh: [-260, 400], el: [-330, 720], hd: [-200, 920], blood: 0.8 },
      armR: { sh: [260, 400], el: [380, 800], hd: [420, 1250], fist: false } }, x, 700 + bob, 1.2);
    inLocal((g2, lw) => { bloodyKnife(g2, -200, 920, 2.3, 320, lw, 1); fist(g2, [-200, 920], Math.atan2(200, 130), LI.skin, lw); }, x, 700 + bob, 1.2)(g);
    finish(g, W, H, t, { vig: 0.75 });
  },

  // 16 (ref 43.0-47.0) outside, close on the bus side: him behind the window, the glass cracks and bursts
  '16': ({ W, H, dur }) => { const T = N(dur, 4); return (g, t, u) => {
    const tt = T(t), k = lerp(1, 1.06, ease(u));
    g.save(); g.translate(W / 2, H / 2); g.scale(k, k); g.translate(-W / 2, -H / 2);
    g.fillStyle = '#2350a0'; g.fillRect(0, 0, W, H);
    g.fillStyle = '#16233f'; g.font = '900 150px sans-serif'; g.textAlign = 'center'; g.fillText('22', 300, 230);
    g.save(); g.beginPath(); g.rect(40, 420, 1000, 900); g.clip();
    g.fillStyle = '#20252f'; g.fillRect(40, 420, 1000, 900);
    seatBack(g, 140, 760, 260, 700, '#1a1e2c'); seatBack(g, 700, 720, 260, 700, '#1a1e2c');
    const pull = E(tt, 2.6, 3.2);
    drawBust(g, LI, { tn: 0.25, eye: 1.15, iris: 0.6, look: 0.7, mouth: 'neutral', smirk: 0.6, sweat: 1, shirtBlood: 1,
      armR: { front: true, sh: [260, 400], el: [lerp(440, 420, pull), lerp(760, 700, pull)], hd: [lerp(520, 470, pull), lerp(560, 470, pull)] } }, 520, 720, 1.0);
    wash(g, W, H, '#1c3d70', 0.38);
    g.strokeStyle = 'rgba(200,220,240,0.25)'; g.lineWidth = 30; g.beginPath(); g.moveTo(700, 420); g.lineTo(400, 1320); g.stroke();
    const crack = E(tt, 1.0, 2.9), cx0 = 840, cy0 = 980;
    g.strokeStyle = '#e8f2fa'; g.lineWidth = 4;
    for (let i = 0; i < 14; i++) { const a = i * 0.449 + 0.2, L = (120 + (i * 53) % 260) * crack; g.beginPath(); g.moveTo(cx0, cy0); g.lineTo(cx0 + Math.cos(a) * L * 0.5 + 12, cy0 + Math.sin(a) * L * 0.5); g.lineTo(cx0 + Math.cos(a) * L, cy0 + Math.sin(a) * L); g.stroke(); }
    if (crack > 0.3) for (let r = 60; r < 260 * crack; r += 70) { g.beginPath(); g.arc(cx0, cy0, r, 0, 7); g.stroke(); }
    g.restore();
    g.strokeStyle = INK; g.lineWidth = 8; g.strokeRect(40, 420, 1000, 900);
    g.fillStyle = '#c9ccd2'; g.fillRect(0, 1330, W, 40); g.strokeRect(-5, 1330, W + 10, 40);
    const burst = seg(tt, 3.3, 4);
    if (burst > 0) for (let i = 0; i < 26; i++) { const a = i * 0.9, d = burst * (200 + (i * 37) % 500); g.fillStyle = 'rgba(220,235,245,0.85)'; g.beginPath(); const x = cx0 + Math.cos(a) * d, y = cy0 + Math.sin(a) * d * 0.8 + burst * burst * 300; g.moveTo(x, y); g.lineTo(x + 30, y + 12); g.lineTo(x + 8, y + 40); g.closePath(); g.fill(); g.strokeStyle = INK; g.lineWidth = 2; g.stroke(); }
    g.restore();
    finish(g, W, H, t, { vig: 0.75 });
  }; },

  // 17 (ref 47.0-49.0) inside: him crouched between the seats, sweating, eyes darting, then ducks down
  '17': ({ W, H, dur }) => { const T = N(dur, 2); return (g, t, u) => {
    const tt = T(t);
    seatsBg(g, W, H, t, { winY: 380, rows: false });
    wash(g, W, H, '#0b0c10', 0.25);
    const duck = E(tt, 1.2, 1.7);
    drawBust(g, LI, { tn: 0.1 * Math.sin(tt * 6), look: Math.sin(tt * 5) > 0 ? 0.9 : -0.9, eye: 1.15, iris: 0.6, brow: 0.9, sweat: 1, mouth: 'neutral', shirtBlood: 1 }, 540, lerp(820, 1220, duck), 1.25);
    seatBack(g, -120, 1100, 560, 900); seatBack(g, 640, 1100, 560, 900);
    finish(g, W, H, t, { vig: 0.8 });
  }; },

  // 18 (ref 49.0-50.5) a police officer in the aisle, taser aimed; it fires
  '18': ({ W, H, dur }) => { const T = N(dur, 1.5); return (g, t, u) => {
    const tt = T(t);
    seatsBg(g, W, H, t, { winY: 380 });
    wash(g, W, H, '#0b0c10', 0.2);
    const k = 1.3;
    drawBust(g, COP, { tn: -0.4, brow: 0.9, eye: 1, look: -0.8, mouth: 'neutral',
      armL: { front: true, sh: [-250, 400], el: [-360, 620], hd: [-440, 420] }, armR: { front: true, sh: [250, 400], el: [60, 660], hd: [-380, 470] } }, 640, 640, k);
    const hx = 640 - 420 * k, hy = 640 + 430 * k;
    g.save(); g.translate(hx, hy); g.fillStyle = '#e3c22b'; g.fillRect(-150, -40, 160, 70); g.strokeStyle = INK; g.lineWidth = 6; g.strokeRect(-150, -40, 160, 70); g.fillStyle = '#1b1b1b'; g.fillRect(-150, -40, 40, 70); g.restore();
    const fire = seg(tt, 0.9, 1.1);
    if (fire > 0) { g.strokeStyle = '#d8ecff'; g.lineWidth = 4; for (const dy of [-14, 14]) { g.beginPath(); g.moveTo(hx - 150, hy + dy); for (let i = 1; i <= 8; i++) g.lineTo(hx - 150 - i * 90 * fire, hy + dy + (i % 2 ? 18 : -18)); g.stroke(); } wash(g, W, H, '#cfe6ff', 0.25 * (1 - fire)); }
    finish(g, W, H, t, { vig: 0.75 });
  }; },

  // 19 (ref 50.5-55.5) interrogation: an officer stands, he sits behind the table, the evidence laid out
  '19': ({ W, H }) => (g, t, u) => {
    const ty = 1240; interrogation(g, W, H, ty, t);
    const k = lerp(1, 1.06, ease(u));
    g.save(); g.translate(W / 2, H * 0.6); g.scale(k, k); g.translate(-W / 2, -H * 0.6);
    lightCone(g, W, H, 640, ty, 760);
    drawBust(g, COP, { tn: 0.35, mouth: 'neutral', eye: 0.9, look: 0.6 }, 150, 560, 0.85);
    drawBust(g, LI, { tn: -0.05, lookY: 0.7, eye: 0.8, brow: 0.5, sweat: 1, mouth: 'neutral', smirk: 0.2 }, 640, 760, 0.95);
    table(g, W, H, ty);
    evidenceBagsRow(g, ty + 70, 0.75);
    g.restore();
    wash(g, W, H, '#2a2410', 0.1);
    finish(g, W, H, t, { vig: 0.8, desat: 0.3 });
  },
  // 20 (ref 55.5-58.5) slow pan across the evidence on the table
  '20': ({ W, H }) => (g, t, u) => {
    g.fillStyle = '#5b5a3a'; g.fillRect(0, 0, W, H); table(g, W, H, 520);
    g.save(); g.translate(-lerp(0, 700, ease(u)), 0); evidenceBagsRow(g, 640, 1.7); g.restore();
    lightCone(g, W, H, 540, 520, 1400, 0.8);
    finish(g, W, H, t, { vig: 0.8, desat: 0.3 });
  },

  // 21 (ref 58.5-60.5) from behind him again, hunched over the seat
  '21': ({ W, H }) => (g, t, u) => hunchedBack(g, W, H, t, u, 1),
  // 22 (ref 60.5-62.5) LOOP: back to the opening shot
  '22': hook,
  // 23 (ref 62.5-66.7) Tim's empty seat by the window: his headphones, blood, the light flickering. Fade to black.
  '23': ({ W, H, dur }) => { const T = N(dur, 4.2); return (g, t, u) => {
    const tt = T(t);
    g.fillStyle = '#2c2e33'; g.fillRect(0, 0, W, H);
    nightView(g, 0, 0, W, 900, 800, t, 20, 9, 1.6);
    g.fillStyle = '#5d6168'; g.fillRect(0, 900, W, 30); g.strokeStyle = INK; g.lineWidth = 4; g.strokeRect(-5, 900, W + 10, 30);
    const k = lerp(1, 1.12, ease(u));
    g.save(); g.translate(W / 2, H * 0.55); g.scale(k, k); g.translate(-W / 2, -H * 0.55);
    seatBack(g, 180, 760, 720, 900, '#1d2131');
    g.fillStyle = '#252a3a'; g.fillRect(170, 1560, 740, 220); g.strokeStyle = INK; g.lineWidth = 7; g.strokeRect(170, 1560, 740, 220);
    smear(g, 420, 980, 300, 1, 61, 3); splat(g, 700, 1180, 200, 1, 63); splat(g, 520, 1640, 220, 1, 65); splat(g, 260, 600, 120, 0.8, 67);
    g.strokeStyle = INK; g.lineWidth = 30; g.beginPath(); g.arc(560, 1640, 120, Math.PI * 1.1, Math.PI * 1.9); g.stroke(); g.strokeStyle = '#2b2c33'; g.lineWidth = 18; g.stroke();
    for (const s of [-1, 1]) { g.beginPath(); g.ellipse(560 + s * 112, 1640, 44, 60, s * 0.3, 0, 7); g.fillStyle = '#2b2c33'; g.fill(); g.lineWidth = 6; g.strokeStyle = INK; g.stroke(); g.beginPath(); g.ellipse(560 + s * 118, 1640, 20, 32, s * 0.3, 0, 7); g.fillStyle = '#b5342b'; g.fill(); g.stroke(); }
    g.restore();
    finish(g, W, H, t, { vig: 0.85, flick: 0.8, seed: 23 });
    wash(g, W, H, '#000', E(tt, 3.2, 4.2));
  }; },
};

function evidenceBagsRow(g, y, s) {
  const items = [
    ['KNIFE', (g2, w, h) => bloodyKnife(g2, w * 0.15, h * 0.45, -0.25, w * 0.75, 4, 1)],
    ['CLOTHING', (g2, w, h) => { g2.fillStyle = '#b7babd'; g2.fillRect(w * 0.15, h * 0.2, w * 0.7, h * 0.5); g2.strokeStyle = INK; g2.lineWidth = 3; g2.strokeRect(w * 0.15, h * 0.2, w * 0.7, h * 0.5); splat(g2, w * 0.5, h * 0.45, w * 0.3, 1, 7); }],
    ['HEADPHONES', (g2, w, h) => { g2.strokeStyle = '#2b2c33'; g2.lineWidth = 14; g2.beginPath(); g2.arc(w * 0.5, h * 0.55, w * 0.25, Math.PI, 0); g2.stroke(); for (const sx of [-1, 1]) { g2.fillStyle = '#2b2c33'; g2.beginPath(); g2.ellipse(w * 0.5 + sx * w * 0.25, h * 0.58, w * 0.08, h * 0.1, 0, 0, 7); g2.fill(); } }],
    ['WALLET / ID', (g2, w, h) => { g2.fillStyle = '#5a3a24'; g2.fillRect(w * 0.25, h * 0.28, w * 0.5, h * 0.36); g2.strokeStyle = INK; g2.lineWidth = 3; g2.strokeRect(w * 0.25, h * 0.28, w * 0.5, h * 0.36); }],
  ];
  items.forEach(([label, fn], i) => evidenceBag(g, 60 + i * 260 * s, y + (i % 2) * 30 * s, 220 * s, 300 * s, (i % 2 ? 0.06 : -0.05), label, fn));
}
