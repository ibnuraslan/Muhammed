// ===================== laomaps.js: 2D maps and graphics for the Laos film =====================
import * as L from './lib3.js';
import * as M from './maps.js';
const { W, H, lerp, clamp, ease } = L;
export const CITY = { Vientiane: [102.6, 17.97], 'Luang Prabang': [102.13, 19.89], 'Xieng Khouang': [103.2, 19.45], Viengxay: [104.23, 20.42], Savannakhet: [104.75, 16.55], Pakse: [105.8, 15.12], Tchepone: [106.22, 16.69], Attapeu: [106.83, 14.81], Hanoi: [105.85, 21.03], Saigon: [106.7, 10.8], Bangkok: [100.5, 13.75], 'Phnom Penh': [104.9, 11.55] };
// projection with correct aspect: centre lon/lat and vertical span in degrees
export function view(lon, lat, span) { const k = Math.cos(lat * Math.PI / 180), hs = span / 2, ws = span * W / H / k / 2; return M.proj(lon - ws, lon + ws, lat - hs, lat + hs); }
export function viewLerp(a, b, p) { return view(lerp(a[0], b[0], p), lerp(a[1], b[1], p), Math.exp(lerp(Math.log(a[2]), Math.log(b[2]), p))); }
export const TRAIL = [[[105.9, 18.3], [105.65, 17.6], [105.9, 17.1], [106.22, 16.69], [106.45, 16.0], [106.6, 15.4], [106.83, 14.81], [107.15, 14.1], [107.3, 13.3], [107.1, 12.5], [106.85, 11.6], [106.7, 11.1]],
  [[106.4, 17.6], [106.25, 17.1], [106.22, 16.69]], [[106.22, 16.69], [106.7, 16.4], [107.2, 16.2]], [[106.45, 16.0], [106.9, 15.8], [107.4, 15.6]], [[107.15, 14.1], [107.6, 14.2], [108.0, 14.0]], [[106.83, 14.81], [106.5, 14.2], [106.1, 13.4], [105.9, 12.6]], [[105.65, 17.6], [105.2, 17.0], [105.4, 16.3], [106.0, 15.8], [106.45, 16.0]]];
export function base(c, pr, o = {}) { M.paper(c, { sea: o.sea || '#2e3e4a' }); M.baseLand(c, pr, { land: o.land || '#b8a888' });
  (o.hl || []).forEach(([n, col, a = 1]) => { const f = M.byName(n); if (!f) return; c.save(); c.globalAlpha = a; M.pathFeature(c, pr, f); c.fillStyle = col; c.fill(); c.restore(); }); }
export function outline(c, pr, name, col = '#f2e8d2', w = 4, glow = 14) { const f = M.byName(name); if (!f) return; c.save(); M.pathFeature(c, pr, f); c.strokeStyle = col; c.lineWidth = w; c.shadowColor = col; c.shadowBlur = glow; c.stroke(); c.restore(); }
export function city(c, pr, n, o = {}) { const [x, y] = pr(...CITY[n]); c.save(); c.globalAlpha = o.a ?? 1; c.fillStyle = o.dot || '#f2e8d2'; c.strokeStyle = '#2a1a10'; c.lineWidth = 3; c.beginPath(); c.arc(x, y, o.r || 8, 0, 7); c.fill(); c.stroke(); c.restore(); M.label(c, (o.name || n).toUpperCase(), x + (o.dx || 0), y + (o.dy ?? -18), o.size || 22, '#fff4e0', o.a ?? 1); }
export function name(c, pr, s, lon, lat, size = 34, a = 1, col = '#f2e8d2') { const [x, y] = pr(lon, lat); M.label(c, s, x, y, size, col, a); }
export function trail(c, pr, p, o = {}) { c.save(); c.lineCap = 'round'; c.lineJoin = 'round';
  TRAIL.forEach((line, li) => { const pts = line.map(q => pr(...q)); let tot = 0; const seg = []; for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(d); tot += d; }
    const pp = clamp(p * 1.4 - li * .12), lim = pp * tot; c.strokeStyle = o.col || '#d8a030'; c.lineWidth = li ? (o.w || 5) * .7 : (o.w || 5); c.setLineDash(o.dash || []); c.shadowColor = 'rgba(0,0,0,.6)'; c.shadowBlur = 6; c.beginPath(); c.moveTo(...pts[0]); let acc = 0;
    for (let i = 1; i < pts.length; i++) { if (acc + seg[i - 1] <= lim) { c.lineTo(...pts[i]); acc += seg[i - 1]; } else { const f = (lim - acc) / seg[i - 1]; if (f > 0) c.lineTo(lerp(pts[i - 1][0], pts[i][0], f), lerp(pts[i - 1][1], pts[i][1], f)); break; } } c.stroke(); });
  c.restore(); }
