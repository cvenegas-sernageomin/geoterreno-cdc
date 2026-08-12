# -*- coding: utf-8 -*-
"""
Build de la PWA 'Captura de datos en terreno' (Track A).

Reinyecta modelo_canonico.json en el index.html EXISTENTE (index.html es la
fuente de verdad; se edita a mano, incluida su parte JS/CSS). Tambien genera
manifest.json e iconos PNG minimos si faltan. sw.js es de mantencion manual
(ver escribir_sw). Sin Node. Solo stdlib. Correr tras (re)generar el modelo
canonico: es idempotente, no toca el resto del archivo.

"""
import json, os, struct, zlib, base64

HERE = os.path.dirname(__file__)
MODELO = os.path.join(HERE, "..", "modelo", "modelo_canonico.json")
OUT_HTML = os.path.join(HERE, "index.html")

with open(MODELO, encoding="utf-8") as fh:
    modelo_json = fh.read()

# ---------------------------------------------------------------------------
# index.html es la FUENTE DE VERDAD (se edita a mano, incluida su parte JS).
# build_pwa.py ya NO guarda una copia del HTML: solo reinyecta el bloque del
# modelo canonico en el archivo que ya esta en disco, entre las anclas de abajo.
_MODELO_INI = "const MODELO = "
_MODELO_FIN = ";\n</script>"

def actualizar_modelo_en_html():
    """Reinyecta modelo_canonico.json en el index.html existente, sin tocar nada
    mas del archivo. Idempotente: si el modelo no cambio, no reescribe nada."""
    with open(OUT_HTML, encoding="utf-8") as fh:
        html = fh.read()
    i = html.index(_MODELO_INI) + len(_MODELO_INI)
    j = html.index(_MODELO_FIN, i)
    nuevo = html[:i] + modelo_json + html[j:]
    if nuevo == html:
        return False
    with open(OUT_HTML, "w", encoding="utf-8") as fh:
        fh.write(nuevo)
    return True

def escribir_iconos():
    # Los iconos definitivos (martillo geologico, 2026-07-11) se renderizaron desde SVG
    # con Playwright y NO deben sobrescribirse: solo genera placeholders si faltan.
    d = os.path.join(HERE, "icons"); os.makedirs(d, exist_ok=True)
    if all(os.path.exists(os.path.join(d, "icon-%d.png" % s)) for s in (192, 512)):
        return
    def png(size):
        # PNG solido verde con un rombo claro (icono minimo, sin libs)
        def chunk(typ, data):
            c = typ + data
            return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
        w = h = size
        raw = bytearray()
        cx = cy = size/2
        for y in range(h):
            raw.append(0)
            for x in range(w):
                # rombo: |dx|+|dy| < r  -> claro
                if abs(x-cx)+abs(y-cy) < size*0.32:
                    raw += bytes((214, 240, 226))
                else:
                    raw += bytes((31, 111, 79))
        sig = b"\x89PNG\r\n\x1a\n"
        ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
        comp = zlib.compress(bytes(raw), 9)
        return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", comp) + chunk(b"IEND", b"")
    for s in (192, 512):
        with open(os.path.join(d, "icon-%d.png" % s), "wb") as fh:
            fh.write(png(s))

def escribir_manifest():
    manifest = {
        "name": "GeoTerreno CDC — Libreta geológica de campo",
        "short_name": "GeoTerreno",
        "description": "Libreta digital de geología básica en terreno, offline (captura, mapa satelital y export CSV/KMZ/GeoPackage/GDB/PDF).",
        "start_url": ".", "scope": ".", "display": "standalone",
        "background_color": "#1f6f4f", "theme_color": "#1f6f4f", "orientation": "portrait",
        "icons": [
            {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    }
    with open(os.path.join(HERE, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

def escribir_sw():
    # sw.js es 100% de mantencion manual (no depende del modelo canonico): al
    # agregar un vendor/*.js nuevo o cambiar el codigo, subir CACHE y ASSETS a
    # mano en sw.js, igual que APP_VER en index.html. Aca solo se crea un
    # bootstrap minimo si el archivo faltara por completo.
    p = os.path.join(HERE, "sw.js")
    if os.path.exists(p):
        return
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(
            "// Service worker offline-first (cache estatico)\n"
            "const CACHE='geoterreno-cdc-v0';\n"
            "const ASSETS=['./','./index.html','./manifest.json'];\n"
            "self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE)"
            ".then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()));});\n"
        )

def main():
    cambio = actualizar_modelo_en_html()
    escribir_manifest(); escribir_sw(); escribir_iconos()
    if cambio:
        print("OK: modelo canonico actualizado en index.html")
    else:
        print("OK: index.html ya estaba al dia con modelo_canonico.json (sin cambios)")

if __name__ == "__main__":
    main()
