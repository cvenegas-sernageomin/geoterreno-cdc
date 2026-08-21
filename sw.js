// Service worker offline-first (cache estatico)
const CACHE='geoterreno-cdc-v70';
const ASSETS=['./','./index.html','./manifest.json','./icons/icon-192.png','./icons/icon-512.png',
  './vendor/leaflet.css','./vendor/leaflet.js','./vendor/idb.js','./vendor/leaflet.offline.js',
  './vendor/georaster.browser.bundle.min.js','./vendor/georaster-layer-for-leaflet.min.js',
  './vendor/sql-wasm.js','./vendor/sql-wasm.wasm','./vendor/jszip.js',
  './vendor/images/marker-icon.png','./vendor/images/marker-icon-2x.png','./vendor/images/marker-shadow.png',
  './vendor/images/layers.png','./vendor/images/layers-2x.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;
  const req=e.request;
  // Cross-origin (tiles satelitales/topo de Esri y OpenTopoMap, export de ArcGIS): NO se
  // cachea aca. Los tiles offline los administra leaflet.offline en IndexedDB con el boton
  // "Descargar tiles", que ademas deja elegir el area y el zoom. Cachearlos tambien aca
  // duplicaba el almacenamiento y crecia sin techo: este cache solo se limpia al subir de
  // version, asi que cada tile que el usuario mirara al pasar quedaba guardado para siempre.
  if(new URL(req.url).origin!==self.location.origin) return;
  const esDoc = req.mode==='navigate' || req.destination==='document' || req.url.endsWith('/') || req.url.endsWith('index.html');
  if(esDoc){   // network-first para el HTML: siempre la última versión estando en línea
    // solo se cachea si resp.ok: un 404 (ej. deploy a medio subir) quedaba cacheado para
    // siempre y la app seguía rota offline hasta la próxima versión de CACHE.
    e.respondWith(fetch(req).then(resp=>{if(resp.ok){const cp=resp.clone();caches.open(CACHE).then(c=>c.put(req,cp));}return resp;})
      .catch(()=>caches.match(req).then(r=>r||caches.match('./index.html'))));
    return;
  }
  // cache-first para assets. Sin fallback a index.html: devolver el HTML cuando falla una
  // imagen o un .wasm no arregla nada y disfraza el error real de un fallo de red.
  e.respondWith(caches.match(req).then(r=>r||fetch(req).then(resp=>{
    // mismo criterio que la rama de documento: no cachear respuestas con error.
    if(resp.ok){const cp=resp.clone();caches.open(CACHE).then(c=>c.put(req,cp));}return resp;
  })));});