// bombing intensity: weighted random points inside Laos; reveal fraction p
const HOT = [[103.2, 19.45, .55, .26], [104.1, 20.3, .45, .12], [102.4, 19.6, .5, .06], [105.3, 15.6, .6, .06]];
let PTS = null; function genPts() { const r = M.mulberry(11), out = [], f = M.byName('Laos'); const cv = document.createElement('canvas'); cv.width = 1000; cv.height = 1000; const x = cv.getContext('2d'); const pr = M.proj(100, 108, 13.8, 22.6).bind ? null : null;
  const p2 = (lon, lat) => [(lon - 100) / 8 * 1000, (22.6 - lat) / 8.8 * 1000]; M.pathFeature(x, p2, f);
  const gauss = () => { let u = 0; for (let i = 0; i < 4; i++) u += r(); return (u - 2) / .58; };
  let n = 0; while (out.length < 2600 && n++ < 60000) { const k = r(); let lon, lat;
    if (k < .5) { const line = TRAIL[0]; const i = Math.floor(r() * (line.length - 1)), f2 = r(); lon = lerp(line[i][0], line[i + 1][0], f2) - Math.abs(gauss()) * .45; lat = lerp(line[i][1], line[i + 1][1], f2) + gauss() * .15; }
    else if (k < .96) { let acc = .5, h = HOT[0]; for (const hh of HOT) { acc += hh[3]; if (k < acc) { h = hh; break; } } lon = h[0] + gauss() * h[2]; lat = h[1] + gauss() * h[2] * .8; }
    else { lon = 100 + r() * 8; lat = 13.8 + r() * 8.8; }
    const [px, py] = p2(lon, lat); if (x.isPointInPath(px, py)) out.push([lon, lat, r()]); }
  return out; }
export function bombDots(c, pr, p, o = {}) { if (!PTS) PTS = genPts(); const n = Math.floor(PTS.length * clamp(p)); c.save(); c.globalCompositeOperation = o.op || 'source-over';
  for (let i = 0; i < n; i++) { const [lon, lat, rr] = PTS[i]; let [x, y] = pr(lon, lat); if (o.even) { const e = o.even; const [ex, ey] = pr(100.6 + ((.5 + i * 0.7548776662) % 1) * 6.4, 14.4 + ((.5 + i * 0.5698402910) % 1) * 7.6); x = lerp(x, ex, e); y = lerp(y, ey, e); }
    c.fillStyle = o.col || `rgba(${200 + rr * 55 | 0},${40 + rr * 60 | 0},20,.75)`; c.beginPath(); c.arc(x, y, o.r || 3.2, 0, 7); c.fill(); }
  c.restore(); }
export function clipLaos(c, pr, fn) { const f = M.byName('Laos'); c.save(); M.pathFeature(c, pr, f); c.clip(); fn(); c.restore(); }
export function arrow(c, a, b, p, col, w = 14, o = {}) { const [x0, y0] = a, x1 = lerp(x0, b[0], p), y1 = lerp(y0, b[1], p); if (p <= 0) return; const ang = Math.atan2(y1 - y0, x1 - x0); c.save(); c.strokeStyle = col; c.fillStyle = col; c.lineWidth = w; c.lineCap = 'round'; c.shadowColor = 'rgba(0,0,0,.6)'; c.shadowBlur = 10; c.globalAlpha = o.a ?? 1;
  c.beginPath(); c.moveTo(x0, y0); const mx = (x0 + x1) / 2 + (o.bend || 0) * -Math.sin(ang), my = (y0 + y1) / 2 + (o.bend || 0) * Math.cos(ang); c.quadraticCurveTo(mx, my, x1, y1); c.stroke();
  const an2 = Math.atan2(y1 - my, x1 - mx); c.beginPath(); c.moveTo(x1 + Math.cos(an2) * w * 1.6, y1 + Math.sin(an2) * w * 1.6); c.lineTo(x1 + Math.cos(an2 + 2.3) * w * 1.8, y1 + Math.sin(an2 + 2.3) * w * 1.8); c.lineTo(x1 + Math.cos(an2 - 2.3) * w * 1.8, y1 + Math.sin(an2 - 2.3) * w * 1.8); c.fill(); c.restore(); }
