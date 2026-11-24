// ===================== 2D map & paper overlays =====================
import { LAND, W, H, lerp, clamp, ease, mapProj, flameIcon } from './lib3.js';
export const proj = (lon0, lon1, lat0, lat1) => mapProj(lon0, lon1, lat0, lat1, 0, 0, W, H);
const feats = () => LAND.features;
export function pathFeature(c, pr, f, dx = 0, dy = 0) { const polys = f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates; c.beginPath(); polys.forEach(poly => poly.forEach(ring => { ring.forEach(([lon, lat], i) => { const [x, y] = pr(lon, lat); i ? c.lineTo(x + dx, y + dy) : c.moveTo(x + dx, y + dy); }); c.closePath(); })); }
export function pathPoly(c, pr, pts, dx = 0, dy = 0) { c.beginPath(); pts.forEach(([lon, lat], i) => { const [x, y] = pr(lon, lat); i ? c.lineTo(x + dx, y + dy) : c.moveTo(x + dx, y + dy); }); c.closePath(); }
export const byName = n => feats().find(f => f.properties && f.properties.name === n);
export function paper(c, o = {}) { c.fillStyle = o.sea || '#3a4a56'; c.fillRect(0, 0, W, H); }
export function baseLand(c, pr, o = {}) { feats().forEach(f => { pathFeature(c, pr, f); c.fillStyle = o.land || '#b8a888'; c.fill(); if (o.borders !== false) { c.strokeStyle = 'rgba(60,45,30,.35)'; c.lineWidth = 1; c.stroke(); } }); }
export function vignette(c, a = .65) { const g = c.createRadialGradient(W / 2, H / 2, H * .3, W / 2, H / 2, W * .7); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(10,6,2,${a})`); c.fillStyle = g; c.fillRect(0, 0, W, H);
  c.globalAlpha = .08; for (let i = 0; i < 60; i++) { c.fillStyle = i % 2 ? '#fff' : '#000'; c.fillRect((i * 733) % W, (i * 397) % H, 3, 3); } c.globalAlpha = 1; }
export function label(c, s, x, y, size = 30, col = '#f2e8d2', a = 1, align = 'center') { c.save(); c.globalAlpha = a; c.fillStyle = col; c.font = `700 ${size}px Cinzel, serif`; c.textAlign = align; c.shadowColor = 'rgba(0,0,0,.7)'; c.shadowBlur = 10; c.fillText(s, x, y); c.restore(); }
export function title(c, s1, s2, a) { c.save(); c.globalAlpha = a; label(c, s1, 70, 100, 44, '#f2e8d2', a, 'left'); if (s2) label(c, s2, 72, 145, 26, '#e0d0b0', a, 'left'); c.restore(); }
// Austria-Hungary (stylised from modern borders + rough extra provinces)
const GALICIA = [[18.9, 49.6], [19.8, 50.2], [21.3, 50.3], [22.6, 50.6], [24.0, 50.4], [25.6, 49.9], [26.4, 48.9], [25.2, 48.0], [24.0, 48.3], [22.6, 49.1], [21.0, 49.3], [19.5, 49.3]];
const BUKOVINA = [[25.2, 48.0], [26.4, 48.9], [26.9, 48.2], [26.0, 47.5], [25.2, 47.6]];
const TRANSYL = [[22.0, 47.6], [23.2, 47.9], [24.5, 47.9], [25.2, 47.6], [26.0, 47.5], [26.5, 46.6], [26.2, 45.6], [25.0, 45.4], [23.5, 45.3], [22.3, 45.5], [21.4, 46.2], [21.6, 47.0]];
export const AUSTRIAN = ['Austria', 'Czechia', 'Slovenia'], HUNGARIAN = ['Hungary', 'Slovakia', 'Croatia'], OTHER_AH = ['Bosnia and Herz.'];
export function ahMap(c, lt, d, mode, t) {
  const pr = proj(4, 34, 40.5, 54.5); paper(c); baseLand(c, pr, { land: '#a89878' });
  const A = '#c9b48a', Hc = '#b89a72', hi = '#e04030';
  const app = ease(clamp(lt / .8));
  const fillF = (n, col, a = 1) => { const f = byName(n); if (!f) return; c.globalAlpha = a; pathFeature(c, pr, f); c.fillStyle = col; c.fill(); c.globalAlpha = 1; };
  const fillP = (p, col) => { pathPoly(c, pr, p); c.fillStyle = col; c.fill(); };
  AUSTRIAN.forEach(n => fillF(n, A)); fillP(GALICIA, A); fillP(BUKOVINA, A); HUNGARIAN.forEach(n => fillF(n, Hc)); fillP(TRANSYL, Hc); fillF('Bosnia and Herz.', '#b0a07c');
  // outer outline
  c.strokeStyle = '#2a1a10'; c.lineWidth = 3; [...AUSTRIAN, ...HUNGARIAN, ...OTHER_AH].forEach(n => { const f = byName(n); if (f) { pathFeature(c, pr, f); c.stroke(); } }); [GALICIA, BUKOVINA, TRANSYL].forEach(p => { pathPoly(c, pr, p); c.stroke(); });
  const pulse = .55 + Math.sin(t * 5) * .2;
  if (mode === 'czech' || mode === 'both') { fillF('Czechia', hi, pulse * app); const [x, y] = pr(15.3, 49.8); label(c, 'BOHEMIA & MORAVIA', x, y + 8, 26, '#fff4e0', app); }
  if (mode === 'slovak' || mode === 'both') { fillF('Slovakia', hi, pulse * app); const [x, y] = pr(19.5, 48.7); label(c, 'SLOVAKIA', x, y + 8, 26, '#fff4e0', app); }
  const [ax, ay] = pr(13.3, 47.6), [hx, hy] = pr(19.3, 46.9); label(c, 'AUSTRIA', ax, ay + 40, 30, '#3a2614', .9); label(c, 'HUNGARY', hx, hy + 30, 30, '#3a2614', .9);
  title(c, 'AUSTRIA-HUNGARY', '1914', clamp(lt / .5)); vignette(c);
}
// the empire breaks apart into its peoples
export function ahBreak(c, lt, d, t) { const pr = proj(4, 34, 40.5, 54.5); paper(c); baseLand(c, pr, { land: '#a89878' });
  const s = ease(clamp((lt - 1.2) / (d - 1.6))), ctr = pr(18, 47.5);
  const pieces = [['Austria', '#c9b48a'], ['Czechia', '#e04030'], ['Slovenia', '#c4aa80'], ['Hungary', '#b89a72'], ['Slovakia', '#e04030'], ['Croatia', '#c0a070'], ['Bosnia and Herz.', '#b0a07c'], [GALICIA, '#cfb890'], [TRANSYL, '#bfa078'], [BUKOVINA, '#c8b088']];
  pieces.forEach(([n, col], i) => { let cx0, cy0; if (typeof n === 'string') { const f = byName(n); if (!f) return; const b = bbox(f, pr); cx0 = b[0]; cy0 = b[1]; } else { const xs = n.map(p => pr(...p)); cx0 = xs.reduce((a, p) => a + p[0], 0) / xs.length; cy0 = xs.reduce((a, p) => a + p[1], 0) / xs.length; }
    const dx = (cx0 - ctr[0]) * s * .35, dy = (cy0 - ctr[1]) * s * .35;
    c.save(); c.shadowColor = 'rgba(0,0,0,.6)'; c.shadowBlur = 25 * s; c.shadowOffsetY = 10 * s; typeof n === 'string' ? pathFeature(c, pr, byName(n), dx, dy) : pathPoly(c, pr, n, dx, dy); c.fillStyle = col; c.fill(); c.restore(); c.strokeStyle = '#2a1a10'; c.lineWidth = 2.5; c.stroke(); });
  // cracks flash before the split
  if (lt > .6 && lt < 1.4) { c.strokeStyle = `rgba(255,240,210,${1 - Math.abs(lt - 1.0) * 2.5})`; c.lineWidth = 4; c.beginPath(); const r = mulberry(7); for (let k = 0; k < 7; k++) { let [x, y] = ctr; c.moveTo(x, y); for (let j = 0; j < 6; j++) { x += (r() - .5) * 90; y += (r() - .5) * 90; c.lineTo(x, y); } } c.stroke(); }
  title(c, 'THE HABSBURG EMPIRE', 'A STATE OF MANY PEOPLES', clamp(lt / .5)); vignette(c); }
function bbox(f, pr) { let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9; const polys = f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates; polys.forEach(p => p[0].forEach(([lo, la]) => { const [x, y] = pr(lo, la); x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); })); return [(x0 + x1) / 2, (y0 + y1) / 2]; }
export function mulberry(a) { return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
// route with stops (lon,lat,name); draws progressively
export function routeStops(c, pr, stops, p, t, o = {}) {
  const pts = stops.map(([lon, lat, n]) => [n, ...pr(lon, lat)]), prog = p * (pts.length - 1);
  c.strokeStyle = o.col || '#c8241c'; c.lineWidth = o.w || 6; c.setLineDash(o.dash || [14, 9]); c.lineCap = 'round'; c.shadowColor = 'rgba(0,0,0,.5)'; c.shadowBlur = 8; c.beginPath();
  for (let i = 0; i <= Math.floor(prog); i++) { const [, x, y] = pts[i]; i ? c.lineTo(x, y) : c.moveTo(x, y); } const fi = Math.floor(prog), fr = prog - fi; if (fi < pts.length - 1) c.lineTo(lerp(pts[fi][1], pts[fi + 1][1], fr), lerp(pts[fi][2], pts[fi + 1][2], fr)); c.stroke(); c.setLineDash([]); c.shadowBlur = 0;
  pts.forEach(([n, x, y], i) => { if (i <= prog + .02) { c.fillStyle = o.dot || '#f2e8d2'; c.strokeStyle = '#2a1a10'; c.lineWidth = 3; c.beginPath(); c.arc(x, y, 9, 0, 7); c.fill(); c.stroke(); if (n) label(c, n, x + (o.lx || 0), y + (o.ly ?? 38), o.size || 24, '#fff4e0'); } });
  if (o.head && fi < pts.length - 1) { const x = lerp(pts[fi][1], pts[fi + 1][1], fr), y = lerp(pts[fi][2], pts[fi + 1][2], fr); flameIcon(c, x, y, .7, t); }
}
// newspaper spinning in
export function newspaper(c, lt, head, sub, o = {}) { const s = ease(clamp(lt / (o.spin || .9))), ang = (1 - s) * 6.5 + (o.tilt || -.06), sc = lerp(.1, o.scale || .78, s);
  c.save(); c.translate(W / 2 + (o.dx || 0), H / 2 + (o.dy || 0)); c.rotate(ang); c.scale(sc, sc); const w = 1100, h = 1300;
  c.shadowColor = 'rgba(0,0,0,.6)'; c.shadowBlur = 40; c.fillStyle = '#ece2c8'; c.fillRect(-w / 2, -h / 2, w, h); c.shadowBlur = 0;
  c.fillStyle = '#1e1810'; c.textAlign = 'center'; c.font = '700 64px DejaVu Serif, serif'; c.fillText(o.paper || 'THE DAILY CHRONICLE', 0, -h / 2 + 100); c.fillRect(-w / 2 + 40, -h / 2 + 125, w - 80, 4); c.font = '22px DejaVu Serif, serif'; c.fillText(o.date || '1918', 0, -h / 2 + 160); c.fillRect(-w / 2 + 40, -h / 2 + 175, w - 80, 2);
  c.font = '900 92px DejaVu Serif, serif'; (Array.isArray(head) ? head : [head]).forEach((l, i) => c.fillText(l, 0, -h / 2 + 290 + i * 100));
  c.font = 'italic 40px DejaVu Serif, serif'; (Array.isArray(sub) ? sub : [sub]).forEach((l, i) => c.fillText(l, 0, -h / 2 + 520 + i * 50));
  c.fillStyle = 'rgba(30,24,16,.55)'; for (let col = 0; col < 3; col++) for (let ln = 0; ln < 22; ln++) c.fillRect(-w / 2 + 50 + col * 340, -h / 2 + 640 + ln * 26, 300 - ((ln * 37 + col * 13) % 60), 9);
  c.fillStyle = '#9a9488'; c.fillRect(w / 2 - 380, -h / 2 + 640, 330, 240); c.restore(); }
// typed document / telegram
export function documentPage(c, lt, lines, o = {}) { const a = clamp(lt / .4); c.save(); c.globalAlpha = a; c.translate(W / 2, H / 2); c.rotate(o.tilt || .02); const w = o.w || 900, h = o.h || 620; c.shadowColor = 'rgba(0,0,0,.6)'; c.shadowBlur = 30; c.fillStyle = o.bg || '#e8dcc0'; c.fillRect(-w / 2, -h / 2, w, h); c.shadowBlur = 0;
  c.fillStyle = '#2a2018'; c.textAlign = 'left'; const chars = Math.floor((lt - .3) * (o.cps || 40)); let used = 0;
  lines.forEach(([s, size, bold], i) => { const n = Math.max(0, Math.min(s.length, chars - used)); used += s.length; c.font = `${bold ? '700 ' : ''}${size || 30}px DejaVu Sans Mono, monospace`; c.fillText(s.slice(0, n), -w / 2 + 60, -h / 2 + 90 + i * ((size || 30) * 1.6)); });
  if (o.stamp && lt > o.stamp[0]) { const k = clamp((lt - o.stamp[0]) / .15), sc = lerp(2.2, 1, k); c.save(); c.translate(o.stamp[2] || 150, o.stamp[3] || 150); c.rotate(-.18); c.scale(sc, sc); c.globalAlpha = a * k * .85; c.strokeStyle = '#b01a10'; c.lineWidth = 8; c.strokeRect(-230, -60, 460, 120); c.fillStyle = '#b01a10'; c.font = '900 64px DejaVu Sans, sans-serif'; c.textAlign = 'center'; c.fillText(o.stamp[1], 0, 22); c.restore(); }
  c.restore(); }
