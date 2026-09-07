// Service worker de AUTODESTRUCCION para la ruta vieja /geoterreno-cdc/.
//
// Por que existe: el repo se renombro a "geonotas" el 2026-09-07 y GitHub Pages
// NO redirige la ruta vieja. Los telefonos que instalaron la PWA desde
// /geoterreno-cdc/ siguen con el service worker de esa ruta registrado, y ese SW
// es cache-first: responde desde su cache y nunca llega a la red, asi que una
// pagina de redirect por si sola JAMAS los alcanzaria.
//
// El navegador si vuelve a pedir este archivo (sw.js) por red al navegar, como
// parte del chequeo de actualizacion del SW. Al recibir este, lo instala, y este
// se limpia y se da de baja: la siguiente carga cae a la red y ahi si ve
// index.html con el redirect a /geonotas/.
//
// NO hay handler de 'fetch' a proposito: sin el, este SW no intercepta nada y
// todo pasa directo a la red mientras se termina de dar de baja.

// ---------------------------------------------------------------------------
// CUIDADO AL TOCAR ESTO: no borrar caches por NOMBRE.
//
// La app vieja cacheaba bajo nombres 'geonotas-vNNN' / 'geoterreno-cdc-vNNN', y
// la app NUEVA en /geonotas/ usa exactamente el mismo patron ('geonotas-v114').
// La Cache API tiene alcance de ORIGEN, no de ruta, y las dos rutas viven en el
// mismo cvenegas-sernageomin.github.io: borrar por patron de nombre desde aqui
// dejaria sin offline a la app viva, que es justo el bug que el sw.js de la app
// ya documenta y evita con esMia().
//
// Por eso se borran solo las ENTRADAS cuya URL cuelga de /geoterreno-cdc/, y un
// cache solo se elimina si quedo vacio. Tampoco se toca 'transformers-cache'
// (modelo de voz de ~78 MB de la light), que no cuelga de ninguna de las dos.
// ---------------------------------------------------------------------------

self.addEventListener('install', e => { self.skipWaiting(); });

self.addEventListener('activate', e => e.waitUntil((async () => {
  const base = new URL('./', self.location).href;   // .../geoterreno-cdc/
  const barrer = async () => {
    for (const nombre of await caches.keys()) {
      const c = await caches.open(nombre);
      let borradas = 0;
      for (const req of await c.keys()) {
        if (req.url.startsWith(base)) { await c.delete(req); borradas++; }
      }
      // Solo se elimina el cache entero si era exclusivamente de la ruta vieja.
      if (borradas > 0 && (await c.keys()).length === 0) await caches.delete(nombre);
    }
  };
  await barrer();
  await self.registration.unregister();
  // Segunda pasada: el SW viejo sigue vivo hasta que termina de darse de baja y su
  // rama cache-first alcanza a guardar la respuesta de red DESPUES del primer barrido.
  // Medido el 2026-09-07 contra el sitio: quedaba un cache 'geonotas-v113' con una
  // sola entrada, la propia pagina de redireccion. Es inerte (ya nadie lo lee), pero
  // se limpia igual para no dejar basura en el dispositivo del geologo.
  await barrer();
  // Recargar las ventanas abiertas: ya sin SW, caen a la red y ven el redirect.
  const clientes = await self.clients.matchAll({ type: 'window' });
  for (const cl of clientes) { try { await cl.navigate(cl.url); } catch (_) {} }
})()));