// big number card
export function counter(c, lt, value, line1, line2, o = {}) { const a = clamp(lt / .35); const k = ease(clamp(lt / (o.dur || 1.6))); const v = Math.round(value * k);
  c.save(); if (o.bg !== false) { c.fillStyle = `rgba(14,10,8,${.72 * a})`; c.fillRect(0, 0, W, H); }
  M.label(c, (o.fmt ? o.fmt(v) : v.toLocaleString('en-US')) + (o.suffix || ''), W / 2, H / 2 + (o.y || 0), o.size || 150, o.col || '#f2c050', a);
  if (line1) M.label(c, line1, W / 2, H / 2 + 80 + (o.y || 0), 40, '#f2e8d2', a); if (line2) M.label(c, line2, W / 2, H / 2 + 130 + (o.y || 0), 28, '#d8c8a8', a); c.restore(); }
export function card(c, lines, a = 1, o = {}) { c.save(); if (o.bg !== false) { c.fillStyle = `rgba(14,10,8,${(o.dim ?? .72) * a})`; c.fillRect(0, 0, W, H); } lines.forEach(([s, size, col], i) => M.label(c, s, W / 2, H / 2 + (o.y || 0) + (i - (lines.length - 1) / 2) * (size * 1.5), size, col || '#f2e8d2', a)); c.restore(); }
export function lowerThird(c, s1, s2, a) { L.caption(c, s1, s2, a); }
// dominoes across SE Asia
export function domino(c, pr, lt) { const order = [['Laos', 103.5, 19], ['Thailand', 101, 15.5], ['Cambodia', 104.8, 12.6], ['Vietnam', 106.5, 14.5], ['Myanmar', 96.5, 20], ['Malaysia', 102, 4.5]];
  order.forEach(([n, lon, lat], i) => { const [x, y] = pr(lon, lat); const fall = ease(clamp((lt - .8 - i * .55) / .5)); c.save(); c.translate(x, y + 40); c.rotate(fall * 1.2); c.fillStyle = '#f2ead8'; c.strokeStyle = '#2a1a10'; c.lineWidth = 4; c.fillRect(-22, -90, 44, 90); c.strokeRect(-22, -90, 44, 90); c.fillStyle = '#2a1a10'; for (const dy of [-70, -25]) { c.beginPath(); c.arc(0, dy, 6, 0, 7); c.fill(); } c.fillRect(-22, -48, 44, 4); c.restore(); M.label(c, n.toUpperCase(), x, y + 70, 20, '#fff4e0'); }); }
