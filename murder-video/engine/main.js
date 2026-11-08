// Frame-accurate renderer: given a timeline, renders frame N (3D at low res + 2D caption layer at 1080x1920)
'use strict';

const OW = 1080, OH = 1920, RW = 720, RH = 1280;
let TL = null;
const gl = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
gl.shadowMap.enabled = true;
gl.shadowMap.type = THREE.PCFSoftShadowMap;
gl.outputEncoding = THREE.sRGBEncoding;
gl.toneMapping = THREE.ACESFilmicToneMapping;
gl.toneMappingExposure = 1.05;
gl.setPixelRatio(1);
gl.setSize(RW, RH);
const out = document.createElement('canvas'); out.width = OW; out.height = OH;
document.body.appendChild(out);
const ctx = out.getContext('2d');
const camera = new THREE.PerspectiveCamera(50, RW / RH, 0.05, 300);

const setCache = {}, chars = {};
const bloom = document.createElement('canvas'); bloom.width = 90; bloom.height = 160; const bctx = bloom.getContext('2d');
function getSet(name, variant) {
  const k = name + ':' + (variant || '');
  if (!setCache[k]) {
    const set = SETS[name](variant);
    let sun = null;
    set.scene.traverse(o => {
      if (o.isDirectionalLight && !sun) sun = o;
      if (o.isMesh) { const m = o.material; const basic = m && (m.isMeshBasicMaterial || m.transparent); o.castShadow = !basic; o.receiveShadow = !(m && m.isMeshBasicMaterial); }
    });
    if (sun) {
      sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
      const c = sun.shadow.camera; c.left = c.bottom = -5; c.right = c.top = 5; c.near = 0.5; c.far = 40;
      sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.02; sun.shadow.radius = 4;
      sun.target.position.set(0, 0, 0); set.scene.add(sun.target);
    }
    setCache[k] = set;
  }
  return setCache[k];
}
function getChar(id) {
  if (!chars[id]) chars[id] = makeCharacter(id, TL.cast[id], Object.keys(chars).length * 17 + 5);
  return chars[id];
}

// ------------------------------------------------------------ helpers
const ease = x => 0.5 - 0.5 * Math.cos(Math.PI * Math.min(1, Math.max(0, x)));
const lerp = (a, b, k) => a + (b - a) * k;
const lerp3 = (a, b, k) => [lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k)];
const V = a => new THREE.Vector3(a[0], a[1], a[2]);
const wrapAng = a => { while (a > Math.PI) a -= 2 * Math.PI; while (a < -Math.PI) a += 2 * Math.PI; return a; };

function shotAt(t) { for (const s of TL.shots) if (t < s.end) return s; return TL.shots[TL.shots.length - 1]; }

function talkAmp(id, t) {
  let amp = 0;
  for (const l of TL.lines) {
    if (l.who !== id) continue;
    const k = Math.floor((t - l.start) * TL.fps);
    if (k >= 0 && k < l.env.length) amp = l.env[k];
  }
  return amp;
}
function talkLevel(id, t) { // slow-moving "is talking" for gestures
  let s = 0; for (let i = 0; i < 12; i++) s += talkAmp(id, t - i / TL.fps) > 0.05 ? 1 : 0; return s / 12;
}

function animAt(actor, p) {
  if (!Array.isArray(actor.anim)) return { a: actor.anim || 'idle', prev: null, k: 1 };
  let cur = actor.anim[0], prev = null;
  for (const kf of actor.anim) if (p >= kf.at) { prev = cur; cur = kf; }
  if (prev === cur) prev = null;
  return { a: cur.anim, prev: prev ? prev.anim : null, since: cur.at };
}

function keyDown(shot, t) {
  if (!shot.morse) return false;
  for (const [a, b] of shot.morse) if (t >= a && t < b) return true;
  return false;
}

