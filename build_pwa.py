# -*- coding: utf-8 -*-
"""
Build de la PWA 'Captura de datos en terreno' (Track A).

Inyecta modelo_canonico.json en un index.html monolitico offline.
Genera tambien manifest.json, sw.js e iconos PNG minimos.
Sin Node. Solo stdlib. Ejecutar tras (re)generar el modelo canonico.

!!! NO EJECUTAR TAL CUAL (2026-08-12) !!!
Las funciones de colecciones Terreno/Gabinete (storeActivo, toggleColeccion,
updateFormReadonly), respaldo JSON (buildBackupBlob, importBackup), import de
KMZ (parseKmzFile, insertKmzGeometries) y su UI se agregaron DIRECTO en
index.html (commits 421dbb6..ef3a761) y NO estan en esta plantilla todavia.
Correr este script regenera index.html y sw.js y BORRA todo eso.
Portar esos bloques aca antes de volver a usarlo.
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
  .collap{padding:0;overflow:hidden}
  .collap-head{display:flex;align-items:center;gap:9px;padding:13px 14px;cursor:pointer;font-weight:650;color:var(--verde);font-size:14px;-webkit-user-select:none;user-select:none}
  .collap-head .ctitle{flex:1;letter-spacing:.2px}
  .collap-head .pill{font-weight:600}
  .collap-body{display:none;padding:0 14px 14px}
  .collap.open .collap-body{display:flex;flex-direction:column}
  .collap-fin{order:99}
  .collap.lleno{border-left:4px solid var(--verde2)}
  .collap.lleno .collap-head{color:var(--verde2)}
  .collap.lleno .collap-head .ctitle::after{content:' ✓';font-weight:700}
  .chev{font-size:11px;color:var(--muted);width:12px;text-align:center}
  .collap-fin{display:flex;justify-content:flex-end;margin-top:10px}
  .collap-fin button{background:var(--surface2);color:var(--muted);border:1px solid var(--bd);font-size:12px;padding:6px 16px}
  .multichips{display:flex;flex-wrap:wrap;gap:6px}
  .multichips .chip{display:inline-flex;align-items:center;gap:5px;padding:6px 11px;border:1px solid var(--inp-bd);border-radius:20px;background:var(--inp);font-size:13px;cursor:pointer}
  .multichips .chip.on{background:var(--verde);color:#fff;border-color:var(--verde)}
  .multichips .chip input{width:15px;height:15px;margin:0}
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
  .medbar{flex:0 0 100%;width:100%;background:var(--surface2);border:1px solid var(--bd);border-radius:10px;padding:8px 10px;margin-bottom:9px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
  .mapfull{height:66vh;min-height:340px;width:100%;border-radius:10px;overflow:hidden;z-index:0}
  .mapbig{height:calc(100vh - 162px);height:calc(100dvh - 162px);min-height:320px;width:100%;border-radius:10px;overflow:hidden;z-index:0}
  .mapcard{padding:0;margin-bottom:6px;overflow:hidden;position:relative}
  .drawbanner{position:absolute;top:8px;left:8px;right:8px;z-index:500;background:rgba(20,30,22,.92);color:#fff;border-radius:9px;padding:8px 10px;display:flex;gap:8px;align-items:center;font-size:12px;box-shadow:0 3px 12px rgba(0,0,0,.4)}
  .drawbanner span{flex:1}
  .drawbanner .btn{padding:6px 10px}
  .modtoggle{display:flex;gap:8px;margin-bottom:8px}
  .modtoggle .btn{flex:1;font-size:13px;padding:8px}
  .fab.compact{padding:6px 10px}
  .fab.compact .btn{padding:7px 10px;font-size:12.5px}
  .estsym{background:none;border:none}
  .ptlabel{background:rgba(20,30,22,.72);color:#fff;border:none;border-radius:4px;font-size:10px;font-weight:600;padding:1px 5px;box-shadow:none;white-space:nowrap}
  .ptlabel:before{display:none!important}
  .fpin img{width:44px;height:44px;object-fit:cover;border:2px solid #fff;border-radius:8px;box-shadow:0 1px 5px rgba(0,0,0,.55);cursor:pointer}
  .fmbread{display:flex;flex-wrap:wrap;gap:4px;align-items:center;font-size:12px;margin-bottom:8px}
  .fmbread a{color:var(--azul);cursor:pointer}
  .fmov{position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:200;display:flex;align-items:center;justify-content:center;padding:14px}
  .fmov img{max-width:96vw;max-height:92vh;object-fit:contain;border-radius:8px}
  .sensorwrap{display:flex;gap:6px;align-items:stretch}
  .sensorwrap input{flex:1;min-width:0}
  .sensorwrap .btn{white-space:nowrap;padding:0 13px;font-size:16px}
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
const APP_VER = 'v32';   // se muestra en Proyectos; subir junto con el cache del SW
// ============================ Utilidades ============================
const $ = s => document.querySelector(s);
const el = (t,a={},...c)=>{const e=document.createElement(t);for(const k in a){if(k==='class')e.className=a[k];else if(k==='html')e.innerHTML=a[k];else if(k.startsWith('on'))e.addEventListener(k.slice(2),a[k]);else e.setAttribute(k,a[k]);}c.flat().forEach(x=>e.append(x&&x.nodeType?x:document.createTextNode(x==null?'':x)));return e;};
const uid = ()=> 'x'+Date.now().toString(36)+Math.random().toString(36).slice(2,7);
function toast(m){const t=$('#toast');t.textContent=m;t.classList.add('on');clearTimeout(t._t);t._t=setTimeout(()=>t.classList.remove('on'),2200);}
const esc = s => (s==null?'':String(s)).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

// Campos "pegajosos": se recuerdan entre puntos (por dispositivo) para no re-escribirlos cada vez.
const STICKY=['GEOLOGO','PROYECCION','FUENTE_COORDENADAS','METODO_UBICACION','CONTEXTO_GEOMORFOLOGICO','NOMBRE_LOCALIDAD'];
function stickyGet(){try{return JSON.parse(localStorage.getItem('gt-sticky')||'{}');}catch(e){return {};}}
function stickySet(reg){const s=stickyGet();STICKY.forEach(k=>{if(reg[k])s[k]=reg[k];});localStorage.setItem('gt-sticky',JSON.stringify(s));}
function ahora(){const d=new Date();return {FECHA:d.toISOString().slice(0,10),HORA:d.toTimeString().slice(0,5)};}

// Mapa store -> tabla del modelo
const STORE2TBL = {proyecto:'TBL_PROYECTO',punto:'PUNTO_CONTROL',litologia:'TBL_LITOLOGIA',
  estructural:'TBL_DATOS_ESTRUCTURALES',contacto:'TBL_CONTACTO',muestreo:'TBL_MUESTREO',
  foto:'TBL_FOTOGRAFIAS',esquema:'TBL_ESQUEMA_DIBUJO',geomorf:'TBL_GEOMORFOLOGIA'};
const STORES = Object.keys(STORE2TBL);
// 'linea' no cuelga de un punto (es una capa aparte, hermana de PUNTO_CONTROL) -> no entra
// en STORES/HIJAS, pero necesita su propia tabla del modelo para el formulario/exports.
const LINEA_TBL = 'LINEA_CONTROL';
const HIJAS = [
  {store:'litologia', titulo:'Litología', clase:'lito', oblig:true},
  {store:'estructural', titulo:'Datos estructurales', clase:''},
  {store:'contacto', titulo:'Contactos', clase:''},
  {store:'geomorf', titulo:'Geomorfología', clase:''},
  {store:'muestreo', titulo:'Muestreo', clase:''},
  {store:'foto', titulo:'Fotografías', clase:''},
  {store:'esquema', titulo:'Esquemas / dibujos', clase:''},
];
function campos(store){return (MODELO.tablas[store==='linea'?LINEA_TBL:STORE2TBL[store]]||{}).campos||[];}
function pkDe(store){return (MODELO.tablas[store==='linea'?LINEA_TBL:STORE2TBL[store]]||{}).pk;}

// ============================ IndexedDB ============================
const DB='captura-terreno', VER=4;   // v4: nuevo store 'geomorf' (TBL_GEOMORFOLOGIA)
let db;
function openDB(){return new Promise((res,rej)=>{
  let done=false; const finish=(fn,v)=>{if(!done){done=true;fn(v);}};
  const r=indexedDB.open(DB,VER);
  r.onupgradeneeded=()=>{const d=r.result;STORES.concat(['fotomapa','linea']).forEach(s=>{if(!d.objectStoreNames.contains(s)){const os=d.createObjectStore(s,{keyPath:'id'});
    if(s!=='proyecto')os.createIndex('parent','_parent',{unique:false});}});};
  r.onsuccess=()=>{db=r.result;
    db.onversionchange=()=>{try{db.close();}catch(e){}};   // libera para que otra instancia pueda actualizar
    finish(res,db);};
  r.onerror=()=>finish(rej,r.error||new Error('IndexedDB error'));
  r.onblocked=()=>finish(rej,new Error('BLOCKED'));         // otra pestaña/instancia tiene la BD abierta
  setTimeout(()=>finish(rej,new Error('TIMEOUT')),6000);    // no colgar la app indefinidamente
});}
// carga una imagen comprimida devolviendo dataURL + dimensiones naturales (para el foto-mapa)
function cargarImagen(file,max,q){return new Promise(res=>{const img=new Image();const rd=new FileReader();
  rd.onload=()=>{img.onload=()=>{let w=img.width,h=img.height;const s=Math.min(1,max/Math.max(w,h));w=Math.round(w*s);h=Math.round(h*s);
    const cv=el('canvas');cv.width=w;cv.height=h;cv.getContext('2d').drawImage(img,0,0,w,h);res({dataUrl:cv.toDataURL('image/jpeg',q),w,h});};img.src=rd.result;};rd.readAsDataURL(file);});}
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
  if(/COTA|AZIMUT|MANTEO|BUZAMIENTO|PESO|VOLUMEN|RUMBO|ORIENTACION|TREND|PLUNGE/.test(n)) return 'number';
  if(n==='FECHA') return 'date';
  if(n==='HORA') return 'time';
  if(/DESCRIPCION|OBSERVACION|COMENTARIO|RELACION_LITOLOGIA|DISTRIBUCION/.test(n)) return 'textarea';
  return 'text';
}
const esPK = (store,n)=> n===pkDe(store);
const esFK = n => ['ID_PUNTO_CONTROL','ID_PROYECTO','ID_LITOLOGIA','ID_ESQUEMA','ID_FOTOGRAFIA','ID_FOTOGRAFIA_ASOCIADA'].includes(n);
// Claves de negocio que el usuario SÍ nombra (visibles/editables); el resto de ids son técnicos y se ocultan.
const NOMBRABLES = new Set(['ID_PROYECTO','ID_PUNTO_CONTROL','ID_MUESTRA']);
function hideField(store,n){
  if((store!=='proyecto'&&store!=='punto') && (n==='ID_PUNTO_CONTROL'||n==='ID_PROYECTO')) return true; // FK a padre en hijas
  if(store==='punto' && n==='ID_PROYECTO') return true;                                                  // FK proyecto en punto
  if(n===pkDe(store)) return !NOMBRABLES.has(n);                                                          // PK propio: ocultar salvo nombrables
  if(n==='ID_LITOLOGIA') return store==='litologia';                                                      // FK selector en estructural/foto; PK oculto en litología
  if(['ID_ESTRUCTURA','ID_CONTACTO','ID_FOTOGRAFIA','ID_ESQUEMA'].includes(n)) return true;               // ids técnicos
  return false;
}

// Campos condicionales: se muestran/habilitan solo si se cumple la regla; si no, se limpian.
//  modo 'bloquear' = se deshabilita y atenúa · modo 'ocultar' = se esconde por completo.
const CONDICIONALES = {
  // Una litología es roca O depósito: TIPO_DEPOSITO solo con TIPO_ROCA = "Depósito".
  TIPO_DEPOSITO: {modo:'bloquear', regla: v => v['TIPO_ROCA']==='Depósito'},
  // Granulometría solo para siliciclásticos y piroclásticos (la cascada tiene opciones solo para esos).
  GRANULOMETRIA: {modo:'ocultar', regla: v => opciones('GRANULOMETRIA', v['NOMBRE_ROCA']).length>0},
  // Tipo de falla solo cuando la estructura medida es una falla (formulario de punto).
  TIPO_FALLA: {modo:'ocultar', regla: v => v['TIPO_ESTRUCTURA']==='Estructura falla'},
  // --- LINEA_CONTROL: el tipo y el subtipo los resuelve la cascada
  // CLASE_LINEA→TIPO_LINEA→SUBTIPO_LINEA, no reglas condicionales. Aquí solo quedan
  // el subtipo (hay tipos sin subtipos: el select vacío se esconde, mismo criterio que
  // GRANULOMETRIA) y las unidades techo/base, que solo tienen sentido en un contacto.
  SUBTIPO_LINEA: {modo:'ocultar', regla: v => opciones('SUBTIPO_LINEA', v['TIPO_LINEA']).length>0},
  UNIDAD_TECHO_LINEA: {modo:'ocultar', regla: v => v['CLASE_LINEA']==='Contacto'},
  UNIDAD_BASE_LINEA:  {modo:'ocultar', regla: v => v['CLASE_LINEA']==='Contacto'},
};

// Construye el DOM de un formulario para (store, registro). Devuelve {node, getData}
function formulario(store, reg, ctx){
  const cont=el('div');
  const inputs={};
  const cs=campos(store).filter(c=> !hideField(store,c.nombre));
  const rowWrap=el('div',{class:'row'});
  cs.forEach(campo=>{
    const n=campo.nombre;
    const fld=el('div',{class:'fld'});
    const lab=el('label',{},n.replace(/_/g,' '));
    if(campo.obligatorio) lab.append(el('span',{class:'req'},'*'));
    fld.append(lab);
    let inp;
    const w=tipoWidget(campo);
    if(w==='select' && campo.multiple){
      // selección múltiple: grupo de chips con checkbox (ej. propósito de análisis)
      inp=el('div',{class:'multichips'});
      const sel=new Set((reg[n]?String(reg[n]).split(/\s*;\s*/):[]).filter(Boolean));
      opciones(campo.dominio,null).forEach(o=>{
        const chip=el('label',{class:'chip'+(sel.has(o.value)?' on':'')});
        const cb=el('input',{type:'checkbox'});cb.checked=sel.has(o.value);cb.value=o.value;
        cb.addEventListener('change',()=>chip.classList.toggle('on',cb.checked));
        chip.append(cb,el('span',{},o.label));inp.append(chip);
      });
      inp.name=n; inp._multi=true;
    } else if(w==='select'){
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
    // FK PUNTOS_APOYO -> multi-selección de puntos de control del proyecto activo
    if(n==='PUNTOS_APOYO' && ctx && ctx.puntos){
      inp=el('div',{class:'multichips'});
      const sel=new Set((reg[n]?String(reg[n]).split(/\s*;\s*/):[]).filter(Boolean));
      ctx.puntos.forEach(p=>{
        const chip=el('label',{class:'chip'+(sel.has(p.id)?' on':'')});
        const cb=el('input',{type:'checkbox'});cb.checked=sel.has(p.id);cb.value=p.id;
        cb.addEventListener('change',()=>chip.classList.toggle('on',cb.checked));
        chip.append(cb,el('span',{},p.ID_PUNTO_CONTROL||p.id.slice(0,6)));inp.append(chip);
      });
      inp.name=n; inp._multi=true;
    }
    inputs[n]=inp;
    const sensor = tipoSensor(n);
    // en tablas con plano (estructural/contacto) se usa la barra de medición combinada, no botones sueltos
    if(sensor && w==='number' && !PLANO_CAMPOS[store]) fld.append(sensorInput(inp,sensor));
    else fld.append(inp);
    if(campo.nota) fld.append(el('div',{class:'nota'},campo.nota));
    rowWrap.append(fld);
  });
  cont.append(rowWrap);

  // habilita/oculta campos condicionales según los valores actuales
  function aplicarCondicionales(){
    const v={};for(const k in inputs)v[k]=inputs[k].value;
    for(const cn in CONDICIONALES){
      const inp=inputs[cn]; if(!inp)continue;
      const {modo,regla}=CONDICIONALES[cn];
      const ok=regla(v);
      const fld=inp.closest('.fld');
      if(modo==='ocultar'){ if(fld)fld.style.display=ok?'':'none'; }
      else { inp.disabled=!ok; if(fld)fld.style.opacity=ok?'':'0.5'; }
      if(!ok){ if(inp.value)inp.value=''; inp.required=false; }
      else { const cd=cs.find(c=>c.nombre===cn); if(cd&&cd.obligatorio)inp.required=true; }
    }
  }
  // repuebla recursivamente los selects hijos de 'parentName' (cadena TIPO_ROCA→NOMBRE_ROCA→GRANULOMETRIA)
  function repoblarHijosDe(parentName, parentValue){
    Object.values(inputs).forEach(inp=>{
      if(inp.tagName==='SELECT' && inp.dataset.cascadaPadre===parentName){
        const campo=cs.find(c=>c.nombre===inp.name);
        inp.innerHTML='';inp.append(el('option',{value:''},'— seleccionar —'));
        opciones(campo.dominio, parentValue).forEach(o=>inp.append(el('option',{value:o.value},o.label)));
        inp.value='';
        repoblarHijosDe(inp.name,'');   // nietos: su padre quedó vacío
      }
    });
  }
  aplicarCondicionales();

  // cascadas: al cambiar el padre, repoblar hijos (y nietos)
  cont.addEventListener('change',e=>{
    const changed=e.target.name; if(!changed)return;
    repoblarHijosDe(changed, e.target.value);
    aplicarCondicionales();
    // dominio abierto "agregar nuevo"
    if(e.target.tagName==='SELECT' && e.target.value==='__add__'){
      const campo=cs.find(c=>c.nombre===e.target.name);
      const nv=prompt('Nuevo valor para '+e.target.name.replace(/_/g,' ')+':');
      if(nv){dominio(campo.dominio).valores.push(nv);
        const opt=el('option',{value:nv},nv);e.target.insertBefore(opt,e.target.querySelector('option[value="__add__"]'));e.target.value=nv;}
      else e.target.value='';
    }
  });

  return {node:cont, getData(){const o={};for(const n in inputs){const i=inputs[n];
    o[n]= i._multi ? [...i.querySelectorAll('input:checked')].map(c=>c.value).join('; ') : i.value;
  } return o;}};
}

// ============================ Mapa satelital (Leaflet + Esri) ============================
const ESRI_URL='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
const ICONO=L.icon({iconUrl:'vendor/images/marker-icon.png',iconRetinaUrl:'vendor/images/marker-icon-2x.png',shadowUrl:'vendor/images/marker-shadow.png',iconSize:[25,41],iconAnchor:[12,41],popupAnchor:[1,-34],shadowSize:[41,41]});
let mapa=null, marcador=null, gtLayer=null, savetiles=null;
const inLat='Coordenadas Geográficas Decimales_Lat', inLon='Coordenadas Geográficas Decimales_Long';

// capas base (satelital + relieve/topo con curvas de nivel) + control de tiles offline.
// Todas con CORS habilitado (verificado 2026-07-11) para poder guardar tiles offline.
const BASES=[
  {nombre:'🛰️ Satelital (Esri)', url:ESRI_URL, attr:'Tiles © Esri', maxz:19},
  {nombre:'⛰️ Topo Esri (relieve + curvas)', url:'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', attr:'Tiles © Esri', maxz:19},
  {nombre:'🗻 OpenTopoMap (curvas de nivel)', url:'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', attr:'© OpenTopoMap (CC-BY-SA)', maxz:17},
];
function capaSatelital(map){
  const capas={};
  BASES.forEach((b,i)=>{
    const tl=(L.tileLayer.offline?L.tileLayer.offline:L.tileLayer)(b.url,
      {attribution:b.attr,maxZoom:19,maxNativeZoom:b.maxz,crossOrigin:true,subdomains:'abc'});
    tl._maxz=b.maxz; tl._nombreBase=b.nombre;
    capas[b.nombre]=tl;
    if(i===0)tl.addTo(map);
  });
  L.control.layers(capas,null,{position:'topright'}).addTo(map);
  if(L.control&&L.control.savetiles){
    const st=L.control.savetiles(capas[BASES[0].nombre],{zoomlevels:[13,14,15,16,17],
      confirm(l,cb){const zl=st.options.zoomlevels||[];const n=(l&&l._tilesforSave)?l._tilesforSave.length+' ':'';
        if(confirm('¿Descargar '+n+'tiles de '+(st._nombreBase||'la capa actual')+' (zoom '+zl[0]+'–'+zl[zl.length-1]+') para uso offline?'))cb();},
      confirmRemoval(l,cb){if(confirm('¿Borrar tiles guardados?'))cb();},saveText:'⬇️',rmText:'🗑️'});
    st._maxz=19; st._nombreBase=BASES[0].nombre;
    st.addTo(map);
    // al cambiar de capa base, el control de descarga apunta a la capa activa
    map.on('baselayerchange',e=>{st.setLayer(e.layer);st._maxz=e.layer._maxz||19;st._nombreBase=e.layer._nombreBase||'';});
    return st;
  }
  return null;
}
// selector de zoom máximo antes de descargar (estilo StraboSpot; el plugin lee options.zoomlevels al guardar)
function descargarTilesConZoom(){
  const a=document.querySelector('a.savetiles');
  if(!a||!savetiles){toast('Descarga offline no disponible (recarga con conexión)');return;}
  const maxz=savetiles._maxz||19;
  const ov=el('div',{class:'fmov',onclick:e=>{if(e.target===ov)ov.remove();}});
  const box=el('div',{class:'card',style:'max-width:420px;width:92vw'});
  box.append(el('h2',{},'⬇️ Descargar tiles offline'));
  box.append(el('div',{class:'muted',html:'Capa: <b>'+(savetiles._nombreBase||'actual')+'</b>. Se descarga el <b>área visible</b>. Cada nivel extra ≈ <b>4× más</b> tiles. Para z18–19 acércate primero al sector de interés.'
    +(maxz<19?'<br>⚠️ Esta capa llega hasta <b>z'+maxz+'</b>.':'')}));
  const bar=el('div',{class:'btnbar',style:'margin-top:10px;flex-direction:column;align-items:stretch'});
  [[17,'Zoom 13–17 · estándar (liviano)','btn'],
   [18,'Zoom 13–18 · detalle (~4× más)','btn blue'],
   [19,'Zoom 13–19 · máximo detalle (~16× más)','btn orange']].filter(([mz])=>mz<=maxz).forEach(([mz,txt,cls])=>{
    bar.append(el('button',{class:cls,onclick:()=>{
      const zl=[];for(let z=13;z<=mz;z++)zl.push(z);
      savetiles.options.zoomlevels=zl;
      ov.remove(); a.click();
    }},txt));
  });
  bar.append(el('button',{class:'btn sec',onclick:()=>ov.remove()},'Cancelar'));
  box.append(bar);ov.append(box);document.body.append(ov);
}

function initMapPunto(reg, f){
  const la=parseFloat(reg[inLat]), lo=parseFloat(reg[inLon]);
  const lat=isNaN(la)?-33.45:la, lon=isNaN(lo)?-70.65:lo;
  if(mapa){try{mapa.remove();}catch(e){}mapa=null;}
  mapa=L.map('map',{center:[lat,lon],zoom:isNaN(la)?5:16});
  savetiles=capaSatelital(mapa);
  marcador=L.marker([lat,lon],{draggable:true,icon:ICONO}).addTo(mapa);
  const iLat=()=>f.node.querySelector('[name="'+inLat+'"]'), iLon=()=>f.node.querySelector('[name="'+inLon+'"]');
  const sync=()=>{const ll=marcador.getLatLng();if(iLat())iLat().value=ll.lat.toFixed(6);if(iLon())iLon().value=ll.lng.toFixed(6);
    const cl=document.getElementById('coordlbl');if(cl)cl.textContent='📍 '+ll.lat.toFixed(6)+', '+ll.lng.toFixed(6);};
  marcador.on('dragend',sync);
  mapa.on('click',e=>{marcador.setLatLng(e.latlng);sync();});   // tocar el mapa reubica el pin
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
function descargarTiles(){descargarTilesConZoom();}

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

// ============================ Clinómetro (plano + lineación) ============================
// Mide rumbo/manteo (y trend/plunge de una línea) con los sensores del teléfono.
// Muestrea 3 s, calcula el vector normal al plano (eje Z del teléfono) y el eje mayor (eje Y)
// en marco Este-Norte-Arriba, y promedia los VECTORES (media esférica, correcta cerca de 0/360°).
const CLINO_MS = 3000;         // duración del muestreo (3 s, aprobado)
const D2R = Math.PI/180, R2D = 180/Math.PI;
const PLANO_CAMPOS = {
  estructural: {rumbo:'AZIMUT', manteo:'MANTEO_BUZAMIENTO', trend:'TREND', plunge:'PLUNGE', conf:'GRADO_CONFIANZA_ESTRUCTURA'},
  contacto:    {rumbo:'RUMBO_CONTACTO', manteo:'MANTEO_CONTACTO', conf:'GRADO_CONFIANZA_CONTACTO'},
};
// alpha absoluto por plataforma (Android: alpha absoluto; iOS: 360 - webkitCompassHeading)
function anglesFromEvent(e){
  let a=e.alpha;
  if(typeof e.webkitCompassHeading==='number') a=(360-e.webkitCompassHeading);
  if(a==null||e.beta==null||e.gamma==null) return null;
  return {a:a*D2R, b:e.beta*D2R, g:e.gamma*D2R};
}
// vectores en mundo ENU: n = normal a la pantalla (eje Z), L = eje mayor del teléfono (eje Y)
function ejesMundo(a,b,g){
  const cA=Math.cos(a),sA=Math.sin(a),cB=Math.cos(b),sB=Math.sin(b),cG=Math.cos(g),sG=Math.sin(g);
  const n=[cA*sG+sA*sB*cG, sA*sG-cA*sB*cG, cB*cG];
  const L=[-sA*cB, cA*cB, sB];
  return {n,L};
}
function normaliza(v){const m=Math.hypot(v[0],v[1],v[2])||1;return [v[0]/m,v[1]/m,v[2]/m];}
function media(vecs){const s=[0,0,0];vecs.forEach(v=>{s[0]+=v[0];s[1]+=v[1];s[2]+=v[2];});return normaliza(s);}
function planoDeNormal(n){
  if(n[2]<0)n=[-n[0],-n[1],-n[2]];                       // hemisferio superior
  const dip=Math.acos(Math.max(-1,Math.min(1,n[2])))*R2D;
  const dipDir=((Math.atan2(n[0],n[1])*R2D)+180+360)%360;
  const strike=(dipDir-90+360)%360;                      // regla de la mano derecha
  return {rumbo:strike, manteo:dip};
}
function lineaDeVector(L){
  if(L[2]>0)L=[-L[0],-L[1],-L[2]];                       // apunta hacia abajo (plunge ≥ 0)
  const plunge=-Math.asin(Math.max(-1,Math.min(1,L[2])))*R2D;
  const trend=((Math.atan2(L[0],L[1])*R2D)+360)%360;
  return {trend, plunge};
}
function dispersionGrados(vecs,m){    // ángulo medio entre cada lectura y la media (calidad)
  if(!vecs.length)return 99;
  let s=0;vecs.forEach(v=>{const d=Math.max(-1,Math.min(1,v[0]*m[0]+v[1]*m[1]+v[2]*m[2]));s+=Math.acos(Math.abs(d));});
  return (s/vecs.length)*R2D;
}
async function medirEstructura(modo, onTick){   // modo: 'plano' | 'linea'
  if(!(await ensureOrientPerm())) return null;
  const evt=('ondeviceorientationabsolute' in window)?'deviceorientationabsolute':'deviceorientation';
  const normals=[], lines=[];
  return new Promise(res=>{
    const on=e=>{const ang=anglesFromEvent(e);if(!ang)return;const {n,L}=ejesMundo(ang.a,ang.b,ang.g);
      normals.push(n[2]<0?[-n[0],-n[1],-n[2]]:n);
      lines.push(L[2]>0?[-L[0],-L[1],-L[2]]:L);};
    window.addEventListener(evt,on);
    const t0=Date.now(); let iv=null;
    if(onTick){iv=setInterval(()=>onTick(Math.max(0,Math.ceil((CLINO_MS-(Date.now()-t0))/1000))),250);}
    setTimeout(()=>{window.removeEventListener(evt,on);if(iv)clearInterval(iv);
      if(!normals.length){res(null);return;}
      const mn=media(normals), pl=planoDeNormal(mn), disp=dispersionGrados(normals,mn);
      const out={...pl, n:normals.length, disp};
      if(modo==='linea'){Object.assign(out, lineaDeVector(media(lines)));}
      res(out);
    }, CLINO_MS);
  });
}
// barra de medición para bloques con plano (estructural, contacto)
function barraMedicion(store, f){
  const map=PLANO_CAMPOS[store]; if(!map)return null;
  const bar=el('div',{class:'medbar'});
  bar.append(el('span',{class:'muted',style:'font-weight:700'},'📡 Medir:'));
  const status=el('span',{class:'muted',style:'flex-basis:100%'});
  const setV=(campo,val)=>{if(!campo||val==null)return;const i=f.node.querySelector('[name="'+campo+'"]');
    if(i){i.value=Math.round(val);i.dispatchEvent(new Event('change',{bubbles:true}));}};
  const medir=async(modo)=>{
    status.textContent='📡 Mantén el teléfono firme… 3';
    const r=await medirEstructura(modo, s=>status.textContent='📡 Mantén firme… '+s);
    if(!r){status.textContent='⚠️ Sin sensor / permiso — ingresa manual';toast('Sin sensor de orientación');return;}
    setV(map.rumbo,r.rumbo); setV(map.manteo,r.manteo);
    if(modo==='linea'){setV(map.trend,r.trend); setV(map.plunge,r.plunge);}
    const conf=r.disp<2?'ALTA':(r.disp<5?'MEDIA':'BAJA');
    const cg=f.node.querySelector('[name="'+map.conf+'"]'); if(cg&&!cg.value){cg.value=conf;cg.dispatchEvent(new Event('change',{bubbles:true}));}
    status.textContent='✓ '+r.n+' lecturas · ±'+r.disp.toFixed(1)+'° · '+conf
      +'  →  '+Math.round(r.rumbo)+'/'+Math.round(r.manteo)+(r.trend!=null?'  · L '+Math.round(r.trend)+'/'+Math.round(r.plunge):'');
  };
  bar.append(el('button',{type:'button',class:'btn blue mini',onclick:()=>medir('plano')},'📐 Medir plano'));
  if(map.trend)bar.append(el('button',{type:'button',class:'btn orange mini',onclick:()=>medir('linea')},'📏 Plano + línea'));
  bar.append(status);
  return bar;
}

// ============================ Sensores de orientación (brújula / clinómetro) ============================
// Portado de catastro-remociones: webkitCompassHeading (norte real iOS), alpha (Android absoluto),
// media circular (correcta cerca de 0°/360°), dip por inclinación |beta|.
let orientPermOK=false;
async function ensureOrientPerm(){
  if(typeof DeviceOrientationEvent!=='undefined' && typeof DeviceOrientationEvent.requestPermission==='function'){
    if(orientPermOK)return true;
    try{const p=await DeviceOrientationEvent.requestPermission();if(p!=='granted')return false;orientPermOK=true;}catch{return false;}
  }
  return true;
}
function headingFromEvent(e){
  if(typeof e.webkitCompassHeading==='number')return e.webkitCompassHeading;   // iOS: norte magnético real
  if(e.alpha!=null)return (360-e.alpha)%360;                                     // Android orientación absoluta
  return null;
}
function circularMean(ds){if(!ds.length)return null;const r=ds.map(d=>d*Math.PI/180);
  const x=r.reduce((s,v)=>s+Math.cos(v),0)/r.length,y=r.reduce((s,v)=>s+Math.sin(v),0)/r.length;
  return (Math.round(Math.atan2(y,x)*180/Math.PI)+360)%360;}
function medirSensor(modo){ // modo: 'brujula'(azimut 0-360) | 'dip'(inclinación 0-90)
  return new Promise(async res=>{
    if(!(await ensureOrientPerm())){res(null);return;}
    const hs=[],bs=[];
    const evt = ('ondeviceorientationabsolute' in window) ? 'deviceorientationabsolute' : 'deviceorientation';
    const on=e=>{const h=headingFromEvent(e);if(h!=null)hs.push(h);if(e.beta!=null)bs.push(Math.abs(e.beta));
      if((modo==='brujula'?hs.length:bs.length)>=6){window.removeEventListener(evt,on);fin();}};
    const fin=()=>{window.removeEventListener(evt,on);
      if(modo==='brujula')res(hs.length?circularMean(hs):null);
      else res(bs.length?Math.min(90,Math.round(bs.reduce((s,b)=>s+b,0)/bs.length)):null);};
    window.addEventListener(evt,on);
    setTimeout(fin,2500);
  });
}
// qué sensor aplica a cada campo numérico
const RE_AZIMUT=/^(AZIMUT|RUMBO_CONTACTO|ORIENTACION_FOTO|ORIENTACION_MUESTRA)$/;
const RE_DIP=/(MANTEO_BUZAMIENTO|MANTEO_CONTACTO)$/;
function tipoSensor(n){ if(RE_AZIMUT.test(n))return 'brujula'; if(RE_DIP.test(n))return 'dip'; return null; }
// envuelve un input numérico con su botón de sensor
function sensorInput(inp,modo){
  const wrap=el('div',{class:'sensorwrap'});
  const btn=el('button',{type:'button',class:'btn '+(modo==='brujula'?'blue':'orange')+' mini',
    title: modo==='brujula'?'Medir azimut con la brújula del teléfono':'Medir inclinación (apoya el teléfono en el plano)'},
    modo==='brujula'?'🧭':'📐');
  btn.addEventListener('click',async()=>{
    const orig=btn.textContent;btn.textContent='⏳';btn.disabled=true;
    const v=await medirSensor(modo);
    btn.disabled=false;btn.textContent=orig;
    if(v==null){toast('Sin sensor de orientación; ingresa el valor manual');return;}
    inp.value=Math.round(v);inp.dispatchEvent(new Event('change',{bubbles:true}));
    toast((modo==='brujula'?'Azimut ':'Inclinación ')+Math.round(v)+'°');
  });
  wrap.append(inp,btn);
  return wrap;
}

// ============================ Estado / navegación ============================
let vista={n:'home'}; // {n:'home'} | {n:'proyecto',id} | {n:'punto',id}
function nav(v){vista=v;render();}
$('#btnBack').addEventListener('click',()=>{
  if(vista.n==='punto'){const p= curPunto&&curPunto._parent; nav({n:'proyecto',id:p});}
  else if(vista.n==='proyecto') nav({n:'home'});
});

let curProyecto=null, curPunto=null;

async function render(){
  dibujando=false; agregandoPunto=false;   // corta modos de dibujo/agregar al navegar
  const app=$('#app'); app.innerHTML=''; $('#fab').innerHTML=''; $('#fab').className='fab';
  if(vista.n==='home') return renderHome(app);
  if(vista.n==='proyecto') return renderProyecto(app);
  if(vista.n==='mapa') return renderMapa(app);
  if(vista.n==='punto') return renderPunto(app);
}

// -------- Home: proyectos --------
async function renderHome(app){
  $('#btnBack').style.display='none';
  $('#ttl').textContent='Proyectos'; $('#ctx').textContent='Captura de geología básica · '+APP_VER;
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

// -------- Convención de nombres (autonumeración estilo StraboSpot) --------
function namingCfg(pr){
  const d={pc:{on:false,prefix:'PC-',pad:3,next:1}, smp:{on:false,prefix:'M-',pad:3,next:1}};
  const n=(pr&&pr._naming)||{};
  return {pc:Object.assign({},d.pc,n.pc), smp:Object.assign({},d.smp,n.smp)};
}
function fmtName(c){return c.prefix+String(c.next).padStart(c.pad||0,'0');}

function editorNaming(pr){
  const app=$('#app');app.innerHTML='';$('#fab').innerHTML='';$('#btnBack').style.display='';
  $('#ttl').textContent='Convención de nombres';$('#ctx').textContent=pr.NOMBRE_PROYECTO||'';
  const cfg=namingCfg(pr);
  const fld=(lab,inp)=>el('div',{class:'fld'},el('label',{},lab),inp);
  const seccion=(titulo,c,ayuda)=>{
    const card=el('div',{class:'card'});card.append(el('h2',{},titulo));
    const on=el('input',{type:'checkbox'});on.checked=c.on;
    const pre=el('input',{type:'text',value:c.prefix});
    const pad=el('input',{type:'number',min:'0',max:'6',value:c.pad,inputmode:'numeric'});
    const nxt=el('input',{type:'number',min:'1',value:c.next,inputmode:'numeric'});
    const prev=el('div',{class:'muted',style:'margin-top:4px'});
    const upd=()=>{prev.textContent='Ejemplo: '+pre.value+String(nxt.value||1).padStart(+pad.value||0,'0');};
    [pre,pad,nxt].forEach(i=>i.addEventListener('input',upd));upd();
    const lblOn=el('label',{class:'btnbar',style:'cursor:pointer'},on,el('span',{style:'font-weight:600'},'Activar autonumeración'));
    card.append(lblOn,el('div',{class:'row'},fld('Prefijo',pre),fld('Dígitos (ceros)',pad),fld('Próximo número',nxt)),
      el('div',{class:'nota'},ayuda),prev);
    card._get=()=>({on:on.checked,prefix:pre.value,pad:+pad.value||0,next:Math.max(1,+nxt.value||1)});
    app.append(card);return card;
  };
  const cPc=seccion('📍 Puntos de control (ID_PUNTO_CONTROL)',cfg.pc,
    'Cada punto nuevo toma el número siguiente automáticamente al guardar. Puedes editarlo a mano en el punto.');
  const cSm=seccion('🧪 Muestras (ID_MUESTRA)',cfg.smp,
    'Cada muestra nueva toma el número siguiente al agregarla.');
  $('#fab').append(
    el('button',{class:'btn',onclick:async()=>{pr._naming={pc:cPc._get(),smp:cSm._get()};await put('proyecto',pr);toast('Convención guardada');nav({n:'proyecto',id:pr.id});}},'Guardar'),
    el('button',{class:'btn sec',onclick:()=>nav({n:'proyecto',id:pr.id})},'Cancelar'));
}

// -------- Proyecto: puntos de control --------
async function renderProyecto(app){
  curProyecto=await get('proyecto',vista.id);
  if(!curProyecto)return nav({n:'home'});
  $('#btnBack').style.display='';
  $('#ttl').textContent=curProyecto.NOMBRE_PROYECTO||'Proyecto';
  $('#ctx').textContent='ID '+(curProyecto.ID_PROYECTO||'—');
  app.append(toggleModo('puntos'));
  const puntos=(await childrenOf('punto',curProyecto.id));
  curProyecto._npuntos=puntos.length;put('proyecto',curProyecto);
  const head=el('div',{class:'card'});
  head.append(el('h2',{},'Proyecto'),
    el('div',{class:'btnbar'},
      el('button',{class:'btn sec mini',onclick:()=>editorProyecto(curProyecto)},'✎ Editar proyecto'),
      el('button',{class:'btn sec mini',onclick:()=>editorNaming(curProyecto)},'🔤 Convención de nombres')));
  app.append(head);
  const card=el('div',{class:'card'});
  card.append(el('h2',{},'Puntos de control ('+puntos.length+')'));
  if(!puntos.length)card.append(el('div',{class:'empty'},'Sin puntos. Agrega el primero con el botón +.'));
  puntos.forEach((pt,i)=>{
    card.append(el('div',{class:'list-item',onclick:()=>nav({n:'punto',id:pt.id})},
      el('div',{class:'t'},el('b',{},pt.ID_PUNTO_CONTROL||('Punto '+(i+1))),
        el('small',{},(pt['Coordenadas Geográficas Decimales_Lat']||pt.LAT||'—')+', '+(pt['Coordenadas Geográficas Decimales_Long']||pt.LONG||'—')+' · '+(pt.FECHA||'')) ),
      el('span',{class:'pill'},(pt._nlito||0)+' lito'),
      el('button',{class:'btn sec mini',title:'Duplicar (sin coordenadas)',onclick:async(e)=>{e.stopPropagation();const np=await duplicarPunto(pt.id);toast('Duplicado — asigna coordenadas e ID');nav({n:'punto',id:np.id});}},'⧉')));
  });
  app.append(card);
  $('#fab').append(el('button',{class:'btn',onclick:()=>nav0Punto()},'+ Nuevo punto'),
    el('button',{class:'btn sec',onclick:()=>nav({n:'home'})},'⌂ Proyectos'));
}
function nav0Punto(){curPunto=null;nav({n:'punto',id:'__new__'});}

// ---- Tarjetas colapsables (acordeón) del editor de punto ----
let secAbiertas=new Set(['punto']); let ultimoPuntoRender=null;
function tarjetaColapsable(titulo, opts){
  opts=opts||{};
  const abierto = opts.clave ? secAbiertas.has(opts.clave) : !!opts.abierto;
  const card=el('div',{class:'card collap'+(opts.lleno?' lleno':'')});
  const chev=el('span',{class:'chev'},'▸');
  const head=el('div',{class:'collap-head'}, chev, el('span',{class:'ctitle'},titulo), opts.badge!=null?el('span',{class:'pill'},opts.badge):'');
  const body=el('div',{class:'collap-body'});
  const setOpen=(o)=>{card.classList.toggle('open',o);chev.textContent=o?'▾':'▸';
    if(opts.clave){if(o)secAbiertas.add(opts.clave);else secAbiertas.delete(opts.clave);}
    if(o&&opts.onOpen)opts.onOpen();};
  head.addEventListener('click',()=>setOpen(!card.classList.contains('open')));
  // botón contraer al pie de la sección
  body.append(el('div',{class:'collap-fin'},el('button',{onclick:()=>{setOpen(false);card.scrollIntoView({behavior:'smooth',block:'nearest'});}},'▲ Contraer')));
  card.append(head,body);
  if(abierto)setOpen(true);
  return {card,body};
}

// -------- Punto de control + hijas --------
async function renderPunto(app){
  app.innerHTML=''; $('#fab').innerHTML=''; $('#fab').className='fab';   // evita duplicar al re-render directo (agregar/eliminar hijo)
  const nuevo = vista.id==='__new__';
  // punto nuevo: precarga colector y campos constantes recordados + fecha/hora automáticas
  curPunto = nuevo ? Object.assign({id:uid(),_parent:curProyecto.id}, stickyGet(), ahora())
                   : await get('punto',vista.id);
  if(nuevo){const c=namingCfg(curProyecto).pc; if(c.on){curPunto.ID_PUNTO_CONTROL=fmtName(c);curPunto._idPreview=curPunto.ID_PUNTO_CONTROL;}}
  if(nuevo&&coordsPendientes){curPunto[inLat]=coordsPendientes[0].toFixed(6);curPunto[inLon]=coordsPendientes[1].toFixed(6);coordsPendientes=null;}
  if(!curPunto)return nav({n:'proyecto',id:curProyecto.id});
  $('#btnBack').style.display='';
  $('#ttl').textContent = curPunto.ID_PUNTO_CONTROL || (nuevo?'Nuevo punto':'Punto');
  $('#ctx').textContent = curProyecto.NOMBRE_PROYECTO||'';
  if(ultimoPuntoRender!==curPunto.id){secAbiertas=new Set(['punto']);ultimoPuntoRender=curPunto.id;}  // reset acordeón al cambiar de punto

  // --- formulario del punto (colapsable, abierto por defecto) ---
  const puntoLleno=!!(curPunto['Coordenadas Geográficas Decimales_Lat']||curPunto.GEOLOGO);
  const cp=tarjetaColapsable('📍 Punto de control (estación y ubicación)',{clave:'punto',lleno:puntoLleno});
  cp.body.append(el('div',{class:'btnbar'},el('button',{class:'btn blue mini',onclick:()=>tomarGPS(f)},'📡 Tomar GPS')));
  const f=formulario('punto',curPunto);cp.body.append(f.node);
  app.append(cp.card);

  // --- mapa satelital (colapsable; el mapa se inicia al abrir la sección) ---
  let mapIniciado=false;
  const cm=tarjetaColapsable('🛰️ Ubicación satelital',{clave:'map',lleno:!!curPunto._satelital,badge:curPunto._satelital?'📸':null,
    onOpen:()=>{ if(!mapIniciado){mapIniciado=true;setTimeout(()=>initMapPunto(curPunto,f),80);} else if(mapa){setTimeout(()=>mapa.invalidateSize(),80);} }});
  cm.body.append(el('div',{id:'map',class:'mapbox'}));
  cm.body.append(el('div',{class:'btnbar'},
    el('button',{class:'btn blue mini',onclick:ubicarGPSmapa},'📡 GPS'),
    el('button',{class:'btn sec mini',onclick:descargarTiles},'⬇️ Tiles offline'),
    el('button',{class:'btn sec mini',onclick:cargarGeoTIFF},'🗺️ GeoTIFF'),
    el('button',{class:'btn orange mini',onclick:capturarSatelital},'📸 Capturar satelital')));
  cm.body.append(el('div',{class:'muted',id:'coordlbl'},''));
  const satThumb=el('div',{class:'thumbs',id:'satthumb'});
  if(curPunto._satelital)satThumb.append(el('img',{src:'data:image/jpeg;base64,'+curPunto._satelital}));
  cm.body.append(satThumb);
  app.append(cm.card);

  const guardarPunto=async()=>{
    const d=f.getData();Object.assign(curPunto,d);curPunto._parent=curProyecto.id;
    curPunto.ID_PROYECTO=curProyecto.ID_PROYECTO||curProyecto.id;
    // autonumeración del ID de punto: al primer guardado, si el usuario no lo cambió, asigna y avanza el correlativo
    const nc=namingCfg(curProyecto).pc;
    if(nc.on && !curPunto._idDone && (!curPunto.ID_PUNTO_CONTROL || curPunto.ID_PUNTO_CONTROL===curPunto._idPreview)){
      curPunto.ID_PUNTO_CONTROL=fmtName(nc);
      const full=namingCfg(curProyecto);full.pc.next=nc.next+1;curProyecto._naming=full;await put('proyecto',curProyecto);
    }
    curPunto._idDone=true;
    await put('punto',curPunto);
    stickySet(curPunto);  // recuerda colector/proyección/etc. para el próximo punto
    if(vista.id==='__new__')vista={n:'punto',id:curPunto.id};  // fija id real: evita re-crear punto vacío al re-render
    return curPunto;
  };

  // --- secciones hijas (colapsables) ---
  const litos=await childrenOf('litologia',curPunto.id);
  for(const h of HIJAS){
    const items=await childrenOf(h.store,curPunto.id);
    if(h.store==='litologia')curPunto._nlito=items.length;
    const hc=tarjetaColapsable(h.titulo+(h.oblig?' *':''),{clave:h.store,lleno:items.length>0,badge:items.length});
    const box=el('div');hc.body.append(box);
    items.forEach((it,i)=>box.append(bloqueHijo(h,it,i,litos)));
    hc.body.append(el('div',{class:'btnbar'},
      el('button',{class:'btn '+(h.clase==='lito'?'':'orange')+' mini',onclick:async()=>{
        await guardarPunto();
        const reg={id:uid(),_parent:curPunto.id};
        if(h.store==='muestreo'){const sc=namingCfg(curProyecto).smp;
          if(sc.on){reg.ID_MUESTRA=fmtName(sc);const full=namingCfg(curProyecto);full.smp.next=sc.next+1;curProyecto._naming=full;await put('proyecto',curProyecto);}}
        await put(h.store,reg);
        secAbiertas.add(h.store);   // mantener esta sección abierta tras re-render
        await renderPunto(app);
        requestAnimationFrame(()=>{const bs=document.querySelectorAll('.child-block[data-store="'+h.store+'"]');
          const last=bs[bs.length-1];if(last){last.scrollIntoView({behavior:'smooth',block:'center'});
          const inp=last.querySelector('input,select,textarea');if(inp)inp.focus({preventScroll:true});}});
        toast(h.titulo+' agregada — completa los campos');
      }},'+ Agregar '+h.titulo.toLowerCase())));
    app.append(hc.card);
  }

  // --- Foto-mapa (colapsable) ---
  {
    const raices=await fotomapasRaiz(curPunto.id);
    const fmc=tarjetaColapsable('🖼️ Foto-mapa — cambio de escala',{clave:'fotomapa',lleno:raices.length>0,badge:raices.length});
    fmc.body.append(el('div',{class:'muted',html:'Foto como lienzo con fotos de detalle; cada detalle es a su vez otro lienzo (multiescala).'}));
    const box=el('div',{style:'margin-top:8px'});
    for(const fm of raices){
      const nh=(await fotomapaHijos(fm.id)).length;
      box.append(el('div',{class:'list-item',onclick:()=>editorFotomapa(fm)},
        fm._base?el('img',{src:fm._base,style:'width:54px;height:40px;object-fit:cover;border-radius:6px'}):el('span',{class:'pill'},'sin foto'),
        el('div',{class:'t'},el('b',{},fm.TITULO||'Foto-mapa'),el('small',{},nh+' detalles')),
        el('button',{class:'btn del mini',onclick:async(e)=>{e.stopPropagation();if(confirm('¿Eliminar este foto-mapa y sus detalles?')){await borrarFotomapaArbol(fm.id);renderPunto(app);}}},'🗑')));
    }
    fmc.body.append(box);
    fmc.body.append(el('div',{class:'btnbar'},
      el('button',{class:'btn mini',onclick:async()=>{await guardarPunto();const reg={id:uid(),_parent:null,_punto:curPunto.id,_pins:null};await put('fotomapa',reg);secAbiertas.add('fotomapa');editorFotomapa(reg);}},'+ Nuevo foto-mapa')));
    app.append(fmc.card);
  }

  $('#fab').append(
    el('button',{class:'btn',onclick:async()=>{await guardarPunto();toast('Punto guardado');nav({n:'proyecto',id:curProyecto.id});}},'✓ Guardar punto'),
    el('button',{class:'btn sec',onclick:async()=>{await guardarPunto();const np=await duplicarPunto(curPunto.id);toast('Duplicado — asigna coordenadas e ID');nav({n:'punto',id:np.id});}},'⧉ Duplicar'),
    el('button',{class:'btn sec',onclick:()=>guardarPunto().then(()=>nav({n:'proyecto',id:curProyecto.id}))},'Volver'),
    nuevo?null:el('button',{class:'btn del',onclick:async()=>{if(confirm('¿Eliminar este punto y sus datos asociados?')){await borrarPunto(curPunto.id);nav({n:'proyecto',id:curProyecto.id});}}},'🗑'));
}

function bloqueHijo(h,reg,i,litos){
  const b=el('div',{class:'child-block'+(h.clase==='lito'?' lito':''),'data-store':h.store});
  const hd=el('div',{class:'hd'});
  hd.append(el('span',{class:'n'},h.titulo+' '+(i+1)));
  hd.append(el('button',{class:'btn del mini',onclick:async()=>{await del(h.store,reg.id);renderPunto($('#app'));}},'Eliminar'));
  b.append(hd);
  if(h.store==='foto'){ b.append(bloqueFoto(reg,litos)); }
  else if(h.store==='esquema'){ b.append(bloqueEsquema(reg)); }
  else {
    const f=formulario(h.store,reg,{litologias:litos});
    b.append(f.node);
    const barra=barraMedicion(h.store,f);
    if(barra){
      const map=PLANO_CAMPOS[h.store];
      const anchor=f.node.querySelector('[name="'+map.rumbo+'"]');
      const fld=anchor&&anchor.closest('.fld');
      if(fld) fld.parentNode.insertBefore(barra, fld);   // justo antes de los números (rumbo/manteo/…)
      else b.append(barra);
    }
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
const comprimir=(file,max,q)=>cargarImagen(file,max,q).then(r=>r.dataUrl);   // alias de cargarImagen (sin duplicar lógica canvas)

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
  for(const fm of await fotomapasRaiz(id)) await borrarFotomapaArbol(fm.id);
  await del('punto',id);
}

// ============================ Foto-mapa (image basemap anidado, estilo StraboSpot) ============================
let fmap=null, curFM=null;
async function fotomapasRaiz(puntoId){return (await all('fotomapa')).filter(f=>f._punto===puntoId && !f._parent);}
async function fotomapaHijos(nodeId){return (await all('fotomapa')).filter(f=>f._parent===nodeId);}
async function borrarFotomapaArbol(nodeId){for(const h of await fotomapaHijos(nodeId))await borrarFotomapaArbol(h.id);await del('fotomapa',nodeId);}
async function rutaFotomapa(node){const p=[];let n=node;while(n){p.unshift(n);n=n._parent?await get('fotomapa',n._parent):null;}return p;}

async function editorFotomapa(node){
  curFM=node;
  const app=$('#app');app.innerHTML='';$('#fab').innerHTML='';$('#btnBack').style.display='';
  $('#ttl').textContent='Foto-mapa'; $('#ctx').textContent=curProyecto.NOMBRE_PROYECTO||'';
  const card=el('div',{class:'card'});
  // migas de pan (jerarquía de escala)
  const ruta=await rutaFotomapa(node);
  const bread=el('div',{class:'fmbread'});
  ruta.forEach((n,i)=>{ bread.append(i? el('span',{},' › ') : '');
    if(n.id===node.id) bread.append(el('b',{},n.TITULO||('Nivel '+(i+1))));
    else bread.append(el('a',{onclick:()=>editorFotomapa(n)}, n.TITULO||('Nivel '+(i+1)))); });
  card.append(bread);
  // título
  const t=el('input',{type:'text',placeholder:'Título de este nivel',value:node.TITULO||''});
  t.addEventListener('change',async()=>{node.TITULO=t.value;await put('fotomapa',node);});
  card.append(el('div',{class:'fld'},el('label',{},'Título'),t));

  if(!node._base){
    const inp=el('input',{type:'file',accept:'image/*',capture:'environment',style:'display:none'});
    inp.addEventListener('change',async e=>{const f=e.target.files[0];if(!f)return;
      const im=await cargarImagen(f,1600,.82);node._base=im.dataUrl;node._w=im.w;node._h=im.h;await put('fotomapa',node);editorFotomapa(node);});
    card.append(el('div',{class:'btnbar'},el('button',{class:'btn blue',onclick:()=>inp.click()},'📷 Cargar foto de este nivel'),inp));
    card.append(el('div',{class:'muted'},'Foto amplia para el 1er nivel (afloramiento). Luego tocas sobre ella para agregar detalles.'));
  } else {
    card.append(el('div',{class:'muted'},'Toca la foto para colocar un detalle · toca un pin para entrar (más escala).'));
    card.append(el('div',{id:'fmap',class:'mapbox'}));
    card.append(el('div',{class:'btnbar'},
      el('button',{class:'btn sec mini',onclick:()=>verFotoCompleta(node._base)},'🔍 Ver foto completa'),
      el('button',{class:'btn sec mini',onclick:()=>editorFotomapa(node)},'↻ Recentrar')));
    setTimeout(()=>initFotomapaMap(node),60);
  }
  app.append(card);
  const volver=()=> node._parent ? get('fotomapa',node._parent).then(p=>editorFotomapa(p)) : nav({n:'punto',id:curPunto.id});
  $('#fab').append(el('button',{class:'btn',onclick:()=>nav({n:'punto',id:curPunto.id})},'✓ Listo'),
    el('button',{class:'btn sec',onclick:volver},'‹ Volver'));
}

async function initFotomapaMap(node){
  if(fmap){try{fmap.remove();}catch(e){}fmap=null;}
  const w=node._w||1000, h=node._h||750, bounds=[[0,0],[h,w]];
  fmap=L.map('fmap',{crs:L.CRS.Simple,minZoom:-5,maxZoom:5,zoomControl:true,attributionControl:false});
  L.imageOverlay(node._base,bounds).addTo(fmap);
  fmap.fitBounds(bounds);
  for(const hijo of await fotomapaHijos(node.id)) addFotoPin(node,hijo);
  fmap.on('click',async e=>{
    const x=e.latlng.lng, y=e.latlng.lat; if(x<0||y<0||x>w||y>h)return;
    const inp=el('input',{type:'file',accept:'image/*',capture:'environment'});
    inp.onchange=async ev=>{const f=ev.target.files[0];if(!f)return;
      const im=await cargarImagen(f,1500,.82), th=await cargarImagen(f,110,.7);
      const hijo={id:uid(),_parent:node.id,_punto:node._punto,_base:im.dataUrl,_w:im.w,_h:im.h,_thumb:th.dataUrl,x,y,TITULO:''};
      await put('fotomapa',hijo); addFotoPin(node,hijo); toast('Detalle agregado');
    };
    inp.click();
  });
  setTimeout(()=>fmap.invalidateSize(),140);
}
function addFotoPin(node,hijo){
  const icon=L.divIcon({className:'fpin',html:'<img src="'+(hijo._thumb||hijo._base)+'">',iconSize:[44,44],iconAnchor:[22,22]});
  const m=L.marker([hijo.y,hijo.x],{icon,draggable:true}).addTo(fmap);
  m.on('dragend',async()=>{const ll=m.getLatLng();hijo.x=ll.lng;hijo.y=ll.lat;await put('fotomapa',hijo);});
  m.on('click',()=>editorFotomapa(hijo));   // entrar al detalle (cambio de escala)
}
function verFotoCompleta(src){const ov=el('div',{class:'fmov',onclick:()=>ov.remove()});ov.append(el('img',{src}));document.body.append(ov);}

// ============================ Modo Mapa + simbología estructural ============================
function toggleModo(activo){
  const bar=el('div',{class:'modtoggle'});
  const mk=(n,txt,dest)=>el('button',{class:'btn '+(activo===n?'':'sec'),onclick:()=>{if(activo!==n)dest();}},txt);
  bar.append(mk('mapa','🗺️ Mapa',()=>nav({n:'mapa',id:curProyecto.id})),
             mk('puntos','📋 Puntos de control',()=>nav({n:'proyecto',id:curProyecto.id})));
  return bar;
}
let mapaVista=null;
async function renderMapa(app){
  curProyecto=await get('proyecto',vista.id); if(!curProyecto)return nav({n:'home'});
  $('#btnBack').style.display='';
  $('#ttl').textContent=curProyecto.NOMBRE_PROYECTO||'Mapa'; $('#ctx').textContent='Mapa del proyecto';
  app.append(toggleModo('mapa'));
  const card=el('div',{class:'card mapcard'});
  card.append(el('div',{id:'projmap',class:'mapbig'}));
  app.append(card);
  const puntos=await childrenOf('punto',curProyecto.id);
  const conC=puntos.filter(p=>!isNaN(parseFloat(p['Coordenadas Geográficas Decimales_Lat']))&&!isNaN(parseFloat(p['Coordenadas Geográficas Decimales_Long'])));
  $('#fab').className='fab compact';
  $('#fab').append(
    el('button',{class:'btn mini',onclick:iniciarAgregarPunto},'📍+ Punto'),
    el('button',{class:'btn blue mini',onclick:iniciarDibujoLinea},'✏️ Línea'),
    el('button',{class:'btn sec mini',onclick:legendaSimbologia},'ⓘ'),
    el('span',{class:'muted',style:'flex:1;align-self:center;font-size:11px'},conC.length+'/'+puntos.length+' pts'),
    el('button',{class:'btn sec mini',onclick:descargarTilesConZoom},'⬇️ Tiles'),
    el('button',{class:'btn sec mini',onclick:()=>nav({n:'home'})},'⌂'));
  setTimeout(()=>initMapaVista(conC),80);
}
function legendaSimbologia(){
  const ov=el('div',{class:'fmov',onclick:e=>{if(e.target===ov)ov.remove();}});
  const box=el('div',{class:'card',style:'max-width:420px'});
  box.append(el('h2',{},'Simbología'));
  box.append(el('div',{class:'muted',html:
    '<b>●</b> estación (punto de control) · con su ID<br>'
   +'<b>—⊢ 30</b> rumbo/manteo de un <b>plano</b> (tick al lado del manteo, valor en grados)<br>'
   +'<b>→ 40</b> <b>lineación</b> (flecha = trend, valor = plunge)<br>'
   +'plano + flecha en rojo = <b>falla</b> con estría<br>'
   +'<b>▲</b> azul = punto con <b>muestras</b> (número)<br><br>Toca un punto para abrir su ficha.'}));
  box.append(el('div',{class:'btnbar'},el('button',{class:'btn',onclick:()=>ov.remove()},'Cerrar')));
  ov.append(box);document.body.append(ov);
}
async function initMapaVista(puntos){
  if(mapaVista){try{mapaVista.remove();}catch(e){}mapaVista=null;}
  mapaVista=L.map('projmap',{zoomControl:true});
  savetiles=capaSatelital(mapaVista);
  const pts=[];
  for(const p of puntos){
    const lat=parseFloat(p['Coordenadas Geográficas Decimales_Lat']), lon=parseFloat(p['Coordenadas Geográficas Decimales_Long']);
    if(isNaN(lat)||isNaN(lon))continue;
    const estr=await childrenOf('estructural',p.id), mus=await childrenOf('muestreo',p.id);
    const m=L.marker([lat,lon],{icon:iconoPunto(estr,mus)}).addTo(mapaVista);
    if(p.ID_PUNTO_CONTROL)m.bindTooltip(p.ID_PUNTO_CONTROL,{permanent:true,direction:'bottom',offset:[0,18],className:'ptlabel'});
    m.on('click',()=>{curPunto=null;vista={n:'punto',id:p.id};render();});
    pts.push([lat,lon]);
  }
  // --- líneas geológicas (contactos/fallas) del proyecto ---
  const lineas=await childrenOf('linea',curProyecto.id);
  for(const L2 of lineas){
    if(!L2.geom||L2.geom.length<2)continue;
    const pl=L.polyline(L2.geom, estiloLinea(L2)).addTo(mapaVista);
    pl.on('click',ev=>{ if(dibujando)return; L.DomEvent.stop(ev);
      formLinea(L2, async()=>{await put('linea',L2);initMapaVista(_puntosMapa);},
                    async()=>{await del('linea',L2.id);initMapaVista(_puntosMapa);}); });
  }
  _puntosMapa=puntos;
  // click en el mapa: si está el modo dibujo activo, agrega vértice
  mapaVista.on('click',ev=>{
    if(agregandoPunto){ agregandoPunto=false;
      const b=document.getElementById('drawbanner'); if(b)b.remove();
      mapaVista.getContainer().style.cursor='';
      coordsPendientes=[ev.latlng.lat, ev.latlng.lng];
      curPunto=null; vista={n:'punto',id:'__new__'}; render();
      return; }
    if(!dibujando)return;
    _verts.push([ev.latlng.lat,ev.latlng.lng]);
    if(_tmpLine)_tmpLine.setLatLngs(_verts); else _tmpLine=L.polyline(_verts,{color:'#12a4ff',weight:3,dashArray:'5,5'}).addTo(mapaVista);
    _tmpMk.push(L.circleMarker(ev.latlng,{radius:4,color:'#12a4ff',fillColor:'#12a4ff',fillOpacity:1,weight:1}).addTo(mapaVista));
    bannerDibujo(); });
  if(pts.length)mapaVista.fitBounds(pts,{padding:[46,46],maxZoom:17}); else mapaVista.setView([-33.45,-70.65],5);
  setTimeout(()=>mapaVista.invalidateSize(),160);
}
// ---- iconos / simbología (SVG orientada por azimut; norte = arriba) ----
const _rad=d=>d*Math.PI/180;
function _uv(az){const a=_rad(az);return [Math.sin(a),-Math.cos(a)];}   // [este(x), norte(-y)] en coords de pantalla
function _hl(x1,y1,x2,y2,col){col=col||'#141414';
  return '<line x1="'+x1.toFixed(1)+'" y1="'+y1.toFixed(1)+'" x2="'+x2.toFixed(1)+'" y2="'+y2.toFixed(1)+'" stroke="#fff" stroke-width="3.4" stroke-linecap="round"/>'
       + '<line x1="'+x1.toFixed(1)+'" y1="'+y1.toFixed(1)+'" x2="'+x2.toFixed(1)+'" y2="'+y2.toFixed(1)+'" stroke="'+col+'" stroke-width="1.6" stroke-linecap="round"/>';}
function _ht(x,y,txt,col){col=col||'#141414';
  return '<text x="'+x.toFixed(1)+'" y="'+y.toFixed(1)+'" font-size="9.5" font-weight="700" text-anchor="middle" dominant-baseline="central" stroke="#fff" stroke-width="3" paint-order="stroke" fill="'+col+'">'+txt+'</text>';}
function simboloPlano(cx,cy,az,dip,col){
  const [sx,sy]=_uv(az),[dx,dy]=_uv(az+90);const Ls=15,Lt=8;
  let s=_hl(cx-sx*Ls,cy-sy*Ls,cx+sx*Ls,cy+sy*Ls,col);   // línea de rumbo
  s+=_hl(cx,cy,cx+dx*Lt,cy+dy*Lt,col);                    // tick de manteo (a la derecha del rumbo, RHR)
  if(!isNaN(dip))s+=_ht(cx+dx*(Lt+8),cy+dy*(Lt+8),Math.round(dip),col);
  return s;
}
function simboloLinea(cx,cy,tr,pl,col){col=col||'#1a5fb4';
  const [tx,ty]=_uv(tr);const La=15;const px=cx+tx*La,py=cy+ty*La;
  let s=_hl(cx,cy,px,py,col);
  const a1=_uv(tr+180+24),a2=_uv(tr+180-24),hl=6;         // punta de flecha
  s+=_hl(px,py,px+a1[0]*hl,py+a1[1]*hl,col);
  s+=_hl(px,py,px+a2[0]*hl,py+a2[1]*hl,col);
  if(!isNaN(pl))s+=_ht(px+tx*8,py+ty*8,Math.round(pl),col);
  return s;
}
function svgEstructura(e,cx,cy){
  const az=parseFloat(e.AZIMUT),dip=parseFloat(e.MANTEO_BUZAMIENTO),tr=parseFloat(e.TREND),pl=parseFloat(e.PLUNGE);
  const hasPlano=!isNaN(az)&&!isNaN(dip),hasLinea=!isNaN(tr)&&!isNaN(pl);
  const esFalla=(e.TIPO_ESTRUCTURA==='Estructura falla');
  const lineaPura=hasPlano&&!hasLinea&&/lineaci|eje|estr[íi]a|paleocorriente/i.test(e.TIPO_MEDIDA_ESTRUCTURAL||'');
  let s='';
  if(hasPlano&&!lineaPura)s+=simboloPlano(cx,cy,az,dip,esFalla?'#b02a1a':'#141414');
  if(hasLinea)s+=simboloLinea(cx,cy,tr,pl,esFalla?'#b02a1a':'#1a5fb4');
  if(lineaPura)s+=simboloLinea(cx,cy,az,dip,'#1a5fb4');
  return s;
}
// ---- Líneas de control dibujadas sobre el satelital ----
// El color va por CLASE_LINEA (no por cada tipo/subtipo, para no mantener una paleta de
// 100+ entradas); el punteado sigue yendo por certeza, igual que antes.
// Siempre 6 dígitos hex: toKmlColor() del export KMZ trocea de a 2 y con #abc produce basura.
const LINEA_CLASE_COLOR={'Contacto':'#1a1a1a','Estructura tectónica':'#c0392b','Cuerpo tabular':'#8e44ad','Geomorfología':'#16739e','Otro':'#666666'};
const LINEA_DASH={'Observado':null,'Inferido':'10,7','Cubierto':'2,7'};
function estiloLinea(l){return {color:LINEA_CLASE_COLOR[l.CLASE_LINEA]||'#666666', weight:3.5, opacity:.95, dashArray:LINEA_DASH[l.CERTEZA_LINEA]||null};}
let dibujando=false,_verts=[],_tmpLine=null,_tmpMk=[],_puntosMapa=[];
let agregandoPunto=false, coordsPendientes=null;
function limpiarTemp(){ if(mapaVista){ if(_tmpLine)mapaVista.removeLayer(_tmpLine); _tmpMk.forEach(m=>mapaVista.removeLayer(m)); } _tmpLine=null;_tmpMk=[];_verts=[]; }
function bannerDibujo(){
  const cont=document.querySelector('.mapcard'); if(!cont)return;
  let b=document.getElementById('drawbanner'); if(b)b.remove();
  b=el('div',{id:'drawbanner',class:'drawbanner'},
    el('span',{},'✏️ Toca el mapa para trazar ('+_verts.length+' vértices)'),
    el('button',{class:'btn mini',onclick:terminarDibujo},'✓ Terminar'),
    el('button',{class:'btn sec mini',onclick:e=>{const v=_verts;if(v.length){v.pop();if(_tmpMk.length){mapaVista.removeLayer(_tmpMk.pop());}if(_tmpLine)_tmpLine.setLatLngs(v);}bannerDibujo();}},'↶'),
    el('button',{class:'btn del mini',onclick:cancelarDibujo},'✕'));
  cont.append(b);
}
function iniciarAgregarPunto(){
  if(!mapaVista)return; cancelarDibujo(); agregandoPunto=true;
  mapaVista.getContainer().style.cursor='crosshair';
  const cont=document.querySelector('.mapcard'); if(cont){
    let b=document.getElementById('drawbanner'); if(b)b.remove();
    b=el('div',{id:'drawbanner',class:'drawbanner'},
      el('span',{},'📍 Toca el mapa donde va el nuevo punto de control'),
      el('button',{class:'btn del mini',onclick:()=>{agregandoPunto=false;b.remove();mapaVista.getContainer().style.cursor='';}},'✕'));
    cont.append(b); }
  toast('Toca el mapa para ubicar el punto');
}
function iniciarDibujoLinea(){ if(!mapaVista)return; dibujando=true; limpiarTemp(); mapaVista.getContainer().style.cursor='crosshair'; bannerDibujo(); toast('Modo dibujo: toca el mapa'); }
function cancelarDibujo(){ dibujando=false; limpiarTemp(); const b=document.getElementById('drawbanner');if(b)b.remove(); if(mapaVista)mapaVista.getContainer().style.cursor=''; }
function terminarDibujo(){
  if(_verts.length<2){toast('Traza al menos 2 puntos');return;}
  const l={id:uid(),_parent:curProyecto.id,geom:_verts.slice(),CLASE_LINEA:'Contacto',CERTEZA_LINEA:'Observado',NOTA:''};
  const b=document.getElementById('drawbanner');if(b)b.remove();
  dibujando=false; limpiarTemp(); if(mapaVista)mapaVista.getContainer().style.cursor='';
  formLinea(l, async()=>{await put('linea',l);initMapaVista(_puntosMapa);toast('Línea guardada');}, null);
}
function formLinea(linea,onSave,onDelete){
  const ov=el('div',{class:'fmov',onclick:e=>{if(e.target===ov)ov.remove();}});
  const box=el('div',{class:'card',style:'max-width:440px;width:92vw'});
  box.append(el('h2',{},'✏️ Línea de control'));
  const f=formulario('linea', linea, {puntos:_puntosMapa});
  box.append(f.node);
  box.append(el('div',{class:'muted',style:'font-size:11px'},(linea.geom||[]).length+' vértices'));
  const bar=el('div',{class:'btnbar'});
  bar.append(el('button',{class:'btn',onclick:()=>{Object.assign(linea,f.getData());ov.remove();onSave();}},'Guardar'));
  if(onDelete)bar.append(el('button',{class:'btn del',onclick:()=>{if(confirm('¿Eliminar esta línea?')){ov.remove();onDelete();}}},'Eliminar'));
  bar.append(el('button',{class:'btn sec',onclick:()=>ov.remove()},'Cancelar'));
  box.append(bar);ov.append(box);document.body.append(ov);
}

function iconoPunto(estr,mus){
  const cx=30,cy=30;let inner='';
  (estr||[]).forEach(e=>inner+=svgEstructura(e,cx,cy));       // símbolos estructurales orientados
  inner+='<circle cx="30" cy="30" r="4.2" fill="#c0392b" stroke="#fff" stroke-width="1.6"/>';   // estación
  if(mus&&mus.length)inner+='<g transform="translate(45,15)"><polygon points="0,-6 6,5 -6,5" fill="#2166a8" stroke="#fff" stroke-width="1.2"/><text x="0" y="2.5" font-size="7" fill="#fff" text-anchor="middle" font-weight="bold">'+mus.length+'</text></g>';
  const svg='<svg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">'+inner+'</svg>';
  return L.divIcon({className:'estsym',html:svg,iconSize:[60,60],iconAnchor:[30,30]});
}
// compone la foto base con pines numerados (para la libreta PDF)
function compositaFotomapa(node){return new Promise(async res=>{
  const hijos=await fotomapaHijos(node.id);
  const img=new Image();
  img.onload=()=>{const cv=el('canvas');cv.width=img.width;cv.height=img.height;const c=cv.getContext('2d');
    c.drawImage(img,0,0);const rad=Math.max(13,img.width*0.018);
    hijos.forEach((h,i)=>{const x=h.x, y=img.height-h.y;   // CRS.Simple: y invertido respecto al canvas
      c.beginPath();c.arc(x,y,rad,0,7);c.fillStyle='rgba(230,80,40,.9)';c.fill();c.lineWidth=2;c.strokeStyle='#fff';c.stroke();
      c.fillStyle='#fff';c.font='bold '+Math.round(rad*1.3)+'px sans-serif';c.textAlign='center';c.textBaseline='middle';c.fillText(String(i+1),x,y);});
    res(cv.toDataURL('image/jpeg',.85));};
  img.onerror=()=>res(node._base); img.src=node._base;});}

// Duplica un punto con sus datos DESCRIPTIVOS (litología, estructurales, contactos, muestreo),
// pero deja en blanco las coordenadas y NO copia fotos/esquemas/imagen satelital (son propios del sitio).
async function duplicarPunto(srcId){
  const src=await get('punto',srcId); if(!src)return null;
  const np=Object.assign({},src,{id:uid(),_parent:src._parent},ahora());
  ['Coordenadas Geográficas Decimales_Lat','Coordenadas Geográficas Decimales_Long','COTA','PRECISION_GPS','ID_PUNTO_CONTROL']
    .forEach(k=>np[k]='');
  delete np._satelital; delete np._satBounds;   // la vista satelital es del sitio anterior
  await put('punto',np);
  // litologías (remapear ids para reenlazar estructurales)
  const mapLito={};
  for(const li of await childrenOf('litologia',srcId)){const n=Object.assign({},li,{id:uid(),_parent:np.id});mapLito[li.id]=n.id;await put('litologia',n);}
  for(const store of ['estructural','contacto','muestreo']){
    for(const it of await childrenOf(store,srcId)){const n=Object.assign({},it,{id:uid(),_parent:np.id});
      if(n.ID_LITOLOGIA&&mapLito[n.ID_LITOLOGIA])n.ID_LITOLOGIA=mapLito[n.ID_LITOLOGIA];
      await put(store,n);}
  }
  return np;
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
    el('button',{class:'btn blue',onclick:exportGPKG},'🗺️ GeoPackage (.gpkg — QGIS / ArcGIS)'),
    el('button',{class:'btn blue',onclick:exportGDB},'🗄️ GDB — File Geodatabase de Esri (ZIP)'),
    el('button',{class:'btn orange',onclick:exportPDF},'📄 PDF — Libreta de terreno')));
  card.append(el('div',{class:'muted',style:'margin-top:8px;font-size:12px',html:
    'GDB: la primera vez requiere conexión (descarga el conversor GDAL, ~40 MB); después queda disponible offline.'}));
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
  // líneas de control -> LineString con color por CLASE_LINEA
  let lineasKml=''; let nLin=0;
  const toKmlColor=hex=>{const h=(hex||'#444444').replace('#','');return 'ff'+h.slice(4,6)+h.slice(2,4)+h.slice(0,2);};
  // nombre = clase — tipo (subtipo) [certeza], omitiendo los niveles que estén vacíos
  const rotuloLinea=l=>[l.CLASE_LINEA,l.TIPO_LINEA].filter(Boolean).join(' — ')
    +(l.SUBTIPO_LINEA?' '+l.SUBTIPO_LINEA:'')
    +(l.CERTEZA_LINEA?' ('+l.CERTEZA_LINEA+')':'');
  for(const l of await all('linea')){
    if(!l.geom||l.geom.length<2)continue; nLin++;
    const coords=l.geom.map(c=>c[1]+','+c[0]+',0').join(' ');
    const nombre=rotuloLinea(l);
    lineasKml+='<Placemark><name>'+esc(nombre)+'</name><description>'+esc(l.NOTA||'')+'</description>'
      +'<Style><LineStyle><color>'+toKmlColor(LINEA_CLASE_COLOR[l.CLASE_LINEA])+'</color><width>3</width></LineStyle></Style>'
      +'<LineString><tessellate>1</tessellate><coordinates>'+coords+'</coordinates></LineString></Placemark>\n';
  }
  const kml='<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Captura de terreno</name>\n'+overlays+lineasKml+pk+'</Document></kml>';
  files.unshift({name:'doc.kml',data:new TextEncoder().encode(kml)});
  descargar('captura_terreno.kmz',zipStore(files));
  toast('KMZ exportado ('+n+' puntos'+(nLin?', '+nLin+' líneas':'')+(files.length>1?', imágenes':'')+')');
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

// -------- GeoPackage (sql.js) y GDB Esri (gdal3.js) --------
function cargarLib(src){return new Promise((res,rej)=>{if(document.querySelector('script[data-lib="'+src+'"]'))return res();
  const s=el('script',{src,'data-lib':src});s.onload=res;s.onerror=()=>rej(new Error('no se pudo cargar '+src+' — ¿sin conexión?'));document.head.append(s);});}
function dataUrlBytes(d){return (d&&d.startsWith('data:'))?b64ToBytes(d.split(',')[1]):null;}
function wkbPoint(lon,lat){const v=new DataView(new ArrayBuffer(21));v.setUint8(0,1);v.setUint32(1,1,true);
  v.setFloat64(5,lon,true);v.setFloat64(13,lat,true);return new Uint8Array(v.buffer);}
function wkbLine(coords){const v=new DataView(new ArrayBuffer(9+16*coords.length));v.setUint8(0,1);v.setUint32(1,2,true);
  v.setUint32(5,coords.length,true);coords.forEach((c,i)=>{v.setFloat64(9+16*i,c[1],true);v.setFloat64(17+16*i,c[0],true);});
  return new Uint8Array(v.buffer);}
function gpkgGeom(wkb){const g=new Uint8Array(8+wkb.length);g[0]=0x47;g[1]=0x50;g[2]=0;g[3]=1;
  new DataView(g.buffer).setInt32(4,4326,true);g.set(wkb,8);return g;}
const WKT4326='GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]]';

async function construirGPKG(){
  if(!window.initSqlJs)await cargarLib('vendor/sql-wasm.js');
  const SQL=await initSqlJs({locateFile:f=>'vendor/'+f});
  const db=new SQL.Database();
  const cq=n=>'"'+String(n).replace(/"/g,'""')+'"';
  const txt=v=>(v==null||v==='')?null:String(v);
  db.run('PRAGMA application_id=1196444487');  // 'GPKG'
  db.run('PRAGMA user_version=10300');         // GeoPackage 1.3
  db.run('CREATE TABLE gpkg_spatial_ref_sys (srs_name TEXT NOT NULL, srs_id INTEGER PRIMARY KEY, organization TEXT NOT NULL, organization_coordsys_id INTEGER NOT NULL, definition TEXT NOT NULL, description TEXT)');
  db.run("INSERT INTO gpkg_spatial_ref_sys VALUES ('WGS 84',4326,'EPSG',4326,?,NULL),('Undefined cartesian SRS',-1,'NONE',-1,'undefined',NULL),('Undefined geographic SRS',0,'NONE',0,'undefined',NULL)",[WKT4326]);
  db.run("CREATE TABLE gpkg_contents (table_name TEXT NOT NULL PRIMARY KEY, data_type TEXT NOT NULL, identifier TEXT UNIQUE, description TEXT DEFAULT '', last_change DATETIME NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')), min_x DOUBLE, min_y DOUBLE, max_x DOUBLE, max_y DOUBLE, srs_id INTEGER)");
  db.run('CREATE TABLE gpkg_geometry_columns (table_name TEXT NOT NULL, column_name TEXT NOT NULL, geometry_type_name TEXT NOT NULL, srs_id INTEGER NOT NULL, z TINYINT NOT NULL, m TINYINT NOT NULL, CONSTRAINT pk_geom_cols PRIMARY KEY (table_name, column_name))');
  // ID_REG/ID_PADRE replican id/_parent internos para conservar las relaciones entre tablas
  function crear(tbl,cs,extras,conGeom){
    const cols=['ID_REG TEXT','ID_PADRE TEXT'].concat(cs.map(n=>cq(n)+' TEXT')).concat(extras.map(e=>e[0]+' BLOB'));
    db.run('CREATE TABLE '+cq(tbl)+' (fid INTEGER PRIMARY KEY AUTOINCREMENT'+(conGeom?', geom BLOB':'')+', '+cols.join(', ')+')');
    const names=(conGeom?['geom']:[]).concat(['ID_REG','ID_PADRE'],cs.map(cq),extras.map(e=>e[0]));
    return db.prepare('INSERT INTO '+cq(tbl)+' ('+names.join(', ')+') VALUES ('+names.map(()=>'?').join(',')+')');
  }
  const latF=p=>p['Coordenadas Geográficas Decimales_Lat']||p.LAT;
  const lonF=p=>p['Coordenadas Geográficas Decimales_Long']||p.LONG;
  let nP=0,nL=0;
  {// capa de puntos de control
   const cs=campos('punto').map(c=>c.nombre);
   const extras=[['IMAGEN_SATELITAL',r=>r._satelital?b64ToBytes(r._satelital):null]];
   const st=crear('PUNTO_CONTROL',cs,extras,true);
   const env={x0:1/0,y0:1/0,x1:-1/0,y1:-1/0};
   for(const r of await all('punto')){
     const lat=parseFloat(latF(r)),lon=parseFloat(lonF(r));let g=null;
     if(!isNaN(lat)&&!isNaN(lon)){g=gpkgGeom(wkbPoint(lon,lat));nP++;
       env.x0=Math.min(env.x0,lon);env.x1=Math.max(env.x1,lon);env.y0=Math.min(env.y0,lat);env.y1=Math.max(env.y1,lat);}
     st.run([g,txt(r.id),txt(r._parent)].concat(cs.map(c=>txt(r[c])),extras.map(e=>e[1](r))));
   }
   st.free();
   db.run("INSERT INTO gpkg_contents (table_name,data_type,identifier,min_x,min_y,max_x,max_y,srs_id) VALUES ('PUNTO_CONTROL','features','PUNTO_CONTROL',?,?,?,?,4326)",nP?[env.x0,env.y0,env.x1,env.y1]:[null,null,null,null]);
   db.run("INSERT INTO gpkg_geometry_columns VALUES ('PUNTO_CONTROL','geom','POINT',4326,0,0)");
  }
  {// capa de líneas de control (contacto/estructura-falla/geomorfología) dibujadas en el mapa
   const csL=campos('linea').filter(c=>c.nombre!=='ID_PROYECTO'&&c.nombre!=='ID_LINEA').map(c=>c.nombre);
   const st=crear('LINEA_CONTROL',csL,[],true);
   const env={x0:1/0,y0:1/0,x1:-1/0,y1:-1/0};
   for(const l of await all('linea')){
     if(!l.geom||l.geom.length<2)continue;nL++;
     l.geom.forEach(c=>{env.x0=Math.min(env.x0,c[1]);env.x1=Math.max(env.x1,c[1]);env.y0=Math.min(env.y0,c[0]);env.y1=Math.max(env.y1,c[0]);});
     st.run([gpkgGeom(wkbLine(l.geom)),txt(l.id),txt(l._parent)].concat(csL.map(n=>txt(l[n]))));
   }
   st.free();
   db.run("INSERT INTO gpkg_contents (table_name,data_type,identifier,min_x,min_y,max_x,max_y,srs_id) VALUES ('LINEA_CONTROL','features','LINEA_CONTROL',?,?,?,?,4326)",nL?[env.x0,env.y0,env.x1,env.y1]:[null,null,null,null]);
   db.run("INSERT INTO gpkg_geometry_columns VALUES ('LINEA_CONTROL','geom','LINESTRING',4326,0,0)");
  }
  for(const s of STORES){  // resto de tablas, sin geometría
    if(s==='punto')continue;
    const tbl=STORE2TBL[s];const cs=campos(s).map(c=>c.nombre);
    const extras=(s==='foto'||s==='esquema')?[['IMAGEN',r=>dataUrlBytes(r._img)]]:[];
    const st=crear(tbl,cs,extras,false);
    for(const r of await all(s))st.run([txt(r.id),txt(r._parent)].concat(cs.map(c=>txt(r[c])),extras.map(e=>e[1](r))));
    st.free();
    db.run("INSERT INTO gpkg_contents (table_name,data_type,identifier,srs_id) VALUES (?,?,?,0)",[tbl,'attributes',tbl]);
  }
  const bytes=db.export();db.close();
  return {bytes,nP,nL};
}

async function exportGPKG(){
  try{
    toast('Generando GeoPackage…');
    const r=await construirGPKG();
    descargar('captura_terreno.gpkg',new Blob([r.bytes],{type:'application/geopackage+sqlite3'}));
    toast('GeoPackage exportado ('+r.nP+' puntos, '+r.nL+' líneas, 8 tablas)');
  }catch(e){console.error(e);toast('Error al generar GeoPackage: '+e.message);}
}

async function exportGDB(){
  try{
    toast('Preparando conversor GDB…');
    if(!window.initGdalJs)await cargarLib('vendor/gdal3.js');
    if(!window._Gdal)window._Gdal=await initGdalJs({path:'vendor',useWorker:false});
    const Gdal=window._Gdal;
    const r=await construirGPKG();
    const stem='ct_'+Date.now().toString(36);   // nombre único: aísla esta corrida de restos de intentos previos en /output
    const res=await Gdal.open(new File([r.bytes],stem+'.gpkg'));
    const ds=res.datasets[0];
    toast('Convirtiendo a File Geodatabase…');
    // sin API Arrow: usa hilos (pthreads) y falla en WASM sin COOP/COEP
    await Gdal.ogr2ogr(ds,['-f','OpenFileGDB','--config','OGR2OGR_USE_ARROW_API','NO']);
    const salidas=(await Gdal.getOutputFiles()).filter(o=>String(o.path||o).includes('/'+stem+'.gdb/'));
    if(!salidas.length)throw new Error('GDAL no generó la GDB');
    const files=[];
    for(const o of salidas){
      const p=String(o.path||o);
      try{files.push({name:'captura_terreno.gdb/'+p.split('.gdb/')[1],data:new Uint8Array(await Gdal.getFileBytes(p))});}
      catch(_){/* entradas de directorio */}
    }
    await Gdal.close(ds);
    descargar('captura_terreno_GDB.zip',zipStore(files));
    toast('GDB exportada ('+r.nP+' puntos, '+r.nL+' líneas) — descomprima el ZIP; la carpeta .gdb se abre en ArcGIS/QGIS');
  }catch(e){console.error(e);toast('Error al generar GDB: '+e.message);}
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
  // foto-mapas: base con pines numerados + galería de detalles
  let fmHtml='';
  for(const fm of await fotomapasRaiz(pt.id)){
    const comp=await compositaFotomapa(fm); const hijos=await fotomapaHijos(fm.id);
    let gal=''; hijos.forEach((c,i)=>{gal+='<figure><img src="'+c._base+'"><figcaption>'+(i+1)+'. '+esc(c.TITULO||'detalle')+'</figcaption></figure>';});
    fmHtml+='<div class="sec"><h2>Foto-mapa: '+esc(fm.TITULO||'')+'</h2>'
      +'<img style="max-width:100%;border:1px solid #999" src="'+comp+'">'
      +(gal?'<div class="imgs">'+gal+'</div>':'')+'</div>';
  }
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
    +fmHtml
    +'</div>';
}

// ============================ Init ============================
function pantallaError(msg,detalle){
  const app=$('#app'); if(!app)return;
  $('#ttl').textContent='GeoTerreno CDC';
  app.innerHTML='<div class="card"><h2>⚠️ '+msg+'</h2>'
    +'<div class="muted" style="margin:6px 0">'+(detalle||'')+'</div>'
    +'<div class="btnbar"><button class="btn" onclick="location.reload()">↻ Reintentar</button></div></div>';
}
// muestra cualquier error de JS en pantalla (para no quedar en blanco)
window.addEventListener('error',e=>{if(!db)pantallaError('Error al iniciar',(e.message||'')+'');});
(async()=>{
  try{
    await openDB();
  }catch(e){
    const m=String(e&&e.message||e);
    if(m.includes('BLOCKED')) return pantallaError('La app está abierta en otra ventana',
      'Cierra las otras pestañas o la app instalada y toca Reintentar. La base de datos se estaba actualizando.');
    if(m.includes('TIMEOUT')) return pantallaError('No se pudo abrir la base de datos',
      'Cierra completamente la app (todas las pestañas) y ábrela de nuevo. Si persiste, borra los datos del sitio y recarga.');
    return pantallaError('No se pudo abrir la base de datos', m);
  }
  try{ render(); }catch(e){ pantallaError('Error al dibujar', String(e&&e.message||e)); }
  if('serviceWorker' in navigator){
    // auto-actualiza: cuando el nuevo SW toma control, recarga una vez para tomar la última versión
    let recargando=false;
    navigator.serviceWorker.addEventListener('controllerchange',()=>{if(recargando)return;recargando=true;location.reload();});
    try{await navigator.serviceWorker.register('sw.js');}catch(e){}
  }
})();
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
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
    sw = r"""// Service worker offline-first (cache estatico)
const CACHE='geoterreno-cdc-v32';
const ASSETS=['./','./index.html','./manifest.json','./icons/icon-192.png','./icons/icon-512.png',
  './vendor/leaflet.css','./vendor/leaflet.js','./vendor/idb.js','./vendor/leaflet.offline.js',
  './vendor/georaster.browser.bundle.min.js','./vendor/georaster-layer-for-leaflet.min.js',
  './vendor/sql-wasm.js','./vendor/sql-wasm.wasm',
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
