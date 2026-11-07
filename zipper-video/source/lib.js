// ---------- core helpers ----------
const W = 720, H = 1280, S = 1.5; // design units -> pixels (1080x1920)
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const P = (t, s, d) => clamp((t - s) / d);
const E = {
  out: t => 1 - Math.pow(1 - t, 3),
  in: t => t * t * t,
  inOut: t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
  back: t => { const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
  elastic: t => t === 0 ? 0 : t === 1 ? 1 : Math.pow(2, -10 * t) * Math.sin((t * 10 - .75) * (2 * Math.PI / 3)) + 1,
  slam: t => t < .6 ? E.in(t / .6) : 1 + Math.sin((t - .6) / .4 * Math.PI) * 0.06 * (1 - (t - .6) / .4),
};
function rng(seed) { let s = (seed * 2654435761) >>> 0 || 1; return () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; }; }
function mkCanvas(w, h) { const c = document.createElement('canvas'); c.width = Math.round(w); c.height = Math.round(h); return c; }

function noiseFactory(seed) {
  const r = rng(seed), perm = new Uint8Array(512), g = new Float32Array(256);
  const p = [...Array(256).keys()];
  for (let i = 255; i > 0; i--) { const j = Math.floor(r() * (i + 1));[p[i], p[j]] = [p[j], p[i]]; }
  for (let i = 0; i < 512; i++) perm[i] = p[i & 255];
  for (let i = 0; i < 256; i++) g[i] = r();
  return (x, y) => {
    const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
    const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
    const X = xi & 255, Y = yi & 255;
    const a = g[perm[X + perm[Y]]], b = g[perm[X + 1 + perm[Y]]], c = g[perm[X + perm[Y + 1]]], d = g[perm[X + 1 + perm[Y + 1]]];
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
  };
}
function fbm(n, x, y, o = 4) { let s = 0, a = .5, f = 1, t = 0; for (let i = 0; i < o; i++) { s += a * n(x * f, y * f); t += a; a *= .5; f *= 2.03; } return s / t; }

// ---------- procedural textures (pixel resolution) ----------
function texFromFn(w, h, fn) {
  const c = mkCanvas(w, h), x = c.getContext('2d'), id = x.createImageData(w, h), d = id.data;
  for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
    const [r, g, b] = fn(i, j), k = (j * w + i) * 4;
    d[k] = r; d[k + 1] = g; d[k + 2] = b; d[k + 3] = 255;
  }
  x.putImageData(id, 0, 0); return c;
}
function makeWood(seed, dark = 0, plankH = 260) {
  const n = noiseFactory(seed), n2 = noiseFactory(seed + 9), r = rng(seed);
  const offs = Array.from({ length: 20 }, () => [r() * 1000, r() * .25 - .12]);
  const ph = plankH * S;
  return texFromFn(W * S, H * S, (x, y) => {
    const pl = Math.floor(y / ph), [ox, tone] = offs[pl % 20];
    const yy = y - pl * ph;
    const warp = fbm(n2, (x + ox) / 420, y / 160, 3) * 60;
    const ring = Math.sin((y + warp) * 0.23 + fbm(n, (x + ox) / 900, y / 30, 2) * 9);
    const fine = n((x + ox) / 6, y / 1.2);
    let v = 0.55 + 0.16 * ring + 0.14 * (fbm(n, (x + ox) / 300, y / 50, 3) - .5) * 2 + 0.1 * (fine - .5) + tone;
    const seam = Math.min(yy, ph - yy); if (seam < 5) v *= 0.35 + 0.13 * seam; else if (seam < 14) v *= 0.85 + 0.01 * seam;
    v = clamp(v * (1 - dark));
    return [40 + 120 * v, 22 + 70 * v, 10 + 36 * v];
  });
}
function makePaperTex(seed) {
  const n = noiseFactory(seed), n2 = noiseFactory(seed + 3), r = rng(seed + 1);
  const pw = 1100, phh = 1600;
  return texFromFn(pw, phh, (x, y) => {
    const blot = fbm(n, x / 220, y / 220, 5), fine = n2(x / 2.2, y / 2.2), fib = n2(x / 40, y / 3);
    let v = 0.87 + (blot - .5) * .13 + (fine - .5) * .07 + (fib - .5) * .04;
    const stain = Math.max(0, fbm(n2, x / 70 + 50, y / 70, 3) - .66) * .55;
    v -= stain;
    return [236 * v + 6, 220 * v - 4, 182 * v - 22];
  });
}
function makeFelt(seed) {
  const n = noiseFactory(seed);
  return texFromFn(W * S / 2, H * S / 2, (x, y) => {
    const v = .55 + (fbm(n, x / 120, y / 120, 4) - .5) * .5 + (n(x / 1.3, y / 1.3) - .5) * .25;
    return [30 * v + 8, 62 * v + 10, 50 * v + 8];
  });
}
function makeCanvasCloth(seed, base = [92, 92, 52]) {
  const n = noiseFactory(seed);
  return texFromFn(W * S / 2, H * S / 2, (x, y) => {
    const weave = (Math.sin(x * 1.7) * Math.sin(y * 1.7)) * .06;
    const v = .8 + (fbm(n, x / 90, y / 90, 4) - .5) * .45 + weave + (n(x / 1.1, y / 1.1) - .5) * .12;
    return [base[0] * v, base[1] * v, base[2] * v];
  });
}
function makeGrain(seed) {
  const c = mkCanvas(540, 960), x = c.getContext('2d'), id = x.createImageData(540, 960), d = id.data, r = rng(seed);
  for (let i = 0; i < d.length; i += 4) { const v = 128 + (r() + r() + r() - 1.5) * 120; d[i] = d[i + 1] = d[i + 2] = v; d[i + 3] = 255; }
  x.putImageData(id, 0, 0); return c;
}

