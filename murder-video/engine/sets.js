// Sets / locations. Each builder returns { scene, update(t, ctx) }.
'use strict';

function baseScene(bg, fogNear, fogFar) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(bg);
  if (fogFar) scene.fog = new THREE.Fog(bg, fogNear, fogFar);
  return scene;
}

function particles(scene, n, area, color, size, seed, opacity = 0.8) {
  const R = makeRng(seed);
  const g = new THREE.BufferGeometry();
  const arr = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { arr[i * 3] = (R() - 0.5) * area[0]; arr[i * 3 + 1] = R() * area[1]; arr[i * 3 + 2] = (R() - 0.5) * area[2] + (area[3] || 0); }
  g.setAttribute('position', new THREE.BufferAttribute(arr, 3));
  const base = arr.slice();
  const pts = new THREE.Points(g, new THREE.PointsMaterial({ color, size, transparent: true, opacity, depthWrite: false, sizeAttenuation: true }));
  scene.add(pts);
  return { pts, base, n, area };
}

const SETS = {
  // ------------------------------------------------------------ London street at night
  street(variant) {
    const dark = variant === 'dark';
    const scene = baseScene(dark ? '#05070d' : '#0c1528', 7, dark ? 16 : 24);
    scene.add(new THREE.AmbientLight(dark ? '#232838' : '#34405e', dark ? 0.6 : 0.85));
    const moon = new THREE.DirectionalLight('#8fa6d8', dark ? 0.25 : 0.45); moon.position.set(-4, 10, 6); scene.add(moon);
    const ground = plane(scene, 60, 60, M('#555b66', { map: Tex.cobble([24, 24]) })); ground.rotation.x = -Math.PI / 2;
    box(scene, 30, 0.14, 2.6, M('#5d5e63', { map: Tex.stone([16, 2]) }), 0, 0.07, -2.25);
    const brick = M('#8a5040', { map: Tex.brick([5, 4], '#7a4535', '#3e3a36') });
    const houses = [[0, 0], [-9.2, 1], [9.2, 2]];
    houses.forEach(([hx, v]) => {
      const g = new THREE.Group(); g.position.x = hx; scene.add(g);
      box(g, 9, 7.2, 0.6, brick, 0, 3.6, -4.2);
      const roof = cyl(g, 0.01, 2.6, 9.2, 3, M('#1c1f27'), 0, 8.0, -4.6); roof.rotation.z = Math.PI / 2; roof.rotation.y = Math.PI / 2; roof.scale.set(1, 1, 0.7);
      box(g, 9.2, 0.25, 0.8, M('#c8c2b4'), 0, 7.2, -4.0);
      box(g, 9.2, 0.18, 0.7, M('#c8c2b4'), 0, 3.6, -3.95);
      for (const [wx, wy, lit] of [[-2.6, 1.9, 1], [-0.6, 1.9, 0], [-2.6, 5.4, v === 0 ? 1 : 0], [-0.4, 5.4, 0], [2.6, 5.4, v !== 1 ? 1 : 0]]) {
        const on = lit && !dark;
        box(g, 1.25, 1.95, 0.12, M('#e6e0d0'), wx, wy, -3.88);
        const glass = plane(g, 1.05, 1.75, on ? Basic('#fff', { map: Tex.window('#ffcf70') }) : M('#1a2233', { map: Tex.window('#2a3550') }), wx, wy, -3.81);
        box(g, 1.4, 0.1, 0.25, M('#e6e0d0'), wx, wy - 1.0, -3.8);
        if (on && v === 0) { const L = new THREE.PointLight('#ffb860', 0.9, 6, 2); L.position.set(wx, wy, -3.2); g.add(L); }
      }
      // door
      box(g, 1.5, 2.6, 0.15, M('#e6e0d0'), 1.5, 1.45, -3.88);
      plane(g, 1.1, 2.2, M('#fff', { map: Tex.frontDoor() }), 1.5, 1.3, -3.79);
      plane(g, 1.1, 0.35, dark ? M('#222') : Basic('#ffcf70'), 1.5, 2.6, -3.79);
      for (let i = 0; i < 3; i++) box(g, 1.7, 0.14, 0.4 - i * 0.0, M('#9a968c'), 1.5, 0.07 + i * 0.14, -3.55 - i * 0.12 + 0.24);
      // railings
      for (let x = -4.3; x < 0.6; x += 0.22) box(g, 0.035, 0.95, 0.035, M('#111'), x, 0.6, -3.25);
      box(g, 4.9, 0.05, 0.05, M('#111'), -1.85, 1.05, -3.25);
    });
    // street lamp
    const lamp = new THREE.Group(); lamp.position.set(-2.4, 0, -1.3); scene.add(lamp);
    cyl(lamp, 0.06, 0.09, 3.6, 6, M('#15171b'), 0, 1.8, 0);
    cyl(lamp, 0.2, 0.12, 0.45, 4, dark ? M('#333') : Basic('#ffd690'), 0, 3.8, 0).rotation.y = Math.PI / 4;
    cyl(lamp, 0.02, 0.26, 0.2, 4, M('#15171b'), 0, 4.12, 0).rotation.y = Math.PI / 4;
    if (!dark) { const L = new THREE.PointLight('#ffc070', 2.2, 9, 1.6); L.position.set(0, 3.6, 0.3); lamp.add(L); }
    // halo sprite
    const halo = plane(lamp, 1.6, 1.6, Basic('#ffcf80', { transparent: true, opacity: dark ? 0 : 0.18, depthWrite: false }), 0, 3.8, 0.1);
    // bare tree
    const tree = new THREE.Group(); tree.position.set(4.6, 0, -2.0); scene.add(tree);
    const bark = M('#1d1712');
    cyl(tree, 0.1, 0.2, 3.4, 5, bark, 0, 1.7, 0);
    const R = makeRng(4);
    for (let i = 0; i < 9; i++) { const b = cyl(tree, 0.02, 0.06, 1.4 + R(), 4, bark, 0, 2.4 + R() * 1.4, 0); b.rotation.z = (R() - 0.5) * 2.0; b.rotation.x = (R() - 0.5) * 1.2; b.position.x += Math.sin(b.rotation.z) * -0.5; }
    // moon
    ball(scene, 1.0, Basic(dark ? '#7b8399' : '#e8ecf5'), -9, 13, -22, 10, 8);
    const rain = particles(scene, 900, [16, 9, 14, 0], '#9fb2d6', 0.035, 21, 0.55);
    return {
      scene, update(t) {
        const a = rain.pts.geometry.attributes.position;
        for (let i = 0; i < rain.n; i++) { let y = rain.base[i * 3 + 1] - (t * 7.5) % 9; if (y < 0) y += 9; a.array[i * 3 + 1] = y; a.array[i * 3] = rain.base[i * 3] - y * 0.08; }
        a.needsUpdate = true;
        halo.lookAt(halo.parent.localToWorld(new THREE.Vector3(0, 3.8, 1)));
      }
    };
  },

  // ------------------------------------------------------------ Victorian parlour (tea table)
  parlour() {
    const scene = baseScene('#2a1d12', 12, 30);
    scene.add(new THREE.AmbientLight('#ffe2b8', 0.62));
    const sun = new THREE.DirectionalLight('#fff1d6', 0.55); sun.position.set(-2, 4, 2); scene.add(sun);
    const warm = new THREE.PointLight('#ffb36b', 0.9, 9, 1.4); warm.position.set(1.8, 2.2, 1.6); scene.add(warm);
    const floor = plane(scene, 8, 8, M('#7a4e2c', { map: Tex.wood([5, 3], '#6e4426') })); floor.rotation.x = -Math.PI / 2;
    const wp = M('#ffffff', { map: Tex.wallpaper([7, 3.4]) });
    const back = plane(scene, 8, 3.4, wp, 0, 1.7, -3);
    const left = plane(scene, 8, 3.4, wp, -3.2, 1.7, 0); left.rotation.y = Math.PI / 2;
    const right = plane(scene, 8, 3.4, wp, 3.2, 1.7, 0); right.rotation.y = -Math.PI / 2;
    const ceil = plane(scene, 8, 8, M('#d8ccb0'), 0, 3.4, 0); ceil.rotation.x = Math.PI / 2;
    const wain = M('#4a2c18');
    box(scene, 8, 0.9, 0.06, wain, 0, 0.45, -2.97); box(scene, 0.06, 0.9, 8, wain, -3.17, 0.45, 0); box(scene, 0.06, 0.9, 8, wain, 3.17, 0.45, 0);
    box(scene, 8, 0.06, 0.1, M('#3a2010'), 0, 0.92, -2.95);
    box(scene, 8, 0.16, 0.12, M('#e9e0c8'), 0, 3.32, -2.95);
    // window with lace + plant
    box(scene, 1.5, 1.7, 0.08, M('#efe9da'), -1.2, 1.85, -2.98);
    plane(scene, 1.3, 1.5, Basic('#fff', { map: Tex.window('#dfeaf0') }), -1.2, 1.85, -2.93);
    plane(scene, 1.45, 1.0, M('#ffffff', { map: Tex.lace(), transparent: true, alphaTest: 0.3, side: THREE.DoubleSide }), -1.2, 2.18, -2.86);
    box(scene, 1.7, 0.08, 0.25, M('#efe9da'), -1.2, 0.98, -2.88);
    cyl(scene, 0.12, 0.09, 0.2, 7, M('#a8563a'), -1.6, 1.12, -2.85);
    for (let i = 0; i < 6; i++) { const lf = blob(scene, 0.09, M('#3f7a3a'), 40 + i, 0.3, 0); lf.position.set(-1.6 + Math.sin(i) * 0.1, 1.3 + (i % 3) * 0.07, -2.85 + Math.cos(i) * 0.08); }
    // door
    box(scene, 1.15, 2.3, 0.08, M('#3a2010'), 2.0, 1.15, -2.98);
    plane(scene, 1.0, 2.15, M('#fff', { map: Tex.door() }), 2.0, 1.08, -2.93);
    // portrait of Belle + sideboard
    box(scene, 0.72, 0.92, 0.05, M('#a07a30', { shininess: 40 }), 0.5, 1.95, -2.96);
    plane(scene, 0.6, 0.8, M('#fff', { map: Tex.portrait() }), 0.5, 1.95, -2.93);
    box(scene, 1.4, 0.85, 0.45, M('#4a2a16'), 0.5, 0.43, -2.75);
    for (const x of [0.05, 0.95]) { cyl(scene, 0.03, 0.05, 0.25, 6, M('#c9a24a', { shininess: 50 }), x, 0.98, -2.7); box(scene, 0.02, 0.06, 0.02, Basic('#ffe0a0'), x, 1.13, -2.7); }
    // grandfather clock
    const clock = new THREE.Group(); clock.position.set(-2.6, 0, -2.6); clock.rotation.y = 0.6; scene.add(clock);
    box(clock, 0.5, 2.1, 0.35, M('#3e2412'), 0, 1.05, 0); box(clock, 0.58, 0.2, 0.4, M('#3e2412'), 0, 2.15, 0);
    const face = plane(clock, 0.36, 0.36, M('#fff', { map: Tex.clockface() }), 0, 1.75, 0.18);
    const hand1 = box(clock, 0.015, 0.13, 0.01, M('#111'), 0, 1.75, 0.19); const hand2 = box(clock, 0.02, 0.09, 0.01, M('#111'), 0, 1.75, 0.19);
    hand1.geometry.translate(0, 0.06, 0); hand2.geometry.translate(0, 0.04, 0);
    const pend = new THREE.Group(); pend.position.set(0, 1.45, 0.18); clock.add(pend);
    box(pend, 0.015, 0.55, 0.01, M('#c9a24a'), 0, -0.27, 0); cyl(pend, 0.06, 0.06, 0.015, 8, M('#d9b84a', { shininess: 60 }), 0, -0.55, 0).rotation.x = Math.PI / 2;
    // table with floral cloth + tea set
    const table = new THREE.Group(); scene.add(table);
    cyl(table, 0.85, 0.85, 0.04, 10, M('#fff', { map: Tex.floral([3, 1]) }), 0, 0.77, 0);
    cyl(table, 0.88, 0.95, 0.5, 10, M('#fff', { map: Tex.floral([4, 1]), side: THREE.DoubleSide }), 0, 0.52, 0, true);
    const china = M('#e8eef2', { shininess: 40, specular: 0x444444 });
    const pot = ball(table, 0.13, china, 0.1, 0.9, -0.1, 8, 6); pot.scale.y = 0.85;
    cyl(table, 0.03, 0.02, 0.16, 5, china, 0.24, 0.92, -0.1).rotation.z = -0.9;
    ball(table, 0.03, M('#c9a24a'), 0.1, 1.02, -0.1, 5, 4);
    for (const [x, z] of [[-0.55, 0.05], [-0.15, -0.55], [0.5, 0.25], [-0.2, 0.45]]) {
      cyl(table, 0.09, 0.09, 0.012, 8, china, x, 0.8, z);
      cyl(table, 0.05, 0.04, 0.07, 8, china, x, 0.84, z);
      cyl(table, 0.045, 0.045, 0.005, 8, M('#5a2e12'), x, 0.873, z);
    }
    cyl(table, 0.18, 0.18, 0.015, 10, china, 0.3, 0.8, 0.35);
    for (let i = 0; i < 6; i++) cyl(table, 0.04, 0.04, 0.014, 7, M('#b07a3a'), 0.3 + Math.sin(i) * 0.08, 0.815 + (i % 2) * 0.012, 0.35 + Math.cos(i * 2) * 0.08);
    // standard lamp
    const sl = new THREE.Group(); sl.position.set(2.5, 0, -1.6); scene.add(sl);
    cyl(sl, 0.02, 0.02, 1.6, 5, M('#2a1a10'), 0, 0.8, 0); cyl(sl, 0.2, 0.3, 0.3, 8, Basic('#f3c27a'), 0, 1.7, 0);
    return {
      scene, update(t) {
        pend.rotation.z = Math.sin(t * Math.PI) * 0.18;
        hand1.rotation.z = -t * 0.05; hand2.rotation.z = -1.2 - t * 0.004;
      }
    };
  },

  // ------------------------------------------------------------ the cellar
  cellar(variant) {
    const dark = variant === 'dark';
    const scene = baseScene('#030303', 2.5, dark ? 7 : 11);
    scene.add(new THREE.AmbientLight(dark ? '#3a4560' : '#3a3434', dark ? 0.75 : 0.6));
    const shaft = new THREE.DirectionalLight('#7f95c0', dark ? 0.35 : 0.3); shaft.position.set(0.5, 4, -3); scene.add(shaft);
    const fl = plane(scene, 8, 8, M('#6a5a50', { map: Tex.brick([5, 5], '#5e4a40', '#2a2622') })); fl.rotation.x = -Math.PI / 2;
    const wb = M('#7a5a4a', { map: Tex.brick([4, 2], '#5a3a2e', '#2e2a26') });
    plane(scene, 8, 2.6, wb, 0, 1.3, -2.2);
    const l = plane(scene, 8, 2.6, wb, -2.4, 1.3, 0); l.rotation.y = Math.PI / 2;
    const r = plane(scene, 8, 2.6, wb, 2.4, 1.3, 0); r.rotation.y = -Math.PI / 2;
    const c = plane(scene, 8, 8, M('#1e1812'), 0, 2.6, 0); c.rotation.x = Math.PI / 2;
    for (let x = -2; x <= 2; x += 0.9) box(scene, 0.2, 0.22, 8, M('#3a2a1c'), x, 2.5, 0);
    // little high window
    plane(scene, 0.6, 0.3, Basic(dark ? '#2a3550' : '#8fa6d0'), 0.6, 2.2, -2.18);
    const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.75, 2.6, 6, 1, true), Basic('#9fb6e6', { transparent: true, opacity: dark ? 0.03 : 0.07, depthWrite: false, side: THREE.DoubleSide }));
    beam.position.set(0.4, 1.2, -1.2); beam.rotation.x = -0.45; scene.add(beam);
    // the hole: lifted bricks
    const hole = plane(scene, 0.95, 0.65, Basic('#000'), 0, 0.012, 0); hole.rotation.x = -Math.PI / 2;
    const R = makeRng(8);
    const bm = M('#7a5444');
    for (let i = 0; i < 9; i++) { const b = box(scene, 0.24, 0.07, 0.11, bm, (R() - 0.5) * 1.6, 0.04 + R() * 0.03, (R() > 0.5 ? 1 : -1) * (0.4 + R() * 0.35)); b.rotation.set(R() * 0.5, R() * 3, R() * 0.4); }
    const dirt = blob(scene, 0.3, M('#3a2a1e'), 33, 0.3); dirt.position.set(0.8, 0.02, -0.2); dirt.scale.set(1.2, 0.35, 1);
    // lantern on floor
    const lan = new THREE.Group(); lan.position.set(0.55, 0, 0.45); scene.add(lan);
    box(lan, 0.14, 0.03, 0.14, M('#222'), 0, 0.015, 0); box(lan, 0.12, 0.18, 0.12, Basic(dark ? '#3a2410' : '#ffb347'), 0, 0.12, 0); box(lan, 0.14, 0.03, 0.14, M('#222'), 0, 0.225, 0);
    const lanL = new THREE.PointLight('#ff9a3c', 1.8, 5.5, 1.4); lanL.position.set(0, 0.35, 0); lan.add(lanL);
    // shovel, crates, barrel, coal
    const shv = new THREE.Group(); shv.position.set(2.2, 0, -1.4); shv.rotation.z = 0.25; scene.add(shv);
    box(shv, 0.04, 1.2, 0.04, M('#5a3a20'), 0, 0.75, 0); box(shv, 0.22, 0.28, 0.02, M('#444', { shininess: 30 }), 0, 0.14, 0);
    const crate = M('#7a5a36', { map: Tex.wood([1, 1], '#7a5a36') });
    box(scene, 0.6, 0.6, 0.6, crate, -1.6, 0.3, -1.4); box(scene, 0.45, 0.45, 0.45, crate, -1.55, 0.83, -1.35).rotation.y = 0.3;
    cyl(scene, 0.3, 0.3, 0.8, 8, M('#5a3a22'), 1.7, 0.4, -1.6);
    for (let i = 0; i < 6; i++) { const cl = blob(scene, 0.18, M('#151515', { shininess: 30 }), 50 + i, 0.3, 0); cl.position.set(-1.9 + i * 0.12, 0.05, 1.2 + (i % 3) * 0.15); cl.scale.y = 0.5; }
    // poison bottle on the crate
    const bottle = new THREE.Group(); bottle.position.set(-1.55, 1.055, -1.35); scene.add(bottle);
    cyl(bottle, 0.055, 0.06, 0.2, 8, M('#1f5a3a', { transparent: true, opacity: 0.92, shininess: 90, specular: 0x88ffaa, emissive: '#06180e' }), 0, 0.1, 0);
    cyl(bottle, 0.02, 0.045, 0.06, 8, M('#1f5a3a', { shininess: 90 }), 0, 0.23, 0);
    cyl(bottle, 0.022, 0.022, 0.04, 6, M('#a07a4a'), 0, 0.28, 0);
    const label = new THREE.Mesh(new THREE.CylinderGeometry(0.0565, 0.0605, 0.09, 12, 1, true, -0.9, 1.8), M('#fff', { map: Tex.poison() }));
    label.position.y = 0.1; label.rotation.y = 0.95; bottle.add(label);
    const bl = new THREE.PointLight('#ffcf90', dark ? 0 : 0.7, 1.6, 1.5); bl.position.set(0.25, 0.45, 0.4); bottle.add(bl);
    const dust = particles(scene, 160, [4, 2.4, 4, 0], '#d8c8a8', 0.018, 77, 0.6);
    return {
      scene, update(t) {
        lanL.intensity = (dark ? 0.35 : 1.7) + 0.25 * Math.sin(t * 13) + 0.15 * Math.sin(t * 29.3);
        const a = dust.pts.geometry.attributes.position;
        for (let i = 0; i < dust.n; i++) { a.array[i * 3] = dust.base[i * 3] + Math.sin(t * 0.3 + i) * 0.15; a.array[i * 3 + 1] = (dust.base[i * 3 + 1] + t * 0.05) % 2.4; }
        a.needsUpdate = true;
      }
    };
  },

  // ------------------------------------------------------------ ship deck (SS Montrose)
  deck(variant) {
    const dawn = variant === 'dawn';
    const skyTop = dawn ? '#3c4a78' : '#5b8fc7', skyBot = dawn ? '#f0a58a' : '#cfe3ef';
    const scene = baseScene(skyBot, 18, 70);
    scene.background = Tex.sky(skyTop, skyBot);
    scene.add(new THREE.HemisphereLight(dawn ? '#ffd0b0' : '#e8f2ff', dawn ? '#40384a' : '#3a4a55', 0.75));
    const sunL = new THREE.DirectionalLight(dawn ? '#ffb48a' : '#fff6e0', 0.85); sunL.position.set(dawn ? -8 : 5, dawn ? 3 : 10, -6); scene.add(sunL);
    // sea
    const seaG = new THREE.PlaneGeometry(160, 120, 48, 36); seaG.rotateX(-Math.PI / 2);
    const sea = new THREE.Mesh(seaG, M(dawn ? '#5a5a7a' : '#2f6482', { shininess: 30, specular: dawn ? 0x553322 : 0x335566 }));
    sea.position.set(0, -1.6, -55); scene.add(sea);
    const seaBase = seaG.attributes.position.array.slice();
    // horizon sun
    if (dawn) ball(scene, 3, Basic('#ffd6a0'), -30, 2, -78, 10, 8);
    // deck
    const deck = box(scene, 40, 0.3, 11, M('#b89060', { map: Tex.wood([30, 6], '#a88050') }), 0, -0.15, 1.5);
    deck.material.map.rotation = Math.PI / 2;
    box(scene, 40, 2.5, 0.3, M('#1a1a1a'), 0, -1.5, -4.0);
    // railing (sea side)
    const rail = M('#efefe8');
    for (let x = -18; x <= 18; x += 0.9) box(scene, 0.05, 1.0, 0.05, rail, x, 0.5, -3.6);
    box(scene, 36, 0.07, 0.1, rail, 0, 1.0, -3.6); box(scene, 36, 0.04, 0.05, rail, 0, 0.55, -3.6);
    // deckhouse + funnel (behind the camera side)
    box(scene, 22, 2.6, 0.4, M('#efeae0'), 0, 1.3, 6.2);
    for (let x = -9; x <= 9; x += 1.6) { const p = cyl(scene, 0.18, 0.18, 0.05, 10, M('#2a3a4a', { shininess: 80 }), x, 1.6, 5.99); p.rotation.x = Math.PI / 2; }
    for (let x = -9.8; x <= 9.8; x += 3.2) box(scene, 0.9, 1.9, 0.06, M('#6a4a2a', { map: Tex.door() }), x, 0.95, 5.98);
    box(scene, 22.4, 0.2, 0.6, M('#e0dbd0'), 0, 2.65, 6.1);
    cyl(scene, 1.0, 1.0, 4.5, 10, M('#c99a50'), 1.5, 4.8, 8.0); cyl(scene, 1.02, 1.02, 0.9, 10, M('#151515'), 1.5, 6.7, 8.0);
    // lifeboat, ventilators, deck chairs, mast
    const lb = new THREE.Group(); lb.position.set(6, 2.1, -3.2); scene.add(lb);
    const hull = ball(lb, 0.6, M('#f2f2ee'), 0, 0, 0, 8, 4); hull.scale.set(3.2, 0.6, 1);
    box(lb, 0.06, 2.2, 0.06, M('#ddd'), -1.6, -0.6, 0.1); box(lb, 0.06, 2.2, 0.06, M('#ddd'), 1.6, -0.6, 0.1);
    for (const x of [-6, -2.5, 9]) { cyl(scene, 0.18, 0.2, 1.4, 8, M('#efeae0'), x, 0.7, 5.0); const cw = ball(scene, 0.3, M('#efeae0'), x, 1.5, 5.1, 8, 5); cw.scale.z = 0.6; plane(scene, 0.3, 0.3, M('#7a1f1f'), x, 1.5, 4.93).rotation.y = Math.PI; }
    for (const x of [-8.5, -7.6, 4.0]) { const ch = new THREE.Group(); ch.position.set(x, 0, 4.4); ch.rotation.y = Math.PI + 0.2; scene.add(ch); box(ch, 0.55, 0.05, 0.9, M('#8a6038'), 0, 0.35, 0).rotation.x = -0.2; box(ch, 0.55, 0.7, 0.05, M('#8a6038'), 0, 0.65, -0.45).rotation.x = -0.4; }
    cyl(scene, 0.1, 0.14, 14, 6, M('#6a4a2a'), -12, 7, -1.5);
    const smoke = particles(scene, 60, [2, 8, 2, 8], dawn ? '#8a7a7a' : '#5a5a5a', 0.9, 99, 0.5);
    return {
      scene, update(t) {
        const a = seaG.attributes.position.array;
        for (let i = 0; i < a.length; i += 3) { const x = seaBase[i], z = seaBase[i + 2]; a[i + 1] = Math.sin(x * 0.35 + t * 1.3) * 0.28 + Math.sin(z * 0.5 + t * 0.9 + x * 0.1) * 0.22 + Math.sin((x + z) * 1.3 + t * 2) * 0.05; }
        seaG.attributes.position.needsUpdate = true; seaG.computeVertexNormals();
        const s = smoke.pts.geometry.attributes.position;
        for (let i = 0; i < smoke.n; i++) { const k = (smoke.base[i * 3 + 1] / 8 + t * 0.1) % 1; s.array[i * 3 + 1] = 7 + k * 8; s.array[i * 3] = 1.5 + smoke.base[i * 3] * (0.4 + k) - k * 6; }
        s.needsUpdate = true;
      }
    };
  },
  deck_dawn() { return SETS.deck('dawn'); },

  // ------------------------------------------------------------ Marconi wireless room
  radio() {
    const scene = baseScene('#120d0a', 4, 12);
    scene.add(new THREE.AmbientLight('#ffd8a8', 0.45));
    const lamp = new THREE.PointLight('#ffbe7a', 1.2, 6, 1.5); lamp.position.set(0.6, 2.2, 0.8); scene.add(lamp);
    const fl = plane(scene, 6, 6, M('#5a3a22', { map: Tex.wood([4, 4], '#4a3020') })); fl.rotation.x = -Math.PI / 2;
    const pw = M('#6a4426', { map: Tex.wood([4, 1], '#6a4426') });
    plane(scene, 6, 2.6, pw, 0, 1.3, -1.6);
    const l = plane(scene, 6, 2.6, pw, -2, 1.3, 0); l.rotation.y = Math.PI / 2;
    const r = plane(scene, 6, 2.6, pw, 2, 1.3, 0); r.rotation.y = -Math.PI / 2;
    const port = cyl(scene, 0.25, 0.25, 0.05, 12, Basic('#6aa0c8'), 1.0, 1.75, -1.58); port.rotation.x = Math.PI / 2;
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.27, 0.05, 5, 12), M('#b08a40', { shininess: 60 })); ring.position.set(1.0, 1.75, -1.55); scene.add(ring);
    // desk + apparatus
    box(scene, 1.8, 0.06, 0.8, M('#4a2e18'), 0, 0.76, -1.05);
    box(scene, 0.06, 0.76, 0.75, M('#3a2412'), -0.85, 0.38, -1.05); box(scene, 0.06, 0.76, 0.75, M('#3a2412'), 0.85, 0.38, -1.05);
    box(scene, 0.9, 0.45, 0.35, M('#2a2420', { map: Tex.dials() }), -0.2, 1.02, -1.3);
    box(scene, 0.5, 0.3, 0.3, M('#3a302a'), 0.55, 0.94, -1.3);
    for (let i = 0; i < 3; i++) { const co = new THREE.Mesh(new THREE.TorusGeometry(0.09, 0.02, 4, 8), M('#b8742a', { shininess: 60 })); co.position.set(0.45 + i * 0.1, 1.2, -1.3); co.rotation.y = Math.PI / 2; scene.add(co); }
    box(scene, 0.14, 0.03, 0.08, M('#222'), 0.05, 0.8, -0.8);
    const key = box(scene, 0.03, 0.02, 0.12, M('#b08a40', { shininess: 60 }), 0.05, 0.83, -0.8);
    // spark gap
    ball(scene, 0.03, M('#ccc', { shininess: 80 }), -0.65, 1.32, -1.3, 6, 4); ball(scene, 0.03, M('#ccc', { shininess: 80 }), -0.53, 1.32, -1.3, 6, 4);
    const spark = plane(scene, 0.1, 0.06, Basic('#cfe6ff', { transparent: true, opacity: 0 }), -0.59, 1.32, -1.27);
    const sparkL = new THREE.PointLight('#9fc8ff', 0, 4, 1.2); sparkL.position.set(-0.59, 1.35, -1.1); scene.add(sparkL);
    for (let i = 0; i < 4; i++) box(scene, 0.12, 0.16, 0.002, M('#efe8d4'), 1.3 + (i % 2) * 0.16, 1.5 - Math.floor(i / 2) * 0.2, -1.59).rotation.z = (i - 1.5) * 0.08;
    return {
      scene, update(t, ctx) {
        const on = ctx.keyDown ? 1 : 0;
        spark.material.opacity = on * (0.7 + 0.3 * Math.sin(t * 90));
        sparkL.intensity = on * 2.2;
        key.position.y = 0.83 - on * 0.008;
      }
    };
  },
};
