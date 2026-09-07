# geoterreno-cdc — redirección a PWA Geonotas

Este repo **no tiene la aplicación**. Solo redirige la dirección vieja a la nueva:

| | |
|---|---|
| Vieja (aquí) | `https://cvenegas-sernageomin.github.io/geoterreno-cdc/` |
| **Nueva** | **https://cvenegas-sernageomin.github.io/geonotas/** |

La app se llama **PWA Geonotas** desde agosto de 2026 y el repo se renombró a
[`geonotas`](https://github.com/cvenegas-sernageomin/geonotas) el 2026-09-07.
GitHub redirige el repo y el `git remote`, pero **no redirige GitHub Pages**: la
dirección vieja quedaba en 404, y con ella los QR y enlaces ya repartidos.

## Qué hay acá

| Archivo | Para qué |
|---|---|
| `index.html` | Página de aviso + redirección a la dirección nueva. |
| `404.html` | Copia de la anterior; GitHub Pages la sirve para cualquier subruta, así que `…/geoterreno-cdc/loquesea` también llega. |
| `sw.js` | **Service worker de autodestrucción.** Lo importante. |

## Por qué hace falta el `sw.js`

Los teléfonos que instalaron la PWA desde la ruta vieja tienen su service worker
registrado ahí, y es *cache-first*: responde desde su caché y **nunca llega a la
red**, así que una página de redirección por sí sola no los alcanzaría jamás.

El navegador sí vuelve a pedir `sw.js` por red al navegar (chequeo de
actualización del service worker). Recibe este, lo instala, y este se limpia y se
da de baja; la siguiente carga cae a la red y ahí sí ve la redirección.

**Al tocar `sw.js`, no borrar cachés por nombre.** La app nueva usa el mismo
patrón de nombre (`geonotas-vNNN`) en el mismo origen, así que borrar por patrón
desde acá dejaría sin uso offline a la app viva. Se borran solo las *entradas*
que cuelgan de `/geoterreno-cdc/`, y un caché se elimina solo si quedó vacío.

## Los datos de terreno no se pierden

IndexedDB tiene alcance de **origen**, no de ruta, y el origen
(`cvenegas-sernageomin.github.io`) no cambió. La app en la dirección nueva abre
exactamente la misma base de datos.
