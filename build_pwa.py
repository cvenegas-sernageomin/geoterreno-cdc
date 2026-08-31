# -*- coding: utf-8 -*-
"""
Build de la PWA Geonotas (Track A).

Reinyecta modelo_canonico.json en el index.html EXISTENTE (index.html es la
fuente de verdad; se edita a mano, incluida su parte JS/CSS). Tambien genera
manifest.json e iconos PNG minimos si faltan. sw.js es de mantencion manual
(ver escribir_sw). Sin Node. Solo stdlib. Correr tras (re)generar el modelo
canonico: es idempotente, no toca el resto del archivo.

Reglas que este script respeta a proposito (cada una nacio de un incidente):

- NO traduce saltos de linea. Se abre con newline="" al leer Y al escribir, y el
  JSON inyectado se adapta al salto que ya usa el archivo destino. Antes se abria
  en modo texto normal: en Windows eso convertia el archivo ENTERO de LF a CRLF en
  cuanto el modelo cambiaba (medido: 8579 lineas reescritas en la light), lo que
  sepultaba el cambio real bajo un diff de todo el archivo.
- VALIDA el JSON antes de inyectarlo y valida que el tramo que va a reemplazar sea
  JSON puro. Si el ancla se corriera, el reemplazo se comeria el codigo que hubiera
  entre el modelo y el </script>; ahora aborta sin tocar nada en vez de callar.
- Solo genera los iconos que FALTEN. Antes, si faltaba uno solo, regeneraba los dos
  y pisaba con un placeholder el icono bueno hecho a mano.
"""
import json, os, re, struct, zlib

# abspath: si no, correr el script desde otro directorio resolvia ../modelo contra
# el cwd y no contra la ubicacion real del script.
HERE = os.path.dirname(os.path.abspath(__file__))
MODELO = os.path.join(HERE, "..", "modelo", "modelo_canonico.json")
OUT_HTML = os.path.join(HERE, "index.html")


def leer_modelo():
    """Lee el modelo canonico y falla ruidosamente si no esta o no es JSON."""
    if not os.path.exists(MODELO):
        raise SystemExit("ERROR: no existe el modelo canonico:\n       %s" % MODELO)
    with open(MODELO, encoding="utf-8") as fh:   # universal newlines -> \n
        txt = fh.read()
    try:
        json.loads(txt)
    except ValueError as e:
        raise SystemExit("ERROR: modelo_canonico.json no es JSON valido (%s).\n"
                         "       No se inyecta nada; index.html queda intacto." % e)
    return txt


# ---------------------------------------------------------------------------
# index.html es la FUENTE DE VERDAD (se edita a mano, incluida su parte JS).
# build_pwa.py ya NO guarda una copia del HTML: solo reinyecta el bloque del
# modelo canonico en el archivo que ya esta en disco, entre las anclas de abajo.
_MODELO_INI = "const MODELO = "
_MODELO_FIN = re.compile(r";\r?\n</script>")   # \r? : el HTML puede estar en CRLF

def actualizar_modelo_en_html(modelo_json):
    """Reinyecta modelo_canonico.json en el index.html existente, sin tocar nada
    mas del archivo (ni sus saltos de linea). Idempotente: si el modelo no
    cambio, no reescribe nada."""
    # Revalidar aca aunque leer_modelo() ya valide: esta es la funcion que ESCRIBE
    # el archivo, y no debe confiar en su entrada. Si alguien la llama desde otro
    # lado, el index.html no puede quedar con un modelo roto adentro.
    try:
        json.loads(modelo_json)
    except ValueError as e:
        raise SystemExit("ERROR: el modelo a inyectar no es JSON valido (%s).\n"
                         "       No se toco index.html." % e)

    with open(OUT_HTML, encoding="utf-8", newline="") as fh:   # newline="": sin traducir
        html = fh.read()

    i = html.find(_MODELO_INI)
    if i < 0:
        raise SystemExit("ERROR: no se encontro el ancla %r en index.html.\n"
                         "       No se toco nada." % _MODELO_INI)
    i += len(_MODELO_INI)
    m = _MODELO_FIN.search(html, i)
    if m is None:
        raise SystemExit("ERROR: no se encontro el cierre ';</script>' del bloque del\n"
                         "       modelo en index.html. No se toco nada.")
    j = m.start()

    # Guarda contra deriva del ancla: lo que se va a reemplazar tiene que ser el
    # JSON del modelo y NADA mas. Si algun dia queda codigo entre el modelo y el
    # </script>, esto lo detecta en vez de borrarlo en silencio.
    try:
        json.loads(html[i:j])
    except ValueError as e:
        raise SystemExit("ERROR: el tramo que se iba a reemplazar en index.html no es\n"
                         "       JSON puro (%s).\n"
                         "       El ancla se corrio: revisar index.html. No se toco nada." % e)

    salto = "\r\n" if "\r\n" in html else "\n"
    nuevo = html[:i] + modelo_json.replace("\n", salto) + html[j:]
    if nuevo == html:
        return False
    with open(OUT_HTML, "w", encoding="utf-8", newline="") as fh:
        fh.write(nuevo)
    return True


