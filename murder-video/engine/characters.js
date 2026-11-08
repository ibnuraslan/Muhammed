// Low-poly characters with blocky faceted hair, simple rig, pose library, lip-sync + blinking
'use strict';

const THIGH = 0.43, SHIN = 0.43, LEG = THIGH + SHIN;

function makeCharacter(id, d, seed) {
  const W = d.width || 1;
  const skin = M(d.skin || '#e5b994');
  const hairM = M(d.hair || '#3a2a1e');
  const jacket = M(d.dress || d.jacket || '#333');
  const pantsM = M(d.dress ? '#3a2a2a' : (d.pants || '#2a2a2a'));
  const shoeM = M('#1a1412');
  const root = new THREE.Group();
  root.name = id;
  const P = { root };

  // blob shadow
  const sh = new THREE.Mesh(new THREE.CircleGeometry(0.32 * W, 10), Basic('#000', { transparent: true, opacity: 0.38, depthWrite: false }));
  sh.rotation.x = -Math.PI / 2; sh.position.y = 0.012; root.add(sh); P.shadow = sh;

  const hips = new THREE.Group(); hips.position.y = LEG; root.add(hips); P.hips = hips;
  box(hips, 0.32 * W, 0.14, 0.2, pantsM, 0, 0.0, 0);
  // legs
  for (const side of ['L', 'R']) {
    const sx = side === 'L' ? 1 : -1;
    const leg = new THREE.Group(); leg.position.set(0.085 * sx * W, 0, 0); hips.add(leg);
    box(leg, 0.13, THIGH, 0.14, pantsM, 0, -THIGH / 2, 0);
    const knee = new THREE.Group(); knee.position.y = -THIGH; leg.add(knee);
    box(knee, 0.115, SHIN, 0.125, pantsM, 0, -SHIN / 2, 0);
    box(knee, 0.11, 0.07, 0.22, shoeM, 0, -SHIN + 0.035, 0.045);
    P['thigh' + side] = leg; P['shin' + side] = knee;
  }
  if (d.dress) {
    const sk = cyl(hips, 0.17 * W, 0.31 * W, LEG - 0.06, 8, jacket, 0, -(LEG - 0.06) / 2 + 0.04, 0);
    P.skirt = sk;
  }
  if (d.coat) box(hips, 0.38 * W, 0.5, 0.25, M(d.coat), 0, -0.22, 0);

  // chair (shown only when seated)
  const chair = new THREE.Group(); root.add(chair); P.chair = chair; chair.visible = false;
  const wood = M('#4a2c18');
  box(chair, 0.46, 0.05, 0.44, wood, 0, 0.45, -0.05);
  box(chair, 0.46, 0.6, 0.05, wood, 0, 0.75, -0.27);
  for (const [x, z] of [[-0.2, 0.14], [0.2, 0.14], [-0.2, -0.24], [0.2, -0.24]]) box(chair, 0.04, 0.45, 0.04, wood, x, 0.225, z);

  const torso = new THREE.Group(); hips.add(torso); P.torso = torso;
  box(torso, 0.36 * W, 0.52, 0.22 * Math.min(W, 1.15), jacket, 0, 0.29, 0);
  const front = 0.111 * Math.min(W, 1.15);
  if (!d.dress) {
    box(torso, 0.12, 0.3, 0.01, M(d.shirt || '#eee'), 0, 0.4, front);
    if (d.tie) box(torso, 0.04, 0.26, 0.012, M(d.tie), 0, 0.39, front + 0.006);
  } else {
    box(torso, 0.14, 0.08, 0.01, skin, 0, 0.5, front); // neckline
  }
  if (d.buttons) for (let i = 0; i < 4; i++) for (const sx of [-1, 1]) box(torso, 0.022, 0.022, 0.012, M(d.buttons, { emissive: '#3a2a00' }), 0.1 * sx, 0.18 + i * 0.09, front + 0.004);
  if (d.pearls) for (let i = 0; i < 9; i++) { const a = (i / 8 - 0.5) * 2.2; ball(torso, 0.014, M('#f4f0e6', { shininess: 60, specular: 0xffffff }), Math.sin(a) * 0.09, 0.52 - Math.cos(a) * 0.04, Math.cos(a) * 0.1 + 0.02, 5, 4); }
  if (d.brooch) {
    const b = ball(torso, 0.024, M(d.brooch, { emissive: d.broochGlow ? d.brooch : '#000', shininess: 80, specular: 0xffffff }), -0.08 * W, 0.42, front + 0.01, 6, 4);
    P.brooch = b;
  }
  if (d.fur) {
    const fm = M(d.fur);
    for (let i = 0; i < 7; i++) { const a = (i / 6 - 0.5) * 3.4; const bl = blob(torso, 0.06, fm, seed * 7 + i, 0.25); bl.position.set(Math.sin(a) * 0.19, 0.5 - Math.abs(a) * 0.05, Math.cos(a) * 0.11); }
  }
  // neck + head
  cyl(torso, 0.05, 0.055, 0.1, 6, skin, 0, 0.58, 0);
  const head = new THREE.Group(); head.position.y = 0.61; torso.add(head); P.head = head;
  const HS = 1.12; // slightly big heads read better on a phone
  head.scale.setScalar(HS);
  const skull = ball(head, 0.115, skin, 0, 0.12, 0, 8, 6); skull.scale.set(1, 1.17, 1.06);
  box(head, 0.03, 0.05, 0.03, skin, 0.112, 0.12, -0.005); box(head, 0.03, 0.05, 0.03, skin, -0.112, 0.12, -0.005);
  const es = d.eyes || 1;
  const white = M('#f4f1ea'), pupilM = M('#1c140f'), browM = M(shade(d.hair || '#333', 0.7));
  P.eyes = []; P.brows = [];
  for (const sx of [-1, 1]) {
    const eg = new THREE.Group(); eg.position.set(0.043 * sx, 0.135, 0.105); head.add(eg);
    box(eg, 0.036 * es, 0.022 * es, 0.016, white, 0, 0, 0);
    box(eg, 0.016 * es, 0.019 * es, 0.01, pupilM, 0, -0.001, 0.009);
    P.eyes.push(eg);
    const br = box(head, 0.048, 0.012, 0.014, browM, 0.043 * sx, 0.167, 0.106); P.brows.push(br);
  }
  box(head, 0.024, 0.045, 0.034, M(shade(d.skin || '#e5b994', 0.95)), 0, 0.108, 0.118);
  const mouth = box(head, 0.052, 0.011, 0.016, M('#5a1c1c'), 0, 0.066, 0.106); P.mouth = mouth;
  if (d.glasses) {
    const gm = M(d.glasses, { shininess: 50 });
    for (const sx of [-1, 1]) { const r = new THREE.Mesh(new THREE.TorusGeometry(0.027, 0.0045, 4, 8), gm); r.position.set(0.043 * sx, 0.135, 0.122); head.add(r); }
    box(head, 0.03, 0.005, 0.005, gm, 0, 0.138, 0.124);
    for (const sx of [-1, 1]) box(head, 0.005, 0.005, 0.1, gm, 0.07 * sx, 0.138, 0.075);
  }
  if (d.moustache) { const m = blob(head, 0.032, M(d.moustache), seed + 3, 0.15, 0); m.scale.set(1.9, 0.55, 0.7); m.position.set(0, 0.085, 0.118); }
  if (d.beard) { const b = blob(head, 0.1, M(d.beard), seed + 4, 0.14); b.position.set(0, 0.035, 0.03); b.scale.set(1.08, 0.8, 0.9); mouth.position.z = 0.125; const m = blob(head, 0.03, M(d.beard), seed + 5, 0.15, 0); m.scale.set(1.9, 0.55, 0.7); m.position.set(0, 0.085, 0.12); }
  if (d.stubble) box(head, 0.1, 0.06, 0.03, M(d.stubble), 0, 0.045, 0.095);

  // hair — the crumpled "box" hair
  const hs = d.hairStyle || 'short';
  const H = (r, x, y, z, sx = 1, sy = 1, sz = 1, j = 0.16, det = 1) => { const b = blob(head, r, hairM, seed * 13 + x * 100 + y * 1000 + z * 77 | 0, j, det); b.position.set(x, y, z); b.scale.set(sx, sy, sz); return b; };
  if (hs === 'short') { H(0.125, 0, 0.175, -0.03, 1.0, 0.82, 1.05); }
  if (hs === 'tucked') { H(0.12, 0, 0.16, -0.035, 1.0, 0.85, 1.0); }
  if (hs === 'balding') { H(0.055, 0.1, 0.13, -0.03, 0.8, 1.2, 1.2, 0.2, 0); H(0.055, -0.1, 0.13, -0.03, 0.8, 1.2, 1.2, 0.2, 0); H(0.1, 0, 0.12, -0.065, 1.1, 0.8, 0.7); H(0.1, 0, 0.235, -0.02, 0.95, 0.28, 1.0, 0.1); }
  if (hs === 'bob') { H(0.14, 0, 0.17, -0.03, 1.06, 0.92, 1.06, 0.13); H(0.075, 0.105, 0.06, -0.015, 0.7, 1.45, 0.95); H(0.075, -0.105, 0.06, -0.015, 0.7, 1.45, 0.95); H(0.11, 0, 0.07, -0.075, 1.15, 1.2, 0.7); H(0.08, 0, 0.215, 0.075, 1.45, 0.45, 0.6, 0.12); }
  if (hs === 'bun') { H(0.13, 0, 0.17, -0.025, 1.02, 0.86, 1.06, 0.12); H(0.085, 0, 0.3, -0.035, 1.05, 0.95, 1.05, 0.2); }
  if (hs === 'updo') { H(0.13, 0, 0.17, -0.025, 1.02, 0.88, 1.06, 0.13); H(0.09, 0, 0.25, -0.1, 1.1, 1.0, 0.9, 0.2); }

  // hats
  if (d.hat === 'bowler') {
    const hm = M(d.hatColor || '#222');
    cyl(head, 0.165, 0.165, 0.014, 10, hm, 0, 0.245, -0.01);
    const c = ball(head, 0.118, hm, 0, 0.27, -0.01, 8, 5); c.scale.set(1, 0.85, 1.05);
  }
  if (d.hat === 'cap') {
    const hm = M(d.hatColor || '#555');
    const c = blob(head, 0.135, hm, seed + 9, 0.08); c.position.set(0, 0.24, -0.01); c.scale.set(1.02, 0.42, 1.08);
    box(head, 0.17, 0.014, 0.09, hm, 0, 0.23, 0.11).rotation.x = 0.15;
  }
  if (d.hat === 'captain') {
    const hm = M(d.hatColor || '#fff');
    cyl(head, 0.14, 0.125, 0.07, 10, hm, 0, 0.29, -0.01);
    cyl(head, 0.124, 0.124, 0.04, 10, M('#111'), 0, 0.25, -0.01);
    box(head, 0.17, 0.012, 0.085, M('#0d0d0d', { shininess: 60 }), 0, 0.235, 0.1).rotation.x = 0.22;
    box(head, 0.04, 0.03, 0.01, M('#d9b84a', { emissive: '#3a2a00' }), 0, 0.255, 0.125);
  }
  if (d.headphones) {
    const hm = M('#2a2a2a');
    const band = new THREE.Mesh(new THREE.TorusGeometry(0.135, 0.012, 4, 10, Math.PI), hm); band.position.set(0, 0.13, -0.01); head.add(band);
    for (const sx of [-1, 1]) { const cup = cyl(head, 0.04, 0.04, 0.03, 8, hm, 0.13 * sx, 0.12, -0.01); cup.rotation.z = Math.PI / 2; }
  }

  // arms
  const sleeve = d.dress ? jacket : jacket;
  for (const side of ['L', 'R']) {
    const sx = side === 'L' ? 1 : -1;
    const arm = new THREE.Group(); arm.position.set((0.215 * W) * sx, 0.5, 0); torso.add(arm);
    box(arm, 0.1, 0.3, 0.11, sleeve, 0, -0.14, 0);
    const el = new THREE.Group(); el.position.y = -0.29; arm.add(el);
    box(el, 0.09, 0.26, 0.1, sleeve, 0, -0.13, 0);
    const hand = new THREE.Group(); hand.position.y = -0.29; el.add(hand);
    box(hand, 0.075, 0.09, 0.055, skin, 0, 0, 0);
    P['arm' + side] = arm; P['fore' + side] = el; P['hand' + side] = hand;
  }

  // props (hidden unless an anim needs them)
  P.props = {};
  const lantern = new THREE.Group(); P.handR.add(lantern); lantern.position.set(0, -0.12, 0.02);
  box(lantern, 0.1, 0.02, 0.1, M('#222'), 0, 0.08, 0); box(lantern, 0.1, 0.02, 0.1, M('#222'), 0, -0.08, 0);
  box(lantern, 0.085, 0.14, 0.085, Basic('#ffb347'), 0, 0, 0);
  const ll = new THREE.PointLight('#ffa040', 0.8, 4.5, 1.5); ll.position.set(0, 0, 0.05); lantern.add(ll);
  lantern.userData.light = ll;
  P.props.lantern = lantern;
  const bar = new THREE.Group(); P.handR.add(bar); box(bar, 0.025, 0.7, 0.025, M('#3a3a3c', { shininess: 40 }), 0, -0.22, 0.03); P.props.crowbar = bar;
  const bino = new THREE.Group(); head.add(bino); bino.position.set(0, 0.135, 0.17);
  for (const sx of [-1, 1]) { const b = cyl(bino, 0.026, 0.03, 0.11, 7, M('#151515', { shininess: 40 }), 0.04 * sx, 0, 0); b.rotation.x = Math.PI / 2; }
  P.props.binoculars = bino;
  const paper = new THREE.Group(); P.handR.add(paper); const pp = plane(paper, 0.16, 0.22, M('#efe8d4', { side: THREE.DoubleSide }), 0, -0.05, 0.05); pp.rotation.x = -1.1; P.props.paper = paper;
  for (const k in P.props) P.props[k].visible = false;

  root.scale.setScalar(d.height || 1);
  return { id, def: d, P, seed, talkSmooth: 0 };
}

