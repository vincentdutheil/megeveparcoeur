/* Compteur maison (/api/compteur) : visites du site, ouvertures de l'appli, installations.
   Aucun cookie, aucune donnée personnelle : seuls des totaux sont envoyés. */
(function(){
  if(window.__mpcCpt) return; window.__mpcCpt=1;
  if(!/megeveparcoeur\.fr$/.test(location.hostname)) return;
  const hit=k=>{const u="/api/compteur?k="+k;
    try{if(navigator.sendBeacon&&navigator.sendBeacon(u,""))return;}catch(e){}
    fetch(u,{method:"POST",keepalive:true}).catch(()=>{});
    try{window.va&&window.va("event",{name:k==="install"?"appli_installee":k==="app"?"appli_ouverte":"visite_site"});}catch(e){}};
  const ls={get:k=>{try{return localStorage.getItem(k);}catch(e){return null;}},set:(k,v)=>{try{localStorage.setItem(k,v);}catch(e){}}};
  const app=matchMedia("(display-mode: standalone)").matches||matchMedia("(display-mode: fullscreen)").matches||navigator.standalone===true||/[?&]app=1\b/.test(location.search);
  // installation : événement du navigateur (Android, ordinateur)…
  addEventListener("appinstalled",()=>{if(!ls.get("mpc-installee")){ls.set("mpc-installee","1");hit("install");}});
  // …ou première ouverture depuis l'écran d'accueil (iPhone, qui ne prévient pas)
  if(app&&!ls.get("mpc-installee")){ls.set("mpc-installee","1");hit("install");}
  // une visite (ou une ouverture de l'appli) par session
  let done=null;try{done=sessionStorage.getItem("mpc-vu");}catch(e){}
  if(!done){try{sessionStorage.setItem("mpc-vu","1");}catch(e){}hit(app?"app":"web");}
})();