// ------------------------------------------------------------ scene setup + posing
let curShot = null, curSet = null;
function setupShot(shot) {
  if (curSet) for (const id in chars) if (chars[id].P.root.parent === curSet.scene) curSet.scene.remove(chars[id].P.root);
  curSet = getSet(shot.set, shot.variant);
  for (const a of shot.actors || []) {
    const ch = getChar(a.id);
    curSet.scene.add(ch.P.root);
    for (const k in ch.P.props) ch.P.props[k].visible = false;
  }
  curShot = shot;
}

function poseActors(shot, t) {
  const lt = t - shot.start, dur = shot.end - shot.start, p = lt / dur;
  const kd = keyDown(shot, t);
  for (const a of shot.actors || []) {
    const ch = getChar(a.id), root = ch.P.root;
    let anim;
    if (a.walk) {
      const t0 = a.walk.t0 || 0, t1 = a.walk.t1 || 1;
      const k = Math.min(1, Math.max(0, (p - t0) / (t1 - t0)));
      const from = a.walk.from, to = a.walk.to;
      root.position.set(lerp(from[0], to[0], k), 0, lerp(from[1], to[1], k));
      root.rotation.y = Math.atan2(to[0] - from[0], to[1] - from[1]);
      const dist = Math.hypot(to[0] - from[0], to[1] - from[1]) * k;
      ch.walkPhase = dist / (0.36 * (TL.cast[a.id].height || 1));
      anim = { a: k < 1 && k > 0 ? 'walk' : 'idle', prev: null };
    } else {
      root.position.set(a.pos[0], 0, a.pos[1]);
      root.rotation.y = (a.face || 0) * Math.PI / 180;
      anim = animAt(a, p);
    }
    let pose = poseFor(anim.a, t, ch);
    if (anim.prev) {
      const k = Math.min(1, (lt - anim.since * dur) / 0.3);
      if (k < 1) pose = lerpPose(poseFor(anim.prev, t, ch), pose, ease(k));
    }
    if (anim.a === 'type') { const tap = kd ? 0.14 : 0; pose.aRx -= tap; pose.fR += tap; }
    // talking overlay
    const amp = talkAmp(a.id, t);
    const lvl = talkLevel(a.id, t);
    ch.talkSmooth = lvl;
    const busy = /kneel|binoculars|type|walk|admire/.test(anim.a);
    if (!busy) { pose.aRx -= 0.35 * lvl + 0.12 * lvl * Math.sin(t * 2.3); pose.fR -= 0.55 * lvl; pose.aRz += 0.1 * lvl; }
    pose.headX += 0.05 * amp * Math.sin(t * 9);
    // look-at
    let headYaw = 0, headPitch = 0, torsoYaw = 0, eyeYaw = 0, eyePitch = 0;
    if (a.look && pose.lookAmt > 0) {
      let target;
      if (a.look === 'cam') target = camera.position.clone();
      else if (chars[a.look] && chars[a.look].P.root.parent === curSet.scene) { const o = chars[a.look]; o.P.root.updateMatrixWorld(true); target = o.P.head.getWorldPosition(new THREE.Vector3()); }
      if (target) {
        root.updateMatrixWorld(true);
        const hp = ch.P.head.getWorldPosition(new THREE.Vector3());
        const yaw = wrapAng(Math.atan2(target.x - hp.x, target.z - hp.z) - root.rotation.y);
        const cl = Math.max(-1.3, Math.min(1.3, yaw));
        torsoYaw = cl * 0.3 * pose.lookAmt; headYaw = cl * 0.65 * pose.lookAmt;
        const dy = target.y - hp.y, dh = Math.hypot(target.x - hp.x, target.z - hp.z);
        headPitch = -Math.atan2(dy, dh) * 0.5 * pose.lookAmt;
        eyeYaw = Math.max(-0.35, Math.min(0.35, yaw * 0.3)); eyePitch = headPitch * 0.6;
      }
    }
    // blink
    const per = 3.1 + (ch.seed % 7) * 0.31, ph = (t + ch.seed * 0.37) % per;
    const blink = ph < 0.12;
    const sit = /sit|type/.test(anim.a) || (Array.isArray(a.anim) && a.anim.some(k => /sit/.test(k.anim)));
    applyPose(ch, pose, { talk: amp, blink, headYaw, headPitch, torsoYaw, eyeYaw, eyePitch, chair: sit });
    // props
    const PR = ch.P.props;
    PR.crowbar.visible = anim.a === 'kneel_dig';
    PR.lantern.visible = anim.a === 'kneel_shocked';
    PR.binoculars.visible = anim.a === 'binoculars';
    PR.paper.visible = anim.a === 'hold_paper';
    if (ch.P.brooch && TL.cast[a.id].broochGlow) ch.P.brooch.material.emissiveIntensity = 0.6 + 0.4 * Math.sin(t * 6);
  }
}

