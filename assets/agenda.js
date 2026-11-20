/* Agenda Megève par cœur : filtres, boutons « ajouter à mon agenda » / WhatsApp / partager,
   données structurées Google (schema.org/Event). Utilisé par / (fr) et /en/ (en). */
(function(){
const LANG=document.documentElement.lang==="en"?"en":"fr";
const SITE="https://www.megeveparcoeur.fr";
const PAGE=SITE+(LANG==="en"?"/en/":"/");
const T={
  fr:{months:["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"],
      mc:["janv.","févr.","mars","avr.","mai","juin","juil.","août","sept.","oct.","nov.","déc."],
      days:["dim.","lun.","mar.","mer.","jeu.","ven.","sam."],
      season:"Toute la saison", until:"Jusqu'au", to:"au", more:"Plus d'infos ↗", none:"Aucun événement pour ce choix. Essayez un autre filtre.",
      add:"📅 Ajouter à mon agenda", gcal:"Google Agenda", ics:"iPhone, Outlook (.ics)", wa:"💬 WhatsApp", share:"↗ Partager", copied:"Lien copié ✓",
      q:{all:"Tout",fav:"Mes sorties",today:"Aujourd'hui",we:"Ce week-end",free:"Gratuit",kids:"Avec des enfants",rain:"S'il pleut"},nofav:"Touche ☆ sur un événement pour le garder dans « Mes sorties ».",favon:"Retirer de mes sorties",favoff:"Garder dans mes sorties",
      waText:(e,dt)=>`${e} · ${dt}\nTout l'agenda de Megève & alentours :`, upcoming:n=>`<span><b>${n}</b> événements à venir</span>`, villages:n=>`<span><b>${n}</b> villages</span>`, weekly:"<span>🔄 Mis à jour chaque jeudi</span>"},
  en:{months:["January","February","March","April","May","June","July","August","September","October","November","December"],
      mc:["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
      days:["Sun","Mon","Tue","Wed","Thu","Fri","Sat"],
      season:"All season", until:"Until", to:"to", more:"More info ↗", none:"No events for this choice. Try another filter.",
      add:"📅 Add to calendar", gcal:"Google Calendar", ics:"iPhone, Outlook (.ics)", wa:"💬 WhatsApp", share:"↗ Share", copied:"Link copied ✓",
      q:{all:"All",fav:"My picks",today:"Today",we:"This weekend",free:"Free",kids:"With kids",rain:"Rainy day"},nofav:"Tap ☆ on an event to save it to “My picks”.",favon:"Remove from my picks",favoff:"Save to my picks",
      waText:(e,dt)=>`${e} · ${dt}\nWhat's on in Megève & around:`, upcoming:n=>`<span><b>${n}</b> upcoming events</span>`, villages:n=>`<span><b>${n}</b> villages</span>`, weekly:"<span>🔄 Updated every Thursday</span>"}
}[LANG];
const CP={"Megève":"74120","Demi-Quartier":"74120","Praz-sur-Arly":"74120","Combloux":"74920"};
const esc=s=>String(s==null?"":s).replace(/&/g,"&amp;").replace(/"/g,"&quot;").replace(/</g,"&lt;");
const iso=d=>d.toISOString().slice(0,10);
const pad=n=>String(n).padStart(2,"0");
function localToday(){const n=new Date();return `${n.getFullYear()}-${pad(n.getMonth()+1)}-${pad(n.getDate())}`;}
function addDays(s,k){const d=new Date(s+"T12:00:00");d.setDate(d.getDate()+k);return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;}
function slug(e){return "e-"+e.d+"-"+(e.t||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"").slice(0,40);}
/* page de l'événement (créée au déploiement par tools/build.mjs, même règle) */
let DUP={};
const strip=s=>String(s||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"");
const pbase=e=>{const t=strip(e.t);return e.d+"-"+(t.length<=60?t:t.slice(0,60).replace(/-[^-]*$/,""));};
const pslug=e=>pbase(e)+(DUP[pbase(e)]>1?"-"+strip(e.lieu):"");
const evUrl=e=>SITE+(LANG==="en"?"/en":"")+"/agenda/"+pslug(e)+"/";
const title=e=>LANG==="en"&&e.t_en?e.t_en:e.t, desc=e=>LANG==="en"&&e.x_en?e.x_en:e.x;
function hhmm(h){if(!h)return null;const m=String(h).match(/(\d{1,2})\s*h\s*(\d{2})?/i);if(!m)return null;return [pad(+m[1]),m[2]||"00"];}
function dParts(s){const [y,m,d]=s.split("-").map(Number);return {y,m,d};}
function dLabel(e){const a=dParts(e.d); if(!e.d2||e.d2===e.d) return {big:`${a.d} ${T.mc[a.m-1]}`,small:T.days[new Date(e.d+"T12:00:00").getDay()]+" "+a.y};
  const b=dParts(e.d2); if(e.always) return {big:T.until,small:`${b.d} ${T.mc[b.m-1]} ${b.y}`};
  if(a.m===b.m&&a.y===b.y) return {big:`${a.d}–${b.d} ${T.mc[a.m-1]}`,small:String(a.y)};
  return {big:`${a.d} ${T.mc[a.m-1]}`,small:`${T.to} ${b.d} ${T.mc[b.m-1]} ${b.y}`};}
function dateText(e){const L=dLabel(e);return `${L.big} ${L.small}${e.h?" · "+e.h:""}`;}

/* étiquettes déduites (la tâche du jeudi peut aussi poser free/kids/indoor explicitement) */
const txt=e=>((e.t||"")+" "+(e.x||"")).toLowerCase();
const isFree=e=>e.free===true||(e.free!==false&&/gratuit|entr[ée]e libre|acc[eè]s libre|\bfree\b/.test(txt(e))&&!/payant/.test(txt(e)));
const isKids=e=>e.kids===true||(e.kids!==false&&(e.cat==="Famille"||/enfant|famille|b[ée]b[ée]|conte|guignol|p[èe]re no[ëe]l|lutin|jeunesse|kids|ludique|chasse au/.test(txt(e))));
const isRain=e=>e.indoor===true||(e.indoor!==false&&e.cat!=="Ski"&&(["Expo","Spectacle"].includes(e.cat)||/salle|palais|m[ée]diath[eè]que|mus[ée]e|[ée]glise|cin[ée]ma|th[ée][âa]tre|auditorium|chapelle|biblioth[eè]que|escape|atelier|conf[ée]rence|projection|patinoire|galerie|int[ée]rieur/.test(txt(e))));
function overlaps(e,a,b){const s=e.d,f=e.d2||e.d;return s<=b&&f>=a;}
function weekend(){const t=localToday(),wd=new Date(t+"T12:00:00").getDay();
  if(wd===6) return [t,addDays(t,1)]; if(wd===0) return [t,t];
  const sat=addDays(t,6-wd); return [addDays(sat,-1),addDays(sat,1)];} // vendredi → dimanche

const PRESET=(document.getElementById("agenda-list")||{dataset:{}}).dataset.q||"";
let A=[], lieu="all", quick=PRESET||"all";
/* « Mes sorties » : favoris gardés sur l'appareil */
let FAV=[];try{FAV=JSON.parse(localStorage.getItem("mpc-favs")||"[]");}catch(_){}
const isFav=id=>FAV.includes(id);
function toggleFav(id){FAV=isFav(id)?FAV.filter(x=>x!==id):[...FAV,id];try{localStorage.setItem("mpc-favs",JSON.stringify(FAV));}catch(_){}}
function filtered(){const t=localToday();
  return A.filter(e=>(e.d2||e.d)>=t && (lieu==="all"||e.lieu===lieu) && (
    quick==="all" ? true : quick==="fav" ? isFav(slug(e)) :
    quick==="today" ? overlaps(e,t,t) :
    quick==="we" ? (()=>{const [a,b]=weekend();return overlaps(e,a,b);})() :
    quick==="free" ? isFree(e) : quick==="kids" ? isKids(e) : quick==="rain" ? isRain(e) : true))
   .sort((x,y)=>(x.always?1:0)-(y.always?1:0)||x.d.localeCompare(y.d));}

function render(){
  const list=filtered(); let html="",cur="";
  for(const e of list){
    const a=dParts(e.d), key=e.always?T.season:`${T.months[a.m-1]} ${a.y}`;
    if(key!==cur){cur=key;html+=`<h3 class="month">${key.charAt(0).toUpperCase()+key.slice(1)}</h3>`;}
    const L=dLabel(e), id=slug(e), tags=[isFree(e)?(LANG==="en"?"Free":"Gratuit"):"",isKids(e)?(LANG==="en"?"Kids":"Enfants"):""].filter(Boolean);
    html+=`<article class="ev" id="${id}"><div class="date"><b>${L.big}</b><span>${L.small}</span></div>
      <div><h3><a href="${evUrl(e).slice(SITE.length)}">${esc(title(e))}</a></h3><p>${e.h?`<span class="hour">${esc(e.h)} · </span>`:""}${esc(desc(e))}</p>
        <div class="acts">${tags.map(x=>`<span class="tg">${x}</span>`).join("")}
          <span class="addw"><button type="button" class="act" data-a="add" data-id="${id}" aria-expanded="false">${T.add}</button>
            <span class="menu" hidden><button type="button" data-a="gcal" data-id="${id}">${T.gcal}</button><button type="button" data-a="ics" data-id="${id}">${T.ics}</button></span></span>
          <button type="button" class="act" data-a="wa" data-id="${id}">${T.wa}</button>
          <button type="button" class="act" data-a="share" data-id="${id}">${T.share}</button>
          <button type="button" class="act fav" data-a="fav" data-id="${id}" aria-pressed="${isFav(id)}" title="${isFav(id)?T.favon:T.favoff}">${isFav(id)?"⭐":"☆"}</button></div></div>
      <div class="meta"><span class="place ${esc(e.lieu)}">${esc(e.lieu)}</span>${e.u?`<a class="more" href="${esc(e.u)}" target="_blank" rel="noopener">${T.more}</a>`:""}</div></article>`;
  }
  document.getElementById("agenda-list").innerHTML=html||`<p class="note">${quick==="fav"?T.nofav:T.none}</p>`;
}
const byId=id=>A.find(e=>slug(e)===id);
function gcalUrl(e){const hm=hhmm(e.h),d=e.d.replace(/-/g,""),end=(e.d2||e.d);
  const dates=hm&&(!e.d2||e.d2===e.d)?`${d}T${hm[0]}${hm[1]}00/${d}T${pad((+hm[0]+2)%24)}${hm[1]}00`:`${d}/${addDays(end,1).replace(/-/g,"")}`;
  const p=new URLSearchParams({action:"TEMPLATE",text:title(e),dates,details:(desc(e)||"")+"\n\n"+evUrl(e),location:`${e.lieu}, ${CP[e.lieu]||""} France`,ctz:"Europe/Paris"});
  return "https://calendar.google.com/calendar/render?"+p;}
function icsFile(e){const hm=hhmm(e.h),d=e.d.replace(/-/g,""),one=!e.d2||e.d2===e.d;
  const icsEsc=s=>String(s||"").replace(/\\/g,"\\\\").replace(/;/g,"\\;").replace(/,/g,"\\,").replace(/\n/g,"\\n");
  const lines=["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Megeve par coeur//Agenda//FR","CALSCALE:GREGORIAN","BEGIN:VEVENT",
    "UID:"+slug(e)+"@megeveparcoeur.fr","DTSTAMP:"+new Date().toISOString().replace(/[-:]/g,"").slice(0,15)+"Z",
    ...(hm&&one?["DTSTART;TZID=Europe/Paris:"+d+"T"+hm[0]+hm[1]+"00","DURATION:PT2H"]:["DTSTART;VALUE=DATE:"+d,"DTEND;VALUE=DATE:"+addDays(e.d2||e.d,1).replace(/-/g,"")]),
    "SUMMARY:"+icsEsc(title(e)),"DESCRIPTION:"+icsEsc((desc(e)||"")+"\n"+(e.u||"")),"LOCATION:"+icsEsc(e.lieu+", France"),"URL:"+evUrl(e),"END:VEVENT","END:VCALENDAR"];
  const blob=new Blob([lines.join("\r\n")],{type:"text/calendar;charset=utf-8"}),a=document.createElement("a");
  a.href=URL.createObjectURL(blob);a.download=slug(e).slice(2)+".ics";document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();},1500);}

function onClick(ev){const b=ev.target.closest("button[data-a]");
  if(!b){document.querySelectorAll(".acts .menu").forEach(m=>{m.hidden=true;});return;}
  const e=byId(b.dataset.id); if(!e) return; const link=evUrl(e);
  if(b.dataset.a==="fav"){toggleFav(b.dataset.id);const on=isFav(b.dataset.id);b.textContent=on?"⭐":"☆";b.setAttribute("aria-pressed",on);b.title=on?T.favon:T.favoff;if(quick==="fav")render();return;}
  if(b.dataset.a==="add"){const m=b.nextElementSibling,open=m.hidden;document.querySelectorAll(".acts .menu").forEach(x=>{x.hidden=true;});m.hidden=!open;b.setAttribute("aria-expanded",open);return;}
  document.querySelectorAll(".acts .menu").forEach(m=>{m.hidden=true;});
  if(b.dataset.a==="gcal") window.open(gcalUrl(e),"_blank","noopener");
  try{window.va&&window.va("event",{name:"agenda_"+b.dataset.a});}catch(_){}
  if(b.dataset.a==="ics") icsFile(e);
  if(b.dataset.a==="wa") window.open("https://wa.me/?text="+encodeURIComponent(T.waText(title(e),dateText(e)+" · "+e.lieu)+" "+link),"_blank","noopener");
  if(b.dataset.a==="share"){const data={title:title(e),text:dateText(e)+" · "+e.lieu,url:link};
    if(navigator.share) navigator.share(data).catch(()=>{});
    else if(navigator.clipboard){navigator.clipboard.writeText(link).then(()=>{const o=b.textContent;b.textContent=T.copied;setTimeout(()=>{b.textContent=o;},1800);});}}
}

/* Données structurées Google : un schema.org/Event par événement à venir */
function jsonLd(){const t=localToday();
  const evs=(PRESET?filtered():A.filter(e=>(e.d2||e.d)>=t)).slice(0,300).map(e=>{const hm=hhmm(e.h),one=!e.d2||e.d2===e.d;
    const o={"@context":"https://schema.org","@type":"Event",name:title(e),description:desc(e)||title(e),
      startDate:hm&&one?`${e.d}T${hm[0]}:${hm[1]}`:e.d, endDate:e.d2||e.d,
      eventStatus:"https://schema.org/EventScheduled",eventAttendanceMode:"https://schema.org/OfflineEventAttendanceMode",
      location:{"@type":"Place",name:e.lieu,address:{"@type":"PostalAddress",addressLocality:e.lieu,postalCode:CP[e.lieu]||"",addressRegion:"Haute-Savoie",addressCountry:"FR"}},
      image:[SITE+"/videos/hero-poster.jpg"],url:evUrl(e),inLanguage:LANG};
    if(isFree(e)) o.isAccessibleForFree=true;
    if(e.u) o.sameAs=e.u;
    return o;});
  let s=document.getElementById("ld-events"); if(!s){s=document.createElement("script");s.type="application/ld+json";s.id="ld-events";document.head.appendChild(s);}
  s.textContent=JSON.stringify(evs);}

function mount(){
  const tabs=document.getElementById("ag-tabs"), q=document.getElementById("ag-quick");
  tabs&&tabs.addEventListener("click",e=>{const b=e.target.closest(".tab");if(!b)return;tabs.querySelectorAll(".tab").forEach(x=>x.setAttribute("aria-pressed",x===b));lieu=b.dataset.l;render();});
  if(q){q.innerHTML=Object.entries(T.q).map(([k,v])=>`<button type="button" class="qf" data-q="${k}" aria-pressed="${k===quick}">${{all:"✨",fav:"⭐",today:"☀️",we:"🎉",free:"🆓",kids:"🧒",rain:"☔"}[k]} ${v}</button>`).join("");
    if(PRESET){const pb=q.querySelector('[aria-pressed="true"]');if(pb)q.scrollLeft=pb.offsetLeft-q.offsetLeft-16;}
    q.addEventListener("click",e=>{const b=e.target.closest(".qf");if(!b)return;q.querySelectorAll(".qf").forEach(x=>x.setAttribute("aria-pressed",x===b));quick=b.dataset.q;render();});}
  document.getElementById("agenda-list").addEventListener("click",onClick);
  document.addEventListener("click",e=>{if(!e.target.closest(".addw"))document.querySelectorAll(".acts .menu").forEach(m=>{m.hidden=true;});});
  fetch("/data/agenda.json",{cache:"no-store"}).then(r=>r.json()).then(d=>{A=d;DUP={};A.forEach(e=>{const k=pbase(e);DUP[k]=(DUP[k]||0)+1;});render();jsonLd();
    const t=localToday(),st=document.getElementById("ag-stats");
    if(st)st.innerHTML=T.upcoming(PRESET?filtered().length:d.filter(e=>(e.d2||e.d)>=t).length)+T.villages(new Set(d.map(e=>e.lieu)).size)+T.weekly;
    if(location.hash.startsWith("#e-")){const el=document.getElementById(location.hash.slice(1));if(el){el.classList.add("hl");el.scrollIntoView({block:"center"});}}
  }).catch(()=>{document.getElementById("agenda-list").innerHTML='<p class="note">⚠️</p>';});
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",mount);else mount();
})();
