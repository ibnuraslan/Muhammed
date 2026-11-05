// engine.js - tiny 3D "toon world" engine for story shorts (three.js)
// Everything is procedural: no downloaded models or textures.
import * as THREE from 'three';
export { THREE };

export const W = 1080, H = 1920, FPS = 30;

// ------------------------------------------------------------------ math
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const seg = (u, a, b) => clamp((u - a) / (b - a));
export const ease = {
  lin: t => t,
  in: t => t * t * t,
  out: t => 1 - Math.pow(1 - t, 3),
  io: t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  back: t => { const c = 1.9; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); },
};
export const lerp3 = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
export function rng(seed = 1) {
  let s = (seed * 2654435761) >>> 0 || 1;
  return () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; };
}

// ------------------------------------------------------------------ materials
let _grad = null;
function gradientMap() {
  if (_grad) return _grad;
  const d = new Uint8Array([110, 110, 110, 255, 185, 185, 185, 255, 255, 255, 255, 255]);
  _grad = new THREE.DataTexture(d, 3, 1, THREE.RGBAFormat);
  _grad.minFilter = _grad.magFilter = THREE.NearestFilter;
  _grad.needsUpdate = true;
  return _grad;
}
export function toon(color, o = {}) {
  return new THREE.MeshToonMaterial({ color, gradientMap: gradientMap(), ...o });
}
export function basic(color, o = {}) { return new THREE.MeshBasicMaterial({ color, ...o }); }

export function canvasTex(w, h, draw, repeat) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const g = c.getContext('2d'); draw(g, w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  if (repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...repeat); }
  t.userData.canvas = c; t.userData.ctx = g;
  return t;
}
// speckled painterly texture
export function noiseTex(base, specks, n = 4000, size = 512, repeat = [8, 8], seed = 3, r = [1, 4]) {
  const R = rng(seed);
  return canvasTex(size, size, (g, w, h) => {
    g.fillStyle = base; g.fillRect(0, 0, w, h);
    for (let i = 0; i < n; i++) {
      g.fillStyle = specks[Math.floor(R() * specks.length)];
      g.globalAlpha = 0.25 + R() * 0.5;
      const s = r[0] + R() * (r[1] - r[0]);
      g.beginPath(); g.ellipse(R() * w, R() * h, s * 1.6, s, R() * 3, 0, 7); g.fill();
    }
    g.globalAlpha = 1;
  }, repeat);
}

// ------------------------------------------------------------------ geometry helpers
export function mesh(geo, mat, pos = [0, 0, 0], o = {}) {
  const m = new THREE.Mesh(geo, mat);
  m.position.set(...pos);
  if (o.rot) m.rotation.set(...o.rot);
  if (o.scale) Array.isArray(o.scale) ? m.scale.set(...o.scale) : m.scale.setScalar(o.scale);
  m.castShadow = o.cast !== false; m.receiveShadow = o.receive !== false;
  return m;
}
export const box = (w, h, d, mat, pos, o) => mesh(new THREE.BoxGeometry(w, h, d), mat, pos, o);
export const cyl = (rt, rb, h, mat, pos, o = {}) => mesh(new THREE.CylinderGeometry(rt, rb, h, o.seg || 24), mat, pos, o);
export const sphere = (r, mat, pos, o = {}) => mesh(new THREE.SphereGeometry(r, o.seg || 24, o.seg ? o.seg / 2 : 16), mat, pos, o);

// text on a transparent (or coloured) plane
export function textPlane(lines, o = {}) {
  const w = o.px || 1024, h = Math.round(w * (o.h || 1) / (o.w || 4));
  const tex = canvasTex(w, h, (g) => {
    if (o.bg) { g.fillStyle = o.bg; roundRect(g, 0, 0, w, h, o.radius || 0); g.fill(); }
    if (o.border) { g.strokeStyle = o.border; g.lineWidth = h * 0.05; roundRect(g, h * .04, h * .04, w - h * .08, h - h * .08, o.radius || 0); g.stroke(); }
    const L = Array.isArray(lines) ? lines : [lines];
    L.forEach((ln, i) => {
      const fs = (o.size || 0.62) * h / L.length;
      g.font = `${o.weight || 900} ${fs}px ${o.font || 'Georgia, serif'}`;
      g.fillStyle = o.fg || '#222'; g.textAlign = 'center'; g.textBaseline = 'middle';
      g.fillText(ln, w / 2, h * (i + 0.5) / L.length, w * 0.92);
    });
  });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(o.w || 4, o.h || 1),
    new THREE.MeshBasicMaterial({ map: tex, transparent: !o.bg, side: THREE.DoubleSide, toneMapped: false }));
  return m;
}
export function roundRect(g, x, y, w, h, r) {
  g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r);
  g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath();
}

// ------------------------------------------------------------------ stage
export class Stage {
  constructor(renderer, seed = 1) {
    this.renderer = renderer;
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(50, W / H, 0.1, 2000);
    this.R = rng(seed);
    this.chars = [];
    this.updaters = [];
    this.shake = 0;
  }
  add(...o) { o.forEach(x => this.scene.add(x)); return o[0]; }
  onUpdate(fn) { this.updaters.push(fn); }

