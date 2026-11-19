/* Service worker Megève par cœur : le site s'ouvre même sans réseau (dernière version vue). */
const V="mpc-v2";
const SHELL=["/","/meteo/","/webcams/","/assets/agenda.js","/assets/app.js","/img/logo.png","/img/icon-192.png","/videos/hero-poster.jpg"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(SHELL).catch(()=>{})));self.skipWaiting();});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==V).map(x=>caches.delete(x)))).then(()=>self.clients.claim()));});
self.addEventListener("fetch",e=>{
  const r=e.request; if(r.method!=="GET") return;
  const u=new URL(r.url); if(u.origin!==location.origin) return;            // météo, webcams, polices : réseau direct
  if(u.pathname.startsWith("/admin")||u.pathname.startsWith("/api/")) return;
  if(/\.(mp4|webm)$/.test(u.pathname)) return;                               // vidéos : pas de cache
  const isData=u.pathname.startsWith("/data/")||r.mode==="navigate";
  if(isData){ // réseau d'abord (données fraîches), cache si hors ligne
    e.respondWith(fetch(r).then(res=>{const c=res.clone();caches.open(V).then(x=>x.put(r,c));return res;}).catch(()=>caches.match(r,{ignoreSearch:true}).then(m=>m||caches.match("/"))));
  }else{ // cache d'abord, mise à jour en arrière-plan
    e.respondWith(caches.match(r).then(m=>{const net=fetch(r).then(res=>{if(res.ok){const c=res.clone();caches.open(V).then(x=>x.put(r,c));}return res;}).catch(()=>m);return m||net;}));
  }
});
