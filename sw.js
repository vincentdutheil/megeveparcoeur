/* Service worker Megève par cœur : le site s'ouvre même sans réseau (dernière version vue). */
const V="mpc-v20";
const SHELL=["/","/meteo/","/webcams/","/assets/agenda.js","/assets/app.js","/assets/compteur.js?v=1","/assets/ciel.js","/assets/ciel.css","/img/logo.png","/img/icon-192.png","/videos/hero-poster.jpg"];
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

/* Notifications : le texte est demandé au serveur au moment de l'affichage */
self.addEventListener("push",e=>{
  e.waitUntil(self.registration.pushManager.getSubscription()
    .then(s=>fetch("/api/push?latest=1&ep="+encodeURIComponent(s?s.endpoint:""),{cache:"no-store"}))
    .then(r=>r.json()).catch(()=>({title:"Megève par cœur",body:"Du nouveau à Megève !",url:"/"}))
    .then(m=>self.registration.showNotification(m.title||"Megève par cœur",{body:m.body||"",icon:"/img/icon-192.png",badge:"/img/icon-192.png",tag:m.tag||"mpc",data:{url:m.url||"/"}})));
});
self.addEventListener("notificationclick",e=>{
  e.notification.close();
  const url=new URL((e.notification.data&&e.notification.data.url)||"/",self.location.origin).href;
  e.waitUntil(clients.matchAll({type:"window",includeUncontrolled:true}).then(ws=>{
    for(const w of ws){if("focus" in w){w.navigate&&w.navigate(url);return w.focus();}}
    return clients.openWindow(url);
  }));
});