// clock: a planeload every eight minutes
export function clock(c, lt, d) { M.paper(c, { sea: '#1e1a16' }); const cx = W / 2, cy = H / 2 - 30, R = 300; c.save(); c.strokeStyle = '#e8dcc0'; c.lineWidth = 10; c.beginPath(); c.arc(cx, cy, R, 0, 7); c.stroke();
  for (let i = 0; i < 60; i++) { const a = i / 60 * Math.PI * 2 - Math.PI / 2, l = i % 5 ? 14 : 34; c.lineWidth = i % 5 ? 3 : 7; c.beginPath(); c.moveTo(cx + Math.cos(a) * (R - 8), cy + Math.sin(a) * (R - 8)); c.lineTo(cx + Math.cos(a) * (R - 8 - l), cy + Math.sin(a) * (R - 8 - l)); c.stroke(); }
  const mins = lt / d * 60 * 1.0; // one hour sweeps over the shot
  for (let k = 0; k < 8; k++) { const m = k * 8; if (m > mins) continue; const a = m / 60 * Math.PI * 2 - Math.PI / 2, age = mins - m; const px = cx + Math.cos(a) * (R + 70), py = cy + Math.sin(a) * (R + 70); c.save(); c.translate(px, py); c.rotate(a + Math.PI / 2); c.globalAlpha = clamp(age / 2); plane(c, 0, 0, 1.1, '#e85a2a'); c.restore(); }
  const ma = mins / 60 * Math.PI * 2 - Math.PI / 2; c.strokeStyle = '#f2c050'; c.lineWidth = 10; c.lineCap = 'round'; c.beginPath(); c.moveTo(cx, cy); c.lineTo(cx + Math.cos(ma) * (R - 50), cy + Math.sin(ma) * (R - 50)); c.stroke();
  c.fillStyle = '#f2c050'; c.beginPath(); c.arc(cx, cy, 14, 0, 7); c.fill(); c.restore();
  M.label(c, 'EVERY 8 MINUTES', W / 2, H - 120, 46, '#f2e8d2', clamp(lt / .4)); M.label(c, '24 HOURS A DAY  ·  FOR 9 YEARS', W / 2, H - 70, 28, '#d8c8a8', clamp((lt - 1.5) / .4)); }
export function plane(c, x, y, s = 1, col = '#2a1a10') { c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = col; c.beginPath(); c.moveTo(0, -40); c.lineTo(6, -20); c.lineTo(6, -6); c.lineTo(36, 10); c.lineTo(36, 16); c.lineTo(6, 8); c.lineTo(5, 26); c.lineTo(14, 34); c.lineTo(14, 38); c.lineTo(0, 34); c.lineTo(-14, 38); c.lineTo(-14, 34); c.lineTo(-5, 26); c.lineTo(-6, 8); c.lineTo(-36, 16); c.lineTo(-36, 10); c.lineTo(-6, -6); c.lineTo(-6, -20); c.closePath(); c.fill(); c.restore(); }
// ledger page (paper with handwritten-like rows)
export function ledger(c, lt, rows, o = {}) { const a = clamp(lt / .4); c.save(); c.fillStyle = '#1a140e'; c.fillRect(0, 0, W, H); c.globalAlpha = a; c.translate(W / 2, H / 2); c.rotate(o.tilt ?? -.015);
  const w = 1100, h = 720; c.fillStyle = o.paper || '#ece2c8'; c.shadowColor = 'rgba(0,0,0,.6)'; c.shadowBlur = 30; c.fillRect(-w / 2, -h / 2, w, h); c.shadowBlur = 0;
  c.strokeStyle = 'rgba(80,110,150,.35)'; c.lineWidth = 2; for (let y = -h / 2 + 140; y < h / 2 - 30; y += 70) { c.beginPath(); c.moveTo(-w / 2 + 40, y); c.lineTo(w / 2 - 40, y); c.stroke(); }
  c.strokeStyle = 'rgba(190,60,50,.5)'; c.beginPath(); c.moveTo(-w / 2 + 120, -h / 2); c.lineTo(-w / 2 + 120, h / 2); c.stroke();
  c.fillStyle = '#2a1a10'; c.font = '700 46px Cinzel, serif'; c.textAlign = 'left'; c.fillText(o.title || '', -w / 2 + 150, -h / 2 + 100);
  rows.forEach(([k, v], i) => { const ra = clamp((lt - .5 - i * (o.gap || .45)) / .3); c.globalAlpha = a * ra; c.font = '600 38px DejaVu Serif, serif'; c.fillStyle = '#2a1a10'; c.fillText(k, -w / 2 + 150, -h / 2 + 200 + i * 70); c.textAlign = 'right'; c.fillStyle = o.valCol || '#8a2418'; c.fillText(v, w / 2 - 70, -h / 2 + 200 + i * 70); c.textAlign = 'left'; });
  c.restore(); }
