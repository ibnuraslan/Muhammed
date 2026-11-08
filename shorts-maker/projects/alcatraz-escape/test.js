// test.js - 16:9 look test for the Alcatraz long-form: night kit + investigation kit.
import { THREE, ease, seg, lerp, clamp, rng, toon, basic, box, cyl, mesh } from '/animator/engine.js';
import { Char, portraitCanvas } from '/animator/cast.js';
import { office, desk, impactBurst } from '/animator/props.js';
import { nightSky, ocean, lightBeam, flicker, cityLights, prisonIsland, prisonCell } from '/animator/kits/night.js';
import { evidenceBoard, mapPlane, land, label, caseFile, titleCard } from '/animator/kits/investigation.js';

// the men (plain prison shirts, cartoon versions - not likenesses)
const MORRIS = { body: 'plain', color: '#7d8fa6', shirt: '#d6dbe2', bodyW: 150, headR: 144, hat: 'hair', hairColor: '#2b1d14', eyes: 'half', mouth: 'flat' };
const JOHN = { ...MORRIS, hairColor: '#8a5a2b', headR: 148, eyes: 'dot' };
const CLARENCE = { ...MORRIS, hairColor: '#a06b38', headR: 150, eyes: 'dot', mouth: 'smirk' };
const WEST = { ...MORRIS, hairColor: '#151515', mustache: 'pencil', eyes: 'dot' };

// San Francisco Bay, stylised (u right, v down)
function drawBay(g, w, h) {
  g.fillStyle = '#9db4b8'; g.fillRect(0, 0, w, h);                 // water
  g.strokeStyle = 'rgba(60,90,100,0.18)'; g.lineWidth = 2;
  for (let y = 20; y < h; y += 26) { g.beginPath(); for (let x = 0; x <= w; x += 20) g.lineTo(x, y + Math.sin(x * 0.03) * 3); g.stroke(); }
  land(g, w, h, [[0, 0], [0.55, 0], [0.5, 0.12], [0.4, 0.22], [0.33, 0.35], [0.22, 0.48], [0.1, 0.56], [0, 0.58]]);             // Marin
  land(g, w, h, [[0, 0.7], [0.18, 0.66], [0.3, 0.68], [0.38, 0.74], [0.47, 0.76], [0.52, 0.84], [0.5, 1], [0, 1]]);              // San Francisco
  land(g, w, h, [[0.8, 0], [1, 0], [1, 1], [0.78, 1], [0.74, 0.8], [0.77, 0.55], [0.82, 0.3]]);                                   // East Bay
  land(g, w, h, [[0.45, 0.27], [0.5, 0.21], [0.56, 0.24], [0.58, 0.31], [0.53, 0.37], [0.46, 0.35]]);                            // Angel Island
  land(g, w, h, [[0.522, 0.552], [0.538, 0.548], [0.542, 0.562], [0.526, 0.566]], { fill: '#8a7a5a' });                          // Alcatraz
  label(g, w, h, 'MARIN', 0.2, 0.22); label(g, w, h, 'SAN FRANCISCO', 0.22, 0.86); label(g, w, h, 'ANGEL ISLAND', 0.51, 0.17, { size: 0.022 });
  label(g, w, h, 'ALCATRAZ', 0.62, 0.56, { size: 0.024, color: '#7a1e1e' }); label(g, w, h, 'GOLDEN GATE', 0.09, 0.635, { size: 0.018 });
  label(g, w, h, 'San Francisco Bay', 0.64, 0.68, { size: 0.026, italic: true, color: '#3c5a63' });
  // compass
  g.save(); g.translate(w * 0.9, h * 0.12); g.strokeStyle = '#4a3824'; g.fillStyle = '#4a3824'; g.lineWidth = 3;
  g.beginPath(); g.moveTo(0, -40); g.lineTo(10, 0); g.lineTo(0, 40); g.lineTo(-10, 0); g.closePath(); g.stroke(); g.beginPath(); g.moveTo(0, -40); g.lineTo(10, 0); g.lineTo(-10, 0); g.closePath(); g.fill();
  g.font = '700 26px Georgia, serif'; g.textAlign = 'center'; g.fillText('N', 0, -52); g.restore();
}

// cover the office's daylight windows with night glass
function nightWindows(S) {
  const nightT = new THREE.MeshBasicMaterial({ color: 0x0b1630 });
  for (const x of [-7, 0, 7]) { const m = new THREE.Mesh(new THREE.PlaneGeometry(4.6, 4.4), nightT); m.position.set(x, 5.2, -7.76); S.add(m); }
}