function placeCamera(shot, t) {
  const lt = t - shot.start, dur = shot.end - shot.start, p = ease(lt / dur);
  const c = shot.cam;
  let pos, look, fov = c.fov || 50;
  if (c.focus) {
    const ch = getChar(c.focus);
    ch.P.root.updateMatrixWorld(true);
    const hp = ch.P.head.getWorldPosition(new THREE.Vector3());
    hp.y += 0.12 * (TL.cast[c.focus].height || 1);
    const d = Array.isArray(c.dist) ? lerp(c.dist[0], c.dist[1], p) : (c.dist || 1);
    const ang = ch.P.root.rotation.y + (c.yaw || 0) * Math.PI / 180;
    pos = [hp.x + Math.sin(ang) * d, hp.y + (c.dy || 0), hp.z + Math.cos(ang) * d];
    look = [hp.x, hp.y - 0.24, hp.z];
    fov = c.fov || 40;
  } else {
    pos = lerp3(c.from, c.to || c.from, p);
    look = lerp3(c.look, c.lookTo || c.look, p);
  }
  // handheld drift
  const sh = c.shake === undefined ? 1 : c.shake;
  pos[0] += Math.sin(t * 0.9) * 0.012 * sh; pos[1] += Math.sin(t * 1.3 + 1) * 0.008 * sh;
  look[0] += Math.sin(t * 0.7 + 2) * 0.01 * sh;
  camera.fov = fov; camera.updateProjectionMatrix();
  camera.position.set(pos[0], pos[1], pos[2]);
  camera.lookAt(V(look));
}

// ------------------------------------------------------------ 2D overlay (captions in the pixel style)
function pixelText(text, x, y, size, opts = {}) {
  ctx.font = `${size}px Pixel`;
  ctx.textAlign = opts.align || 'center'; ctx.textBaseline = 'middle';
  const o = Math.max(3, Math.round(size * (opts.outline || 0.16)));
  ctx.fillStyle = 'rgba(0,0,0,0.55)';
  for (let dx = -o; dx <= o; dx += Math.ceil(o / 2)) for (let dy = -o; dy <= o; dy += Math.ceil(o / 2)) ctx.fillText(text, x + dx + o * 0.7, y + dy + o * 0.9);
  ctx.fillStyle = '#000';
  for (let dx = -o; dx <= o; dx += Math.ceil(o / 3)) for (let dy = -o; dy <= o; dy += Math.ceil(o / 3)) ctx.fillText(text, x + dx, y + dy);
  ctx.fillStyle = opts.color || '#fff';
  ctx.fillText(text, x, y);
}
function wrapLines(text, size, maxW) {
  ctx.font = `${size}px Pixel`;
  const words = text.split(' '), lines = []; let cur = '';
  for (const w of words) { const c = cur ? cur + ' ' + w : w; if (ctx.measureText(c).width > maxW && cur) { lines.push(cur); cur = w; } else cur = c; }
  if (cur) lines.push(cur);
  return lines;
}

function magnifier(x, y, s, color) {
  ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = s * 0.14; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.arc(x - s * 0.1, y - s * 0.1, s * 0.32, 0, Math.PI * 2); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(x + s * 0.13, y + s * 0.13); ctx.lineTo(x + s * 0.42, y + s * 0.42); ctx.stroke();
  ctx.restore();
}