// cutaway of a karst mountain with lit chambers
export function cutaway(c, lt, o = {}) { const a = clamp(lt / .4); c.save(); c.fillStyle = '#121a20'; c.fillRect(0, 0, W, H);
  const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#1a2a3a'); g.addColorStop(1, '#2a3a2a'); c.fillStyle = g; c.fillRect(0, 0, W, H);
  c.fillStyle = '#5a5248'; c.beginPath(); c.moveTo(160, H - 120); c.bezierCurveTo(200, 300, 420, 120, 700, 150); c.bezierCurveTo(900, 60, 1200, 90, 1380, 220); c.bezierCurveTo(1620, 300, 1720, 600, 1760, H - 120); c.closePath(); c.fill();
  c.strokeStyle = '#2a2620'; c.lineWidth = 6; c.stroke(); c.fillStyle = '#3e5a2e'; c.fillRect(0, H - 120, W, 120);
  const rooms = o.rooms || [[520, 640, 'OFFICES'], [820, 520, 'SCHOOL'], [1100, 650, 'HOSPITAL'], [700, 820, 'BAKERY'], [1000, 830, 'SHOP'], [1300, 780, 'THEATRE'], [950, 380, 'HQ']];
  c.strokeStyle = '#1a1612'; c.lineWidth = 22; c.lineCap = 'round'; c.beginPath(); c.moveTo(300, H - 140); rooms.forEach(([x, y]) => c.lineTo(x, y)); c.stroke();
  rooms.forEach(([x, y, n], i) => { const ra = clamp((lt - .4 - i * (o.gap || .45)) / .3); const gl = c.createRadialGradient(x, y, 4, x, y, 90); gl.addColorStop(0, `rgba(255,200,110,${.9 * ra})`); gl.addColorStop(1, 'rgba(255,160,60,0)'); c.fillStyle = gl; c.beginPath(); c.ellipse(x, y, 110, 60, 0, 0, 7); c.fill();
    c.fillStyle = `rgba(40,30,20,${ra})`; c.beginPath(); c.ellipse(x, y, 70, 34, 0, 0, 7); c.fill(); c.fillStyle = `rgba(255,190,100,${ra})`; c.beginPath(); c.ellipse(x, y, 60, 26, 0, 0, 7); c.fill(); M.label(c, n, x, y - 50, 24, '#fff4e0', ra); });
  c.restore(); M.vignette(c, .5); }
// route diagram: home -> shelter -> hospital at night
export function journey(c, lt) { c.save(); c.fillStyle = '#0e1422'; c.fillRect(0, 0, W, H); const r = M.mulberry(5); c.fillStyle = '#e8e8f8'; for (let i = 0; i < 160; i++) { c.globalAlpha = r() * .8; c.fillRect(r() * W, r() * H * .6, 2, 2); } c.globalAlpha = 1;
  c.fillStyle = '#1e2a24'; c.beginPath(); c.moveTo(0, H * .75); for (let x = 0; x <= W; x += 40) c.lineTo(x, H * .72 + Math.sin(x * .01) * 30); c.lineTo(W, H); c.lineTo(0, H); c.fill();
  const P = [[260, 760, 'HOME'], [900, 690, 'SHELTER'], [1640, 740, 'HOSPITAL']];
  P.forEach(([x, y, n], i) => { c.fillStyle = '#f2e8d2'; c.beginPath(); c.arc(x, y, 14, 0, 7); c.fill(); M.label(c, n, x, y - 36, 30, '#fff4e0'); });
  const seg = (a, b, p, col) => { c.strokeStyle = col; c.lineWidth = 6; c.setLineDash([16, 12]); c.beginPath(); c.moveTo(a[0], a[1]); const mx = (a[0] + b[0]) / 2, my = Math.min(a[1], b[1]) - 120; const N = 30; for (let k = 1; k <= N * p; k++) { const t = k / N; c.lineTo((1 - t) * (1 - t) * a[0] + 2 * (1 - t) * t * mx + t * t * b[0], (1 - t) * (1 - t) * a[1] + 2 * (1 - t) * t * my + t * t * b[1]); } c.stroke(); c.setLineDash([]); };
  seg(P[0], P[1], clamp(lt / 1.6), '#f2c050'); seg(P[1], P[2], clamp((lt - 2) / 2), '#e85a2a');
  if (lt > 1.6) M.label(c, 'JOURNEY 1', 580, 600, 24, '#f2c050', clamp((lt - 1.6) / .3)); if (lt > 4) M.label(c, 'JOURNEY 2', 1270, 600, 24, '#e85a2a', clamp((lt - 4) / .3)); c.restore(); M.vignette(c, .4); }