export const shots = {
  // 1. The island at night, the beam sweeping, three men on a raft in the black water. Title.
  '01': (S) => {
    nightSky(S, { fog: [160, 1100], moon: [-420, 150, -260] });
    ocean(S, { amp: 0.4 });
    const { lampPos } = prisonIsland(S);
    lightBeam(S, lampPos, { length: 160, radius: 16, spin: 0.55, yaw: 2.2, tilt: 0.06 });
    cityLights(S, { z: -340 });
    const raft = new THREE.Group();
    const rubber = toon(0x3e3a2c);
    raft.add(cyl(0.35, 0.35, 4.2, rubber, [-0.85, 0.25, 0], { rot: [Math.PI / 2, 0, 0] }));
    raft.add(cyl(0.35, 0.35, 4.2, rubber, [0.85, 0.25, 0], { rot: [Math.PI / 2, 0, 0] }));
    raft.add(box(1.7, 0.12, 4.0, rubber, [0, 0.1, 0]));
    raft.position.set(62, 0, 112); raft.rotation.y = 0.9; S.add(raft);
    const men = [MORRIS, JOHN, CLARENCE].map((d, i) => { const c = new Char(S, d, { seed: 10 + i, h: 1.7, shadow: false }); c.set({ sit: true, look: -0.4, eyes: 'wide', mouth: 'flat' }); c.dz = -1.2 + i * 1.2; return c; });
    const title = titleCard(S, 'THE ALCATRAZ ESCAPE', { sub: 'JUNE 11, 1962', y: 0.27 });
    S.grade({ vignette: 0.7, grain: 0.07 });
    return (t, u) => {
      const bob = Math.sin(t * 1.6) * 0.18, roll = Math.sin(t * 1.1) * 0.06;
      raft.position.set(62 - t * 0.4, bob, 112 - t * 0.5); raft.rotation.z = roll;
      men.forEach((c, i) => { const p = new THREE.Vector3(0, 0.15, c.dz).applyAxisAngle(new THREE.Vector3(0, 1, 0), raft.rotation.y).add(raft.position);
        c.pos(p.x, p.y - 0.25, p.z); c.set({ armR: 1.2 + Math.sin(t * 5 + i) * 0.5 }); });
      title.userData.fade(ease.io(seg(u, 0.45, 0.65)));
      S.camMove(u, [[68, 1.6, 121], [30, 5, 50]], [[66, 2.0, 118], [20, 9, 30]], ease.io, [40, 38]);
    };
  },
  // 2. A cell at night: digging at the vent with a spoon; a guard's flashlight sweeps the bars - he freezes.
  '02': (S) => {
    nightSky(S, { moon: null, stars: false, fog: null, hemi: 0.18, moonLight: 0.15 });
    const cell = prisonCell(S, { toilet: false });
    const man = new Char(S, MORRIS, { seed: 21, pos: [0.15, -0.72, -1.15], shadow: false });
    man.set({ sit: true, hold: 'spoon', facing: 1 });
    const dust = [0, 1, 2].map(() => { const b = impactBurst(S, { text: null, size: 0.28, color: '#b8b2a6' }); b.position.set(0.55, 0.42, -1.5); return b; });
    const torch = new THREE.SpotLight(0xfff0c8, 0, 18, 0.32, 0.5, 1.2); torch.position.set(-2.6, 1.8, 3.6); S.add(torch, torch.target);
    const beam = lightBeam(S, [-2.6, 1.8, 3.6], { length: 9, radius: 1.3, spin: 0, opacity: 0.18 });
    S.grade({ vignette: 0.75, grain: 0.08 });
    return (t, u) => {
      const sweep = seg(u, 0.5, 0.85), lit = sweep > 0 && sweep < 1;
      const aim = new THREE.Vector3(lerp(-1.2, 1.6, ease.io(sweep)), 0.8, -1.2);
      torch.target.position.copy(aim); torch.intensity = lit ? 40 : 0;
      beam.visible = lit; beam.lookAt(aim);
      beam.rotateY(Math.PI);
      const frozen = u > 0.55;
      man.set({ armR: frozen ? 1.45 : 1.5 + Math.sin(t * 14) * 0.13, eyes: frozen ? 'wide' : 'half', sweat: frozen ? 1 : 0, look: frozen ? -0.6 : 0.4, mouth: frozen ? 'o' : 'flat' });
      dust.forEach((b, i) => { const k = ((t * 2.2 + i / 3) % 1) * 0.45; b.show(frozen ? -1 : k); });
      S.camMove(u, [[0.85, 1.05, 1.3], [0.3, 0.6, -1.3]], [[0.7, 0.95, 0.65], [0.32, 0.55, -1.3]], ease.io, [52, 48]);
    };
  },
  // 3. The evidence board: the detective works the case, red strings connecting the men.
  '03': (S) => {
    S.sky({ hemi: 0.22, fog: null, sun: [-20, 30, 40], sunI: 0.25, shadow: 15 });
    office(S); nightWindows(S);
    S.scene.traverse(o => { if (o.isPointLight) o.intensity = 6; });
    const lamp = new THREE.SpotLight(0xffd59a, 140, 16, 0.55, 0.5, 1.3); lamp.position.set(0.5, 7, -2.5); lamp.target.position.set(0, 3.4, -7.6); S.add(lamp, lamp.target);
    flicker(S, lamp, { seed: 8, amount: 0.5 });
    const items = [
      { type: 'photo', design: MORRIS, label: 'AZ-1441', caption: 'FRANK MORRIS', at: [-2.1, 0.7] },
      { type: 'photo', design: JOHN, label: 'AZ-1476', caption: 'JOHN ANGLIN', at: [-0.7, 0.75] },
      { type: 'photo', design: CLARENCE, label: 'AZ-1485', caption: 'CLARENCE ANGLIN', at: [0.7, 0.7] },
      { type: 'photo', design: WEST, label: '', caption: 'ALLEN WEST', at: [2.1, 0.75] },
      { type: 'note', text: 'JUNE 11\n1962', at: [-1.9, -0.95] },
      { type: 'note', text: '?', at: [-0.1, -1.0], color: '#ffffff', fontSize: 170, size: [0.7, 0.7] },
      { type: 'note', text: '50+\nRAINCOATS', at: [1.25, -0.95] },
      { type: 'note', text: 'LEFT\nBEHIND', at: [2.45, -0.85], color: '#ff9f9f' },
    ];
    const board = evidenceBoard(S, { pos: [0, 3.6, -7.55], items, links: [[0, 5], [1, 5], [2, 5], [0, 1], [1, 2], [4, 5], [6, 5], [3, 7]] });
    const det = new Char(S, 'detective', { pos: [1.9, 0, -4.6] });
    const fill = new THREE.PointLight(0xffd59a, 10, 6, 1.5); fill.position.set(1.2, 2.6, -3.2); S.add(fill);
    S.grade({ vignette: 0.7, grain: 0.06 });
    return (t, u) => {
      board.userData.setStrings(seg(u, 0.1, 0.85));
      det.set({ facing: -1, armR: lerp(0.3, 2.2, ease.back(seg(u, 0.15, 0.4))), eyes: 'half', mouth: 'flat', look: -0.5, brow: 0.3 });
      S.camMove(u, [[-1.4, 2.9, 1.6], [0.2, 3.0, -7.6]], [[0.4, 2.7, -0.6], [0.6, 2.8, -7.6]], ease.io, [44, 42]);
    };
  },
  // 4. The map on the desk: the route into the bay, the paddle, the question mark, then UNSOLVED.
  '04': (S) => {
    S.sky({ hemi: 0.2, fog: null, sun: [-20, 30, 40], sunI: 0.2, shadow: 10 });
    office(S); nightWindows(S);
    S.scene.traverse(o => { if (o.isPointLight) o.intensity = 4; });
    const dk = desk(S, 0, 0, { w: 3.6, d: 2.0 });
    dk.userData.items.forEach(o => { o.visible = false; });
    const map = mapPlane({ w: 2.2, h: 1.6, draw: drawBay,
      route: [[0.53, 0.556], [0.525, 0.5], [0.518, 0.45], [0.51, 0.4]],
      markers: [{ uv: [0.63, 0.34], text: 'PADDLE', at: 0.62, size: 0.03 }, { uv: [0.51, 0.47], text: '?', at: 0.78, size: 0.11 }, { uv: [0.13, 0.6], text: '?', at: 0.86, size: 0.08 }] });
    map.rotation.x = -Math.PI / 2; map.position.set(-0.45, 1.075, 0.05); S.add(map);
    const file = caseFile({ title: 'CASE FILE', lines: ['ALCATRAZ ESCAPE', 'JUNE 11-12, 1962', 'MORRIS · ANGLIN · ANGLIN'], stamp: 'UNSOLVED' });
    file.rotation.set(-Math.PI / 2, 0, -0.12); file.scale.setScalar(0.72); file.position.set(1.25, 1.08, 0.2); S.add(file);
    const lamp = new THREE.SpotLight(0xffd59a, 70, 10, 0.6, 0.5, 1.2); lamp.position.set(0.6, 3.6, -0.9); lamp.target.position.set(0, 1.06, 0); S.add(lamp, lamp.target);
    S.camera.up.set(0, 0, -1);
    S.grade({ vignette: 0.7, grain: 0.06 });
    const STAMP = 0.86;
    return (t, u) => {
      map.userData.setProgress(seg(u, 0.08, 0.9));
      const k = (u - STAMP) * S.duration;
      file.userData.stamp(k);
      S.shake = k > 0 && k < 0.25 ? 0.025 * (1 - k / 0.25) : 0;
      S.camMove(u, [[0.25, 3.3, 1.3], [0.2, 1.06, -0.05]], [[0.35, 2.6, 0.8], [0.35, 1.06, 0.0]], ease.io, [46, 46]);
    };
  },
};
