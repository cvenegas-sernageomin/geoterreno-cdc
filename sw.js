// Service worker offline-first (cache estatico)
const CACHE='geoterreno-cdc-v29';
const ASSETS=['./','./index.html','./manifest.json','./icons/icon-192.png','./icons/icon-512.png',
  './vendor/leaflet.css','./vendor/leaflet.js','./vendor/idb.js','./vendor/leaflet.offline.js',
  './vendor/georaster.browser.bundle.min.js','./vendor/georaster-layer-for-leaflet.min.js',
  './vendor/images/marker-icon.png','./vendor/images/marker-icon-2x.png','./vendor/images/marker-shadow.png',
  './vendor/images/layers.png','./vendor/images/layers-2x.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;
  const req=e.request;
  const esDoc = req.mode==='navigate' || req.destination==='document' || req.url.endsWith('/') || req.url.endsWith('index.html');
  if(esDoc){   // network-first para el HTML: siempre la última versión estando en línea
    e.respondWith(fetch(req).then(resp=>{const cp=resp.clone();caches.open(CACHE).then(c=>c.put(req,cp));return resp;})
      .catch(()=>caches.match(req).then(r=>r||caches.match('./index.html'))));
    return;
  }
  e.respondWith(caches.match(req).then(r=>r||fetch(req).then(resp=>{   // cache-first para assets
    const cp=resp.clone();caches.open(CACHE).then(c=>c.put(req,cp));return resp;
  }).catch(()=>caches.match('./index.html'))));});