// ------------------------------------------------------------------ poses
const POSE_KEYS = ['hipY', 'rootY', 'torsoX', 'torsoY', 'torsoZ', 'headX', 'headY', 'headZ', 'aLx', 'aLz', 'fL', 'aRx', 'aRz', 'fR', 'tL', 'sL', 'tR', 'sR', 'mouth', 'brow', 'eyes', 'skirt', 'lookAmt'];

function basePose() {
  const p = {}; POSE_KEYS.forEach(k => p[k] = 0);
  p.aLz = 0.1; p.aRz = -0.1; p.fL = -0.15; p.fR = -0.15; p.skirt = 1; p.lookAmt = 1;
  return p;
}

function poseFor(anim, t, ch) {
  const p = basePose();
  const s = ch.seed;
  const sit = () => { p.hipY = 0.47 - LEG; p.tL = p.tR = -1.5; p.sL = p.sR = 1.5; p.aLx = p.aRx = -0.72; p.fL = p.fR = -0.8; p.aLz = -0.05; p.aRz = 0.05; p.torsoX = 0.06; p.skirt = 0.5; };
  const kneel = () => { p.hipY = 0.47 - LEG; p.tL = -1.45; p.sL = 1.45; p.tR = -0.15; p.sR = 1.6; };
  switch (anim) {
    case 'idle': case 'nod':
      p.torsoZ = 0.02 * Math.sin(t * 0.7 + s); p.headX = 0.03 * Math.sin(t * 0.9 + s);
      if (anim === 'nod') p.headX += 0.1 * Math.max(0, Math.sin(t * 3.2));
      break;
    case 'nervous':
      p.aLx = p.aRx = -0.55; p.aLz = -0.3; p.aRz = 0.3; p.fL = p.fR = -1.25; p.lookAmt = 0;
      p.headY = 0.75 * Math.sin(t * 1.1 + s) ; p.headX = 0.05; p.brow = 0.5;
      break;
    case 'sit': sit(); p.headX = 0.03 * Math.sin(t * 0.8 + s); break;
    case 'sit_shocked': sit(); p.torsoX = -0.12; p.headX = -0.06; p.mouth = 0.7; p.brow = 1; p.aRx = -0.6; p.fR = -1.5; p.aRz = 0.3; break;
    case 'shocked': p.torsoX = -0.1; p.mouth = 0.8; p.brow = 1; p.aLx = p.aRx = -0.55; p.aLz = 0.35; p.aRz = -0.35; p.fL = p.fR = -1.2; break;
    case 'sad': p.headX = 0.32; p.torsoX = 0.1; p.aLz = 0.04; p.aRz = -0.04; p.fL = p.fR = -0.05; p.brow = 0.45; p.eyes = 0.45; p.lookAmt = 0.3; break;
    case 'admire': p.aRx = -0.55; p.aRz = 0.32; p.fR = -1.45; p.aLz = 0.15; p.headX = -0.1; p.headZ = 0.1; p.eyes = 0.3; p.torsoY = 0.15 * Math.sin(t * 0.6); break;
    case 'kneel_dig': kneel(); p.torsoX = 0.55; p.headX = 0.3; p.lookAmt = 0;
      p.aLx = -1.0 + 0.28 * Math.sin(t * 4.5 + 1); p.aRx = -1.05 + 0.3 * Math.sin(t * 4.5); p.fL = p.fR = -0.35; p.aLz = -0.1; p.aRz = 0.1; break;
    case 'kneel_shocked': kneel(); p.torsoX = -0.05; p.headX = 0.12; p.mouth = 0.7; p.brow = 1; p.lookAmt = 0; p.aLx = -0.5; p.aLz = 0.3; p.fL = -0.6; p.aRx = -1.25; p.fR = -0.75; p.aRz = 0.05; break;
    case 'binoculars': p.aLx = p.aRx = -1.3; p.aLz = -0.42; p.aRz = 0.42; p.fL = p.fR = -1.45; p.headX = -0.04; p.headY = 0.12 * Math.sin(t * 0.5); p.lookAmt = 0.2; break;
    case 'hold_paper': p.aRx = -0.75; p.aRz = 0.2; p.fR = -0.9; p.headX = 0.18; break;
    case 'type': sit(); p.headX = 0.2; p.aRx = -0.62; p.fR = -0.85; p.aLx = -0.62; p.fL = -0.85; p.lookAmt = 0; break;
    case 'walk': {
      const ph = ch.walkPhase || 0;
      p.tL = -0.42 * Math.sin(ph); p.tR = 0.42 * Math.sin(ph);
      p.sL = 0.15 + 0.5 * Math.max(0, -Math.sin(ph + 0.6)); p.sR = 0.15 + 0.5 * Math.max(0, Math.sin(ph + 0.6));
      p.aLx = 0.32 * Math.sin(ph); p.aRx = -0.32 * Math.sin(ph); p.fL = p.fR = -0.3;
      p.rootY = 0.022 * Math.abs(Math.cos(ph)); p.torsoX = 0.04;
      break;
    }
  }
  return p;
}

