# GeoTerreno CDC — Libreta geológica de campo

PWA offline para captura de datos de **geología básica en terreno** (modelo CDC SERNAGEOMIN).
Instalable en celular; funciona sin conexión tras la primera carga.

**En línea:** https://cvenegas-sernageomin.github.io/geoterreno-cdc/

## Funcionalidad
- Multi-proyecto, modelo relacional de 8 tablas (proyecto → punto de control → litología,
  estructurales, contactos, muestreo, fotografías, esquemas), almacenado en IndexedDB.
- Formularios maestro-detalle con **listas de dominio y cascadas** (TIPO_ROCA → NOMBRE_ROCA;
  TIPO_ESTRUCTURA → tipo de medida).
- **Mapa satelital** (Esri World Imagery) con pin arrastrable ↔ coordenadas, GPS, descarga de
  **tiles offline**, captura de vista satelital y overlay de **GeoTIFF** propio.
- Cámara para fotografías y **esquema en canvas**.
- **Exportación: CSV** (ZIP con las 8 tablas), **KMZ** (puntos + imagen satelital + GeoTIFF como
  GroundOverlay), **GeoPackage** (.gpkg con capas de puntos y líneas EPSG:4326 + tablas de
  atributos con fotos/esquemas como BLOB; QGIS/ArcGIS), **GDB** (File Geodatabase de Esri en ZIP,
  convertida en el navegador con GDAL/WASM — la primera vez requiere conexión, ~40 MB) y
  **PDF libreta de terreno** (una página por punto).

## Uso local
Requiere servirse por HTTP (no abrir el `index.html` con doble clic, por el Service Worker):
```
python -m http.server 8000    # luego abrir http://localhost:8000
```

## Prueba de humo
Con el servidor levantado, abrir **http://localhost:8000/smoke.html**. Corre sola y cubre el ciclo
completo (capturar → respaldar → borrar → restaurar → exportar) contra el `index.html` real,
cargado en un iframe, más una prueba de regresión por cada bug de la auditoría del 2026-08-12.

**No toca tus datos:** todo lo que crea lleva el prefijo `smoke-` (los ids reales que genera
`uid()` empiezan con `x`), solo borra lo suyo, y la última prueba verifica que la cantidad de
registros ajenos no cambió. Se puede correr sobre un dispositivo con datos de terreno reales.

Dos cosas a tener presentes al tocarla:
- La app declara casi todo con `const`/`let` de nivel superior, que **no** son propiedades de
  `window`: desde el iframe padre solo se ven las **declaraciones de función**. Por eso la señal
  de "app lista" es que `all()` resuelva, `APP_VER` se lee del archivo con `fetch`, y los nombres
  de campo (`inLat`/`inLon`) se replican y se contrastan contra el modelo en la primera prueba.
- Los `File`/`Blob` que consume la app se construyen con el constructor **del iframe**
  (`new w.File(...)`). JSZip corre dentro del iframe y valida con `instanceof ArrayBuffer`; uno
  nacido en el realm del padre falla y JSZip responde *"Can't read the data of the loaded zip
  file"*, que parece un KMZ corrupto pero es un artefacto de la prueba.

## Estructura
- `index.html` — app monolítica (generada por `build_pwa.py`, que inyecta el modelo canónico).
- `manifest.json`, `sw.js`, `icons/` — PWA instalable/offline.
- `vendor/` — librerías locales (Leaflet, leaflet.offline, idb, georaster, sql.js para GPKG,
  gdal3.js para GDB) para 100% offline.
- `build_pwa.py` — regenera `index.html` desde `../modelo/modelo_canonico.json`.
- `smoke.html` — prueba de humo (ver arriba); no forma parte de la app ni del `sw.js`.

Datos capturados quedan en el dispositivo (IndexedDB); el mapa satelital requiere internet la
primera vez (luego los tiles descargados quedan disponibles offline).
