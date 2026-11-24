// ===================== sculpted procedural heads =====================
import { THREE, mat, mesh, rng } from './engine.js';
const g2 = (dx, dy, dz, s) => Math.exp(-(dx * dx + dy * dy + dz * dz) / (s * s));
// head in unit space: x forward (face), y up, z side. Returns displaced, smooth geometry.
export let HD = false; export const setHD = v => HD = v;
export function headGeometry(v = {}) {
  const geo = new THREE.SphereGeometry(1, HD ? 72 : 36, HD ? 56 : 28), p = geo.attributes.position, n = new THREE.Vector3();
  const jawW = v.jawW ?? .78, chin = v.chin ?? .12, cheek = v.cheek ?? .1, brow = v.brow ?? .1, nose = v.nose ?? 1, noseLen = v.noseLen ?? 1;
  for (let i = 0; i < p.count; i++) {
    let x = p.getX(i), y = p.getY(i), z = p.getZ(i);
    n.set(x, y, z).normalize();
    // base proportions: taller, narrower, flatter sides, fuller back of skull
    y *= 1.13; z *= .9; if (x < 0) x *= 1.05; if (y > .5) { x *= 1 - (y - .5) * .12; z *= 1 - (y - .5) * .08; }
    // jaw taper & chin
    if (y < -.15) { const k = Math.min(1, (-.15 - y) / .95); z *= 1 - (1 - jawW) * k; x *= 1 - .08 * k; if (x > 0) x += chin * g2(0, y + 1.0, z, .35) * 1.0; }
    let d = 0;
    d += brow * g2(x - .92, y - .3, Math.abs(z) - .32, .28);                       // brow ridge
    d -= .11 * g2(x - .88, y - .12, Math.abs(z) - .34, .17);                       // eye sockets
    d += cheek * g2(x - .62, y + .12, Math.abs(z) - .56, .3);                      // cheekbones
    d += .2 * nose * g2(x - .95, (y + .12) / noseLen, z * 1.9, .22);               // nose
    d += .1 * nose * g2(x - 1.0, y + .38 * noseLen, z * 1.4, .13);                 // nose tip
    d += .035 * g2(x - .98, y + .4 * noseLen, Math.abs(z) - .12, .06);             // nostril wings
    d -= .025 * g2(x - .96, y + .62, z * .6, .07);                                 // mouth line
    d += .035 * g2(x - .97, y + .55, z * .7, .1);                                  // upper lip
    d += .03 * g2(x - .95, y + .7, z * .8, .1);                                    // lower lip
    d -= .04 * g2(x - .6, y - .1, Math.abs(z) - .78, .25);                         // temples
    p.setXYZ(i, x + n.x * d, y + n.y * d, z + n.z * d);
  }
  geo.computeVertexNormals(); return geo;
}
function irisTexture(col) { const cv = document.createElement('canvas'); cv.width = 256; cv.height = 128; const x = cv.getContext('2d'); x.fillStyle = '#efe9df'; x.fillRect(0, 0, 256, 128); x.save(); x.translate(128, 64); x.scale(1, 2); const g = x.createRadialGradient(0, 0, 1, 0, 0, 13); g.addColorStop(0, '#050302'); g.addColorStop(.38, '#050302'); g.addColorStop(.45, col); g.addColorStop(.9, col); g.addColorStop(1, '#140c06'); x.fillStyle = g; x.beginPath(); x.arc(0, 0, 13, 0, 7); x.fill(); x.fillStyle = 'rgba(255,255,255,.95)'; x.beginPath(); x.arc(-4, -4, 2.6, 0, 7); x.fill(); x.restore(); const t = new THREE.CanvasTexture(x.canvas); t.colorSpace = THREE.SRGBColorSpace; return t; }
function skinTexture(hex) { const cv = document.createElement('canvas'); cv.width = cv.height = 256; const x = cv.getContext('2d'); const c = new THREE.Color(hex); x.fillStyle = '#' + c.getHexString(); x.fillRect(0, 0, 256, 256); const r = rng(3); for (let i = 0; i < 2500; i++) { x.fillStyle = `rgba(${r() < .5 ? '120,60,40' : '255,230,210'},${r() * .06})`; x.fillRect(r() * 256, r() * 256, 2, 2); } const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; return t; }
const strand = (pts, r, m) => new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts.map(p => new THREE.Vector3(...p))), HD ? 24 : 10, r, HD ? 8 : 5, false), m);
// builds a full face into `head` group (head-local units ~ meters, head height ~ .24)
export function buildFace(head, o) {
  const r = rng((o.seed || 1) * 31 + 5), S = .102;
  const skinM = new THREE.MeshStandardMaterial({ color: 0xffffff, map: skinTexture(o.skin), roughness: .55, metalness: 0 });
  const hairM = mat(o.hair, .85);
  const v = { jawW: .72 + r() * .14, chin: .06 + r() * .12, cheek: .06 + r() * .08, brow: .07 + r() * .07, nose: .8 + r() * .5, noseLen: .9 + r() * .25 };
  const h = new THREE.Mesh(headGeometry(v), skinM); h.scale.setScalar(S); h.position.y = o.y0 ?? .04; h.castShadow = h.receiveShadow = true; head.add(h);
  const P = (x, y, z) => [x * S, y * S * 1.0 + (o.y0 ?? .04), z * S];
  // eyes
  const iris = irisTexture(o.eye || '#4a3a22');
  for (const s of [-1, 1]) { const e = new THREE.Mesh(new THREE.SphereGeometry(.14 * S, HD ? 24 : 12, HD ? 16 : 8), new THREE.MeshStandardMaterial({ map: iris, roughness: .12 })); e.position.set(...P(.78, .13, s * .33)); e.rotation.y = s * .08; head.add(e); (head.userData.eyes = head.userData.eyes || []).push(e);
    const lid = new THREE.Mesh(new THREE.SphereGeometry(.152 * S, HD ? 20 : 10, HD ? 10 : 5, 0, Math.PI * 2, 0, Math.PI * .34), skinM); lid.position.copy(e.position); lid.rotation.z = -.45; head.add(lid); (head.userData.lids = head.userData.lids || []).push(lid);
    const br = strand([P(.92, .3, s * .14), P(.97, .36, s * .3), P(.9, .34, s * .48)], .028 * S * 1.6, hairM); head.add(br); }
  // ears
  for (const s of [-1, 1]) { const ear = new THREE.Mesh(new THREE.TorusGeometry(.13 * S, .06 * S, 8, 16, Math.PI * 1.6), skinM); ear.position.set(...P(-.08, .05, s * .86)); ear.rotation.set(0, s > 0 ? 0 : Math.PI, Math.PI * .6); ear.scale.set(1, 1.5, .6); head.add(ear); }
  // mustache / beard
  if (!o.noMustache) for (const s of [-1, 1]) head.add(strand([P(1.03, -.44, s * .02), P(1.02, -.46, s * .18), P(.96, -.52, s * .32), P(.88, -.57, s * .4)], .075 * S, hairM));
  if (o.beard) { const bg = headGeometry(v), pos = bg.attributes.position, idx = bg.index.array, keep = [];
    const ok = i => { const x = pos.getX(i), y = pos.getY(i); return y < -.28 + (x < .5 ? .25 : 0) && x > -.35; };
    for (let i = 0; i < idx.length; i += 3) if (ok(idx[i]) && ok(idx[i + 1]) && ok(idx[i + 2])) keep.push(idx[i], idx[i + 1], idx[i + 2]);
    bg.setIndex(keep); const b = new THREE.Mesh(bg, hairM); b.scale.set(S * 1.06, S * (1.02 + o.beard * .06), S * 1.07); b.position.set(.004, .04 - o.beard * .006, 0); head.add(b); }
  // hair (under the cap): back and sides
  const hg = new THREE.SphereGeometry(1, HD ? 40 : 20, HD ? 24 : 12, -Math.PI * .5, Math.PI, 0, Math.PI * .6); const hr = new THREE.Mesh(hg, hairM); hr.scale.set(S * 1.08, S * 1.16, S * .96); hr.position.set(-.004, (o.y0 ?? .04) + .002, 0); head.add(hr);
  return h;
}
