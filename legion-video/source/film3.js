import * as L from './lib3.js';
const q = new URLSearchParams(location.search), sec = q.get('sec') || '1';
window.READY = (async () => {
  const ff = new FontFace('Cinzel', 'url(Cinzel.woff2)'); await ff.load(); document.fonts.add(ff);
  const topo = await (await fetch('countries-50m.json')).json(); L.setLand(window.topojson.feature(topo, topo.objects.countries));
  const TL = await (await fetch('tl6.json')).json();
  L.setRifle(await L.model('bolt_action_rifle_7_62')); L.initLowRifle();
  const mod = await import(`./sec${sec}.js`);
  await mod.build(TL.shots); L.toonify(); await Promise.all(L.TEXP); await new Promise(r => setTimeout(r, 300));
  const { f0, f1 } = L.makeRunner(TL.shots, mod.SHOTS, mod.RANGE);
  return { f0, f1, frames: f1 - f0 };
})();