// ---------- paper pieces (cached) ----------
const cache = {};
function tornPath(c, w, h, seed, rough = 4, step = 9) {
  const r = rng(seed); c.beginPath();
  const edge = (x0, y0, x1, y1, first) => {
    const L = Math.hypot(x1 - x0, y1 - y0), n = Math.max(2, Math.round(L / step));
    const nx = -(y1 - y0) / L, ny = (x1 - x0) / L;
    for (let i = 0; i <= n; i++) {
      const t = i / n, j = (i === 0 || i === n) ? 0 : (r() - .5) * rough * 2;
      const px = lerp(x0, x1, t) + nx * j, py = lerp(y0, y1, t) + ny * j;
      if (first && i === 0) c.moveTo(px, py); else c.lineTo(px, py);
    }
  };
  const m = rough;
  edge(m, m, w - m, m, true); edge(w - m, m, w - m, h - m); edge(w - m, h - m, m, h - m); edge(m, h - m, m, m);
  c.closePath();
}
function paper(w, h, seed = 1, o = {}) {
  const key = `p${w}_${h}_${seed}_${JSON.stringify(o)}`; if (cache[key]) return cache[key];
  const pad = 6, cw = (w + pad * 2) * S, ch = (h + pad * 2) * S;
  const c = mkCanvas(cw, ch), x = c.getContext('2d');
  x.scale(S, S); x.translate(pad, pad);
  const rough = o.rough ?? 3.5;
  tornPath(x, w, h, seed, rough, o.step ?? 8);
  x.save(); x.clip();
  const r = rng(seed + 7), tex = TEX.paper;
  const sx = r() * (tex.width - Math.min(tex.width, w * S)), sy = r() * (tex.height - Math.min(tex.height, h * S));
  x.drawImage(tex, sx, sy, Math.min(tex.width, w * S), Math.min(tex.height, h * S), 0, 0, w, h);
  if (o.tint) { x.fillStyle = o.tint; x.globalCompositeOperation = 'multiply'; x.fillRect(0, 0, w, h); x.globalCompositeOperation = 'source-over'; }
  // aged/burnt edges
  x.filter = `blur(${o.burnBlur ?? 10}px)`;
  x.strokeStyle = o.burn ?? 'rgba(110,70,25,0.55)'; x.lineWidth = o.burnW ?? 26;
  tornPath(x, w, h, seed, rough, o.step ?? 8); x.stroke();
  x.filter = 'none';
  if (o.lines) { // ruled lines
    x.strokeStyle = 'rgba(80,90,120,0.18)'; x.lineWidth = 1;
    for (let yy = 40; yy < h; yy += 26) { x.beginPath(); x.moveTo(0, yy); x.lineTo(w, yy); x.stroke(); }
  }
  if (o.fold) { const g = x.createLinearGradient(w / 2 - 8, 0, w / 2 + 8, 0); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(.5, 'rgba(90,60,20,0.18)'); g.addColorStop(.51, 'rgba(255,255,255,0.15)'); g.addColorStop(1, 'rgba(0,0,0,0)'); x.fillStyle = g; x.fillRect(w / 2 - 8, 0, 16, h); }
  x.restore();
  x.strokeStyle = 'rgba(90,60,25,0.5)'; x.lineWidth = .8; tornPath(x, w, h, seed, rough, o.step ?? 8); x.stroke();
  const res = { c, w, h, pad }; cache[key] = res; return res;
}
function drawPaper(ctx, pp, x, y, rot = 0, o = {}) { // x,y = center
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); if (o.scale) ctx.scale(o.scale, o.scale);
  ctx.globalAlpha *= o.alpha ?? 1;
  ctx.shadowColor = `rgba(0,0,0,${o.shadowA ?? .55})`; ctx.shadowBlur = (o.shadow ?? 18) * S; ctx.shadowOffsetY = (o.shadowY ?? 8) * S; ctx.shadowOffsetX = (o.shadowX ?? 3) * S;
  ctx.drawImage(pp.c, -pp.w / 2 - pp.pad, -pp.h / 2 - pp.pad, pp.w + pp.pad * 2, pp.h + pp.pad * 2);
  ctx.restore();
}