  // sky dome + fog + lights
  sky({ top = '#1d5bd4', horizon = '#a9d6ff', bottom = '#f3d9b0', fog = [60, 420], sun = [40, 60, 30], sunColor = 0xfff1d6, sunI = 2.6, hemi = 0.95, shadow = 40, ground = 0xd9a46a } = {}) {
    const geo = new THREE.SphereGeometry(900, 32, 16);
    const mat = new THREE.ShaderMaterial({
      side: THREE.BackSide, depthWrite: false, fog: false,
      uniforms: { top: { value: new THREE.Color(top) }, hor: { value: new THREE.Color(horizon) }, bot: { value: new THREE.Color(bottom) } },
      vertexShader: 'varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0);}',
      fragmentShader: `uniform vec3 top; uniform vec3 hor; uniform vec3 bot; varying vec3 vP;
        void main(){ float h=vP.y; vec3 c = h>0.0 ? mix(hor, top, pow(clamp(h*1.6,0.0,1.0),0.7)) : mix(hor, bot, clamp(-h*4.0,0.0,1.0));
        gl_FragColor = vec4(c,1.0);
        #include <colorspace_fragment>
        }`,
    });
    const dome = new THREE.Mesh(geo, mat); dome.renderOrder = -10;
    this.scene.add(dome); this.dome = dome;
    if (fog) this.scene.fog = new THREE.Fog(new THREE.Color(horizon), fog[0], fog[1]);
    const hemiL = new THREE.HemisphereLight(new THREE.Color(horizon), new THREE.Color(ground), hemi);
    const sunL = new THREE.DirectionalLight(sunColor, sunI);
    sunL.position.set(...sun); sunL.castShadow = true;
    sunL.shadow.mapSize.set(2048, 2048);
    const sc = sunL.shadow.camera; sc.left = sc.bottom = -shadow; sc.right = sc.top = shadow; sc.near = 1; sc.far = 400;
    sunL.shadow.bias = -0.0006; sunL.shadow.normalBias = 0.03;
    this.scene.add(hemiL, sunL, sunL.target);
    this.sun = sunL; this.hemi = hemiL;
    return this;
  }
  // keep the shadow box centred on what we're looking at
  shadowFocus(x, y, z) { this.sun.target.position.set(x, y, z); const p = this._sunOff || (this._sunOff = this.sun.position.clone()); this.sun.position.set(x + p.x, y + p.y, z + p.z); }

  cloud(pos, scale = 1, seed = 1) {
    const R = rng(seed), g = new THREE.Group();
    const m = toon(0xffffff, { emissive: 0x8899bb, emissiveIntensity: 0.25 });
    const n = 6 + Math.floor(R() * 5);
    for (let i = 0; i < n; i++) {
      const r = 2 + R() * 3;
      const s = mesh(new THREE.IcosahedronGeometry(r, 2), m, [(R() - .5) * 14, R() * 2.5, (R() - .5) * 5], { cast: false, receive: false });
      s.scale.y = 0.7; g.add(s);
    }
    g.position.set(...pos); g.scale.setScalar(scale);
    this.scene.add(g); return g;
  }

  camAt(pos, look, fov) {
    const c = this.camera; c.position.set(...pos);
    if (this.shake) { const t = this._t || 0; c.position.x += Math.sin(t * 47) * this.shake; c.position.y += Math.sin(t * 61 + 1) * this.shake; }
    c.lookAt(...look);
    if (fov) { c.fov = fov; c.updateProjectionMatrix(); }
  }
  // camera move between two framings with easing
  camMove(u, from, to, e = ease.io, fov) {
    const k = e(clamp(u));
    this.camAt(lerp3(from[0], to[0], k), lerp3(from[1], to[1], k), fov ? lerp(fov[0], fov[1], k) : undefined);
  }
  // orbit around a point
  camOrbit(u, center, radius, a0, a1, height, e = ease.io, fov) {
    const a = lerp(a0, a1, e(clamp(u)));
    this.camAt([center[0] + Math.sin(a) * radius, center[1] + height, center[2] + Math.cos(a) * radius], center, fov);
  }
  frame(t, u) {
    this._t = t;
    if (this.update) this.update(t, u);
    for (const f of this.updaters) f(t, u);
    for (const c of this.chars) c.update(this.camera, t);
    this.renderer.render(this.scene, this.camera);
  }
  dispose() {
    this.scene.traverse(o => {
      if (o.geometry) o.geometry.dispose();
      if (o.material) [].concat(o.material).forEach(m => { if (m.map) m.map.dispose(); m.dispose(); });
    });
  }
}

// ------------------------------------------------------------------ renderer
export function makeRenderer() {
  const r = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
  r.setPixelRatio(1); r.setSize(W, H);
  r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFSoftShadowMap;
  r.outputColorSpace = THREE.SRGBColorSpace;
  r.toneMapping = THREE.NoToneMapping;
  document.body.appendChild(r.domElement);
  return r;
}