const grain = (() => { const c = document.createElement('canvas'); c.width = 270; c.height = 480; const g = c.getContext('2d'); const d = g.createImageData(270, 480); const R = makeRng(5); for (let i = 0; i < d.data.length; i += 4) { const v = R() * 255; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; } g.putImageData(d, 0, 0); return c; })();
const vignette = (() => { const c = document.createElement('canvas'); c.width = OW; c.height = OH; const g = c.getContext('2d'); const gr = g.createRadialGradient(OW / 2, OH * 0.45, OH * 0.25, OW / 2, OH * 0.5, OH * 0.75); gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, 'rgba(0,0,0,0.42)'); g.fillStyle = gr; g.fillRect(0, 0, OW, OH); return c; })();

function overlay(shot, t, frame) {
  const lt = t - shot.start, dur = shot.end - shot.start;
  ctx.drawImage(vignette, 0, 0);
  ctx.save(); ctx.globalAlpha = 0.045; ctx.globalCompositeOperation = 'overlay';
  ctx.drawImage(grain, (frame * 37) % 60 - 60, (frame * 53) % 80 - 80, OW + 120, OH + 160); ctx.restore();

  // watermark (like the handle in the reference)
  if (shot.overlay !== 'endcard') {
    ctx.save(); ctx.globalAlpha = 0.85;
    magnifier(OW * 0.885, OH * 0.235, 46, '#fff');
    ctx.font = '26px Oswald'; ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.shadowColor = 'rgba(0,0,0,0.7)'; ctx.shadowBlur = 6;
    ctx.fillText(TL.handle || '', OW * 0.885, OH * 0.235 + 52);
    ctx.restore();
  }

  // location / date stamp (typewriter)
  if (shot.stamp && lt < 3.6) {
    const n = Math.floor(Math.max(0, lt - 0.15) * 30);
    const full = shot.stamp; const shown = full.slice(0, n);
    const lines = shown.split('\n');
    const a = lt > 3.1 ? 1 - (lt - 3.1) / 0.5 : 1;
    ctx.save(); ctx.globalAlpha = a;
    const fullLines = full.split('\n');
    ctx.font = '28px Pixel';
    const w = Math.max(...fullLines.map(l => ctx.measureText(l).width)) + 48;
    ctx.fillStyle = 'rgba(0,0,0,0.6)'; ctx.fillRect(56, 300, w, fullLines.length * 46 + 30);
    ctx.fillStyle = '#c0392b'; ctx.fillRect(56, 300, 8, fullLines.length * 46 + 30);
    lines.forEach((l, i) => pixelText(l, 88, 338 + i * 46, 28, { align: 'left', color: '#f3e6b0', outline: 0.08 }));
    if (n < full.length || (Math.floor(lt * 3) % 2 === 0)) {
      const last = lines[lines.length - 1]; ctx.font = '28px Pixel';
      ctx.fillStyle = '#f3e6b0'; ctx.fillRect(90 + ctx.measureText(last).width + 4, 322 + (lines.length - 1) * 46, 20, 30);
    }
    ctx.restore();
  }

  // telegram overlay
  if (shot.telegram) {
    const k = Math.min(1, Math.max(0, (lt - 0.3) / (dur * 0.8)));
    const txt = shot.telegram.slice(0, Math.floor(shot.telegram.length * k));
    ctx.save(); ctx.translate(OW / 2, 600); ctx.rotate(-0.03);
    ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.fillRect(-440 + 12, -170 + 14, 880, 400);
    ctx.fillStyle = '#efe4c6'; ctx.fillRect(-440, -170, 880, 400);
    ctx.fillStyle = '#8a2a1a'; ctx.font = '22px Pixel'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('MARCONI WIRELESS TELEGRAM', 0, -130);
    ctx.fillRect(-400, -105, 800, 4);
    ctx.fillStyle = '#2a2018'; ctx.font = '22px Pixel'; ctx.textAlign = 'left';
    const lines = []; let cur = '';
    for (const w of txt.split(' ')) { const c = cur ? cur + ' ' + w : w; if (ctx.measureText(c).width > 780 && cur) { lines.push(cur); cur = w; } else cur = c; }
    lines.push(cur);
    lines.forEach((l, i) => ctx.fillText(l, -390, -65 + i * 38));
    ctx.restore();
  }

  // main captions: only the most recent chunk is shown (no overlaps)
  let cur = null;
  for (const l of TL.lines) {
    if (l.shot !== shot.index) continue;
    for (const c of l.chunks) if (t >= c.start - 0.03 && t < c.end + 0.25) { if (!cur || c.start > cur.c.start) cur = { c, l }; }
  }
  if (cur) {
    if (cur.l.big) {
      const ls = wrapLines(cur.c.text, 58, 900);
      ls.forEach((s, i) => pixelText(s, OW / 2, OH * 0.6 + (i - (ls.length - 1) / 2) * 84, 58, { color: '#ffe14d' }));
    } else {
      const ls = wrapLines(cur.c.text, 44, 960);
      ls.forEach((s, i) => pixelText(s, OW / 2, OH * 0.655 + i * 64, 44));
    }
  }
  if (shot.sub === 'hook' && TL.hook) {
    const ls = wrapLines(TL.hook, 22, 900);
    ls.forEach((s, i) => pixelText(s, OW / 2, OH * 0.655 + 92 + i * 34, 22, { outline: 0.2 }));
  }

  // end card
  if (shot.overlay === 'endcard') {
    const a = Math.min(1, lt / 0.6);
    ctx.fillStyle = `rgba(0,0,0,${0.72 * a})`; ctx.fillRect(0, 0, OW, OH);
    ctx.save(); ctx.globalAlpha = a;
    (TL.endcard || []).forEach((s, i) => pixelText(s, OW / 2, OH * 0.36 + i * 70, 48));
    magnifier(OW / 2, OH * 0.5, 130, '#fff');
    ctx.font = '44px Oswald'; ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(TL.handle || '', OW / 2, OH * 0.5 + 130);
    ctx.restore();
  }

  // transitions
  const fx = shot.fx || [];
  if (fx.includes('fadein') && lt < 1.0) { ctx.fillStyle = `rgba(0,0,0,${1 - lt / 1.0})`; ctx.fillRect(0, 0, OW, OH); }
  if (fx.includes('flash') && lt < 0.35) { ctx.fillStyle = `rgba(255,255,255,${0.85 * (1 - lt / 0.35)})`; ctx.fillRect(0, 0, OW, OH); }
  if (fx.includes('fadeout') && dur - lt < 1.2) { ctx.fillStyle = `rgba(0,0,0,${1 - (dur - lt) / 1.2})`; ctx.fillRect(0, 0, OW, OH); }
}

