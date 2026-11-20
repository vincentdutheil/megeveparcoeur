/* Appli sur l'écran d'accueil : enregistrement du service worker + invitation à installer */
(function(){
  if("serviceWorker" in navigator) addEventListener("load",()=>navigator.serviceWorker.register("/sw.js").catch(()=>{}));
  const standalone=matchMedia("(display-mode: standalone)").matches||navigator.standalone;
  if(standalone) return;
  const en=document.documentElement.lang==="en";
  let seen=false; try{seen=localStorage.getItem("mpc-install")==="no";}catch(e){}
  const ua=navigator.userAgent;
  // navigateur intégré d'Instagram, Facebook, TikTok… : on ne peut pas y installer l'appli
  const inApp=/Instagram|FBAN|FBAV|FB_IAB|FBIOS|Line\/|Twitter|TikTok|musical_ly|BytedanceWebview|Snapchat|Pinterest|LinkedInApp/i.test(ua);
  const ios=/iphone|ipad|ipod/i.test(ua)&&!/crios|fxios/i.test(ua)&&!inApp;
  let deferred=null;
  function bar(html,onYes){
    if(seen||document.getElementById("mpc-inst")) return;
    const d=document.createElement("div");d.id="mpc-inst";d.setAttribute("role","dialog");d.setAttribute("aria-label",en?"Install the app":"Installer l'appli");
    d.innerHTML=`<img src="/img/icon-192.png" alt=""><div class="tx">${html}</div>${onYes?`<button class="y">${en?"Install":"Installer"}</button>`:`<a class="y" href="${en?"/en/app/":"/app/"}" style="text-decoration:none">${en?"How?":"Comment ?"}</a>`}<button class="n" aria-label="${en?"Close":"Fermer"}">✕</button>`;
    const st=document.createElement("style");st.textContent=`#mpc-inst{position:fixed;left:12px;right:12px;bottom:12px;z-index:60;max-width:520px;margin:0 auto;display:flex;align-items:center;gap:12px;background:#0a1424;color:#f4f8ff;border-radius:18px;padding:12px 14px;box-shadow:0 14px 40px rgba(0,0,0,.4);font:600 .9rem/1.35 "Nunito Sans",system-ui,sans-serif;animation:mpcup .4s ease}
#mpc-inst img{width:42px;height:42px;border-radius:10px}#mpc-inst .tx{flex:1}#mpc-inst b{display:block;font-size:1rem}
#mpc-inst .y{background:#c8323d;color:#fff;border:0;border-radius:999px;padding:9px 14px;font:800 .88rem inherit;cursor:pointer}
#mpc-inst .n{background:transparent;border:0;color:#fff;opacity:.7;font-size:1.1rem;cursor:pointer;padding:6px}
@keyframes mpcup{from{transform:translateY(120%)}to{transform:none}}`;
    document.head.appendChild(st);document.body.appendChild(d);
    d.querySelector(".n").onclick=()=>{d.remove();try{localStorage.setItem("mpc-install","no");}catch(e){}};
    if(onYes) d.querySelector(".y").onclick=onYes;
  }
  addEventListener("beforeinstallprompt",e=>{e.preventDefault();deferred=e;
    setTimeout(()=>bar(en?"<b>Megève par cœur on your phone</b>Agenda, snow & webcams in one tap.":"<b>Megève par cœur sur ton téléphone</b>Agenda, neige et webcams en un geste.",async()=>{deferred.prompt();await deferred.userChoice.catch(()=>{});document.getElementById("mpc-inst")?.remove();}),6000);});
  if(inApp&&innerWidth<820) setTimeout(()=>bar(en?"<b>Want the app?</b>First open this site in your browser (menu ⋯ then “Open in browser”).":"<b>Envie de l'appli ?</b>Ouvre d'abord le site dans ton navigateur (menu ⋯ puis « Ouvrir dans le navigateur »)."),8000);
  if(ios&&innerWidth<820) setTimeout(()=>bar(en?"<b>Add to your home screen</b>Tap <span aria-label='Share'>⬆︎</span> Share, then “Add to Home Screen”.":"<b>Ajoute l'appli à ton écran d'accueil</b>Touche <span aria-label='Partager'>⬆︎</span> Partager, puis « Sur l'écran d'accueil »."),8000);
})();

/* Statistiques de visites (Vercel Web Analytics : sans cookies, pas de bandeau) + quelques clics utiles */
(function(){
  if(location.hostname==="localhost"||location.hostname==="127.0.0.1") return;
  window.va=window.va||function(){(window.vaq=window.vaq||[]).push(arguments);};
  const s=document.createElement("script");s.defer=true;s.src="/_vercel/insights/script.js";document.head.appendChild(s);
  document.addEventListener("click",e=>{const a=e.target.closest("a[href]");if(!a)return;const h=a.getAttribute("href")||"";
    let n=null;
    if(/instagram\.com/.test(h)) n="instagram";
    else if(/coupedesbanquesgenevoises/.test(h)) n="boutique_externe";
    else if(/skaping\.com/.test(h)) n="webcam_ouverte";
    else if(/google\.com\/maps/.test(h)) n="itineraire";
    else if(a.classList.contains("more")) n="agenda_plus_infos";
    if(n) try{window.va("event",{name:n});}catch(_){}
  },true);
  document.addEventListener("submit",e=>{if(e.target&&e.target.id==="nl-form") try{window.va("event",{name:"newsletter_envoi"});}catch(_){}
    if(e.target&&e.target.id==="pr-form") try{window.va("event",{name:"proposition_evenement"});}catch(_){}},true);
})();