// ---------- text ----------
function font(fam, size) { return `${size}px "${fam}"`; }
function txt(ctx, s, x, y, o = {}) {
  ctx.save();
  ctx.font = font(o.fam || 'Special Elite', o.size || 40);
  ctx.textAlign = o.align || 'center'; ctx.textBaseline = o.base || 'alphabetic';
  if (o.ls != null) ctx.letterSpacing = o.ls + 'px';
  ctx.globalAlpha *= o.alpha ?? 1;
  ctx.translate(x, y); if (o.rot) ctx.rotate(o.rot); if (o.scale != null) ctx.scale(o.scale, o.scale * (o.sy ?? 1));
  let str = s; if (o.typed != null) str = s.slice(0, Math.floor(s.length * clamp(o.typed) + 0.0001));
  if (o.shadow) { ctx.shadowColor = o.shadow; ctx.shadowBlur = (o.shadowBlur ?? 10) * S; ctx.shadowOffsetY = (o.shadowY ?? 3) * S; }
  if (o.stroke) { ctx.strokeStyle = o.stroke; ctx.lineWidth = o.strokeW || 4; ctx.lineJoin = 'round'; ctx.strokeText(str, 0, 0); ctx.shadowColor = 'transparent'; }
  ctx.fillStyle = o.color || '#2b2118';
  if (!o.noFill) ctx.fillText(str, 0, 0);
  ctx.restore();
}
function measure(ctx, s, fam, size, ls = 0) { ctx.save(); ctx.font = font(fam, size); ctx.letterSpacing = ls + 'px'; const w = ctx.measureText(s).width; ctx.restore(); return w; }

// torn paper strip with text
function strip(ctx, s, x, y, o = {}) {
  const fam = o.fam || 'Special Elite', size = o.size || 30;
  const tw = measure(ctx, s, fam, size, o.ls || 0);
  const w = Math.round(tw + (o.padX ?? 26) * 2), h = Math.round(size * 1.15 + (o.padY ?? 10) * 2);
  const pp = paper(w, h, o.seed || (s.length * 13 + size), { rough: 3, step: 6, burnW: 14, burnBlur: 6, tint: o.tint });
  const p = o.p ?? 1; if (p <= 0) return;
  ctx.save(); ctx.translate(x, y); ctx.rotate(o.rot || 0);
  const sc = o.anim === 'slide' ? 1 : lerp(o.from ?? 1.6, 1, E.back(p));
  const dx = o.anim === 'slide' ? (1 - E.out(p)) * (o.dx ?? -500) : 0;
  ctx.translate(dx, 0); ctx.scale(sc, sc); ctx.globalAlpha *= clamp(p * 3);
  drawPaper(ctx, pp, 0, 0, 0, { shadow: 10, shadowY: 5, shadowA: .5 });
  txt(ctx, s, 0, size * 0.36, { fam, size, color: o.color || '#231a12', ls: o.ls, typed: o.typed });
  ctx.restore();
}