// ------------------------------------------------------------ public API used by tools/render.js
window.init = async (timeline) => {
  TL = timeline;
  await document.fonts.load('40px Pixel'); await document.fonts.load('30px Oswald');
  for (const s of TL.shots) { getSet(s.set, s.variant); for (const a of s.actors || []) getChar(a.id); }
  return { frames: Math.ceil(TL.duration * TL.fps) };
};

window.renderFrame = (frame, quality = 0.9) => {
  const t = frame / TL.fps;
  const shot = shotAt(t);
  if (shot !== curShot) setupShot(shot);
  poseActors(shot, t);
  placeCamera(shot, t);
  poseActors(shot, t); // second pass so "look: cam" uses this frame's camera
  curSet.update(t, { keyDown: keyDown(shot, t), shot });
  gl.render(curSet.scene, camera);
  ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
  ctx.filter = 'saturate(0.88) contrast(1.04)';
  ctx.drawImage(gl.domElement, 0, 0, OW, OH);
  ctx.filter = 'none';
  // soft glow (the hazy cutscene look)
  bctx.filter = 'brightness(0.85) contrast(1.8) saturate(1.2)';
  bctx.drawImage(gl.domElement, 0, 0, bloom.width, bloom.height);
  ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.globalAlpha = 0.22;
  ctx.drawImage(bloom, 0, 0, OW, OH); ctx.restore();
  overlay(shot, t, frame);
  return out.toDataURL('image/jpeg', quality);
};
