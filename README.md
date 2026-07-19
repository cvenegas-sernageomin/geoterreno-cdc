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

## Estructura
- `index.html` — app monolítica (generada por `build_pwa.py`, que inyecta el modelo canónico).
- `manifest.json`, `sw.js`, `icons/` — PWA instalable/offline.
- `vendor/` — librerías locales (Leaflet, leaflet.offline, idb, georaster, sql.js para GPKG,
  gdal3.js para GDB) para 100% offline.
- `build_pwa.py` — regenera `index.html` desde `../modelo/modelo_canonico.json`.

Datos capturados quedan en el dispositivo (IndexedDB); el mapa satelital requiere internet la
primera vez (luego los tiles descargados quedan disponibles offline).