function lerpPose(a, b, k) { const o = {}; POSE_KEYS.forEach(n => o[n] = a[n] + (b[n] - a[n]) * k); return o; }

function applyPose(ch, p, extra) {
  const P = ch.P;
  P.hips.position.y = LEG + p.hipY + p.rootY;
  P.torso.rotation.set(p.torsoX, p.torsoY + (extra.torsoYaw || 0), p.torsoZ);
  P.head.rotation.set(p.headX + (extra.headPitch || 0), p.headY + (extra.headYaw || 0), p.headZ);
  P.armL.rotation.set(p.aLx, 0, p.aLz); P.foreL.rotation.set(p.fL, 0, 0);
  P.armR.rotation.set(p.aRx, 0, p.aRz); P.foreR.rotation.set(p.fR, 0, 0);
  P.thighL.rotation.x = p.tL; P.shinL.rotation.x = p.sL;
  P.thighR.rotation.x = p.tR; P.shinR.rotation.x = p.sR;
  if (P.skirt) { P.skirt.scale.y = p.skirt; P.skirt.position.y = -(LEG - 0.06) * p.skirt / 2 + 0.04; P.skirt.rotation.x = p.skirt < 0.8 ? -0.35 : 0; }
  const open = Math.max(p.mouth, extra.talk || 0);
  P.mouth.scale.set(1 - open * 0.2, 1 + open * 2.4, 1);
  P.mouth.position.y = 0.066 - open * 0.012;
  const blink = extra.blink ? 1 : 0;
  const shut = Math.max(p.eyes, blink);
  P.eyes.forEach(e => e.scale.y = Math.max(0.08, 1 - shut * 0.92));
  P.brows.forEach((b, i) => { b.position.y = 0.167 + p.brow * 0.018; b.rotation.z = (i ? -1 : 1) * (p.brow * 0.25 - (extra.frown || 0) * 0.3); });
  P.chair.visible = !!extra.chair;
}