def escribir_iconos():
    # Los iconos definitivos (martillo geologico, 2026-07-11) se renderizaron desde SVG
    # con Playwright y NO deben sobrescribirse: solo se genera el que FALTE. Antes esto
    # era un all(...) que, si faltaba uno de los dos, regeneraba AMBOS y pisaba el bueno.
    d = os.path.join(HERE, "icons"); os.makedirs(d, exist_ok=True)
    faltan = [s for s in (192, 512) if not os.path.exists(os.path.join(d, "icon-%d.png" % s))]
    if not faltan:
        return False
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
    for s in faltan:
        with open(os.path.join(d, "icon-%d.png" % s), "wb") as fh:
            fh.write(png(s))
        print("AVISO: faltaba icons/icon-%d.png; se genero un PLACEHOLDER.\n"
              "       Reemplazarlo por el icono real antes de publicar." % s)
    return True


def escribir_manifest():
    manifest = {
        "name": "PWA Geonotas — Libreta geológica de campo",
        "short_name": "Geonotas",
        "description": "Libreta digital de geología básica en terreno, offline (captura, mapa satelital y export CSV/KMZ/GeoPackage/GDB/PDF).",
        "start_url": ".", "scope": ".", "display": "standalone",
        "background_color": "#1f6f4f", "theme_color": "#1f6f4f", "orientation": "portrait",
        "icons": [
            {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    }
    txt = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    p = os.path.join(HERE, "manifest.json")
    # solo reescribe si cambio, para no ensuciar la fecha del archivo en cada build
    if os.path.exists(p):
        with open(p, encoding="utf-8", newline="") as fh:
            if fh.read() == txt:
                return False
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    return True


def escribir_sw():
    # sw.js es 100% de mantencion manual (no depende del modelo canonico): al
    # agregar un vendor/*.js nuevo o cambiar el codigo, subir CACHE y ASSETS a
    # mano en sw.js, igual que APP_VER en index.html. Aca solo se crea un
    # bootstrap si el archivo faltara por completo, y se AVISA: ese bootstrap no
    # conoce vendor/, asi que la app quedaria sin offline real. Antes el bootstrap
    # ademas no traia 'activate' ni 'fetch' -- cacheaba y no servia nada.
    p = os.path.join(HERE, "sw.js")
    if os.path.exists(p):
        return False
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(
            "// Service worker offline-first (bootstrap MINIMO generado por build_pwa.py).\n"
            "// Incompleto a proposito: no lista vendor/. Completar ASSETS y subir CACHE a mano.\n"
            "const CACHE='geonotas-bootstrap-v0';\n"
            "const ASSETS=['./','./index.html','./manifest.json'];\n"
            "self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE)"
            ".then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()));});\n"
            "self.addEventListener('activate',e=>{e.waitUntil(caches.keys()"
            ".then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k))))"
            ".then(()=>self.clients.claim()));});\n"
            "self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;\n"
            "  if(new URL(e.request.url).origin!==self.location.origin)return;\n"
            "  e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)));});\n"
        )
    print("AVISO: faltaba sw.js. Se escribio un bootstrap MINIMO: la app NO queda\n"
          "       offline de verdad hasta completar ASSETS y CACHE a mano.")
    return True


def main():
    modelo_json = leer_modelo()
    cambio = actualizar_modelo_en_html(modelo_json)
    escribir_manifest(); escribir_sw(); escribir_iconos()
    if cambio:
        print("OK: modelo canonico actualizado en index.html")
    else:
        print("OK: index.html ya estaba al dia con modelo_canonico.json (sin cambios)")


if __name__ == "__main__":
    main()
