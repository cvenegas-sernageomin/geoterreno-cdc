# -*- coding: utf-8 -*-
"""
Build de la PWA 'Captura de datos en terreno' (Track A).

Inyecta modelo_canonico.json en un index.html monolitico offline.
Genera tambien manifest.json, sw.js e iconos PNG minimos.
Sin Node. Solo stdlib. Ejecutar tras (re)generar el modelo canonico.
"""
import json, os, struct, zlib, base64

HERE = os.path.dirname(__file__)
MODELO = os.path.join(HERE, "..", "modelo", "modelo_canonico.json")
OUT_HTML = os.path.join(HERE, "index.html")

with open(MODELO, encoding="utf-8") as fh:
    modelo_json = fh.read()

# ---------------------------------------------------------------------------
# Plantilla HTML (offline, monolitica). __MODELO_JSON__ se reemplaza al final.
# ---------------------------------------------------------------------------
HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#1f6f4f">
<title>GeoTerreno CDC — Libreta geológica de campo</title>
<link rel="manifest" href="manifest.json">
<link rel="icon" href="icons/icon-192.png">
<link rel="stylesheet" href="vendor/leaflet.css">
<script src="vendor/leaflet.js"></script>
<script src="vendor/idb.js"></script>
<script src="vendor/leaflet.offline.js"></script>
<script src="vendor/georaster.browser.bundle.min.js"></script>
<script src="vendor/georaster-layer-for-leaflet.min.js"></script>
<style>
  /* ---- Paleta: cálida, natural (geología), suave a la vista + modo oscuro auto ---- */
  :root{
    --verde:#2f6b4f;--verde2:#3a8a66;--azul:#2b6fa8;--naranja:#bd7a2c;--rojo:#c0463a;
    --header1:#2f6b4f;--header2:#22513c;
    --bg1:#ebeee6;--bg2:#e2e7db;
    --surface:#f8f9f4;--surface2:#eef2e9;
    --txt:#27302a;--muted:#5f6b62;--lbl:#48544c;
    --bd:#d5dbce;--bd2:#c8d0c0;
    --inp:#eef1e9;--inp-bd:#cfd6c7;
    --btn-green:#2f7a58;--btn-blue:#2b6fa8;--btn-orange:#b9761f;
    --shadow:0 1px 2px rgba(30,50,35,.05),0 12px 26px -18px rgba(30,50,35,.30);
    --ring:0 0 0 3px rgba(47,122,88,.20);
  }
  @media (prefers-color-scheme:dark){:root{
    --verde:#5cbd8c;--verde2:#6ccf9c;--azul:#6aa8dd;--naranja:#d59147;--rojo:#e0796d;
    --header1:#1d4433;--header2:#122b20;
    --bg1:#141a16;--bg2:#0e130f;
    --surface:#1d251f;--surface2:#242e26;
    --txt:#e6ede3;--muted:#9aab9d;--lbl:#c0ccbd;
    --bd:#33402f;--bd2:#3d4c39;
    --inp:#232e25;--inp-bd:#3b4b3d;
    --btn-green:#2f915f;--btn-blue:#2f7bb8;--btn-orange:#bd7f2c;
    --shadow:0 1px 2px rgba(0,0,0,.35),0 14px 28px -18px rgba(0,0,0,.65);
    --ring:0 0 0 3px rgba(92,189,140,.24);
  }}
  *{box-sizing:border-box}
  body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--txt);
    background:linear-gradient(180deg,var(--bg1),var(--bg2)) fixed;min-height:100vh;-webkit-text-size-adjust:100%}
  header{background:linear-gradient(135deg,var(--header1),var(--header2));color:#fff;padding:12px 15px;display:flex;align-items:center;gap:10px;position:sticky;top:0;z-index:10;box-shadow:0 4px 14px -6px rgba(0,0,0,.4)}
  header h1{font-size:16px;margin:0;flex:1;font-weight:650;letter-spacing:.2px}
  header .ctx{font-size:11px;opacity:.88;font-weight:400}
  main{max-width:820px;margin:0 auto;padding:14px 12px 96px}
  .card{background:var(--surface);border:1px solid var(--bd);border-radius:16px;padding:14px;margin-bottom:13px;box-shadow:var(--shadow)}
  .card h2{font-size:14px;margin:0 0 11px;color:var(--verde);display:flex;align-items:center;gap:8px;font-weight:650;letter-spacing:.2px}
  .row{display:flex;flex-wrap:wrap;gap:10px}
  .fld{display:flex;flex-direction:column;gap:4px;margin-bottom:10px;flex:1 1 220px;min-width:0}
  .fld label{font-size:11.5px;font-weight:600;color:var(--lbl);letter-spacing:.2px}
  .fld label .req{color:var(--rojo);margin-left:2px}
  .fld input,.fld select,.fld textarea{padding:9px 10px;border:1px solid var(--inp-bd);border-radius:10px;font-size:14px;font-family:inherit;background:var(--inp);color:var(--txt);width:100%;transition:border-color .15s,box-shadow .15s}
  .fld input:focus,.fld select:focus,.fld textarea:focus{outline:none;border-color:var(--verde);box-shadow:var(--ring)}
  .fld textarea{resize:vertical;min-height:58px}
  .fld .nota{font-size:10px;color:var(--muted)}
  button{font-family:inherit;font-size:14px;border:none;border-radius:10px;padding:9px 15px;cursor:pointer;font-weight:600;transition:filter .15s,transform .05s;color:#fff}
  button:hover{filter:brightness(1.07)}button:active{transform:translateY(1px)}
  .btn{background:var(--btn-green)}
  .btn.sec{background:var(--surface2);color:var(--txt);border:1px solid var(--bd)}
  .btn.mini{padding:7px 11px;font-size:12px}
  .btn.del{background:transparent;color:var(--rojo);border:1px solid var(--rojo)}
  .btn.blue{background:var(--btn-blue)}
  .btn.orange{background:var(--btn-orange)}
  .btnbar{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;align-items:center}
  .list-item{display:flex;align-items:center;gap:10px;padding:11px 12px;border:1px solid var(--bd);border-radius:13px;margin-bottom:8px;background:var(--surface);cursor:pointer;transition:transform .1s,box-shadow .15s,background .15s}
  .list-item:hover{background:var(--surface2);transform:translateY(-1px);box-shadow:var(--shadow)}
  .list-item .t{flex:1;min-width:0}
  .list-item .t b{font-size:14px}
  .list-item .t small{color:var(--muted);font-size:11.5px;display:block;margin-top:1px}
  .pill{font-size:10px;padding:3px 9px;border-radius:20px;background:var(--surface2);color:var(--muted);border:1px solid var(--bd);white-space:nowrap}
  .empty{color:var(--muted);font-size:13px;text-align:center;padding:20px}
  .child-block{border-left:3px solid var(--naranja);padding:9px 11px;margin:8px 0;background:var(--surface2);border-radius:0 12px 12px 0}
  .child-block.lito{border-left-color:var(--verde2)}
  .child-block .hd{display:flex;align-items:center;gap:8px;font-weight:650;font-size:13px;margin-bottom:7px;color:var(--txt)}
  .child-block .hd .n{flex:1}
  fieldset{border:1px solid var(--bd);border-radius:10px;margin:0 0 10px;padding:8px 10px}
  legend{font-size:12px;font-weight:700;color:var(--naranja);padding:0 6px}
  legend.lito{color:var(--verde2)}
  .fab{position:fixed;left:0;right:0;bottom:0;background:var(--surface);border-top:1px solid var(--bd);padding:9px 12px;display:flex;gap:8px;max-width:820px;margin:0 auto;z-index:9;box-shadow:0 -6px 18px -10px rgba(0,0,0,.28)}
  .toast{position:fixed;bottom:72px;left:50%;transform:translateX(-50%);background:#1f2a22;color:#eef4ee;padding:11px 18px;border-radius:22px;font-size:13px;opacity:0;transition:.3s;z-index:99;pointer-events:none;box-shadow:0 8px 24px -8px rgba(0,0,0,.5)}
  .toast.on{opacity:.97}
  .thumbs{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}
  .thumbs img{width:64px;height:64px;object-fit:cover;border-radius:8px;border:1px solid var(--bd)}
  canvas.sketch{border:1px solid var(--bd);border-radius:10px;touch-action:none;background:#fff;width:100%;max-width:100%}
  .muted{color:var(--muted);font-size:12px}
  .warn{background:var(--surface2);border:1px solid var(--naranja);border-radius:10px;padding:8px 11px;font-size:12px;color:var(--txt);margin-bottom:10px}
  a.link{color:var(--azul);cursor:pointer;text-decoration:underline;font-size:12px}
  select:disabled{background:var(--surface2);color:var(--muted)}
  .mapbox{height:320px;width:100%;border:1px solid var(--bd);border-radius:12px;z-index:0;overflow:hidden}
  .leaflet-control-savetiles a{font-size:15px;line-height:26px}
  #satthumb img{width:120px;height:90px}
</style>
</head>
<body>
<header>
  <button class="btn sec mini" id="btnBack" style="display:none">‹</button>
  <div style="flex:1">
    <h1 id="ttl">GeoTerreno CDC</h1>
    <div class="ctx" id="ctx"></div>
  </div>
</header>
<main id="app"></main>
<div class="fab" id="fab"></div>
<div class="toast" id="toast"></div>

<script>
const MODELO = __MODELO_JSON__;
</script>
<script>
"use strict";
// ============================ Utilidades ============================
const $ = s => document.querySelector(s);
const el = (t,a={},...c)=>{const e=document.createElement(t);for(const k in a){if(k==='class')e.className=a[k];else if(k==='html')e.innerHTML=a[k];else if(k.startsWith('on'))e.addEventListener(k.slice(2),a[k]);else e.setAttribute(k,a[k]);}c.flat().forEach(x=>e.append(x&&x.nodeType?x:document.createTextNode(x==null?'':x)));return e;};
const uid = ()=> 'x'+Date.now().toString(36)+Math.random().toString(36).slice(2,7);
function toast(m){const t=$('#toast');t.textContent=m;t.classList.add('on');clearTimeout(t._t);t._t=setTimeout(()=>t.classList.remove('on'),2200);}
const esc = s => (s==null?'':String(s)).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

// Mapa store -> tabla del modelo
const STORE2TBL = {proyecto:'TBL_PROYECTO',punto:'PUNTO_CONTROL',litologia:'TBL_LITOLOGIA',
  estructural:'TBL_DATOS_ESTRUCTURALES',contacto:'TBL_CONTACTO',muestreo:'TBL_MUESTREO',
  foto:'TBL_FOTOGRAFIAS',esquema:'TBL_ESQUEMA_DIBUJO'};
const STORES = Object.keys(STORE2TBL);
const HIJAS = [
  {store:'litologia', titulo:'Litología', clase:'lito', oblig:true},
  {store:'estructural', titulo:'Datos estructurales', clase:''},
  {store:'contacto', titulo:'Contactos', clase:''},
  {store:'muestreo', titulo:'Muestreo', clase:''},
  {store:'foto', titulo:'Fotografías', clase:''},
  {store:'esquema', titulo:'Esquemas / dibujos', clase:''},
];
function campos(store){return (MODELO.tablas[STORE2TBL[store]]||{}).campos||[];}
function pkDe(store){return (MODELO.tablas[STORE2TBL[store]]||{}).pk;}

// ============================ IndexedDB ============================
const DB='captura-terreno', VER=1;
let db;
function openDB(){return new Promise((res,rej)=>{const r=indexedDB.open(DB,VER);
  r.onupgradeneeded=()=>{const d=r.result;STORES.forEach(s=>{if(!d.objectStoreNames.contains(s)){const os=d.createObjectStore(s,{keyPath:'id'});
    if(s!=='proyecto')os.createIndex('parent','_parent',{unique:false});}});};
  r.onsuccess=()=>{db=r.result;res(db);};r.onerror=()=>rej(r.error);});}
function tx(store,mode='readonly'){return db.transaction(store,mode).objectStore(store);}
function put(store,obj){return new Promise((res,rej)=>{const r=tx(store,'readwrite').put(obj);r.onsuccess=()=>res(obj);r.onerror=()=>rej(r.error);});}
function del(store,id){return new Promise((res,rej)=>{const r=tx(store,'readwrite').delete(id);r.onsuccess=()=>res();r.onerror=()=>rej(r.error);});}
function all(store){return new Promise((res,rej)=>{const r=tx(store).getAll();r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error);});}
function get(store,id){return new Promise((res,rej)=>{const r=tx(store).get(id);r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error);});}
async function childrenOf(store,parentId){return (await all(store)).filter(x=>x._parent===parentId);}

// ============================ Dominios / cascadas ============================
function dominio(nombre){return MODELO.dominios[nombre];}
// opciones [{value,label}] para un campo, dado el valor del padre (si cascada)
function opciones(domName, parentValue){
  const d=dominio(domName); if(!d)return [];
  if(d.tipo==='simple'||d.tipo==='abierta') return (d.valores||[]).map(v=>({value:v,label:v}));
  if(d.tipo==='cascada'){
    const arr=(d.mapa||{})[parentValue]||[];
    return arr.map(v=> (typeof v==='object') ? {value:v.codigo,label:v.descripcion||v.codigo} : {value:v,label:v});
  }
  return [];
}
// para un campo cascada, cual es el campo-padre en el formulario (mismo dominio que d.padre)
function campoPadreDe(store, campo){
  const d=dominio(campo.dominio); if(!d||d.tipo!=='cascada')return null;
  const padreDom=d.padre;
  const c=campos(store).find(x=>x.dominio===padreDom);
  return c?c.nombre:null;
}

// ============================ Widgets de formulario ============================
function tipoWidget(campo){
  const n=campo.nombre;
  if(campo.dominio) return 'select';
  if(/^(LAT|LONG)/.test(n)||/Lat$|Long$/.test(n)) return 'number';
  if(/COTA|AZIMUT|MANTEO|BUZAMIENTO|PESO|VOLUMEN|PRECISION|RUMBO/.test(n)) return 'number';
  if(n==='FECHA') return 'date';
  if(n==='HORA') return 'time';
  if(/DESCRIPCION|OBSERVACION|COMENTARIO|RELACION_LITOLOGIA|DISTRIBUCION/.test(n)) return 'textarea';
  return 'text';
}
const esPK = (store,n)=> n===pkDe(store);
const esFK = n => ['ID_PUNTO_CONTROL','ID_PROYECTO','ID_LITOLOGIA','ID_ESQUEMA','ID_FOTOGRAFIA','ID_FOTOGRAFIA_ASOCIADA'].includes(n);

// Construye el DOM de un formulario para (store, registro). Devuelve {node, getData}
function formulario(store, reg, ctx){
  const cont=el('div');
  const inputs={};
  const cs=campos(store).filter(c=> !esPK(store,c.nombre) && !(esFK(c.nombre) && c.nombre!=='ID_LITOLOGIA'&&c.nombre!=='ID_FOTOGRAFIA_ASOCIADA'&&c.nombre!=='ID_ESQUEMA'));
  const rowWrap=el('div',{class:'row'});
  cs.forEach(campo=>{
    const n=campo.nombre;
    const fld=el('div',{class:'fld'});
    const lab=el('label',{},n.replace(/_/g,' '));
    if(campo.obligatorio) lab.append(el('span',{class:'req'},'*'));
    fld.append(lab);
    let inp;
    const w=tipoWidget(campo);
    if(w==='select'){
      inp=el('select');
      inp.append(el('option',{value:''},'— seleccionar —'));
      const padre=campoPadreDe(store,campo);
      const pv = padre? (reg[padre]||'') : null;
      opciones(campo.dominio, pv).forEach(o=>inp.append(el('option',{value:o.value},o.label)));
      if(padre) inp.dataset.cascadaPadre=padre;
      // dominio abierto: permitir agregar (UNIDAD_GEOLOGICA)
      if((dominio(campo.dominio)||{}).tipo==='abierta'){
        const add=el('option',{value:'__add__'},'➕ Agregar nuevo…');inp.append(add);
      }
    } else if(w==='textarea'){ inp=el('textarea',{rows:2});
    } else if(w==='number'){ inp=el('input',{type:'number',step:'any',inputmode:'decimal'});
    } else if(w==='date'){ inp=el('input',{type:'date'});
    } else if(w==='time'){ inp=el('input',{type:'time'});
    } else { inp=el('input',{type:'text'}); }
    inp.name=n;
    if(reg[n]!=null) inp.value=reg[n];
    if(campo.obligatorio) inp.required=true;
    // FK ID_LITOLOGIA -> select de litologias del punto (en estructural/foto)
    if(n==='ID_LITOLOGIA' && ctx && ctx.litologias){
      inp=el('select');inp.name=n;inp.append(el('option',{value:''},'— (opcional) litología —'));
      ctx.litologias.forEach((L,i)=>inp.append(el('option',{value:L.id},'Lito '+(i+1)+': '+(L.NOMBRE_ROCA||L.TIPO_ROCA||L.id.slice(0,5)))));
      if(reg[n])inp.value=reg[n];
    }
    inputs[n]=inp;
    fld.append(inp);
    if(campo.nota) fld.append(el('div',{class:'nota'},campo.nota));
    rowWrap.append(fld);
  });
  cont.append(rowWrap);

  // cascadas: al cambiar el padre, repoblar hijos
  cont.addEventListener('change',e=>{
    const changed=e.target.name; if(!changed)return;
    Object.values(inputs).forEach(inp=>{
      if(inp.tagName==='SELECT' && inp.dataset.cascadaPadre===changed){
        const campo=cs.find(c=>c.nombre===inp.name);
        const cur=inp.value;
        inp.innerHTML='';inp.append(el('option',{value:''},'— seleccionar —'));
        opciones(campo.dominio, e.target.value).forEach(o=>inp.append(el('option',{value:o.value},o.label)));
        inp.value=''; // reset porque cambió el padre
      }
    });
    // dominio abierto "agregar nuevo"
    if(e.target.tagName==='SELECT' && e.target.value==='__add__'){
      const campo=cs.find(c=>c.nombre===e.target.name);
      const nv=prompt('Nuevo valor para '+e.target.name.replace(/_/g,' ')+':');
      if(nv){dominio(campo.dominio).valores.push(nv);
        const opt=el('option',{value:nv},nv);e.target.insertBefore(opt,e.target.querySelector('option[value="__add__"]'));e.target.value=nv;}
      else e.target.value='';
    }
  });

  return {node:cont, getData(){const o={};for(const n in inputs)o[n]=inputs[n].value; return o;}};
}

// ============================ Mapa satelital (Leaflet + Esri) ============================
const ESRI_URL='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
const ICONO=L.icon({iconUrl:'vendor/images/marker-icon.png',iconRetinaUrl:'vendor/images/marker-icon-2x.png',shadowUrl:'vendor/images/marker-shadow.png',iconSize:[25,41],iconAnchor:[12,41],popupAnchor:[1,-34],shadowSize:[41,41]});
let mapa=null, marcador=null, gtLayer=null, savetiles=null;
const inLat='Coordenadas Geográficas Decimales_Lat', inLon='Coordenadas Geográficas Decimales_Long';

function initMapPunto(reg, f){
  const la=parseFloat(reg[inLat]), lo=parseFloat(reg[inLon]);
  const lat=isNaN(la)?-33.45:la, lon=isNaN(lo)?-70.65:lo;
  if(mapa){try{mapa.remove();}catch(e){}mapa=null;}
  mapa=L.map('map',{center:[lat,lon],zoom:isNaN(la)?5:16});
  const tl=(L.tileLayer.offline?L.tileLayer.offline:L.tileLayer)(ESRI_URL,{attribution:'Tiles © Esri',maxZoom:19,crossOrigin:true});
  tl.addTo(mapa);
  if(L.control&&L.control.savetiles){
    savetiles=L.control.savetiles(tl,{zoomlevels:[13,14,15,16,17],
      confirm(l,cb){if(confirm('¿Descargar tiles satelitales de esta área (zoom 13-17) para uso offline?'))cb();},
      confirmRemoval(l,cb){if(confirm('¿Borrar tiles guardados?'))cb();},saveText:'⬇️',rmText:'🗑️'});
    savetiles.addTo(mapa);
  }
  marcador=L.marker([lat,lon],{draggable:true,icon:ICONO}).addTo(mapa);
  const iLat=()=>f.node.querySelector('[name="'+inLat+'"]'), iLon=()=>f.node.querySelector('[name="'+inLon+'"]');
  const sync=()=>{const ll=marcador.getLatLng();if(iLat())iLat().value=ll.lat.toFixed(6);if(iLon())iLon().value=ll.lng.toFixed(6);
    const cl=document.getElementById('coordlbl');if(cl)cl.textContent='📍 '+ll.lat.toFixed(6)+', '+ll.lng.toFixed(6);};
  marcador.on('dragend',sync);
  if(!isNaN(la))sync();
  f.node.addEventListener('change',e=>{if(e.target.name===inLat||e.target.name===inLon){
    const a=parseFloat(iLat().value),o=parseFloat(iLon().value);if(!isNaN(a)&&!isNaN(o)){marcador.setLatLng([a,o]);mapa.panTo([a,o]);}}});
  // reponer GeoTIFF del proyecto (como imagen) si existe
  if(curProyecto&&curProyecto._geotiffB64&&curProyecto._geotiffBounds){const b=curProyecto._geotiffBounds;
    L.imageOverlay('data:image/jpeg;base64,'+curProyecto._geotiffB64,[[b.south,b.west],[b.north,b.east]],{opacity:.85}).addTo(mapa);}
  setTimeout(()=>mapa.invalidateSize(),120);
}
function ubicarGPSmapa(){if(!navigator.geolocation||!marcador)return;toast('Obteniendo GPS…');
  navigator.geolocation.getCurrentPosition(p=>{marcador.setLatLng([p.coords.latitude,p.coords.longitude]);
    mapa.setView([p.coords.latitude,p.coords.longitude],16);marcador.fire('dragend');
    toast('GPS ✓ ±'+Math.round(p.coords.accuracy)+' m');},e=>toast('GPS: '+e.message),{enableHighAccuracy:true,timeout:15000});}
function descargarTiles(){const b=document.querySelector('a.savetiles');if(b)b.click();else toast('Descarga offline no disponible (recarga con conexión)');}

async function capturarSatelital(){
  if(!mapa)return;const b=mapa.getBounds();
  const bbox=b.getWest()+','+b.getSouth()+','+b.getEast()+','+b.getNorth();
  const url='https://server.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/export?bbox='+bbox+'&bboxSR=4326&size=800,600&imageSR=4326&format=jpg&f=image';
  toast('Capturando satelital…');
  try{const r=await fetch(url,{signal:AbortSignal.timeout(9000)});if(!r.ok)throw 0;const blob=await r.blob();
    const b64=await new Promise(res=>{const rd=new FileReader();rd.onload=()=>res(rd.result.split(',')[1]);rd.readAsDataURL(blob);});
    curPunto._satelital=b64;curPunto._satBounds={west:b.getWest(),south:b.getSouth(),east:b.getEast(),north:b.getNorth()};
    await put('punto',curPunto);
    const th=document.getElementById('satthumb');th.innerHTML='';th.append(el('img',{src:'data:image/jpeg;base64,'+b64}));
    toast('Satelital capturada ✓');
  }catch(e){toast('No se pudo capturar (¿sin conexión?)');}
}
function cargarGeoTIFF(){
  if(typeof parseGeoraster==='undefined'||typeof GeoRasterLayer==='undefined'){toast('Librería GeoTIFF no cargada');return;}
  const inp=el('input',{type:'file',accept:'.tif,.tiff'});
  inp.onchange=async()=>{const file=inp.files[0];if(!file)return;toast('Cargando GeoTIFF…');
    try{const gr=await parseGeoraster(await file.arrayBuffer());
      if(gtLayer){mapa.removeLayer(gtLayer);}
      gtLayer=new GeoRasterLayer({georaster:gr,opacity:.85,resolution:256});gtLayer.addTo(mapa);
      mapa.fitBounds(gtLayer.getBounds());
      const bd=gtLayer.getBounds();
      curProyecto._geotiffBounds={south:bd.getSouth(),west:bd.getWest(),north:bd.getNorth(),east:bd.getEast()};
      curProyecto._geotiffB64=georasterToJPG(gr,800);
      await put('proyecto',curProyecto);
      toast('GeoTIFF cargado ✓');
    }catch(e){toast('Error GeoTIFF: '+e.message);}
  };inp.click();
}
// rasteriza un georaster (1 o ≥3 bandas) a JPG base64 (para overlay KMZ y persistencia)
function georasterToJPG(gr,maxdim){
  const bands=gr.values,h=gr.height,w=gr.width,nb=bands.length,nd=gr.noDataValue;
  const sc=Math.min(1,maxdim/Math.max(w,h)),ow=Math.max(1,Math.round(w*sc)),oh=Math.max(1,Math.round(h*sc));
  const cv=el('canvas');cv.width=ow;cv.height=oh;const cx=cv.getContext('2d'),img=cx.createImageData(ow,oh);
  const mm=[];for(let k=0;k<Math.min(nb,3);k++){let mn=Infinity,mx=-Infinity;const B=bands[k];
    for(let y=0;y<h;y+=Math.ceil(h/128)){for(let x=0;x<w;x+=Math.ceil(w/128)){const v=B[y][x];if(v===nd||v==null)continue;if(v<mn)mn=v;if(v>mx)mx=v;}}mm.push([mn,mx===mn?mn+1:mx]);}
  const norm=(v,k)=>{if(v===nd||v==null)return null;return Math.max(0,Math.min(255,Math.round((v-mm[k][0])/(mm[k][1]-mm[k][0])*255)));};
  for(let y=0;y<oh;y++)for(let x=0;x<ow;x++){const sx=Math.floor(x/sc),sy=Math.floor(y/sc),o=(y*ow+x)*4;
    const r=norm(bands[0][sy][sx],0);const g=nb>2?norm(bands[1][sy][sx],1):r;const bl=nb>2?norm(bands[2][sy][sx],2):r;
    img.data[o]=r==null?0:r;img.data[o+1]=g==null?0:g;img.data[o+2]=bl==null?0:bl;img.data[o+3]=r==null?0:255;}
  cx.putImageData(img,0,0);return cv.toDataURL('image/jpeg',.8).split(',')[1];
}
function b64ToBytes(b64){const bin=atob(b64);const u=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);return u;}

// ============================ Estado / navegación ============================
let vista={n:'home'}; // {n:'home'} | {n:'proyecto',id} | {n:'punto',id}
function nav(v){vista=v;render();}
$('#btnBack').addEventListener('click',()=>{
  if(vista.n==='punto'){const p= curPunto&&curPunto._parent; nav({n:'proyecto',id:p});}
  else if(vista.n==='proyecto') nav({n:'home'});
});

let curProyecto=null, curPunto=null;

async function render(){
  const app=$('#app'); app.innerHTML=''; $('#fab').innerHTML='';
  if(vista.n==='home') return renderHome(app);
  if(vista.n==='proyecto') return renderProyecto(app);
  if(vista.n==='punto') return renderPunto(app);
}

// -------- Home: proyectos --------
async function renderHome(app){
  $('#btnBack').style.display='none';
  $('#ttl').textContent='Proyectos'; $('#ctx').textContent='Captura de geología básica en terreno';
  const ps=await all('proyecto');
  const card=el('div',{class:'card'});
  card.append(el('h2',{},'Proyectos ('+ps.length+')'));
  if(!ps.length) card.append(el('div',{class:'empty'},'Aún no hay proyectos. Crea el primero.'));
  ps.forEach(p=>{
    card.append(el('div',{class:'list-item',onclick:()=>nav({n:'proyecto',id:p.id})},
      el('div',{class:'t'}, el('b',{},p.NOMBRE_PROYECTO||'(sin nombre)'),
        el('small',{},'ID: '+(p.ID_PROYECTO||'—')+' · Jefe: '+(p.JEFE_PROYECTO||'—'))),
      el('span',{class:'pill'},(p._npuntos||0)+' pts')));
  });
  app.append(card);
  $('#fab').append(el('button',{class:'btn',onclick:()=>editorProyecto()},'+ Nuevo proyecto'),
    el('button',{class:'btn sec',onclick:exportMenu},'⇩ Exportar'));
}

function editorProyecto(p){
  const app=$('#app');app.innerHTML='';$('#fab').innerHTML='';
  const reg=p||{id:uid()};
  $('#ttl').textContent=p?'Editar proyecto':'Nuevo proyecto';$('#ctx').textContent='';
  $('#btnBack').style.display='';
  const card=el('div',{class:'card'});card.append(el('h2',{},'Datos del proyecto'));
  const f=formulario('proyecto',reg);card.append(f.node);app.append(card);
  $('#fab').append(el('button',{class:'btn',onclick:async()=>{
    const d=f.getData();if(!d.NOMBRE_PROYECTO){toast('Falta NOMBRE_PROYECTO');return;}
    await put('proyecto',Object.assign(reg,d));toast('Proyecto guardado');nav({n:'proyecto',id:reg.id});
  }},'Guardar'), el('button',{class:'btn sec',onclick:()=>nav({n:'home'})},'Cancelar'));
}

// -------- Proyecto: puntos de control --------
async function renderProyecto(app){
  curProyecto=await get('proyecto',vista.id);
  if(!curProyecto)return nav({n:'home'});
  $('#btnBack').style.display='';
  $('#ttl').textContent=curProyecto.NOMBRE_PROYECTO||'Proyecto';
  $('#ctx').textContent='ID '+(curProyecto.ID_PROYECTO||'—');
  const puntos=(await childrenOf('punto',curProyecto.id));
  curProyecto._npuntos=puntos.length;put('proyecto',curProyecto);
  const head=el('div',{class:'card'});
  head.append(el('h2',{},'Proyecto'),
    el('div',{class:'btnbar'},
      el('button',{class:'btn sec mini',onclick:()=>editorProyecto(curProyecto)},'✎ Editar proyecto')));
  app.append(head);
  const card=el('div',{class:'card'});
  card.append(el('h2',{},'Puntos de control ('+puntos.length+')'));
  if(!puntos.length)card.append(el('div',{class:'empty'},'Sin puntos. Agrega el primero con el botón +.'));
  puntos.forEach((pt,i)=>{
    card.append(el('div',{class:'list-item',onclick:()=>nav({n:'punto',id:pt.id})},
      el('div',{class:'t'},el('b',{},pt.ID_PUNTO_CONTROL||('Punto '+(i+1))),
        el('small',{},(pt['Coordenadas Geográficas Decimales_Lat']||pt.LAT||'—')+', '+(pt['Coordenadas Geográficas Decimales_Long']||pt.LONG||'—')+' · '+(pt.FECHA||'')) ),
      el('span',{class:'pill'},(pt._nlito||0)+' lito')));
  });
  app.append(card);
  $('#fab').append(el('button',{class:'btn',onclick:()=>nav0Punto()},'+ Nuevo punto'),
    el('button',{class:'btn sec',onclick:()=>nav({n:'home'})},'⌂ Proyectos'));
}
function nav0Punto(){curPunto=null;nav({n:'punto',id:'__new__'});}

// -------- Punto de control + hijas --------
async function renderPunto(app){
  const nuevo = vista.id==='__new__';
  curPunto = nuevo ? {id:uid(),_parent:curProyecto.id} : await get('punto',vista.id);
  if(!curPunto)return nav({n:'proyecto',id:curProyecto.id});
  $('#btnBack').style.display='';
  $('#ttl').textContent = curPunto.ID_PUNTO_CONTROL || (nuevo?'Nuevo punto':'Punto');
  $('#ctx').textContent = curProyecto.NOMBRE_PROYECTO||'';

  // --- formulario del punto ---
  const card=el('div',{class:'card'});
  card.append(el('h2',{},'📍 Punto de control (estación y ubicación)'));
  const gps=el('button',{class:'btn blue mini',onclick:()=>tomarGPS(f)},'📡 Tomar GPS');
  card.append(el('div',{class:'btnbar'},gps));
  const f=formulario('punto',curPunto);card.append(f.node);

  // --- mapa satelital ---
  const mapCard=el('div',{class:'card'});
  mapCard.append(el('h2',{},'🛰️ Ubicación satelital'));
  mapCard.append(el('div',{id:'map',class:'mapbox'}));
  mapCard.append(el('div',{class:'btnbar'},
    el('button',{class:'btn blue mini',onclick:ubicarGPSmapa},'📡 GPS'),
    el('button',{class:'btn sec mini',onclick:descargarTiles},'⬇️ Tiles offline'),
    el('button',{class:'btn sec mini',onclick:cargarGeoTIFF},'🗺️ GeoTIFF'),
    el('button',{class:'btn orange mini',onclick:capturarSatelital},'📸 Capturar satelital')));
  mapCard.append(el('div',{class:'muted',id:'coordlbl'},''));
  const satThumb=el('div',{class:'thumbs',id:'satthumb'});
  if(curPunto._satelital)satThumb.append(el('img',{src:'data:image/jpeg;base64,'+curPunto._satelital}));
  mapCard.append(satThumb);
  app.append(mapCard);
  app.append(card);
  setTimeout(()=>initMapPunto(curPunto,f),60);

  const guardarPunto=async()=>{
    const d=f.getData();Object.assign(curPunto,d);curPunto._parent=curProyecto.id;
    curPunto.ID_PROYECTO=curProyecto.ID_PROYECTO||curProyecto.id;
    await put('punto',curPunto);return curPunto;
  };

  // --- secciones hijas ---
  const litos=await childrenOf('litologia',curPunto.id);
  for(const h of HIJAS){
    const card=el('div',{class:'card'});
    const items=await childrenOf(h.store,curPunto.id);
    if(h.store==='litologia')curPunto._nlito=items.length;
    card.append(el('h2',{},h.titulo+' ('+items.length+')'+(h.oblig?' *':'')));
    const box=el('div');card.append(box);
    items.forEach((it,i)=>box.append(bloqueHijo(h,it,i,litos)));
    card.append(el('div',{class:'btnbar'},
      el('button',{class:'btn '+(h.clase==='lito'?'':'orange')+' mini',onclick:async()=>{
        await guardarPunto();
        const reg={id:uid(),_parent:curPunto.id};
        await put(h.store,reg);renderPunto(app);
      }},'+ Agregar '+h.titulo.toLowerCase())));
    app.append(card);
  }

  $('#fab').append(
    el('button',{class:'btn',onclick:async()=>{await guardarPunto();toast('Punto guardado');nav({n:'proyecto',id:curProyecto.id});}},'✓ Guardar punto'),
    el('button',{class:'btn sec',onclick:()=>guardarPunto().then(()=>nav({n:'proyecto',id:curProyecto.id}))},'Volver'),
    nuevo?null:el('button',{class:'btn del',onclick:async()=>{if(confirm('¿Eliminar este punto y sus datos asociados?')){await borrarPunto(curPunto.id);nav({n:'proyecto',id:curProyecto.id});}}},'🗑'));
}

function bloqueHijo(h,reg,i,litos){
  const b=el('div',{class:'child-block'+(h.clase==='lito'?' lito':'')});
  const hd=el('div',{class:'hd'});
  hd.append(el('span',{class:'n'},h.titulo+' '+(i+1)));
  hd.append(el('button',{class:'btn del mini',onclick:async()=>{await del(h.store,reg.id);renderPunto($('#app'));}},'Eliminar'));
  b.append(hd);
  if(h.store==='foto'){ b.append(bloqueFoto(reg,litos)); }
  else if(h.store==='esquema'){ b.append(bloqueEsquema(reg)); }
  else {
    const f=formulario(h.store,reg,{litologias:litos});
    b.append(f.node);
    b._save=async()=>{Object.assign(reg,f.getData());await put(h.store,reg);};
    // guardar al vuelo (blur)
    f.node.addEventListener('change',()=>b._save());
  }
  return b;
}

// -------- Foto --------
function bloqueFoto(reg,litos){
  const wrap=el('div');
  const f=formulario('foto',reg,{litologias:litos});
  wrap.append(f.node);
  const thumbs=el('div',{class:'thumbs'});
  if(reg._img)thumbs.append(el('img',{src:reg._img}));
  const inp=el('input',{type:'file',accept:'image/*',capture:'environment',style:'display:none'});
  inp.addEventListener('change',async e=>{
    const file=e.target.files[0];if(!file)return;
    const img=await comprimir(file,1280,.72);reg._img=img;
    Object.assign(reg,f.getData());await put('foto',reg);
    thumbs.innerHTML='';thumbs.append(el('img',{src:img}));toast('Foto agregada');
  });
  wrap.append(el('div',{class:'btnbar'},
    el('button',{class:'btn blue mini',onclick:()=>inp.click()},'📷 Tomar / elegir foto'),inp),thumbs);
  f.node.addEventListener('change',async()=>{Object.assign(reg,f.getData());await put('foto',reg);});
  return wrap;
}
function comprimir(file,max,q){return new Promise(res=>{const img=new Image();const rd=new FileReader();
  rd.onload=()=>{img.onload=()=>{let{width:w,height:h}=img;if(w>max||h>max){const s=max/Math.max(w,h);w*=s;h*=s;}
    const cv=el('canvas');cv.width=w;cv.height=h;cv.getContext('2d').drawImage(img,0,0,w,h);res(cv.toDataURL('image/jpeg',q));};img.src=rd.result;};rd.readAsDataURL(file);});}

// -------- Esquema (canvas) --------
function bloqueEsquema(reg){
  const wrap=el('div');
  const f=formulario('esquema',reg);wrap.append(f.node);
  const cv=el('canvas',{class:'sketch',width:600,height:340});
  const ctx=cv.getContext('2d');ctx.lineWidth=2;ctx.lineCap='round';ctx.strokeStyle='#153';
  if(reg._img){const im=new Image();im.onload=()=>ctx.drawImage(im,0,0,cv.width,cv.height);im.src=reg._img;}
  let draw=false,lx,ly;
  const pos=e=>{const r=cv.getBoundingClientRect();const t=e.touches?e.touches[0]:e;return[(t.clientX-r.left)*cv.width/r.width,(t.clientY-r.top)*cv.height/r.height];};
  const start=e=>{draw=true;[lx,ly]=pos(e);e.preventDefault();};
  const move=e=>{if(!draw)return;const[x,y]=pos(e);ctx.beginPath();ctx.moveTo(lx,ly);ctx.lineTo(x,y);ctx.stroke();[lx,ly]=[x,y];e.preventDefault();};
  const end=async()=>{if(!draw)return;draw=false;reg._img=cv.toDataURL('image/png');Object.assign(reg,f.getData());await put('esquema',reg);};
  cv.addEventListener('mousedown',start);cv.addEventListener('mousemove',move);window.addEventListener('mouseup',end);
  cv.addEventListener('touchstart',start);cv.addEventListener('touchmove',move);cv.addEventListener('touchend',end);
  wrap.append(cv);
  wrap.append(el('div',{class:'btnbar'},el('button',{class:'btn sec mini',onclick:async()=>{ctx.clearRect(0,0,cv.width,cv.height);reg._img=null;await put('esquema',reg);}},'Limpiar')));
  f.node.addEventListener('change',async()=>{Object.assign(reg,f.getData());await put('esquema',reg);});
  return wrap;
}

async function borrarPunto(id){
  for(const h of HIJAS){const its=await childrenOf(h.store,id);for(const it of its)await del(h.store,it.id);}
  await del('punto',id);
}

// -------- GPS --------
function tomarGPS(f){
  if(!navigator.geolocation){toast('Sin geolocalización');return;}
  toast('Obteniendo GPS…');
  navigator.geolocation.getCurrentPosition(p=>{
    const set=(name,val)=>{const i=f.node.querySelector('[name="'+name+'"]');if(i)i.value=val;};
    set('Coordenadas Geográficas Decimales_Lat',p.coords.latitude.toFixed(6));
    set('Coordenadas Geográficas Decimales_Long',p.coords.longitude.toFixed(6));
    if(p.coords.altitude!=null)set('COTA',Math.round(p.coords.altitude));
    set('PRECISION_GPS','±'+Math.round(p.coords.accuracy)+' m');
    const now=new Date();
    set('FECHA',now.toISOString().slice(0,10));set('HORA',now.toTimeString().slice(0,5));
    toast('GPS ✓ ±'+Math.round(p.coords.accuracy)+' m');
  },e=>toast('GPS error: '+e.message),{enableHighAccuracy:true,timeout:15000});
}

// ============================ Exportación ============================
async function exportMenu(){
  const app=$('#app');app.innerHTML='';$('#fab').innerHTML='';$('#btnBack').style.display='';
  $('#ttl').textContent='Exportar datos';$('#ctx').textContent='';
  const card=el('div',{class:'card'});
  card.append(el('h2',{},'Salidas'));
  card.append(el('div',{class:'muted',html:'Genera los archivos con todos los datos capturados en este dispositivo.'}));
  card.append(el('div',{class:'btnbar',style:'margin-top:12px;flex-direction:column;align-items:stretch'},
    el('button',{class:'btn',onclick:exportCSV},'⇩ CSV (ZIP con las 8 tablas)'),
    el('button',{class:'btn blue',onclick:exportKMZ},'🌎 KMZ (puntos para Google Earth)'),
    el('button',{class:'btn orange',onclick:exportPDF},'📄 PDF — Libreta de terreno')));
  app.append(card);
  $('#fab').append(el('button',{class:'btn sec',onclick:()=>nav({n:'home'})},'‹ Volver'));
}

function descargar(nombre,blob){const a=el('a');a.href=URL.createObjectURL(blob);a.download=nombre;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),4000);}
function csvCell(v){v=v==null?'':String(v);return /[",\n;]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v;}

async function exportCSV(){
  const files=[];
  for(const s of STORES){
    const rows=await all(s);const cs=campos(s).map(c=>c.nombre);
    const extra=['id','_parent'];const cols=extra.concat(cs);
    const lines=[cols.join(',')];
    rows.forEach(r=>lines.push(cols.map(c=>csvCell(c.startsWith('_img')?'':r[c])).join(',')));
    files.push({name:STORE2TBL[s]+'.csv',data:new TextEncoder().encode('﻿'+lines.join('\r\n'))});
  }
  descargar('captura_terreno_CSV.zip', zipStore(files));
  toast('CSV exportado');
}

async function exportKMZ(){
  const puntos=await all('punto');
  const proyectos=await all('proyecto');
  const latF=p=>p['Coordenadas Geográficas Decimales_Lat']||p.LAT;
  const lonF=p=>p['Coordenadas Geográficas Decimales_Long']||p.LONG;
  const files=[]; let pk='', overlays='', n=0;
  for(const p of puntos){
    const lat=parseFloat(latF(p)),lon=parseFloat(lonF(p));if(isNaN(lat)||isNaN(lon))continue;
    n++;
    const litos=await childrenOf('litologia',p.id);
    const ed=campos('punto').filter(c=>p[c.nombre]&&!c.nombre.startsWith('_')).map(c=>'<Data name="'+esc(c.nombre)+'"><value>'+esc(p[c.nombre])+'</value></Data>').join('');
    let satImg='';
    if(p._satelital){const fn='sat_'+p.id+'.jpg';files.push({name:fn,data:b64ToBytes(p._satelital)});
      satImg='<br><img src="'+fn+'" style="max-width:340px"/>';}
    const desc='<![CDATA['+'<b>'+esc(p.ID_PUNTO_CONTROL||'')+'</b><br>'+litos.map(l=>'• '+esc(l.NOMBRE_ROCA||l.TIPO_ROCA||'')).join('<br>')+satImg+']]>';
    pk+='<Placemark><name>'+esc(p.ID_PUNTO_CONTROL||p.id)+'</name><description>'+desc+'</description>'
      +'<ExtendedData>'+ed+'</ExtendedData>'
      +'<Point><coordinates>'+lon+','+lat+',0</coordinates></Point></Placemark>\n';
  }
  // GeoTIFF por proyecto -> GroundOverlay
  for(const pr of proyectos){
    if(pr._geotiffB64&&pr._geotiffBounds){const fn='geotiff_'+pr.id+'.jpg';files.push({name:fn,data:b64ToBytes(pr._geotiffB64)});
      const b=pr._geotiffBounds;
      overlays+='<GroundOverlay><name>GeoTIFF '+esc(pr.NOMBRE_PROYECTO||'')+'</name><Icon><href>'+fn+'</href></Icon>'
        +'<LatLonBox><north>'+b.north+'</north><south>'+b.south+'</south><east>'+b.east+'</east><west>'+b.west+'</west></LatLonBox></GroundOverlay>\n';}
  }
  const kml='<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Captura de terreno</name>\n'+overlays+pk+'</Document></kml>';
  files.unshift({name:'doc.kml',data:new TextEncoder().encode(kml)});
  descargar('captura_terreno.kmz',zipStore(files));
  toast('KMZ exportado ('+n+' puntos'+(files.length>1?', '+(files.length-1)+' imágenes)':')'));
}

// -------- ZIP store-only (sin compresión) --------
function crc32(buf){let c,crc=0xffffffff;for(let i=0;i<buf.length;i++){c=(crc^buf[i])&0xff;for(let k=0;k<8;k++)c=c&1?(c>>>1)^0xEDB88320:c>>>1;crc=(crc>>>8)^c;}return (crc^0xffffffff)>>>0;}
function zipStore(files){
  const enc=s=>new TextEncoder().encode(s);const parts=[];const central=[];let offset=0;
  const u16=n=>[n&255,(n>>8)&255];const u32=n=>[n&255,(n>>8)&255,(n>>16)&255,(n>>24)&255];
  files.forEach(f=>{
    const name=enc(f.name);const data=f.data;const crc=crc32(data);
    const local=[].concat(u32(0x04034b50),u16(20),u16(0),u16(0),u16(0),u16(0),u32(crc),u32(data.length),u32(data.length),u16(name.length),u16(0));
    parts.push(new Uint8Array(local),name,data);
    const cen=[].concat(u32(0x02014b50),u16(20),u16(20),u16(0),u16(0),u16(0),u16(0),u32(crc),u32(data.length),u32(data.length),u16(name.length),u16(0),u16(0),u16(0),u16(0),u32(0),u32(offset));
    central.push(new Uint8Array(cen),name);
    offset+=local.length+name.length+data.length;
  });
  let cenSize=0;central.forEach(p=>cenSize+=p.length);
  const cenOff=offset;
  const end=new Uint8Array([].concat(u32(0x06054b50),u16(0),u16(0),u16(files.length),u16(files.length),u32(cenSize),u32(cenOff),u16(0)));
  return new Blob([...parts,...central,end],{type:'application/zip'});
}

// -------- PDF libreta de terreno (print) --------
async function exportPDF(){
  const proyectos=await all('proyecto');
  let paginas='';
  for(const pr of proyectos){
    const puntos=await childrenOf('punto',pr.id);
    for(const pt of puntos){
      paginas+=await paginaLibreta(pr,pt);
    }
  }
  if(!paginas){toast('No hay puntos para exportar');return;}
  const html='<!DOCTYPE html><html><head><meta charset="utf-8"><title>Libreta de terreno</title><style>'
    +'@page{size:A4;margin:12mm}*{box-sizing:border-box}body{font-family:Arial,sans-serif;color:#111;font-size:10pt;margin:0}'
    +'.pg{page-break-after:always;padding:0 0 6mm}h1{font-size:13pt;margin:0 0 2mm;color:#1f6f4f;border-bottom:2px solid #1f6f4f;padding-bottom:2mm}'
    +'.meta{display:flex;flex-wrap:wrap;gap:2mm 8mm;font-size:9pt;margin:2mm 0}.meta div{min-width:30%}'
    +'.sec{margin-top:3mm}.sec h2{font-size:10.5pt;background:#eef5f1;color:#1f6f4f;padding:1.5mm 2mm;margin:0 0 1mm;border-left:3px solid #1f6f4f}'
    +'table{width:100%;border-collapse:collapse;font-size:8.5pt;margin-bottom:1mm}td,th{border:1px solid #bbb;padding:1.5mm;text-align:left;vertical-align:top}th{background:#f4f5f7}'
    +'.imgs{display:flex;flex-wrap:wrap;gap:2mm}.imgs figure{margin:0;width:46%}.imgs img{width:100%;border:1px solid #999}.imgs figcaption{font-size:8pt;color:#555}'
    +'.lbl{color:#666;font-weight:bold}</style></head><body>'+paginas+'</body></html>';
  let ifr=$('#pdf-iframe');if(ifr)ifr.remove();
  ifr=el('iframe',{id:'pdf-iframe',style:'position:fixed;left:-9999px;top:-9999px;width:210mm;height:297mm;border:none'});
  document.body.append(ifr);ifr.contentDocument.open();ifr.contentDocument.write(html);ifr.contentDocument.close();
  setTimeout(()=>{ifr.contentWindow.focus();ifr.contentWindow.print();setTimeout(()=>ifr.remove(),1500);},700);
}

function tablaRegs(store,regs){
  if(!regs.length)return '<p class="lbl" style="font-size:8.5pt">—</p>';
  const cs=campos(store).map(c=>c.nombre).filter(n=>!esFK(n)&&n!==pkDe(store));
  let h='<table><tr>'+cs.map(c=>'<th>'+esc(c.replace(/_/g,' '))+'</th>').join('')+'</tr>';
  regs.forEach(r=>{h+='<tr>'+cs.map(c=>'<td>'+esc(r[c]||'')+'</td>').join('')+'</tr>';});
  return h+'</table>';
}
async function paginaLibreta(pr,pt){
  const lat=pt['Coordenadas Geográficas Decimales_Lat']||pt.LAT||'';
  const lon=pt['Coordenadas Geográficas Decimales_Long']||pt.LONG||'';
  const litos=await childrenOf('litologia',pt.id);
  const estr=await childrenOf('estructural',pt.id);
  const cont=await childrenOf('contacto',pt.id);
  const mues=await childrenOf('muestreo',pt.id);
  const fotos=await childrenOf('foto',pt.id);
  const esqs=await childrenOf('esquema',pt.id);
  let imgs='';
  fotos.forEach((f,i)=>{if(f._img)imgs+='<figure><img src="'+f._img+'"><figcaption>Foto '+(i+1)+' '+esc(f.ORIENTACION_FOTO||'')+' — '+esc(f.COMENTARIO_FOTO||'')+'</figcaption></figure>';});
  esqs.forEach((e,i)=>{if(e._img)imgs+='<figure><img src="'+e._img+'"><figcaption>Esquema '+(i+1)+' — '+esc(e.OBSERVACION||'')+'</figcaption></figure>';});
  return '<div class="pg"><h1>Libreta de terreno — '+esc(pt.ID_PUNTO_CONTROL||pt.id)+'</h1>'
    +'<div class="meta"><div><span class="lbl">Proyecto:</span> '+esc(pr.NOMBRE_PROYECTO||'')+'</div>'
    +'<div><span class="lbl">Geólogo:</span> '+esc(pt.GEOLOGO||'')+'</div>'
    +'<div><span class="lbl">Fecha/Hora:</span> '+esc((pt.FECHA||'')+' '+(pt.HORA||''))+'</div>'
    +'<div><span class="lbl">Coord:</span> '+esc(lat)+', '+esc(lon)+'  (cota '+esc(pt.COTA||'—')+')</div>'
    +'<div><span class="lbl">Localidad:</span> '+esc(pt.NOMBRE_LOCALIDAD||'')+'</div>'
    +'<div><span class="lbl">Geomorfología:</span> '+esc(pt.CONTEXTO_GEOMORFOLOGICO||'')+'</div></div>'
    +'<div class="sec"><h2>Litología ('+litos.length+')</h2>'+tablaRegs('litologia',litos)+'</div>'
    +(estr.length?'<div class="sec"><h2>Datos estructurales</h2>'+tablaRegs('estructural',estr)+'</div>':'')
    +(cont.length?'<div class="sec"><h2>Contactos</h2>'+tablaRegs('contacto',cont)+'</div>':'')
    +(mues.length?'<div class="sec"><h2>Muestreo</h2>'+tablaRegs('muestreo',mues)+'</div>':'')
    +(imgs?'<div class="sec"><h2>Fotografías y esquemas</h2><div class="imgs">'+imgs+'</div></div>':'')
    +'</div>';
}

// ============================ Init ============================
(async()=>{
  await openDB();
  if(MODELO.avisos&&MODELO.avisos.length){/* dominios provisionales existen; ver JSON */}
  render();
  if('serviceWorker' in navigator){try{await navigator.serviceWorker.register('sw.js');}catch(e){}}
})();
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
def escribir_iconos():
    d = os.path.join(HERE, "icons"); os.makedirs(d, exist_ok=True)
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
        "description": "Libreta digital de geología básica en terreno, offline (captura, mapa satelital y export CSV/KMZ/PDF).",
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
    sw = r"""// Service worker offline-first (cache estatico)
const CACHE='geoterreno-cdc-v4';
const ASSETS=['./','./index.html','./manifest.json','./icons/icon-192.png','./icons/icon-512.png',
  './vendor/leaflet.css','./vendor/leaflet.js','./vendor/idb.js','./vendor/leaflet.offline.js',
  './vendor/georaster.browser.bundle.min.js','./vendor/georaster-layer-for-leaflet.min.js',
  './vendor/images/marker-icon.png','./vendor/images/marker-icon-2x.png','./vendor/images/marker-shadow.png',
  './vendor/images/layers.png','./vendor/images/layers-2x.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;
  e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request).then(resp=>{
    const cp=resp.clone();caches.open(CACHE).then(c=>c.put(e.request,cp));return resp;
  }).catch(()=>caches.match('./index.html'))));});
"""
    with open(os.path.join(HERE, "sw.js"), "w", encoding="utf-8") as fh:
        fh.write(sw)

def main():
    html = HTML.replace("__MODELO_JSON__", modelo_json)
    with open(OUT_HTML, "w", encoding="utf-8") as fh:
        fh.write(html)
    escribir_manifest(); escribir_sw(); escribir_iconos()
    print("OK PWA generada:")
    print("  index.html", len(html), "bytes")
    print("  manifest.json, sw.js, icons/icon-192.png, icons/icon-512.png")

if __name__ == "__main__":
    main()