// rubber stamp
function stampCanvas(lines, o = {}) {
  const key = 'st' + JSON.stringify([lines, o]); if (cache[key]) return cache[key];
  const fam = o.fam || 'Black Ops One', size = o.size || 60, color = o.color || '#a3221c';
  const tmp = mkCanvas(10, 10).getContext('2d');
  const tw = Math.max(...lines.map(l => measure(tmp, l, fam, size, o.ls || 2)));
  const w = tw + 60, h = lines.length * size * 1.05 + 44;
  const c = mkCanvas(w * S, h * S), x = c.getContext('2d'); x.scale(S, S);
  x.strokeStyle = color; x.fillStyle = color;
  if (o.oval) { x.lineWidth = 7; x.beginPath(); x.ellipse(w / 2, h / 2, w / 2 - 6, h / 2 - 6, 0, 0, 7); x.stroke(); x.lineWidth = 2.5; x.beginPath(); x.ellipse(w / 2, h / 2, w / 2 - 16, h / 2 - 16, 0, 0, 7); x.stroke(); }
  else if (!o.noBorder) { x.lineWidth = 6; x.strokeRect(6, 6, w - 12, h - 12); x.lineWidth = 2; x.strokeRect(14, 14, w - 28, h - 28); }
  x.font = font(fam, size); x.textAlign = 'center'; x.letterSpacing = (o.ls || 2) + 'px';
  lines.forEach((l, i) => x.fillText(l, w / 2, 22 + size * .86 + i * size * 1.05));
  // ink wear
  x.globalCompositeOperation = 'destination-out';
  const r = rng(lines.join('').length * 7 + 3), n = noiseFactory(5);
  for (let i = 0; i < 900; i++) { x.globalAlpha = r() * .8; x.fillRect(r() * w, r() * h, r() * 2.5 + .5, r() * 2.5 + .5); }
  x.globalAlpha = 1;
  for (let i = 0; i < 30; i++) { x.globalAlpha = .35; x.beginPath(); x.ellipse(r() * w, r() * h, r() * 22 + 4, r() * 6 + 2, r() * 3, 0, 7); x.fill(); }
  const res = { c, w, h }; cache[key] = res; return res;
}
function stamp(ctx, st, x, y, p, rot = 0, sc = 1) {
  if (p <= 0) return;
  const s = lerp(2.6, 1, E.out(clamp(p * 1.4))) * sc;
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s);
  ctx.globalAlpha *= clamp(p * 2.5) * .92; ctx.globalCompositeOperation = 'multiply';
  ctx.drawImage(st.c, -st.w / 2, -st.h / 2, st.w, st.h); ctx.restore();
}

// ---------- shapes ----------
function rr(c, x, y, w, h, r) { c.beginPath(); c.roundRect(x, y, w, h, r); }
function shade(c, x0, y0, x1, y1, stops) { const g = c.createLinearGradient(x0, y0, x1, y1); stops.forEach(([o, col]) => g.addColorStop(o, col)); return g; }
function radial(c, x, y, r0, r1, stops) { const g = c.createRadialGradient(x, y, r0, x, y, r1); stops.forEach(([o, col]) => g.addColorStop(o, col)); return g; }
function softShadow(c, x, y, rx, ry, a = .5) { c.save(); c.fillStyle = radial(c, 0, 0, 0, 1, [[0, `rgba(0,0,0,${a})`], [1, 'rgba(0,0,0,0)']]); c.translate(x, y); c.scale(rx, ry); c.beginPath(); c.arc(0, 0, 1, 0, 7); c.fill(); c.restore(); }
